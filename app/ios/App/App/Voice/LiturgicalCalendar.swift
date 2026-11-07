import Foundation

/// The church calendar, read from the app's API for Siri's answers ("what feast is today?",
/// "what's the collect?"). The page and Cloudflare cache the same answers, so these are cheap.
/// See LiturgicalAnswers for how each answer is worded.
enum CalendarAPIError: LocalizedError {
    case unreachable
    case unexpected

    var errorDescription: String? {
        switch self {
        case .unreachable: return "The Daily Office couldn’t reach the calendar. Check your connection and try again."
        case .unexpected: return "The Daily Office couldn’t read the calendar for that day."
        }
    }
}

enum CalendarAPI {
    static let base = URL(string: "https://api.dailyoffice2019.com/api/v1/")!

    /// The API's date form: 2026-11-3 (no padding), as app/src/offline/urls.js writes it.
    static func apiDate(_ date: Date, calendar: Calendar = .current) -> String {
        let parts = calendar.dateComponents([.year, .month, .day], from: date)
        return "\(parts.year!)-\(parts.month!)-\(parts.day!)"
    }

    static func get(_ path: String, query: [String: String] = [:]) async throws -> Any {
        var components = URLComponents(url: base.appendingPathComponent(path), resolvingAgainstBaseURL: false)!
        if !query.isEmpty {
            components.queryItems = query.sorted { $0.key < $1.key }.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        var request = URLRequest(url: components.url!)
        request.timeoutInterval = 12
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await URLSession.shared.data(for: request)
        } catch {
            throw CalendarAPIError.unreachable
        }
        guard (response as? HTTPURLResponse)?.statusCode == 200,
              let object = try? JSONSerialization.jsonObject(with: data)
        else { throw CalendarAPIError.unexpected }
        return object
    }

    static func day(_ date: Date) async throws -> CalendarDay {
        guard let object = try await get("calendar/\(apiDate(date))") as? [String: Any] else {
            throw CalendarAPIError.unexpected
        }
        return CalendarDay(object)
    }

    /// The office readings (lessons and psalms) for Morning or Evening Prayer.
    static func officeReadings(_ date: Date, service: ReadingsService) async throws -> [Reading] {
        let settings = AppPreferences.settings
        let query = [
            "translation": settings["bible_translation"] ?? "esv",
            "psalms": settings["psalm_translation"] ?? "contemporary",
            "style": settings["psalm_style"] ?? "unison",
        ]
        guard let object = try await get("readings/\(apiDate(date))", query: query) as? [String: Any],
              let services = object["services"] as? [String: Any],
              let office = services[service.title] as? [String: Any],
              let readings = office["readings"] as? [[String: Any]]
        else { throw CalendarAPIError.unexpected }
        let length = settings["reading_length"] ?? "full"
        let cycle = settings["psalter"] ?? "60"
        return readings.compactMap { entry -> Reading? in
            guard let reading = (entry[length] ?? entry["full"]) as? [String: Any],
                  let citation = reading["citation"] as? String else { return nil }
            // Psalms come in both cycles; keep the listener's.
            if let readingCycle = reading["cycle"] as? String, readingCycle != cycle { return nil }
            return Reading(name: reading["name"] as? String ?? "", citation: citation)
        }
    }

    /// A psalm's verses, in the listener's psalm translation.
    static func psalmText(_ number: Int) async throws -> String {
        guard let object = try await get("psalms/\(number)/") as? [String: Any],
              let verses = object["verses"] as? [[String: Any]]
        else { throw CalendarAPIError.unexpected }
        let traditional = AppPreferences.settings["psalm_translation"] == "traditional"
        let lines = verses.map { verse -> String in
            let first = (traditional ? verse["first_half_tle"] : nil) as? String ?? verse["first_half"] as? String ?? ""
            let second = (traditional ? verse["second_half_tle"] : nil) as? String ?? verse["second_half"] as? String ?? ""
            return LiturgicalText.plain("\(first) \(second)")
        }
        return lines.joined(separator: "\n")
    }
}

struct Reading: Hashable {
    let name: String
    let citation: String
}

/// One day from /api/v1/calendar/<date>.
struct CalendarDay {
    struct Commemoration {
        let uuid: String
        let name: String
        let saintName: String?
        let rankName: String
        let rankTitle: String
        let precedence: Int
        let colors: [String]
        let collect: String?
        let summary: String?
        let points: [String]
        let biography: String?

        init(_ object: [String: Any]) {
            uuid = object["uuid"] as? String ?? ""
            name = LiturgicalText.plain(object["name"] as? String ?? "")
            saintName = (object["saint_name"] as? String).map(LiturgicalText.plain)
            let rank = object["rank"] as? [String: Any] ?? [:]
            rankName = rank["name"] as? String ?? ""
            rankTitle = rank["formatted_name"] as? String ?? ""
            precedence = rank["precedence"] as? Int ?? 99
            colors = object["colors"] as? [String] ?? []
            collect = (object["collect"] as? String).map(LiturgicalText.plain).flatMap { $0.isEmpty ? nil : $0 }
            summary = (object["ai_one_sentence"] as? String).map(LiturgicalText.plain).flatMap { $0.isEmpty ? nil : $0 }
            // Sometimes a list, sometimes an empty string.
            points = (object["ai_bullet_points"] as? [String] ?? []).map(LiturgicalText.plain)
            biography = (object["biography"] as? String).map(LiturgicalText.plain).flatMap { $0.isEmpty ? nil : $0 }
        }

        /// A saint's day or holy day, rather than an ordinary weekday or Sunday.
        var isSaintOrHolyDay: Bool {
            ["HOLY_DAY", "COMMEMORATION_ANGLICAN", "COMMEMORATION_ECUMENICAL"].contains(rankName)
                || (rankName == "PRINCIPAL_FEAST" && saintName != nil)
        }
    }

    let date: String
    let weekday: String
    let longDate: String
    let seasonName: String
    let seasonColors: [String]
    let fastDay: Int
    let fastDescription: String
    let fastReasons: [String]
    let commemorations: [Commemoration]
    let eveningCommemorations: [Commemoration]
    let massReadings: [String]
    let primaryColor: String
    let primaryEveningColor: String
    let primaryFeast: String
    let primaryEveningFeast: String
    let majorFeast: String?

    init(_ object: [String: Any]) {
        date = object["date"] as? String ?? ""
        let description = object["date_description"] as? [String: Any] ?? [:]
        weekday = description["weekday"] as? String ?? ""
        longDate = [
            description["weekday"] as? String,
            [description["month_name"] as? String, description["day"] as? String].compactMap { $0 }.joined(separator: " "),
        ].compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: ", ")
        let season = object["season"] as? [String: Any] ?? [:]
        seasonName = season["name"] as? String ?? ""
        seasonColors = season["colors"] as? [String] ?? []
        let fast = object["fast"] as? [String: Any] ?? [:]
        fastDay = fast["fast_day"] as? Int ?? 0
        fastDescription = fast["fast_day_description"] as? String ?? ""
        fastReasons = fast["fast_day_reason"] as? [String] ?? []
        commemorations = (object["commemorations"] as? [[String: Any]] ?? []).map(Commemoration.init)
        eveningCommemorations = (object["evening_commemorations"] as? [[String: Any]] ?? []).map(Commemoration.init)
        massReadings = (object["mass_readings"] as? [[String: Any]] ?? []).compactMap { $0["citation"] as? String }
        primaryColor = object["primary_color"] as? String ?? ""
        primaryEveningColor = object["primary_evening_color"] as? String ?? primaryColor
        primaryFeast = LiturgicalText.plain(object["primary_feast"] as? String ?? "")
        primaryEveningFeast = LiturgicalText.plain(object["primary_evening_feast"] as? String ?? "")
        majorFeast = (object["major_feast"] as? String).map(LiturgicalText.plain)
    }

    var saints: [Commemoration] { commemorations.filter(\.isSaintOrHolyDay) }

    /// What to call the day: its first observance, unless that is a plain weekday (a feria, such
    /// as "Saturday after the Twenty-third Sunday after Pentecost") with a saint or holy day kept
    /// on it, when it is the saint.
    var headline: String { Self.headline(commemorations, otherwise: primaryFeast) }

    /// The same for the evening, which on the eve of a feast is the feast.
    var eveningHeadline: String {
        Self.headline(
            eveningCommemorations.isEmpty ? commemorations : eveningCommemorations,
            otherwise: primaryEveningFeast.isEmpty ? primaryFeast : primaryEveningFeast
        )
    }

    /// Whether a saint stands in for a plain weekday in the headline.
    var headlineIsSaint: Bool { headline != primaryFeast }

    private static func headline(_ observances: [Commemoration], otherwise: String) -> String {
        guard let first = observances.first, first.rankName.hasSuffix("FERIA"), observances.count > 1 else {
            return otherwise
        }
        return observances[1].name
    }

    /// After 3 p.m. the evening's observance (the eve of a feast) is the one being prayed.
    func isEvening(_ date: Date = Date()) -> Bool { Calendar.current.component(.hour, from: date) >= 15 }
}

/// Turns the API's HTML and typography into plain words Siri can say.
enum LiturgicalText {
    // The psalter and lessons set LORD and GOD in small capitals.
    private static let smallCaps: [Character: Character] = [
        "ᴀ": "a", "ʙ": "b", "ᴄ": "c", "ᴅ": "d", "ᴇ": "e", "ꜰ": "f", "ɢ": "g", "ʜ": "h", "ɪ": "i",
        "ᴊ": "j", "ᴋ": "k", "ʟ": "l", "ᴍ": "m", "ɴ": "n", "ᴏ": "o", "ᴘ": "p", "ʀ": "r", "ꜱ": "s",
        "ᴛ": "t", "ᴜ": "u", "ᴠ": "v", "ᴡ": "w", "ʏ": "y", "ᴢ": "z",
    ]

    static func plain(_ html: String) -> String {
        var text = html
            .replacingOccurrences(of: "<br\\s*/?>", with: "\n", options: .regularExpression)
            .replacingOccurrences(of: "</p>", with: "\n")
            .replacingOccurrences(of: "<[^>]+>", with: "", options: .regularExpression)
            // Footnote marks from the commemorations' sources: [1][4].
            .replacingOccurrences(of: "\\[\\d+\\]", with: "", options: .regularExpression)
        let entities = [
            "&nbsp;": " ", "&amp;": "&", "&quot;": "\"", "&#39;": "’", "&rsquo;": "’", "&lsquo;": "‘",
            "&ldquo;": "“", "&rdquo;": "”", "&mdash;": "—", "&ndash;": "–", "&lt;": "<", "&gt;": ">",
        ]
        for (entity, value) in entities { text = text.replacingOccurrences(of: entity, with: value) }
        text = String(text.map { smallCaps[$0] ?? $0 })
        text = text.replacingOccurrences(of: "*", with: "")
        text = text.replacingOccurrences(of: "[ \\t]+", with: " ", options: .regularExpression)
        text = text.replacingOccurrences(of: " *\\n+ *", with: "\n", options: .regularExpression)
        return text.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// "II Chronicles 30:1-22" as it is read aloud: "Second Chronicles 30:1-22".
    static func spokenCitation(_ citation: String) -> String {
        let books = ["III ": "Third ", "II ": "Second ", "I ": "First "]
        var text = citation.replacingOccurrences(of: ",  ", with: ", ")
        for (roman, word) in books where text.hasPrefix(roman) {
            text = word + text.dropFirst(roman.count)
            break
        }
        // "Psalms 43" is one psalm; "Psalms 15, 16, 17" stays plural.
        return text.contains(",") ? text : text.replacingOccurrences(of: "Psalms ", with: "Psalm ")
    }

    /// Liturgical colors as the API names them, for saying aloud.
    static func colorName(_ color: String) -> String {
        switch color.lowercased() {
        case "lenten array": return "Lenten array"
        case "": return "not given"
        default: return color.lowercased()
        }
    }

    static func list(_ items: [String]) -> String {
        switch items.count {
        case 0: return ""
        case 1: return items[0]
        case 2: return "\(items[0]) and \(items[1])"
        default: return items.dropLast().joined(separator: ", ") + ", and " + items.last!
        }
    }
}

/// The great feasts, worked out from the date of Easter, so "when is Ash Wednesday?" can be
/// answered without the network. The calendar API then confirms the day (a feast that falls in Holy
/// Week, for instance, moves).
enum MajorFeast: String, CaseIterable {
    case adventSunday
    case christmas
    case epiphany
    case presentation
    case ashWednesday
    case annunciation
    case palmSunday
    case maundyThursday
    case goodFriday
    case easter
    case ascension
    case pentecost
    case trinitySunday
    case transfiguration
    case allSaints
    case christTheKing

    var title: String {
        switch self {
        case .adventSunday: return "the First Sunday of Advent"
        case .christmas: return "Christmas Day"
        case .epiphany: return "the Epiphany"
        case .presentation: return "the Presentation"
        case .ashWednesday: return "Ash Wednesday"
        case .annunciation: return "the Annunciation"
        case .palmSunday: return "Palm Sunday"
        case .maundyThursday: return "Maundy Thursday"
        case .goodFriday: return "Good Friday"
        case .easter: return "Easter Day"
        case .ascension: return "Ascension Day"
        case .pentecost: return "the Day of Pentecost"
        case .trinitySunday: return "Trinity Sunday"
        case .transfiguration: return "the Transfiguration"
        case .allSaints: return "All Saints’ Day"
        case .christTheKing: return "Christ the King"
        }
    }

    /// Words in the calendar's own name for the day, to confirm it there.
    var calendarWords: [String] {
        switch self {
        case .adventSunday: return ["First Sunday in Advent", "First Sunday of Advent"]
        case .christmas: return ["Christmas", "Nativity"]
        case .epiphany: return ["Epiphany"]
        case .presentation: return ["Presentation"]
        case .ashWednesday: return ["Ash Wednesday"]
        case .annunciation: return ["Annunciation of our Lord"]
        case .palmSunday: return ["Palm Sunday"]
        case .maundyThursday: return ["Maundy Thursday"]
        case .goodFriday: return ["Good Friday"]
        case .easter: return ["Easter Day"]
        case .ascension: return ["Ascension"]
        case .pentecost: return ["Pentecost"]
        case .trinitySunday: return ["Trinity Sunday"]
        case .transfiguration: return ["Transfiguration"]
        case .allSaints: return ["All Saints"]
        case .christTheKing: return ["Christ the King", "Last Sunday after Pentecost"]
        }
    }

    /// Fixed feasts can be moved off a Sunday or out of Holy Week; the calendar knows where.
    var mayMove: Bool {
        [.presentation, .annunciation, .transfiguration, .allSaints, .epiphany].contains(self)
    }

    /// Easter Day in the Gregorian calendar (the anonymous "Meeus/Jones/Butcher" algorithm).
    static func easter(_ year: Int, calendar: Calendar = .current) -> Date {
        let a = year % 19, b = year / 100, c = year % 100
        let d = b / 4, e = b % 4, f = (b + 8) / 25, g = (b - f + 1) / 3
        let h = (19 * a + b - d - g + 15) % 30
        let i = c / 4, k = c % 4
        let l = (32 + 2 * e + 2 * i - h - k) % 7
        let m = (a + 11 * h + 22 * l) / 451
        let month = (h + l - 7 * m + 114) / 31
        let day = ((h + l - 7 * m + 114) % 31) + 1
        return calendar.date(from: DateComponents(year: year, month: month, day: day))!
    }

    /// The first Sunday of Advent: the fourth Sunday before Christmas.
    static func adventSunday(_ year: Int, calendar: Calendar = .current) -> Date {
        let christmas = calendar.date(from: DateComponents(year: year, month: 12, day: 25))!
        let weekday = calendar.component(.weekday, from: christmas) // 1 = Sunday
        let daysBack = weekday == 1 ? 7 : weekday - 1
        let sundayBefore = calendar.date(byAdding: .day, value: -daysBack, to: christmas)!
        return calendar.date(byAdding: .day, value: -21, to: sundayBefore)!
    }

    func date(in year: Int, calendar: Calendar = .current) -> Date {
        func fixed(_ month: Int, _ day: Int) -> Date {
            calendar.date(from: DateComponents(year: year, month: month, day: day))!
        }
        let easter = MajorFeast.easter(year, calendar: calendar)
        func fromEaster(_ days: Int) -> Date { calendar.date(byAdding: .day, value: days, to: easter)! }
        switch self {
        case .adventSunday: return MajorFeast.adventSunday(year, calendar: calendar)
        case .christmas: return fixed(12, 25)
        case .epiphany: return fixed(1, 6)
        case .presentation: return fixed(2, 2)
        case .ashWednesday: return fromEaster(-46)
        case .annunciation: return fixed(3, 25)
        case .palmSunday: return fromEaster(-7)
        case .maundyThursday: return fromEaster(-3)
        case .goodFriday: return fromEaster(-2)
        case .easter: return easter
        case .ascension: return fromEaster(39)
        case .pentecost: return fromEaster(49)
        case .trinitySunday: return fromEaster(56)
        case .transfiguration: return fixed(8, 6)
        case .allSaints: return fixed(11, 1)
        case .christTheKing:
            return calendar.date(byAdding: .day, value: -7, to: MajorFeast.adventSunday(year, calendar: calendar))!
        }
    }

    /// The next time this feast comes, today included.
    func next(after today: Date = Date(), calendar: Calendar = .current) -> Date {
        let start = calendar.startOfDay(for: today)
        let year = calendar.component(.year, from: start)
        let thisYear = date(in: year, calendar: calendar)
        return thisYear >= start ? thisYear : date(in: year + 1, calendar: calendar)
    }
}
