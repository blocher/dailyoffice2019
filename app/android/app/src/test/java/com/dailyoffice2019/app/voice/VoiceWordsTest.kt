package com.dailyoffice2019.app.voice

import java.util.Calendar
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * The voice matcher (VoiceWords.kt), with the same cases as the iOS app's
 * (ios/App/VoiceTests/main.swift). Run with ./gradlew :app:testDebugUnitTest.
 */
class VoiceWordsTest {
    private fun at(hour: Int): Calendar = Calendar.getInstance().apply {
        clear()
        set(2026, Calendar.NOVEMBER, 7, hour, 0)
    }

    private fun office(office: Office) = VoiceRequest.ForOffice(office)

    private fun readings(service: ReadingsService) = VoiceRequest.ForReadings(service)

    private fun expect(text: String?, expected: VoiceRequest?, family: Boolean = false, hour: Int = 9) {
        assertEquals("\"$text\" (family: $family, $hour:00)", expected, VoiceWords.match(text, family, at(hour)))
    }

    @Test
    fun matchesWhatPeopleSay() {
        // Tests for the voice matcher (App/Voice/VoiceModel.swift VoiceWords). The app has no XCTest
        // target, so this compiles the model on its own and runs on the Mac: ./run.sh
        // Office names, as said and as misheard.
        expect("Midday Prayer", office(Office.MIDDAY_PRAYER))
        expect("play midday prayer on the daily office", office(Office.MIDDAY_PRAYER))
        expect("Noonday Prayer", office(Office.MIDDAY_PRAYER))
        expect("mid-day prayer", office(Office.MIDDAY_PRAYER))
        expect("mid day prayer", office(Office.MIDDAY_PRAYER))
        expect("noon day prayer", office(Office.MIDDAY_PRAYER))
        expect("Noon prayer", office(Office.MIDDAY_PRAYER))
        expect("Sext", office(Office.MIDDAY_PRAYER))
        expect("Evening Prayer", office(Office.EVENING_PRAYER))
        expect("Evensong", office(Office.EVENING_PRAYER))
        expect("even song", office(Office.EVENING_PRAYER))
        expect("Vespers", office(Office.EVENING_PRAYER))
        expect("the evening office", office(Office.EVENING_PRAYER))
        expect("Compline", office(Office.COMPLINE))
        expect("complin", office(Office.COMPLINE))
        expect("comp line", office(Office.COMPLINE))
        expect("Night Prayer", office(Office.COMPLINE))
        expect("prayers at the end of the day", office(Office.COMPLINE))
        expect("prayers at bedtime", office(Office.COMPLINE))
        expect("Matins", office(Office.MORNING_PRAYER))
        expect("Lauds", office(Office.MORNING_PRAYER))
        expect("the Morning Office", office(Office.MORNING_PRAYER))
        expect("Morning Prayer", office(Office.MORNING_PRAYER))
        // Verbs.
        expect("pray Evening Prayer", office(Office.EVENING_PRAYER))
        expect("read me Compline", office(Office.COMPLINE))
        expect("read Compline to me", office(Office.COMPLINE))
        expect("listen to Evensong", office(Office.EVENING_PRAYER))
        expect("put on Morning Prayer", office(Office.MORNING_PRAYER))
        expect("let's pray Compline", office(Office.COMPLINE))
        expect("start Midday Prayer", office(Office.MIDDAY_PRAYER))
        // Family Prayer.
        expect("Family Prayer in the Morning", office(Office.FAMILY_MORNING))
        expect("family morning prayer", office(Office.FAMILY_MORNING))
        expect("family evening prayer", office(Office.FAMILY_EARLY_EVENING))
        expect("Family Prayer in the Early Evening", office(Office.FAMILY_EARLY_EVENING))
        expect("Family Prayer at the Close of Day", office(Office.FAMILY_CLOSE_OF_DAY))
        expect("Close of Day", office(Office.FAMILY_CLOSE_OF_DAY))
        expect("bedtime prayers with the family", office(Office.FAMILY_CLOSE_OF_DAY))
        expect("prayers with the kids", office(Office.FAMILY_MORNING), hour = 8)
        expect("family prayer", office(Office.FAMILY_MIDDAY), hour = 12)
        expect("Family Compline", office(Office.FAMILY_CLOSE_OF_DAY))
        // An office's own name is that office, even for someone who prays Family Prayer.
        expect("Evening Prayer", office(Office.EVENING_PRAYER), family = true)
        expect("Compline", office(Office.COMPLINE), family = true)
        // A bare time of day follows their choice.
        expect("evening", office(Office.EVENING_PRAYER))
        expect("evening", office(Office.FAMILY_EARLY_EVENING), family = true)
        expect("bedtime prayers", office(Office.FAMILY_CLOSE_OF_DAY), family = true)
        expect("morning", office(Office.MORNING_PRAYER))
        // The office for now.
        expect(null, office(Office.MORNING_PRAYER), hour = 8)
        expect("", office(Office.EVENING_PRAYER), hour = 17)
        expect("the office", office(Office.MIDDAY_PRAYER), hour = 12)
        expect("my prayers", office(Office.COMPLINE), hour = 22)
        expect("the daily office", office(Office.COMPLINE), hour = 2)
        expect("The Daily Office", office(Office.FAMILY_MORNING), family = true, hour = 7)
        expect("today's office", office(Office.EVENING_PRAYER), hour = 16)
        expect("the next office", office(Office.MIDDAY_PRAYER), hour = 13)
        expect("let's pray", office(Office.EVENING_PRAYER), hour = 18)
        expect("tonight's office", office(Office.EVENING_PRAYER), hour = 18)
        expect("Daily Office 2019", office(Office.MORNING_PRAYER), hour = 6)
        // Readings.
        expect("today's readings", readings(ReadingsService.MORNING_PRAYER), hour = 9)
        expect("today's readings", readings(ReadingsService.EVENING_PRAYER), hour = 16)
        expect("the lessons", readings(ReadingsService.MORNING_PRAYER), hour = 9)
        expect("the evening readings", readings(ReadingsService.EVENING_PRAYER), hour = 9)
        expect("the readings for Morning Prayer", readings(ReadingsService.MORNING_PRAYER), hour = 20)
        expect("the Gospel", readings(ReadingsService.HOLY_EUCHARIST))
        expect("the psalms for today", readings(ReadingsService.MORNING_PRAYER), hour = 10)
        expect("Sunday's readings", readings(ReadingsService.HOLY_EUCHARIST))
        expect("the Eucharist", readings(ReadingsService.HOLY_EUCHARIST))
        // Not ours.
        expect("jazz", null)
        expect("Taylor Swift", null)
        expect("psalm 23", null)
        // Every synonym the app gives Siri is understood as its office.
    }

    @Test
    fun everySynonymIsItsOffice() {
        for (office in Office.entries) {
            for (name in listOf(office.title) + office.synonyms) {
                assertEquals(name, VoiceRequest.ForOffice(office), VoiceWords.match(name, false, at(9)))
            }
        }
    }

    @Test
    fun normalizesSpeech() {
        assertEquals("midday prayer", VoiceWords.normalize("Mid-day Prayer!"))
        assertEquals("evensong", VoiceWords.normalize("Even Song"))
        assertEquals("todays readings", VoiceWords.normalize("Today’s readings"))
        assertEquals("compline", VoiceWords.normalize("comp line"))
    }
}
