import BackgroundTasks
import Capacitor
import CryptoKit
import Foundation

/// Keeps the downloaded offices fresh while the app is in the background.
///
/// Background code can't reach the web view's IndexedDB, so a background run downloads into files
/// (an inbox) and the page moves them into IndexedDB the next time it opens
/// (app/src/offline/native.js). The run follows the same rules as the web app's service worker
/// (app/src/offline/serviceWorker.js, backgroundRefresh): ask the API what content changed, then
/// download up to 80 missing or stale answers for today onward, and audio for today and tomorrow
/// when offline audio is on (tracks go to a background URLSession, OfflineAudioDownloads, which iOS
/// finishes on its own time). android/.../offline/ does the same on Android.
///
/// The page calls:
///
///     schedule({ plan, contentVersion, invalidations, fetched, audio })  -> { scheduled }
///     drain({ limit })  -> { entries, remaining, contentVersion, invalidations, audio, lastRunAt }
///     ack({ keys, invalidationsThrough, audio })
///     runNow()  -> { finished }  (for testing: one run now, in the foreground)
///
/// iOS runs the task (a BGAppRefreshTask registered in AppDelegate) when it chooses, no sooner
/// than about six hours after it was last scheduled, and gives it about 30 seconds.
@objc(OfflineSyncPlugin)
public class OfflineSyncPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "OfflineSyncPlugin"
    public let jsName = "OfflineSync"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "schedule", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "drain", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "ack", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "runNow", returnType: CAPPluginReturnPromise),
    ]

    /// Must match BGTaskSchedulerPermittedIdentifiers in Info.plist.
    static let taskIdentifier = "com.dailyoffice.dailyoffice2019.offline-refresh"
    private static let interval: TimeInterval = 6 * 3600

    @objc func schedule(_ call: CAPPluginCall) {
        let plan = call.options["plan"] as? [String: Any] ?? [:]
        let state: [String: Any] = [
            "plan": plan,
            "contentVersion": call.options["contentVersion"] as? NSNumber ?? 0,
            "invalidations": call.options["invalidations"] as? [Any] ?? [],
            "audio": call.options["audio"] as? [String: Any] ?? [:],
        ]
        let fetched = call.options["fetched"] as? [String: Any] ?? [:]
        OfflineSyncStore.shared.saveSchedule(state: state, fetched: fetched)
        if !OfflineSyncStore.shared.hasPlan {
            // Downloads removed (or turned off): stop the tracks on their way too.
            OfflineAudioDownloads.shared.cancelAll()
        }
        if let error = Self.scheduleNext() {
            call.resolve(["scheduled": false, "error": error.localizedDescription])
        } else {
            call.resolve(["scheduled": OfflineSyncStore.shared.hasPlan])
        }
    }

    @objc func drain(_ call: CAPPluginCall) {
        let limit = max(1, call.getInt("limit") ?? 20)
        call.resolve(OfflineSyncStore.shared.drain(limit: limit))
    }

    @objc func ack(_ call: CAPPluginCall) {
        let keys = call.options["keys"] as? [String] ?? []
        let through = (call.options["invalidationsThrough"] as? NSNumber)?.doubleValue ?? 0
        let audio = call.options["audio"] as? [String] ?? []
        OfflineSyncStore.shared.ack(keys: keys, invalidationsThrough: through, audio: audio)
        call.resolve()
    }

    /// One run now, for testing (the page doesn't call it).
    @objc func runNow(_ call: CAPPluginCall) {
        Task {
            let finished = await OfflineSyncRunner().run()
            call.resolve(["finished": finished])
        }
    }

    /// Called from AppDelegate's didFinishLaunching, as iOS requires.
    static func registerBackgroundTask() {
        BGTaskScheduler.shared.register(forTaskWithIdentifier: taskIdentifier, using: nil) { task in
            guard let task = task as? BGAppRefreshTask else {
                task.setTaskCompleted(success: false)
                return
            }
            handle(task)
        }
    }

    /// Ask for the next run (or, with nothing planned, cancel it). Returns why it couldn't be
    /// asked for (the Simulator, or Background App Refresh turned off).
    @discardableResult
    static func scheduleNext() -> Error? {
        guard OfflineSyncStore.shared.hasPlan else {
            BGTaskScheduler.shared.cancel(taskRequestWithIdentifier: taskIdentifier)
            return nil
        }
        let request = BGAppRefreshTaskRequest(identifier: taskIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: interval)
        do {
            try BGTaskScheduler.shared.submit(request)
            return nil
        } catch {
            print("Offline refresh could not be scheduled: \(error)")
            return error
        }
    }

    private static func handle(_ task: BGAppRefreshTask) {
        // The next run first, so the chain goes on whatever happens to this one.
        scheduleNext()
        let work = Task { await OfflineSyncRunner().run() }
        task.expirationHandler = {
            // Each download is saved as it lands; the rest wait for the next run.
            work.cancel()
        }
        Task {
            let finished = await work.value
            task.setTaskCompleted(success: finished)
        }
    }
}

// MARK: - Files

/// The plugin's files, in Application Support/offline-sync (not backed up):
///
///     state.json    what the page last scheduled: { plan, contentVersion, invalidations, audio }
///     index.json    { key: fetchedAt } of every planned answer stored or in the inbox
///     learned.json  what runs learned that the page hasn't taken yet:
///                   { contentVersion, invalidations, audio, lastRunAt }
///     inbox/        one file per downloaded answer, named for its key:
///                   { key, url, kind, date, profile, fetchedAt, body }
///
/// Audio goes where the page keeps its own downloads (app/src/offline/audio.js):
/// Library/NoCloud/offline-audio/<hashString(url)>.mp3.
final class OfflineSyncStore {
    static let shared = OfflineSyncStore()

    private let queue = DispatchQueue(label: "com.dailyoffice2019.offline-sync.store")
    private let fileManager = FileManager.default
    /// Goes up when the page removes the downloads, so a run under way stops writing.
    private var clearCount = 0
    private let root: URL
    private let inbox: URL
    let audioDirectory: URL

    private init() {
        let support = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask)[0]
        var root = support.appendingPathComponent("offline-sync", isDirectory: true)
        let library = fileManager.urls(for: .libraryDirectory, in: .userDomainMask)[0]
        audioDirectory = library.appendingPathComponent("NoCloud/offline-audio", isDirectory: true)
        inbox = root.appendingPathComponent("inbox", isDirectory: true)
        try? fileManager.createDirectory(at: inbox, withIntermediateDirectories: true)
        var values = URLResourceValues()
        values.isExcludedFromBackup = true
        try? root.setResourceValues(values)
        self.root = root
    }

    private func url(_ name: String) -> URL {
        root.appendingPathComponent(name)
    }

    private func read(_ name: String) -> [String: Any] {
        guard let data = try? Data(contentsOf: url(name)),
              let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else { return [:] }
        return object
    }

    private func write(_ name: String, _ object: [String: Any]) {
        guard let data = try? JSONSerialization.data(withJSONObject: object) else { return }
        try? data.write(to: url(name), options: .atomic)
    }

    private func inboxFile(_ key: String) -> URL {
        let digest = SHA256.hash(data: Data(key.utf8)).map { String(format: "%02x", $0) }.joined()
        return inbox.appendingPathComponent("\(digest).json")
    }

    private func inboxFiles() -> [URL] {
        let files = (try? fileManager.contentsOfDirectory(at: inbox, includingPropertiesForKeys: nil)) ?? []
        return files.filter { $0.pathExtension == "json" }.sorted { $0.lastPathComponent < $1.lastPathComponent }
    }

    var hasPlan: Bool {
        queue.sync {
            let plan = read("state.json")["plan"] as? [String: Any]
            return !((plan?["tasks"] as? [Any]) ?? []).isEmpty
        }
    }

    func state() -> [String: Any] {
        queue.sync { read("state.json") }
    }

    /// For a run to check, before writing, that the downloads weren't removed since it began.
    var generation: Int {
        queue.sync { clearCount }
    }

    func index() -> [String: Double] {
        queue.sync {
            var index: [String: Double] = [:]
            read("index.json").forEach { key, value in
                if let at = (value as? NSNumber)?.doubleValue { index[key] = at }
            }
            return index
        }
    }

    func learned() -> [String: Any] {
        queue.sync { read("learned.json") }
    }

    /// The page's plan. The index becomes what the page has stored, plus what is still waiting
    /// in the inbox. With nothing planned, what's waiting is dropped.
    func saveSchedule(state: [String: Any], fetched: [String: Any]) {
        queue.sync {
            let old = read("index.json")
            write("state.json", state)
            let tasks = (state["plan"] as? [String: Any])?["tasks"] as? [Any] ?? []
            if tasks.isEmpty {
                clearCount += 1
                inboxFiles().forEach { try? fileManager.removeItem(at: $0) }
                var learned = read("learned.json")
                (learned["audio"] as? [[String: Any]] ?? []).forEach { track in
                    if let path = track["path"] as? String {
                        try? fileManager.removeItem(at: audioDirectory.deletingLastPathComponent().appendingPathComponent(path))
                    }
                }
                learned["audio"] = []
                learned["invalidations"] = []
                write("learned.json", learned)
                write("index.json", [:])
                return
            }
            var index: [String: Any] = fetched
            old.forEach { key, value in
                guard let at = (value as? NSNumber)?.doubleValue,
                      fileManager.fileExists(atPath: inboxFile(key).path) else { return }
                let known = (index[key] as? NSNumber)?.doubleValue ?? 0
                if at > known { index[key] = at }
            }
            write("index.json", index)
        }
    }

    func setIndex(_ key: String, _ fetchedAt: Double) {
        queue.sync {
            var index = read("index.json")
            index[key] = fetchedAt
            write("index.json", index)
        }
    }

    func updateLearned(_ change: (inout [String: Any]) -> Void) {
        queue.sync {
            var learned = read("learned.json")
            change(&learned)
            write("learned.json", learned)
        }
    }

    /// A track saved to `audioDirectory`, for the page to take: { url, path, bytes, date, office, savedAt }.
    func learnTrack(_ track: [String: Any]) {
        guard let url = track["url"] as? String else { return }
        updateLearned { learned in
            var list = learned["audio"] as? [[String: Any]] ?? []
            list.removeAll { $0["url"] as? String == url }
            list.append(track)
            learned["audio"] = list
        }
    }

    /// Whether an earlier run saved this office's track, and it waits for the page to take it.
    func hasLearnedTrack(date: String, office: String?) -> Bool {
        let tracks = learned()["audio"] as? [[String: Any]] ?? []
        return tracks.contains { track in
            guard track["date"] as? String == date, track["office"] as? String == office,
                  let path = track["path"] as? String else { return false }
            let file = audioDirectory.deletingLastPathComponent().appendingPathComponent(path)
            return fileManager.fileExists(atPath: file.path)
        }
    }

    /// Write one downloaded answer, whole or not at all.
    func putInbox(_ entry: [String: Any]) -> Bool {
        guard let key = entry["key"] as? String,
              let data = try? JSONSerialization.data(withJSONObject: entry) else { return false }
        return queue.sync {
            do {
                try data.write(to: inboxFile(key), options: .atomic)
                return true
            } catch {
                return false
            }
        }
    }

    func drain(limit: Int) -> [String: Any] {
        queue.sync {
            let files = inboxFiles()
            var entries: [[String: Any]] = []
            for file in files.prefix(limit) {
                guard let data = try? Data(contentsOf: file),
                      let entry = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
                else {
                    try? fileManager.removeItem(at: file)
                    continue
                }
                entries.append(entry)
            }
            let learned = read("learned.json")
            return [
                "entries": entries,
                "remaining": max(0, files.count - min(limit, files.count)),
                "contentVersion": learned["contentVersion"] ?? 0,
                "invalidations": learned["invalidations"] ?? [],
                "audio": learned["audio"] ?? [],
                "lastRunAt": learned["lastRunAt"] ?? NSNull(),
            ]
        }
    }

    func ack(keys: [String], invalidationsThrough: Double, audio: [String]) {
        queue.sync {
            keys.forEach { try? fileManager.removeItem(at: inboxFile($0)) }
            var learned = read("learned.json")
            let invalidations = learned["invalidations"] as? [[String: Any]] ?? []
            learned["invalidations"] = invalidations.filter {
                (($0["at"] as? NSNumber)?.doubleValue ?? 0) > invalidationsThrough
            }
            let tracks = learned["audio"] as? [[String: Any]] ?? []
            learned["audio"] = tracks.filter { !audio.contains($0["url"] as? String ?? "") }
            write("learned.json", learned)
        }
    }
}

// MARK: - A run

/// One background run; the same rules as backgroundRefresh in app/src/offline/serviceWorker.js.
actor OfflineSyncRunner {
    private static let limit = 80
    private static let concurrency = 3
    private static let maxInvalidations = 50
    private static let referenceRefresh: Double = 7 * 24 * 3600 * 1000
    private static let syncHeader = "X-Offline-Sync"

    private let store = OfflineSyncStore.shared
    private let session: URLSession = {
        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 20
        configuration.requestCachePolicy = .reloadIgnoringLocalCacheData
        configuration.urlCache = nil
        return URLSession(configuration: configuration)
    }()

    private var fetched = 0
    private var stopped = false
    /// The store's generation when this run began (see OfflineSyncStore.generation).
    private var generation = 0

    private static func now() -> Double {
        (Date().timeIntervalSince1970 * 1000).rounded()
    }

    private static func isoDay(_ date: Date) -> String {
        let parts = Calendar(identifier: .gregorian).dateComponents([.year, .month, .day], from: date)
        return String(format: "%04d-%02d-%02d", parts.year ?? 0, parts.month ?? 0, parts.day ?? 0)
    }

    /// Returns false when the run was cut short (to tell iOS the work isn't done).
    func run() async -> Bool {
        // Each run has its own session: let it go when the run ends.
        defer { session.finishTasksAndInvalidate() }
        generation = store.generation
        let state = store.state()
        guard let plan = state["plan"] as? [String: Any],
              let tasks = plan["tasks"] as? [[String: Any]], !tasks.isEmpty,
              let apiBase = plan["apiBase"] as? String, apiBase.hasPrefix("http")
        else { return true }
        let base = apiBase.hasSuffix("/") ? apiBase : apiBase + "/"

        var invalidations = state["invalidations"] as? [[String: Any]] ?? []
        invalidations += await checkContentChanges(base: base, state: state)
        if Task.isCancelled { return false }

        let now = Date()
        let today = Self.isoDay(now)
        // The next calendar day (24 hours from now isn't, on the day the clocks go back).
        let tomorrow = Self.isoDay(Calendar(identifier: .gregorian).date(byAdding: .day, value: 1, to: now) ?? now)
        let index = store.index()
        let wanted = tasks.filter { task in
            needsDownload(task, index: index, invalidations: invalidations, today: today, tomorrow: tomorrow)
        }
        var position = 0
        while position < wanted.count, fetched < Self.limit, !stopped, !Task.isCancelled {
            let batch = Array(wanted[position..<min(wanted.count, position + Self.concurrency, position + Self.limit - fetched)])
            position += batch.count
            await withTaskGroup(of: Void.self) { group in
                for task in batch {
                    group.addTask { _ = await self.download(task) }
                }
            }
        }

        if let audio = state["audio"] as? [String: Any], audio["enabled"] as? Bool == true {
            await downloadAudio(audio["tasks"] as? [[String: Any]] ?? [], base: base, today: today, tomorrow: tomorrow)
        }
        store.updateLearned { $0["lastRunAt"] = Self.now() }
        print("Offline background run downloaded \(fetched)\(stopped ? " (stopped: offline)" : "")")
        return !Task.isCancelled
    }

    // MARK: Content changes

    private func checkContentChanges(base: String, state: [String: Any]) async -> [[String: Any]] {
        let learned = store.learned()
        let known = max(
            (state["contentVersion"] as? NSNumber)?.intValue ?? 0,
            (learned["contentVersion"] as? NSNumber)?.intValue ?? 0
        )
        guard let url = URL(string: "\(base)api/v1/content_changes?since=\(known)"),
              let answer = try? await session.data(from: url),
              (answer.1 as? HTTPURLResponse)?.statusCode == 200,
              let summary = try? JSONSerialization.jsonObject(with: answer.0) as? [String: Any],
              let version = (summary["version"] as? NSNumber)?.intValue
        else {
            // The downloads go ahead anyway.
            return (learned["invalidations"] as? [[String: Any]]) ?? []
        }
        let all = summary["all"] as? Bool ?? false
        let dates = summary["dates"] as? [Any] ?? []
        var added: [[String: Any]] = []
        store.updateLearned { learned in
            var list = learned["invalidations"] as? [[String: Any]] ?? []
            if known > 0 && (all || !dates.isEmpty) {
                list.append([
                    "at": Self.now(),
                    "all": all,
                    "urgent": summary["urgent"] as? Bool ?? false,
                    "dates": dates,
                ])
                list = Array(list.suffix(Self.maxInvalidations))
            }
            learned["invalidations"] = list
            learned["contentVersion"] = max(version, known)
            added = list
        }
        return added
    }

    // MARK: What to download

    /// Same rule as app/src/offline/staleness.js: a change's dated ranges are refreshed at once; an
    /// every-date change (`all`) soon, or at once when urgent.
    private func staleness(fetchedAt: Double, kind: String?, date: String?, invalidations: [[String: Any]]) -> String? {
        var result: String?
        for change in invalidations {
            guard let at = (change["at"] as? NSNumber)?.doubleValue, at > fetchedAt else { continue }
            if let date {
                let end = kind == "month" ? monthEnd(date) : date
                let ranges = change["dates"] as? [[String]] ?? []
                if ranges.contains(where: { $0.count == 2 && $0[0] <= end && $0[1] >= date }) { return "hard" }
            }
            guard change["all"] as? Bool == true else { continue }
            if change["urgent"] as? Bool == true { return "hard" }
            result = "soft"
        }
        return result
    }

    private func monthEnd(_ first: String) -> String {
        let parts = first.split(separator: "-").compactMap { Int($0) }
        guard parts.count >= 2,
              let start = Calendar(identifier: .gregorian).date(from: DateComponents(year: parts[0], month: parts[1], day: 1)),
              let days = Calendar(identifier: .gregorian).range(of: .day, in: .month, for: start)
        else { return first }
        return String(format: "%04d-%02d-%02d", parts[0], parts[1], days.count)
    }

    private func needsDownload(_ task: [String: Any], index: [String: Double], invalidations: [[String: Any]], today: String, tomorrow: String) -> Bool {
        guard let key = task["key"] as? String, task["url"] is String else { return false }
        let kind = task["kind"] as? String
        let date = task["date"] as? String
        if let date {
            if kind == "month" {
                if date.prefix(7) < today.prefix(7) { return false }
            } else if date < today {
                return false
            }
        }
        guard let fetchedAt = index[key] else { return true }
        switch staleness(fetchedAt: fetchedAt, kind: kind, date: date, invalidations: invalidations) {
        case nil:
            return false
        case "hard":
            return true
        default:
            guard let date else { return Self.now() - fetchedAt > Self.referenceRefresh }
            if kind == "month" { return date.prefix(7) == today.prefix(7) }
            return date <= tomorrow
        }
    }

    // MARK: Downloads

    private func request(_ url: URL) -> URLRequest {
        var request = URLRequest(url: url)
        // Not a view: the API doesn't count these (analytics/middleware.py).
        request.setValue("1", forHTTPHeaderField: Self.syncHeader)
        return request
    }

    /// A finished track: "preparing" answers aren't kept (keepable in app/src/offline/cacheAdapter.js).
    private static func hasTrack(_ body: Any) -> Bool {
        guard let audio = (body as? [String: Any])?["audio"] as? [String: Any],
              audio["status"] as? String != "preparing",
              let single = audio["single_track"] as? [Any] else { return false }
        return !single.isEmpty
    }

    /// Download one answer into the inbox. Returns its parsed body (an object or a list). Audio
    /// answers are only kept once their track is ready.
    @discardableResult
    private func download(_ task: [String: Any]) async -> Any? {
        guard let address = task["url"] as? String, let key = task["key"] as? String,
              let url = URL(string: address) else { return nil }
        do {
            let (data, response) = try await session.data(for: request(url))
            guard (response as? HTTPURLResponse)?.statusCode == 200,
                  let body = try? JSONSerialization.jsonObject(with: data),
                  body is [String: Any] || body is [Any],
                  task["kind"] as? String != "audio" || Self.hasTrack(body),
                  let text = String(data: data, encoding: .utf8)
            else { return nil }
            // The downloads were removed while this was on its way.
            guard store.generation == generation else {
                stopped = true
                return nil
            }
            let fetchedAt = Self.now()
            let saved = store.putInbox([
                "key": key,
                "url": address,
                "kind": task["kind"] ?? NSNull(),
                "date": task["date"] ?? NSNull(),
                "profile": task["profile"] ?? NSNull(),
                "fetchedAt": fetchedAt,
                "body": text,
            ])
            guard saved else { return nil }
            store.setIndex(key, fetchedAt)
            fetched += 1
            return body
        } catch {
            // Offline again, or out of time: the next run tries again.
            print("Offline download failed: \(error)")
            stopped = true
            return nil
        }
    }

    /// FNV-1a, base 36: the same as hashString in app/src/offline/keys.js.
    static func hashString(_ value: String) -> String {
        var hash: UInt32 = 0x811c_9dc5
        for unit in value.utf16 {
            hash ^= UInt32(unit)
            hash = hash &* 0x0100_0193
        }
        return String(hash, radix: 36)
    }

    /// The API's track address, as resolveAudioUrl in app/src/helpers/officeAudio.js makes it.
    private func resolveTrack(_ raw: String, base: String) -> String {
        let path = URLComponents(string: raw)?.percentEncodedPath ?? raw
        let trimmedBase = base.hasSuffix("/") ? String(base.dropLast()) : base
        let trimmedPath = path.hasPrefix("/") ? String(path.dropFirst()) : path
        return "\(trimmedBase)/\(trimmedPath)"
    }

    private func downloadAudio(_ tasks: [[String: Any]], base: String, today: String, tomorrow: String) async {
        let fileManager = FileManager.default
        try? fileManager.createDirectory(at: store.audioDirectory, withIntermediateDirectories: true)
        for task in tasks {
            if stopped || Task.isCancelled || fetched >= Self.limit { return }
            guard let date = task["date"] as? String, date >= today, date <= tomorrow,
                  task["track"] as? String == nil else { continue }
            // Saved by an earlier run; the page hasn't taken it yet.
            if store.hasLearnedTrack(date: date, office: task["office"] as? String) { continue }
            guard let body = await download(task) as? [String: Any],
                  let audio = body["audio"] as? [String: Any],
                  // [url, file path, chapters, timings, ...]: only the first is wanted.
                  let raw = (audio["single_track"] as? [Any])?.first as? String
            else { continue }
            let track = resolveTrack(raw, base: base)
            let name = "\(Self.hashString(track)).mp3"
            let file = store.audioDirectory.appendingPathComponent(name)
            // Only the path: the app's folder moves when the app is updated (app/src/offline/audio.js).
            var record: [String: Any] = [
                "url": track,
                "path": "offline-audio/\(name)",
                "date": date,
                "office": task["office"] ?? NSNull(),
            ]
            guard store.generation == generation else { return }
            if fileManager.fileExists(atPath: file.path) {
                record["bytes"] = (try? fileManager.attributesOfItem(atPath: file.path)[.size] as? NSNumber)?.intValue ?? 0
                record["savedAt"] = Self.now()
                store.learnTrack(record)
            } else if let url = URL(string: track) {
                record["name"] = name
                await OfflineAudioDownloads.shared.start(request(url), track: record)
            }
        }
    }
}

// MARK: - Audio

/// Office audio downloads in a background URLSession. A track can be 30 MB, more than a refresh task
/// (about 30 seconds) can fetch on a slow connection; iOS finishes background transfers on its own
/// time, waking the app (AppDelegate's handleEventsForBackgroundURLSession) to file them.
final class OfflineAudioDownloads: NSObject, URLSessionDownloadDelegate {
    static let shared = OfflineAudioDownloads()
    static let identifier = "com.dailyoffice.dailyoffice2019.offline-audio"

    /// iOS's handler from a relaunch to finish downloads: called once they're filed.
    var backgroundCompletion: (() -> Void)?

    private lazy var session: URLSession = {
        let configuration = URLSessionConfiguration.background(withIdentifier: Self.identifier)
        configuration.sessionSendsLaunchEvents = true
        configuration.isDiscretionary = false
        return URLSession(configuration: configuration, delegate: self, delegateQueue: nil)
    }()

    /// Open the session again after a relaunch, so iOS can hand over what finished.
    func reconnect() {
        _ = session
    }

    /// Download a track, unless it is on its way already. `track` is what the page is told once
    /// the file is saved, plus its file `name`.
    func start(_ request: URLRequest, track: [String: Any]) async {
        let pending = await session.allTasks
        if pending.contains(where: { $0.originalRequest?.url == request.url }) { return }
        guard let description = try? JSONSerialization.data(withJSONObject: track) else { return }
        let task = session.downloadTask(with: request)
        task.taskDescription = String(data: description, encoding: .utf8)
        task.resume()
    }

    func cancelAll() {
        session.getAllTasks { tasks in tasks.forEach { $0.cancel() } }
    }

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask, didFinishDownloadingTo location: URL) {
        // The file at `location` is deleted when this returns: move it now.
        let fileManager = FileManager.default
        let store = OfflineSyncStore.shared
        guard (downloadTask.response as? HTTPURLResponse)?.statusCode == 200,
              let description = downloadTask.taskDescription?.data(using: .utf8),
              var track = (try? JSONSerialization.jsonObject(with: description)) as? [String: Any],
              let name = track.removeValue(forKey: "name") as? String,
              store.hasPlan
        else { return }
        let size = ((try? fileManager.attributesOfItem(atPath: location.path))?[.size] as? NSNumber)?.intValue ?? 0
        guard size > 0 else { return }
        let file = store.audioDirectory.appendingPathComponent(name)
        do {
            try fileManager.createDirectory(at: store.audioDirectory, withIntermediateDirectories: true)
            try? fileManager.removeItem(at: file)
            try fileManager.moveItem(at: location, to: file)
        } catch {
            print("Offline audio could not be saved: \(error)")
            return
        }
        track["bytes"] = size
        track["savedAt"] = (Date().timeIntervalSince1970 * 1000).rounded()
        store.learnTrack(track)
    }

    func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: Error?) {
        if let error, (error as? URLError)?.code != .cancelled {
            // The next run asks again.
            print("Offline audio download failed: \(error)")
        }
    }

    func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
        DispatchQueue.main.async {
            self.backgroundCompletion?()
            self.backgroundCompletion = nil
        }
    }
}
