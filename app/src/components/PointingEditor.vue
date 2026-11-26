<template>
  <UiSheet
    :open="open"
    size="lg"
    eyebrow="Suggest a fix"
    :title="`Psalm ${psalm}`"
    subtitle="Mark the verse as it should be sung; an editor will look at it."
    @update:open="(value) => !value && close()"
    @close="close"
  >
    <div class="pointing-editor stack">
      <div class="pointing-editor__verse cluster">
        <UiButton
          size="sm"
          variant="ghost"
          icon="chevron-left"
          :disabled="!previousVerse || loading"
          aria-label="Previous verse"
          @click="goTo(previousVerse)"
        />
        <UiSelect
          v-model="verseChoice"
          class="pointing-editor__verse-select"
          :options="verseOptions"
          aria-label="Verse"
        />
        <UiButton
          size="sm"
          variant="ghost"
          icon="chevron-right"
          :disabled="!nextVerse || loading"
          aria-label="Next verse"
          @click="goTo(nextVerse)"
        />
      </div>

      <UiAlert v-if="loadError" tone="error" :title="loadError" />

      <template v-if="data">
        <p class="pointing-editor__help">
          <template v-if="bookTone">
            Tap a syllable to change its mark, as the St. Bernard Psalter prints
            it: <span class="pointing-editor__key is-pointed">bold</span> for a
            ticked note of the tone,
            <span class="pointing-editor__key is-slur">italic</span> for a slur,
            then plain again.
          </template>
          <template v-else>
            Tap a syllable to mark it
            <span class="pointing-editor__key is-stress">stressed</span>, or tap
            again to clear it.
          </template>
        </p>

        <div
          v-for="(half, halfIndex) in halves"
          :key="halfIndex"
          class="pointing-editor__half"
          :class="{ 'pointing-editor__half--second': halfIndex === 1 }"
          role="group"
          :aria-label="halfIndex === 0 ? 'First half' : 'Second half'"
        >
          <span
            v-for="(word, wordIndex) in words(half)"
            :key="wordIndex"
            class="pointing-editor__word"
            ><button
              v-for="syllable in word"
              :key="syllable.index"
              type="button"
              class="pointing-editor__syllable"
              :class="syllableClass(halfIndex, syllable.index)"
              :aria-label="`${syllable.t}: ${markName(syllable.m)}`"
              @click="cycle(halfIndex, syllable.index)"
            >
              {{ syllable.t }}
            </button></span
          ><span v-if="halfIndex === 0" class="pointing-editor__asterisk"
            >*</span
          >
        </div>

        <section class="pointing-editor__sung surface">
          <div class="pointing-editor__sung-head cluster">
            <h3 class="section-title">How it will be sung</h3>
            <UiButton
              size="sm"
              :icon="playing ? 'pause' : 'play'"
              :disabled="!preview"
              @click="playing ? player.stop() : play()"
            >
              {{ playing ? 'Stop' : 'Play' }}
            </UiButton>
          </div>
          <p v-if="preview" class="book pointing-editor__preview">
            <ChantText :segments="preview.first_half" :active="active(0)" /> *
            <br />
            <ChantText :segments="preview.second_half" :active="active(1)" />
          </p>
          <p v-else-if="previewError" class="pointing-editor__problem">
            {{ previewError }}
          </p>
          <ul
            v-if="preview && preview.warnings.length"
            class="pointing-editor__warnings"
          >
            <li v-for="warning in preview.warnings" :key="warning">
              {{ warning }}
            </li>
          </ul>
        </section>

        <UiField label="Tone" for-id="pointing-tone">
          <UiSelect id="pointing-tone" v-model="tone" :options="toneOptions" />
        </UiField>

        <UiField label="Why" for-id="pointing-note" optional>
          <UiInput
            id="pointing-note"
            v-model="note"
            multiline
            :rows="2"
            placeholder="For example: “every” is two syllables here."
          />
        </UiField>
        <div class="pointing-editor__who">
          <UiField label="Your name" for-id="pointing-name" optional>
            <UiInput id="pointing-name" v-model="name" />
          </UiField>
          <UiField
            label="Email"
            for-id="pointing-email"
            optional
            hint="Only if you’d like a reply."
          >
            <UiInput id="pointing-email" v-model="email" type="email" />
          </UiField>
        </div>
        <UiAlert v-if="sendError" tone="error" :title="sendError" />
        <UiAlert
          v-if="sent"
          tone="success"
          title="Thank you. An editor will look at your suggestion."
        />
      </template>
    </div>

    <template #footer>
      <div class="pointing-editor__actions cluster">
        <UiButton variant="ghost" :disabled="!changed" @click="reset">
          Start over
        </UiButton>
        <UiButton
          variant="primary"
          icon="send"
          :loading="sending"
          :disabled="!changed || !data"
          @click="send"
        >
          Send suggestion
        </UiButton>
      </div>
    </template>
  </UiSheet>
</template>

<script setup>
/*
  The chant pointing of one verse, to correct and send to an editor. Each
  syllable is a button that cycles through the marks the tone uses: for a St.
  Bernard Psalter tone, plain, bold ("^", a pointed note) and italic ("~", a
  slur); for the other tones, plain and stressed ("+"). The server shows how
  the marks will be sung (api/v1/pointing/preview), which can be played, and
  takes the suggestion (api/v1/pointing/proposals) for review in the admin.
*/
import axios from 'axios';
import { computed, onBeforeUnmount, ref, watch } from 'vue';

import ChantText from '@/components/ChantText.vue';
import {
  buildTimeline,
  createChantPlayer,
  pulseFor,
  transposeFor,
} from '@/helpers/chantPlayer';

const props = defineProps({
  open: { type: Boolean, default: false },
  psalm: { type: Number, required: true },
  // The psalm's verse numbers, to step through.
  verses: { type: Array, default: () => [] },
  verse: { type: Number, default: 1 },
});
const emit = defineEmits(['update:open', 'close']);

const api = () => import.meta.env.VITE_API_URL;
const BOOK_CYCLE = ['', '^', '~'];
const STRESS_CYCLE = ['', '+'];

const current = ref(props.verse);
const data = ref(null);
const loading = ref(false);
const loadError = ref('');
const edited = ref([[], []]);
const tone = ref('');
const preview = ref(null);
const previewError = ref('');
const note = ref('');
const name = ref('');
const email = ref('');
const sending = ref(false);
const sendError = ref('');
const sent = ref(false);
const playing = ref(false);
const position = ref(null);

const player = createChantPlayer({
  onPosition: (syllable) => (position.value = syllable),
  onEnd: () => {
    playing.value = false;
    position.value = null;
  },
});

const verseChoice = computed({
  get: () => current.value,
  set: (value) => goTo(Number(value)),
});
const verseOptions = computed(() =>
  props.verses.map((number) => ({ value: number, label: `Verse ${number}` }))
);
const indexInPsalm = computed(() => props.verses.indexOf(current.value));
const previousVerse = computed(() => props.verses[indexInPsalm.value - 1]);
const nextVerse = computed(() => props.verses[indexInPsalm.value + 1]);

const toneInfo = computed(() =>
  data.value?.tones.find((t) => t.code === tone.value)
);
const bookTone = computed(() => Boolean(toneInfo.value?.book));
const toneOptions = computed(() => {
  if (!data.value) return [];
  const option = (t) => ({ value: t.code, label: t.label });
  return [
    {
      label: 'St. Bernard Psalter',
      options: data.value.tones.filter((t) => t.book).map(option),
    },
    {
      label: 'Other tones',
      options: data.value.tones.filter((t) => !t.book).map(option),
    },
  ];
});

const halves = computed(() => edited.value);
const changed = computed(() => {
  if (!data.value) return false;
  if (tone.value !== data.value.tone.code) return true;
  return [0, 1].some((half) =>
    edited.value[half].some(
      (syllable, index) => syllable.m !== original(half)[index].m
    )
  );
});

function original(half) {
  return half === 0 ? data.value.first_half : data.value.second_half;
}

function words(half) {
  const out = [];
  half.forEach((syllable, index) => {
    if (syllable.w || !out.length) out.push([]);
    out[out.length - 1].push({ ...syllable, index });
  });
  return out;
}

function markName(mark) {
  return (
    { '^': 'bold', '~': 'italic', '=': 'underlined', '+': 'stressed' }[mark] ||
    'plain'
  );
}

function syllableClass(half, index) {
  const mark = edited.value[half][index].m;
  return {
    'is-pointed': mark === '^' || mark === '=',
    'is-slur': mark === '~' || mark === '=',
    'is-stress': mark === '+',
    'is-changed': data.value && mark !== original(half)[index].m,
  };
}

function cycle(half, index) {
  const cycleMarks = bookTone.value ? BOOK_CYCLE : STRESS_CYCLE;
  sent.value = false; // a new edit is a new suggestion
  const syllable = edited.value[half][index];
  const at = cycleMarks.indexOf(syllable.m);
  syllable.m = cycleMarks[(at + 1) % cycleMarks.length];
}

// The notation the server reads: "/" between syllables, a mark before each.
function notation(half) {
  return edited.value[half]
    .map((syllable, index) => {
      const joiner = index === 0 ? '' : syllable.w ? ' ' : '/';
      return `${joiner}${syllable.m}${syllable.t}`;
    })
    .join('');
}

function payload() {
  return {
    psalm: props.psalm,
    verse: current.value,
    first_half: notation(0),
    second_half: notation(1),
    tone: tone.value,
  };
}

async function load() {
  player.stop();
  loading.value = true;
  loadError.value = '';
  preview.value = null;
  try {
    const { data: result } = await axios.get(
      `${api()}api/v1/psalms/${props.psalm}/verses/${current.value}/pointing`
    );
    data.value = result;
    tone.value = result.tone.code;
    reset();
  } catch (error) {
    data.value = null;
    loadError.value = error?.isOffline
      ? 'Suggesting a fix needs a connection.'
      : 'This verse could not be loaded.';
  } finally {
    loading.value = false;
  }
}

function reset() {
  if (!data.value) return;
  edited.value = [
    data.value.first_half.map((s) => ({ ...s })),
    data.value.second_half.map((s) => ({ ...s })),
  ];
  tone.value = data.value.tone.code;
}

// When the tone changes kind, carry the marks across as best we can: a stress
// becomes bold and back.
watch(bookTone, (book, wasBook) => {
  if (!data.value || book === wasBook) return;
  edited.value.forEach((half) =>
    half.forEach((syllable) => {
      if (book && syllable.m === '+') syllable.m = '^';
      else if (!book && syllable.m) syllable.m = '+';
    })
  );
});

let previewTimer = null;
let previewRequest = 0;
watch(
  [edited, tone],
  () => {
    if (!data.value) return;
    window.clearTimeout(previewTimer);
    previewTimer = window.setTimeout(refreshPreview, 250);
  },
  { deep: true }
);

async function refreshPreview() {
  const request = ++previewRequest;
  try {
    const { data: result } = await axios.post(
      `${api()}api/v1/pointing/preview`,
      payload()
    );
    if (request !== previewRequest) return;
    preview.value = result;
    previewError.value = '';
  } catch (error) {
    if (request !== previewRequest) return;
    preview.value = null;
    previewError.value =
      error?.response?.data?.detail || 'The preview isn’t available now.';
  }
}

function play() {
  if (!preview.value) return;
  const timeline = buildTimeline(
    [
      {
        number: current.value,
        halves: [preview.value.first_half, preview.value.second_half],
      },
    ],
    {
      pulse: pulseFor('normal'),
      transpose: transposeFor('medium', data.value.tone.tenor),
    }
  );
  player.play(timeline).then((started) => (playing.value = started));
}

function active(half) {
  const at = position.value;
  return at && at.half === half ? at.index : -1;
}

async function send() {
  sending.value = true;
  sendError.value = '';
  sent.value = false;
  try {
    await axios.post(`${api()}api/v1/pointing/proposals`, {
      ...payload(),
      note: note.value,
      name: name.value,
      email: email.value,
    });
    sent.value = true;
    note.value = '';
    await load();
  } catch (error) {
    sendError.value =
      error?.response?.status === 429
        ? 'That’s a lot of suggestions for one hour; please try again later.'
        : error?.response?.data?.detail ||
          error?.response?.data?.email?.[0] ||
          'Your suggestion could not be sent. Please try again.';
  } finally {
    sending.value = false;
  }
}

function goTo(number) {
  if (!number || number === current.value) return;
  sent.value = false;
  current.value = number;
}

function close() {
  player.stop();
  emit('update:open', false);
  emit('close');
}

watch(
  () => [props.open, props.verse],
  ([open, verse]) => {
    if (!open) return;
    if (verse && verse !== current.value) current.value = verse;
    else load();
  },
  { immediate: true }
);
watch(current, () => {
  if (props.open) load();
});

onBeforeUnmount(() => {
  window.clearTimeout(previewTimer);
  player.stop();
});
</script>

<style scoped>
.pointing-editor {
  --stack-gap: var(--space-4);
}

.pointing-editor__verse {
  flex-wrap: nowrap;
  gap: var(--space-2);
}

.pointing-editor__verse-select {
  flex: 1;
  min-width: 0;
}

.pointing-editor__help {
  color: var(--ink-soft);
  font-size: var(--text-sm);
  margin: 0;
}

.pointing-editor__key {
  font-variant-caps: all-small-caps;
}

.pointing-editor__half {
  font-size: var(--text-lg);
  line-height: 2.1;
}

.pointing-editor__half--second {
  padding-left: var(--space-4);
}

.pointing-editor__word {
  display: inline-block;
  margin-right: 0.3em;
  white-space: nowrap;
}

.pointing-editor__syllable {
  appearance: none;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--ink);
  cursor: pointer;
  font: inherit;
  min-height: 2.2em;
  min-width: 1.6em;
  padding: 0 0.12em;
}

.pointing-editor__syllable + .pointing-editor__syllable {
  border-left: 1px dotted var(--rule);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.pointing-editor__syllable:hover,
.pointing-editor__syllable:focus-visible {
  border-color: var(--accent);
  outline: none;
}

.pointing-editor__syllable.is-pointed {
  font-weight: 700;
}

.pointing-editor__syllable.is-slur {
  font-style: italic;
}

.pointing-editor__syllable.is-stress {
  text-decoration-line: underline;
  text-decoration-color: var(--accent);
  text-decoration-thickness: 0.09em;
  text-underline-offset: 0.18em;
}

.pointing-editor__syllable.is-changed {
  background-color: color-mix(in srgb, var(--accent) 16%, transparent);
}

.pointing-editor__asterisk {
  color: var(--ink-soft);
}

.pointing-editor__sung {
  padding: var(--space-3) var(--space-4);
}

.pointing-editor__sung-head {
  justify-content: space-between;
}

.pointing-editor__sung-head .section-title {
  margin: 0;
}

.pointing-editor__preview {
  margin: var(--space-2) 0 0;
}

.pointing-editor__problem,
.pointing-editor__warnings {
  color: var(--ink-soft);
  font-size: var(--text-sm);
  margin: var(--space-2) 0 0;
}

.pointing-editor__warnings {
  padding-left: 1.2em;
}

.pointing-editor__who {
  display: grid;
  gap: var(--space-3);
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
}

.pointing-editor__actions {
  justify-content: flex-end;
  width: 100%;
}
</style>
