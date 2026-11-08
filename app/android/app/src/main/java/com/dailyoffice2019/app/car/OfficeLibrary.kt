package com.dailyoffice2019.app.car

import android.content.Context
import androidx.annotation.OptIn
import androidx.core.content.ContextCompat
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.session.LibraryResult
import androidx.media3.session.MediaLibraryService.LibraryParams
import androidx.media3.session.MediaLibraryService.MediaLibrarySession
import androidx.media3.session.MediaSession
import androidx.media3.session.MediaSession.MediaItemsWithStartPosition
import androidx.media3.session.SessionError
import androidx.media3.session.SessionResult
import com.dailyoffice2019.app.voice.Office
import com.dailyoffice2019.app.voice.ReadingsService
import com.google.common.collect.ImmutableList
import com.google.common.util.concurrent.Futures
import com.google.common.util.concurrent.ListenableFuture
import com.google.common.util.concurrent.MoreExecutors
import java.util.concurrent.Executors

/**
 * What Android Auto (and Assistant's "play Compline on Daily Office") browses and plays: a Pray
 * folder with the office for now and all eight offices, and a Readings folder. Choosing one finds
 * its audio (OfficeAudioResolver) and plays it in PlaybackService's player, the same one the page
 * uses. The Android side of ios/App/App/Car/CarPlaySceneDelegate.swift.
 *
 * Voice requests ("play Evening Prayer on Daily Office" in the car or to Assistant, and the
 * MEDIA_PLAY_FROM_SEARCH that voice/VoicePlayActivity.kt passes on) arrive as a search query,
 * matched by voice/VoiceWords.kt; an empty one is the office for now. Play with nothing worth
 * resuming (nothing loaded, an office that finished, or one paused for hours) plays the office
 * for now too, rather than this morning's office in the evening.
 *
 * Library ids: "office:now", "office:family-now", "office:<office key>", "readings:<slug>".
 * The page's own items carry their audio address instead (NativeAudioPlugin), and only this app
 * may load an address.
 */
@OptIn(UnstableApi::class)
class OfficeLibrary(private val context: Context) : MediaLibrarySession.Callback {

    private val executor = MoreExecutors.listeningDecorator(Executors.newSingleThreadExecutor())

    companion object {
        const val ROOT = "root"
        const val PRAY = "pray"
        const val READINGS = "readings"
        private const val ARTIST = "The Daily Office"

        /** A paused office older than this is not resumed by a bare "play" from outside the app. */
        const val STALE_AFTER_MS = 2 * 60 * 60 * 1000L
    }

    // When the player last played or paused, to tell a paused office from a stale one.
    @Volatile private var lastActive = System.currentTimeMillis()

    /** Follows the session's player (PlaybackService), for STALE_AFTER_MS. */
    fun watch(player: Player) {
        player.addListener(
            object : Player.Listener {
                override fun onIsPlayingChanged(isPlaying: Boolean) {
                    lastActive = System.currentTimeMillis()
                }

                override fun onPlaybackStateChanged(playbackState: Int) {
                    lastActive = System.currentTimeMillis()
                }
            },
        )
    }

    /** Nothing loaded, an office that has finished, or one paused for hours. */
    fun nothingToResume(player: Player, now: Long = System.currentTimeMillis()): Boolean =
        player.mediaItemCount == 0 ||
            player.playbackState == Player.STATE_ENDED ||
            (!player.isPlaying && now - lastActive > STALE_AFTER_MS)

    private fun folder(id: String, title: String) = MediaItem.Builder()
        .setMediaId(id)
        .setMediaMetadata(
            MediaMetadata.Builder()
                .setTitle(title)
                .setIsBrowsable(true)
                .setIsPlayable(false)
                .setMediaType(MediaMetadata.MEDIA_TYPE_FOLDER_MIXED)
                .build(),
        )
        .build()

    private fun playable(id: String, title: String, subtitle: String?) = MediaItem.Builder()
        .setMediaId(id)
        .setMediaMetadata(
            MediaMetadata.Builder()
                .setTitle(title)
                .setDisplayTitle(title)
                .setSubtitle(subtitle ?: ARTIST)
                .setArtist(ARTIST)
                .setIsBrowsable(false)
                .setIsPlayable(true)
                .setMediaType(MediaMetadata.MEDIA_TYPE_PODCAST_EPISODE)
                .build(),
        )
        .build()

    private fun children(parentId: String): List<MediaItem>? = when (parentId) {
        ROOT -> listOf(folder(PRAY, "Pray"), folder(READINGS, "Readings"))
        PRAY -> {
            val now = Office.named("now", context)!!
            val family = Office.named("family", context)!!
            listOf(
                playable("office:now", now.title, "For this time of day"),
                playable("office:family-now", family.title, "Family Prayer for now"),
            ) + Office.entries.map { playable("office:${it.key}", it.title, null) }
        }
        READINGS -> ReadingsService.entries.map {
            playable("readings:${it.slug}", "Readings for ${it.title}", "Psalms and lessons, read aloud")
        }
        else -> null
    }

    private fun request(mediaId: String): OfficeAudioResolver.Request? = when {
        mediaId == "office:now" -> OfficeAudioResolver.Request.ForOffice(Office.named("now", context)!!)
        mediaId == "office:family-now" -> OfficeAudioResolver.Request.ForOffice(Office.named("family", context)!!)
        mediaId.startsWith("office:") ->
            Office.entries.firstOrNull { it.key == mediaId.removePrefix("office:") }?.let {
                OfficeAudioResolver.Request.ForOffice(it)
            }
        mediaId.startsWith("readings:") ->
            ReadingsService.entries.firstOrNull { it.slug == mediaId.removePrefix("readings:") }?.let {
                OfficeAudioResolver.Request.ForReadings(it)
            }
        else -> null
    }

    /** The track's item, as the page names it (by its address), so the page can follow it. */
    private fun trackItem(track: OfficeAudioResolver.Track): MediaItem = MediaItem.Builder()
        .setMediaId(track.uri.toString())
        .setUri(track.uri)
        .setMediaMetadata(
            MediaMetadata.Builder()
                .setTitle(track.title)
                .setDisplayTitle(track.title)
                .setArtist(ARTIST)
                .setSubtitle(ARTIST)
                .setMediaType(MediaMetadata.MEDIA_TYPE_PODCAST_EPISODE)
                .build(),
        )
        .build()

    /** A voice search's answer, as a library item ("office:compline"), or null. */
    fun searchResult(query: String?): MediaItem? {
        val request = OfficeAudioResolver.requestFor(context, query) ?: return null
        val id = when (request) {
            is OfficeAudioResolver.Request.ForOffice -> "office:${request.office.key}"
            is OfficeAudioResolver.Request.ForReadings -> "readings:${request.service.slug}"
        }
        return playable(id, request.title, null)
    }

    private fun notOurs(query: String?) = OfficeAudioResolver.Failure(
        "The Daily Office has no “${query.orEmpty().trim()}”. Try Morning Prayer, Compline, or today’s readings.",
    )

    override fun onGetLibraryRoot(
        session: MediaLibrarySession,
        browser: MediaSession.ControllerInfo,
        params: LibraryParams?,
    ): ListenableFuture<LibraryResult<MediaItem>> =
        Futures.immediateFuture(LibraryResult.ofItem(folder(ROOT, ARTIST), params))

    override fun onGetChildren(
        session: MediaLibrarySession,
        browser: MediaSession.ControllerInfo,
        parentId: String,
        page: Int,
        pageSize: Int,
        params: LibraryParams?,
    ): ListenableFuture<LibraryResult<ImmutableList<MediaItem>>> {
        val items = children(parentId)
            ?: return Futures.immediateFuture(LibraryResult.ofError(SessionError.ERROR_BAD_VALUE))
        val from = (page * pageSize).coerceAtMost(items.size)
        val to = (from + pageSize).coerceAtMost(items.size)
        return Futures.immediateFuture(LibraryResult.ofItemList(items.subList(from, to), params))
    }

    override fun onGetItem(
        session: MediaLibrarySession,
        browser: MediaSession.ControllerInfo,
        mediaId: String,
    ): ListenableFuture<LibraryResult<MediaItem>> {
        val item = listOf(ROOT, PRAY, READINGS).flatMap { children(it).orEmpty() }.firstOrNull { it.mediaId == mediaId }
            ?: if (mediaId == ROOT) folder(ROOT, ARTIST) else null
        return Futures.immediateFuture(
            if (item != null) LibraryResult.ofItem(item, null) else LibraryResult.ofError(SessionError.ERROR_BAD_VALUE),
        )
    }

    /**
     * Turns what a controller asks to play into playable items: the page's own (with its address),
     * a library id, or a voice search. Finding the audio may take a moment (it can be prepared on
     * the server first), so it runs off the main thread.
     */
    override fun onAddMediaItems(
        mediaSession: MediaSession,
        controller: MediaSession.ControllerInfo,
        mediaItems: MutableList<MediaItem>,
    ): ListenableFuture<MutableList<MediaItem>> {
        val ownApp = controller.packageName == context.packageName
        // The page's items already carry their address; only this app may load one.
        if (mediaItems.all { it.requestMetadata.mediaUri != null }) {
            if (!ownApp) return Futures.immediateFailedFuture(UnsupportedOperationException())
            return Futures.immediateFuture(
                mediaItems.map { it.buildUpon().setUri(it.requestMetadata.mediaUri).build() }.toMutableList(),
            )
        }
        val future = executor.submit<MutableList<MediaItem>> {
            mediaItems.map { item ->
                val uri = item.requestMetadata.mediaUri
                if (uri != null && ownApp) return@map item.buildUpon().setUri(uri).build()
                val query = item.requestMetadata.searchQuery
                val request = request(item.mediaId)
                    // A voice search ("" for "play Daily Office": the office for now).
                    ?: OfficeAudioResolver.requestFor(context, query)
                    ?: throw notOurs(query ?: item.mediaId)
                trackItem(OfficeAudioResolver.resolve(context, request))
            }.toMutableList()
        }
        reportFailure(mediaSession, controller, future)
        return future
    }

    /**
     * Play pressed with nothing in the player (a headset, the car, Assistant's "play", the system's
     * resume card): the office for now.
     */
    override fun onPlaybackResumption(
        mediaSession: MediaSession,
        controller: MediaSession.ControllerInfo,
        isForPlayback: Boolean,
    ): ListenableFuture<MediaItemsWithStartPosition> {
        val future = executor.submit<MediaItemsWithStartPosition> {
            val office = Office.current(com.dailyoffice2019.app.voice.AppPreferences(context).prefersFamilyPrayer)
            val track = OfficeAudioResolver.resolve(context, OfficeAudioResolver.Request.ForOffice(office))
            MediaItemsWithStartPosition(listOf(trackItem(track)), 0, 0L)
        }
        if (isForPlayback) reportFailure(mediaSession, controller, future)
        return future
    }

    /**
     * Play from outside the app (Bluetooth, the car, Assistant) on an office that finished or was
     * left paused for hours plays the office for now instead. The page's own Play, and the
     * notification's, resume what they show.
     */
    @Deprecated("Media3 still calls this; kept until the replacement is stable.")
    override fun onPlayerCommandRequest(
        session: MediaSession,
        controller: MediaSession.ControllerInfo,
        playerCommand: Int,
    ): Int {
        val player = session.player
        if (playerCommand == Player.COMMAND_PLAY_PAUSE &&
            controller.packageName != context.packageName &&
            !player.playWhenReady &&
            player.mediaItemCount > 0 &&
            nothingToResume(player)
        ) {
            playNow(session, controller)
            return SessionResult.RESULT_INFO_SKIPPED
        }
        @Suppress("DEPRECATION")
        return super.onPlayerCommandRequest(session, controller, playerCommand)
    }

    /** Loads and plays the office for now. */
    private fun playNow(session: MediaSession, controller: MediaSession.ControllerInfo) {
        val future = onPlaybackResumption(session, controller, true)
        Futures.addCallback(
            future,
            object : com.google.common.util.concurrent.FutureCallback<MediaItemsWithStartPosition> {
                override fun onSuccess(result: MediaItemsWithStartPosition) {
                    val player = session.player
                    player.setMediaItems(result.mediaItems, result.startIndex, result.startPositionMs)
                    player.prepare()
                    player.play()
                }

                override fun onFailure(error: Throwable) = Unit
            },
            ContextCompat.getMainExecutor(context),
        )
    }

    /** "Play Compline" said to Android Auto's search, or typed there. */
    override fun onSearch(
        session: MediaLibrarySession,
        browser: MediaSession.ControllerInfo,
        query: String,
        params: LibraryParams?,
    ): ListenableFuture<LibraryResult<Void>> {
        session.notifySearchResultChanged(browser, query, if (searchResult(query) != null) 1 else 0, params)
        return Futures.immediateFuture(LibraryResult.ofVoid())
    }

    override fun onGetSearchResult(
        session: MediaLibrarySession,
        browser: MediaSession.ControllerInfo,
        query: String,
        page: Int,
        pageSize: Int,
        params: LibraryParams?,
    ): ListenableFuture<LibraryResult<ImmutableList<MediaItem>>> {
        val found = searchResult(query)
        val items = if (found != null && page == 0) ImmutableList.of(found) else ImmutableList.of()
        return Futures.immediateFuture(LibraryResult.ofItemList(items, params))
    }

    private fun <T> reportFailure(
        mediaSession: MediaSession,
        controller: MediaSession.ControllerInfo,
        future: ListenableFuture<T>,
    ) {
        Futures.addCallback(
            future,
            object : com.google.common.util.concurrent.FutureCallback<T> {
                override fun onSuccess(result: T) = Unit

                override fun onFailure(error: Throwable) {
                    // Shown in the car: why nothing plays.
                    val message = (error as? OfficeAudioResolver.Failure)?.message ?: OfficeAudioResolver.UNREACHABLE
                    mediaSession.sendError(controller, SessionError(SessionError.ERROR_IO, message))
                }
            },
            // The session is only used from the main thread.
            ContextCompat.getMainExecutor(context),
        )
    }
}
