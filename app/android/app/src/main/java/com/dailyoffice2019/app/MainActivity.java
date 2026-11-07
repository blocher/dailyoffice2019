package com.dailyoffice2019.app;

import android.os.Bundle;
import androidx.activity.EdgeToEdge;
import com.dailyoffice2019.app.audio.NativeAudioPlugin;
import com.dailyoffice2019.app.offline.OfflineSyncPlugin;
import com.dailyoffice2019.app.voice.TodayWidget;
import com.dailyoffice2019.app.voice.VoiceLaunchPlugin;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        // Local plugins must be registered before the bridge starts.
        registerPlugin(NativeAudioPlugin.class);
        registerPlugin(OfflineSyncPlugin.class);
        // Shortcuts and voice assistants learn what the listener prays (voice/).
        registerPlugin(VoiceLaunchPlugin.class);
        super.onCreate(savedInstanceState);
        // Draw behind the system bars (enforced when targeting Android 16); Capacitor's
        // SystemBars plugin passes the insets to the page as env(safe-area-inset-*).
        EdgeToEdge.enable(this);
        // The calendar widget reads the day again whenever the app opens (voice/TodayWidget.kt).
        TodayWidget.refreshAll(this);
    }
}
