import AppIntents
import CoreSpotlight
import SwiftUI

// Siri, Shortcuts, Spotlight and the Action button, on iOS 17 and later. (iOS 15 and 16 get
// Siri Suggestions and Spotlight from the page's NSUserActivity, in VoiceLaunchPlugin.swift.)
//
// Three kinds of action:
// - Play: these play the audio in the background without opening the app (AudioPlaybackIntent),
//   through the same player and request addresses as CarPlay (VoicePlayback.swift), so they work
//   with the phone locked in a car.
// - Open, read or show: these open the app at a page (VoiceLaunch).
// - Questions: answered from the calendar API in the background, spoken on AirPods and shown on
//   screen, without opening the app (LiturgicalAnswers.swift).
//
// "Play Compline on The Daily Office" may reach the app as Siri's media request instead of these
// phrases; VoicePlayback.swift handles that with the same words (VoiceWords in VoiceModel.swift).
//
// DailyOfficeShortcuts gives the most-used ones phrases that work with no setup ("Play Compline in
// The Daily Office"). On iOS 27.3 with Siri AI, SiriAI.swift also offers every action here to Siri
// as a tool, so it can be asked in any words.

// MARK: - Choices


@available(iOS 17.0, *)
enum OfficeChoice: String, AppEnum {
    case now
    case familyNow
    case morningPrayer
    case middayPrayer
    case eveningPrayer
    case compline
    case familyMorning
    case familyMidday
    case familyEarlyEvening
    case familyCloseOfDay

    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Office"

    static let caseDisplayRepresentations: [OfficeChoice: DisplayRepresentation] = [
        .now: DisplayRepresentation(
            title: "The office for now",
            subtitle: "Morning, Midday, Evening Prayer or Compline, by the time of day",
            synonyms: ["the office", "the daily office", "today’s office", "the next office", "the hours", "my prayers", "our prayers", "prayers"]
        ),
        .familyNow: DisplayRepresentation(
            title: "Family Prayer",
            subtitle: "Family Prayer for this time of day",
            synonyms: ["family prayer", "family prayers", "prayers with the kids", "prayers with the children", "prayers with my family", "prayers with the family"]
        ),
        // These must be literals for Siri; keep them in step with VoiceWords (VoiceModel.swift).
        .morningPrayer: DisplayRepresentation(title: "Morning Prayer", subtitle: "The Daily Office", synonyms: ["Matins", "Lauds", "Morning Office", "Daily Morning Prayer"]),
        .middayPrayer: DisplayRepresentation(
            title: "Midday Prayer",
            subtitle: "The Daily Office",
            synonyms: ["Noonday Prayer", "Noon Prayer", "Mid-day Prayer", "Midday Office", "Sext", "Daily Midday Prayer"]
        ),
        .eveningPrayer: DisplayRepresentation(title: "Evening Prayer", subtitle: "The Daily Office", synonyms: ["Evensong", "Vespers", "Evening Office", "Daily Evening Prayer"]),
        .compline: DisplayRepresentation(
            title: "Compline",
            subtitle: "The Daily Office",
            synonyms: ["Night Prayer", "Night Office", "Bedtime Prayers", "Prayers at Bedtime", "Prayer at the End of the Day"]
        ),
        .familyMorning: DisplayRepresentation(title: "Family Prayer in the Morning", subtitle: "Family Prayer", synonyms: ["Family Morning Prayer", "Morning Family Prayer"]),
        .familyMidday: DisplayRepresentation(title: "Family Prayer at Midday", subtitle: "Family Prayer", synonyms: ["Family Midday Prayer", "Family Noonday Prayer"]),
        .familyEarlyEvening: DisplayRepresentation(title: "Family Prayer in the Early Evening", subtitle: "Family Prayer", synonyms: ["Family Evening Prayer", "Family Early Evening Prayer", "Family Supper Prayer"]),
        .familyCloseOfDay: DisplayRepresentation(
            title: "Family Prayer at the Close of Day",
            subtitle: "Family Prayer",
            synonyms: ["Family Bedtime Prayer", "Bedtime Prayers with the Family", "Family Night Prayer", "Family Compline", "Close of Day"]
        ),
    ]

    init(_ office: Office) {
        self = OfficeChoice(rawValue: office.rawValue) ?? .now
    }

    /// The office it names; "now" goes by the clock, and by whether the listener last prayed the
    /// Daily Office or Family Prayer.
    func resolve(at date: Date = Date()) -> Office {
        switch self {
        case .now: return Office.current(family: AppPreferences.prefersFamilyPrayer, at: date)
        case .familyNow: return Office.current(family: true, at: date)
        default: return Office(rawValue: rawValue) ?? .morningPrayer
        }
    }
}

@available(iOS 17.0, *)
enum ReadingsChoice: String, AppEnum {
    case morningPrayer
    case eveningPrayer
    case holyEucharist

    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Readings"

    static let caseDisplayRepresentations: [ReadingsChoice: DisplayRepresentation] = [
        .morningPrayer: DisplayRepresentation(title: "Morning Prayer", synonyms: ["the morning readings", "the morning lessons", "Matins"]),
        .eveningPrayer: DisplayRepresentation(title: "Evening Prayer", synonyms: ["the evening readings", "the evening lessons", "Evensong"]),
        .holyEucharist: DisplayRepresentation(
            title: "Holy Eucharist",
            synonyms: ["the Eucharist", "Mass", "Communion", "the Lord’s Supper", "Sunday’s readings", "the lectionary", "the Gospel"]
        ),
    ]

    var service: ReadingsService { ReadingsService(rawValue: rawValue) ?? .morningPrayer }

    /// Morning Prayer's until 3 p.m., then Evening Prayer's.
    static func forNow(_ date: Date = Date()) -> ReadingsChoice {
        Calendar.current.component(.hour, from: date) < 15 ? .morningPrayer : .eveningPrayer
    }
}

@available(iOS 17.0, *)
enum FeastChoice: String, AppEnum {
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

    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Feast"

    static let caseDisplayRepresentations: [FeastChoice: DisplayRepresentation] = [
        .adventSunday: DisplayRepresentation(title: "Advent", synonyms: ["Advent Sunday", "the First Sunday of Advent", "the start of Advent"]),
        .christmas: DisplayRepresentation(title: "Christmas", synonyms: ["Christmas Day", "the Nativity"]),
        .epiphany: DisplayRepresentation(title: "Epiphany", synonyms: ["the Epiphany", "Twelfth Night", "Three Kings Day"]),
        .presentation: DisplayRepresentation(title: "The Presentation", synonyms: ["Candlemas", "the Purification"]),
        .ashWednesday: DisplayRepresentation(title: "Ash Wednesday", synonyms: ["the start of Lent", "Lent"]),
        .annunciation: DisplayRepresentation(title: "The Annunciation", synonyms: ["Lady Day"]),
        .palmSunday: DisplayRepresentation(title: "Palm Sunday", synonyms: ["Holy Week", "the Sunday of the Passion"]),
        .maundyThursday: DisplayRepresentation(title: "Maundy Thursday", synonyms: ["Holy Thursday"]),
        .goodFriday: DisplayRepresentation(title: "Good Friday"),
        .easter: DisplayRepresentation(title: "Easter", synonyms: ["Easter Day", "Easter Sunday", "the Resurrection"]),
        .ascension: DisplayRepresentation(title: "Ascension Day", synonyms: ["the Ascension"]),
        .pentecost: DisplayRepresentation(title: "Pentecost", synonyms: ["Whitsunday", "the Day of Pentecost"]),
        .trinitySunday: DisplayRepresentation(title: "Trinity Sunday", synonyms: ["Trinity"]),
        .transfiguration: DisplayRepresentation(title: "The Transfiguration"),
        .allSaints: DisplayRepresentation(title: "All Saints’ Day", synonyms: ["All Saints", "All Hallows"]),
        .christTheKing: DisplayRepresentation(title: "Christ the King", synonyms: ["the Last Sunday after Pentecost"]),
    ]

    var feast: MajorFeast { MajorFeast(rawValue: rawValue) ?? .easter }
}

// MARK: - Entities

/// A psalm, for "open Psalm 23", "read me the De profundis", or "a psalm about God's mercy".
@available(iOS 17.0, *)
struct PsalmEntity: AppEntity {
    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Psalm"
    static let defaultQuery = PsalmQuery()

    let id: Int

    var info: PsalmInfo { PsalmInfo.number(id) ?? PsalmInfo(number: id, latinTitle: "", topics: []) }

    var displayRepresentation: DisplayRepresentation {
        let info = info
        return DisplayRepresentation(
            title: "Psalm \(id)",
            subtitle: "\(info.latinTitle)",
            synonyms: ["\(info.latinTitle)"] + info.topics.map { "\($0)" }
        )
    }
}

@available(iOS 17.0, *)
struct PsalmQuery: EntityStringQuery {
    func entities(for identifiers: [Int]) async throws -> [PsalmEntity] {
        identifiers.filter { (1...150).contains($0) }.map(PsalmEntity.init)
    }

    func entities(matching string: String) async throws -> [PsalmEntity] {
        PsalmInfo.search(string).map { PsalmEntity(id: $0.number) }
    }

    func suggestedEntities() async throws -> [PsalmEntity] {
        PsalmInfo.all.map { PsalmEntity(id: $0.number) }
    }
}

/// One of the offices, as something on screen or in Spotlight ("share this", "play this").
@available(iOS 17.0, *)
struct OfficeEntity: AppEntity {
    static let typeDisplayRepresentation: TypeDisplayRepresentation = "Office"
    static let defaultQuery = OfficeQuery()

    let id: String

    var office: Office { Office(rawValue: id) ?? .morningPrayer }

    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(
            title: "\(office.title)",
            subtitle: office.serviceType == "family" ? "Family Prayer" : "The Daily Office",
            synonyms: office.synonyms.map { "\($0)" }
        )
    }
}

@available(iOS 17.0, *)
struct OfficeQuery: EntityQuery {
    func entities(for identifiers: [String]) async throws -> [OfficeEntity] {
        identifiers.compactMap { Office(rawValue: $0) }.map { OfficeEntity(id: $0.rawValue) }
    }

    func suggestedEntities() async throws -> [OfficeEntity] {
        Office.allCases.map { OfficeEntity(id: $0.rawValue) }
    }
}

// MARK: - Opening and playing

/// Opens the app at a page.
@available(iOS 17.0, *)
private func openPage(_ path: String, autoplay: Bool = false) {
    VoiceLaunch.open(path: VoiceLinks.adding(autoplay: autoplay, to: path))
}

/// Plays without opening the app (VoicePlayback.swift), and says what is playing.
@available(iOS 17.0, *)
@MainActor
private func playDialog(_ request: OfficeAudioResolver.Request) async -> IntentDialog {
    switch await OfficePlayback.start(request) {
    case .playing(let title):
        return IntentDialog(full: "Playing \(title).", supporting: "Playing \(title)")
    case .starting(let title):
        return IntentDialog(full: "Starting \(title). It will begin in a moment.", supporting: "Starting \(title)")
    case .failed(let error):
        return IntentDialog("\(error.localizedDescription)")
    }
}

@available(iOS 17.0, *)
struct PlayOfficeIntent: AudioPlaybackIntent {
    static let title: LocalizedStringResource = "Play an Office"
    static let description = IntentDescription(
        "Reads today’s Morning Prayer, Midday Prayer, Evening Prayer, Compline, or one of the four Family Prayer offices aloud from The Daily Office, without opening the app (with the phone locked, and in CarPlay). With no office named, plays the one for this time of day.",
        categoryName: "Pray"
    )
    static let openAppWhenRun = false

    @Parameter(
        title: "Office",
        description: "Which office to pray. Leave empty for the office for this time of day."
    )
    var office: OfficeChoice?

    init() {}

    init(office: OfficeChoice?) {
        self.office = office
    }

    static var parameterSummary: some ParameterSummary {
        Summary("Play \(\.$office)")
    }

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        let chosen = (office ?? .now).resolve()
        return .result(dialog: await playDialog(.office(chosen)))
    }
}

@available(iOS 17.0, *)
struct OpenOfficeIntent: AppIntent {
    static let title: LocalizedStringResource = "Open an Office"
    static let description = IntentDescription(
        "Opens today’s office in The Daily Office to pray along with the text, without starting the audio. With no office named, opens the one for this time of day.",
        categoryName: "Pray"
    )
    static let openAppWhenRun = true

    @Parameter(title: "Office", description: "Which office to open. Leave empty for the office for this time of day.")
    var office: OfficeChoice?

    init() {}

    init(office: OfficeChoice?) {
        self.office = office
    }

    static var parameterSummary: some ParameterSummary {
        Summary("Open \(\.$office)")
    }

    @MainActor
    func perform() async throws -> some IntentResult {
        openPage((office ?? .now).resolve().path)
        return .result()
    }
}

/// Opens an office found in Spotlight or on screen.
@available(iOS 17.0, *)
struct OpenOfficeEntityIntent: OpenIntent {
    static let title: LocalizedStringResource = "Open Office"
    static let isDiscoverable = false

    @Parameter(title: "Office")
    var target: OfficeEntity

    init() {}

    @MainActor
    func perform() async throws -> some IntentResult {
        openPage(target.office.path)
        return .result()
    }
}

@available(iOS 17.0, *)
struct PlayReadingsIntent: AudioPlaybackIntent {
    static let title: LocalizedStringResource = "Play Today’s Readings"
    static let description = IntentDescription(
        "Reads today’s Scripture readings aloud from The Daily Office (the psalms and lessons appointed for Morning or Evening Prayer, or the Holy Eucharist), without opening the app.",
        categoryName: "Readings"
    )
    static let openAppWhenRun = false

    @Parameter(
        title: "Service",
        description: "Morning Prayer, Evening Prayer, or Holy Eucharist. Leave empty for Morning Prayer before 3 p.m. and Evening Prayer after."
    )
    var service: ReadingsChoice?

    init() {}

    init(service: ReadingsChoice?) {
        self.service = service
    }

    static var parameterSummary: some ParameterSummary {
        Summary("Play the readings for \(\.$service)")
    }

    @MainActor
    func perform() async throws -> some IntentResult & ProvidesDialog {
        let chosen = (service ?? .forNow()).service
        return .result(dialog: await playDialog(.readings(chosen)))
    }
}

@available(iOS 17.0, *)
struct OpenReadingsIntent: AppIntent {
    static let title: LocalizedStringResource = "Open the Readings"
    static let description = IntentDescription(
        "Opens the Scripture readings for a day in The Daily Office.",
        categoryName: "Readings"
    )
    static let openAppWhenRun = true

    @Parameter(title: "Service", description: "Morning Prayer, Evening Prayer, or Holy Eucharist.")
    var service: ReadingsChoice?

    @Parameter(title: "Day", description: "The day whose readings to open. Leave empty for today.")
    var date: Date?

    init() {}

    @MainActor
    func perform() async throws -> some IntentResult {
        let chosen = (service ?? .forNow()).service
        openPage(LiturgicalAnswers.readingsPath(chosen, date ?? Date()))
        return .result()
    }
}

@available(iOS 17.0, *)
struct OpenPsalmIntent: AppIntent {
    static let title: LocalizedStringResource = "Open a Psalm"
    static let description = IntentDescription(
        "Opens one of the 150 psalms from the Psalter of the Book of Common Prayer (2019), by number, Latin title, or topic.",
        categoryName: "Psalms"
    )
    static let openAppWhenRun = true

    @Parameter(title: "Psalm", description: "The psalm, by number (1 to 150), Latin title, or topic.")
    var psalm: PsalmEntity

    init() {}

    init(psalm: PsalmEntity) {
        self.psalm = psalm
    }

    @MainActor
    func perform() async throws -> some IntentResult {
        openPage(psalm.info.path)
        return .result()
    }
}

/// Opens a psalm found in Spotlight or on screen.
@available(iOS 17.0, *)
struct OpenPsalmEntityIntent: OpenIntent {
    static let title: LocalizedStringResource = "Open Psalm"
    static let isDiscoverable = false

    @Parameter(title: "Psalm")
    var target: PsalmEntity

    init() {}

    @MainActor
    func perform() async throws -> some IntentResult {
        openPage(target.info.path)
        return .result()
    }
}

@available(iOS 17.0, *)
struct OpenPageIntent: AppIntent {
    enum Page: String, AppEnum {
        case today
        case calendar
        case litany
        case collects
        case psalms
        case settings

        static let typeDisplayRepresentation: TypeDisplayRepresentation = "Page"
        static let caseDisplayRepresentations: [Page: DisplayRepresentation] = [
            .today: DisplayRepresentation(title: "Today", synonyms: ["the home page", "today’s office"]),
            .calendar: DisplayRepresentation(title: "The Calendar", synonyms: ["the church calendar", "the liturgical calendar"]),
            .litany: DisplayRepresentation(title: "The Great Litany", synonyms: ["the Litany"]),
            .collects: DisplayRepresentation(title: "The Collects", synonyms: ["collects", "prayers"]),
            .psalms: DisplayRepresentation(title: "The Psalter", synonyms: ["the psalms", "all the psalms"]),
            .settings: DisplayRepresentation(title: "Settings", synonyms: ["preferences", "options"]),
        ]

        var path: String {
            switch self {
            case .today: return "/"
            case .calendar: return "/calendar"
            case .litany: return "/litany/"
            case .collects: return "/collects"
            case .psalms: return "/psalms"
            case .settings: return "/settings"
            }
        }
    }

    static let title: LocalizedStringResource = "Open a Page"
    static let description = IntentDescription(
        "Opens a page of The Daily Office: today’s office, the church calendar, the Great Litany, the collects, the Psalter, or settings."
    )
    static let openAppWhenRun = true

    @Parameter(title: "Page")
    var page: Page

    init() {}

    @MainActor
    func perform() async throws -> some IntentResult {
        openPage(page.path)
        return .result()
    }
}

@available(iOS 17.0, *)
struct OpenDayIntent: AppIntent {
    static let title: LocalizedStringResource = "Open a Day in the Calendar"
    static let description = IntentDescription(
        "Opens a day in The Daily Office’s church calendar, with its feast, saints, color, and readings.",
        categoryName: "Calendar"
    )
    static let openAppWhenRun = true

    @Parameter(title: "Day")
    var date: Date

    init() {}

    @MainActor
    func perform() async throws -> some IntentResult {
        openPage(LiturgicalAnswers.dayPath(date))
        return .result()
    }
}

// MARK: - Questions

@available(iOS 17.0, *)
extension CalendarAPIError: CustomLocalizedStringResourceConvertible {
    var localizedStringResource: LocalizedStringResource { "\(errorDescription ?? "Something went wrong.")" }
}

/// Reads a day from the calendar and words an answer about it.
@available(iOS 17.0, *)
private func answer(
    on date: Date?,
    _ make: (CalendarDay, Date) -> LiturgicalAnswer
) async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
    let day = date ?? Date()
    let answer = make(try await CalendarAPI.day(day), day)
    return respond(answer)
}

@available(iOS 17.0, *)
private func respond(_ answer: LiturgicalAnswer) -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
    .result(
        value: answer.spoken,
        dialog: IntentDialog(full: "\(answer.spoken)", supporting: "\(answer.short)"),
        view: AnswerSnippet(answer: answer)
    )
}

/// Siri's card for an answer.
@available(iOS 17.0, *)
struct AnswerSnippet: View {
    let answer: LiturgicalAnswer

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("THE DAILY OFFICE")
                .font(.caption2)
                .foregroundColor(.secondary)
            Text(answer.short)
                .font(.system(.headline, design: .serif))
            Text(answer.spoken)
                .font(.system(.subheadline, design: .serif))
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
    }
}

@available(iOS 17.0, *)
struct GetLiturgicalDayIntent: AppIntent {
    static let title: LocalizedStringResource = "What Day Is It in the Church Calendar"
    static let description = IntentDescription(
        "Tells you the observance for a day in the church calendar of the Book of Common Prayer (2019): the feast or Sunday, the season, the liturgical color, the saints remembered, and whether it is a fast day.",
        categoryName: "Calendar"
    )

    @Parameter(title: "Day", description: "The day to ask about. Leave empty for today.")
    var date: Date?

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        try await answer(on: date) { LiturgicalAnswers.day($0, on: $1) }
    }
}

@available(iOS 17.0, *)
struct GetLiturgicalColorIntent: AppIntent {
    static let title: LocalizedStringResource = "Liturgical Color"
    static let description = IntentDescription(
        "Tells you the liturgical color for a day (for vestments and hangings), from the church calendar of the Book of Common Prayer (2019).",
        categoryName: "Calendar"
    )

    @Parameter(title: "Day", description: "The day to ask about. Leave empty for today.")
    var date: Date?

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        try await answer(on: date) { LiturgicalAnswers.color($0, on: $1) }
    }
}

@available(iOS 17.0, *)
struct GetSeasonIntent: AppIntent {
    static let title: LocalizedStringResource = "Church Season"
    static let description = IntentDescription(
        "Tells you which season of the church year a day falls in: Advent, Christmas, Epiphany, Lent, Holy Week, Easter, or the season after Pentecost.",
        categoryName: "Calendar"
    )

    @Parameter(title: "Day", description: "The day to ask about. Leave empty for today.")
    var date: Date?

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        try await answer(on: date) { LiturgicalAnswers.season($0, on: $1) }
    }
}

@available(iOS 17.0, *)
struct GetFastDayIntent: AppIntent {
    static let title: LocalizedStringResource = "Is It a Fast Day"
    static let description = IntentDescription(
        "Tells you whether a day is a fast day in the Book of Common Prayer (2019), and what kind of fast (partial or total abstinence) and why.",
        categoryName: "Calendar"
    )

    @Parameter(title: "Day", description: "The day to ask about. Leave empty for today.")
    var date: Date?

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        try await answer(on: date) { LiturgicalAnswers.fast($0, on: $1) }
    }
}

@available(iOS 17.0, *)
struct GetSaintsIntent: AppIntent {
    static let title: LocalizedStringResource = "Saints Remembered"
    static let description = IntentDescription(
        "Tells you which saints and holy days the church remembers on a day.",
        categoryName: "Saints"
    )

    @Parameter(title: "Day", description: "The day to ask about. Leave empty for today.")
    var date: Date?

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        try await answer(on: date) { LiturgicalAnswers.saints($0, on: $1) }
    }
}

@available(iOS 17.0, *)
struct AboutSaintIntent: AppIntent {
    static let title: LocalizedStringResource = "About Today’s Saint"
    static let description = IntentDescription(
        "Tells you about the saint the church remembers on a day: who they were and why they are remembered.",
        categoryName: "Saints"
    )

    @Parameter(title: "Day", description: "The day to ask about. Leave empty for today.")
    var date: Date?

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        try await answer(on: date) { LiturgicalAnswers.aboutSaint($0, on: $1) }
    }
}

@available(iOS 17.0, *)
struct GetCollectIntent: AppIntent {
    static let title: LocalizedStringResource = "Collect of the Day"
    static let description = IntentDescription(
        "Reads the collect (the day’s short prayer) for a day’s feast, Sunday, or saint, from the Book of Common Prayer (2019). After 3 p.m., the collect for the evening’s observance.",
        categoryName: "Pray"
    )

    @Parameter(title: "Day", description: "The day to ask about. Leave empty for today.")
    var date: Date?

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        try await answer(on: date) { LiturgicalAnswers.collect($0, on: $1) }
    }
}

@available(iOS 17.0, *)
struct GetReadingsIntent: AppIntent {
    static let title: LocalizedStringResource = "Today’s Readings"
    static let description = IntentDescription(
        "Tells you which Scripture passages and psalms are appointed for Morning Prayer, Evening Prayer, or the Holy Eucharist on a day, following the listener’s psalter and lectionary settings.",
        categoryName: "Readings"
    )

    @Parameter(
        title: "Service",
        description: "Morning Prayer, Evening Prayer, or Holy Eucharist. Leave empty for Morning Prayer before 3 p.m. and Evening Prayer after."
    )
    var service: ReadingsChoice?

    @Parameter(title: "Day", description: "The day to ask about. Leave empty for today.")
    var date: Date?

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        let day = date ?? Date()
        let chosen = (service ?? .forNow()).service
        if chosen == .holyEucharist {
            return respond(LiturgicalAnswers.massReadings(try await CalendarAPI.day(day), on: day))
        }
        let readings = try await CalendarAPI.officeReadings(day, service: chosen)
        return respond(LiturgicalAnswers.officeReadings(readings, service: chosen, on: day))
    }
}

@available(iOS 17.0, *)
struct GetGospelIntent: AppIntent {
    static let title: LocalizedStringResource = "Today’s Gospel"
    static let description = IntentDescription(
        "Tells you which Gospel passage is appointed for the Holy Eucharist on a day.",
        categoryName: "Readings"
    )

    @Parameter(title: "Day", description: "The day to ask about. Leave empty for today.")
    var date: Date?

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        try await answer(on: date) { LiturgicalAnswers.gospel($0, on: $1) }
    }
}

@available(iOS 17.0, *)
struct ReadPsalmIntent: AppIntent {
    static let title: LocalizedStringResource = "Read a Psalm Aloud"
    static let description = IntentDescription(
        "Reads one of the 150 psalms aloud from the Psalter of the Book of Common Prayer (2019), in the listener’s psalm translation.",
        categoryName: "Psalms"
    )

    @Parameter(title: "Psalm", description: "The psalm, by number (1 to 150), Latin title, or topic.")
    var psalm: PsalmEntity

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        let info = psalm.info
        let text = try await CalendarAPI.psalmText(info.number)
        let heading = info.latinTitle.isEmpty ? info.title : "\(info.title), \(info.latinTitle)."
        return respond(LiturgicalAnswer(spoken: "\(heading)\n\(text)", short: info.title, path: info.path))
    }
}

@available(iOS 17.0, *)
struct FindFeastIntent: AppIntent {
    static let title: LocalizedStringResource = "When Is a Feast"
    static let description = IntentDescription(
        "Tells you the date of a great feast or holy day (Easter, Ash Wednesday, Pentecost, Christmas, Advent, and others) in the church calendar.",
        categoryName: "Calendar"
    )

    @Parameter(title: "Feast", description: "The feast or holy day to find.")
    var feast: FeastChoice

    @Parameter(title: "Year", description: "The calendar year, such as 2027. Leave empty for the next time it comes.")
    var year: Int?

    init() {}

    init(feast: FeastChoice) {
        self.feast = feast
    }

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        let reckoned = year.map { feast.feast.date(in: $0) } ?? feast.feast.next()
        let date = await LiturgicalAnswers.confirmFeast(feast.feast, from: reckoned)
        return respond(LiturgicalAnswers.feast(feast.feast, on: date))
    }
}

@available(iOS 17.0, *)
struct NextHolyDayIntent: AppIntent {
    static let title: LocalizedStringResource = "Next Holy Day"
    static let description = IntentDescription(
        "Tells you the next principal feast or holy day in the church calendar within the next six weeks.",
        categoryName: "Calendar"
    )

    init() {}

    func perform() async throws -> some IntentResult & ReturnsValue<String> & ProvidesDialog & ShowsSnippetView {
        respond(try await LiturgicalAnswers.nextHolyDay())
    }
}

// MARK: - Siri phrases

/// Phrases that work as soon as the app is installed. Each must name the app; iOS allows ten.
@available(iOS 17.0, *)
struct DailyOfficeShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: PlayOfficeIntent(),
            // The verbs and names are VoiceWords' (VoiceModel.swift); "Read me" plays, "Read"
            // alone opens the page (OpenOfficeIntent).
            phrases: [
                "Play \(\.$office) in \(.applicationName)",
                "Play \(\.$office) on \(.applicationName)",
                "Play \(\.$office) with \(.applicationName)",
                "Pray \(\.$office) with \(.applicationName)",
                "Pray \(\.$office) in \(.applicationName)",
                "Pray \(\.$office) on \(.applicationName)",
                "Start \(\.$office) in \(.applicationName)",
                "Start \(\.$office) on \(.applicationName)",
                "Begin \(\.$office) in \(.applicationName)",
                "Say \(\.$office) with \(.applicationName)",
                "Read me \(\.$office) in \(.applicationName)",
                "Read me \(\.$office) from \(.applicationName)",
                "Listen to \(\.$office) in \(.applicationName)",
                "Listen to \(\.$office) on \(.applicationName)",
                "Put on \(\.$office) in \(.applicationName)",
                "Resume \(\.$office) in \(.applicationName)",
                "Let’s pray \(\.$office) with \(.applicationName)",
                "Let’s pray with \(.applicationName)",
                "Pray with \(.applicationName)",
                "Play \(.applicationName)",
                "Start \(.applicationName)",
                "Pray the office with \(.applicationName)",
                "Play the office in \(.applicationName)",
            ],
            shortTitle: "Play an Office",
            systemImageName: "play.circle"
        )
        AppShortcut(
            intent: OpenOfficeIntent(),
            phrases: [
                "Open \(\.$office) in \(.applicationName)",
                "Read \(\.$office) in \(.applicationName)",
                "Show \(\.$office) in \(.applicationName)",
                "Open \(.applicationName)",
            ],
            shortTitle: "Open an Office",
            systemImageName: "book"
        )
        AppShortcut(
            intent: PlayReadingsIntent(),
            phrases: [
                "Play today’s readings in \(.applicationName)",
                "Play today’s readings on \(.applicationName)",
                "Play the readings for \(\.$service) in \(.applicationName)",
                "Play the readings for \(\.$service) on \(.applicationName)",
                "Read me today’s readings in \(.applicationName)",
                "Read me the lessons in \(.applicationName)",
                "Play today’s lessons in \(.applicationName)",
                "Play the psalms for today in \(.applicationName)",
                "Listen to today’s readings in \(.applicationName)",
            ],
            shortTitle: "Play the Readings",
            systemImageName: "text.book.closed"
        )
        AppShortcut(
            intent: GetLiturgicalDayIntent(),
            phrases: [
                "What’s today in \(.applicationName)",
                "What day is it in \(.applicationName)",
                "What feast is it in \(.applicationName)",
                "What’s the church calendar today in \(.applicationName)",
                "Ask \(.applicationName) about today",
            ],
            shortTitle: "Today in the Calendar",
            systemImageName: "calendar"
        )
        AppShortcut(
            intent: GetReadingsIntent(),
            phrases: [
                "What are today’s readings in \(.applicationName)",
                "What are the readings for \(\.$service) in \(.applicationName)",
                "What are the lessons today in \(.applicationName)",
            ],
            shortTitle: "Today’s Readings",
            systemImageName: "list.bullet.rectangle"
        )
        AppShortcut(
            intent: GetCollectIntent(),
            phrases: [
                "Read me the collect in \(.applicationName)",
                "What’s the collect of the day in \(.applicationName)",
                "Pray the collect with \(.applicationName)",
            ],
            shortTitle: "Collect of the Day",
            systemImageName: "hands.sparkles"
        )
        AppShortcut(
            intent: GetSaintsIntent(),
            phrases: [
                "Who do we remember today in \(.applicationName)",
                "Whose feast is it in \(.applicationName)",
                "What saint is today in \(.applicationName)",
            ],
            shortTitle: "Saints Remembered",
            systemImageName: "person.2"
        )
        AppShortcut(
            intent: GetLiturgicalColorIntent(),
            phrases: [
                "What color is it today in \(.applicationName)",
                "What’s the liturgical color in \(.applicationName)",
            ],
            shortTitle: "Liturgical Color",
            systemImageName: "paintpalette"
        )
        AppShortcut(
            intent: GetFastDayIntent(),
            phrases: [
                "Is today a fast day in \(.applicationName)",
                "Am I fasting today in \(.applicationName)",
            ],
            shortTitle: "Fast Day",
            systemImageName: "fork.knife"
        )
        AppShortcut(
            intent: FindFeastIntent(),
            phrases: [
                "When is \(\.$feast) in \(.applicationName)",
                "What day is \(\.$feast) in \(.applicationName)",
            ],
            shortTitle: "When Is a Feast",
            systemImageName: "calendar.badge.clock"
        )
    }
}

// MARK: - Learning from the app

/// Donations of what the listener does in the page, so Siri can suggest it at the right time
/// ("Time for Compline").
@available(iOS 17.0, *)
enum VoiceIntentDonations {
    static func donate(_ activity: VoiceActivity) {
        Task {
            switch activity.kind {
            case .office:
                guard let office = activity.office else { return }
                if activity.played {
                    _ = IntentDonationManager.shared.donate(intent: PlayOfficeIntent(office: OfficeChoice(office)))
                } else {
                    _ = IntentDonationManager.shared.donate(intent: OpenOfficeIntent(office: OfficeChoice(office)))
                }
            case .readings:
                guard activity.played, let service = activity.readings else { return }
                _ = IntentDonationManager.shared.donate(intent: PlayReadingsIntent(service: ReadingsChoice(rawValue: service.rawValue)))
            case .psalm:
                guard let number = activity.psalm else { return }
                _ = IntentDonationManager.shared.donate(intent: OpenPsalmIntent(psalm: PsalmEntity(id: number)))
            }
        }
    }
}

// MARK: - Spotlight (iOS 18) and what's on screen (iOS 18.2)

@available(iOS 18.0, *)
extension PsalmEntity: IndexedEntity {}

@available(iOS 18.0, *)
extension OfficeEntity: IndexedEntity {}

@available(iOS 18.2, *)
enum VoiceEntityAnnotations {
    /// Tells Siri which office or psalm is on screen, so "play this" or "share this" refers to it.
    static func annotate(_ userActivity: NSUserActivity, for activity: VoiceActivity) {
        if let office = activity.office {
            userActivity.appEntityIdentifier = EntityIdentifier(for: OfficeEntity.self, identifier: office.rawValue)
        } else if let psalm = activity.psalm {
            userActivity.appEntityIdentifier = EntityIdentifier(for: PsalmEntity.self, identifier: psalm)
        }
    }
}

@available(iOS 18.0, *)
enum VoiceSpotlight {
    private static let indexedKey = "VoiceSpotlight.indexedVersion"
    // Raise to index again after changing the entities' titles or synonyms.
    private static let version = 1

    /// Adds the offices and psalms to Spotlight's semantic index, which Siri searches, once.
    static func indexIfNeeded() {
        guard UserDefaults.standard.integer(forKey: indexedKey) < version else { return }
        Task.detached(priority: .utility) {
            do {
                let index = CSSearchableIndex.default()
                try await index.indexAppEntities(Office.allCases.map { OfficeEntity(id: $0.rawValue) })
                try await index.indexAppEntities(PsalmInfo.all.map { PsalmEntity(id: $0.number) })
                UserDefaults.standard.set(version, forKey: indexedKey)
            } catch {
                print("Could not index offices and psalms for Siri: \(error)")
            }
        }
    }
}
