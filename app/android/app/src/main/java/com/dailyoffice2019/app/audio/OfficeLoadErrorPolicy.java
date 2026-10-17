package com.dailyoffice2019.app.audio;

import androidx.annotation.NonNull;
import androidx.annotation.OptIn;
import androidx.media3.common.C;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.datasource.HttpDataSource;
import androidx.media3.exoplayer.upstream.DefaultLoadErrorHandlingPolicy;

/**
 * Keeps retrying a dropped connection for as long as the listener wants to listen.
 *
 * <p>The default policy gives up after a few failures and puts the player in an error state, which
 * also takes the service out of the foreground; on a locked phone Android may then not allow it
 * back. Retrying instead (at most 5 seconds apart) keeps the office buffering, in the foreground,
 * and resuming by itself as soon as the network returns. A response the server will not change
 * (404, 403, ...) still fails at once, as do the errors the default policy never retries.
 */
@OptIn(markerClass = UnstableApi.class)
final class OfficeLoadErrorPolicy extends DefaultLoadErrorHandlingPolicy {

    @Override
    public long getRetryDelayMsFor(@NonNull LoadErrorInfo loadErrorInfo) {
        if (loadErrorInfo.exception instanceof HttpDataSource.InvalidResponseCodeException) {
            int code = ((HttpDataSource.InvalidResponseCodeException) loadErrorInfo.exception).responseCode;
            if (code >= 400 && code < 500 && code != 408 && code != 429) {
                return C.TIME_UNSET;
            }
        }
        return super.getRetryDelayMsFor(loadErrorInfo);
    }

    @Override
    public int getMinimumLoadableRetryCount(int dataType) {
        return Integer.MAX_VALUE;
    }
}
