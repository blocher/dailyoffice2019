<template>
  <div class="page voice-guide">
    <header class="page-header">
      <p class="eyebrow">Pray hands-free</p>
      <h1 class="page-title">{{ copy.title }}</h1>
      <p class="page-lede">{{ copy.lede }}</p>
    </header>

    <!-- On the website both apps are described; in an app, its own. -->
    <div v-if="isWeb" class="voice-guide__platform">
      <UiSegmented
        v-model="shown"
        :options="platformOptions"
        size="sm"
        aria-label="Which app"
      />
      <p class="voice-guide__get">
        These work in the
        <a :href="storeLink" target="_blank" rel="noopener">{{
          shown === 'ios' ? 'iPhone and iPad app' : 'Android app'
        }}</a
        >.
      </p>
    </div>

    <template v-if="shown === 'ios'">
      <section class="voice-section" aria-labelledby="siri-title">
        <h2 id="siri-title" class="section-title">
          <UiIcon name="mic" /> Ask Siri
        </h2>
        <p>
          Say “Hey Siri,” then any of these. Siri needs the app’s name, “The
          Daily Office” (or just “Daily Office”), in each one. If Siri mishears,
          try typing to Siri.
        </p>
        <div
          v-for="group in siriPhrases"
          :key="group.title"
          class="phrase-group"
        >
          <h3 class="phrase-group__title">{{ group.title }}</h3>
          <ul class="phrases">
            <li v-for="phrase in group.phrases" :key="phrase">
              “{{ phrase }}”
            </li>
          </ul>
        </div>
        <p class="voice-note">
          Siri plays an office or the readings without opening the app, even
          with the phone locked, and answers questions aloud on AirPods. Other
          names work too: Noonday Prayer, Evensong, Vespers, Matins, Night
          Prayer. To read along, say “Open” instead of “Play”. Needs iOS 17 or
          later.
        </p>
      </section>

      <section class="voice-section" aria-labelledby="shortcuts-title">
        <h2 id="shortcuts-title" class="section-title">
          <UiIcon name="link" /> Make your own Siri phrase
        </h2>
        <p>
          To say just “Play Compline” (without the app’s name), make a shortcut
          with that name:
        </p>
        <ol class="steps">
          <li>
            Open the <strong>Shortcuts</strong> app and tap <strong>+</strong>.
          </li>
          <li>
            Tap <strong>Add Action</strong>, search for
            <strong>The Daily Office</strong>, and choose
            <strong>Play an Office</strong>.
          </li>
          <li>
            Tap the office in the action and choose one, such as Compline.
          </li>
          <li>
            Name the shortcut what you’ll say, such as
            <strong>Play Compline</strong>, and tap <strong>Done</strong>.
          </li>
        </ol>
        <p>
          The Daily Office’s other actions are there too: the day’s feast,
          collect, readings and saints, the next holy day, a psalm read aloud.
          Put one on the <strong>Action button</strong> (iPhone 15 Pro and
          later) in Settings › Action Button › Shortcut.
        </p>
        <p class="voice-note">
          Siri also learns when you pray: after you’ve prayed an office in the
          app a few times, it suggests it at that time of day.
        </p>
      </section>

      <section class="voice-section" aria-labelledby="home-widget-title">
        <h2 id="home-widget-title" class="section-title">
          <UiIcon name="calendar" /> Home Screen widget
        </h2>
        <p>
          Today in the church calendar: the feast, season and color, the saint
          remembered, and any fast. After 3 p.m. it shows the evening’s
          observance.
        </p>
        <ol class="steps">
          <li>
            Touch and hold an empty part of the Home Screen until the apps
            jiggle.
          </li>
          <li>
            Tap <strong>Edit</strong> › <strong>Add Widget</strong>, and search
            for <strong>Daily Office</strong>.
          </li>
          <li>
            Choose the small or medium size and tap
            <strong>Add Widget</strong>. The medium size adds
            <strong>Pray</strong> and <strong>Readings</strong> buttons.
          </li>
        </ol>
        <p>
          On a weekday when a saint is remembered, the widget names the saint.
          To show the weekday instead, touch and hold the widget and choose
          <strong>Edit Widget</strong> (iOS 17 and later).
        </p>
      </section>

      <section class="voice-section" aria-labelledby="lock-widget-title">
        <h2 id="lock-widget-title" class="section-title">
          <UiIcon name="phone" /> Lock Screen widgets
        </h2>
        <ol class="steps">
          <li>
            Touch and hold the Lock Screen, then tap
            <strong>Customize</strong> › <strong>Lock Screen</strong>.
          </li>
          <li>
            Tap the space above the clock for a one-line widget, or below it for
            the others, and choose <strong>The Daily Office</strong>.
          </li>
          <li>
            Pick the round <strong>Pray</strong> button, the rectangle with
            today’s name, or both, then tap <strong>Done</strong>.
          </li>
        </ol>
        <p class="voice-note">
          Pray opens the office for the time of day, ready to pray. Needs iOS 16
          or later.
        </p>
      </section>

      <section class="voice-section" aria-labelledby="carplay-title">
        <h2 id="carplay-title" class="section-title">
          <UiIcon name="headphones" /> CarPlay
        </h2>
        <p>
          Open The Daily Office on your car’s screen to play the office for now,
          any office, or the day’s readings. Siri works in the car too, with the
          phone locked: “Hey Siri, play Midday Prayer on The Daily Office.”
          Pressing play with nothing to resume plays the office for now.
        </p>
      </section>
    </template>

    <template v-else>
      <section class="voice-section" aria-labelledby="google-title">
        <h2 id="google-title" class="section-title">
          <UiIcon name="mic" /> Ask Google
        </h2>
        <p>Say “Hey Google,” then any of these:</p>
        <ul class="phrases">
          <li>“Play Evening Prayer on Daily Office”</li>
          <li>“Play Compline on Daily Office”</li>
          <li>“Play Daily Office” (the office for now)</li>
          <li>“Open Pray now on Daily Office”</li>
          <li>“Open Family Prayer on Daily Office”</li>
          <li>“Open the readings on Daily Office”</li>
          <li>“Open the calendar on Daily Office”</li>
        </ul>
        <p>
          “Play” starts the audio without opening the app; “Open” shows the page
          to read along. Offices you pray in the app are added too, so “Open
          Compline on Daily Office” works once you’ve prayed Compline.
        </p>
        <p class="voice-note">
          On Android 16 and later, Gemini can play any office and answer
          questions about the church calendar (the day’s feast, color, saints,
          collect and readings, and when a feast falls), as Google opens Gemini
          to apps.
        </p>
      </section>

      <section class="voice-section" aria-labelledby="android-shortcuts-title">
        <h2 id="android-shortcuts-title" class="section-title">
          <UiIcon name="link" /> Shortcuts
        </h2>
        <ol class="steps">
          <li>
            Touch and hold the Daily Office icon to see
            <strong>Pray now</strong>, <strong>Family Prayer</strong>,
            <strong>Readings</strong> and <strong>Calendar</strong>, and the
            offices you’ve prayed.
          </li>
          <li>
            Drag one onto your home screen to keep it a tap away. Pray now
            starts the audio for the office of the hour.
          </li>
        </ol>
      </section>

      <section class="voice-section" aria-labelledby="android-widget-title">
        <h2 id="android-widget-title" class="section-title">
          <UiIcon name="calendar" /> Home screen widget
        </h2>
        <p>
          Today in the church calendar: the feast, season and color, the saint
          remembered, and any fast, with <strong>Pray</strong> and
          <strong>Readings</strong> buttons. After 3 p.m. it shows the evening’s
          observance.
        </p>
        <ol class="steps">
          <li>Touch and hold an empty part of your home screen.</li>
          <li>
            Tap <strong>Widgets</strong> and find
            <strong>Daily Office</strong> (or search for “Church”).
          </li>
          <li>
            Tap <strong>Today in the Church Calendar</strong>, then
            <strong>Add</strong>. Resize it by touching and holding it.
          </li>
        </ol>
        <p>
          On a weekday when a saint is remembered, the widget names the saint.
          To show the weekday instead, touch and hold the widget and choose
          <strong>Settings</strong>.
        </p>
      </section>

      <section class="voice-section" aria-labelledby="auto-title">
        <h2 id="auto-title" class="section-title">
          <UiIcon name="headphones" /> Android Auto
        </h2>
        <p>
          Open Daily Office in Android Auto to play the office for now, any
          office, or the day’s readings. Or ask: “Hey Google, play Evensong on
          Daily Office,” or “play today’s readings on Daily Office.”
        </p>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { Capacitor } from '@capacitor/core';
import { APP_STORE_URLS } from '@/helpers/appStores';

/*
  How to use the apps with Siri, Google, shortcuts, widgets and the car.
  The phrases match what the apps offer: ios/App/App/Voice/VoiceIntents.swift
  (DailyOfficeShortcuts), the words both apps understand (VoiceWords in
  ios/.../Voice/VoiceModel.swift and android/.../voice/VoiceWords.kt), and
  android/.../res/xml/shortcuts.xml.
*/
const platform = Capacitor.getPlatform();
const isWeb = platform === 'web';
const prefersAndroid = /android/i.test(window.navigator?.userAgent || '');
const shown = ref(
  platform === 'android' || (isWeb && prefersAndroid) ? 'android' : 'ios'
);

const platformOptions = [
  { value: 'ios', label: 'iPhone & iPad', icon: 'apple' },
  { value: 'android', label: 'Android', icon: 'android' },
];

const storeLink = computed(() =>
  shown.value === 'ios' ? APP_STORE_URLS.ios : APP_STORE_URLS.android
);

const copy = computed(() =>
  shown.value === 'ios'
    ? {
        title: 'Siri & Widgets',
        lede: 'Pray, listen, and ask about the church calendar without opening the app, from Siri, the Home and Lock Screens, and CarPlay.',
      }
    : {
        title: 'Google & Widgets',
        lede: 'Pray, listen, and see the church calendar from Google, your home screen, and Android Auto.',
      }
);

const siriPhrases = [
  {
    title: 'Pray',
    phrases: [
      'Play Compline on The Daily Office',
      'Play Midday Prayer on The Daily Office',
      'Pray Morning Prayer with The Daily Office',
      'Play Evensong in The Daily Office',
      'Play Family Prayer in The Daily Office',
      'Read me Night Prayer in The Daily Office',
      'Play The Daily Office',
      'Open Evening Prayer in The Daily Office',
      'Play today’s readings in The Daily Office',
    ],
  },
  {
    title: 'Ask',
    phrases: [
      'What’s today in The Daily Office',
      'What are today’s readings in The Daily Office',
      'Read me the collect in The Daily Office',
      'Who do we remember today in The Daily Office',
      'What color is it today in The Daily Office',
      'Is today a fast day in The Daily Office',
      'When is Easter in The Daily Office',
    ],
  },
];
</script>

<style scoped>
.voice-guide {
  max-width: 44rem;
}

.voice-guide__platform {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
}

.voice-guide__get {
  margin: 0;
  color: var(--ink-soft);
  font-size: var(--text-sm);
}

.voice-section {
  margin-bottom: var(--space-7);
  color: var(--ink);
  font-size: var(--text-md);
  line-height: var(--leading-prose);
}

.voice-section .section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.voice-section .section-title :deep(svg) {
  color: var(--accent);
}

.voice-section p {
  margin: var(--space-2) 0 var(--space-3);
}

.phrase-group__title {
  margin: var(--space-4) 0 var(--space-2);
  color: var(--ink-faint);
  font-size: var(--text-sm);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.06em;
}

.phrases {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.phrases li {
  padding: var(--space-2) var(--space-3);
  border-left: 3px solid var(--accent);
  border-radius: var(--radius-sm);
  background-color: var(--paper-sunken);
  font-style: italic;
}

.steps {
  margin: var(--space-2) 0 var(--space-3);
  padding-left: 1.4em;
  list-style: decimal outside;
}

.steps li::marker {
  color: var(--ink-faint);
}

.steps li {
  margin-bottom: var(--space-2);
}

.voice-note {
  color: var(--ink-soft);
  font-size: var(--text-sm);
}
</style>
