import Foundation

// Tests for the voice matcher (App/Voice/VoiceModel.swift VoiceWords). The app has no XCTest
// target, so this compiles the model on its own and runs on the Mac: ./run.sh

var failures = 0

func at(_ hour: Int) -> Date {
    var components = DateComponents()
    components.year = 2026
    components.month = 11
    components.day = 7
    components.hour = hour
    return Calendar.current.date(from: components)!
}

func expect(_ text: String?, _ expected: VoiceRequest?, family: Bool = false, hour: Int = 9, line: Int = #line) {
    let got = VoiceWords.match(text, prefersFamily: family, at: at(hour))
    if got != expected {
        failures += 1
        print("FAIL line \(line): \"\(text ?? "nil")\" (family: \(family), \(hour):00) → \(String(describing: got)), expected \(String(describing: expected))")
    }
}

// Office names, as said and as misheard.
expect("Midday Prayer", .office(.middayPrayer))
expect("play midday prayer on the daily office", .office(.middayPrayer))
expect("Noonday Prayer", .office(.middayPrayer))
expect("mid-day prayer", .office(.middayPrayer))
expect("mid day prayer", .office(.middayPrayer))
expect("noon day prayer", .office(.middayPrayer))
expect("Noon prayer", .office(.middayPrayer))
expect("Sext", .office(.middayPrayer))
expect("Evening Prayer", .office(.eveningPrayer))
expect("Evensong", .office(.eveningPrayer))
expect("even song", .office(.eveningPrayer))
expect("Vespers", .office(.eveningPrayer))
expect("the evening office", .office(.eveningPrayer))
expect("Compline", .office(.compline))
expect("complin", .office(.compline))
expect("comp line", .office(.compline))
expect("Night Prayer", .office(.compline))
expect("prayers at the end of the day", .office(.compline))
expect("prayers at bedtime", .office(.compline))
expect("Matins", .office(.morningPrayer))
expect("Lauds", .office(.morningPrayer))
expect("the Morning Office", .office(.morningPrayer))
expect("Morning Prayer", .office(.morningPrayer))

// Verbs.
expect("pray Evening Prayer", .office(.eveningPrayer))
expect("read me Compline", .office(.compline))
expect("read Compline to me", .office(.compline))
expect("listen to Evensong", .office(.eveningPrayer))
expect("put on Morning Prayer", .office(.morningPrayer))
expect("let's pray Compline", .office(.compline))
expect("start Midday Prayer", .office(.middayPrayer))

// Family Prayer.
expect("Family Prayer in the Morning", .office(.familyMorning))
expect("family morning prayer", .office(.familyMorning))
expect("family evening prayer", .office(.familyEarlyEvening))
expect("Family Prayer in the Early Evening", .office(.familyEarlyEvening))
expect("Family Prayer at the Close of Day", .office(.familyCloseOfDay))
expect("Close of Day", .office(.familyCloseOfDay))
expect("bedtime prayers with the family", .office(.familyCloseOfDay))
expect("prayers with the kids", .office(.familyMorning), hour: 8)
expect("family prayer", .office(.familyMidday), hour: 12)
expect("Family Compline", .office(.familyCloseOfDay))

// An office's own name is that office, even for someone who prays Family Prayer.
expect("Evening Prayer", .office(.eveningPrayer), family: true)
expect("Compline", .office(.compline), family: true)
// A bare time of day follows their choice.
expect("evening", .office(.eveningPrayer))
expect("evening", .office(.familyEarlyEvening), family: true)
expect("bedtime prayers", .office(.familyCloseOfDay), family: true)
expect("morning", .office(.morningPrayer))

// The office for now.
expect(nil, .office(.morningPrayer), hour: 8)
expect("", .office(.eveningPrayer), hour: 17)
expect("the office", .office(.middayPrayer), hour: 12)
expect("my prayers", .office(.compline), hour: 22)
expect("the daily office", .office(.compline), hour: 2)
expect("The Daily Office", .office(.familyMorning), family: true, hour: 7)
expect("today's office", .office(.eveningPrayer), hour: 16)
expect("the next office", .office(.middayPrayer), hour: 13)
expect("let's pray", .office(.eveningPrayer), hour: 18)
expect("tonight's office", .office(.eveningPrayer), hour: 18)
expect("Daily Office 2019", .office(.morningPrayer), hour: 6)

// Readings.
expect("today's readings", .readings(.morningPrayer), hour: 9)
expect("today's readings", .readings(.eveningPrayer), hour: 16)
expect("the lessons", .readings(.morningPrayer), hour: 9)
expect("the evening readings", .readings(.eveningPrayer), hour: 9)
expect("the readings for Morning Prayer", .readings(.morningPrayer), hour: 20)
expect("the Gospel", .readings(.holyEucharist))
expect("the psalms for today", .readings(.morningPrayer), hour: 10)
expect("Sunday's readings", .readings(.holyEucharist))
expect("the Eucharist", .readings(.holyEucharist))

// Not ours.
expect("jazz", nil)
expect("Taylor Swift", nil)
expect("psalm 23", nil)

// Every synonym the app gives Siri is understood as its office.
for office in Office.allCases {
    for name in [office.title] + office.synonyms {
        let got = VoiceWords.match(name, prefersFamily: false, at: at(9))
        if got != .office(office) {
            failures += 1
            print("FAIL synonym \"\(name)\" → \(String(describing: got)), expected \(office)")
        }
    }
}

if failures > 0 {
    print("\(failures) failed")
    exit(1)
}
print("All voice matcher tests passed")
