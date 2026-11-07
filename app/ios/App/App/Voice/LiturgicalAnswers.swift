import Foundation

/// Siri's answers about the church calendar, worded to be heard as well as read: the `spoken` text
/// stands on its own on AirPods or HomePod, and `short` sits under Siri's card.
struct LiturgicalAnswer {
    let spoken: String
    let short: String
    /// An app page that shows more, for "open it".
    var path: String?
}

private extension CalendarDay {
    /// A feast's name inside a sentence: "for the Twenty-fourth Sunday", not "for The Twenty-fourth Sunday".
    var feast: String { primaryFeast.hasPrefix("The ") ? "the " + primaryFeast.dropFirst(4) : primaryFeast }
    var eveningFeast: String { eveningHeadline.hasPrefix("The ") ? "the " + eveningHeadline.dropFirst(4) : eveningHeadline }
    /// The day, after "Today is": a weekday's saint as "the commemoration of Willibrord, …".
    var dayName: String { headlineIsSaint ? "the commemoration of \(headline)" : feast }
}

enum LiturgicalAnswers {
    // MARK: Days

    /// The day as a sentence's subject: "Today", "Tomorrow", or "Sunday, November 8".
    static func dayPhrase(_ date: Date, now: Date = Date(), calendar: Calendar = .current) -> String {
        if calendar.isDate(date, inSameDayAs: now) { return "Today" }
        if let tomorrow = calendar.date(byAdding: .day, value: 1, to: now), calendar.isDate(date, inSameDayAs: tomorrow) {
            return "Tomorrow"
        }
        if let yesterday = calendar.date(byAdding: .day, value: -1, to: now), calendar.isDate(date, inSameDayAs: yesterday) {
            return "Yesterday"
        }
        let formatter = DateFormatter()
        formatter.setLocalizedDateFormatFromTemplate(
            calendar.component(.year, from: date) == calendar.component(.year, from: now) ? "EEEEMMMMd" : "EEEEMMMMdyyyy"
        )
        return formatter.string(from: date)
    }

    /// The day after a verb: "today", "tomorrow", or "on Sunday, November 8".
    static func onPhrase(_ date: Date, now: Date = Date()) -> String {
        let subject = dayPhrase(date, now: now)
        return ["Today", "Tomorrow", "Yesterday"].contains(subject) ? subject.lowercased() : "on \(subject)"
    }

    private static func capitalized(_ text: String) -> String { text.prefix(1).uppercased() + text.dropFirst() }

    static func fullDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateStyle = .full
        formatter.timeStyle = .none
        return formatter.string(from: date)
    }

    static func dayPath(_ date: Date, calendar: Calendar = .current) -> String {
        let parts = calendar.dateComponents([.year, .month, .day], from: date)
        return "/day/\(parts.year!)/\(parts.month!)/\(parts.day!)/"
    }

    /// Everything about one day: its observance, season, color, saints, and any fast.
    static func day(_ day: CalendarDay, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        let when = dayPhrase(date, now: now)
        let isToday = when == "Today"
        var sentences: [String]
        if day.headlineIsSaint {
            // A weekday with a saint: the saint first, then the weekday.
            sentences = [
                "\(capitalized(onPhrase(date, now: now))) the church remembers \(day.headline).",
                "It is \(day.feast), in \(seasonPhrase(day.seasonName)).",
            ]
        } else {
            sentences = ["\(when) is \(day.feast)."]
            if !day.seasonName.isEmpty, !day.primaryFeast.localizedCaseInsensitiveContains(day.seasonName) {
                sentences.append("It falls in \(seasonPhrase(day.seasonName)).")
            }
        }
        if !day.primaryColor.isEmpty {
            sentences.append("The color is \(LiturgicalText.colorName(day.primaryColor)).")
        }
        let saints = day.saints.filter { $0.name != day.primaryFeast && $0.name != day.headline }
        if !saints.isEmpty {
            sentences.append("The church remembers \(LiturgicalText.list(saints.map(\.name))).")
        }
        if day.fastDay > 0 {
            sentences.append(fastSentence(day))
        }
        if isToday, day.isEvening(now), day.eveningHeadline != day.headline, day.eveningHeadline != day.primaryFeast {
            sentences.append("This evening the church keeps \(day.eveningFeast).")
        }
        return LiturgicalAnswer(spoken: sentences.joined(separator: " "), short: day.headline, path: dayPath(date))
    }

    static func color(_ day: CalendarDay, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        let color = LiturgicalText.colorName(day.primaryColor)
        var spoken = "The liturgical color \(onPhrase(date, now: now)) is \(color), for \(day.feast)."
        if Calendar.current.isDate(date, inSameDayAs: now), day.isEvening(now), !day.primaryEveningColor.isEmpty, day.primaryEveningColor != day.primaryColor {
            spoken += " This evening it is \(LiturgicalText.colorName(day.primaryEveningColor)), for \(day.primaryEveningFeast)."
        }
        return LiturgicalAnswer(spoken: spoken, short: color.capitalized, path: dayPath(date))
    }

    static func season(_ day: CalendarDay, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        let when = dayPhrase(date, now: now)
        let verb = when == "Today" ? "We are in" : "\(when) falls in"
        let colors = day.seasonColors.map(LiturgicalText.colorName)
        var spoken = "\(verb) \(seasonPhrase(day.seasonName))."
        if !colors.isEmpty { spoken += " Its color is \(LiturgicalText.list(colors).replacingOccurrences(of: " and ", with: " or "))." }
        return LiturgicalAnswer(spoken: spoken, short: day.seasonName, path: dayPath(date))
    }

    /// "Advent" -> "Advent"; "Season After Pentecost" -> "the Season after Pentecost".
    static func seasonPhrase(_ name: String) -> String {
        name.lowercased().hasPrefix("season") ? "the \(name.replacingOccurrences(of: "After", with: "after"))" : name
    }

    static func fast(_ day: CalendarDay, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        let when = dayPhrase(date, now: now)
        guard day.fastDay > 0 else {
            let feast = day.weekday == "Sunday" || day.majorFeast != nil ? " It is \(day.feast), a feast." : ""
            return LiturgicalAnswer(spoken: "\(when) is not a fast day.\(feast)", short: "Not a fast day", path: dayPath(date))
        }
        return LiturgicalAnswer(spoken: "\(when) is \(day.dayName). \(fastSentence(day))", short: fastKind(day), path: dayPath(date))
    }

    private static func fastKind(_ day: CalendarDay) -> String {
        // "Fast (Total abstinence)" -> "total abstinence"
        if let open = day.fastDescription.firstIndex(of: "("), let close = day.fastDescription.lastIndex(of: ")"), open < close {
            return String(day.fastDescription[day.fastDescription.index(after: open)..<close])
        }
        return day.fastDescription.isEmpty ? "Fast" : day.fastDescription
    }

    private static func fastSentence(_ day: CalendarDay) -> String {
        let kind = fastKind(day).lowercased()
        let reasons = day.fastReasons.filter { !$0.isEmpty }
        let why = reasons.isEmpty ? "" : ", for \(LiturgicalText.list(reasons))"
        return "It is a fast day, with \(kind)\(why)."
    }

    // MARK: Saints

    static func saints(_ day: CalendarDay, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        let when = dayPhrase(date, now: now)
        let saints = day.saints
        guard !saints.isEmpty else {
            return LiturgicalAnswer(
                spoken: "No saint is remembered \(onPhrase(date, now: now)). \(when) is \(day.feast).",
                short: day.primaryFeast,
                path: dayPath(date)
            )
        }
        let names = saints.map(\.name)
        return LiturgicalAnswer(
            spoken: "\(capitalized(onPhrase(date, now: now))) the church remembers \(LiturgicalText.list(names)).",
            short: names.joined(separator: " · "),
            path: saints.count == 1 ? "/commemorations/\(saints[0].uuid)" : dayPath(date)
        )
    }

    static func aboutSaint(_ day: CalendarDay, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        guard let saint = day.saints.first else { return saints(day, on: date, now: now) }
        var about: String
        if let summary = saint.summary {
            about = summary
        } else if !saint.points.isEmpty {
            about = saint.points.prefix(2).joined(separator: " ")
        } else if let biography = saint.biography {
            about = firstSentences(biography, count: 2)
        } else {
            about = "The Daily Office has no notes on \(saint.saintName ?? saint.name) yet."
        }
        return LiturgicalAnswer(
            spoken: "\(capitalized(onPhrase(date, now: now))) the church remembers \(saint.name). \(about)",
            short: saint.name,
            path: "/commemorations/\(saint.uuid)"
        )
    }

    static func firstSentences(_ text: String, count: Int) -> String {
        var sentences: [String] = []
        text.enumerateSubstrings(in: text.startIndex..., options: .bySentences) { sentence, _, _, stop in
            if let sentence { sentences.append(sentence.trimmingCharacters(in: .whitespaces)) }
            if sentences.count >= count { stop = true }
        }
        return sentences.joined(separator: " ")
    }

    // MARK: Collect and readings

    static func collect(_ day: CalendarDay, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        let evening = Calendar.current.isDate(date, inSameDayAs: now) && day.isEvening(now)
        let source = (evening ? day.eveningCommemorations : day.commemorations).first { $0.collect != nil }
            ?? day.commemorations.first { $0.collect != nil }
        guard let observance = source, let collect = observance.collect else {
            return LiturgicalAnswer(spoken: "The Daily Office has no collect for that day.", short: "No collect", path: dayPath(date))
        }
        return LiturgicalAnswer(
            spoken: "The collect for \(observance.name). \(collect)",
            short: observance.name,
            path: "/collects"
        )
    }

    static func officeReadings(_ readings: [Reading], service: ReadingsService, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        let on = onPhrase(date, now: now)
        let citations = readings.map { LiturgicalText.spokenCitation($0.citation) }
        guard !citations.isEmpty else {
            return LiturgicalAnswer(spoken: "There are no readings for \(service.title) \(on).", short: service.title, path: service.path)
        }
        return LiturgicalAnswer(
            spoken: "The readings for \(service.title) \(on) are \(LiturgicalText.list(citations)).",
            short: readings.map(\.citation).joined(separator: " · "),
            path: readingsPath(service, date)
        )
    }

    static func massReadings(_ day: CalendarDay, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        let citations = day.massReadings.map(LiturgicalText.spokenCitation)
        guard !citations.isEmpty else {
            return LiturgicalAnswer(spoken: "There are no Eucharist readings for that day.", short: "Holy Eucharist", path: ReadingsService.holyEucharist.path)
        }
        return LiturgicalAnswer(
            spoken: "The readings at the Eucharist for \(day.feast) are \(LiturgicalText.list(citations)).",
            short: day.massReadings.joined(separator: " · "),
            path: readingsPath(.holyEucharist, date)
        )
    }

    static func gospel(_ day: CalendarDay, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        // The Gospel is read last at the Eucharist.
        guard let gospel = day.massReadings.last else { return massReadings(day, on: date, now: now) }
        return LiturgicalAnswer(
            spoken: "The Gospel \(onPhrase(date, now: now)) is \(LiturgicalText.spokenCitation(gospel)), for \(day.feast).",
            short: gospel,
            path: readingsPath(.holyEucharist, date)
        )
    }

    static func readingsPath(_ service: ReadingsService, _ date: Date, calendar: Calendar = .current) -> String {
        let parts = calendar.dateComponents([.year, .month, .day], from: date)
        return "/readings/\(service.slug)/\(parts.year!)/\(parts.month!)/\(parts.day!)"
    }

    // MARK: Feasts

    static func feast(_ feast: MajorFeast, on date: Date, now: Date = Date()) -> LiturgicalAnswer {
        let calendar = Calendar.current
        let days = calendar.dateComponents([.day], from: calendar.startOfDay(for: now), to: calendar.startOfDay(for: date)).day ?? 0
        let title = feast.title.prefix(1).uppercased() + feast.title.dropFirst()
        let away: String
        switch days {
        case 0: away = "That’s today."
        case 1: away = "That’s tomorrow."
        default: away = "That’s in \(days) days."
        }
        return LiturgicalAnswer(spoken: "\(title) is \(fullDate(date)). \(away)", short: fullDate(date), path: dayPath(date))
    }

    /// Where the calendar keeps a feast this year: the reckoned day, or the next few days if it was
    /// moved (the Annunciation out of Holy Week, say). Without the network, the reckoned day.
    static func confirmFeast(_ feast: MajorFeast, from reckoned: Date) async -> Date {
        guard feast.mayMove else { return reckoned }
        for offset in 0..<16 {
            guard let date = Calendar.current.date(byAdding: .day, value: offset, to: reckoned),
                  let day = try? await CalendarAPI.day(date) else { return reckoned }
            let names = [day.primaryFeast] + day.commemorations.map(\.name)
            if names.contains(where: { name in feast.calendarWords.contains { name.localizedCaseInsensitiveContains($0) } }) {
                return date
            }
        }
        return reckoned
    }

    /// The next holy day or principal feast within six weeks, read from the calendar a week at a
    /// time.
    static func nextHolyDay(now: Date = Date()) async throws -> LiturgicalAnswer {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: now)
        for week in 0..<6 {
            let days = try await withThrowingTaskGroup(of: (Int, CalendarDay).self) { group -> [(Int, CalendarDay)] in
                for offset in (week * 7 + 1)...(week * 7 + 7) {
                    let date = calendar.date(byAdding: .day, value: offset, to: today)!
                    group.addTask { (offset, try await CalendarAPI.day(date)) }
                }
                var found: [(Int, CalendarDay)] = []
                for try await item in group { found.append(item) }
                return found.sorted { $0.0 < $1.0 }
            }
            for (offset, day) in days {
                let holy = day.commemorations.first { ["PRINCIPAL_FEAST", "HOLY_DAY"].contains($0.rankName) }
                if let holy {
                    let date = calendar.date(byAdding: .day, value: offset, to: today)!
                    return LiturgicalAnswer(
                        spoken: "The next holy day is \(holy.name), \(onPhrase(date, now: now)).",
                        short: holy.name,
                        path: dayPath(date)
                    )
                }
            }
        }
        return LiturgicalAnswer(spoken: "There are no holy days in the next six weeks.", short: "None soon", path: "/calendar")
    }
}
