<template>
  <section class="custom-podcast" aria-labelledby="custom-podcast-title">
    <header class="custom-podcast__head">
      <UiTag tone="warning">Experimental</UiTag>
      <h2 id="custom-podcast-title" class="custom-podcast__title">
        Make your own podcast
      </h2>
      <p class="custom-podcast__lede">
        Any office or readings, prayed with your own settings, in your podcast
        app. Your feed keeps the last {{ options.window_days || 7 }} days, with
        each new day at {{ options.publish_hour || 2 }}&nbsp;a.m. Eastern.
      </p>
    </header>

    <div class="custom-podcast__card surface">
      <ol v-if="!created" class="steps">
        <li v-for="item in steps" :key="item.number">
          <button
            type="button"
            class="step"
            :class="{
              'is-current': step === item.number,
              'is-done': step > item.number,
            }"
            :aria-current="step === item.number ? 'step' : null"
            :disabled="!canJumpTo(item.number)"
            @click="step = item.number"
          >
            <span class="step__number" aria-hidden="true">
              <UiIcon v-if="step > item.number" name="check" />
              <template v-else>{{ item.number }}</template>
            </span>
            <span class="step__label">{{ item.label }}</span>
          </button>
        </li>
      </ol>

      <!-- 1. Type -->
      <fieldset v-if="!created && step === 1" class="builder-step">
        <legend class="builder-label">What would you like to hear?</legend>
        <div class="choices">
          <label
            v-for="type in options.types"
            :key="type.slug"
            class="choice"
            :class="{ 'is-selected': typeSlug === type.slug }"
          >
            <input
              type="radio"
              class="choice__input"
              name="custom-podcast-type"
              :value="type.slug"
              :checked="typeSlug === type.slug"
              @change="chooseType(type.slug)"
            />
            <UiIcon :name="typeIcon(type.slug)" class="choice__icon" />
            <span class="choice__text">
              <span class="choice__title">{{ typeLabel(type) }}</span>
              <span class="choice__note">{{ type.description }}</span>
            </span>
          </label>
        </div>
      </fieldset>

      <!-- 2. Office -->
      <fieldset v-if="!created && step === 2" class="builder-step">
        <legend class="builder-label">Which one?</legend>
        <div class="choices">
          <label
            v-for="office in offices"
            :key="office.service"
            class="choice"
            :class="{ 'is-selected': service === office.service }"
          >
            <input
              type="radio"
              class="choice__input"
              name="custom-podcast-office"
              :value="office.service"
              :checked="service === office.service"
              @change="chooseOffice(office.service)"
            />
            <UiIcon
              :name="office.is_readings ? 'book-text' : 'book'"
              class="choice__icon"
            />
            <span class="choice__text">
              <span class="choice__title">{{ office.title }}</span>
            </span>
          </label>
        </div>
      </fieldset>

      <!-- 3. Settings -->
      <fieldset v-if="!created && step === 3" class="builder-step">
        <legend class="builder-label">Settings for {{ officeTitle }}</legend>
        <div class="choices choices--two">
          <label
            class="choice"
            :class="{ 'is-selected': settingsMode === 'current' }"
          >
            <input
              type="radio"
              class="choice__input"
              name="custom-podcast-settings"
              value="current"
              :checked="settingsMode === 'current'"
              @change="settingsMode = 'current'"
            />
            <UiIcon name="check-circle" class="choice__icon" />
            <span class="choice__text">
              <span class="choice__title">Use my current settings</span>
              <span class="choice__note">{{
                summarize(snapshot.settings)
              }}</span>
            </span>
          </label>
          <label
            class="choice"
            :class="{ 'is-selected': settingsMode === 'custom' }"
          >
            <input
              type="radio"
              class="choice__input"
              name="custom-podcast-settings"
              value="custom"
              :checked="settingsMode === 'custom'"
              @change="openCustomize"
            />
            <UiIcon name="sliders" class="choice__icon" />
            <span class="choice__text">
              <span class="choice__title">Customize…</span>
              <span class="choice__note">
                <template v-if="draft">
                  {{ summarize(draft)
                  }}<template v-if="changedCount">
                    · {{ changedCount }} changed from yours</template
                  >
                </template>
                <template v-else>
                  Choose every setting for this podcast alone.
                </template>
              </span>
            </span>
          </label>
        </div>
        <UiButton
          v-if="settingsMode === 'custom'"
          variant="quiet"
          size="sm"
          icon="pen"
          class="builder-edit"
          @click="openCustomize"
        >
          Edit these settings
        </UiButton>
        <p v-if="snapshot.adjusted.length" class="builder-hint">
          <UiIcon name="info" />
          Audio is read only in English (traditional or contemporary), from the
          ESV or the KJV, with the Coverdale or Renewed Coverdale Psalter, so
          this podcast changes some of your settings to fit.
        </p>
      </fieldset>

      <!-- 4. Player -->
      <fieldset v-if="!created && step === 4" class="builder-step">
        <legend class="builder-label">Which podcast app do you use?</legend>
        <div class="choices choices--apps">
          <label
            v-for="app in appChoices"
            :key="app.id"
            class="choice choice--compact"
            :class="{ 'is-selected': appId === app.id }"
          >
            <input
              type="radio"
              class="choice__input"
              name="custom-podcast-app"
              :value="app.id"
              :checked="appId === app.id"
              @change="appId = app.id"
            />
            <UiIcon :name="app.icon" class="choice__icon" />
            <span class="choice__text">
              <span class="choice__title">{{ app.name }}</span>
              <span class="choice__note">{{ app.platforms }}</span>
            </span>
          </label>
        </div>
        <p class="builder-hint">
          <UiIcon name="info" />
          <span>
            Spotify and YouTube Music can’t follow a private feed like this one.
            To listen there, use
            <button type="button" class="text-link" @click="showPublic">
              our public podcasts
            </button>
            instead.
          </span>
        </p>
        <UiAlert
          v-if="createError"
          tone="error"
          :title="createError"
          class="builder-alert"
        />
      </fieldset>

      <!-- Done -->
      <section v-if="created" class="builder-done" aria-live="polite">
        <div class="builder-done__head">
          <img
            class="builder-done__art"
            :src="created.artwork_url"
            alt=""
            width="600"
            height="600"
          />
          <div>
            <p class="eyebrow">Your podcast</p>
            <h3 class="builder-done__title">{{ created.title }}</h3>
            <p class="builder-done__style">{{ created.style_label }}</p>
          </div>
        </div>

        <div class="builder-feed">
          <label class="builder-label" for="custom-podcast-feed-url">
            Feed link
          </label>
          <div class="builder-feed__row">
            <input
              id="custom-podcast-feed-url"
              class="ui-control"
              type="text"
              readonly
              :value="created.feed_url"
              @focus="$event.target.select()"
            />
            <UiButton
              :variant="selectedApp ? 'secondary' : 'primary'"
              icon="copy"
              @click="copyFeed"
            >
              Copy
            </UiButton>
          </div>
          <p class="builder-hint builder-hint--plain">
            Keep this link to yourself: anyone with it can listen. Episodes
            appear as they’re ready, usually within a few minutes.
          </p>
        </div>

        <div class="builder-add">
          <template v-if="selectedApp">
            <UiButton
              variant="primary"
              :icon="selectedApp.icon"
              :href="selectedApp.href"
              class="builder-add__open"
            >
              Subscribe in {{ selectedApp.name }}
            </UiButton>
            <h4 class="builder-label">Or add it by hand</h4>
            <ol class="builder-add__steps">
              <li>Copy the feed link above.</li>
              <li v-for="(line, index) in selectedApp.steps" :key="index">
                {{ line }}
              </li>
            </ol>
          </template>
          <template v-else>
            <h4 class="builder-label">Add it to your app</h4>
            <p class="builder-add__any">
              Copy the link, then paste it into your app’s “Add by URL,” “Follow
              a Show by URL,” or “RSS feed” option.
            </p>
          </template>
        </div>

        <div class="builder-nav">
          <UiButton variant="ghost" icon="reset" @click="startOver">
            Make another
          </UiButton>
        </div>
      </section>

      <div v-if="!created" class="builder-nav">
        <UiButton
          v-if="step > 1"
          variant="ghost"
          icon="arrow-left"
          @click="step -= 1"
        >
          Back
        </UiButton>
        <UiButton
          v-if="step === 3"
          variant="primary"
          icon-right="arrow-right"
          :disabled="settingsMode === 'custom' && !draft"
          @click="step = 4"
        >
          Continue
        </UiButton>
        <UiButton
          v-if="step === 4"
          variant="primary"
          icon="podcast"
          :disabled="!appId"
          :loading="creating"
          @click="create"
        >
          Make my podcast
        </UiButton>
      </div>
    </div>

    <p class="custom-podcast__feedback">
      <UiIcon name="mail" />
      <span>
        This is new, and we’d love to hear how it works for you:
        <a :href="feedbackHref">feedback@dailyoffice2019.com</a>
      </span>
    </p>

    <UiSheet
      :open="customizing"
      size="lg"
      eyebrow="Customize"
      :title="`Settings for ${officeTitle}`"
      subtitle="These apply only to this podcast. Your own settings stay as they are."
      @update:open="(open) => !open && closeCustomize()"
    >
      <div v-if="draft" class="customize">
        <UiAlert tone="info" title="Read in English, from the ESV or the KJV">
          The voices read only those two translations, in traditional or
          contemporary language, with the Coverdale or Renewed Coverdale
          Psalter, so only those are offered here.
        </UiAlert>

        <template v-if="isReadings">
          <div class="surface customize__rows">
            <SettingRow
              v-for="row in readingsRows"
              :key="row.name"
              :setting="row"
              :value="draft[row.name]"
              :open="openRow === row.name"
              @update:open="(open) => (openRow = open ? row.name : '')"
              @change="(value) => (draft = { ...draft, [row.name]: value })"
            />
          </div>
        </template>

        <template v-else>
          <p v-if="!customizable.length" class="customize__empty">
            The settings are still loading.
          </p>
          <template v-else>
            <UiSegmented
              v-model="customizeSite"
              :options="siteTabs"
              variant="underline"
              block
              aria-label="Which settings to show"
            />
            <label for="custom-podcast-search" class="visually-hidden">
              Search settings
            </label>
            <UiInput
              id="custom-podcast-search"
              v-model="customizeSearch"
              icon="search"
              clearable
              placeholder="Search settings"
            />
            <SettingsPanel
              :key="customizeSite"
              :available-settings="customizable"
              :site="customizeSite"
              :search-query="customizeSearch"
              :values="draft"
              @update:values="(values) => (draft = values)"
            />
          </template>
        </template>
      </div>
      <template #footer>
        <UiButton variant="ghost" icon="reset" @click="resetDraft">
          Start from my settings
        </UiButton>
        <UiButton variant="primary" icon="check" @click="closeCustomize">
          Done
        </UiButton>
      </template>
    </UiSheet>
  </section>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useStore } from 'vuex';
import axios from 'axios';
import { Clipboard } from '@capacitor/clipboard';
import SettingRow from '@/components/SettingRow.vue';
import SettingsPanel from '@/components/SettingsPanel.vue';
import {
  customizableSettings,
  podcastApps,
  readingsSettingRows,
  snapshotSettings,
} from '@/helpers/podcasts';
import { toast } from '@/ui/feedback';

/*
  EXPERIMENTAL: build a private podcast feed of one office (or the
  readings) with the reader's own settings. "Use my current settings" takes
  a snapshot of the Vuex settings; "Customize…" edits a local copy in a sheet
  and never touches the reader's own. The server makes the feed and its
  episodes (site/podcasts/custom.py).
*/
const props = defineProps({
  options: { type: Object, required: true },
});

const FEEDBACK_EMAIL = 'feedback@dailyoffice2019.com';
const COPY_ONLY = {
  id: 'copy',
  name: 'Copy URL',
  platforms: 'Any app that adds a feed by URL',
  icon: 'link',
};

const store = useStore();
const steps = [
  { number: 1, label: 'Type' },
  { number: 2, label: 'Office' },
  { number: 3, label: 'Settings' },
  { number: 4, label: 'Player' },
];
const step = ref(1);
const typeSlug = ref('');
const service = ref('');
const settingsMode = ref('current');
const draft = ref(null);
const customizing = ref(false);
const customizeSite = ref('Daily Office');
const customizeSearch = ref('');
const openRow = ref('');
const appId = ref('');
const creating = ref(false);
const createError = ref('');
const created = ref(null);

const siteTabs = [
  { value: 'Daily Office', label: 'Daily Office' },
  { value: 'Family Prayer', label: 'Family Prayer' },
];

const selectedType = computed(() =>
  props.options.types.find((type) => type.slug === typeSlug.value)
);
const offices = computed(() => selectedType.value?.offices || []);
const selectedOffice = computed(() =>
  offices.value.find((office) => office.service === service.value)
);
const officeTitle = computed(() => selectedOffice.value?.title || '');
const isReadings = computed(() => Boolean(selectedOffice.value?.is_readings));

const snapshot = computed(() =>
  snapshotSettings(props.options, isReadings.value, store.state.settings || {})
);
const chosenSettings = computed(() =>
  settingsMode.value === 'custom' && draft.value
    ? draft.value
    : snapshot.value.settings
);
const changedCount = computed(() => {
  if (!draft.value) return 0;
  return Object.keys(draft.value).filter(
    (key) => draft.value[key] !== snapshot.value.settings[key]
  ).length;
});

const customizable = computed(() =>
  customizableSettings(store.state.availableSettings, props.options)
);
const readingsRows = computed(() => readingsSettingRows(props.options));

const appChoices = computed(() => [...podcastApps(''), COPY_ONLY]);
const selectedApp = computed(() => {
  if (!created.value || appId.value === COPY_ONLY.id) return null;
  return podcastApps(created.value.feed_url, {
    title: created.value.title,
  }).find((app) => app.id === appId.value);
});

const feedbackHref = computed(() => {
  const body = created.value ? `\n\n(My feed: ${created.value.feed_url})` : '';
  return `mailto:${FEEDBACK_EMAIL}?subject=${encodeURIComponent(
    'Custom podcast feedback'
  )}${body ? `&body=${encodeURIComponent(body)}` : ''}`;
});

function typeLabel(type) {
  return type.slug === 'readings'
    ? 'Readings'
    : type.title.replace(/^The /, '');
}

function typeIcon(slug) {
  return { 'daily-office': 'book', family: 'home', readings: 'book-text' }[
    slug
  ];
}

function canJumpTo(number) {
  if (number === 1) return true;
  if (number === 2) return Boolean(typeSlug.value);
  return Boolean(service.value);
}

function chooseType(slug) {
  if (slug !== typeSlug.value) {
    service.value = '';
    draft.value = null;
    settingsMode.value = 'current';
  }
  typeSlug.value = slug;
  customizeSite.value = slug === 'family' ? 'Family Prayer' : 'Daily Office';
  step.value = 2;
}

function chooseOffice(value) {
  const wasReadings = isReadings.value;
  service.value = value;
  // Office and readings settings are different lists; start the copy over.
  if (draft.value && wasReadings !== isReadings.value) {
    draft.value = null;
    settingsMode.value = 'current';
  }
  step.value = 3;
}

function openCustomize() {
  settingsMode.value = 'custom';
  if (!draft.value) draft.value = { ...snapshot.value.settings };
  customizing.value = true;
}

function closeCustomize() {
  customizing.value = false;
}

function resetDraft() {
  draft.value = { ...snapshot.value.settings };
}

function summarize(settings) {
  if (!settings) return '';
  const parts = [
    (settings.translation || settings.bible_translation || '').toUpperCase(),
  ];
  const psalms = settings.psalms || settings.psalm_translation;
  if (settings.language_style) {
    parts.push(
      settings.language_style === 'traditional'
        ? 'Traditional language'
        : 'Contemporary language'
    );
  } else if (psalms) {
    parts.push(
      psalms === 'traditional' ? 'Coverdale Psalter' : 'Renewed Coverdale'
    );
  }
  if (settings.psalter) parts.push(`${settings.psalter}-day psalter`);
  return parts.filter(Boolean).join(' · ');
}

async function create() {
  creating.value = true;
  createError.value = '';
  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_URL}api/v1/podcasts/custom`,
      { service: service.value, settings: { ...chosenSettings.value } }
    );
    created.value = response.data;
  } catch (error) {
    const status = error?.response?.status;
    if (status === 429) {
      createError.value =
        'You’ve made several podcasts in a short time. Please try again in an hour.';
    } else if (status === 400 && error.response.data?.detail) {
      createError.value = error.response.data.detail;
    } else {
      createError.value =
        'Your podcast couldn’t be made just now. Please try again.';
    }
  } finally {
    creating.value = false;
  }
}

async function copyFeed() {
  try {
    await Clipboard.write({ string: created.value.feed_url });
    toast.success('The feed link is copied to your clipboard.');
  } catch {
    toast.error('Couldn’t copy the link. Select it and copy it instead.');
  }
}

function showPublic() {
  document
    .getElementById('podcasts-ours-title')
    ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function startOver() {
  created.value = null;
  createError.value = '';
  step.value = 1;
  typeSlug.value = '';
  service.value = '';
  draft.value = null;
  settingsMode.value = 'current';
  appId.value = '';
}
</script>

<style scoped>
.custom-podcast {
  max-width: 52rem;
  margin: 0 auto;
}

.custom-podcast__head {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-5);
  text-align: center;
}

.custom-podcast__title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  line-height: 1.2;
  color: var(--ink);
}

.custom-podcast__lede {
  max-width: 36rem;
  margin: 0;
  color: var(--ink-soft);
  font-style: italic;
  line-height: var(--leading-prose);
}

.custom-podcast__card {
  padding: var(--space-5);
}

@media (max-width: 480px) {
  .custom-podcast__card {
    padding: var(--space-4) var(--space-3);
  }
}

/* Steps, as in the calendar wizard. */
.steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin: 0 0 var(--space-5);
  padding: 0;
  border-bottom: 1px solid var(--rule);
  list-style: none;
}

.step {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
  width: 100%;
  min-height: 3.5rem;
  padding: var(--space-2) var(--space-1);
  color: var(--ink-faint);
  text-align: center;
  transition: color var(--duration) var(--ease);
}

.step::after {
  content: '';
  position: absolute;
  left: 18%;
  right: 18%;
  bottom: -1px;
  height: 2px;
  border-radius: 2px;
  background-color: transparent;
}

.step:hover:not(:disabled) {
  color: var(--ink);
}

.step:disabled {
  cursor: default;
  opacity: 0.6;
}

.step.is-done {
  color: var(--ink-soft);
}

.step.is-current {
  color: var(--ink);
}

.step.is-current::after {
  background-color: var(--accent);
}

.step:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.step__number {
  display: grid;
  place-items: center;
  width: 1.5rem;
  height: 1.5rem;
  border: 1px solid var(--rule-strong);
  border-radius: 50%;
  font-size: var(--text-xs);
  line-height: 1;
  font-variant-numeric: lining-nums;
}

.step.is-current .step__number {
  border-color: var(--accent);
  color: var(--accent);
}

.step.is-done .step__number {
  border-color: var(--accent-rule);
  color: var(--accent);
}

.step__label {
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  line-height: 1.1;
}

@media (max-width: 379px) {
  .step__label {
    font-size: var(--text-xs);
    letter-spacing: 0.04em;
  }
}

@media (min-width: 480px) {
  .step {
    flex-direction: row;
    justify-content: center;
    gap: var(--space-2);
  }
}

.builder-step {
  margin: 0;
  padding: 0;
  border: 0;
  min-width: 0;
}

.builder-label {
  display: block;
  margin: 0 0 var(--space-3);
  padding: 0;
  font-size: var(--text-md);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  line-height: 1.3;
  color: var(--ink-faint);
}

/* Radio cards. */
.choices {
  display: grid;
  gap: var(--space-2);
}

@media (min-width: 560px) {
  .choices {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .choices--apps {
    grid-template-columns: repeat(auto-fill, minmax(12rem, 1fr));
  }
}

.choice {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  min-height: 3.25rem;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background-color: var(--paper);
  color: var(--ink);
  cursor: pointer;
  transition:
    border-color var(--duration) var(--ease),
    background-color var(--duration) var(--ease);
}

.choice:hover {
  background-color: var(--paper-sunken);
}

.choice.is-selected {
  border-color: var(--accent);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.choice:focus-within {
  box-shadow: var(--focus-ring);
}

.choice--compact {
  align-items: center;
  padding: var(--space-2) var(--space-3);
}

.choice__input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.choice__icon {
  flex: 0 0 auto;
  margin-top: 0.15em;
  font-size: 1.15rem;
  color: var(--accent);
}

.choice--compact .choice__icon {
  margin-top: 0;
}

.choice__text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.choice__title {
  font-size: var(--text-md);
  line-height: var(--leading-tight);
}

.choice__note {
  font-size: var(--text-sm);
  font-style: italic;
  line-height: var(--leading-ui);
  color: var(--ink-faint);
  overflow-wrap: anywhere;
}

.builder-edit {
  margin-top: var(--space-2);
}

.builder-hint {
  display: flex;
  gap: var(--space-2);
  margin: var(--space-4) 0 0;
  font-size: var(--text-sm);
  line-height: var(--leading-prose);
  color: var(--ink-soft);
}

.builder-hint > .ui-icon {
  flex: 0 0 auto;
  margin-top: 0.25em;
  color: var(--ink-faint);
}

.builder-hint--plain {
  margin-top: var(--space-2);
  font-style: italic;
  color: var(--ink-faint);
}

.builder-alert {
  margin-top: var(--space-4);
}

.text-link {
  display: inline;
  padding: 0;
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 0.15em;
}

.builder-nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-2);
  margin-top: var(--space-5);
}

.builder-nav > :last-child {
  margin-left: auto;
}

.builder-done {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.builder-done__head {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  min-width: 0;
}

.builder-done__art {
  flex: 0 0 auto;
  width: clamp(4rem, 20vw, 5.5rem);
  height: clamp(4rem, 20vw, 5.5rem);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  object-fit: cover;
  background-color: var(--paper-sunken);
}

.builder-done__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--ink);
}

.builder-done__style {
  margin: var(--space-1) 0 0;
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-soft);
}

.builder-feed__row {
  display: flex;
  gap: var(--space-2);
}

.builder-feed__row input {
  flex: 1 1 auto;
  min-width: 0;
  font-size: var(--text-sm);
  color: var(--ink-soft);
  text-overflow: ellipsis;
}

.builder-add__open {
  margin-bottom: var(--space-4);
  max-width: 100%;
  white-space: normal;
}

.builder-add__steps {
  margin: 0;
  padding-left: 1.4em;
  list-style: decimal;
  color: var(--ink-soft);
  line-height: var(--leading-prose);
}

.builder-add__steps li + li {
  margin-top: var(--space-1);
}

.builder-add__any {
  margin: 0;
  color: var(--ink-soft);
  line-height: var(--leading-prose);
}

.custom-podcast__feedback {
  display: flex;
  justify-content: center;
  gap: var(--space-2);
  margin: var(--space-4) 0 0;
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-faint);
  text-align: center;
}

.custom-podcast__feedback > .ui-icon {
  flex: 0 0 auto;
  margin-top: 0.25em;
}

.custom-podcast__feedback a {
  color: var(--accent);
  overflow-wrap: anywhere;
}

.customize {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.customize__rows {
  overflow: hidden;
}

.customize__empty {
  font-style: italic;
  color: var(--ink-faint);
  text-align: center;
}
</style>
