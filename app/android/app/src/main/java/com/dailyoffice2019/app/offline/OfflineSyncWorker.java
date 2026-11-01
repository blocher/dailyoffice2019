package com.dailyoffice2019.app.offline;

import android.content.Context;
import android.util.Log;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.Date;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

/**
 * One background run, scheduled by OfflineSyncPlugin: the same rules as backgroundRefresh in
 * app/src/offline/serviceWorker.js (and OfflineSyncPlugin.swift on iOS). Ask the API what content
 * changed, then download up to 80 missing or stale answers for today onward into the inbox, and
 * audio for today and tomorrow when offline audio is on.
 */
public class OfflineSyncWorker extends Worker {

    private static final int LIMIT = 80;
    private static final int MAX_INVALIDATIONS = 50;
    private static final double REFERENCE_REFRESH_MS = 7d * 24 * 3600 * 1000;
    private static final int TIMEOUT_MS = 20000;
    private static final String SYNC_HEADER = "X-Offline-Sync";
    private static final String TAG = "OfflineSync";

    private final OfflineSyncStore store;
    private int fetched = 0;
    private boolean offline = false;

    public OfflineSyncWorker(@NonNull Context context, @NonNull WorkerParameters params) {
        super(context, params);
        store = OfflineSyncStore.get(context);
    }

    @NonNull
    @Override
    public Result doWork() {
        JSONObject state = store.state();
        JSONObject plan = state.optJSONObject("plan");
        JSONArray tasks = plan == null ? null : plan.optJSONArray("tasks");
        String apiBase = plan == null ? "" : plan.optString("apiBase", "");
        if (tasks == null || tasks.length() == 0 || !apiBase.startsWith("http")) {
            return Result.success();
        }
        String base = apiBase.endsWith("/") ? apiBase : apiBase + "/";

        JSONArray invalidations = new JSONArray();
        append(invalidations, state.optJSONArray("invalidations"));
        append(invalidations, checkContentChanges(base, state));

        String today = isoDay(0);
        String tomorrow = isoDay(1);
        JSONObject index = store.index();
        for (int i = 0; i < tasks.length(); i++) {
            if (fetched >= LIMIT || offline || isStopped()) break;
            JSONObject task = tasks.optJSONObject(i);
            if (task != null && needsDownload(task, index, invalidations, today, tomorrow)) {
                download(task);
            }
        }

        JSONObject audio = state.optJSONObject("audio");
        if (audio != null && audio.optBoolean("enabled", false)) {
            downloadAudio(audio.optJSONArray("tasks"), base, today, tomorrow);
        }
        store.updateLearned((learned) -> learned.put("lastRunAt", (double) System.currentTimeMillis()));
        Log.i(TAG, "Background run downloaded " + fetched + (offline ? " (stopped: offline)" : ""));
        // Cut short by the system, or the connection dropped: the next run carries on.
        return isStopped() || offline ? Result.retry() : Result.success();
    }

    private static void append(JSONArray to, @Nullable JSONArray from) {
        if (from == null) return;
        for (int i = 0; i < from.length(); i++) {
            JSONObject item = from.optJSONObject(i);
            if (item != null) to.put(item);
        }
    }

    private static String isoDay(int offset) {
        Calendar calendar = Calendar.getInstance();
        calendar.add(Calendar.DAY_OF_MONTH, offset);
        return new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(calendar.getTime());
    }

    // Content changes

    @Nullable
    private JSONArray checkContentChanges(String base, JSONObject state) {
        JSONObject learned = store.learned();
        long known = Math.max(state.optLong("contentVersion", 0), learned.optLong("contentVersion", 0));
        JSONObject summary;
        try {
            String text = fetchText(base + "api/v1/content_changes?since=" + known, false);
            summary = text == null ? null : new JSONObject(text);
        } catch (IOException | JSONException error) {
            summary = null;
        }
        if (summary == null || !summary.has("version")) {
            // The downloads go ahead anyway.
            return learned.optJSONArray("invalidations");
        }
        final JSONObject answer = summary;
        final JSONArray[] list = { new JSONArray() };
        store.updateLearned((current) -> {
            JSONArray changes = current.optJSONArray("invalidations");
            if (changes == null) changes = new JSONArray();
            boolean all = answer.optBoolean("all", false);
            JSONArray dates = answer.optJSONArray("dates");
            if (known > 0 && (all || (dates != null && dates.length() > 0))) {
                JSONObject change = new JSONObject();
                change.put("at", (double) System.currentTimeMillis());
                change.put("all", all);
                change.put("urgent", answer.optBoolean("urgent", false));
                change.put("dates", dates == null ? new JSONArray() : dates);
                changes.put(change);
                while (changes.length() > MAX_INVALIDATIONS) changes.remove(0);
            }
            current.put("invalidations", changes);
            current.put("contentVersion", Math.max(answer.optLong("version", 0), known));
            list[0] = changes;
        });
        return list[0];
    }

    // What to download

    /**
     * Same rule as app/src/offline/staleness.js: a change's dated ranges are refreshed at once; an
     * every-date change ("all") soon, or at once when urgent.
     */
    @Nullable
    private static String staleness(double fetchedAt, @Nullable String kind, @Nullable String date, JSONArray invalidations) {
        String result = null;
        for (int i = 0; i < invalidations.length(); i++) {
            JSONObject change = invalidations.optJSONObject(i);
            if (change == null || change.optDouble("at", 0) <= fetchedAt) continue;
            if (date != null) {
                String end = "month".equals(kind) ? monthEnd(date) : date;
                JSONArray ranges = change.optJSONArray("dates");
                for (int j = 0; ranges != null && j < ranges.length(); j++) {
                    JSONArray range = ranges.optJSONArray(j);
                    if (range == null || range.length() < 2) continue;
                    if (range.optString(0).compareTo(end) <= 0 && range.optString(1).compareTo(date) >= 0) return "hard";
                }
            }
            if (!change.optBoolean("all", false)) continue;
            if (change.optBoolean("urgent", false)) return "hard";
            result = "soft";
        }
        return result;
    }

    private static String monthEnd(String first) {
        try {
            int year = Integer.parseInt(first.substring(0, 4));
            int month = Integer.parseInt(first.substring(5, 7));
            Calendar calendar = Calendar.getInstance();
            calendar.clear();
            calendar.set(year, month - 1, 1);
            int last = calendar.getActualMaximum(Calendar.DAY_OF_MONTH);
            return String.format(Locale.US, "%04d-%02d-%02d", year, month, last);
        } catch (RuntimeException error) {
            return first;
        }
    }

    @Nullable
    private static String optString(JSONObject object, String name) {
        return object.isNull(name) ? null : object.optString(name, null);
    }

    private static boolean needsDownload(JSONObject task, JSONObject index, JSONArray invalidations, String today, String tomorrow) {
        String key = optString(task, "key");
        if (key == null || optString(task, "url") == null) return false;
        String kind = optString(task, "kind");
        String date = optString(task, "date");
        if (date != null) {
            if ("month".equals(kind)) {
                if (date.substring(0, 7).compareTo(today.substring(0, 7)) < 0) return false;
            } else if (date.compareTo(today) < 0) {
                return false;
            }
        }
        if (!index.has(key)) return true;
        double fetchedAt = index.optDouble(key, 0);
        String stale = staleness(fetchedAt, kind, date, invalidations);
        if (stale == null) return false;
        if ("hard".equals(stale)) return true;
        if (date == null) return System.currentTimeMillis() - fetchedAt > REFERENCE_REFRESH_MS;
        if ("month".equals(kind)) return date.substring(0, 7).equals(today.substring(0, 7));
        return date.compareTo(tomorrow) <= 0;
    }

    // Downloads

    private static HttpURLConnection open(String address, boolean sync) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL(address).openConnection();
        connection.setConnectTimeout(TIMEOUT_MS);
        connection.setReadTimeout(TIMEOUT_MS);
        connection.setUseCaches(false);
        // Not a view: the API doesn't count these (analytics/middleware.py).
        if (sync) connection.setRequestProperty(SYNC_HEADER, "1");
        return connection;
    }

    /** The body of a 200 answer; null for any other answer. Throws when the API can't be reached. */
    @Nullable
    private static String fetchText(String address, boolean sync) throws IOException {
        HttpURLConnection connection = open(address, sync);
        try {
            if (connection.getResponseCode() != 200) return null;
            try (InputStream in = connection.getInputStream()) {
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                byte[] buffer = new byte[16384];
                int read;
                while ((read = in.read(buffer)) != -1) out.write(buffer, 0, read);
                return out.toString(StandardCharsets.UTF_8.name());
            }
        } finally {
            connection.disconnect();
        }
    }

    /** A finished track: "preparing" answers aren't kept (keepable in app/src/offline/cacheAdapter.js). */
    private static boolean hasTrack(Object body) {
        JSONObject audio = body instanceof JSONObject ? ((JSONObject) body).optJSONObject("audio") : null;
        if (audio == null || "preparing".equals(audio.optString("status"))) return false;
        JSONArray single = audio.optJSONArray("single_track");
        return single != null && single.length() > 0;
    }

    /**
     * Download one answer into the inbox. Returns its parsed body (a JSONObject or JSONArray). Audio
     * answers are only kept once their track is ready.
     */
    @Nullable
    private Object download(JSONObject task) {
        String address = optString(task, "url");
        String key = optString(task, "key");
        if (address == null || key == null) return null;
        try {
            String text = fetchText(address, true);
            if (text == null) return null;
            Object body = new JSONTokener(text).nextValue();
            if (!(body instanceof JSONObject) && !(body instanceof JSONArray)) return null;
            if ("audio".equals(optString(task, "kind")) && !hasTrack(body)) return null;
            double fetchedAt = System.currentTimeMillis();
            JSONObject entry = new JSONObject();
            entry.put("key", key);
            entry.put("url", address);
            entry.put("kind", task.opt("kind"));
            entry.put("date", task.opt("date"));
            entry.put("profile", task.opt("profile"));
            entry.put("fetchedAt", fetchedAt);
            entry.put("body", text);
            if (!store.putInbox(entry)) return null;
            store.setIndex(key, fetchedAt);
            fetched += 1;
            return body;
        } catch (JSONException error) {
            // Not an answer to keep.
            return null;
        } catch (IOException error) {
            // Offline again: the next run tries again.
            Log.w(TAG, "Download failed: " + error);
            offline = true;
            return null;
        }
    }

    /** FNV-1a, base 36: the same as hashString in app/src/offline/keys.js. */
    static String hashString(String value) {
        int hash = 0x811c9dc5;
        for (int i = 0; i < value.length(); i++) {
            hash ^= value.charAt(i);
            hash *= 0x01000193;
        }
        return Long.toString(hash & 0xffffffffL, 36);
    }

    /** The API's track address, as resolveAudioUrl in app/src/helpers/officeAudio.js makes it. */
    private static String resolveTrack(String raw, String base) {
        String path;
        try {
            path = new URI(raw).getRawPath();
        } catch (Exception error) {
            path = null;
        }
        if (path == null) path = raw;
        String trimmedBase = base.endsWith("/") ? base.substring(0, base.length() - 1) : base;
        String trimmedPath = path.startsWith("/") ? path.substring(1) : path;
        return trimmedBase + "/" + trimmedPath;
    }

    private void downloadAudio(@Nullable JSONArray tasks, String base, String today, String tomorrow) {
        if (tasks == null) return;
        File directory = store.audioDirectory();
        //noinspection ResultOfMethodCallIgnored
        directory.mkdirs();
        for (int i = 0; i < tasks.length(); i++) {
            if (offline || isStopped() || fetched >= LIMIT) return;
            JSONObject task = tasks.optJSONObject(i);
            if (task == null || optString(task, "track") != null) continue;
            String date = optString(task, "date");
            if (date == null || date.compareTo(today) < 0 || date.compareTo(tomorrow) > 0) continue;
            final String office = optString(task, "office");
            // Saved by an earlier run; the page hasn't taken it yet.
            if (store.hasLearnedTrack(date, office)) continue;
            Object body = download(task);
            JSONObject audio = body instanceof JSONObject ? ((JSONObject) body).optJSONObject("audio") : null;
            if (audio == null || "preparing".equals(audio.optString("status"))) continue;
            JSONArray single = audio.optJSONArray("single_track");
            String raw = single == null || single.length() == 0 ? null : single.optString(0, null);
            if (raw == null) continue;
            String track = resolveTrack(raw, base);
            String name = hashString(track) + ".mp3";
            File file = new File(directory, name);
            if (!file.exists() && !saveTrack(track, file)) continue;
            store.updateLearned((learned) -> {
                JSONArray list = learned.optJSONArray("audio");
                JSONArray kept = new JSONArray();
                for (int j = 0; list != null && j < list.length(); j++) {
                    JSONObject item = list.optJSONObject(j);
                    if (item != null && !track.equals(item.optString("url"))) kept.put(item);
                }
                JSONObject item = new JSONObject();
                item.put("url", track);
                // Only the path, as on iOS: the page finds the file from it (app/src/offline/audio.js).
                item.put("path", "offline-audio/" + name);
                item.put("bytes", file.length());
                item.put("date", date);
                item.put("office", office == null ? JSONObject.NULL : office);
                item.put("savedAt", (double) System.currentTimeMillis());
                kept.put(item);
                learned.put("audio", kept);
            });
        }
    }

    private boolean saveTrack(String address, File file) {
        File partial = new File(file.getPath() + ".part");
        try {
            HttpURLConnection connection = open(address, true);
            try {
                if (connection.getResponseCode() != 200) return false;
                long expected = connection.getContentLengthLong();
                long written = 0;
                try (InputStream in = connection.getInputStream(); OutputStream out = new FileOutputStream(partial)) {
                    byte[] buffer = new byte[65536];
                    int read;
                    while ((read = in.read(buffer)) != -1) {
                        if (isStopped()) return false;
                        out.write(buffer, 0, read);
                        written += read;
                    }
                }
                if (written == 0 || (expected > 0 && written < expected)) return false;
                return partial.renameTo(file);
            } finally {
                connection.disconnect();
            }
        } catch (IOException error) {
            offline = true;
            return false;
        } finally {
            //noinspection ResultOfMethodCallIgnored
            partial.delete();
        }
    }
}
