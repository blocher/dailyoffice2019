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
        :model-value="tempo"
        :options="tempos"
        size="sm"
        aria-label="Speed"
        @update:model-value="setTempo"
      />
      <UiSegmented
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
  pulseFor,
  transposeFor,
} from '@/helpers/chantPlayer';
import { DynamicStorage } from '@/helpers/storage';
import { toast } from '@/ui/feedback';

const props = defineProps({
  // [{ number, chant: { first_half, second_half } }]
  verses: { type: Array, required: true },
  // { label, tenor, demo: { first_half, second_half } }
  tone: { type: Object, required: true },
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

// The verse being sung, so a change of speed or pitch restarts it.
let lastVerse = null;

const player = createChantPlayer({
  onPosition: (syllable) => {
    if (syllable && playing.value === 'psalm') lastVerse = syllable.verse;
    emit('position', playing.value === 'psalm' ? syllable : null);
    emit('tone-position', playing.value === 'tone' ? syllable : null);
  },
  onEnd: () => {
    playing.value = null;
  },
});

onMounted(async () => {
  const [storedTempo, storedPitch] = await Promise.all([
    DynamicStorage.getItem('chantTempo'),
    DynamicStorage.getItem('chantPitch'),
  ]);
  if (TEMPOS.some((t) => t.value === storedTempo)) tempo.value = storedTempo;
  if (PITCHES.some((p) => p.value === storedPitch)) pitch.value = storedPitch;
});

onBeforeUnmount(() => player.stop());

function options() {
  return {
    pulse: pulseFor(tempo.value),
    transpose: transposeFor(pitch.value, props.tone.tenor),
  };
}

async function start(kind, verses) {
  player.stop();
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

/** Play the psalm from a verse number (or the beginning). */
function playFrom(verseNumber) {
  const verses = props.verses
    .filter((v) => v.chant && (verseNumber == null || v.number >= verseNumber))
    .map((v) => ({
      number: v.number,
      halves: [v.chant.first_half, v.chant.second_half],
    }));
  return start('psalm', verses);
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
