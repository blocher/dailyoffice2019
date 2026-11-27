<template>
  <div class="chant-player">
    <p v-if="!hasNotes" class="chant-player__hint">
      The notes for playing aren’t here yet. Reload the page to fetch them.
    </p>
    <div v-if="hasNotes" class="chant-player__buttons">
      <UiButton
        :icon="playing === 'psalm' ? 'pause' : 'play'"
        size="sm"
        variant="primary"
        @click="playing === 'psalm' ? stop() : playFrom(null)"
      >
        {{ playing === 'psalm' ? 'Stop' : 'Play the psalm' }}
      </UiButton>
      <UiButton
        :icon="playing === 'tone' ? 'pause' : 'volume'"
        size="sm"
        @click="playing === 'tone' ? stop() : playTone()"
      >
        {{ playing === 'tone' ? 'Stop' : 'Hear the tone' }}
      </UiButton>
    </div>
    <div v-if="hasNotes" class="chant-player__settings">
      <UiSegmented
        v-if="recording"
        :model-value="voice"
        :options="voices"
        size="sm"
        aria-label="Voice"
        @update:model-value="setVoice"
      />
      <UiSegmented
        v-if="!useChoir"
        :model-value="tempo"
        :options="tempos"
        size="sm"
        aria-label="Speed"
        @update:model-value="setTempo"
      />
      <UiSegmented
        v-if="!useChoir"
        :model-value="pitch"
        :options="pitches"
        size="sm"
        aria-label="Pitch"
        @update:model-value="setPitch"
      />
    </div>
    <p v-if="hasNotes" class="chant-player__hint">
      Tap a verse number to start there.
    </p>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import {
  PITCHES,
  TEMPOS,
  buildTimeline,
  createChantPlayer,
  createRecordingPlayer,
  pulseFor,
  recordingUrl,
  transposeFor,
  verseStart,
} from '@/helpers/chantPlayer';
import { DynamicStorage } from '@/helpers/storage';
import { toast } from '@/ui/feedback';

const props = defineProps({
  // [{ number, chant: { first_half, second_half } }]
  verses: { type: Array, required: true },
  // { label, tenor, demo: { first_half, second_half } }
  tone: { type: Object, required: true },
  // { url, pulse, voice }: the psalm sung by a choir, or null.
  recording: { type: Object, default: null },
});
const emit = defineEmits(['position', 'tone-position']);

// A psalm stored on the device before the server sent notes has marks but
// no pitches: say so rather than fail to play.
const hasNotes = computed(() =>
  props.verses.some((v) =>
    v.chant?.first_half?.some((segment) => segment.p?.length)
  )
);

const tempos = TEMPOS.map(({ value, label }) => ({ value, label }));
const pitches = PITCHES.map(({ value, label }) => ({ value, label }));
const tempo = ref('normal');
const pitch = ref('medium');
const playing = ref(null); // 'psalm' | 'tone' | null
const voices = [
  { value: 'choir', label: 'Choir' },
  { value: 'organ', label: 'Organ' },
];
const voice = ref('choir');
// The choir recording has its own speed and pitch; the organ follows the
// settings.
const useChoir = computed(
  () => Boolean(props.recording?.url) && voice.value === 'choir'
);

// The verse being sung, so a change of speed or pitch restarts it.
let lastVerse = null;

const callbacks = {
  onPosition: (syllable) => {
    if (syllable && playing.value === 'psalm') lastVerse = syllable.verse;
    emit('position', playing.value === 'psalm' ? syllable : null);
    emit('tone-position', playing.value === 'tone' ? syllable : null);
  },
  onEnd: () => {
    playing.value = null;
  },
};
const player = createChantPlayer(callbacks);
const choir = createRecordingPlayer(callbacks);

onMounted(async () => {
  const [storedTempo, storedPitch, storedVoice] = await Promise.all([
    DynamicStorage.getItem('chantTempo'),
    DynamicStorage.getItem('chantPitch'),
    DynamicStorage.getItem('chantVoice'),
  ]);
  if (TEMPOS.some((t) => t.value === storedTempo)) tempo.value = storedTempo;
  if (PITCHES.some((p) => p.value === storedPitch)) pitch.value = storedPitch;
  if (voices.some((v) => v.value === storedVoice)) voice.value = storedVoice;
});

onBeforeUnmount(() => {
  player.stop();
  choir.stop();
});

function options() {
  return {
    pulse: pulseFor(tempo.value),
    transpose: transposeFor(pitch.value, props.tone.tenor),
  };
}

async function start(kind, verses) {
  player.stop();
  choir.stop();
  const timeline = buildTimeline(verses, options());
  // Set before playing: the player reports the first syllable at once.
  playing.value = kind;
  if (kind === 'psalm') lastVerse = verses[0]?.number ?? null;
  const started = await player.play(timeline);
  if (!started) {
    playing.value = null;
    toast('This device can’t play the tone.');
  }
}

function chantVerses(verseNumber = null) {
  return props.verses
    .filter((v) => v.chant && (verseNumber == null || v.number >= verseNumber))
    .map((v) => ({
      number: v.number,
      halves: [v.chant.first_half, v.chant.second_half],
    }));
}

/** Play the psalm from a verse number (or the beginning). */
function playFrom(verseNumber) {
  if (useChoir.value) return playRecording(verseNumber);
  return start('psalm', chantVerses(verseNumber));
}

async function playRecording(verseNumber) {
  player.stop();
  choir.stop();
  // The recording is the whole psalm, so time it as the whole psalm and seek.
  const timeline = buildTimeline(chantVerses(), {
    pulse: props.recording.pulse,
  });
  playing.value = 'psalm';
  lastVerse = verseNumber;
  const started = await choir.play(
    recordingUrl(props.recording.url),
    timeline,
    verseStart(timeline, verseNumber)
  );
  if (started === false) {
    playing.value = null;
    toast('The choir recording couldn’t be played. Try the organ.');
  }
}

function playTone() {
  const demo = props.tone.demo;
  if (!demo) return;
  return start('tone', [
    { number: 0, halves: [demo.first_half, demo.second_half] },
  ]);
}

function stop() {
  player.stop();
  choir.stop();
}

function restartIfPlaying() {
  // Settings take effect from the start of the current verse.
  if (playing.value === 'psalm') playFrom(lastVerse);
}

async function setTempo(value) {
  tempo.value = value;
  await DynamicStorage.setItem('chantTempo', value);
  restartIfPlaying();
}

async function setVoice(value) {
  voice.value = value;
  await DynamicStorage.setItem('chantVoice', value);
  restartIfPlaying();
}

async function setPitch(value) {
  pitch.value = value;
  await DynamicStorage.setItem('chantPitch', value);
  restartIfPlaying();
}

defineExpose({ playFrom, stop });
</script>

<style scoped>
.chant-player {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.chant-player__buttons,
.chant-player__settings {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2) var(--space-3);
}

.chant-player__hint {
  margin: 0;
  font-size: var(--text-xs);
  color: var(--ink-faint);
}
</style>
