package com.dailyoffice2019.app.offline;

import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.ExistingWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.PeriodicWorkRequest;
import androidx.work.WorkManager;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Keeps the downloaded offices fresh while the app is in the background.
 *
 * <p>Background code can't reach the WebView's IndexedDB, so OfflineSyncWorker downloads into
 * files (an inbox, see OfflineSyncStore) and the page moves them into IndexedDB the next time it
 * opens (app/src/offline/native.js). The page calls:
 *
 * <pre>
 * schedule({ plan, contentVersion, invalidations, fetched, audio })  -> { scheduled }
 * drain({ limit })  -> { entries, remaining, contentVersion, invalidations, audio, lastRunAt }
 * ack({ keys, invalidationsThrough, audio })
 * runNow()  (for testing: one run as soon as there is a connection)
 * </pre>
 *
 * <p>WorkManager runs the worker about every 12 hours, on a connection, with the battery not low.
 * ios/App/App/OfflineSyncPlugin.swift does the same on iOS.
 */
@CapacitorPlugin(name = "OfflineSync")
public class OfflineSyncPlugin extends Plugin {

    static final String WORK_NAME = "offline-refresh";
    private static final long INTERVAL_HOURS = 12;

    @PluginMethod
    public void schedule(PluginCall call) {
        try {
            JSObject plan = call.getObject("plan", new JSObject());
            JSONObject state = new JSONObject();
            state.put("plan", plan);
            state.put("contentVersion", call.getData().optLong("contentVersion", 0));
            state.put("invalidations", call.getArray("invalidations", new JSArray()));
            state.put("audio", call.getObject("audio", new JSObject()));
            OfflineSyncStore store = OfflineSyncStore.get(getContext());
            store.saveSchedule(state, call.getObject("fetched", new JSObject()));

            WorkManager work = WorkManager.getInstance(getContext());
            JSObject result = new JSObject();
            if (!store.hasPlan()) {
                work.cancelUniqueWork(WORK_NAME);
                result.put("scheduled", false);
                call.resolve(result);
                return;
            }
            Constraints constraints = new Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .setRequiresBatteryNotLow(true)
                .build();
            PeriodicWorkRequest request = new PeriodicWorkRequest.Builder(OfflineSyncWorker.class, INTERVAL_HOURS, TimeUnit.HOURS)
                .setConstraints(constraints)
                // The page has just synced: the first background run can wait a period.
                .setInitialDelay(INTERVAL_HOURS, TimeUnit.HOURS)
                .build();
            // UPDATE keeps the timing of work already scheduled.
            work.enqueueUniquePeriodicWork(WORK_NAME, ExistingPeriodicWorkPolicy.UPDATE, request);
            result.put("scheduled", true);
            call.resolve(result);
        } catch (JSONException | RuntimeException error) {
            call.reject("Background downloads could not be scheduled", error);
        }
    }

    /**
     * One run now, for testing. WorkManager won't start periodic work before its time, even when
     * JobScheduler is told to (adb shell cmd jobscheduler run -f).
     */
    @PluginMethod
    public void runNow(PluginCall call) {
        Constraints constraints = new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
        OneTimeWorkRequest request = new OneTimeWorkRequest.Builder(OfflineSyncWorker.class).setConstraints(constraints).build();
        WorkManager.getInstance(getContext()).enqueueUniqueWork(WORK_NAME + "-now", ExistingWorkPolicy.REPLACE, request);
        call.resolve();
    }

    @PluginMethod
    public void drain(PluginCall call) {
        int limit = Math.max(1, call.getInt("limit", 20));
        try {
            JSONObject result = OfflineSyncStore.get(getContext()).drain(limit);
            call.resolve(JSObject.fromJSONObject(result));
        } catch (JSONException error) {
            call.reject("The background downloads could not be read", error);
        }
    }

    @PluginMethod
    public void ack(PluginCall call) {
        List<String> keys = new ArrayList<>();
        JSArray keyArray = call.getArray("keys", new JSArray());
        for (int i = 0; i < keyArray.length(); i++) {
            String key = keyArray.optString(i, null);
            if (key != null) keys.add(key);
        }
        Set<String> audio = new HashSet<>();
        JSONArray audioArray = call.getArray("audio", new JSArray());
        for (int i = 0; i < audioArray.length(); i++) {
            String url = audioArray.optString(i, null);
            if (url != null) audio.add(url);
        }
        double through = call.getData().optDouble("invalidationsThrough", 0);
        OfflineSyncStore.get(getContext()).ack(keys, through, audio);
        call.resolve();
    }
}
