import Intents
import UIKit

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
        let track = try await OfficeAudioResolver.resolve(request)
        let player = OfficePlayer.shared
        player.setSource(
            track.url.absoluteString,
            title: track.title,
            artist: "The Daily Office",
            artworkPath: "android-chrome-512x512.png",
            rate: nil
        )
        try player.play()
        current = request
        currentSource = track.url.absoluteString
        return track
    }

    /// Plays, answering within a few seconds for Siri, and keeps the app awake until the track
    /// has started even when that takes longer.
    static func start(_ request: OfficeAudioResolver.Request) async -> Outcome {
        let application = UIApplication.shared
        var task = UIBackgroundTaskIdentifier.invalid
        task = application.beginBackgroundTask(withName: "Play \(request.title)") {
            application.endBackgroundTask(task)
            task = .invalid
        }
        let playing = Task { @MainActor () -> Error? in
            defer {
                if task != .invalid {
                    application.endBackgroundTask(task)
                    task = .invalid
                }
            }
            do {
                try await play(request)
                return nil
            } catch {
                return error
            }
        }
        let answer = await withTaskGroup(of: Outcome?.self) { group -> Outcome in
            group.addTask {
                if let error = await playing.value { return .failed(error) }
                return .playing(request.title)
            }
            group.addTask {
                try? await Task.sleep(nanoseconds: UInt64(answerWithin * 1_000_000_000))
                return nil
            }
            let first = await group.next() ?? nil
            group.cancelAll()
            return first ?? .starting(request.title)
        }
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

// MARK: - Siri's media requests

/// "Play Midday Prayer on The Daily Office", "Play The Daily Office", and the same in CarPlay:
/// Siri sends these to media apps as INPlayMediaIntent rather than to the App Shortcuts. Handled
/// in the app (AppDelegate application(_:handlerFor:)); playback starts in
/// application(_:handle:completionHandler:), where iOS lets a background app start audio.
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
            guard let request = Self.request(for: intent) else {
                completion([INPlayMediaMediaItemResolutionResult.unsupported()])
                return
            }
            completion(INPlayMediaMediaItemResolutionResult.successes(with: [Self.mediaItem(for: request)]))
        }
    }

    func handle(intent: INPlayMediaIntent, completion: @escaping (INPlayMediaIntentResponse) -> Void) {
        // iOS starts (or wakes) the app in the background and calls
        // application(_:handle:completionHandler:), where it may start audio.
        completion(INPlayMediaIntentResponse(code: .handleInApp, userActivity: nil))
    }

    /// From AppDelegate application(_:handle:completionHandler:).
    @MainActor
    static func play(_ intent: INPlayMediaIntent, completion: @escaping (INPlayMediaIntentResponse) -> Void) {
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
                print("Siri could not play \(request.title): \(error.localizedDescription)")
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
