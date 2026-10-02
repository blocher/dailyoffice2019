"use strict";
const $ = (id) => document.getElementById(id);
const token = document.querySelector('meta[name="audition-token"]').content;
let state,
  selected,
  page = 0,
  busy = false,
  saving = Promise.resolve();
const PAGE_SIZE = 24;
// Google's curated studio roster; extended voices also have type="prebuilt".
// https://ai.google.dev/gemini-api/docs/speech-generation#prebuilt_voices
const studioVoices = new Set(
  "Zephyr Puck Charon Kore Fenrir Leda Orus Aoede Callirrhoe Autonoe Enceladus Iapetus Umbriel Algieba Despina Erinome Algenib Rasalgethi Laomedeia Achernar Alnilam Schedar Gacrux Pulcherrima Achird Zubenelgenubi Vindemiatrix Sadachbia Sadaltager Sulafat"
    .toLowerCase().split(" "),
);
const voiceLibrary = (v) => studioVoices.has(v.id.toLowerCase()) ? "studio" : "extended";
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const label = (v) => v.display_name || v.id;
const result = (id) =>
  state.results[id] || { status: "unreviewed", rating: 0, notes: "" };
const gender = (v) =>
  ["male", "female"].includes(v.gender) ? v.gender : "neutral";
function notice(message, error = false) {
  $("notice").textContent = message;
  $("notice").classList.toggle("error", error);
}
async function api(path, data) {
  const response = await fetch(
    path,
    data === undefined
      ? {}
      : {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Audition-Token": token,
          },
          body: JSON.stringify(data),
        },
  );
  const value = await response.json();
  if (!response.ok)
    throw new Error(value.error || "Request failed. Please try again.");
  return value;
}
function filtered() {
  const query = $("search").value.toLowerCase();
  return state.voices
    .filter(
      (v) =>
        (!query ||
          [v.id, v.display_name, v.description, v.accent, v.persona]
            .join(" ")
            .toLowerCase()
            .includes(query)) &&
        (!$("voice-library").value || voiceLibrary(v) === $("voice-library").value) &&
        (!$("gender").value || gender(v) === $("gender").value) &&
        (!$("accent").value || v.accent === $("accent").value) &&
        (!$("review-filter").value ||
          result(v.id).status === $("review-filter").value),
    )
    .sort((a, b) =>
      $("sort").value === "rating"
        ? result(b.id).rating - result(a.id).rating ||
          label(a).localeCompare(label(b))
        : label(a).localeCompare(label(b)),
    );
}
function renderLibrary() {
  const voices = filtered();
  page = Math.min(page, Math.max(0, Math.ceil(voices.length / PAGE_SIZE) - 1));
  $("library-count").textContent =
    `${voices.length} matching / ${state.voices.length} American English`;
  $("library-list").innerHTML =
    voices
      .slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
      .map(
        (v) =>
          `<button class="voice-row ${selected === v.id ? "selected" : ""}" data-voice="${esc(v.id)}" aria-pressed="${selected === v.id}"><span class="avatar">${esc(label(v).slice(0, 2))}</span><span class="voice-info"><strong>${esc(label(v))}</strong><small>${voiceLibrary(v) === "studio" ? "Studio" : "Extended"} · ${esc(v.accent)} · ${esc(gender(v))}</small><small class="voice-description">${esc(v.description || v.persona || "No description available.")}</small><small>${esc(result(v.id).status)}${state.cached.includes(v.id) ? " · audio ready" : ""}</small></span><span aria-hidden="true">›</span></button>`,
      )
      .join("") || '<p class="muted">No voices match these filters.</p>';
  $("page-info").textContent =
    `${voices.length ? page * PAGE_SIZE + 1 : 0}–${Math.min((page + 1) * PAGE_SIZE, voices.length)} of ${voices.length}`;
  $("page-prev").disabled = page === 0;
  $("page-next").disabled = (page + 1) * PAGE_SIZE >= voices.length;
  $("progress").textContent =
    `${Object.values(state.results).filter((r) => r.status !== "unreviewed" || r.rating > 0).length} evaluated · ${state.cached.length} samples generated`;
}
function renderBoard() {
  const voices = state.voices
    .filter((v) =>
      $("board-filter").value === "all"
        ? result(v.id).status !== "unreviewed" || result(v.id).rating > 0
        : result(v.id).status === $("board-filter").value,
    )
    .sort(
      (a, b) =>
        result(b.id).rating - result(a.id).rating ||
        label(a).localeCompare(label(b)),
    );
  $("board-count").textContent = `${voices.length} voices`;
  const groups = $("group-gender").checked
    ? [
        ["male", "Male"],
        ["female", "Female"],
        ["neutral", "Neutral / unspecified"],
      ]
    : [["all", "All results"]];
  $("board-list").innerHTML = groups
    .map(([key, name]) => {
      const items = voices.filter((v) => key === "all" || gender(v) === key);
      return `<section class="result-group"><h3>${name} <small>${items.length}</small></h3>${items.map((v) => `<button class="result-row" data-voice="${esc(v.id)}"><strong>${esc(label(v))}</strong><span class="stars">${"★".repeat(result(v.id).rating)}${"☆".repeat(5 - result(v.id).rating)}</span><small>${esc(result(v.id).status)} · ${esc(v.accent)}</small>${result(v.id).notes ? `<small>${esc(result(v.id).notes)}</small>` : ""}</button>`).join("") || '<p class="muted empty">No voices here yet.</p>'}</section>`;
    })
    .join("");
  $("export-env").disabled = !state.voices.some(
    (v) => result(v.id).status === "shortlist",
  );
}
function renderSelection(resetEditor = false) {
  const voice = state.voices.find((v) => v.id === selected);
  if (!voice) return;
  $("voice-name").textContent = label(voice);
  $("voice-id").textContent = voice.id;
  $("voice-meta").textContent = [
    voice.accent,
    gender(voice),
    voice.pitch && `${voice.pitch} pitch`,
  ]
    .filter(Boolean)
    .join(" · ");
  $("voice-description").textContent = voice.description || voice.persona || "";
  if (resetEditor) {
    $("notes").value = result(selected).notes;
    $("rating").value = result(selected).rating;
  }
  document
    .querySelectorAll("[data-decision]")
    .forEach((b) =>
      b.setAttribute(
        "aria-pressed",
        String(b.dataset.decision === result(selected).status),
      ),
    );
  $("play").textContent = state.cached.includes(selected)
    ? "▶ Play sample"
    : "▶ Generate & play";
  $("play").disabled = busy;
  $("decision-label").textContent =
    result(selected).status === "unreviewed"
      ? "Not evaluated"
      : result(selected).status;
}
async function choose(id) {
  if (id === selected) return;
  await saveNotes();
  $("audio").pause();
  $("audio").removeAttribute("src");
  $("audio").load();
  selected = id;
  renderSelection(true);
  renderLibrary();
  notice("");
}
async function save(patch) {
  const id = selected;
  let next;
  $("save-state").textContent = "Saving…";
  const work = saving.then(() => {
    next = { ...result(id), ...patch };
    return api("/api/result", { voice: id, ...next });
  });
  saving = work.catch(() => {});
  try {
    await work;
    state.results[id] = next;
    $("save-state").textContent = "Saved on this computer";
    renderLibrary();
    renderBoard();
    if (selected === id) renderSelection();
  } catch (e) {
    $("save-state").textContent = "Not saved";
    notice(e.message, true);
    throw e;
  }
}
async function saveNotes() {
  if (selected && $("notes").value !== result(selected).notes)
    await save({ notes: $("notes").value });
}
async function play() {
  if (busy || !selected) return;
  const id = selected;
  busy = true;
  $("play").disabled = true;
  notice(
    state.cached.includes(id)
      ? "Loading saved sample…"
      : "Generating one sample with Google…",
  );
  try {
    const data = await api("/api/sample", { voice: id });
    if (!state.cached.includes(id)) state.cached.push(id);
    if (selected === id) {
      $("audio").src = data.url;
      await $("audio").play();
      notice("Playing the shared Collect for Grace sample.");
    }
  } catch (e) {
    notice(e.message, true);
  } finally {
    busy = false;
    renderSelection();
    renderLibrary();
  }
}
function download(name, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function nextVoice() {
  const voices = filtered(),
    index = voices.findIndex((v) => v.id === selected);
  if (voices.length) await choose(voices[(index + 1) % voices.length].id);
}
function renderBatch() {
  const batch = state.batch;
  const running = ["running", "stopping"].includes(batch.status);
  const missing = state.voices.length - state.cached.length;
  $("batch-start").disabled = running || !missing;
  $("batch-start").textContent = batch.failed.length
    ? "Retry failures & generate remaining"
    : state.cached.length ? "Resume remaining samples" : "Generate all missing samples";
  $("batch-stop").disabled = batch.status !== "running";
  $("batch-progress").max = Math.max(1, state.voices.length);
  $("batch-progress").value = state.cached.length;
  const current = state.voices.find((v) => v.id === batch.current);
  $("batch-status").textContent = `${state.cached.length} / ${state.voices.length} ready · ${batch.status}` +
    (current ? ` · ${batch.status === "stopping" ? "Finishing" : "Generating"} ${label(current)}` : "") +
    (batch.failed.length ? ` · ${batch.failed.length} failed; retry when ready` : "");
  $("batch-errors").hidden = !batch.failed.length;
  $("batch-failures").textContent = batch.failed.join(", ");
}
function applyBatch(data) {
  // Polling must not overwrite notes or ratings being edited locally.
  state.cached = data.cached;
  state.batch = data.batch;
  renderBatch();
  renderLibrary();
  renderSelection();
}
let batchRequest = false;
async function batchAction(path) {
  if (!state || batchRequest) return;
  batchRequest = true;
  $("batch-start").disabled = true;
  $("batch-stop").disabled = true;
  try { applyBatch(await api(path, {})); }
  catch (e) { notice(e.message, true); }
  finally { batchRequest = false; renderBatch(); }
}
$("batch-start").onclick = () => batchAction("/api/batch/start");
$("batch-stop").onclick = () => batchAction("/api/batch/stop");
async function pollBatch() {
  try {
    if (state && !batchRequest) applyBatch(await api("/api/state"));
  } catch { $("batch-status").textContent = "Connection lost. Reconnect to the local server to check progress."; }
  finally { setTimeout(pollBatch, 2000); }
}
async function init() {
  try {
    state = await api("/api/state");
    selected = state.voices[0]?.id;
    $("catalog-summary").textContent =
      `${state.voices.length} American English voices from Google's ${state.total.toLocaleString()}-voice catalog`;
    $("sample-title").textContent = state.sample_title;
    $("sample-text").textContent = state.sample;
    $("sample-source").textContent = state.sample_source;
    $("style-text").textContent = state.style;
    $("model-label").textContent = state.model;
    $("accent").innerHTML =
      '<option value="">All US accents</option>' +
      [...new Set(state.voices.map((v) => v.accent).filter(Boolean))]
        .sort()
        .map((a) => `<option>${esc(a)}</option>`)
        .join("");
    renderLibrary();
    renderBoard();
    renderSelection(true);
    renderBatch();
    if (!selected)
      notice(
        "No American English voices found. Try refreshing the catalog.",
        true,
      );
  } catch (e) {
    notice(e.message, true);
  }
}
$("library-list").onclick = $("board-list").onclick = (e) => {
  const row = e.target.closest("[data-voice]");
  if (row) choose(row.dataset.voice).catch(() => {});
};
for (const id of ["search", "voice-library", "gender", "accent", "review-filter", "sort"])
  $(id).addEventListener(id === "search" ? "input" : "change", () => {
    if (!state) return;
    page = 0;
    renderLibrary();
  });
for (const id of ["board-filter", "group-gender"])
  $(id).onchange = () => {
    if (state) renderBoard();
  };
$("page-prev").onclick = () => {
  page--;
  renderLibrary();
};
$("page-next").onclick = () => {
  page++;
  renderLibrary();
};
$("play").onclick = play;
$("next-voice").onclick = () => nextVoice().catch(() => {});
$("rating").onchange = () =>
  save({ rating: Number($("rating").value), notes: $("notes").value }).catch(
    () => {},
  );
$("notes").onchange = () => saveNotes().catch(() => {});
document.querySelectorAll("[data-decision]").forEach(
  (b) =>
    (b.onclick = async () => {
      try {
        await save({ status: b.dataset.decision, notes: $("notes").value });
        if ($("auto-next").checked) await nextVoice();
      } catch {}
    }),
);
$("export-json").onclick = async () => {
  try {
    await saveNotes();
    download(
      "daily-office-voice-results.json",
      JSON.stringify(
        {
          sample: state.sample,
          model: state.model,
          style: state.style,
          results: state.voices
            .filter((v) => state.results[v.id])
            .map((v) => ({ ...v, ...result(v.id) })),
        },
        null,
        2,
      ),
      "application/json",
    );
  } catch {}
};
$("export-env").onclick = () =>
  download(
    "gemini-reader-shortlist.env",
    "GEMINI_TTS_VOICES_READER=" +
      state.voices
        .filter((v) => result(v.id).status === "shortlist")
        .sort((a, b) => result(b.id).rating - result(a.id).rating)
        .map((v) => v.id)
        .join(",") +
      "\n",
    "text/plain",
  );
$("refresh").onclick = async () => {
  if (busy) return;
  $("refresh").disabled = true;
  notice("Refreshing the complete Google catalog…");
  try {
    await api("/api/refresh", {});
    await init();
    notice("Catalog refreshed. Ratings and samples preserved.");
  } catch (e) {
    notice(e.message, true);
  } finally {
    $("refresh").disabled = false;
  }
};
document.addEventListener("keydown", (e) => {
  if (
    !state ||
    !selected ||
    ["INPUT", "TEXTAREA", "SELECT", "BUTTON"].includes(e.target.tagName) ||
    e.ctrlKey ||
    e.metaKey ||
    e.altKey
  )
    return;
  if (e.code === "Space") {
    e.preventDefault();
    if ($("audio").src) {
      if ($("audio").paused)
        $("audio")
          .play()
          .catch(() => {});
      else $("audio").pause();
    } else play();
  } else if (e.key === "ArrowRight") nextVoice().catch(() => {});
  else if (e.key.toLowerCase() === "k")
    document.querySelector('[data-decision="shortlist"]').click();
  else if (e.key.toLowerCase() === "r")
    document.querySelector('[data-decision="reject"]').click();
});
init();
setTimeout(pollBatch, 2000);
