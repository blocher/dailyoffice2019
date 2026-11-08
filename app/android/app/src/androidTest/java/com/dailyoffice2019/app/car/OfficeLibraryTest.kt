package com.dailyoffice2019.app.car

import android.content.ComponentName
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.session.MediaBrowser
import androidx.media3.session.SessionToken
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.dailyoffice2019.app.audio.PlaybackService
import com.dailyoffice2019.app.voice.Office
import com.dailyoffice2019.app.voice.VoicePlayback
import java.util.concurrent.Callable
import java.util.concurrent.FutureTask
import java.util.concurrent.TimeUnit
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

/**
 * The library Android Auto browses and plays (OfficeLibrary.kt), through a MediaBrowser as Android
 * Auto connects, and the audio lookup it relies on (OfficeAudioResolver.kt). Needs the network.
 */
@RunWith(AndroidJUnit4::class)
class OfficeLibraryTest {
    private val context = InstrumentationRegistry.getInstrumentation().targetContext
    private val main = Handler(Looper.getMainLooper())
    private lateinit var browser: MediaBrowser

    private fun <T> onMain(work: () -> T): T {
        val task = FutureTask(Callable { work() })
        main.post(task)
        return task.get(30, TimeUnit.SECONDS)
    }

    @Before
    fun connect() {
        val token = SessionToken(context, ComponentName(context, PlaybackService::class.java))
        val future = onMain { MediaBrowser.Builder(context, token).buildAsync() }
        browser = future.get(30, TimeUnit.SECONDS)
    }

    @After
    fun release() {
        onMain {
            browser.stop()
            browser.clearMediaItems()
            browser.release()
        }
    }

    @Test
    fun browsesPrayAndReadings() {
        val root = onMain { browser.getLibraryRoot(null) }.get(10, TimeUnit.SECONDS).value
        assertNotNull(root)
        val folders = onMain { browser.getChildren(root!!.mediaId, 0, 20, null) }.get(10, TimeUnit.SECONDS).value!!
        assertEquals(listOf("pray", "readings"), folders.map { it.mediaId })

        val offices = onMain { browser.getChildren("pray", 0, 50, null) }.get(10, TimeUnit.SECONDS).value!!
        assertEquals(10, offices.size)
        assertEquals("office:now", offices[0].mediaId)
        assertTrue(offices.all { it.mediaMetadata.isPlayable == true })

        val readings = onMain { browser.getChildren("readings", 0, 50, null) }.get(10, TimeUnit.SECONDS).value!!
        assertEquals(listOf("readings:morning_prayer", "readings:evening_prayer", "readings:holy_eucharist"), readings.map { it.mediaId })
    }

    @Test
    fun playsAnOfficeFromTheLibrary() {
        onMain {
            browser.setMediaItem(MediaItem.Builder().setMediaId("office:${Office.COMPLINE.key}").build())
            browser.prepare()
            browser.play()
        }
        // Finding the audio can take a moment (the API may prepare it first).
        val deadline = SystemClock.elapsedRealtime() + 90_000
        var mediaId: String? = null
        var state = Player.STATE_IDLE
        while (SystemClock.elapsedRealtime() < deadline) {
            val (id, playbackState) = onMain { browser.currentMediaItem?.mediaId to browser.playbackState }
            mediaId = id
            state = playbackState
            if (state == Player.STATE_READY && mediaId?.startsWith("https://api.dailyoffice2019.com/api/v1/audio_track/") == true) break
            SystemClock.sleep(500)
        }
        assertTrue("loaded $mediaId", mediaId?.startsWith("https://api.dailyoffice2019.com/api/v1/audio_track/") == true)
        assertEquals(Player.STATE_READY, state)
        assertEquals("Compline", onMain { browser.mediaMetadata.title?.toString() })
    }

    @Test
    fun hashesTrackAddressesAsThePageDoes() {
        // Values from app/src/offline/keys.js hashString.
        assertEquals(
            "19bffbm",
            OfficeAudioResolver.hashString(
                "https://api.dailyoffice2019.com/api/v1/audio_track/elevenlabs/37076059-fda8-5daf-abc7-9fbf4e448763.mp3",
            ),
        )
        assertEquals("2hb05i", OfficeAudioResolver.hashString("é ✠ Lᴏʀᴅ"))
    }

    @Test
    fun understandsVoiceSearches() {
        fun office(query: String) = (OfficeAudioResolver.requestFor(context, query) as OfficeAudioResolver.Request.ForOffice).office
        assertEquals(Office.COMPLINE, office("Compline"))
        assertEquals(Office.EVENING_PRAYER, office("play evensong"))
        assertEquals(Office.FAMILY_MORNING, office("family morning prayer"))
        assertEquals(Office.MIDDAY_PRAYER, office("Play Midday Prayer on the Daily Office"))
        assertEquals(Office.MIDDAY_PRAYER, office("noon day prayer"))
        assertTrue(OfficeAudioResolver.requestFor(context, "today's readings") is OfficeAudioResolver.Request.ForReadings)
        // Empty: the office for now. Something the app doesn't have: nothing.
        assertNotNull(OfficeAudioResolver.requestFor(context, ""))
        assertNull(OfficeAudioResolver.requestFor(context, "jazz"))
    }

    @Test
    fun searchesTheLibrary() {
        onMain { browser.search("vespers", null) }.get(10, TimeUnit.SECONDS)
        val found = onMain { browser.getSearchResult("vespers", 0, 10, null) }.get(10, TimeUnit.SECONDS).value!!
        assertEquals(listOf("office:evening_prayer"), found.map { it.mediaId })
        val none = onMain { browser.getSearchResult("jazz", 0, 10, null) }.get(10, TimeUnit.SECONDS).value!!
        assertTrue(none.isEmpty())
    }

    /** As Assistant's "play Evensong on Daily Office" arrives (playFromSearch, or VoicePlayActivity). */
    @Test
    fun playsAVoiceSearch() {
        onMain {
            browser.setMediaItem(VoicePlayback.item(null, "play even song on the daily office"))
            browser.prepare()
            browser.play()
        }
        val deadline = SystemClock.elapsedRealtime() + 90_000
        var title: String? = null
        while (SystemClock.elapsedRealtime() < deadline) {
            title = onMain { browser.mediaMetadata.title?.toString() }
            if (title == "Evening Prayer" && onMain { browser.playbackState } == Player.STATE_READY) break
            SystemClock.sleep(500)
        }
        assertEquals("Evening Prayer", title)
    }
}
