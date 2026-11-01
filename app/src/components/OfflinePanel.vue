<template>
  <UiSheet
    :open="panels.offline"
    side="auto"
    title="Offline"
    eyebrow="This device"
    subtitle="Pray without a connection"
    @update:open="(value) => (panels.offline = value)"
  >
    <section class="offline-hero" :class="`is-${hero.tone}`">
      <span class="offline-hero__icon" aria-hidden="true">
        <UiIcon :name="hero.icon" />
      </span>
      <div class="offline-hero__copy">
        <!-- Only the title is announced: the text changes with every download
             (the progress bar carries the count). -->
        <p class="offline-hero__title" aria-live="polite">{{ hero.title }}</p>
        <p v-if="hero.text" class="offline-hero__text">{{ hero.text }}</p>
        <div
          v-if="showProgress"
          class="offline-progress"
          role="progressbar"
          :aria-valuenow="sync.done"
          :aria-valuemin="0"
          :aria-valuemax="sync.total"
          aria-label="Downloading for offline use"
        >
          <span
            class="offline-progress__bar"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>
      </div>
    </section>

    <ol
      v-if="days > 0 && strip.length"
      class="offline-days"
      aria-label="Days kept on this device"
    >
      <li
        v-for="day in strip"
        :key="day.iso"
        class="offline-day"
        :class="{ 'is-ready': day.ready, 'is-today': day.today }"
        :title="`${day.label}: ${day.ready ? 'ready offline' : 'not yet downloaded'}`"
      >
        <span class="offline-day__weekday">{{ day.weekday }}</span>
        <span class="offline-day__date">{{ day.date }}</span>
        <span class="offline-day__mark" aria-hidden="true">
          <UiIcon v-if="day.ready" name="check" />
        </span>
        <span class="visually-hidden">{{
          day.ready ? 'ready offline' : 'not yet downloaded'
        }}</span>
      </li>
      <li
        v-if="days > strip.length"
        class="offline-day offline-day--more"
        :title="`${days - strip.length} more days`"
      >
        <span aria-hidden="true">+{{ days - strip.length }}</span>
        <span class="visually-hidden"
          >and {{ days - strip.length }} more days</span
        >
      </li>
    </ol>

    <section class="sheet-block">
      <h3 class="sheet-block__title">
        <UiIcon name="calendar-days" /> Days to keep
      </h3>
      <p class="sheet-block__text">
        Today and the days ahead, for your settings. More days, more room.
      </p>
      <UiSegmented
        class="offline-days-choice"
        :model-value="days"
        :options="dayOptions"
        size="sm"
        block
        aria-label="Days to keep offline"
        @update:model-value="(value) => setOfflinePref('days', value)"
      />
      <p class="offline-note">{{ daysNote }}</p>
    </section>

    <section class="sheet-block">
      <h3 class="sheet-block__title"><UiIcon name="book" /> Include</h3>
      <div class="offline-row">
        <div class="offline-row__copy">
          <p class="offline-row__label">The Daily Office</p>
          <p class="offline-row__hint">
            Morning, Midday, and Evening Prayer and Compline. Always included.
          </p>
        </div>
        <UiSwitch :model-value="true" disabled label="The Daily Office" />
      </div>
      <div class="offline-row">
        <div class="offline-row__copy">
          <p class="offline-row__label">Family Prayer</p>
          <p class="offline-row__hint">{{ familyHint }}</p>
        </div>
        <UiSwitch
          :model-value="familyOn"
          label="Include Family Prayer"
          @update:model-value="
            (on) => setOfflinePref('family', on ? 'on' : 'off')
          "
        />
      </div>
    </section>

    <section class="sheet-block">
      <h3 class="sheet-block__title"><UiIcon name="headphones" /> Audio</h3>
      <div class="offline-row">
        <div class="offline-row__copy">
          <p class="offline-row__label">Listen offline</p>
          <p class="offline-row__hint">{{ audioHint }}</p>
        </div>
        <UiSwitch
          :model-value="prefs.audio"
          :disabled="!audioPossible"
          label="Download audio for offline listening"
          @update:model-value="(on) => setOfflinePref('audio', on)"
        />
      </div>
      <div v-if="prefs.audio && audioPossible" class="offline-audio">
        <p class="offline-audio__legend" id="offline-audio-offices">Offices</p>
        <div
          class="offline-audio__choices"
          role="group"
          aria-labelledby="offline-audio-offices"
        >
          <UiCheckbox
            v-for="choice in audioChoices"
            :key="choice.value"
            :model-value="prefs.audioOffices"
            :value="choice.value"
            :label="choice.label"
            @update:model-value="setAudioOffices"
          />
        </div>
        <p class="offline-note">{{ audioNote }}</p>
      </div>
    </section>

    <section class="sheet-block">
      <h3 class="sheet-block__title">
        <UiIcon name="hard-drive-download" /> On this device
      </h3>
      <p class="sheet-block__text">{{ deviceLine }}</p>
      <div class="sheet-block__actions">
        <UiButton
          icon="refresh"
          size="sm"
          :disabled="!network.online || busy"
          :loading="busy"
          @click="syncNow"
        >
          {{ busy ? 'Updating…' : 'Update now' }}
        </UiButton>
        <UiButton
          variant="ghost"
          size="sm"
          icon="close"
          :disabled="!storedBytes"
          @click="removeDownloads"
        >
          Remove downloads
        </UiButton>
      </div>
    </section>

    <section v-if="showInstall" class="sheet-block offline-install">
      <h3 class="sheet-block__title">
        <UiIcon name="phone" /> Install the app
      </h3>
      <p class="sheet-block__text">{{ installText }}</p>
      <div v-if="pwa.canPrompt" class="sheet-block__actions">
        <UiButton variant="primary" size="sm" icon="download" @click="install">
          Install The Daily Office
        </UiButton>
      </div>
      <ol v-else class="offline-steps">
        <li>
          <span class="offline-steps__icon" aria-hidden="true"
            ><UiIcon name="share-up"
          /></span>
          Tap <strong>Share</strong> in Safari’s toolbar.
        </li>
        <li>
          <span class="offline-steps__icon" aria-hidden="true"
            ><UiIcon name="square-plus"
          /></span>
          Choose <strong>Add to Home Screen</strong>.
        </li>
      </ol>
    </section>

    <p class="offline-footnote">{{ footnote }}</p>
  </UiSheet>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useStore } from 'vuex';
import { Capacitor } from '@capacitor/core';
import { panels } from '@/helpers/panels';
import { confirm, toast } from '@/ui/feedback';
import {
  DAY_CHOICES,
  clearDownloads,
  effectiveDays,
  nativeSyncState as nativeSync,
  network,
  offlinePrefs as prefs,
  requestSync,
  setOfflinePref,
  syncState as sync,
} from '@/offline';
import { pwaState as pwa, promptInstall } from '@/offline/pwa';
import { usedRecently } from '@/offline/usage';
import { isInstalledApp } from '@/offline/preferences';
import {
  ESTIMATE_BYTES,
  estimateBytes,
  formatBytes,
  friendlyDate,
  relativeTime,
} from '@/offline/format';

const store = useStore();
const familyUsed = ref(false);
const readingsUsed = ref(false);
const now = ref(Date.now());
// "Today" and "checked … ago" move on while the panel stays open.
let clock = null;

function stopClock() {
  window.clearInterval(clock);
  clock = null;
}

onBeforeUnmount(stopClock);

watch(
  () => panels.offline,
  async (open) => {
    stopClock();
    if (!open) return;
    now.value = Date.now();
    clock = window.setInterval(() => {
      now.value = Date.now();
    }, 60 * 1000);
    [familyUsed.value, readingsUsed.value] = await Promise.all([
      usedRecently('family'),
      usedRecently('readings'),
    ]);
  }
);

const installed = computed(() => pwa.installed || isInstalledApp());
const days = computed(() => effectiveDays());
const busy = computed(() => ['checking', 'syncing'].includes(sync.status));

const dayOptions = DAY_CHOICES.map((value) => ({
  value,
  label: value === 0 ? 'Off' : String(value),
  title: value === 0 ? 'Don’t download ahead' : `${value} days`,
}));

const familyOn = computed(
  () => prefs.family === 'on' || (prefs.family === 'auto' && familyUsed.value)
);

const familyHint = computed(() => {
  if (prefs.family === 'auto') {
    return familyUsed.value
      ? 'Included because you’ve prayed it lately.'
      : 'Included once you pray it.';
  }
  return 'Short services for households and children.';
});

const daysNote = computed(() => {
  const parts = [
    days.value
      ? `About ${estimate.value}.`
      : 'Pages you open are still kept for a while.',
  ];
  if (prefs.days === null) {
    parts.push(
      `${days.value} days is the default ${installed.value ? 'for the app' : 'in a browser'}.`
    );
  }
  return parts.join(' ');
});

const estimate = computed(() =>
  formatBytes(
    estimateBytes({
      days: days.value,
      family: familyOn.value,
      readings: readingsUsed.value,
    })
  )
);

const settings = computed(() => store.state.settings || {});
const audioPossible = computed(
  () =>
    ['esv', 'kjv'].includes(settings.value.bible_translation || 'esv') &&
    (settings.value.display_language || 'english') === 'english'
);

const audioChoices = [
  { value: 'morning_prayer', label: 'Morning' },
  { value: 'midday_prayer', label: 'Midday' },
  { value: 'evening_prayer', label: 'Evening' },
  { value: 'compline', label: 'Compline' },
];

function setAudioOffices(value) {
  // Keep the order the offices are prayed in.
  const ordered = audioChoices
    .map((choice) => choice.value)
    .filter((office) => value.includes(office));
  setOfflinePref('audioOffices', ordered);
}

const audioHint = computed(() =>
  audioPossible.value
    ? 'Downloads the spoken office for today and tomorrow.'
    : 'Downloads the spoken office for today and tomorrow. Audio is read from the ESV or KJV, in English.'
);

const audioNote = computed(() => {
  const tracks = prefs.audioOffices.length * 2;
  const parts = [
    `About ${audioEstimate.value} for ${tracks} ${tracks === 1 ? 'track' : 'tracks'}.`,
  ];
  if (audioStatus.value) parts.push(audioStatus.value);
  return parts.join(' ');
});

const audioEstimate = computed(() =>
  formatBytes(prefs.audioOffices.length * 2 * ESTIMATE_BYTES.audioPerOffice)
);

const audioStatus = computed(() => {
  const audio = sync.audio;
  if (!audio.wanted) return '';
  if (audio.active) return 'Downloading…';
  const parts = [`${audio.ready} of ${audio.wanted} ready`];
  if (audio.preparing) parts.push(`${audio.preparing} still being recorded`);
  return `${parts.join(', ')}.`;
});

const storedBytes = computed(() => sync.storageBytes + sync.audio.bytes);

const storageLine = computed(() => {
  if (!storedBytes.value) return 'Nothing downloaded yet.';
  const audio = sync.audio.bytes
    ? `, ${formatBytes(sync.audio.bytes)} of it audio`
    : '';
  return `Using ${formatBytes(storedBytes.value)}${audio}.`;
});

const lastSynced = computed(() => relativeTime(sync.lastSyncAt, now.value));

const deviceLine = computed(() =>
  sync.lastSyncAt
    ? `${storageLine.value} Checked for updates ${lastSynced.value}.`
    : storageLine.value
);

const installText = computed(
  () =>
    `Opens from your home screen like any app, keeps a month of offices, and stays up to date${pwa.iosManual ? '' : ' in the background'}.`
);

const footnote = computed(() => {
  const when =
    pwa.backgroundSync === 'on' || nativeSync.scheduled
      ? 'whenever the app opens, and in the background'
      : 'whenever the app opens';
  return `Downloads refresh ${when}. Corrections reach this device the next time it’s online. Display settings always work offline; other settings need a connection.`;
});

const readyThroughLabel = computed(() =>
  friendlyDate(sync.readyThrough, new Date(now.value))
);

const progressPercent = computed(() =>
  sync.total ? Math.round((sync.done / sync.total) * 100) : 0
);

const showProgress = computed(
  () => sync.status === 'syncing' && sync.total > 0
);

const hero = computed(() => {
  const through = readyThroughLabel.value;
  if (!network.online) {
    if (sync.readyDays > 0) {
      return {
        tone: 'offline',
        icon: 'cloud-off',
        title: 'You’re offline',
        text: `Your offices are here through ${through}.`,
      };
    }
    return {
      tone: 'offline',
      icon: 'cloud-off',
      title: 'You’re offline',
      text: 'Nothing is downloaded for your settings yet. It will be, the next time you’re online.',
    };
  }
  if (days.value === 0) {
    return {
      tone: 'muted',
      icon: 'cloud-off',
      title: 'Downloads are off',
      text: 'Choose how many days to keep, and the app works without a connection.',
    };
  }
  if (sync.status === 'unavailable') {
    return {
      tone: 'warning',
      icon: 'warning',
      title: 'This browser can’t keep downloads',
      text: 'A private window, or blocked site data, keeps the app from saving offices on this device. Pages still work while you’re online.',
    };
  }
  if (sync.status === 'syncing') {
    return {
      tone: 'busy',
      icon: 'cloud-download',
      title:
        sync.reason === 'settings'
          ? 'Downloading for your new settings'
          : 'Downloading the days ahead',
      text: sync.current
        ? `${sync.done} of ${sync.total} · ${capitalize(sync.current)}`
        : `${sync.done} of ${sync.total}`,
    };
  }
  if (sync.status === 'checking') {
    return {
      tone: 'busy',
      icon: 'cloud-download',
      title: 'Checking for updates',
      text: sync.readyDays ? `Ready through ${through}.` : '',
    };
  }
  if (sync.status === 'error' && sync.error) {
    return {
      tone: 'warning',
      icon: 'warning',
      title: sync.readyDays ? `Ready through ${through}` : 'Not finished',
      text: sync.error,
    };
  }
  if (sync.readyDays > 0) {
    return {
      tone: 'ready',
      icon: 'cloud-check',
      title: `Ready offline through ${through}`,
      text: `${sync.readyDays} ${sync.readyDays === 1 ? 'day' : 'days'} of offices, for your settings.`,
    };
  }
  return {
    tone: 'busy',
    icon: 'cloud-download',
    title: 'Getting ready',
    text: 'The days ahead download in a moment.',
  };
});

function capitalize(text) {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// Up to two weeks of days, marked ready or not.
const strip = computed(() => {
  const count = Math.min(days.value, 14);
  const start = new Date(now.value);
  start.setHours(0, 0, 0, 0);
  return Array.from({ length: count }, (_, offset) => {
    const date = new Date(start);
    date.setDate(start.getDate() + offset);
    const pad = (n) => String(n).padStart(2, '0');
    const iso = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
    return {
      iso,
      today: offset === 0,
      weekday: date.toLocaleDateString('en-US', { weekday: 'narrow' }),
      date: date.getDate(),
      label: date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
      }),
      ready: Boolean(sync.readyThrough) && iso <= sync.readyThrough,
    };
  });
});

const showInstall = computed(
  () =>
    !Capacitor.isNativePlatform() &&
    !installed.value &&
    (pwa.canPrompt || pwa.iosManual)
);

async function install() {
  const outcome = await promptInstall();
  if (outcome === 'accepted') {
    toast.success({
      title: 'Installed',
      message: 'Open The Daily Office from your home screen or app list.',
    });
  }
}

function syncNow() {
  requestSync('manual');
}

async function removeDownloads() {
  const ok = await confirm({
    title: 'Remove downloads?',
    message:
      'The offices, readings, and audio kept on this device are removed. They download again the next time the app is online, unless you turn downloads off.',
    confirmText: 'Remove',
    tone: 'danger',
  });
  if (!ok) return;
  try {
    await clearDownloads();
  } catch {
    toast.error('Some downloads couldn’t be removed. Try again.');
    return;
  }
  toast.success('Downloads removed from this device.');
}
</script>

<style scoped>
/* The state, at a glance */
.offline-hero {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  padding: var(--space-4);
  margin-bottom: var(--space-4);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  background-color: var(--paper-raised);
}

.offline-hero.is-ready {
  border-color: var(--accent-rule);
  background-color: var(--accent-wash);
}

.offline-hero.is-offline {
  border-color: var(--rule-strong);
  background-color: var(--paper-sunken);
}

.offline-hero__icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background-color: var(--paper);
  border: 1px solid var(--rule);
  color: var(--accent);
  font-size: var(--text-lg);
}

.offline-hero.is-offline .offline-hero__icon,
.offline-hero.is-muted .offline-hero__icon {
  color: var(--ink-soft);
}

.offline-hero.is-warning .offline-hero__icon {
  color: var(--tone-warning);
}

.offline-hero.is-busy .offline-hero__icon .ui-icon {
  animation: offline-bob 1.6s var(--ease) infinite;
}

@keyframes offline-bob {
  0%,
  100% {
    transform: translateY(-1px);
  }
  50% {
    transform: translateY(2px);
  }
}

.offline-hero__copy {
  flex: 1;
  min-width: 0;
  padding-top: 0.1rem;
}

.offline-hero__title {
  font-size: var(--text-md);
  line-height: var(--leading-tight);
  color: var(--ink);
}

.offline-hero__text {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  line-height: 1.4;
  color: var(--ink-soft);
  overflow-wrap: anywhere;
}

.offline-progress {
  height: 4px;
  margin-top: var(--space-3);
  border-radius: 2px;
  background-color: var(--rule);
  overflow: hidden;
}

.offline-progress__bar {
  display: block;
  height: 100%;
  border-radius: 2px;
  background-color: var(--accent);
  transition: width 300ms var(--ease);
}

/* The days kept, as a strip of dates */
.offline-days {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: var(--space-1);
  margin: 0 0 var(--space-5);
  padding: 0;
  list-style: none;
}

.offline-day {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.1rem;
  padding: 0.35rem 0 0.3rem;
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  color: var(--ink-faint);
  font-size: var(--text-xs);
  line-height: 1.1;
  transition:
    background-color var(--duration) var(--ease),
    border-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}

.offline-day__weekday {
  font-variant-caps: all-small-caps;
  letter-spacing: 0.08em;
}

.offline-day__date {
  font-size: var(--text-sm);
  color: inherit;
}

.offline-day__mark {
  display: grid;
  place-items: center;
  height: 0.9rem;
  font-size: var(--text-xs);
  color: var(--accent);
}

.offline-day.is-ready {
  border-color: var(--accent-rule);
  background-color: var(--accent-wash);
  color: var(--ink);
}

.offline-day.is-today {
  box-shadow: inset 0 -2px 0 var(--accent);
}

.offline-day--more {
  justify-content: center;
  border-style: dashed;
  font-size: var(--text-sm);
}

.offline-days-choice {
  margin-top: var(--space-3);
}

.offline-note {
  margin-top: var(--space-2);
  font-size: var(--text-xs);
  font-style: italic;
  color: var(--ink-faint);
  line-height: 1.45;
}

/* A setting with a switch */
.offline-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3) 0 0;
}

.offline-row__copy {
  min-width: 0;
}

.offline-row__label {
  font-size: var(--text-md);
  color: var(--ink);
}

.offline-row__hint {
  margin-top: 0.15rem;
  font-size: var(--text-sm);
  color: var(--ink-soft);
  line-height: 1.4;
}

.offline-audio {
  margin-top: var(--space-3);
  padding: var(--space-3);
  border-radius: var(--radius);
  background-color: var(--paper-sunken);
}

.offline-audio__legend {
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-soft);
}

.offline-audio__choices {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-1) var(--space-3);
  margin-top: var(--space-2);
}

/* Safari's two steps */
.offline-steps {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: var(--space-3) 0 0;
  padding: 0;
  list-style: none;
  font-size: var(--text-sm);
  color: var(--ink-soft);
}

.offline-steps li {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* Labels in small caps, as elsewhere, not bold. */
.offline-steps strong {
  font-weight: inherit;
  font-variant-caps: all-small-caps;
  color: var(--ink);
}

.offline-steps__icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius);
  border: 1px solid var(--rule);
  background-color: var(--paper-raised);
  color: var(--tone-info);
  font-size: 1.05rem;
}

.offline-footnote {
  margin-top: var(--space-2);
  padding-top: var(--space-4);
  border-top: 1px solid var(--rule);
  font-size: var(--text-xs);
  font-style: italic;
  color: var(--ink-faint);
  line-height: 1.5;
}
</style>
