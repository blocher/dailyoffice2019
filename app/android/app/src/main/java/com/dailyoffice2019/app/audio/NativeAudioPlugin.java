package com.dailyoffice2019.app.audio;

import android.content.ComponentName;
import android.net.Uri;
import android.os.Handler;
import android.os.Looper;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.core.content.ContextCompat;
import androidx.media3.common.C;
import androidx.media3.common.MediaItem;
import androidx.media3.common.MediaMetadata;
import androidx.media3.common.PlaybackException;
import androidx.media3.common.Player;
import androidx.media3.session.MediaController;
import androidx.media3.session.SessionToken;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.google.common.util.concurrent.ListenableFuture;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;

/**
 * The page's handle on PlaybackService. app/src/helpers/nativeAudio.js wraps it in an object that
 * behaves like an audio element, so AudioPlayer.vue drives either one the same way.
 *
 * <p>Every method resolves with the player's status, and the plugin sends a "status" event when
 * the state changes and, while audio plays in the foreground, every quarter second:
 *
 * <pre>
 * { url, state: idle|buffering|ready|ended, playWhenReady, isPlaying,
 *   position, duration, buffered (seconds), rate, error, event }
 * </pre>
 */
@CapacitorPlugin(name = "NativeAudio")
public class NativeAudioPlugin extends Plugin {

    private static final long TICK_MS = 250;

    private final Handler main = new Handler(Looper.getMainLooper());
    private final Runnable tick = () -> {
        emit("tick");
        scheduleTick();
    };

    @Nullable
    private ListenableFuture<MediaController> controllerFuture;

    @Nullable
    private MediaController controller;

    private boolean inForeground = true;

    // The track last loaded, so the page can be told when the service goes away under it.
    @Nullable
    private String lastUrl;

    private final Player.Listener playerListener = new Player.Listener() {
        @Override
        public void onPositionDiscontinuity(
            @NonNull Player.PositionInfo oldPosition,
            @NonNull Player.PositionInfo newPosition,
            int reason
        ) {
            if (reason == Player.DISCONTINUITY_REASON_SEEK) {
                emit("seeked");
            }
        }

        @Override
        public void onEvents(@NonNull Player player, @NonNull Player.Events events) {
            if (
                events.containsAny(
                    Player.EVENT_PLAYBACK_STATE_CHANGED,
                    Player.EVENT_PLAY_WHEN_READY_CHANGED,
                    Player.EVENT_IS_PLAYING_CHANGED,
                    Player.EVENT_IS_LOADING_CHANGED,
                    Player.EVENT_PLAYER_ERROR,
                    Player.EVENT_TIMELINE_CHANGED,
                    Player.EVENT_MEDIA_ITEM_TRANSITION,
                    Player.EVENT_PLAYBACK_PARAMETERS_CHANGED
                )
            ) {
                emit("change");
            }
            scheduleTick();
        }
    };

    private interface ControllerAction {
        void run(MediaController controller);
    }

    @PluginMethod
    public void setSource(PluginCall call) {
        String url = call.getString("url");
        if (url == null || url.isEmpty()) {
            call.reject("A url is required");
            return;
        }
        String title = call.getString("title", "");
        String artist = call.getString("artist", "");
        String artwork = call.getString("artwork", "");
        double rate = call.getDouble("rate", 1.0);
        lastUrl = url;
        // Read off the main thread; used only if the track is (re)loaded.
        byte[] artworkData = readWebAsset(artwork);
        withController(call, (c) -> {
            MediaItem current = c.getCurrentMediaItem();
            boolean same = current != null && url.equals(current.mediaId);
            // This track is already loaded and healthy: the page was reopened while the office
            // played on, or the page is retrying while the player reconnects by itself
            // (OfficeLoadErrorPolicy). Reloading would drop the connection and the buffer.
            if (same && c.getPlaybackState() != Player.STATE_IDLE && c.getPlayerError() == null) {
                return;
            }
            if (!same) {
                c.setPlayWhenReady(false);
            }
            MediaMetadata.Builder metadata = new MediaMetadata.Builder()
                .setTitle(title)
                .setDisplayTitle(title)
                .setArtist(artist)
                .setSubtitle(artist)
                .setMediaType(MediaMetadata.MEDIA_TYPE_PODCAST_EPISODE);
            if (artworkData != null) {
                metadata.setArtworkData(artworkData, MediaMetadata.PICTURE_TYPE_FRONT_COVER);
            }
            MediaItem item = new MediaItem.Builder()
                .setMediaId(url)
                .setUri(url)
                .setMediaMetadata(metadata.build())
                // The session rebuilds the item from this (PlaybackService.Callback).
                .setRequestMetadata(new MediaItem.RequestMetadata.Builder().setMediaUri(Uri.parse(url)).build())
                .build();
            // A retry of the same track reconnects from where it was.
            long startMs = same ? Math.max(0, c.getCurrentPosition()) : 0;
            c.setMediaItem(item, startMs);
            if (rate > 0) {
                c.setPlaybackSpeed((float) rate);
            }
            c.prepare();
        });
    }

    @PluginMethod
    public void play(PluginCall call) {
        withController(call, (c) -> {
            if (c.getMediaItemCount() == 0) {
                throw new IllegalStateException("No audio source");
            }
            if (c.getPlaybackState() == Player.STATE_IDLE) {
                // After an error, try the connection again.
                c.prepare();
            }
            c.play();
        });
    }

    @PluginMethod
    public void pause(PluginCall call) {
        if (controller == null) {
            call.resolve(status("command"));
            return;
        }
        withController(call, Player::pause);
    }

    @PluginMethod
    public void seekTo(PluginCall call) {
        Double position = call.getDouble("position");
        if (position == null || position.isNaN() || position < 0) {
            call.reject("A position is required");
            return;
        }
        withController(call, (c) -> c.seekTo(Math.round(position * 1000)));
    }

    @PluginMethod
    public void setRate(PluginCall call) {
        Double rate = call.getDouble("rate");
        if (rate == null || rate.isNaN() || rate <= 0) {
            call.reject("A rate is required");
            return;
        }
        withController(call, (c) -> c.setPlaybackSpeed(rate.floatValue()));
    }

    @PluginMethod
    public void stop(PluginCall call) {
        if (controller == null) {
            // Nothing is playing; don't start the service just to stop it.
            lastUrl = null;
            call.resolve(status("command"));
            return;
        }
        lastUrl = null;
        withController(call, (c) -> {
            c.pause();
            c.stop();
            c.clearMediaItems();
        });
    }

    @PluginMethod
    public void getStatus(PluginCall call) {
        main.post(() -> call.resolve(status("command")));
    }

    @Override
    protected void handleOnResume() {
        super.handleOnResume();
        inForeground = true;
        main.post(() -> {
            emit("resume");
            scheduleTick();
        });
    }

    @Override
    protected void handleOnPause() {
        super.handleOnPause();
        // State changes still arrive; only the quarter-second clock stops while hidden.
        inForeground = false;
        main.removeCallbacks(tick);
    }

    @Override
    protected void handleOnDestroy() {
        main.removeCallbacks(tick);
        // Playback carries on in the service; only this page's connection ends. Clear the fields
        // first, so the disconnect this causes isn't reported to the page as a lost player.
        MediaController c = controller;
        ListenableFuture<MediaController> future = controllerFuture;
        controller = null;
        controllerFuture = null;
        if (c != null) {
            c.removeListener(playerListener);
        }
        if (future != null) {
            MediaController.releaseFuture(future);
        }
        super.handleOnDestroy();
    }

    // Run `action` on the main thread once connected to the service, then resolve with the status.
    private void withController(PluginCall call, ControllerAction action) {
        main.post(() -> {
            if (controller != null && controller.isConnected()) {
                perform(call, action);
                return;
            }
            ListenableFuture<MediaController> future = connect();
            future.addListener(
                () -> {
                    if (controller == null || !controller.isConnected()) {
                        try {
                            controller = future.get();
                            controller.addListener(playerListener);
                        } catch (Exception e) {
                            if (controllerFuture == future) {
                                controllerFuture = null;
                            }
                            controller = null;
                            call.reject("The audio player is unavailable", e);
                            return;
                        }
                    }
                    perform(call, action);
                },
                ContextCompat.getMainExecutor(getContext())
            );
        });
    }

    private void perform(PluginCall call, ControllerAction action) {
        try {
            action.run(controller);
            scheduleTick();
            call.resolve(status("command"));
        } catch (Exception e) {
            call.reject(e.getMessage() != null ? e.getMessage() : "Audio command failed", e);
        }
    }

    private ListenableFuture<MediaController> connect() {
        if (controllerFuture != null && !controllerFuture.isCancelled()) {
            boolean failed = false;
            if (controllerFuture.isDone()) {
                try {
                    failed = !controllerFuture.get().isConnected();
                } catch (Exception e) {
                    failed = true;
                }
            }
            if (!failed) {
                return controllerFuture;
            }
            MediaController.releaseFuture(controllerFuture);
        }
        controller = null;
        SessionToken token = new SessionToken(getContext(), new ComponentName(getContext(), PlaybackService.class));
        controllerFuture = new MediaController.Builder(getContext(), token)
            .setListener(
                new MediaController.Listener() {
                    @Override
                    public void onDisconnected(@NonNull MediaController disconnected) {
                        // The service ended (stopped by the system); reconnect on the next call. Tell
                        // the page, which would otherwise go on showing the office as playing; it
                        // treats this like a dropped connection and reloads where it was.
                        if (controller == disconnected) {
                            controller = null;
                            controllerFuture = null;
                            main.removeCallbacks(tick);
                            notifyListeners("status", disconnectedStatus());
                        }
                    }
                }
            )
            .buildAsync();
        return controllerFuture;
    }

    private void scheduleTick() {
        main.removeCallbacks(tick);
        MediaController c = controller;
        if (!inForeground || c == null || !c.isConnected() || c.getMediaItemCount() == 0) {
            return;
        }
        if (c.getPlayWhenReady() || c.isLoading()) {
            main.postDelayed(tick, TICK_MS);
        }
    }

    private void emit(String event) {
        if (controller == null) {
            return;
        }
        notifyListeners("status", status(event));
    }

    private JSObject status(String event) {
        JSObject status = new JSObject();
        status.put("event", event);
        MediaController c = controller;
        if (c == null || !c.isConnected()) {
            status.put("state", "idle");
            return status;
        }
        MediaItem item = c.getCurrentMediaItem();
        if (item != null) {
            status.put("url", item.mediaId);
        }
        status.put("state", stateName(c.getPlaybackState()));
        status.put("playWhenReady", c.getPlayWhenReady());
        status.put("isPlaying", c.isPlaying());
        status.put("position", Math.max(0, c.getCurrentPosition()) / 1000.0);
        long duration = c.getDuration();
        status.put("duration", duration == C.TIME_UNSET ? 0 : duration / 1000.0);
        status.put("buffered", Math.max(0, c.getBufferedPosition()) / 1000.0);
        status.put("rate", c.getPlaybackParameters().speed);
        PlaybackException error = c.getPlayerError();
        if (error != null) {
            status.put("error", error.getErrorCodeName());
        }
        return status;
    }

    private JSObject disconnectedStatus() {
        JSObject status = new JSObject();
        status.put("event", "disconnected");
        status.put("state", "idle");
        if (lastUrl != null) {
            status.put("url", lastUrl);
        }
        status.put("error", "ERROR_CODE_DISCONNECTED");
        return status;
    }

    // An image from the app's bundled web assets (app/public), for the lock screen.
    @Nullable
    private byte[] readWebAsset(String path) {
        if (path == null || path.isEmpty() || path.contains("..")) {
            return null;
        }
        try (InputStream in = getContext().getAssets().open("public/" + path.replaceFirst("^/+", ""))) {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buffer = new byte[16 * 1024];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }
            return out.toByteArray();
        } catch (IOException e) {
            return null;
        }
    }

    private static String stateName(int state) {
        switch (state) {
            case Player.STATE_BUFFERING:
                return "buffering";
            case Player.STATE_READY:
                return "ready";
            case Player.STATE_ENDED:
                return "ended";
            default:
                return "idle";
        }
    }
}
