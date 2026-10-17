package com.dailyoffice2019.app.audio;

import androidx.annotation.NonNull;
import androidx.annotation.OptIn;
import androidx.media3.common.Timeline;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.exoplayer.DefaultLoadControl;
import androidx.media3.exoplayer.LoadControl;
import androidx.media3.exoplayer.analytics.PlayerId;
import androidx.media3.exoplayer.source.MediaSource;
import androidx.media3.exoplayer.source.TrackGroupArray;
import androidx.media3.exoplayer.trackselection.ExoTrackSelection;
import androidx.media3.exoplayer.upstream.Allocator;

/**
 * Buffers far ahead while an office plays, but only a little while it is paused.
 *
 * <p>Once playing, a long buffer means a locked phone or a dropped connection is covered by what is
 * already downloaded. Before the listener presses play, though, every office page would otherwise
 * download the whole track (about 25 MB) on the chance it might be heard. Everything else is
 * DefaultLoadControl's.
 */
@OptIn(markerClass = UnstableApi.class)
final class OfficeLoadControl implements LoadControl {

    // Enough to start at once and to read the track's length.
    private static final long PAUSED_BUFFER_US = 30_000_000L;

    private final DefaultLoadControl delegate;

    OfficeLoadControl(DefaultLoadControl delegate) {
        this.delegate = delegate;
    }

    @Override
    public boolean shouldContinueLoading(@NonNull Parameters parameters) {
        // Ask the delegate first so its own loading state stays current.
        boolean load = delegate.shouldContinueLoading(parameters);
        if (!parameters.playWhenReady && parameters.bufferedDurationUs >= PAUSED_BUFFER_US) {
            return false;
        }
        return load;
    }

    @Override
    public boolean shouldStartPlayback(@NonNull Parameters parameters) {
        return delegate.shouldStartPlayback(parameters);
    }

    @Override
    public boolean shouldContinuePreloading(
        @NonNull PlayerId playerId,
        @NonNull Timeline timeline,
        @NonNull MediaSource.MediaPeriodId mediaPeriodId,
        long bufferedDurationUs
    ) {
        return delegate.shouldContinuePreloading(playerId, timeline, mediaPeriodId, bufferedDurationUs);
    }

    @Override
    public void onPrepared(@NonNull PlayerId playerId) {
        delegate.onPrepared(playerId);
    }

    @Override
    public void onTracksSelected(
        @NonNull Parameters parameters,
        @NonNull TrackGroupArray trackGroups,
        @NonNull ExoTrackSelection[] trackSelections
    ) {
        delegate.onTracksSelected(parameters, trackGroups, trackSelections);
    }

    @Override
    public void onStopped(@NonNull PlayerId playerId) {
        delegate.onStopped(playerId);
    }

    @Override
    public void onReleased(@NonNull PlayerId playerId) {
        delegate.onReleased(playerId);
    }

    @NonNull
    @Override
    public Allocator getAllocator(@NonNull PlayerId playerId) {
        return delegate.getAllocator(playerId);
    }

    @Override
    public long getBackBufferDurationUs(@NonNull PlayerId playerId) {
        return delegate.getBackBufferDurationUs(playerId);
    }

    @Override
    public boolean retainBackBufferFromKeyframe(@NonNull PlayerId playerId) {
        return delegate.retainBackBufferFromKeyframe(playerId);
    }
}
