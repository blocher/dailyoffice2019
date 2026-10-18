package com.dailyoffice2019.app;

import android.os.Bundle;
import androidx.activity.EdgeToEdge;
import com.dailyoffice2019.app.audio.NativeAudioPlugin;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        // Local plugins must be registered before the bridge starts.
        registerPlugin(NativeAudioPlugin.class);
        super.onCreate(savedInstanceState);
        // Draw behind the system bars (enforced when targeting Android 16); Capacitor's
        // SystemBars plugin passes the insets to the page as env(safe-area-inset-*).
        EdgeToEdge.enable(this);
    }
}
