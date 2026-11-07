import Foundation

/// Finds an office's (or the readings') audio track without the page, for CarPlay.
///
/// The request must be exactly the one the page would make, so it gets the same track (the same
/// cached clips, never newly generated audio) for the listener's settings and extra collects. The
/// page saves its addresses as templates (app/src/helpers/nativeAudioRequests.js); before it has,
/// the address is built here the same way from the settings it saved. The API answers with the
/// track, or that it is still being prepared (as the page's officeAudio.js handles), and a track
/// downloaded for offline listening plays from the phone.
enum OfficeAudioResolver {
    enum Request: Hashable {
        case office(Office)
        case readings(ReadingsService)

        var title: String {
            switch self {
            case .office(let office): return office.title
            case .readings(let service): return "Readings for \(service.title)"
            }
        }
    }

    struct Track {
        let url: URL
        let title: String
    }

    enum Failure: LocalizedError {
        case noAudio
        case unreachable
        case stillPreparing

        var errorDescription: String? {
            switch self {
            case .noAudio:
                return "Audio isn’t available for these settings. It is read in English, for the ESV and KJV."
            case .unreachable:
                return "The Daily Office couldn’t reach its audio. Check the connection and try again."
            case .stillPreparing:
                return "This audio is still being prepared. Try again in a minute."
            }
        }
    }

    static let api = "https://api.dailyoffice2019.com/"
    private static let preparingLimit: TimeInterval = 90

    /// The day an office is prayed: before 4 a.m., Compline and the Close of Day are still the
    /// night before's (as the app's home page has it).
    static func day(for request: Request, at now: Date = Date(), calendar: Calendar = .current) -> Date {
        guard case .office(let office) = request,
              [.compline, .familyCloseOfDay].contains(office),
              calendar.component(.hour, from: now) < 4
        else { return now }
        return calendar.date(byAdding: .day, value: -1, to: now) ?? now
    }

    static func resolve(_ request: Request, at now: Date = Date()) async throws -> Track {
        let date = day(for: request, at: now)
        guard let address = URL(string: requestAddress(request, date: date)) else { throw Failure.noAudio }
        let giveUpAt = Date().addingTimeInterval(preparingLimit)
        var failures = 0
        while true {
            let audio: [String: Any]
            do {
                audio = try await fetchAudio(address)
            } catch Failure.noAudio {
                throw Failure.noAudio
            } catch {
                failures += 1
                if failures > 2 { throw Failure.unreachable }
                try await Task.sleep(nanoseconds: UInt64(failures) * 2_000_000_000)
                continue
            }
            if audio["status"] as? String == "preparing" {
                guard Date() < giveUpAt else { throw Failure.stillPreparing }
                let wait = min(max((audio["retry_after"] as? Double) ?? 5, 2), 30)
                try await Task.sleep(nanoseconds: UInt64(wait * 1_000_000_000))
                continue
            }
            guard let single = audio["single_track"] as? [Any], let raw = single.first as? String,
                  let track = trackURL(raw)
            else { throw Failure.noAudio }
            return Track(url: storedFile(for: track) ?? track, title: request.title)
        }
    }

    private static func fetchAudio(_ address: URL) async throws -> [String: Any] {
        var request = URLRequest(url: address)
        request.timeoutInterval = 30
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw Failure.unreachable }
        if (400..<500).contains(http.statusCode) { throw Failure.noAudio }
        guard http.statusCode == 200 || http.statusCode == 202,
              let object = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        else { throw Failure.unreachable }
        return object["audio"] as? [String: Any] ?? [:]
    }

    // MARK: - The page's addresses

    /// The address the page asks for this request's audio with, for this day.
    static func requestAddress(_ request: Request, date: Date) -> String {
        let day = CalendarAPI.apiDate(date)
        let templates = savedTemplates()
        switch request {
        case .office(let office):
            let key = "\(office.serviceType)/\(office.slug)"
            let template = (templates?["offices"] as? [String: String])?[key] ?? fallbackOfficeTemplate(office)
            return template.replacingOccurrences(of: "{date}", with: day)
        case .readings(let service):
            let template = templates?["readings"] as? String ?? fallbackReadingsTemplate()
            return template
                .replacingOccurrences(of: "{kind}", with: service.slug)
                .replacingOccurrences(of: "{date}", with: day)
        }
    }

    private static func stored(_ key: String) -> String? {
        UserDefaults.standard.string(forKey: "CapacitorStorage.\(key)")
    }

    private static func savedTemplates() -> [String: Any]? {
        guard let json = stored("nativeAudioRequests"), let data = json.data(using: .utf8) else { return nil }
        return try? JSONSerialization.jsonObject(with: data) as? [String: Any]
    }

    /// The saved settings as the page wrote them, in their order (the query lists them in it).
    static func orderedSettings(_ json: String?) -> [(String, String)] {
        guard let json else { return [] }
        let pattern = #""((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)""#
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return [] }
        let range = NSRange(json.startIndex..., in: json)
        return regex.matches(in: json, range: range).compactMap { match in
            guard let key = Range(match.range(at: 1), in: json), let value = Range(match.range(at: 2), in: json) else {
                return nil
            }
            return (String(json[key]), String(json[value]))
        }
    }

    /// As app/src/offline/urls.js officeUrl builds it.
    static func fallbackOfficeTemplate(_ office: Office) -> String {
        var settings = orderedSettings(stored("settings"))
        if !settings.contains(where: { $0.0 == "bible_translation" && !$0.1.isEmpty }) {
            settings.removeAll { $0.0 == "bible_translation" }
            settings.append(("bible_translation", "esv"))
        }
        let query = settings.map { "\($0.0)=\($0.1)" }.joined(separator: "&")
        var collects = ""
        if office.serviceType == "office",
           let json = stored("extraCollects"), let data = json.data(using: .utf8),
           let chosen = try? JSONSerialization.jsonObject(with: data) as? [String: [Any]],
           let list = chosen[office.title] {
            collects = list.map { "\($0)" }.joined(separator: ",")
        }
        return "\(api)api/v1/\(office.serviceType)/\(office.slug)/{date}?\(query)&extra_collects=\(collects)&include_audio_links=true"
    }

    /// As the Readings page builds it.
    static func fallbackReadingsTemplate() -> String {
        let settings = Dictionary(orderedSettings(stored("settings")), uniquingKeysWith: { first, _ in first })
        var translation = stored("readings_translation") ?? ""
        if translation.isEmpty || translation == "undefined" {
            translation = settings["bible_translation"] ?? "esv"
        }
        let values = [
            ("translation", translation),
            ("psalms", stored("psalms_translation") ?? settings["language_style"] ?? "undefined"),
            ("style", stored("psalm_style") ?? settings["psalm_style"] ?? "undefined"),
            ("psalter", stored("psalter") ?? settings["psalter"] ?? "undefined"),
            ("position", "0"),
            ("include_audio_links", "true"),
        ]
        var components = URLComponents()
        components.queryItems = values.map { URLQueryItem(name: $0.0, value: $0.1) }
        return "\(api)api/v1/readings_audio/{kind}/{date}?\(components.percentEncodedQuery ?? "")"
    }

    // MARK: - The track

    /// The API names the track by its own address; play it from the API's (officeAudio.js
    /// resolveAudioUrl).
    static func trackURL(_ raw: String) -> URL? {
        guard let parsed = URL(string: raw) else { return nil }
        let path = parsed.path.hasPrefix("/") ? String(parsed.path.dropFirst()) : parsed.path
        var address = api + path
        if let query = parsed.query, !query.isEmpty { address += "?\(query)" }
        return URL(string: address)
    }

    /// A track downloaded for offline listening (app/src/offline/audio.js): under
    /// Library/NoCloud/offline-audio, named by the hash of its address without "reload".
    static func storedFile(for track: URL) -> URL? {
        guard var components = URLComponents(url: track, resolvingAgainstBaseURL: false) else { return nil }
        let kept = (components.queryItems ?? []).filter { $0.name != "reload" }
        components.queryItems = kept.isEmpty ? nil : kept
        guard let key = components.url?.absoluteString,
              let library = FileManager.default.urls(for: .libraryDirectory, in: .userDomainMask).first
        else { return nil }
        let file = library.appendingPathComponent("NoCloud/offline-audio/\(hashString(key)).mp3")
        return FileManager.default.fileExists(atPath: file.path) ? file : nil
    }

    /// FNV-1a over UTF-16 code units, in base 36: app/src/offline/keys.js hashString.
    static func hashString(_ value: String) -> String {
        var hash: UInt32 = 0x811C_9DC5
        for unit in value.utf16 {
            hash ^= UInt32(unit)
            hash = hash &* 0x0100_0193
        }
        return String(hash, radix: 36)
    }
}
