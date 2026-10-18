package com.dailyoffice2019.app;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import android.os.SystemClock;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
import org.junit.runner.RunWith;

/** Smoke tests for the shipped app: the store package, the bundled web app, and native audio. */
@RunWith(AndroidJUnit4.class)
public class AppLaunchTest {

    @Test
    public void usesTheStorePackageName() {
        assertEquals(
            "com.dailyoffice2019.app",
            InstrumentationRegistry.getInstrumentation().getTargetContext().getPackageName()
        );
    }

    @Test
    public void loadsTheBundledWebAppWithNativeAudio() {
        try (ActivityScenario<MainActivity> scenario = ActivityScenario.launch(MainActivity.class)) {
            AtomicReference<String> url = new AtomicReference<>();
            AtomicReference<Object> audio = new AtomicReference<>();
            long deadline = SystemClock.elapsedRealtime() + 30_000;
            while (SystemClock.elapsedRealtime() < deadline) {
                scenario.onActivity(activity -> {
                    url.set(activity.getBridge().getWebView().getUrl());
                    audio.set(activity.getBridge().getPlugin("NativeAudio"));
                });
                if (url.get() != null) break;
                SystemClock.sleep(250);
            }
            assertNotNull("the web view never loaded a page", url.get());
            assertTrue("unexpected start URL " + url.get(), url.get().startsWith("https://localhost"));
            assertNotNull("NativeAudio plugin is not registered", audio.get());
        }
    }
}
