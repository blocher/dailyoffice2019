package com.dailyoffice2019.app.voice

import android.app.PendingIntent
import androidx.annotation.RequiresApi
import androidx.appfunctions.AppFunctionAppUnknownException
import androidx.appfunctions.AppFunctionDeclaration
import androidx.appfunctions.AppFunctionElementNotFoundException
import androidx.appfunctions.AppFunctionInvalidArgumentException
import androidx.appfunctions.AppFunctionSerializable
import androidx.appfunctions.AppFunctionService
import androidx.appfunctions.AppFunctionServiceEntryPoint
import androidx.appfunctions.AppFunctionStringValueConstraint
import java.time.LocalDate
import java.util.Calendar
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/*
 * Gemini and other assistants on Android 16 and later call these (AppFunctions): the Android side
 * of the Siri actions in ios/App/App/Voice/VoiceIntents.swift.
 *
 * Opening and playing return a PendingIntent that opens the app at the page (?autoplay=1 starts
 * its audio, app/src/helpers/voice.js). Questions are answered from the calendar API without
 * opening the app.
 *
 * KSP generates DailyOfficeAppFunctionService from this class, and the schema in
 * assets/daily_office_app_functions.xml; AndroidManifest.xml declares the service. The app-wide
 * instructions are in res/xml/app_metadata.xml. Test on a device with:
 *
 *     adb shell cmd app_function list-app-functions | grep dailyoffice2019
 *     adb shell cmd app_function execute-app-function --package com.dailyoffice2019.app \
 *       --function 'com.dailyoffice2019.app.voice.DailyOfficeAppFunctions#getLiturgicalDay' \
 *       --parameters '{}'
 */

/** An answer about the church calendar, written to be read aloud. */
@AppFunctionSerializable(isDescribedByKDoc = true)
data class CalendarAnswer(
    /** The full answer, written to be read aloud as it is, such as "Today is Ash Wednesday. It is a fast day, with total abstinence." */
    val answer: String,
    /** A short heading for the answer, such as the feast's name. */
    val heading: String,
    /** Opens the app at the page that shows more, such as the day in the calendar. */
    val openInApp: PendingIntent?,
)

/** A page of the app, ready to open. */
@AppFunctionSerializable(isDescribedByKDoc = true)
data class AppPage(
    /** What will open, such as "Compline" or "Psalm 23". */
    val title: String,
    /** True when the page starts reading its audio aloud as soon as it opens. */
    val playsAudio: Boolean,
    /** Opens the app at the page. Start it to show the page to the user. */
    val openApp: PendingIntent,
)

/** A psalm's text. */
@AppFunctionSerializable(isDescribedByKDoc = true)
data class PsalmText(
    /** The psalm's number, from 1 to 150. */
    val number: Int,
    /** The psalm's Latin title (its first words in Latin), such as "Dominus regit me". */
    val latinTitle: String,
    /** The psalm's verses, one per line, in the user's chosen psalm translation. */
    val text: String,
    /** Opens the psalm in the app. */
    val openInApp: PendingIntent,
)

@RequiresApi(36)
@AppFunctionServiceEntryPoint(
    serviceName = "DailyOfficeAppFunctionService",
    appFunctionXmlFileName = "daily_office_app_functions",
)
abstract class DailyOfficeAppFunctions : AppFunctionService() {

    private fun page(title: String, path: String, autoplay: Boolean) =
        AppPage(title, autoplay, VoiceLinks.pendingIntent(this, path, autoplay))

    private fun answer(result: LiturgicalAnswer) = CalendarAnswer(
        result.spoken,
        result.short,
        result.path?.let { VoiceLinks.pendingIntent(this, it) },
    )

    private fun calendarOf(date: LocalDate?): Calendar = Calendar.getInstance().apply {
        if (date != null) {
            clear()
            set(date.year, date.monthValue - 1, date.dayOfMonth)
        }
    }

    /** Reads the calendar off the main thread, turning failures into errors the assistant can explain. */
    private suspend fun <T> fromCalendar(read: () -> T): T = withContext(Dispatchers.IO) {
        try {
            read()
        } catch (error: CalendarApiException) {
            throw AppFunctionAppUnknownException(error.message ?: CalendarApi.UNEXPECTED)
        } catch (error: AppFunctionInvalidArgumentException) {
            throw error
        } catch (error: AppFunctionElementNotFoundException) {
            throw error
        } catch (_: Exception) {
            throw AppFunctionAppUnknownException(CalendarApi.UNEXPECTED)
        }
    }

    private fun officeNamed(office: String?): Office =
        Office.named(office, this) ?: throw AppFunctionInvalidArgumentException("Unknown office: $office")

    // Opening and playing

    /**
     * Opens The Daily Office at today's office and starts reading it aloud: Morning Prayer, Midday
     * Prayer, Evening Prayer, or Compline from the Book of Common Prayer (2019), or one of the four
     * shorter Family Prayer offices for households and children.
     *
     * @param office Which office: "now" (or empty) for the office for this time of day, "family" for
     *   Family Prayer for this time of day, or a specific office.
     * @return The page to open; start its openApp to show it.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun playOffice(
        @AppFunctionStringValueConstraint(enumValues = ["now", "family", "morning_prayer", "midday_prayer", "evening_prayer", "compline", "family_morning", "family_midday", "family_early_evening", "family_close_of_day"])
        office: String? = null,
    ): AppPage {
        val chosen = officeNamed(office)
        return page(chosen.title, chosen.path, autoplay = true)
    }

    /**
     * Opens today's office in The Daily Office to read and pray along with the text, without
     * starting the audio.
     *
     * @param office Which office: "now" (or empty) for the office for this time of day, "family" for
     *   Family Prayer for this time of day, or a specific office.
     * @return The page to open; start its openApp to show it.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun openOffice(
        @AppFunctionStringValueConstraint(enumValues = ["now", "family", "morning_prayer", "midday_prayer", "evening_prayer", "compline", "family_morning", "family_midday", "family_early_evening", "family_close_of_day"])
        office: String? = null,
    ): AppPage {
        val chosen = officeNamed(office)
        return page(chosen.title, chosen.path, autoplay = false)
    }

    /**
     * Opens today's Scripture readings (the psalms and lessons appointed for Morning Prayer or
     * Evening Prayer, or the readings for the Holy Eucharist) and starts reading them aloud.
     *
     * @param service "morning_prayer", "evening_prayer", or "holy_eucharist". Empty means Morning
     *   Prayer before 3 p.m. and Evening Prayer after.
     * @return The page to open; start its openApp to show it.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun playReadings(
        @AppFunctionStringValueConstraint(enumValues = ["morning_prayer", "evening_prayer", "holy_eucharist"])
        service: String? = null,
    ): AppPage {
        val chosen = ReadingsService.named(service)
        return page("Readings for ${chosen.title}", chosen.path, autoplay = true)
    }

    /**
     * Opens the Scripture readings for a day in The Daily Office, to read them.
     *
     * @param service "morning_prayer", "evening_prayer", or "holy_eucharist". Empty means Morning
     *   Prayer before 3 p.m. and Evening Prayer after.
     * @param date The day whose readings to open. Empty means today.
     * @return The page to open; start its openApp to show it.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun openReadings(
        @AppFunctionStringValueConstraint(enumValues = ["morning_prayer", "evening_prayer", "holy_eucharist"])
        service: String? = null,
        date: LocalDate? = null,
    ): AppPage {
        val chosen = ReadingsService.named(service)
        return page("Readings for ${chosen.title}", VoiceLinks.readingsPath(chosen, calendarOf(date)), autoplay = false)
    }

    /**
     * Opens one of the 150 psalms from the Psalter of the Book of Common Prayer (2019).
     *
     * @param psalm The psalm by number (such as "23"), Latin title (such as "De profundis"), or
     *   topic (such as "God's mercy"). A topic opens the first matching psalm.
     * @return The page to open; start its openApp to show it.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun openPsalm(psalm: String): AppPage {
        val found = PsalmInfo.search(this, psalm).firstOrNull()
            ?: throw AppFunctionElementNotFoundException("No psalm matches \"$psalm\"")
        return page(found.title, found.path, autoplay = false)
    }

    /**
     * Gets the text of one of the 150 psalms from the Psalter of the Book of Common Prayer (2019),
     * in the user's chosen psalm translation, to read aloud.
     *
     * @param psalm The psalm by number (such as "23"), Latin title (such as "De profundis"), or
     *   topic (such as "God's mercy"). A topic gives the first matching psalm.
     * @return The psalm's number, Latin title, and verses.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun readPsalm(psalm: String): PsalmText {
        val found = PsalmInfo.search(this, psalm).firstOrNull()
            ?: throw AppFunctionElementNotFoundException("No psalm matches \"$psalm\"")
        val text = fromCalendar { CalendarApi.psalmText(this, found.number) }
        return PsalmText(found.number, found.latinTitle, text, VoiceLinks.pendingIntent(this, found.path))
    }

    /**
     * Lists psalms about a topic, or matching a Latin title, from the Psalter of the Book of Common
     * Prayer (2019).
     *
     * @param topic A topic (such as "thanksgiving", "God's mercy", "repentance") or part of a Latin title.
     * @return Matching psalms as "Psalm 23 (Dominus regit me)", at most ten.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun findPsalms(topic: String): List<String> =
        PsalmInfo.search(this, topic).take(10).map { psalm ->
            if (psalm.latinTitle.isEmpty()) psalm.title else "${psalm.title} (${psalm.latinTitle})"
        }

    /**
     * Opens a page of The Daily Office.
     *
     * @param page "today" (the office for now), "calendar" (the church calendar), "litany" (the
     *   Great Litany), "collects", "psalter" (all the psalms), or "settings".
     * @return The page to open; start its openApp to show it.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun openPage(
        @AppFunctionStringValueConstraint(enumValues = ["today", "calendar", "litany", "collects", "psalter", "settings"])
        page: String,
    ): AppPage {
        val (title, path) = when (page) {
            "today" -> "Today" to "/"
            "calendar" -> "The Calendar" to "/calendar"
            "litany" -> "The Great Litany" to "/litany/"
            "collects" -> "The Collects" to "/collects"
            "psalter" -> "The Psalter" to "/psalms"
            "settings" -> "Settings" to "/settings"
            else -> throw AppFunctionInvalidArgumentException("Unknown page: $page")
        }
        return page(title, path, autoplay = false)
    }

    /**
     * Opens a day in The Daily Office's church calendar, with its feast, saints, color, and readings.
     *
     * @param date The day to open.
     * @return The page to open; start its openApp to show it.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun openDay(date: LocalDate): AppPage = page(date.toString(), VoiceLinks.dayPath(calendarOf(date)), autoplay = false)

    // Questions

    /**
     * Describes a day in the church calendar of the Book of Common Prayer (2019): the feast or
     * Sunday, the season, the liturgical color, the saints remembered, and any fast.
     *
     * @param date The day to describe. Empty means today.
     * @return The answer, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun getLiturgicalDay(date: LocalDate? = null): CalendarAnswer {
        val day = calendarOf(date)
        return answer(fromCalendar { LiturgicalAnswers.day(CalendarApi.day(day), day) })
    }

    /**
     * Gets the liturgical color for a day (for vestments and altar hangings).
     *
     * @param date The day to ask about. Empty means today.
     * @return The answer, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun getLiturgicalColor(date: LocalDate? = null): CalendarAnswer {
        val day = calendarOf(date)
        return answer(fromCalendar { LiturgicalAnswers.color(CalendarApi.day(day), day) })
    }

    /**
     * Gets the season of the church year a day falls in: Advent, Christmas, Epiphany, Lent, Holy
     * Week, Easter, or the season after Pentecost.
     *
     * @param date The day to ask about. Empty means today.
     * @return The answer, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun getChurchSeason(date: LocalDate? = null): CalendarAnswer {
        val day = calendarOf(date)
        return answer(fromCalendar { LiturgicalAnswers.season(CalendarApi.day(day), day) })
    }

    /**
     * Tells whether a day is a fast day in the Book of Common Prayer (2019), what kind of fast
     * (partial or total abstinence), and why.
     *
     * @param date The day to ask about. Empty means today.
     * @return The answer, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun getFastDay(date: LocalDate? = null): CalendarAnswer {
        val day = calendarOf(date)
        return answer(fromCalendar { LiturgicalAnswers.fast(CalendarApi.day(day), day) })
    }

    /**
     * Lists the saints and holy days the church remembers on a day.
     *
     * @param date The day to ask about. Empty means today.
     * @return The answer, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun getSaints(date: LocalDate? = null): CalendarAnswer {
        val day = calendarOf(date)
        return answer(fromCalendar { LiturgicalAnswers.saints(CalendarApi.day(day), day) })
    }

    /**
     * Tells about the saint the church remembers on a day: who they were and why they are remembered.
     *
     * @param date The day to ask about. Empty means today.
     * @return The answer, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun aboutSaint(date: LocalDate? = null): CalendarAnswer {
        val day = calendarOf(date)
        return answer(fromCalendar { LiturgicalAnswers.aboutSaint(CalendarApi.day(day), day) })
    }

    /**
     * Gets the collect (the day's short prayer) for a day's feast, Sunday, or saint, from the Book of
     * Common Prayer (2019). After 3 p.m. today, the collect for the evening's observance.
     *
     * @param date The day to ask about. Empty means today.
     * @return The collect, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun getCollect(date: LocalDate? = null): CalendarAnswer {
        val day = calendarOf(date)
        return answer(fromCalendar { LiturgicalAnswers.collect(CalendarApi.day(day), day) })
    }

    /**
     * Lists the Scripture passages and psalms appointed for Morning Prayer, Evening Prayer, or the
     * Holy Eucharist on a day, following the user's psalter and lectionary settings.
     *
     * @param service "morning_prayer", "evening_prayer", or "holy_eucharist". Empty means Morning
     *   Prayer before 3 p.m. and Evening Prayer after.
     * @param date The day to ask about. Empty means today.
     * @return The citations, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun getReadings(
        @AppFunctionStringValueConstraint(enumValues = ["morning_prayer", "evening_prayer", "holy_eucharist"])
        service: String? = null,
        date: LocalDate? = null,
    ): CalendarAnswer {
        val day = calendarOf(date)
        val chosen = ReadingsService.named(service)
        return answer(
            fromCalendar {
                if (chosen == ReadingsService.HOLY_EUCHARIST) {
                    LiturgicalAnswers.massReadings(CalendarApi.day(day), day)
                } else {
                    LiturgicalAnswers.officeReadings(CalendarApi.officeReadings(this, day, chosen), chosen, day)
                }
            },
        )
    }

    /**
     * Gets the Gospel passage appointed for the Holy Eucharist on a day.
     *
     * @param date The day to ask about. Empty means today.
     * @return The answer, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun getGospel(date: LocalDate? = null): CalendarAnswer {
        val day = calendarOf(date)
        return answer(fromCalendar { LiturgicalAnswers.gospel(CalendarApi.day(day), day) })
    }

    /**
     * Finds the date of a great feast or holy day in the church calendar, such as Easter, Ash
     * Wednesday (the start of Lent), Pentecost, Christmas, or the First Sunday of Advent.
     *
     * @param feast The feast to find.
     * @param year The calendar year, such as 2027. 0 means the next time the feast comes.
     * @return The date, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun findFeast(
        @AppFunctionStringValueConstraint(enumValues = ["advent_sunday", "christmas", "epiphany", "presentation", "ash_wednesday", "annunciation", "palm_sunday", "maundy_thursday", "good_friday", "easter", "ascension", "pentecost", "trinity_sunday", "transfiguration", "all_saints", "christ_the_king"])
        feast: String,
        year: Int = 0,
    ): CalendarAnswer {
        val chosen = MajorFeast.named(feast) ?: throw AppFunctionInvalidArgumentException("Unknown feast: $feast")
        if (year != 0 && year !in 1900..2200) throw AppFunctionInvalidArgumentException("Year out of range: $year")
        val reckoned = if (year == 0) chosen.next() else chosen.date(year)
        return answer(fromCalendar { LiturgicalAnswers.feast(chosen, LiturgicalAnswers.confirmFeast(chosen, reckoned)) })
    }

    /**
     * Finds the next principal feast or holy day in the church calendar within the next six weeks.
     *
     * @return The answer, written to be read aloud.
     */
    @AppFunctionDeclaration(isDescribedByKDoc = true)
    suspend fun nextHolyDay(): CalendarAnswer = answer(fromCalendar { LiturgicalAnswers.nextHolyDay() })
}
