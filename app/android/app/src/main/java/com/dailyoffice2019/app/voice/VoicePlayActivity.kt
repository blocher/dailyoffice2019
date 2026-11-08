package com.dailyoffice2019.app.voice

import android.app.Activity
import android.app.SearchManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.MediaStore
import android.widget.Toast
import androidx.annotation.OptIn
import androidx.core.content.ContextCompat
import androidx.media3.common.MediaItem
import androidx.media3.common.PlaybackException
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.session.MediaController
import androidx.media3.session.SessionError
import androidx.media3.session.SessionToken
import com.dailyoffice2019.app.audio.PlaybackService

/**
 * Plays an office without showing the page: Google Assistant's "play Evening Prayer on Daily
 * Office" (android.media.action.MEDIA_PLAY_FROM_SEARCH, with the words heard), and the play
 * actions Gemini starts (DailyOfficeAppFunctions, with a library id such as "office:compline").
 *
 * It asks PlaybackService to play, as Android Auto does (car/OfficeLibrary.kt matches the words
 * with VoiceWords.kt and finds the track the page would), and stays open, invisible, until the
 * audio starts, so Android lets the player run in the foreground. Then it closes; the office keeps
 * playing with the phone locked, with its notification controls.
 */
class VoicePlayActivity : Activity() {
    companion object {
        const val EXTRA_MEDIA_ID = "com.dailyoffice2019.app.MEDIA_ID"
        private const val WAIT_MS = 20_000L

        /** Starts playing a library id ("office:compline", "readings:morning_prayer", "office:now"). */
        fun intent(context: Context, mediaId: String): Intent =
            Intent(context, VoicePlayActivity::class.java)
                .putExtra(EXTRA_MEDIA_ID, mediaId)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    }

    private var controller: MediaController? = null
    private val handler = Handler(Looper.getMainLooper())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val mediaId = intent.getStringExtra(EXTRA_MEDIA_ID)
        val query = if (intent.action == MediaStore.INTENT_ACTION_MEDIA_PLAY_FROM_SEARCH) {
            intent.getStringExtra(SearchManager.QUERY).orEmpty()
        } else {
            null
        }
        play(mediaId, query)
        handler.postDelayed({ done() }, WAIT_MS)
    }

    @OptIn(UnstableApi::class)
    private fun play(mediaId: String?, query: String?) {
        val token = SessionToken(this, ComponentName(this, PlaybackService::class.java))
        val future = MediaController.Builder(applicationContext, token)
            .setListener(
                object : MediaController.Listener {
                    override fun onError(controller: MediaController, sessionError: SessionError) {
                        fail(sessionError.message)
                    }
                },
            )
            .buildAsync()
        future.addListener(
            {
                val connected = try {
                    future.get()
                } catch (_: Exception) {
                    fail(null)
                    return@addListener
                }
                controller = connected
                connected.addListener(
                    object : Player.Listener {
                        override fun onIsPlayingChanged(isPlaying: Boolean) {
                            if (isPlaying) done()
                        }

                        override fun onPlayerError(error: PlaybackException) {
                            fail(null)
                        }
                    },
                )
                val item = VoicePlayback.item(mediaId, query)
                connected.setMediaItem(item)
                connected.prepare()
                connected.play()
            },
            ContextCompat.getMainExecutor(this),
        )
    }

    private fun fail(message: String?) {
        Toast.makeText(
            applicationContext,
            message?.takeIf { it.isNotBlank() } ?: "The Daily Office couldn’t start the audio. Open the app to try again.",
            Toast.LENGTH_LONG,
        ).show()
        done()
    }

    private fun done() {
        handler.removeCallbacksAndMessages(null)
        if (!isFinishing) finish()
    }

    override fun onDestroy() {
        // The service plays on without us.
        controller?.release()
        controller = null
        super.onDestroy()
    }
}

/** What a voice request asks the player for. */
object VoicePlayback {
    /** An item for PlaybackService: a library id, or a search ("" is the office for now). */
    fun item(mediaId: String?, query: String?): MediaItem =
        MediaItem.Builder()
            .setMediaId(mediaId.orEmpty())
            .setRequestMetadata(MediaItem.RequestMetadata.Builder().setSearchQuery(query ?: if (mediaId == null) "" else null).build())
            .build()
}
