package com.dailyoffice2019.app.audio;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;

import android.net.Uri;
import androidx.annotation.OptIn;
import androidx.media3.common.C;
import androidx.media3.common.util.UnstableApi;
import androidx.media3.datasource.DataSpec;
import androidx.media3.datasource.HttpDataSource;
import androidx.media3.exoplayer.source.LoadEventInfo;
import androidx.media3.exoplayer.source.MediaLoadData;
import androidx.media3.exoplayer.upstream.LoadErrorHandlingPolicy.LoadErrorInfo;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import java.io.IOException;
import java.util.Collections;
import org.junit.Test;
import org.junit.runner.RunWith;

@RunWith(AndroidJUnit4.class)
@OptIn(markerClass = UnstableApi.class)
public class OfficeLoadErrorPolicyTest {

    private static final DataSpec TRACK = new DataSpec(Uri.parse("https://api.dailyoffice2019.com/track.mp3"));

    private static LoadErrorInfo error(IOException exception, int errorCount) {
        LoadEventInfo event = new LoadEventInfo(LoadEventInfo.getNewId(), TRACK, 0);
        return new LoadErrorInfo(event, new MediaLoadData(C.DATA_TYPE_MEDIA), exception, errorCount);
    }

    private static IOException http(int code) {
        return new HttpDataSource.InvalidResponseCodeException(
            code,
            "HTTP " + code,
            null,
            Collections.emptyMap(),
            TRACK,
            new byte[0]
        );
    }

    @Test
    public void givesUpAtOnceOnResponsesTheServerWillNotChange() {
        OfficeLoadErrorPolicy policy = new OfficeLoadErrorPolicy();
        assertEquals(C.TIME_UNSET, policy.getRetryDelayMsFor(error(http(404), 1)));
        assertEquals(C.TIME_UNSET, policy.getRetryDelayMsFor(error(http(403), 1)));
    }

    // A first failure retries immediately (a delay of 0), later ones back off.
    @Test
    public void keepsRetryingDroppedConnectionsAndBusyServers() {
        OfficeLoadErrorPolicy policy = new OfficeLoadErrorPolicy();
        assertNotEquals(C.TIME_UNSET, policy.getRetryDelayMsFor(error(new IOException("connection reset"), 1)));
        assertNotEquals(C.TIME_UNSET, policy.getRetryDelayMsFor(error(http(503), 2)));
        assertNotEquals(C.TIME_UNSET, policy.getRetryDelayMsFor(error(http(429), 3)));
        assertNotEquals(C.TIME_UNSET, policy.getRetryDelayMsFor(error(http(408), 4)));
    }

    @Test
    public void neverRunsOutOfRetriesBeforeTheTimeLimit() {
        assertEquals(Integer.MAX_VALUE, new OfficeLoadErrorPolicy().getMinimumLoadableRetryCount(C.DATA_TYPE_MEDIA));
    }
}
