package com.dailyoffice2019.app.voice

import java.util.Calendar

/** What someone asks for by voice: an office, or the readings. */
sealed class VoiceRequest {
    data class ForOffice(val office: Office) : VoiceRequest()
    data class ForReadings(val service: ReadingsService) : VoiceRequest()
}

/**
 * Every word Google Assistant, Android Auto, Gemini and the shortcuts are matched with, in one
 * place: the Android side of VoiceWords in ios/App/App/Voice/VoiceModel.swift; keep the two in
 * step (both have the same tests: VoiceWordsTest.kt and ios/App/VoiceTests/main.swift).
 *
 * The matcher is tolerant: it ignores the verb ("play", "pray", "read me"...), the app's name,
 * and filler, joins words speech recognition splits ("even song", "mid day"), and goes by the time
 * of day a request names. A bare time word ("evening", "bedtime prayers") follows the listener's
 * choice of the Daily Office or Family Prayer; an office's own name ("Evening Prayer", "Vespers")
 * is that office, unless the request says "family".
 */
object VoiceWords {
    /** What people say before the office, ignored. */
    val verbs = listOf(
        "play", "pray", "start", "begin", "say", "read", "read to me", "read me", "listen to",
        "put on", "resume", "continue", "let's pray", "lets pray", "let us pray",
    )

    /** The app's names, ignored (assistants may pass them on). */
    val appNames = listOf("the daily office", "daily office", "daily office 2019", "dailyoffice2019", "the daily office app")

    /** Words speech recognition splits or misspells, and what they are. */
    val respellings = listOf(
        "mid day" to "midday", "noon day" to "noonday", "even song" to "evensong",
        "comp line" to "compline", "complin" to "compline", "compleen" to "compline",
        "complain" to "compline", "mattins" to "matins", "vesper" to "vespers",
        "night time" to "nighttime", "bed time" to "bedtime", "evensongs" to "evensong",
    )

    enum class Hour {
        MORNING, MIDDAY, EVENING, NIGHT;

        fun office(family: Boolean): Office = when (this) {
            MORNING -> if (family) Office.FAMILY_MORNING else Office.MORNING_PRAYER
            MIDDAY -> if (family) Office.FAMILY_MIDDAY else Office.MIDDAY_PRAYER
            EVENING -> if (family) Office.FAMILY_EARLY_EVENING else Office.EVENING_PRAYER
            NIGHT -> if (family) Office.FAMILY_CLOSE_OF_DAY else Office.COMPLINE
        }
    }

    /** An office's own names: the Daily Office office, unless the request says "family". */
    val officeNames = mapOf(
        Hour.MORNING to listOf("morning prayer", "morning office", "matins", "lauds", "daily morning prayer"),
        Hour.MIDDAY to listOf("midday prayer", "noonday prayer", "noon prayer", "noontime prayer", "midday office", "noonday", "sext", "daily midday prayer"),
        Hour.EVENING to listOf("evening prayer", "evensong", "vespers", "evening office", "daily evening prayer"),
        Hour.NIGHT to listOf("compline", "night prayer", "night office", "prayer at the end of the day", "prayers at the end of the day"),
    )

    /** Family Prayer's own names: always Family Prayer. */
    val familyNames = mapOf(
        Hour.MORNING to listOf("family morning prayer", "morning family prayer", "family prayer in the morning"),
        Hour.MIDDAY to listOf("family midday prayer", "family noonday prayer", "family prayer at midday", "family prayer at noon"),
        Hour.EVENING to listOf("family evening prayer", "family early evening prayer", "family prayer in the early evening", "family prayer in the evening", "early evening prayer", "supper prayer", "family supper prayer"),
        Hour.NIGHT to listOf("family bedtime prayer", "family night prayer", "family compline", "family prayer at the close of day", "close of day", "close of the day", "close of day prayer"),
    )

    /** A time of day alone: the listener's usual office for it. */
    val hourWords = mapOf(
        Hour.MORNING to listOf("morning", "this morning", "dawn", "sunrise"),
        Hour.MIDDAY to listOf("midday", "noon", "noontime", "lunchtime", "lunch"),
        Hour.EVENING to listOf("evening", "this evening", "sunset", "supper", "dinner"),
        Hour.NIGHT to listOf("bedtime", "nighttime", "night", "before bed", "end of the day", "end of day", "goodnight", "good night"),
    )

    /** Words that ask for Family Prayer. */
    val familyWords = listOf("family", "families", "kids", "children", "child", "household", "little ones")

    /** Words that ask for the readings, and which. */
    val readingsWords = listOf("reading", "readings", "lesson", "lessons", "lectionary", "scripture", "scriptures", "gospel", "psalms for today", "todays psalms", "the psalms", "psalms", "bible readings")
    val eucharistWords = listOf("eucharist", "mass", "communion", "gospel", "holy eucharist", "sunday", "sundays", "lords supper")

    /** Asking for "the office" in general: the office for now. */
    val genericWords = setOf(
        "office", "offices", "prayer", "prayers", "praying", "hours", "daily", "today",
        "todays", "tonight", "tonights", "next", "now", "current", "my", "our", "the", "a", "some", "for", "with", "in",
        "on", "at", "of", "to", "me", "us", "and", "this", "please", "time", "app", "2019",
        "it", "something", "audio", "aloud", "out", "loud", "go",
    )

    /** Other names for each office (Office.synonyms), for shortcuts and Assistant. */
    val synonyms = mapOf(
        Office.MORNING_PRAYER to listOf("Matins", "Lauds", "Morning Office", "Daily Morning Prayer"),
        Office.MIDDAY_PRAYER to listOf("Noonday Prayer", "Noon Prayer", "Midday Office", "Sext", "Daily Midday Prayer"),
        Office.EVENING_PRAYER to listOf("Evensong", "Vespers", "Evening Office", "Daily Evening Prayer"),
        Office.COMPLINE to listOf("Night Prayer", "Night Office", "Prayer at the End of the Day"),
        Office.FAMILY_MORNING to listOf("Family Morning Prayer", "Morning Family Prayer"),
        Office.FAMILY_MIDDAY to listOf("Family Midday Prayer", "Family Noonday Prayer"),
        Office.FAMILY_EARLY_EVENING to listOf("Family Evening Prayer", "Family Early Evening Prayer", "Family Supper Prayer"),
        Office.FAMILY_CLOSE_OF_DAY to listOf("Family Bedtime Prayer", "Family Night Prayer", "Family Compline", "Close of Day"),
    )

    /** Lowercase words, with punctuation gone and split words joined: "Mid-day Prayer!" is "midday prayer". */
    fun normalize(text: String): String {
        val lowered = text.lowercase()
            .replace('’', '\'')
            .replace('‘', '\'')
            .replace("'", "")
            .map { if (it.isLetterOrDigit()) it else ' ' }
            .joinToString("")
        var padded = " " + lowered.split(' ').filter { it.isNotEmpty() }.joinToString(" ") + " "
        for ((heard, meant) in respellings) {
            padded = padded.replace(" $heard ", " $meant ")
        }
        return padded.trim()
    }

    private fun has(text: String, phrase: String): Boolean = " $text ".contains(" ${normalize(phrase)} ")

    private fun hasAny(text: String, phrases: List<String>?): Boolean = phrases.orEmpty().any { has(text, it) }

    /**
     * What a request asks for, or null if it names something the app doesn't have ("play jazz").
     * Nothing at all, or only "the office", "my prayers", is the office for now.
     */
    fun match(text: String?, prefersFamily: Boolean, now: Calendar = Calendar.getInstance()): VoiceRequest? {
        val words = normalize(text.orEmpty())
        val hour = now.get(Calendar.HOUR_OF_DAY)

        // Readings first: "the morning readings" is the readings, not Morning Prayer.
        if (hasAny(words, readingsWords) || (hasAny(words, eucharistWords) && !hasAny(words, listOf("prayer", "office")))) {
            return VoiceRequest.ForReadings(
                when {
                    hasAny(words, eucharistWords) -> ReadingsService.HOLY_EUCHARIST
                    hasAny(words, listOf("evening", "evensong", "vespers", "tonight")) -> ReadingsService.EVENING_PRAYER
                    hasAny(words, listOf("morning", "matins", "lauds")) -> ReadingsService.MORNING_PRAYER
                    hour < 15 -> ReadingsService.MORNING_PRAYER
                    else -> ReadingsService.EVENING_PRAYER
                },
            )
        }

        val family = hasAny(words, familyWords)
        // Family Prayer's own names, then the offices' names, then a bare time of day; night first,
        // so "close of day" isn't evening.
        val order = listOf(Hour.NIGHT, Hour.EVENING, Hour.MIDDAY, Hour.MORNING)
        order.firstOrNull { hasAny(words, familyNames[it]) }?.let { return VoiceRequest.ForOffice(it.office(true)) }
        order.firstOrNull { hasAny(words, officeNames[it]) }?.let { return VoiceRequest.ForOffice(it.office(family)) }
        order.firstOrNull { hasAny(words, hourWords[it]) }?.let {
            return VoiceRequest.ForOffice(it.office(family || prefersFamily))
        }

        // Anything left must be the verb, the app's name, or "the office": else it's not ours.
        var rest = " $words "
        for (phrase in (verbs + appNames + familyWords).map(::normalize).sortedByDescending { it.length }) {
            rest = rest.replace(" $phrase ", " ").replace(" $phrase ", " ")
        }
        val unknown = rest.split(' ').filter { it.isNotEmpty() && it !in genericWords }
        if (unknown.isNotEmpty()) return null
        return VoiceRequest.ForOffice(Office.current(family || prefersFamily, now))
    }
}
