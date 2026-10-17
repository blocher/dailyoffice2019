package com.dailyoffice2019.app.audio;

import android.os.SystemClock;
import androidx.annotation.NonNull;
import androidx.annotation.OptIn;
import androidx.media3.common.C;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.datasource.HttpDataSource;
import androidx.media3.exoplayer.upstream.DefaultLoadErrorHandlingPolicy;

/**
 * Keeps retrying a dropped connection for a few minutes before giving up.
 *
 * <p>The default policy gives up after a few failures and puts the player in an error state, which
 * also takes the service out of the foreground; on a locked phone Android may then not allow it
 * back. Retrying instead (at most 5 seconds apart) keeps the office buffering, in the foreground,
 * and resuming by itself as soon as the network returns: a tunnel, a lift, a change of network.
 *
 * <p>Retrying holds wake and Wi-Fi locks, though, so it stops after {@link #GIVE_UP_AFTER_MS}
 * without a successful read (a listener asleep with the Wi-Fi down shouldn't drain the battery all
 * night). The player then reports an error, keeps its place, and lets go of the locks; the page
 * offers Retry. A response the server will not change (404, 403, ...) fails at once, as do the
 * errors the default policy never retries.
 */
@OptIn(markerClass = UnstableApi.class)
final class OfficeLoadErrorPolicy extends DefaultLoadErrorHandlingPolicy {

    static final long GIVE_UP_AFTER_MS = 5 * 60 * 1000;

    // When the current run of failures began. ExoPlayer resets a load's error count once it reads
    // data again, so a first error starts a new run. Called on the playback thread only.
    private long failingSinceMs = C.TIME_UNSET;

    @Override
    public long getRetryDelayMsFor(@NonNull LoadErrorInfo loadErrorInfo) {
        if (loadErrorInfo.exception instanceof HttpDataSource.InvalidResponseCodeException) {
            int code = ((HttpDataSource.InvalidResponseCodeException) loadErrorInfo.exception).responseCode;
            if (code >= 400 && code < 500 && code != 408 && code != 429) {
                return C.TIME_UNSET;
            }
        }
        long now = SystemClock.elapsedRealtime();
        if (loadErrorInfo.errorCount <= 1 || failingSinceMs == C.TIME_UNSET) {
            failingSinceMs = now;
        }
        if (now - failingSinceMs >= GIVE_UP_AFTER_MS) {
            failingSinceMs = C.TIME_UNSET;
            return C.TIME_UNSET;
        }
        return super.getRetryDelayMsFor(loadErrorInfo);
    }

    @Override
    public int getMinimumLoadableRetryCount(int dataType) {
        return Integer.MAX_VALUE;
    }
}
