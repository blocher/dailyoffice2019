import Intents
import os
import UIKit

/// Voice requests in the device log (Console), and in Library/Caches/voice-log.txt for copying off
/// a test phone (`xcrun devicectl device copy from --domain-type appDataContainer …`): what Siri
/// asked for and what happened, for diagnosing requests that go astray.
enum VoiceLog {
    private static let logger = Logger(subsystem: "com.dailyoffice.dailyoffice2019", category: "Voice")
    private static let queue = DispatchQueue(label: "VoiceLog")
    private static let file: URL? = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first?
        .appendingPathComponent("voice-log.txt")

    static func note(_ message: String) {
        logger.notice("\(message)")
        let line = "\(ISO8601DateFormatter().string(from: Date())) \(message)\n"
        queue.async {
            guard let file, let data = line.data(using: .utf8) else { return }
            if let handle = try? FileHandle(forWritingTo: file) {
                handle.seekToEndOfFile()
                handle.write(data)
                try? handle.close()
            } else {
                try? data.write(to: file)
            }
        }
    }
}

/// Plays an office (or the readings) straight from Siri, CarPlay, the lock screen or a headset,
/// without opening the page, so it works with the phone locked in a car.
///
/// Every path ends here: CarPlay's lists (Car/CarPlaySceneDelegate.swift), the App Intents
/// (PlayOfficeIntent and PlayReadingsIntent, which are AudioPlaybackIntents), Siri's media
/// requests ("Play Midday Prayer on The Daily Office", an INPlayMediaIntent; see
/// PlayMediaIntentHandler below), and Play pressed with nothing queued (OfficePlayer). The track
/// is found as the page would find it (Car/OfficeAudioResolver.swift), so it is always audio the
/// server already has or is preparing for these settings, never newly generated audio.
@MainActor
enum OfficePlayback {
    /// What was last started here, while the player still has its track.
    private(set) static var current: OfficeAudioResolver.Request?
    private(set) static var currentSource: String?

    enum Outcome {
        /// Playing (or about to: the player is loading the track).
        case playing(String)
        /// Still finding the track (the server may be preparing it); it plays once found.
        case starting(String)
        case failed(Error)
    }

    /// How long Siri waits for an answer before we say "starting" and carry on in the background.
    private static let answerWithin: TimeInterval = 8

    /// Finds the track and plays it.
    @discardableResult
    static func play(_ request: OfficeAudioResolver.Request) async throws -> OfficeAudioResolver.Track {
        VoiceLog.note("Finding audio for \(request.title)")
        let track: OfficeAudioResolver.Track
        do {
            track = try await OfficeAudioResolver.resolve(request)
        } catch {
            VoiceLog.note("No audio for \(request.title): \(error.localizedDescription)")
            throw error
        }
        VoiceLog.note("Playing \(track.url.absoluteString)")
        let player = OfficePlayer.shared
        player.setSource(
            track.url.absoluteString,
            title: track.title,
            artist: "The Daily Office",
            artworkPath: "android-chrome-512x512.png",
            rate: nil
        )
        player.voiceStartedAt = Date()
        try player.play()
        current = request
        currentSource = track.url.absoluteString
        // With the app on screen, show what's playing too. The page asks for the same track and the
        // one player keeps it going (?autoplay=1 only makes sure the page shows it playing).
        if UIApplication.shared.applicationState == .active {
            VoiceLaunch.open(path: VoiceLinks.adding(autoplay: true, to: request.path))
        }
        return track
    }

    /// Plays, answering within a few seconds for Siri, and keeps the app awake until the track
    /// has started even when that takes longer.
    /// How long to keep the app awake for the track to become audible: until then iOS may suspend
    /// a background app (as Siri leaves it), and the office never starts.
    private static let audibleWithin: TimeInterval = 90

    static func start(_ request: OfficeAudioResolver.Request) async -> Outcome {
        let application = UIApplication.shared
        var task = UIBackgroundTaskIdentifier.invalid
        task = application.beginBackgroundTask(withName: "Play \(request.title)") {
            application.endBackgroundTask(task)
            task = .invalid
        }
        var failure: Error?
        var loaded = false
        // Find and load the track, then hold the app awake until it is actually heard (audio
        // playing keeps a background app running from then on).
        Task { @MainActor in
            defer {
                if task != .invalid {
                    application.endBackgroundTask(task)
                    task = .invalid
                }
            }
            do {
                try await play(request)
                loaded = true
                let giveUpAt = Date().addingTimeInterval(audibleWithin)
                while !OfficePlayer.shared.isAudible, Date() < giveUpAt {
                    try? await Task.sleep(nanoseconds: 250_000_000)
                }
                VoiceLog.note("\(request.title) audible: \(OfficePlayer.shared.isAudible)")
            } catch {
                failure = error
            }
        }
        // Answer Siri once it's heard, or failed, or after a few seconds (it carries on).
        let answerBy = Date().addingTimeInterval(answerWithin)
        var answer: Outcome = .starting(request.title)
        while Date() < answerBy {
            if let failure {
                answer = .failed(failure)
                break
            }
            if loaded, OfficePlayer.shared.isAudible {
                answer = .playing(request.title)
                break
            }
            try? await Task.sleep(nanoseconds: 200_000_000)
        }
        VoiceLog.note("Start \(request.title): \(String(describing: answer))")
        return answer
    }

    /// The office for this time of day, Daily Office or Family Prayer as the listener last
    /// prayed (Play pressed with nothing queued).
    static func playNow() {
        let office = Office.current(family: AppPreferences.prefersFamilyPrayer)
        Task { _ = await start(.office(office)) }
    }

    /// What a spoken request names, for the listener's settings and the time now; nil if it
    /// isn't something the app has.
    static func request(for words: String?, at date: Date = Date()) -> OfficeAudioResolver.Request? {
        switch VoiceWords.match(words, prefersFamily: AppPreferences.prefersFamilyPrayer, at: date) {
        case .office(let office): return .office(office)
        case .readings(let service): return .readings(service)
        case nil: return nil
        }
    }
}

extension OfficeAudioResolver.Request {
    /// The app's page for it.
    var path: String {
        switch self {
        case .office(let office): return office.path
        case .readings(let service): return service.path
        }
    }
}

// MARK: - Siri's media requests

/// "Play Midday Prayer on The Daily Office", "Play The Daily Office", and the same in CarPlay:
/// Siri sends these to media apps as INPlayMediaIntent rather than to the App Shortcuts. Handled
/// in the app (AppDelegate application(_:handlerFor:)), which plays straight away in handle().
final class PlayMediaIntentHandler: NSObject, INPlayMediaIntentHandling {
    private static let officePrefix = "office:"
    private static let readingsPrefix = "readings:"

    /// The words Siri heard, from wherever it put them.
    static func words(in intent: INPlayMediaIntent) -> String {
        var parts: [String] = []
        if let search = intent.mediaSearch {
            parts += [search.mediaName, search.albumName, search.artistName].compactMap { $0 }
            parts += search.genreNames ?? []
            parts += search.moodNames ?? []
        }
        if parts.isEmpty {
            parts += (intent.mediaItems ?? []).compactMap(\.title)
        }
        return parts.joined(separator: " ")
    }

    static func identifier(for request: OfficeAudioResolver.Request) -> String {
        switch request {
        case .office(let office): return officePrefix + office.rawValue
        case .readings(let service): return readingsPrefix + service.rawValue
        }
    }

    /// The request a resolved intent carries, or what its words name.
    @MainActor
    static func request(for intent: INPlayMediaIntent) -> OfficeAudioResolver.Request? {
        if let identifier = intent.mediaItems?.first?.identifier {
            if identifier.hasPrefix(officePrefix), let office = Office(rawValue: String(identifier.dropFirst(officePrefix.count))) {
                return .office(office)
            }
            if identifier.hasPrefix(readingsPrefix),
               let service = ReadingsService(rawValue: String(identifier.dropFirst(readingsPrefix.count))) {
                return .readings(service)
            }
        }
        return OfficePlayback.request(for: words(in: intent))
    }

    static func mediaItem(for request: OfficeAudioResolver.Request) -> INMediaItem {
        INMediaItem(
            identifier: identifier(for: request),
            title: request.title,
            type: .podcastEpisode,
            artwork: nil,
            artist: "The Daily Office"
        )
    }

    func resolveMediaItems(for intent: INPlayMediaIntent, with completion: @escaping ([INPlayMediaMediaItemResolutionResult]) -> Void) {
        Task { @MainActor in
            let request = Self.request(for: intent)
            VoiceLog.note("Media request words: \"\(Self.words(in: intent))\" → \(request?.title ?? "nothing")")
            guard let request else {
                completion([INPlayMediaMediaItemResolutionResult.unsupported()])
                return
            }
            completion(INPlayMediaMediaItemResolutionResult.successes(with: [Self.mediaItem(for: request)]))
        }
    }

    func handle(intent: INPlayMediaIntent, completion: @escaping (INPlayMediaIntentResponse) -> Void) {
        // Handled here, in the app Siri woke: answering .handleInApp instead relies on iOS calling
        // application(_:handle:completionHandler:), which it doesn't for this scene-based app.
        VoiceLog.note("Media request handle")
        Task { @MainActor in Self.play(intent, completion: completion) }
    }

    /// Plays what a media request asks for (and from AppDelegate application(_:handle:…), should
    /// iOS deliver one there).
    @MainActor
    static func play(_ intent: INPlayMediaIntent, completion: @escaping (INPlayMediaIntentResponse) -> Void) {
        VoiceLog.note("Media request in app: \"\(words(in: intent))\"")
        // "Resume" with nothing named: carry on with an office paused a little while ago.
        let player = OfficePlayer.shared
        if words(in: intent).isEmpty, intent.mediaItems?.isEmpty ?? true, !player.nothingToResume {
            do {
                try player.play()
                completion(INPlayMediaIntentResponse(code: .success, userActivity: nil))
            } catch {
                completion(INPlayMediaIntentResponse(code: .failure, userActivity: nil))
            }
            return
        }
        guard let request = request(for: intent) else {
            completion(INPlayMediaIntentResponse(code: .failureUnknownMediaType, userActivity: nil))
            return
        }
        Task { @MainActor in
            switch await OfficePlayback.start(request) {
            case .playing, .starting:
                completion(INPlayMediaIntentResponse(code: .success, userActivity: nil))
            case .failed(let error):
                completion(INPlayMediaIntentResponse(code: .failure, userActivity: nil))
            }
        }
    }
}

// MARK: - Words for Siri

/// Teaches Siri the offices' names as media titles, so "Play Compline on The Daily Office" is
/// heard as Compline. (Siri's own App Shortcut phrases are in VoiceIntents.swift.)
enum VoiceVocabulary {
    static func register() {
        var names: [String] = []
        for office in [Office.morningPrayer, .middayPrayer, .eveningPrayer, .compline] + Office.allCases {
            for name in [office.title] + office.synonyms where !names.contains(name) {
                names.append(name)
            }
        }
        names += ["Today’s Readings", "The Readings", "The Daily Office"]
        let vocabulary = INVocabulary.shared()
        vocabulary.setVocabularyStrings(NSOrderedSet(array: names), of: .mediaShowTitle)
        vocabulary.setVocabularyStrings(NSOrderedSet(array: names), of: .mediaPlaylistTitle)
    }
}
