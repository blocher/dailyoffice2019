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

    /// Short words people use for it, for Siri to match.
    var synonyms: [String] {
        switch self {
        case .morningPrayer: return ["Matins", "Morning Office", "Daily Morning Prayer"]
        case .middayPrayer: return ["Noonday Prayer", "Midday Office", "Daily Midday Prayer"]
        case .eveningPrayer: return ["Evensong", "Vespers", "Evening Office", "Daily Evening Prayer"]
        case .compline: return ["Night Prayer", "Bedtime Prayer", "Prayer at the End of the Day"]
        case .familyMorning: return ["Family Morning Prayer", "Morning Family Prayer"]
        case .familyMidday: return ["Family Midday Prayer", "Family Noonday Prayer"]
        case .familyEarlyEvening: return ["Family Evening Prayer", "Family Early Evening Prayer", "Family Supper Prayer"]
        case .familyCloseOfDay: return ["Family Bedtime Prayer", "Family Night Prayer", "Family Compline", "Close of Day"]
        }
    }

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
