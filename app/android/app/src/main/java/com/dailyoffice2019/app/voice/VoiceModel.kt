package com.dailyoffice2019.app.voice

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.net.toUri
import com.dailyoffice2019.app.MainActivity
import com.dailyoffice2019.app.R
import java.util.Calendar
import org.json.JSONArray
import org.json.JSONObject

/*
 * What Google Assistant, Gemini and the home-screen shortcuts can open, play, and answer: the
 * Android side of ios/App/App/Voice/VoiceModel.swift.
 *
 * Voice requests open the app at one of its pages (a dailyoffice2019:// link the App plugin hands
 * to app/src/helpers/voice.js); ?autoplay=1 has the page start the audio. Questions are answered
 * from the calendar API without opening the app (LiturgicalAnswers.kt).
 */

/** One of the eight offices, daily or family. */
enum class Office(val serviceType: String, val slug: String, val title: String) {
    MORNING_PRAYER("office", "morning_prayer", "Morning Prayer"),
    MIDDAY_PRAYER("office", "midday_prayer", "Midday Prayer"),
    EVENING_PRAYER("office", "evening_prayer", "Evening Prayer"),
    COMPLINE("office", "compline", "Compline"),
    FAMILY_MORNING("family", "morning_prayer", "Family Prayer in the Morning"),
    FAMILY_MIDDAY("family", "midday_prayer", "Family Prayer at Midday"),
    FAMILY_EARLY_EVENING("family", "early_evening_prayer", "Family Prayer in the Early Evening"),
    FAMILY_CLOSE_OF_DAY("family", "close_of_day_prayer", "Family Prayer at the Close of Day");

    /** Other names people use for it (VoiceWords has every word the matcher knows). */
    val synonyms: List<String> get() = VoiceWords.synonyms[this].orEmpty()

    /** The app's page for this office today. */
    val path: String get() = "/$serviceType/$slug"

    /** The name AppFunctions take for it: "compline", "family_close_of_day". */
    val key: String get() = name.lowercase()

    companion object {
        fun find(serviceType: String?, slug: String?): Office? =
            entries.firstOrNull { it.serviceType == (serviceType ?: "office") && it.slug == slug }

        /**
         * The office for this time of day, as the home page chooses it (Today.vue): before 4 a.m.
         * still the night before, then morning until 11, midday until 3, evening until 8.
         */
        fun current(family: Boolean, now: Calendar = Calendar.getInstance()): Office =
            when (now.get(Calendar.HOUR_OF_DAY)) {
                in 4 until 11 -> if (family) FAMILY_MORNING else MORNING_PRAYER
                in 11 until 15 -> if (family) FAMILY_MIDDAY else MIDDAY_PRAYER
                in 15 until 20 -> if (family) FAMILY_EARLY_EVENING else EVENING_PRAYER
                else -> if (family) FAMILY_CLOSE_OF_DAY else COMPLINE
            }

        /**
         * An office named the way an assistant might name it: "compline", "evensong",
         * "family_close_of_day", "now", "family". Null for anything else.
         */
        fun named(name: String?, context: Context): Office? {
            val wanted = name?.trim()?.lowercase()?.replace('-', '_')?.replace(' ', '_')
            if (wanted.isNullOrEmpty() || wanted == "now" || wanted == "the_office") {
                return current(AppPreferences(context).prefersFamilyPrayer)
            }
            if (wanted == "family" || wanted == "family_prayer" || wanted == "family_now") return current(true)
            entries.firstOrNull { office ->
                office.key == wanted ||
                    office.title.lowercase().replace(' ', '_') == wanted ||
                    office.synonyms.any { it.lowercase().replace(' ', '_') == wanted }
            }?.let { return it }
            // Any other way of saying it ("noonday", "bedtime prayers with the kids").
            val spoken = VoiceWords.match(wanted.replace('_', ' '), AppPreferences(context).prefersFamilyPrayer)
            return (spoken as? VoiceRequest.ForOffice)?.office
        }
    }
}

/** Which readings: the offices' or the Eucharist's (the Readings page's tabs). */
enum class ReadingsService(val slug: String, val title: String) {
    MORNING_PRAYER("morning_prayer", "Morning Prayer"),
    EVENING_PRAYER("evening_prayer", "Evening Prayer"),
    HOLY_EUCHARIST("holy_eucharist", "Holy Eucharist");

    val path: String get() = "/readings/$slug/"

    companion object {
        fun named(name: String?, now: Calendar = Calendar.getInstance()): ReadingsService {
            val wanted = name?.trim()?.lowercase()?.replace(' ', '_').orEmpty()
            return when {
                wanted.isEmpty() -> forNow(now)
                wanted.contains("eucharist") || wanted.contains("mass") || wanted.contains("communion") -> HOLY_EUCHARIST
                wanted.contains("evening") -> EVENING_PRAYER
                wanted.contains("morning") -> MORNING_PRAYER
                else -> entries.firstOrNull { it.slug == wanted } ?: forNow(now)
            }
        }

        /** Morning Prayer's until 3 p.m., then Evening Prayer's. */
        fun forNow(now: Calendar = Calendar.getInstance()): ReadingsService =
            if (now.get(Calendar.HOUR_OF_DAY) < 15) MORNING_PRAYER else EVENING_PRAYER
    }
}

/**
 * The listener's settings, as the page saved them with Capacitor Preferences
 * (app/src/helpers/storage.js): SharedPreferences named "CapacitorStorage".
 */
class AppPreferences(context: Context) {
    private val preferences = context.getSharedPreferences("CapacitorStorage", Context.MODE_PRIVATE)

    /** The settings object (bible_translation, psalter, ...), or empty. */
    val settings: Map<String, String>
        get() {
            val json = preferences.getString("settings", null) ?: return emptyMap()
            return try {
                val obj = JSONObject(json)
                obj.keys().asSequence().associateWith { obj.optString(it) }
            } catch (_: Exception) {
                emptyMap()
            }
        }

    /** Whether the listener last prayed Family Prayer rather than the Daily Office. */
    val prefersFamilyPrayer: Boolean get() = preferences.getString("serviceType", null) == "family"
}

/** Builds the addresses the app opens at (helpers/voice.js reads them back). */
object VoiceLinks {
    const val SCHEME = "dailyoffice2019"

    fun uri(path: String, autoplay: Boolean = false): Uri {
        val clean = if (path.startsWith("/")) path else "/$path"
        val withPlay = if (autoplay) clean + (if (clean.contains("?")) "&" else "?") + "autoplay=1" else clean
        return "$SCHEME://open$withPlay".toUri()
    }

    /** Opens MainActivity at a page. */
    fun intent(context: Context, path: String, autoplay: Boolean = false): Intent =
        Intent(Intent.ACTION_VIEW, uri(path, autoplay))
            .setClass(context, MainActivity::class.java)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_SINGLE_TOP)

    /** The same, for an assistant to start (AppFunctions return these). */
    fun pendingIntent(context: Context, path: String, autoplay: Boolean = false): PendingIntent =
        PendingIntent.getActivity(
            context,
            (path + autoplay).hashCode(),
            intent(context, path, autoplay),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )

    fun dayPath(day: Calendar): String =
        "/day/${day.get(Calendar.YEAR)}/${day.get(Calendar.MONTH) + 1}/${day.get(Calendar.DAY_OF_MONTH)}/"

    fun readingsPath(service: ReadingsService, day: Calendar): String =
        "/readings/${service.slug}/${day.get(Calendar.YEAR)}/${day.get(Calendar.MONTH) + 1}/${day.get(Calendar.DAY_OF_MONTH)}"
}

/** A psalm from the bundled list (res/raw/psalms.json, from app/scripts/build-voice-psalms.mjs). */
data class PsalmInfo(val number: Int, val latinTitle: String, val topics: List<String>) {
    val title: String get() = "Psalm $number"
    val path: String get() = "/psalm/$number/"

    companion object {
        @Volatile private var cached: List<PsalmInfo>? = null

        fun all(context: Context): List<PsalmInfo> {
            cached?.let { return it }
            val list = try {
                val text = context.resources.openRawResource(R.raw.psalms).bufferedReader().use { it.readText() }
                val array = JSONArray(text)
                (0 until array.length()).map { index ->
                    val psalm = array.getJSONObject(index)
                    val topics = psalm.optJSONArray("topics") ?: JSONArray()
                    PsalmInfo(
                        psalm.getInt("number"),
                        psalm.optString("latin_title"),
                        (0 until topics.length()).map { topics.getString(it) },
                    )
                }
            } catch (_: Exception) {
                (1..150).map { PsalmInfo(it, "", emptyList()) }
            }
            cached = list
            return list
        }

        /** Psalms whose number, Latin title, or topics match the words asked for. */
        fun search(context: Context, text: String): List<PsalmInfo> {
            val query = text.lowercase().replace("psalm", "").trim()
            val all = all(context)
            if (query.isEmpty()) return all
            query.toIntOrNull()?.let { number -> return all.filter { it.number == number } }
            romanValue(query.uppercase())?.let { number -> return all.filter { it.number == number } }
            return all.filter { psalm ->
                psalm.latinTitle.lowercase().contains(query) || psalm.topics.any { it.lowercase().contains(query) }
            }
        }

        private fun romanValue(text: String): Int? {
            val values = mapOf('I' to 1, 'V' to 5, 'X' to 10, 'L' to 50, 'C' to 100)
            if (text.isEmpty() || text.any { it !in values }) return null
            var total = 0
            var previous = 0
            for (character in text.reversed()) {
                val value = values.getValue(character)
                total += if (value < previous) -value else value
                previous = maxOf(previous, value)
            }
            return total
        }
    }
}
