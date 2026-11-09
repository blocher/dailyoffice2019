/*
  Chant player
  ============
  Plays a psalm pointed for a plainsong tone on a soft organ-like voice, with
  Web Audio, so it needs no recordings and works offline.

  The server sends each sung syllable with its pitches ("p", MIDI, do at
  middle C) and their lengths in pulses ("d"); see psalter/chant/pointing.py.
  buildTimeline() turns verses into timed notes and syllables, following the
  Manual of Plainsong, with the lengths the server sets (rhythm() in
  psalter/chant/pointing.py): quicker on the reciting note, broader in the
  cadence, and a short breath after a comma ("w"); a rest of two pulses at
  the asterisk; and one pulse between verses. createChantPlayer() sounds a
  timeline and reports which syllable is being sung.
*/

export const TEMPOS = [
  { value: 'slow', label: 'Slow', pulse: 0.44 },
  { value: 'normal', label: 'Normal', pulse: 0.38 },
  { value: 'brisk', label: 'Brisk', pulse: 0.3 },
];

// Where the reciting note sits (MIDI): F3, A3, D4.
export const PITCHES = [
  { value: 'low', label: 'Low', tenor: 53 },
  { value: 'medium', label: 'Medium', tenor: 57 },
  { value: 'high', label: 'High', tenor: 62 },
];

const REST_AT_ASTERISK = 2;
const REST_BETWEEN_VERSES = 1;

export function pulseFor(tempo) {
  return (TEMPOS.find((t) => t.value === tempo) || TEMPOS[1]).pulse;
}

export function transposeFor(pitch, toneTenor) {
  const target = (PITCHES.find((p) => p.value === pitch) || PITCHES[1]).tenor;
  return target - (toneTenor ?? 60);
}

/**
  verses: [{ number, halves: [segments, segments] }], where segments are the
  chant segments from the API (only those with "p" are sung).
  Returns { notes: [{ midi, start, end }], syllables: [{ verse, half,
  index, start, end }], duration } with times in seconds.
*/
export function buildTimeline(verses, { pulse = 0.38, transpose = 0 } = {}) {
  const notes = [];
  const syllables = [];
  let time = 0;
  verses.forEach((verse, verseIndex) => {
    verse.halves.forEach((segments, half) => {
      (segments || []).forEach((segment, index) => {
        if (!segment.p || !segment.p.length) return;
        const start = time;
        segment.p.forEach((midi, i) => {
          const length = ((segment.d && segment.d[i]) || 1) * pulse;
          notes.push({
            midi: midi + transpose,
            start: time,
            end: time + length,
          });
          time += length;
        });
        syllables.push({ verse: verse.number, half, index, start, end: time });
        // A breath after a comma ("w", in pulses).
        if (segment.w) time += segment.w * pulse;
      });
      if (half === 0) time += REST_AT_ASTERISK * pulse;
    });
    if (verseIndex < verses.length - 1) time += REST_BETWEEN_VERSES * pulse;
  });
  return { notes, syllables, duration: time };
}

/** The syllable sounding at a time, or null. */
export function syllableAt(timeline, time) {
  const { syllables } = timeline;
  let low = 0;
  let high = syllables.length - 1;
  while (low <= high) {
    const mid = (low + high) >> 1;
    const s = syllables[mid];
    if (time < s.start) high = mid - 1;
    else if (time >= s.end) low = mid + 1;
    else return s;
  }
  return null;
}

function frequency(midi) {
  return 440 * 2 ** ((midi - 69) / 12);
}

const LOOKAHEAD = 1.5; // seconds of notes scheduled ahead
const TICK_MS = 60;

/**
  A player for one timeline at a time. onPosition(syllable | null) is called
  as the sung syllable changes; onEnd() when it finishes or is stopped.
*/
export function createChantPlayer({ onPosition, onEnd } = {}) {
  let context = null;
  let output = null;
  let wave = null;
  let timer = null;
  let current = null;

  function ensureContext() {
    if (context) return context;
    const AudioContextClass =
      typeof window !== 'undefined' &&
      (window.AudioContext || window.webkitAudioContext);
    if (!AudioContextClass) return null;
    context = new AudioContextClass();
    // A soft flute-and-principal organ: a few quiet harmonics.
    const real = new Float32Array([0, 1, 0.45, 0.2, 0.12, 0.05]);
    wave = context.createPeriodicWave(real, new Float32Array(real.length));
    const filter = context.createBiquadFilter();
    filter.type = 'lowpass';
    filter.frequency.value = 2400;
    output = context.createGain();
    output.gain.value = 0.22;
    output.connect(filter);
    filter.connect(context.destination);
    return context;
  }

  function sound(note, at) {
    const oscillator = context.createOscillator();
    oscillator.setPeriodicWave(wave);
    oscillator.frequency.value = frequency(note.midi);
    const envelope = context.createGain();
    const start = at + note.start;
    // A slight gap before the next note keeps repeated pitches distinct.
    const end = at + note.end - 0.02;
    envelope.gain.setValueAtTime(0, start);
    envelope.gain.linearRampToValueAtTime(1, start + 0.03);
    envelope.gain.setValueAtTime(1, Math.max(start + 0.03, end - 0.05));
    envelope.gain.linearRampToValueAtTime(0, end);
    oscillator.connect(envelope);
    envelope.connect(output);
    oscillator.start(start);
    oscillator.stop(end + 0.01);
    current.voices.push(oscillator);
  }

  function tick() {
    if (!current) return;
    const now = context.currentTime - current.at;
    while (
      current.next < current.timeline.notes.length &&
      current.timeline.notes[current.next].start < now + LOOKAHEAD
    ) {
      sound(current.timeline.notes[current.next], current.at);
      current.next += 1;
    }
    const syllable = syllableAt(current.timeline, now);
    if (syllable !== current.syllable) {
      current.syllable = syllable;
      onPosition?.(syllable);
    }
    if (now >= current.timeline.duration) stop();
  }

  function stop() {
    if (timer) window.clearInterval(timer);
    timer = null;
    if (current) {
      const now = context.currentTime;
      current.voices.forEach((voice) => {
        try {
          voice.stop(now);
        } catch {
          // Already stopped.
        }
      });
      current = null;
      onPosition?.(null);
      onEnd?.();
    }
  }

  async function play(timeline) {
    stop();
    if (!ensureContext() || !timeline.notes.length) {
      onEnd?.();
      return false;
    }
    // Browsers start audio suspended until a tap; play() is called from one.
    if (context.state === 'suspended') await context.resume();
    current = {
      timeline,
      at: context.currentTime + 0.1,
      next: 0,
      voices: [],
      syllable: null,
    };
    tick();
    timer = window.setInterval(tick, TICK_MS);
    return true;
  }

  return {
    play,
    stop,
    get playing() {
      return Boolean(current);
    },
  };
}

/**
  The full address of a recording the API gives as a path ("/uploads/…").
*/
export function recordingUrl(path, base = import.meta.env.VITE_API_URL) {
  if (!path) return null;
  try {
    return new window.URL(path, base).href;
  } catch {
    return path;
  }
}

/** Where a recording of the whole psalm reaches a verse, in seconds. */
export function verseStart(timeline, verseNumber) {
  if (verseNumber == null) return 0;
  const syllable = timeline.syllables.find((s) => s.verse >= verseNumber);
  return syllable ? syllable.start : 0;
}

/**
  Plays a sung recording of a psalm (manage.py record_chant) and reports the
  syllable being sung from the recording's own position, using the timeline
  of the pulse it was sung at. Same callbacks as createChantPlayer.
  play() resolves true when it starts, false when the file can't be played,
  and null when stopped while it was loading.
*/
export function createRecordingPlayer({ onPosition, onEnd } = {}) {
  let audio = null;
  let timer = null;
  let current = null;

  function tick() {
    if (!current || !audio) return;
    const syllable = syllableAt(current.timeline, audio.currentTime);
    if (syllable !== current.syllable) {
      current.syllable = syllable;
      onPosition?.(syllable);
    }
  }

  function finish() {
    if (timer) window.clearInterval(timer);
    timer = null;
    const wasPlaying = Boolean(current);
    current = null;
    if (wasPlaying) {
      onPosition?.(null);
      onEnd?.();
    }
  }

  function stop() {
    if (audio) audio.pause();
    finish();
  }

  // The recording is fetched whole and played from memory: it is small (about
  // a megabyte a psalm), and seeking to a verse then works whatever the
  // server, including ones that ignore range requests.
  async function load(url) {
    if (audio && audio.dataset.src === url) return;
    const response = await window.fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const blob = await response.blob();
    if (audio) window.URL.revokeObjectURL(audio.src);
    audio = new Audio(window.URL.createObjectURL(blob));
    audio.dataset.src = url;
    audio.preload = 'auto';
    audio.addEventListener('ended', finish);
  }

  async function play(url, timeline, from = 0) {
    stop();
    if (typeof Audio === 'undefined') return false;
    current = { timeline, syllable: null };
    try {
      await load(url);
      if (!current) return null;
      // Seeking before the file's length is known is ignored on some browsers.
      if (from && audio.readyState < 1) {
        await new Promise((resolve, reject) => {
          audio.addEventListener('loadedmetadata', resolve, { once: true });
          audio.addEventListener('error', reject, { once: true });
          audio.load();
        });
      }
      audio.currentTime = from;
      await audio.play();
    } catch {
      finish();
      return false;
    }
    // Stopped while the file was loading.
    if (!current) {
      audio.pause();
      return null;
    }
    tick();
    timer = window.setInterval(tick, TICK_MS);
    return true;
  }

  return {
    play,
    stop,
    get playing() {
      return Boolean(current);
    },
  };
}
