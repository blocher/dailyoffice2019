import AppIntents
import SwiftUI
import WidgetKit

/// The day in the church calendar on the Home Screen, in StandBy, and on the Lock Screen: the feast
/// or Sunday, its season and color, the saint remembered, and any fast. After 3 p.m. it shows the
/// evening's observance (the eve of a feast). Tapping it opens today's office; on the Lock Screen a
/// round size is just that: a Pray button.
///
/// On a plain weekday (a feria) with a saint, it names the saint, or, if someone chooses so when
/// editing the widget (iOS 17 and later), the weekday.
///
/// It reads the same calendar API as the app and Siri (App/Voice/LiturgicalCalendar.swift, compiled
/// into this extension too), refreshes at 3 p.m. and midnight, and keeps the last day it read for
/// when the network isn't there.
@main
struct DailyOfficeWidgets: WidgetBundle {
    var body: some Widget {
        // One or the other: the legacy widget offers no sizes on iOS 17 and later.
        if #available(iOS 17.0, *) {
            TodayWidget()
        }
        TodayWidgetLegacy()
    }
}

enum TodayWidgetInfo {
    static let kind = "DailyOfficeToday"
    static let legacyKind = "DailyOfficeToday.ios15"

    static var families: [WidgetFamily] {
        if #available(iOS 16.0, *) {
            return [.systemSmall, .systemMedium, .accessoryRectangular, .accessoryInline, .accessoryCircular]
        }
        return [.systemSmall, .systemMedium]
    }
}

/// iOS 17 and later: the widget can be edited to choose what a weekday with a saint shows.
@available(iOS 17.0, *)
struct TodayWidget: Widget {
    var body: some WidgetConfiguration {
        AppIntentConfiguration(kind: TodayWidgetInfo.kind, intent: TodayWidgetIntent.self, provider: TodayIntentProvider()) {
            TodayWidgetView(entry: $0)
        }
        .configurationDisplayName("Today in the Church Calendar")
        .description("The day’s feast, season, color, and saint, from the Book of Common Prayer (2019).")
        .supportedFamilies(TodayWidgetInfo.families)
    }
}

/// iOS 15 and 16: the saint on a weekday, always.
struct TodayWidgetLegacy: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: TodayWidgetInfo.legacyKind, provider: TodayProvider()) {
            TodayWidgetView(entry: $0)
        }
        .configurationDisplayName("Today in the Church Calendar")
        .description("The day’s feast, season, color, and saint, from the Book of Common Prayer (2019).")
        .supportedFamilies(Self.families)
    }

    private static var families: [WidgetFamily] {
        if #available(iOS 17.0, *) { return [] }
        return TodayWidgetInfo.families
    }
}

// MARK: - The widget's option

@available(iOS 17.0, *)
enum WeekdayHeadline: String, AppEnum {
    case saint
    case weekday

    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Weekday Name"
    static let caseDisplayRepresentations: [WeekdayHeadline: DisplayRepresentation] = [
        .saint: DisplayRepresentation(title: "The saint", subtitle: "Willibrord, Archbishop of Utrecht"),
        .weekday: DisplayRepresentation(title: "The weekday", subtitle: "Saturday after the Twenty-third Sunday after Pentecost"),
    ]
}

@available(iOS 17.0, *)
struct TodayWidgetIntent: WidgetConfigurationIntent {
    static let title: LocalizedStringResource = "Today in the Church Calendar"
    static let description = IntentDescription("Choose what the widget names on a weekday when a saint is remembered.")

    @Parameter(title: "On a weekday with a saint, show", default: .saint)
    var weekdayHeadline: WeekdayHeadline

    init() {}
}

// MARK: - The day, as the widget shows it

struct DayCard: Codable, Equatable {
    var date: Date
    /// The day's own observance: a feast, a Sunday, or a weekday (shortened).
    var observance: String
    var eveningObservance: String
    /// The saint kept on a plain weekday, if any (CalendarDay.headline), in full.
    var weekdaySaint: String?
    var eveningWeekdaySaint: String?
    var season: String
    var color: String
    var eveningColor: String
    /// The saints remembered, by their short names.
    var saints: [String]
    var fast: String?

    init(day: CalendarDay, date: Date) {
        self.date = Calendar.current.startOfDay(for: date)
        observance = DayCard.shorten(day.primaryFeast)
        eveningObservance = DayCard.shorten(day.primaryEveningFeast.isEmpty ? day.primaryFeast : day.primaryEveningFeast)
        weekdaySaint = day.headlineIsSaint ? day.headline : nil
        let eveningHeadline = day.eveningHeadline
        eveningWeekdaySaint = eveningHeadline != (day.primaryEveningFeast.isEmpty ? day.primaryFeast : day.primaryEveningFeast)
            ? eveningHeadline : nil
        season = day.seasonName.lowercased().hasPrefix("season")
            ? day.seasonName.replacingOccurrences(of: "After", with: "after")
            : day.seasonName
        color = day.primaryColor
        eveningColor = day.primaryEveningColor
        saints = day.saints
            .filter { DayCard.shorten($0.name) != DayCard.shorten(day.primaryFeast) }
            .map { DayCard.shortSaint($0.name) }
        fast = day.fastDay > 0 ? DayCard.fastLabel(day.fastDescription) : nil
    }

    init(date: Date, observance: String, season: String, color: String, saints: [String], fast: String?) {
        self.date = date
        self.observance = observance
        eveningObservance = observance
        self.season = season
        self.color = color
        eveningColor = color
        self.saints = saints
        self.fast = fast
    }

    static let sample = DayCard(
        date: Date(),
        observance: "The Second Sunday in Advent",
        season: "Advent",
        color: "purple",
        saints: ["Nicholas of Myra"],
        fast: nil
    )

    /// "Tuesday after the Twenty-third Sunday after Pentecost, or the Twenty-second Sunday after
    /// Trinity (Proper 26)" -> "Tuesday after the Twenty-third Sunday after Pentecost".
    static func shorten(_ name: String) -> String {
        var text = name
        if let range = text.range(of: ", or the ") { text = String(text[..<range.lowerBound]) }
        text = text.replacingOccurrences(of: "\\s*\\(Proper \\d+\\)", with: "", options: .regularExpression)
        return text.trimmingCharacters(in: .whitespaces)
    }

    /// "Willibrord, Archbishop of Utrecht and Missionary to Frisia, 739" -> "Willibrord".
    static func shortSaint(_ name: String) -> String {
        name.components(separatedBy: ",").first?.trimmingCharacters(in: .whitespaces) ?? name
    }

    /// "Fast (Total abstinence)" -> "Fast · total abstinence".
    static func fastLabel(_ description: String) -> String {
        guard let open = description.firstIndex(of: "("), let close = description.lastIndex(of: ")"), open < close else {
            return description.isEmpty ? "Fast day" : description
        }
        return "Fast · " + description[description.index(after: open)..<close].lowercased()
    }
}

struct TodayEntry: TimelineEntry {
    let date: Date
    let card: DayCard
    /// After 3 p.m.: the evening's observance.
    let evening: Bool
    /// Name a weekday by its saint (the default) rather than by the weekday.
    let saintOnWeekdays: Bool
    /// Shown from the last good read, or a sample before there is one.
    let stale: Bool

    private var weekdaySaint: String? {
        guard saintOnWeekdays else { return nil }
        return evening ? card.eveningWeekdaySaint : card.weekdaySaint
    }

    /// The widget's title.
    var feast: String { weekdaySaint ?? (evening ? card.eveningObservance : card.observance) }

    /// A saint to mention under the title: one not already named in it.
    var saint: String? {
        let shown = weekdaySaint.map(DayCard.shortSaint)
        return card.saints.first { $0 != shown }
    }

    var colorName: String { evening ? card.eveningColor : card.color }
}

// MARK: - Timeline

/// The entries both kinds of widget show.
enum TodayTimeline {
    private static let cacheKey = "TodayWidget.days.v2"
    private static let eveningHour = 15

    static func placeholder(saintOnWeekdays: Bool = true) -> TodayEntry {
        TodayEntry(date: Date(), card: .sample, evening: false, saintOnWeekdays: saintOnWeekdays, stale: true)
    }

    static func snapshot(preview: Bool, saintOnWeekdays: Bool) async -> TodayEntry {
        let now = Date()
        if let card = cached(for: now) { return entry(card, at: now, saintOnWeekdays: saintOnWeekdays) }
        if preview { return placeholder(saintOnWeekdays: saintOnWeekdays) }
        let cards = await load(now)
        return cards.first.map { entry($0, at: now, saintOnWeekdays: saintOnWeekdays) } ?? placeholder(saintOnWeekdays: saintOnWeekdays)
    }

    static func timeline(saintOnWeekdays: Bool) async -> Timeline<TodayEntry> {
        let calendar = Calendar.current
        let now = Date()
        let cards = await load(now)
        guard let today = cards.first(where: { calendar.isDate($0.date, inSameDayAs: now) }) else {
            // Nothing for today, even cached: show the sample, and try again soon.
            return Timeline(entries: [placeholder(saintOnWeekdays: saintOnWeekdays)], policy: .after(now.addingTimeInterval(30 * 60)))
        }
        var entries = [entry(today, at: now, saintOnWeekdays: saintOnWeekdays)]
        if let evening = calendar.date(bySettingHour: eveningHour, minute: 0, second: 0, of: now), evening > now {
            entries.append(TodayEntry(date: evening, card: today, evening: true, saintOnWeekdays: saintOnWeekdays, stale: false))
        }
        let midnight = calendar.startOfDay(for: calendar.date(byAdding: .day, value: 1, to: now)!)
        if let tomorrow = cards.first(where: { calendar.isDate($0.date, inSameDayAs: midnight) }) {
            entries.append(TodayEntry(date: midnight, card: tomorrow, evening: false, saintOnWeekdays: saintOnWeekdays, stale: false))
        }
        // Read again a little after midnight, for the day after.
        return Timeline(entries: entries, policy: .after(midnight.addingTimeInterval(10 * 60)))
    }

    private static func entry(_ card: DayCard, at date: Date, saintOnWeekdays: Bool) -> TodayEntry {
        let evening = Calendar.current.component(.hour, from: date) >= eveningHour
        return TodayEntry(date: date, card: card, evening: evening, saintOnWeekdays: saintOnWeekdays, stale: false)
    }

    /// Today and tomorrow, from the calendar, or as last read.
    static func load(_ now: Date) async -> [DayCard] {
        let calendar = Calendar.current
        let tomorrow = calendar.date(byAdding: .day, value: 1, to: now)!
        async let todayDay = try? CalendarAPI.day(now)
        async let tomorrowDay = try? CalendarAPI.day(tomorrow)
        var cards: [DayCard] = []
        if let day = await todayDay { cards.append(DayCard(day: day, date: now)) }
        if let day = await tomorrowDay { cards.append(DayCard(day: day, date: tomorrow)) }
        if cards.isEmpty { return cachedCards() }
        save(cards)
        return cards
    }

    static func cached(for date: Date) -> DayCard? {
        cachedCards().first { Calendar.current.isDate($0.date, inSameDayAs: date) }
    }

    private static func cachedCards() -> [DayCard] {
        guard let data = UserDefaults.standard.data(forKey: cacheKey),
              let cards = try? JSONDecoder().decode([DayCard].self, from: data) else { return [] }
        return cards
    }

    private static func save(_ cards: [DayCard]) {
        if let data = try? JSONEncoder().encode(cards) { UserDefaults.standard.set(data, forKey: cacheKey) }
    }
}

@available(iOS 17.0, *)
struct TodayIntentProvider: AppIntentTimelineProvider {
    func placeholder(in context: Context) -> TodayEntry { TodayTimeline.placeholder() }

    func snapshot(for configuration: TodayWidgetIntent, in context: Context) async -> TodayEntry {
        await TodayTimeline.snapshot(preview: context.isPreview, saintOnWeekdays: configuration.weekdayHeadline == .saint)
    }

    func timeline(for configuration: TodayWidgetIntent, in context: Context) async -> Timeline<TodayEntry> {
        await TodayTimeline.timeline(saintOnWeekdays: configuration.weekdayHeadline == .saint)
    }
}

struct TodayProvider: TimelineProvider {
    func placeholder(in context: Context) -> TodayEntry { TodayTimeline.placeholder() }

    func getSnapshot(in context: Context, completion: @escaping (TodayEntry) -> Void) {
        Task { completion(await TodayTimeline.snapshot(preview: context.isPreview, saintOnWeekdays: true)) }
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<TodayEntry>) -> Void) {
        Task { completion(await TodayTimeline.timeline(saintOnWeekdays: true)) }
    }
}

// MARK: - Look

/// The app's paper, ink, and season colors (app/src/styles/tokens.css), light and dark.
enum WidgetPalette {
    static let paper = dynamic(light: 0xFDFCF9, dark: 0x161513)
    static let ink = dynamic(light: 0x1C1A17, dark: 0xE9E4DA)
    static let inkSoft = dynamic(light: 0x55504A, dark: 0xB6ADA0)
    static let inkFaint = dynamic(light: 0x857E74, dark: 0x877F73)

    static func season(_ name: String) -> Color {
        switch name.lowercased() {
        case "red": return dynamic(light: 0xA8241C, dark: 0xE4776D)
        case "green": return dynamic(light: 0x2F6A3B, dark: 0x82BF8F)
        case "purple", "violet", "lenten array": return dynamic(light: 0x5B2B84, dark: 0xBB9CDB)
        case "white", "gold": return dynamic(light: 0x9A7A22, dark: 0xDCBC66)
        case "black": return dynamic(light: 0x3A3733, dark: 0xAAA298)
        case "rose": return dynamic(light: 0xA94A76, dark: 0xE59ABA)
        case "blue": return dynamic(light: 0x2A4D97, dark: 0x93B2EC)
        default: return dynamic(light: 0x8A2C25, dark: 0xDF8A7C) // --accent-default
        }
    }

    private static func dynamic(light: UInt32, dark: UInt32) -> Color {
        Color(UIColor { traits in
            let hex = traits.userInterfaceStyle == .dark ? dark : light
            return UIColor(
                red: CGFloat((hex >> 16) & 0xFF) / 255,
                green: CGFloat((hex >> 8) & 0xFF) / 255,
                blue: CGFloat(hex & 0xFF) / 255,
                alpha: 1
            )
        })
    }
}

struct TodayWidgetView: View {
    let entry: TodayEntry
    @Environment(\.widgetFamily) private var family

    private var accent: Color { WidgetPalette.season(entry.colorName) }

    private var isAccessory: Bool {
        if #available(iOS 16.0, *) {
            return [.accessoryInline, .accessoryRectangular, .accessoryCircular].contains(family)
        }
        return false
    }

    var body: some View {
        content
            .widgetURL(VoiceLinks.url(path: "/"))
            .widgetBackground(isAccessory ? nil : WidgetPalette.paper, bar: isAccessory ? nil : accent)
    }

    @ViewBuilder
    private var content: some View {
        switch family {
        case .systemMedium: medium
        default:
            if #available(iOS 16.0, *) {
                switch family {
                case .accessoryInline: inline
                case .accessoryRectangular: rectangular
                case .accessoryCircular: circular
                default: small
                }
            } else {
                small
            }
        }
    }

    private var eyebrow: some View {
        HStack(spacing: 6) {
            Circle().fill(accent).frame(width: 8, height: 8)
            Text(entry.evening ? "THIS EVENING" : "TODAY")
                .font(.system(size: 10, weight: .semibold, design: .serif))
                .tracking(1.2)
                .foregroundColor(WidgetPalette.inkFaint)
        }
    }

    private var small: some View {
        VStack(alignment: .leading, spacing: 6) {
            eyebrow
            Text(entry.feast)
                .font(.system(size: 16, weight: .semibold, design: .serif))
                .foregroundColor(WidgetPalette.ink)
                .lineLimit(4)
                .minimumScaleFactor(0.75)
            Spacer(minLength: 0)
            Text(entry.saint ?? entry.card.season)
                .font(.system(size: 12, design: .serif).italic())
                .foregroundColor(WidgetPalette.inkSoft)
                .lineLimit(2)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .widgetPadding()
    }

    private var medium: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                eyebrow
                Spacer()
                Text(entry.card.date, format: .dateTime.weekday(.wide).month(.wide).day())
                    .font(.system(size: 11, design: .serif))
                    .foregroundColor(WidgetPalette.inkFaint)
            }
            Text(entry.feast)
                .font(.system(size: 18, weight: .semibold, design: .serif))
                .foregroundColor(WidgetPalette.ink)
                .lineLimit(2)
                .minimumScaleFactor(0.8)
            Text(details)
                .font(.system(size: 13, design: .serif).italic())
                .foregroundColor(WidgetPalette.inkSoft)
                .lineLimit(2)
            Spacer(minLength: 0)
            HStack(spacing: 16) {
                // The office for this time of day, ready to pray (not playing).
                Link(destination: VoiceLinks.url(path: "/")) {
                    Label("Pray", systemImage: "book")
                }
                Link(destination: VoiceLinks.url(path: "/readings/")) {
                    Label("Readings", systemImage: "text.book.closed")
                }
            }
            .font(.system(size: 12, weight: .semibold, design: .serif))
            .foregroundColor(accent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
        .widgetPadding()
    }

    /// Season, saint, and fast, as one line: "Advent · Nicholas of Myra · Fast · partial abstinence".
    private var details: String {
        [entry.card.season, entry.saint, entry.card.fast].compactMap { $0 }.filter { !$0.isEmpty }.joined(separator: " · ")
    }

    @available(iOS 16.0, *)
    private var rectangular: some View {
        VStack(alignment: .leading, spacing: 1) {
            Text(entry.feast)
                .font(.system(size: 14, weight: .semibold, design: .serif))
                .lineLimit(2)
                .widgetAccentable()
            Text(entry.saint ?? entry.card.season)
                .font(.system(size: 12, design: .serif))
                .lineLimit(1)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    /// A round Lock Screen button that opens the office for this time of day (not playing).
    @available(iOS 16.0, *)
    private var circular: some View {
        ZStack {
            AccessoryWidgetBackground()
            VStack(spacing: 1) {
                Image(systemName: "book.fill")
                    .font(.system(size: 15, weight: .semibold))
                Text("Pray")
                    .font(.system(size: 11, weight: .semibold, design: .serif))
            }
            .widgetAccentable()
        }
    }

    @available(iOS 16.0, *)
    private var inline: some View {
        Text(entry.feast)
    }
}

// MARK: - iOS 15 to 17

private extension View {
    /// The paper, with the liturgical color as a bar down the leading edge. iOS 17 and later draw a
    /// widget's background themselves (and need one for every widget, even on the Lock Screen,
    /// where they leave it out); before, the view draws it.
    @ViewBuilder
    func widgetBackground(_ paper: Color?, bar: Color?) -> some View {
        let background = HStack(spacing: 0) {
            if let bar { bar.frame(width: 5) }
            (paper ?? Color.clear)
        }
        if #available(iOS 17.0, *) {
            containerBackground(for: .widget) { background }
        } else if paper != nil {
            self.background(background)
        } else {
            self
        }
    }

    /// iOS 17 and later give widgets margins; before, the view leaves its own.
    @ViewBuilder
    func widgetPadding() -> some View {
        if #available(iOS 17.0, *) {
            self
        } else {
            padding(EdgeInsets(top: 14, leading: 18, bottom: 14, trailing: 14))
        }
    }
}
