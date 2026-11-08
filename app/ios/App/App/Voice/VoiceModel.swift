import Foundation

/// What Siri can open, play, and answer, shared by the App Intents (VoiceIntents.swift) and the
/// page bridge (VoiceLaunchPlugin.swift). Nothing here needs iOS 16, so the iOS 15 fallbacks
/// (Siri Suggestions from NSUserActivity, links into the app) use it too.
///
/// Siri opens the app at one of its own pages; the page plays the audio (app/src/helpers/voice.js).
/// Questions ("what feast is today?") are answered from the same calendar API the app reads,
/// without opening the app.

/// One of the eight offices, daily or family.
enum Office: String, CaseIterable {
    case morningPrayer
    case middayPrayer
    case eveningPrayer
    case compline
    case familyMorning
    case familyMidday
    case familyEarlyEvening
    case familyCloseOfDay

    var serviceType: String {
        switch self {
        case .morningPrayer, .middayPrayer, .eveningPrayer, .compline: return "office"
        default: return "family"
        }
    }

    /// The office's name in the app's addresses and the API.
    var slug: String {
        switch self {
        case .morningPrayer, .familyMorning: return "morning_prayer"
        case .middayPrayer, .familyMidday: return "midday_prayer"
        case .eveningPrayer: return "evening_prayer"
        case .compline: return "compline"
        case .familyEarlyEvening: return "early_evening_prayer"
        case .familyCloseOfDay: return "close_of_day_prayer"
        }
    }

    /// As the app titles it (Office.vue).
    var title: String {
        switch self {
        case .morningPrayer: return "Morning Prayer"
        case .middayPrayer: return "Midday Prayer"
        case .eveningPrayer: return "Evening Prayer"
        case .compline: return "Compline"
        case .familyMorning: return "Family Prayer in the Morning"
        case .familyMidday: return "Family Prayer at Midday"
        case .familyEarlyEvening: return "Family Prayer in the Early Evening"
        case .familyCloseOfDay: return "Family Prayer at the Close of Day"
        }
    }

    /// Other names people use for it (VoiceWords has every word the matcher knows).
    var synonyms: [String] { VoiceWords.synonyms[self] ?? [] }

    /// The app's page for this office today.
    var path: String { "/\(serviceType)/\(slug)" }

    static func find(serviceType: String, slug: String) -> Office? {
        allCases.first { $0.serviceType == serviceType && $0.slug == slug }
    }

    /// The office for this time of day, as the app's home page chooses it (Today.vue): before 4 a.m.
    /// still the night before, then morning until 11, midday until 3, evening until 8.
    static func current(family: Bool, at date: Date = Date(), calendar: Calendar = .current) -> Office {
        let hour = calendar.component(.hour, from: date)
        switch hour {
        case 4..<11: return family ? .familyMorning : .morningPrayer
        case 11..<15: return family ? .familyMidday : .middayPrayer
        case 15..<20: return family ? .familyEarlyEvening : .eveningPrayer
        default: return family ? .familyCloseOfDay : .compline
        }
    }
}

/// Which readings: the offices' or the Eucharist's (the Readings page's tabs).
enum ReadingsService: String, CaseIterable {
    case morningPrayer
    case eveningPrayer
    case holyEucharist

    var slug: String {
        switch self {
        case .morningPrayer: return "morning_prayer"
        case .eveningPrayer: return "evening_prayer"
        case .holyEucharist: return "holy_eucharist"
        }
    }

    var title: String {
        switch self {
        case .morningPrayer: return "Morning Prayer"
        case .eveningPrayer: return "Evening Prayer"
        case .holyEucharist: return "Holy Eucharist"
        }
    }

    var path: String { "/readings/\(slug)/" }
}

/// The listener's settings, as the page saved them with Capacitor Preferences
/// (app/src/helpers/storage.js), which keeps them in UserDefaults under "CapacitorStorage.".
enum AppPreferences {
    private static func string(_ key: String) -> String? {
        UserDefaults.standard.string(forKey: "CapacitorStorage.\(key)")
    }

    /// The settings object (bible_translation, psalter, ...), or empty.
    static var settings: [String: String] {
        guard let json = string("settings"), let data = json.data(using: .utf8),
              let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any]
        else { return [:] }
        return object.compactMapValues { value in
            if let text = value as? String { return text }
            if let number = value as? NSNumber { return number.stringValue }
            return nil
        }
    }

    /// Whether the listener last prayed Family Prayer rather than the Daily Office.
    static var prefersFamilyPrayer: Bool { string("serviceType") == "family" }
}

/// Builds the addresses the app opens at (helpers/voice.js reads them back).
enum VoiceLinks {
    static let scheme = "dailyoffice2019"
    static let website = URL(string: "https://www.dailyoffice2019.com")!

    static func url(path: String, autoplay: Bool = false) -> URL {
        var components = URLComponents()
        components.scheme = scheme
        components.host = "open"
        components.path = path.hasPrefix("/") ? path : "/\(path)"
        if autoplay { components.queryItems = [URLQueryItem(name: "autoplay", value: "1")] }
        return components.url ?? URL(string: "\(scheme)://open/")!
    }

    /// The same page on the website, for Handoff and Spotlight.
    static func webURL(path: String) -> URL {
        URL(string: path, relativeTo: website)?.absoluteURL ?? website
    }

    /// The app page a link names: dailyoffice2019://open/office/compline?autoplay=1 or
    /// https://www.dailyoffice2019.com/office/compline.
    static func path(from url: URL) -> String? {
        if url.scheme == scheme {
            var path = url.host == "open" || url.host == nil ? url.path : "/\(url.host!)\(url.path)"
            if path.isEmpty { path = "/" }
            if let query = url.query, !query.isEmpty { path += "?\(query)" }
            return path
        }
        if ["https", "http"].contains(url.scheme ?? ""), url.host?.hasSuffix("dailyoffice2019.com") == true {
            return url.path.isEmpty ? "/" : url.path
        }
        return nil
    }

    static func adding(autoplay: Bool, to path: String) -> String {
        guard autoplay else { return path }
        return path + (path.contains("?") ? "&" : "?") + "autoplay=1"
    }
}

/// A psalm from the bundled list (Psalms.json, written by app/scripts/build-voice-psalms.mjs).
struct PsalmInfo: Decodable, Hashable {
    let number: Int
    let latinTitle: String
    let topics: [String]

    enum CodingKeys: String, CodingKey {
        case number
        case latinTitle = "latin_title"
        case topics
    }

    var title: String { "Psalm \(number)" }
    var path: String { "/psalm/\(number)/" }

    static let all: [PsalmInfo] = {
        guard let url = Bundle.main.url(forResource: "Psalms", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let list = try? JSONDecoder().decode([PsalmInfo].self, from: data)
        else { return (1...150).map { PsalmInfo(number: $0, latinTitle: "", topics: []) } }
        return list
    }()

    static func number(_ number: Int) -> PsalmInfo? { all.first { $0.number == number } }

    /// Psalms whose number, Latin title, or topics match the words asked for.
    static func search(_ text: String) -> [PsalmInfo] {
        let query = text.lowercased()
            .replacingOccurrences(of: "psalm", with: "")
            .trimmingCharacters(in: .whitespacesAndNewlines)
        if query.isEmpty { return all }
        if let number = Int(query) { return all.filter { $0.number == number } }
        if let number = RomanNumerals.value(of: query.uppercased()) {
            return all.filter { $0.number == number }
        }
        return all.filter { psalm in
            psalm.latinTitle.lowercased().contains(query)
                || psalm.topics.contains { $0.lowercased().contains(query) }
        }
    }
}

enum RomanNumerals {
    static func value(of text: String) -> Int? {
        let values: [Character: Int] = ["I": 1, "V": 5, "X": 10, "L": 50, "C": 100]
        guard !text.isEmpty, text.allSatisfy({ values[$0] != nil }) else { return nil }
        var total = 0
        var previous = 0
        for character in text.reversed() {
            let value = values[character]!
            total += value < previous ? -value : value
            previous = max(previous, value)
        }
        return total
    }
}

// MARK: - The words people say

/// What someone asks for by voice: an office, or the readings.
enum VoiceRequest: Equatable {
    case office(Office)
    case readings(ReadingsService)
}

/// Every word Siri, CarPlay and Shortcuts requests are matched with, in one place. The Android
/// app has the same list in voice/VoiceWords.kt; keep the two in step. (The App Shortcut phrases
/// and OfficeChoice's synonyms in VoiceIntents.swift must be written out there, as literals, for
/// Siri to read them at build time; they use these words too.)
///
/// The matcher is tolerant: it ignores the verb ("play", "pray", "read me"...), the app's name,
/// and filler, joins words speech recognition splits ("even song", "mid day"), and goes by the
/// time of day a request names. A bare time word ("evening", "bedtime prayers") follows the
/// listener's choice of the Daily Office or Family Prayer; an office's own name ("Evening
/// Prayer", "Vespers") is that office, unless the request says "family".
enum VoiceWords {
    /// What people say before the office, ignored.
    static let verbs = [
        "play", "pray", "start", "begin", "say", "read", "read to me", "read me", "listen to",
        "put on", "resume", "continue", "let's pray", "lets pray", "let us pray",
    ]

    /// The app's names, ignored (Siri may pass them on).
    static let appNames = ["the daily office", "daily office", "daily office 2019", "dailyoffice2019", "the daily office app"]

    /// Words speech recognition splits or misspells, and what they are.
    static let respellings: [(heard: String, meant: String)] = [
        ("mid day", "midday"), ("noon day", "noonday"), ("even song", "evensong"),
        ("comp line", "compline"), ("complin", "compline"), ("compleen", "compline"),
        ("complain", "compline"), ("mattins", "matins"), ("vesper", "vespers"),
        ("night time", "nighttime"), ("bed time", "bedtime"), ("evensongs", "evensong"),
    ]

    enum Hour: CaseIterable {
        case morning, midday, evening, night

        func office(family: Bool) -> Office {
            switch self {
            case .morning: return family ? .familyMorning : .morningPrayer
            case .midday: return family ? .familyMidday : .middayPrayer
            case .evening: return family ? .familyEarlyEvening : .eveningPrayer
            case .night: return family ? .familyCloseOfDay : .compline
            }
        }
    }

    /// An office's own names: the Daily Office office, unless the request says "family".
    static let officeNames: [Hour: [String]] = [
        .morning: ["morning prayer", "morning office", "matins", "lauds", "daily morning prayer"],
        .midday: ["midday prayer", "noonday prayer", "noon prayer", "noontime prayer", "midday office", "noonday", "sext", "daily midday prayer"],
        .evening: ["evening prayer", "evensong", "vespers", "evening office", "daily evening prayer"],
        .night: ["compline", "night prayer", "night office", "prayer at the end of the day", "prayers at the end of the day"],
    ]

    /// Family Prayer's own names: always Family Prayer.
    static let familyNames: [Hour: [String]] = [
        .morning: ["family morning prayer", "morning family prayer", "family prayer in the morning"],
        .midday: ["family midday prayer", "family noonday prayer", "family prayer at midday", "family prayer at noon"],
        .evening: ["family evening prayer", "family early evening prayer", "family prayer in the early evening", "family prayer in the evening", "early evening prayer", "supper prayer", "family supper prayer"],
        .night: ["family bedtime prayer", "family night prayer", "family compline", "family prayer at the close of day", "close of day", "close of the day", "close of day prayer"],
    ]

    /// A time of day alone: the listener's usual office for it.
    static let hourWords: [Hour: [String]] = [
        .morning: ["morning", "this morning", "dawn", "sunrise"],
        .midday: ["midday", "noon", "noontime", "lunchtime", "lunch"],
        .evening: ["evening", "this evening", "sunset", "supper", "dinner"],
        .night: ["bedtime", "nighttime", "night", "before bed", "end of the day", "end of day", "goodnight", "good night"],
    ]

    /// Words that ask for Family Prayer.
    static let familyWords = ["family", "families", "kids", "children", "child", "household", "little ones"]

    /// Words that ask for the readings, and which.
    static let readingsWords = ["reading", "readings", "lesson", "lessons", "lectionary", "scripture", "scriptures", "gospel", "psalms for today", "todays psalms", "the psalms", "psalms", "bible readings"]
    static let eucharistWords = ["eucharist", "mass", "communion", "gospel", "holy eucharist", "sunday", "sundays", "lords supper"]

    /// Asking for "the office" in general: the office for now.
    static let genericWords = [
        "office", "offices", "prayer", "prayers", "praying", "hours", "daily", "today",
        "todays", "tonight", "tonights", "next", "now", "current", "my", "our", "the", "a", "some", "for", "with", "in",
        "on", "at", "of", "to", "me", "us", "and", "this", "please", "time", "app", "2019",
        "it", "something", "audio", "aloud", "out", "loud", "go",
    ]

    /// Short names for Siri and Shortcuts (Office.synonyms).
    static let synonyms: [Office: [String]] = [
        .morningPrayer: ["Matins", "Lauds", "Morning Office", "Daily Morning Prayer"],
        .middayPrayer: ["Noonday Prayer", "Noon Prayer", "Midday Office", "Sext", "Daily Midday Prayer"],
        .eveningPrayer: ["Evensong", "Vespers", "Evening Office", "Daily Evening Prayer"],
        .compline: ["Night Prayer", "Night Office", "Prayer at the End of the Day"],
        .familyMorning: ["Family Morning Prayer", "Morning Family Prayer"],
        .familyMidday: ["Family Midday Prayer", "Family Noonday Prayer"],
        .familyEarlyEvening: ["Family Evening Prayer", "Family Early Evening Prayer", "Family Supper Prayer"],
        .familyCloseOfDay: ["Family Bedtime Prayer", "Family Night Prayer", "Family Compline", "Close of Day"],
    ]

    /// Lowercase words, with punctuation gone and split words joined: "Mid-day Prayer!" is
    /// "midday prayer".
    static func normalize(_ text: String) -> String {
        var lowered = text.lowercased()
            .replacingOccurrences(of: "’", with: "'")
            .replacingOccurrences(of: "‘", with: "'")
            .replacingOccurrences(of: "'s ", with: "s ")
            .replacingOccurrences(of: "'", with: "")
        lowered = String(lowered.map { $0.isLetter || $0.isNumber ? $0 : " " })
        var padded = " " + lowered.split(separator: " ").joined(separator: " ") + " "
        for (heard, meant) in respellings {
            padded = padded.replacingOccurrences(of: " \(heard) ", with: " \(meant) ")
        }
        return padded.trimmingCharacters(in: .whitespaces)
    }

    private static func has(_ text: String, _ phrase: String) -> Bool {
        (" " + text + " ").contains(" " + normalize(phrase) + " ")
    }

    private static func hasAny(_ text: String, _ phrases: [String]) -> Bool {
        phrases.contains { has(text, $0) }
    }

    /// What a request asks for, or nil if it names something the app doesn't have ("play jazz").
    /// Nothing at all, or only "the office", "my prayers", is the office for now.
    static func match(_ text: String?, prefersFamily: Bool, at date: Date = Date(), calendar: Calendar = .current) -> VoiceRequest? {
        let words = normalize(text ?? "")
        let hour = calendar.component(.hour, from: date)

        // Readings first: "the morning readings" is the readings, not Morning Prayer.
        if hasAny(words, readingsWords) || (hasAny(words, eucharistWords) && !hasAny(words, ["prayer", "office"])) {
            if hasAny(words, eucharistWords) { return .readings(.holyEucharist) }
            if hasAny(words, ["evening", "evensong", "vespers", "tonight"]) { return .readings(.eveningPrayer) }
            if hasAny(words, ["morning", "matins", "lauds"]) { return .readings(.morningPrayer) }
            return .readings(hour < 15 ? .morningPrayer : .eveningPrayer)
        }

        let family = hasAny(words, familyWords)
        // Family Prayer's own names, then the offices' names, longest first within each hour so
        // "evening prayer" beats "evening"; night before evening, so "close of day" isn't evening.
        let order: [Hour] = [.night, .evening, .midday, .morning]
        for hourOfDay in order where hasAny(words, familyNames[hourOfDay] ?? []) {
            return .office(hourOfDay.office(family: true))
        }
        for hourOfDay in order where hasAny(words, officeNames[hourOfDay] ?? []) {
            return .office(hourOfDay.office(family: family))
        }
        for hourOfDay in order where hasAny(words, hourWords[hourOfDay] ?? []) {
            return .office(hourOfDay.office(family: family || prefersFamily))
        }

        // Anything left must be the verb, the app's name, or "the office": else it's not ours.
        var rest = " " + words + " "
        for phrase in (verbs + appNames + familyWords).map(normalize).sorted(by: { $0.count > $1.count }) {
            rest = rest.replacingOccurrences(of: " \(phrase) ", with: " ")
            rest = rest.replacingOccurrences(of: " \(phrase) ", with: " ")
        }
        let generic = Set(genericWords)
        let unknown = rest.split(separator: " ").filter { !generic.contains(String($0)) }
        guard unknown.isEmpty else { return nil }
        return .office(Office.current(family: family || prefersFamily, at: date, calendar: calendar))
    }
}
