package com.dailyoffice2019.app.voice

import android.content.Context
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.Calendar
import org.json.JSONArray
import org.json.JSONObject

/*
 * The church calendar, read from the app's API for assistants' answers ("what feast is today?").
 * The Android side of ios/App/App/Voice/LiturgicalCalendar.swift; keep the two in step.
 */

class CalendarApiException(message: String) : IOException(message)

object CalendarApi {
    private const val BASE = "https://api.dailyoffice2019.com/api/v1/"
    const val UNREACHABLE = "The Daily Office couldn’t reach the calendar. Check your connection and try again."
    const val UNEXPECTED = "The Daily Office couldn’t read the calendar for that day."

    /** The API's date form: 2026-11-3 (no padding), as app/src/offline/urls.js writes it. */
    fun apiDate(day: Calendar): String =
        "${day.get(Calendar.YEAR)}-${day.get(Calendar.MONTH) + 1}-${day.get(Calendar.DAY_OF_MONTH)}"

    /** Blocking: call from a background thread. */
    fun get(path: String, query: Map<String, String> = emptyMap()): Any {
        val search = query.entries.sortedBy { it.key }.joinToString("&") {
            "${it.key}=${URLEncoder.encode(it.value, "UTF-8")}"
        }
        val url = URL(BASE + path + if (search.isEmpty()) "" else "?$search")
        val connection = try {
            (url.openConnection() as HttpURLConnection).apply {
                connectTimeout = 10_000
                readTimeout = 12_000
                instanceFollowRedirects = true
            }
        } catch (_: IOException) {
            throw CalendarApiException(UNREACHABLE)
        }
        try {
            val status = try {
                connection.responseCode
            } catch (_: IOException) {
                throw CalendarApiException(UNREACHABLE)
            }
            if (status != 200) throw CalendarApiException(UNEXPECTED)
            val text = connection.inputStream.bufferedReader().use { it.readText() }
            return try {
                if (text.trimStart().startsWith("[")) JSONArray(text) else JSONObject(text)
            } catch (_: Exception) {
                throw CalendarApiException(UNEXPECTED)
            }
        } finally {
            connection.disconnect()
        }
    }

    fun day(day: Calendar): CalendarDay {
        val obj = get("calendar/${apiDate(day)}") as? JSONObject ?: throw CalendarApiException(UNEXPECTED)
        return CalendarDay(obj)
    }

    /** The office readings (lessons and psalms) for Morning or Evening Prayer. */
    fun officeReadings(context: Context, day: Calendar, service: ReadingsService): List<Reading> {
        val settings = AppPreferences(context).settings
        val query = mapOf(
            "translation" to (settings["bible_translation"] ?: "esv"),
            "psalms" to (settings["psalm_translation"] ?: "contemporary"),
            "style" to (settings["psalm_style"] ?: "unison"),
        )
        val obj = get("readings/${apiDate(day)}", query) as? JSONObject ?: throw CalendarApiException(UNEXPECTED)
        val office = obj.optJSONObject("services")?.optJSONObject(service.title) ?: throw CalendarApiException(UNEXPECTED)
        val readings = office.optJSONArray("readings") ?: JSONArray()
        val length = settings["reading_length"] ?: "full"
        val cycle = settings["psalter"] ?: "60"
        return (0 until readings.length()).mapNotNull { index ->
            val entry = readings.getJSONObject(index)
            val reading = entry.optJSONObject(length) ?: entry.optJSONObject("full") ?: return@mapNotNull null
            val citation = reading.optString("citation").takeIf { it.isNotEmpty() } ?: return@mapNotNull null
            // Psalms come in both cycles; keep the listener's.
            val readingCycle = reading.optString("cycle")
            if (readingCycle.isNotEmpty() && readingCycle != "null" && readingCycle != cycle) return@mapNotNull null
            Reading(reading.optString("name"), citation)
        }
    }

    /** A psalm's verses, in the listener's psalm translation. */
    fun psalmText(context: Context, number: Int): String {
        val obj = get("psalms/$number/") as? JSONObject ?: throw CalendarApiException(UNEXPECTED)
        val verses = obj.optJSONArray("verses") ?: throw CalendarApiException(UNEXPECTED)
        val traditional = AppPreferences(context).settings["psalm_translation"] == "traditional"
        return (0 until verses.length()).joinToString("\n") { index ->
            val verse = verses.getJSONObject(index)
            val first = verse.optString(if (traditional) "first_half_tle" else "first_half").ifEmpty { verse.optString("first_half") }
            val second = verse.optString(if (traditional) "second_half_tle" else "second_half").ifEmpty { verse.optString("second_half") }
            LiturgicalText.plain("$first $second")
        }
    }
}

data class Reading(val name: String, val citation: String)

/** One day from /api/v1/calendar/<date>. */
class CalendarDay(obj: JSONObject) {
    class Commemoration(obj: JSONObject) {
        val uuid: String = obj.optString("uuid")
        val name: String = LiturgicalText.plain(obj.optString("name"))
        val saintName: String? = obj.nullableString("saint_name")?.let(LiturgicalText::plain)
        val rankName: String = obj.optJSONObject("rank")?.optString("name").orEmpty()
        val collect: String? = obj.nullableString("collect")?.let(LiturgicalText::plain)?.ifEmpty { null }
        val summary: String? = obj.nullableString("ai_one_sentence")?.let(LiturgicalText::plain)?.ifEmpty { null }
        // Sometimes a list, sometimes an empty string.
        val points: List<String> = obj.optJSONArray("ai_bullet_points")?.strings()?.map(LiturgicalText::plain) ?: emptyList()
        val biography: String? = obj.nullableString("biography")?.let(LiturgicalText::plain)?.ifEmpty { null }

        /** A saint's day or holy day, rather than an ordinary weekday or Sunday. */
        val isSaintOrHolyDay: Boolean
            get() = rankName in setOf("HOLY_DAY", "COMMEMORATION_ANGLICAN", "COMMEMORATION_ECUMENICAL") ||
                (rankName == "PRINCIPAL_FEAST" && saintName != null)
    }

    val weekday: String = obj.optJSONObject("date_description")?.optString("weekday").orEmpty()
    val seasonName: String = obj.optJSONObject("season")?.optString("name").orEmpty()
    val seasonColors: List<String> = obj.optJSONObject("season")?.optJSONArray("colors")?.strings() ?: emptyList()
    val fastDay: Int = obj.optJSONObject("fast")?.optInt("fast_day") ?: 0
    val fastDescription: String = obj.optJSONObject("fast")?.optString("fast_day_description").orEmpty()
    val fastReasons: List<String> = obj.optJSONObject("fast")?.optJSONArray("fast_day_reason")?.strings() ?: emptyList()
    val commemorations: List<Commemoration> = obj.optJSONArray("commemorations").objects().map(::Commemoration)
    val eveningCommemorations: List<Commemoration> = obj.optJSONArray("evening_commemorations").objects().map(::Commemoration)
    val massReadings: List<String> = obj.optJSONArray("mass_readings").objects().mapNotNull { it.nullableString("citation") }
    val primaryColor: String = obj.optString("primary_color")
    val primaryEveningColor: String = obj.nullableString("primary_evening_color") ?: primaryColor
    val primaryFeast: String = LiturgicalText.plain(obj.optString("primary_feast"))
    val primaryEveningFeast: String = LiturgicalText.plain(obj.optString("primary_evening_feast"))
    val majorFeast: String? = obj.nullableString("major_feast")?.let(LiturgicalText::plain)

    val saints: List<Commemoration> get() = commemorations.filter { it.isSaintOrHolyDay }

    /**
     * What to call the day: its first observance, unless that is a plain weekday (a feria, such as
     * "Saturday after the Twenty-third Sunday after Pentecost") with a saint or holy day kept on it,
     * when it is the saint.
     */
    val headline: String get() = headline(commemorations, primaryFeast)

    /** The same for the evening, which on the eve of a feast is the feast. */
    val eveningHeadline: String
        get() = headline(
            eveningCommemorations.ifEmpty { commemorations },
            primaryEveningFeast.ifEmpty { primaryFeast },
        )

    /** Whether a saint stands in for a plain weekday in the headline. */
    val headlineIsSaint: Boolean get() = headline != primaryFeast

    private fun headline(observances: List<Commemoration>, otherwise: String): String {
        val first = observances.firstOrNull() ?: return otherwise
        return if (first.rankName.endsWith("FERIA") && observances.size > 1) observances[1].name else otherwise
    }

    /** After 3 p.m. the evening's observance (the eve of a feast) is the one being prayed. */
    fun isEvening(now: Calendar = Calendar.getInstance()): Boolean = now.get(Calendar.HOUR_OF_DAY) >= 15
}

private fun JSONObject.nullableString(key: String): String? =
    if (isNull(key)) null else optString(key).takeIf { it.isNotEmpty() }

private fun JSONArray.strings(): List<String> = (0 until length()).mapNotNull { optString(it).takeIf(String::isNotEmpty) }

private fun JSONArray?.objects(): List<JSONObject> =
    if (this == null) emptyList() else (0 until length()).mapNotNull { optJSONObject(it) }

/** Turns the API's HTML and typography into plain words an assistant can say. */
object LiturgicalText {
    // The psalter and lessons set LORD and GOD in small capitals.
    private val smallCaps = mapOf(
        'ᴀ' to 'a', 'ʙ' to 'b', 'ᴄ' to 'c', 'ᴅ' to 'd', 'ᴇ' to 'e', 'ꜰ' to 'f', 'ɢ' to 'g', 'ʜ' to 'h',
        'ɪ' to 'i', 'ᴊ' to 'j', 'ᴋ' to 'k', 'ʟ' to 'l', 'ᴍ' to 'm', 'ɴ' to 'n', 'ᴏ' to 'o', 'ᴘ' to 'p',
        'ʀ' to 'r', 'ꜱ' to 's', 'ᴛ' to 't', 'ᴜ' to 'u', 'ᴠ' to 'v', 'ᴡ' to 'w', 'ʏ' to 'y', 'ᴢ' to 'z',
    )
    private val entities = mapOf(
        "&nbsp;" to " ", "&amp;" to "&", "&quot;" to "\"", "&#39;" to "’", "&rsquo;" to "’", "&lsquo;" to "‘",
        "&ldquo;" to "“", "&rdquo;" to "”", "&mdash;" to "—", "&ndash;" to "–", "&lt;" to "<", "&gt;" to ">",
    )

    fun plain(html: String): String {
        var text = html
            .replace(Regex("<br\\s*/?>"), "\n")
            .replace("</p>", "\n")
            .replace(Regex("<[^>]+>"), "")
            // Footnote marks from the commemorations' sources: [1][4].
            .replace(Regex("\\[\\d+]"), "")
        for ((entity, value) in entities) text = text.replace(entity, value)
        text = text.map { smallCaps[it] ?: it }.joinToString("")
            .replace("*", "")
            .replace(Regex("[ \\t]+"), " ")
            .replace(Regex(" *\\n+ *"), "\n")
        return text.trim()
    }

    /** "II Chronicles 30:1-22" as it is read aloud: "Second Chronicles 30:1-22". */
    fun spokenCitation(citation: String): String {
        var text = citation.replace(",  ", ", ")
        for ((roman, word) in listOf("III " to "Third ", "II " to "Second ", "I " to "First ")) {
            if (text.startsWith(roman)) {
                text = word + text.removePrefix(roman)
                break
            }
        }
        // "Psalms 43" is one psalm; "Psalms 15, 16, 17" stays plural.
        return if (text.contains(",")) text else text.replace("Psalms ", "Psalm ")
    }

    fun colorName(color: String): String = when (color.lowercase()) {
        "lenten array" -> "Lenten array"
        "" -> "not given"
        else -> color.lowercase()
    }

    fun list(items: List<String>): String = when (items.size) {
        0 -> ""
        1 -> items[0]
        2 -> "${items[0]} and ${items[1]}"
        else -> items.dropLast(1).joinToString(", ") + ", and " + items.last()
    }
}

/**
 * The great feasts, worked out from the date of Easter, so "when is Ash Wednesday?" can be
 * answered without the network. The calendar API then confirms the day for feasts that can move.
 */
enum class MajorFeast(val title: String, val calendarWords: List<String>, val mayMove: Boolean = false) {
    ADVENT_SUNDAY("the First Sunday of Advent", listOf("First Sunday in Advent", "First Sunday of Advent")),
    CHRISTMAS("Christmas Day", listOf("Christmas", "Nativity")),
    EPIPHANY("the Epiphany", listOf("Epiphany"), mayMove = true),
    PRESENTATION("the Presentation", listOf("Presentation"), mayMove = true),
    ASH_WEDNESDAY("Ash Wednesday", listOf("Ash Wednesday")),
    ANNUNCIATION("the Annunciation", listOf("Annunciation of our Lord"), mayMove = true),
    PALM_SUNDAY("Palm Sunday", listOf("Palm Sunday")),
    MAUNDY_THURSDAY("Maundy Thursday", listOf("Maundy Thursday")),
    GOOD_FRIDAY("Good Friday", listOf("Good Friday")),
    EASTER("Easter Day", listOf("Easter Day")),
    ASCENSION("Ascension Day", listOf("Ascension")),
    PENTECOST("the Day of Pentecost", listOf("Pentecost")),
    TRINITY_SUNDAY("Trinity Sunday", listOf("Trinity Sunday")),
    TRANSFIGURATION("the Transfiguration", listOf("Transfiguration"), mayMove = true),
    ALL_SAINTS("All Saints’ Day", listOf("All Saints"), mayMove = true),
    CHRIST_THE_KING("Christ the King", listOf("Christ the King", "Last Sunday after Pentecost"));

    val key: String get() = name.lowercase()

    fun date(year: Int): Calendar {
        fun fixed(month: Int, day: Int) = Calendar.getInstance().apply { clear(); set(year, month - 1, day) }
        fun fromEaster(days: Int) = easter(year).apply { add(Calendar.DAY_OF_MONTH, days) }
        return when (this) {
            ADVENT_SUNDAY -> adventSunday(year)
            CHRISTMAS -> fixed(12, 25)
            EPIPHANY -> fixed(1, 6)
            PRESENTATION -> fixed(2, 2)
            ASH_WEDNESDAY -> fromEaster(-46)
            ANNUNCIATION -> fixed(3, 25)
            PALM_SUNDAY -> fromEaster(-7)
            MAUNDY_THURSDAY -> fromEaster(-3)
            GOOD_FRIDAY -> fromEaster(-2)
            EASTER -> easter(year)
            ASCENSION -> fromEaster(39)
            PENTECOST -> fromEaster(49)
            TRINITY_SUNDAY -> fromEaster(56)
            TRANSFIGURATION -> fixed(8, 6)
            ALL_SAINTS -> fixed(11, 1)
            CHRIST_THE_KING -> adventSunday(year).apply { add(Calendar.DAY_OF_MONTH, -7) }
        }
    }

    /** The next time this feast comes, today included. */
    fun next(now: Calendar = Calendar.getInstance()): Calendar {
        val today = startOfDay(now)
        val thisYear = date(today.get(Calendar.YEAR))
        return if (!thisYear.before(today)) thisYear else date(today.get(Calendar.YEAR) + 1)
    }

    companion object {
        fun named(name: String?): MajorFeast? {
            val wanted = name?.trim()?.lowercase()?.replace('’', '\'')?.replace(' ', '_') ?: return null
            val aliases = mapOf(
                "advent" to ADVENT_SUNDAY, "christmas_day" to CHRISTMAS, "nativity" to CHRISTMAS,
                "candlemas" to PRESENTATION, "lent" to ASH_WEDNESDAY, "holy_thursday" to MAUNDY_THURSDAY,
                "easter_sunday" to EASTER, "whitsunday" to PENTECOST, "trinity" to TRINITY_SUNDAY,
                "all_saints'_day" to ALL_SAINTS, "all_saints" to ALL_SAINTS, "ascension_day" to ASCENSION,
            )
            return entries.firstOrNull { it.key == wanted } ?: aliases[wanted]
        }

        fun startOfDay(day: Calendar): Calendar = (day.clone() as Calendar).apply {
            set(Calendar.HOUR_OF_DAY, 0)
            set(Calendar.MINUTE, 0)
            set(Calendar.SECOND, 0)
            set(Calendar.MILLISECOND, 0)
        }

        /** Easter Day in the Gregorian calendar (the anonymous "Meeus/Jones/Butcher" algorithm). */
        fun easter(year: Int): Calendar {
            val a = year % 19
            val b = year / 100
            val c = year % 100
            val d = b / 4
            val e = b % 4
            val f = (b + 8) / 25
            val g = (b - f + 1) / 3
            val h = (19 * a + b - d - g + 15) % 30
            val i = c / 4
            val k = c % 4
            val l = (32 + 2 * e + 2 * i - h - k) % 7
            val m = (a + 11 * h + 22 * l) / 451
            val month = (h + l - 7 * m + 114) / 31
            val day = ((h + l - 7 * m + 114) % 31) + 1
            return Calendar.getInstance().apply { clear(); set(year, month - 1, day) }
        }

        /** The first Sunday of Advent: the fourth Sunday before Christmas. */
        fun adventSunday(year: Int): Calendar {
            val christmas = Calendar.getInstance().apply { clear(); set(year, Calendar.DECEMBER, 25) }
            val weekday = christmas.get(Calendar.DAY_OF_WEEK) // 1 = Sunday
            val daysBack = if (weekday == Calendar.SUNDAY) 7 else weekday - 1
            return christmas.apply { add(Calendar.DAY_OF_MONTH, -daysBack - 21) }
        }
    }
}
