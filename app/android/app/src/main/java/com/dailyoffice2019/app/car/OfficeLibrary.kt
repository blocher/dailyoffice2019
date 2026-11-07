package com.dailyoffice2019.app.car

import android.content.Context
import androidx.annotation.OptIn
import androidx.core.content.ContextCompat
import androidx.media3.common.MediaItem
import androidx.media3.common.MediaMetadata
import androidx.media3.common.util.UnstableApi
import androidx.media3.session.LibraryResult
import androidx.media3.session.MediaLibraryService.LibraryParams
import androidx.media3.session.MediaLibraryService.MediaLibrarySession
import androidx.media3.session.MediaSession
import androidx.media3.session.SessionError
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
    }

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
                val request = request(item.mediaId)
                    ?: OfficeAudioResolver.requestFor(context, item.requestMetadata.searchQuery)
                    ?: throw OfficeAudioResolver.Failure(OfficeAudioResolver.NO_AUDIO)
                val track = OfficeAudioResolver.resolve(context, request)
                MediaItem.Builder()
                    // The track's address, as the page names it, so the page can follow it.
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
            }.toMutableList()
        }
        Futures.addCallback(
            future,
            object : com.google.common.util.concurrent.FutureCallback<MutableList<MediaItem>> {
                override fun onSuccess(result: MutableList<MediaItem>) = Unit

                override fun onFailure(error: Throwable) {
                    // Shown in the car: why nothing plays.
                    val message = (error as? OfficeAudioResolver.Failure)?.message ?: OfficeAudioResolver.UNREACHABLE
                    mediaSession.sendError(controller, SessionError(SessionError.ERROR_IO, message))
                }
            },
            // The session is only used from the main thread.
            ContextCompat.getMainExecutor(context),
        )
        return future
    }
}
