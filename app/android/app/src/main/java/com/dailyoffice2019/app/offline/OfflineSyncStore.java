package com.dailyoffice2019.app.offline;

import android.content.Context;
import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * The background downloads' files, in the app's no-backup files directory, offline-sync/:
 *
 * <pre>
 * state.json    what the page last scheduled: { plan, contentVersion, invalidations, audio }
 * index.json    { key: fetchedAt } of every planned answer stored or in the inbox
 * learned.json  what runs learned that the page hasn't taken yet:
 *               { contentVersion, invalidations, audio, lastRunAt }
 * inbox/        one file per downloaded answer, named for its key:
 *               { key, url, kind, date, profile, fetchedAt, body }
 * </pre>
 *
 * <p>Audio goes where the page keeps its own downloads (app/src/offline/audio.js): the app's files
 * directory (Capacitor's LibraryNoCloud), offline-audio/&lt;hashString(url)&gt;.mp3.
 *
 * <p>The plugin and the worker share one instance; every method holds its lock.
 */
public final class OfflineSyncStore {

    private static final Object LOCK = new Object();

    @Nullable
    private static OfflineSyncStore instance;

    private final File root;
    private final File inbox;
    private final File audioDirectory;

    private OfflineSyncStore(Context context) {
        root = new File(context.getNoBackupFilesDir(), "offline-sync");
        inbox = new File(root, "inbox");
        audioDirectory = new File(context.getFilesDir(), "offline-audio");
        //noinspection ResultOfMethodCallIgnored
        inbox.mkdirs();
    }

    public static OfflineSyncStore get(Context context) {
        synchronized (LOCK) {
            if (instance == null) {
                instance = new OfflineSyncStore(context.getApplicationContext());
            }
            return instance;
        }
    }

    public File audioDirectory() {
        return audioDirectory;
    }

    // Files

    @NonNull
    private static String readText(File file) throws IOException {
        try (InputStream in = new FileInputStream(file)) {
            byte[] bytes = new byte[(int) file.length()];
            int offset = 0;
            while (offset < bytes.length) {
                int read = in.read(bytes, offset, bytes.length - offset);
                if (read < 0) break;
                offset += read;
            }
            return new String(bytes, 0, offset, StandardCharsets.UTF_8);
        }
    }

    /** Whole or not at all: a temporary file renamed over the old one. */
    private static boolean writeText(File file, String text) {
        File temporary = new File(file.getPath() + ".tmp");
        try (OutputStream out = new FileOutputStream(temporary)) {
            out.write(text.getBytes(StandardCharsets.UTF_8));
            out.flush();
        } catch (IOException error) {
            //noinspection ResultOfMethodCallIgnored
            temporary.delete();
            return false;
        }
        return temporary.renameTo(file);
    }

    @NonNull
    private JSONObject read(String name) {
        File file = new File(root, name);
        if (!file.exists()) return new JSONObject();
        try {
            return new JSONObject(readText(file));
        } catch (IOException | JSONException error) {
            return new JSONObject();
        }
    }

    private void write(String name, JSONObject object) {
        writeText(new File(root, name), object.toString());
    }

    private File inboxFile(String key) {
        try {
            byte[] digest = MessageDigest.getInstance("SHA-256").digest(key.getBytes(StandardCharsets.UTF_8));
            StringBuilder name = new StringBuilder();
            for (byte b : digest) {
                name.append(String.format("%02x", b));
            }
            return new File(inbox, name + ".json");
        } catch (NoSuchAlgorithmException error) {
            throw new IllegalStateException(error);
        }
    }

    private List<File> inboxFiles() {
        File[] files = inbox.listFiles((dir, name) -> name.endsWith(".json"));
        List<File> list = files == null ? new ArrayList<>() : new ArrayList<>(Arrays.asList(files));
        list.sort((a, b) -> a.getName().compareTo(b.getName()));
        return list;
    }

    // State

    public boolean hasPlan() {
        synchronized (LOCK) {
            JSONObject plan = read("state.json").optJSONObject("plan");
            JSONArray tasks = plan == null ? null : plan.optJSONArray("tasks");
            return tasks != null && tasks.length() > 0;
        }
    }

    public JSONObject state() {
        synchronized (LOCK) {
            return read("state.json");
        }
    }

    public JSONObject index() {
        synchronized (LOCK) {
            return read("index.json");
        }
    }

    public JSONObject learned() {
        synchronized (LOCK) {
            return read("learned.json");
        }
    }

    /**
     * The page's plan. The index becomes what the page has stored, plus what is still waiting in
     * the inbox. With nothing planned, what's waiting is dropped.
     */
    public void saveSchedule(JSONObject state, JSONObject fetched) {
        synchronized (LOCK) {
            JSONObject old = read("index.json");
            write("state.json", state);
            JSONObject plan = state.optJSONObject("plan");
            JSONArray tasks = plan == null ? null : plan.optJSONArray("tasks");
            if (tasks == null || tasks.length() == 0) {
                for (File file : inboxFiles()) {
                    //noinspection ResultOfMethodCallIgnored
                    file.delete();
                }
                JSONObject learned = read("learned.json");
                JSONArray audio = learned.optJSONArray("audio");
                if (audio != null) {
                    for (int i = 0; i < audio.length(); i++) {
                        JSONObject track = audio.optJSONObject(i);
                        String path = track == null ? null : track.optString("path", null);
                        if (path != null) {
                            //noinspection ResultOfMethodCallIgnored
                            new File(audioDirectory.getParentFile(), path).delete();
                        }
                    }
                }
                try {
                    learned.put("audio", new JSONArray());
                    learned.put("invalidations", new JSONArray());
                } catch (JSONException ignored) {
                    // Not with these values.
                }
                write("learned.json", learned);
                write("index.json", new JSONObject());
                return;
            }
            JSONObject index = fetched;
            Iterator<String> keys = old.keys();
            while (keys.hasNext()) {
                String key = keys.next();
                double at = old.optDouble(key, 0);
                if (at <= 0 || !inboxFile(key).exists()) continue;
                if (at > index.optDouble(key, 0)) {
                    try {
                        index.put(key, at);
                    } catch (JSONException ignored) {
                        // Not with these values.
                    }
                }
            }
            write("index.json", index);
        }
    }

    public void setIndex(String key, double fetchedAt) {
        synchronized (LOCK) {
            JSONObject index = read("index.json");
            try {
                index.put(key, fetchedAt);
            } catch (JSONException ignored) {
                return;
            }
            write("index.json", index);
        }
    }

    public interface LearnedChange {
        void apply(JSONObject learned) throws JSONException;
    }

    public void updateLearned(LearnedChange change) {
        synchronized (LOCK) {
            JSONObject learned = read("learned.json");
            try {
                change.apply(learned);
            } catch (JSONException error) {
                return;
            }
            write("learned.json", learned);
        }
    }

    /** Whether an earlier run saved this office's track, and it waits for the page to take it. */
    public boolean hasLearnedTrack(String date, @Nullable String office) {
        synchronized (LOCK) {
            JSONArray tracks = read("learned.json").optJSONArray("audio");
            for (int i = 0; tracks != null && i < tracks.length(); i++) {
                JSONObject track = tracks.optJSONObject(i);
                if (track == null || !date.equals(track.optString("date"))) continue;
                String trackOffice = track.isNull("office") ? null : track.optString("office", null);
                if (office == null ? trackOffice != null : !office.equals(trackOffice)) continue;
                String path = track.optString("path", "");
                if (!path.isEmpty() && new File(audioDirectory.getParentFile(), path).exists()) return true;
            }
            return false;
        }
    }

    // The inbox

    public boolean putInbox(JSONObject entry) {
        String key = entry.optString("key", null);
        if (key == null) return false;
        synchronized (LOCK) {
            return writeText(inboxFile(key), entry.toString());
        }
    }

    public JSONObject drain(int limit) throws JSONException {
        synchronized (LOCK) {
            List<File> files = inboxFiles();
            JSONArray entries = new JSONArray();
            int count = Math.min(limit, files.size());
            for (int i = 0; i < count; i++) {
                File file = files.get(i);
                try {
                    entries.put(new JSONObject(readText(file)));
                } catch (IOException | JSONException error) {
                    //noinspection ResultOfMethodCallIgnored
                    file.delete();
                }
            }
            JSONObject learned = read("learned.json");
            JSONObject result = new JSONObject();
            result.put("entries", entries);
            result.put("remaining", files.size() - count);
            result.put("contentVersion", learned.optLong("contentVersion", 0));
            result.put("invalidations", learned.has("invalidations") ? learned.get("invalidations") : new JSONArray());
            result.put("audio", learned.has("audio") ? learned.get("audio") : new JSONArray());
            result.put("lastRunAt", learned.has("lastRunAt") ? learned.get("lastRunAt") : JSONObject.NULL);
            return result;
        }
    }

    public void ack(List<String> keys, double invalidationsThrough, Set<String> audio) {
        synchronized (LOCK) {
            for (String key : keys) {
                //noinspection ResultOfMethodCallIgnored
                inboxFile(key).delete();
            }
            JSONObject learned = read("learned.json");
            JSONArray invalidations = learned.optJSONArray("invalidations");
            JSONArray keptChanges = new JSONArray();
            if (invalidations != null) {
                for (int i = 0; i < invalidations.length(); i++) {
                    JSONObject change = invalidations.optJSONObject(i);
                    if (change != null && change.optDouble("at", 0) > invalidationsThrough) keptChanges.put(change);
                }
            }
            JSONArray tracks = learned.optJSONArray("audio");
            JSONArray keptTracks = new JSONArray();
            if (tracks != null) {
                for (int i = 0; i < tracks.length(); i++) {
                    JSONObject track = tracks.optJSONObject(i);
                    if (track != null && !audio.contains(track.optString("url"))) keptTracks.put(track);
                }
            }
            try {
                learned.put("invalidations", keptChanges);
                learned.put("audio", keptTracks);
            } catch (JSONException ignored) {
                return;
            }
            write("learned.json", learned);
        }
    }
}
