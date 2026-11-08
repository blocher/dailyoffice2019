package com.dailyoffice2019.app.car

import android.content.Context
import android.net.Uri
import com.dailyoffice2019.app.voice.AppPreferences
import com.dailyoffice2019.app.voice.CalendarApi
import com.dailyoffice2019.app.voice.Office
import com.dailyoffice2019.app.voice.ReadingsService
import com.dailyoffice2019.app.voice.VoiceRequest
import com.dailyoffice2019.app.voice.VoiceWords
import java.io.File
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder
import java.util.Calendar
import org.json.JSONArray
import org.json.JSONObject

/**
 * Finds an office's (or the readings') audio track without the page, for Android Auto and voice
 * search. The Android side of ios/App/App/Car/OfficeAudioResolver.swift; keep the two in step.
 *
 * The request must be exactly the one the page would make, so it gets the same track (the same
 * cached clips, never newly generated audio) for the listener's settings and extra collects. The
 * page saves its addresses as templates (app/src/helpers/nativeAudioRequests.js); before it has,
 * the address is built here the same way from the settings it saved. A track downloaded for
 * offline listening plays from the phone.
 */
object OfficeAudioResolver {
    sealed class Request {
        abstract val title: String

        data class ForOffice(val office: Office) : Request() {
            override val title: String get() = office.title
        }

        data class ForReadings(val service: ReadingsService) : Request() {
            override val title: String get() = "Readings for ${service.title}"
        }
    }

    data class Track(val uri: Uri, val title: String)

    class Failure(message: String) : IOException(message)

    const val NO_AUDIO = "Audio isn’t available for these settings. It is read in English, for the ESV and KJV."
    const val UNREACHABLE = "The Daily Office couldn’t reach its audio. Check the connection and try again."
    const val STILL_PREPARING = "This audio is still being prepared. Try again in a minute."

    private const val API = "https://api.dailyoffice2019.com/"
    private const val PREPARING_LIMIT_MS = 90_000L

    /**
     * The day an office is prayed: before 4 a.m., Compline and the Close of Day are still the night
     * before's (as the app's home page has it).
     */
    fun day(request: Request, now: Calendar = Calendar.getInstance()): Calendar {
        val late = request is Request.ForOffice &&
            (request.office == Office.COMPLINE || request.office == Office.FAMILY_CLOSE_OF_DAY)
        return (now.clone() as Calendar).apply {
            if (late && get(Calendar.HOUR_OF_DAY) < 4) add(Calendar.DAY_OF_MONTH, -1)
        }
    }

    /** Blocking: call from a background thread. */
    fun resolve(context: Context, request: Request, now: Calendar = Calendar.getInstance()): Track {
        val address = requestAddress(context, request, day(request, now))
        val giveUpAt = System.currentTimeMillis() + PREPARING_LIMIT_MS
        var failures = 0
        while (true) {
            val audio = try {
                fetchAudio(address)
            } catch (failure: Failure) {
                throw failure
            } catch (_: IOException) {
                failures += 1
                if (failures > 2) throw Failure(UNREACHABLE)
                Thread.sleep(failures * 2_000L)
                continue
            }
            if (audio.optString("status") == "preparing") {
                if (System.currentTimeMillis() >= giveUpAt) throw Failure(STILL_PREPARING)
                val wait = audio.optDouble("retry_after", 5.0).coerceIn(2.0, 30.0)
                Thread.sleep((wait * 1000).toLong())
                continue
            }
            val raw = audio.optJSONArray("single_track")?.optString(0)?.takeIf { it.isNotEmpty() }
                ?: throw Failure(NO_AUDIO)
            val track = trackUrl(raw) ?: throw Failure(NO_AUDIO)
            val stored = storedFile(context, track)
            return Track(if (stored != null) Uri.fromFile(stored) else Uri.parse(track), request.title)
        }
    }

    private fun fetchAudio(address: String): JSONObject {
        val connection = (URL(address).openConnection() as HttpURLConnection).apply {
            connectTimeout = 15_000
            readTimeout = 30_000
        }
        try {
            val status = connection.responseCode
            if (status in 400..499) throw Failure(NO_AUDIO)
            if (status != 200 && status != 202) throw IOException("HTTP $status")
            val text = connection.inputStream.bufferedReader().use { it.readText() }
            return JSONObject(text).optJSONObject("audio") ?: JSONObject()
        } finally {
            connection.disconnect()
        }
    }

    // The page's addresses

    private fun stored(context: Context, key: String): String? =
        context.getSharedPreferences("CapacitorStorage", Context.MODE_PRIVATE).getString(key, null)

    /** The address the page asks for this request's audio with, for this day. */
    fun requestAddress(context: Context, request: Request, day: Calendar): String {
        val date = CalendarApi.apiDate(day)
        val templates = stored(context, "nativeAudioRequests")?.let {
            try {
                JSONObject(it)
            } catch (_: Exception) {
                null
            }
        }
        return when (request) {
            is Request.ForOffice -> {
                val key = "${request.office.serviceType}/${request.office.slug}"
                val template = templates?.optJSONObject("offices")?.optString(key)?.takeIf { it.isNotEmpty() }
                    ?: fallbackOfficeTemplate(context, request.office)
                template.replace("{date}", date)
            }
            is Request.ForReadings -> {
                val template = templates?.optString("readings")?.takeIf { it.isNotEmpty() }
                    ?: fallbackReadingsTemplate(context)
                template.replace("{kind}", request.service.slug).replace("{date}", date)
            }
        }
    }

    /** The saved settings as the page wrote them, in their order (the query lists them in it). */
    fun orderedSettings(json: String?): List<Pair<String, String>> {
        if (json == null) return emptyList()
        val pattern = Regex("\"((?:[^\"\\\\]|\\\\.)*)\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"")
        return pattern.findAll(json).map { it.groupValues[1] to it.groupValues[2] }.toList()
    }

    /** As app/src/offline/urls.js officeUrl builds it. */
    fun fallbackOfficeTemplate(context: Context, office: Office): String {
        val settings = orderedSettings(stored(context, "settings")).toMutableList()
        if (settings.none { it.first == "bible_translation" && it.second.isNotEmpty() }) {
            settings.removeAll { it.first == "bible_translation" }
            settings += "bible_translation" to "esv"
        }
        val query = settings.joinToString("&") { "${it.first}=${it.second}" }
        var collects = ""
        if (office.serviceType == "office") {
            try {
                val chosen = stored(context, "extraCollects")?.let { JSONObject(it) }
                val list: JSONArray? = chosen?.optJSONArray(office.title)
                if (list != null) collects = (0 until list.length()).joinToString(",") { list.get(it).toString() }
            } catch (_: Exception) {
                // No extra collects.
            }
        }
        return "${API}api/v1/${office.serviceType}/${office.slug}/{date}?$query&extra_collects=$collects&include_audio_links=true"
    }

    /** As the Readings page builds it. */
    fun fallbackReadingsTemplate(context: Context): String {
        val settings = orderedSettings(stored(context, "settings")).toMap()
        var translation = stored(context, "readings_translation").orEmpty()
        if (translation.isEmpty() || translation == "undefined") translation = settings["bible_translation"] ?: "esv"
        val values = listOf(
            "translation" to translation,
            "psalms" to (stored(context, "psalms_translation") ?: settings["language_style"] ?: "undefined"),
            "style" to (stored(context, "psalm_style") ?: settings["psalm_style"] ?: "undefined"),
            "psalter" to (stored(context, "psalter") ?: settings["psalter"] ?: "undefined"),
            "position" to "0",
            "include_audio_links" to "true",
        )
        val query = values.joinToString("&") { "${it.first}=${URLEncoder.encode(it.second, "UTF-8")}" }
        return "${API}api/v1/readings_audio/{kind}/{date}?$query"
    }

    // The track

    /** The API names the track by its own address; play it from the API's (officeAudio.js resolveAudioUrl). */
    fun trackUrl(raw: String): String? {
        val parsed = try {
            URL(raw)
        } catch (_: Exception) {
            return null
        }
        val path = parsed.path.removePrefix("/")
        val query = parsed.query
        return API + path + if (query.isNullOrEmpty()) "" else "?$query"
    }

    /**
     * A track downloaded for offline listening (app/src/offline/audio.js): in the app's files
     * directory under offline-audio, named by the hash of its address without "reload".
     */
    fun storedFile(context: Context, track: String): File? {
        val uri = Uri.parse(track)
        val kept = uri.queryParameterNames.filter { it != "reload" }
        val builder = uri.buildUpon().clearQuery()
        for (name in kept) uri.getQueryParameters(name).forEach { builder.appendQueryParameter(name, it) }
        val key = builder.build().toString()
        val file = File(context.filesDir, "offline-audio/${hashString(key)}.mp3")
        return if (file.exists()) file else null
    }

    /** FNV-1a over UTF-16 code units, in base 36: app/src/offline/keys.js hashString. */
    fun hashString(value: String): String {
        var hash = 0x811C9DC5.toInt()
        for (char in value) {
            hash = hash xor char.code
            hash *= 0x01000193
        }
        return (hash.toLong() and 0xFFFFFFFFL).toString(36)
    }

    /**
     * What a voice search asks for ("play Evening Prayer on Daily Office", "evensong", "today's
     * readings"), by the words in voice/VoiceWords.kt. An empty search is the office for now; null
     * for words the app has nothing for.
     */
    fun requestFor(context: Context, query: String?, now: Calendar = Calendar.getInstance()): Request? =
        when (val match = VoiceWords.match(query, AppPreferences(context).prefersFamilyPrayer, now)) {
            is VoiceRequest.ForOffice -> Request.ForOffice(match.office)
            is VoiceRequest.ForReadings -> Request.ForReadings(match.service)
            null -> null
        }
}
