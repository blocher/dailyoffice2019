package com.dailyoffice2019.app.audio;

import android.app.PendingIntent;
import android.content.Intent;
import android.net.Uri;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.annotation.OptIn;
import androidx.media3.common.AudioAttributes;
import androidx.media3.common.C;
import androidx.media3.common.MediaItem;
import androidx.media3.common.Player;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.common.util.Util;
import androidx.media3.datasource.DefaultDataSource;
import androidx.media3.datasource.DefaultHttpDataSource;
import androidx.media3.exoplayer.DefaultLoadControl;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory;
import androidx.media3.extractor.DefaultExtractorsFactory;
import androidx.media3.session.MediaSession;
import androidx.media3.session.MediaSessionService;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Plays office audio in a media-playback foreground service.
 *
 * <p>The WebView's own audio stops downloading once the screen locks or the app leaves the
 * foreground, so a long office ran dry partway through. Media3 runs the player here instead: the
 * service is promoted to the foreground while audio plays (with the lock-screen and notification
 * controls), holds wake and Wi-Fi locks, and keeps the network. NativeAudioPlugin connects to it
 * with a MediaController.
 */
@OptIn(markerClass = UnstableApi.class)
public class PlaybackService extends MediaSessionService {

    // While playing, buffer far ahead (an office is about 25 MB at 160 kbps), so a dropped
    // connection or a phone that restricts the network is covered by what is already downloaded.
    // OfficeLoadControl keeps it to 30 seconds until the listener presses play.
    private static final int MIN_BUFFER_MS = 10 * 60 * 1000;
    private static final int MAX_BUFFER_MS = 45 * 60 * 1000;
    private static final int BUFFER_FOR_PLAYBACK_MS = 1500;
    private static final int BUFFER_FOR_PLAYBACK_AFTER_REBUFFER_MS = 3000;
    private static final int TARGET_BUFFER_BYTES = 64 * 1024 * 1024;
    private static final int CONNECT_TIMEOUT_MS = 15_000;
    private static final int READ_TIMEOUT_MS = 20_000;

    @Nullable
    private MediaSession session;

    @Override
    public void onCreate() {
        super.onCreate();
        DefaultHttpDataSource.Factory http = new DefaultHttpDataSource.Factory()
            .setAllowCrossProtocolRedirects(true)
            .setConnectTimeoutMs(CONNECT_TIMEOUT_MS)
            .setReadTimeoutMs(READ_TIMEOUT_MS)
            // "DailyOffice2019/<version> (Linux; Android <version>) AndroidXMedia3/<version>", and
            // the platform header the page's own API requests carry, for the audio analytics.
            .setUserAgent(Util.getUserAgent(this, "DailyOffice2019"))
            .setDefaultRequestProperties(Collections.singletonMap("X-Client-Platform", "android"));
        DefaultMediaSourceFactory mediaSources = new DefaultMediaSourceFactory(
            new DefaultDataSource.Factory(this, http),
            // Accurate seeking even in an mp3 without a seek header.
            new DefaultExtractorsFactory().setConstantBitrateSeekingEnabled(true)
        ).setLoadErrorHandlingPolicy(new OfficeLoadErrorPolicy());
        DefaultLoadControl bufferPolicy = new DefaultLoadControl.Builder()
            .setBufferDurationsMs(MIN_BUFFER_MS, MAX_BUFFER_MS, BUFFER_FOR_PLAYBACK_MS, BUFFER_FOR_PLAYBACK_AFTER_REBUFFER_MS)
            .setTargetBufferBytes(TARGET_BUFFER_BYTES)
            .setPrioritizeTimeOverSizeThresholds(true)
            // Keep what has played too, so rewinding or "Jump to" an earlier section works offline.
            .setBackBuffer(MAX_BUFFER_MS, /* retainBackBufferFromKeyframe= */ false)
            .build();
        ExoPlayer player = new ExoPlayer.Builder(this)
            .setMediaSourceFactory(mediaSources)
            .setLoadControl(new OfficeLoadControl(bufferPolicy))
            .setAudioAttributes(
                new AudioAttributes.Builder().setUsage(C.USAGE_MEDIA).setContentType(C.AUDIO_CONTENT_TYPE_SPEECH).build(),
                /* handleAudioFocus= */ true
            )
            // Pause when headphones are unplugged or Bluetooth disconnects.
            .setHandleAudioBecomingNoisy(true)
            // Wake and Wi-Fi locks while playing, so a locked phone keeps downloading.
            .setWakeMode(C.WAKE_MODE_NETWORK)
            .setSeekBackIncrementMs(15_000)
            .setSeekForwardIncrementMs(15_000)
            .build();

        MediaSession.Builder builder = new MediaSession.Builder(this, player).setCallback(new Callback(getPackageName()));
        PendingIntent openApp = openAppIntent();
        if (openApp != null) {
            builder.setSessionActivity(openApp);
        }
        session = builder.build();
    }

    // Tapping the notification returns to the app (and the office being read).
    @Nullable
    private PendingIntent openAppIntent() {
        Intent launch = getPackageManager().getLaunchIntentForPackage(getPackageName());
        if (launch == null) {
            return null;
        }
        launch.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_REORDER_TO_FRONT);
        return PendingIntent.getActivity(this, 0, launch, PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
    }

    /**
     * A controller's media items arrive without their URI; restore it from the request metadata
     * NativeAudioPlugin sets. Only this app may load audio: other controllers (the lock screen,
     * Bluetooth, the system media controls) can play, pause and seek what is already loaded.
     */
    private static final class Callback implements MediaSession.Callback {

        private final String packageName;

        Callback(String packageName) {
            this.packageName = packageName;
        }

        @NonNull
        @Override
        public ListenableFuture<List<MediaItem>> onAddMediaItems(
            @NonNull MediaSession mediaSession,
            @NonNull MediaSession.ControllerInfo controller,
            @NonNull List<MediaItem> mediaItems
        ) {
            if (!packageName.equals(controller.getPackageName())) {
                return Futures.immediateFailedFuture(new UnsupportedOperationException());
            }
            List<MediaItem> resolved = new ArrayList<>();
            for (MediaItem item : mediaItems) {
                Uri uri = item.requestMetadata.mediaUri;
                resolved.add(uri != null ? item.buildUpon().setUri(uri).build() : item);
            }
            return Futures.immediateFuture(resolved);
        }
    }

    @Nullable
    @Override
    public MediaSession onGetSession(@NonNull MediaSession.ControllerInfo controllerInfo) {
        return session;
    }

    // Swiping the app away ends the office, as closing a browser tab does: the text it follows
    // is gone with it.
    @Override
    public void onTaskRemoved(@Nullable Intent rootIntent) {
        if (session != null) {
            Player player = session.getPlayer();
            player.pause();
            player.stop();
            player.clearMediaItems();
        }
        stopSelf();
    }

    @Override
    public void onDestroy() {
        if (session != null) {
            session.getPlayer().release();
            session.release();
            session = null;
        }
        super.onDestroy();
    }
}
