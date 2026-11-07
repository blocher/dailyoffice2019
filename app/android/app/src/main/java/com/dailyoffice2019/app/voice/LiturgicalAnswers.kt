package com.dailyoffice2019.app.voice

import java.text.DateFormat
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale
import java.util.concurrent.Callable
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * An answer about the church calendar, worded to be heard as well as read: [spoken] stands on its
 * own through earbuds or a speaker; [short] is a heading for a card. [path] is the app page that
 * shows more.
 */
data class LiturgicalAnswer(val spoken: String, val short: String, val path: String? = null)

// A feast's name inside a sentence: "for the Twenty-fourth Sunday", not "for The Twenty-fourth Sunday".
private val CalendarDay.feast: String get() = primaryFeast.replaceFirst(Regex("^The "), "the ")
private val CalendarDay.eveningFeast: String get() = eveningHeadline.replaceFirst(Regex("^The "), "the ")

// The day, after "Today is": a weekday's saint as "the commemoration of Willibrord, …".
private val CalendarDay.dayName: String get() = if (headlineIsSaint) "the commemoration of $headline" else feast

/** The Android side of ios/App/App/Voice/LiturgicalAnswers.swift; keep the two in step. */
object LiturgicalAnswers {
    private fun sameDay(a: Calendar, b: Calendar) =
        a.get(Calendar.YEAR) == b.get(Calendar.YEAR) && a.get(Calendar.DAY_OF_YEAR) == b.get(Calendar.DAY_OF_YEAR)

    private fun shifted(day: Calendar, days: Int) = (day.clone() as Calendar).apply { add(Calendar.DAY_OF_MONTH, days) }

    /** The day as a sentence's subject: "Today", "Tomorrow", or "Sunday, November 8". */
    fun dayPhrase(date: Calendar, now: Calendar = Calendar.getInstance()): String {
        if (sameDay(date, now)) return "Today"
        if (sameDay(date, shifted(now, 1))) return "Tomorrow"
        if (sameDay(date, shifted(now, -1))) return "Yesterday"
        val pattern = if (date.get(Calendar.YEAR) == now.get(Calendar.YEAR)) "EEEE, MMMM d" else "EEEE, MMMM d, yyyy"
        return SimpleDateFormat(pattern, Locale.getDefault()).format(date.time)
    }

    /** The day after a verb: "today", "tomorrow", or "on Sunday, November 8". */
    fun onPhrase(date: Calendar, now: Calendar = Calendar.getInstance()): String {
        val subject = dayPhrase(date, now)
        return if (subject in setOf("Today", "Tomorrow", "Yesterday")) subject.lowercase() else "on $subject"
    }

    private fun String.capitalized() = replaceFirstChar { it.uppercase() }

    fun fullDate(date: Calendar): String = DateFormat.getDateInstance(DateFormat.FULL).format(date.time)

    fun day(day: CalendarDay, date: Calendar, now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        val whenPhrase = dayPhrase(date, now)
        val sentences = mutableListOf<String>()
        if (day.headlineIsSaint) {
            // A weekday with a saint: the saint first, then the weekday.
            sentences += "${onPhrase(date, now).capitalized()} the church remembers ${day.headline}."
            sentences += "It is ${day.feast}, in ${seasonPhrase(day.seasonName)}."
        } else {
            sentences += "$whenPhrase is ${day.feast}."
            if (day.seasonName.isNotEmpty() && !day.primaryFeast.contains(day.seasonName, ignoreCase = true)) {
                sentences += "It falls in ${seasonPhrase(day.seasonName)}."
            }
        }
        if (day.primaryColor.isNotEmpty()) sentences += "The color is ${LiturgicalText.colorName(day.primaryColor)}."
        val saints = day.saints.filter { it.name != day.primaryFeast && it.name != day.headline }
        if (saints.isNotEmpty()) sentences += "The church remembers ${LiturgicalText.list(saints.map { it.name })}."
        if (day.fastDay > 0) sentences += fastSentence(day)
        if (whenPhrase == "Today" && day.isEvening(now) && day.eveningHeadline != day.headline &&
            day.eveningHeadline != day.primaryFeast
        ) {
            sentences += "This evening the church keeps ${day.eveningFeast}."
        }
        return LiturgicalAnswer(sentences.joinToString(" "), day.headline, VoiceLinks.dayPath(date))
    }

    fun color(day: CalendarDay, date: Calendar, now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        val color = LiturgicalText.colorName(day.primaryColor)
        var spoken = "The liturgical color ${onPhrase(date, now)} is $color, for ${day.feast}."
        if (sameDay(date, now) && day.isEvening(now) && day.primaryEveningColor.isNotEmpty() &&
            day.primaryEveningColor != day.primaryColor
        ) {
            spoken += " This evening it is ${LiturgicalText.colorName(day.primaryEveningColor)}, for ${day.primaryEveningFeast}."
        }
        return LiturgicalAnswer(spoken, color.replaceFirstChar { it.uppercase() }, VoiceLinks.dayPath(date))
    }

    fun season(day: CalendarDay, date: Calendar, now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        val whenPhrase = dayPhrase(date, now)
        val verb = if (whenPhrase == "Today") "We are in" else "$whenPhrase falls in"
        val colors = day.seasonColors.map(LiturgicalText::colorName)
        var spoken = "$verb ${seasonPhrase(day.seasonName)}."
        if (colors.isNotEmpty()) spoken += " Its color is ${LiturgicalText.list(colors).replace(" and ", " or ")}."
        return LiturgicalAnswer(spoken, day.seasonName, VoiceLinks.dayPath(date))
    }

    /** "Advent" -> "Advent"; "Season After Pentecost" -> "the Season after Pentecost". */
    fun seasonPhrase(name: String): String =
        if (name.lowercase().startsWith("season")) "the ${name.replace("After", "after")}" else name

    fun fast(day: CalendarDay, date: Calendar, now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        val whenPhrase = dayPhrase(date, now)
        if (day.fastDay <= 0) {
            val feast = if (day.weekday == "Sunday" || day.majorFeast != null) " It is ${day.feast}, a feast." else ""
            return LiturgicalAnswer("$whenPhrase is not a fast day.$feast", "Not a fast day", VoiceLinks.dayPath(date))
        }
        return LiturgicalAnswer("$whenPhrase is ${day.dayName}. ${fastSentence(day)}", fastKind(day), VoiceLinks.dayPath(date))
    }

    private fun fastKind(day: CalendarDay): String {
        // "Fast (Total abstinence)" -> "Total abstinence"
        val open = day.fastDescription.indexOf('(')
        val close = day.fastDescription.lastIndexOf(')')
        if (open in 0 until close) return day.fastDescription.substring(open + 1, close)
        return day.fastDescription.ifEmpty { "Fast" }
    }

    private fun fastSentence(day: CalendarDay): String {
        val reasons = day.fastReasons.filter { it.isNotEmpty() }
        val why = if (reasons.isEmpty()) "" else ", for ${LiturgicalText.list(reasons)}"
        return "It is a fast day, with ${fastKind(day).lowercase()}$why."
    }

    fun saints(day: CalendarDay, date: Calendar, now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        val whenPhrase = dayPhrase(date, now)
        val saints = day.saints
        if (saints.isEmpty()) {
            return LiturgicalAnswer(
                "No saint is remembered ${onPhrase(date, now)}. $whenPhrase is ${day.feast}.",
                day.primaryFeast,
                VoiceLinks.dayPath(date),
            )
        }
        val names = saints.map { it.name }
        return LiturgicalAnswer(
            "${onPhrase(date, now).capitalized()} the church remembers ${LiturgicalText.list(names)}.",
            names.joinToString(" · "),
            if (saints.size == 1) "/commemorations/${saints[0].uuid}" else VoiceLinks.dayPath(date),
        )
    }

    fun aboutSaint(day: CalendarDay, date: Calendar, now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        val saint = day.saints.firstOrNull() ?: return saints(day, date, now)
        val about = saint.summary
            ?: saint.points.take(2).joinToString(" ").ifEmpty { null }
            ?: saint.biography?.let { firstSentences(it, 2) }
            ?: "The Daily Office has no notes on ${saint.saintName ?: saint.name} yet."
        return LiturgicalAnswer(
            "${onPhrase(date, now).capitalized()} the church remembers ${saint.name}. $about",
            saint.name,
            "/commemorations/${saint.uuid}",
        )
    }

    fun firstSentences(text: String, count: Int): String =
        text.split(Regex("(?<=[.!?])\\s+")).take(count).joinToString(" ")

    fun collect(day: CalendarDay, date: Calendar, now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        val evening = sameDay(date, now) && day.isEvening(now)
        val observance = (if (evening) day.eveningCommemorations else day.commemorations).firstOrNull { it.collect != null }
            ?: day.commemorations.firstOrNull { it.collect != null }
            ?: return LiturgicalAnswer("The Daily Office has no collect for that day.", "No collect", VoiceLinks.dayPath(date))
        return LiturgicalAnswer("The collect for ${observance.name}. ${observance.collect}", observance.name, "/collects")
    }

    fun officeReadings(
        readings: List<Reading>,
        service: ReadingsService,
        date: Calendar,
        now: Calendar = Calendar.getInstance(),
    ): LiturgicalAnswer {
        val on = onPhrase(date, now)
        val path = VoiceLinks.readingsPath(service, date)
        if (readings.isEmpty()) {
            return LiturgicalAnswer("There are no readings for ${service.title} $on.", service.title, path)
        }
        val citations = readings.map { LiturgicalText.spokenCitation(it.citation) }
        return LiturgicalAnswer(
            "The readings for ${service.title} $on are ${LiturgicalText.list(citations)}.",
            readings.joinToString(" · ") { it.citation },
            path,
        )
    }

    fun massReadings(day: CalendarDay, date: Calendar): LiturgicalAnswer {
        val path = VoiceLinks.readingsPath(ReadingsService.HOLY_EUCHARIST, date)
        if (day.massReadings.isEmpty()) {
            return LiturgicalAnswer("There are no Eucharist readings for that day.", "Holy Eucharist", path)
        }
        val citations = day.massReadings.map(LiturgicalText::spokenCitation)
        return LiturgicalAnswer(
            "The readings at the Eucharist for ${day.feast} are ${LiturgicalText.list(citations)}.",
            day.massReadings.joinToString(" · "),
            path,
        )
    }

    fun gospel(day: CalendarDay, date: Calendar, now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        // The Gospel is read last at the Eucharist.
        val gospel = day.massReadings.lastOrNull() ?: return massReadings(day, date)
        return LiturgicalAnswer(
            "The Gospel ${onPhrase(date, now)} is ${LiturgicalText.spokenCitation(gospel)}, for ${day.feast}.",
            gospel,
            VoiceLinks.readingsPath(ReadingsService.HOLY_EUCHARIST, date),
        )
    }

    fun feast(feast: MajorFeast, date: Calendar, now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        val days = TimeUnit.MILLISECONDS.toDays(
            MajorFeast.startOfDay(date).timeInMillis - MajorFeast.startOfDay(now).timeInMillis + TimeUnit.HOURS.toMillis(12),
        )
        val away = when (days) {
            0L -> "That’s today."
            1L -> "That’s tomorrow."
            else -> "That’s in $days days."
        }
        val title = feast.title.replaceFirstChar { it.uppercase() }
        return LiturgicalAnswer("$title is ${fullDate(date)}. $away", fullDate(date), VoiceLinks.dayPath(date))
    }

    /**
     * Where the calendar keeps a feast: the reckoned day, or the next few days if it was moved (the
     * Annunciation out of Holy Week, say). Without the network, the reckoned day. Blocking.
     */
    fun confirmFeast(feast: MajorFeast, reckoned: Calendar): Calendar {
        if (!feast.mayMove) return reckoned
        for (offset in 0 until 16) {
            val date = shifted(reckoned, offset)
            val day = try {
                CalendarApi.day(date)
            } catch (_: Exception) {
                return reckoned
            }
            val names = listOf(day.primaryFeast) + day.commemorations.map { it.name }
            if (names.any { name -> feast.calendarWords.any { name.contains(it, ignoreCase = true) } }) return date
        }
        return reckoned
    }

    /** The next holy day or principal feast within six weeks, read a week at a time. Blocking. */
    fun nextHolyDay(now: Calendar = Calendar.getInstance()): LiturgicalAnswer {
        val today = MajorFeast.startOfDay(now)
        val pool = Executors.newFixedThreadPool(7)
        try {
            for (week in 0 until 6) {
                val offsets = (week * 7 + 1)..(week * 7 + 7)
                val days = pool.invokeAll(offsets.map { offset -> Callable { offset to CalendarApi.day(shifted(today, offset)) } })
                    .map { it.get() }
                for ((offset, day) in days.sortedBy { it.first }) {
                    val holy = day.commemorations.firstOrNull { it.rankName == "PRINCIPAL_FEAST" || it.rankName == "HOLY_DAY" }
                    if (holy != null) {
                        val date = shifted(today, offset)
                        return LiturgicalAnswer(
                            "The next holy day is ${holy.name}, ${onPhrase(date, now)}.",
                            holy.name,
                            VoiceLinks.dayPath(date),
                        )
                    }
                }
            }
        } catch (error: java.util.concurrent.ExecutionException) {
            throw (error.cause as? Exception) ?: error
        } finally {
            pool.shutdown()
        }
        return LiturgicalAnswer("There are no holy days in the next six weeks.", "None soon", "/calendar")
    }
}
