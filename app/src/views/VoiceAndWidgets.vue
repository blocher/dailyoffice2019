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

    <nav class="voice-jump" aria-label="On this page">
      <a v-for="item in jumpLinks" :key="item.id" :href="`#${item.id}`">
        <UiIcon :name="item.icon" />
        {{ item.label }}
      </a>
    </nav>

    <template v-if="shown === 'ios'">
      <!-- Widgets -->
      <section
        id="widgets"
        class="voice-section"
        aria-labelledby="widgets-title"
      >
        <h2 id="widgets-title" class="section-title">
          <UiIcon name="calendar" /> Widgets
        </h2>
        <p>
          Today in the church calendar at a glance: the feast, season and color,
          the saint remembered, and any fast. After 3 p.m. it shows the
          evening’s observance. Tap <strong>Pray</strong> for the office of the
          hour.
        </p>

        <div class="shots">
          <figure class="shot">
            <img
              :src="iosHome"
              width="720"
              height="856"
              loading="lazy"
              alt="An iPhone Home Screen with The Daily Office widget in two sizes: the medium one names the Twenty-fourth Sunday after Pentecost, with Pray and Readings buttons."
            />
            <figcaption>Home Screen: small and medium</figcaption>
          </figure>
          <figure class="shot">
            <img
              :src="iosLock"
              width="720"
              height="556"
              loading="lazy"
              alt="An iPhone Lock Screen showing today’s name, the Twenty-fourth Sunday after Pentecost, under the clock, beside a round Pray button."
            />
            <figcaption>Lock Screen widgets</figcaption>
          </figure>
        </div>

        <div class="howto">
          <UiDisclosure title="Add it to the Home Screen">
            <ol class="steps">
              <li>
                Touch and hold an empty part of the Home Screen until the apps
                jiggle.
              </li>
              <li>
                Tap <strong>Edit</strong> › <strong>Add Widget</strong>, and
                search for <strong>Daily Office</strong>.
              </li>
              <li>
                Swipe to the size you want and tap
                <strong>Add Widget</strong>. The medium size has
                <strong>Pray</strong> and <strong>Readings</strong> buttons.
              </li>
            </ol>
            <p class="voice-note">
              On a weekday when a saint is remembered, the widget names the
              saint. To show the weekday instead, touch and hold the widget and
              choose <strong>Edit Widget</strong>.
            </p>
          </UiDisclosure>
          <UiDisclosure title="Add it to the Lock Screen">
            <ol class="steps">
              <li>
                Touch and hold the Lock Screen, then tap
                <strong>Customize</strong> › <strong>Lock Screen</strong>.
              </li>
              <li>
                Tap the space below the clock (or the date above it, for one
                line of text), and choose <strong>The Daily Office</strong>.
              </li>
              <li>
                Pick the rectangle with today’s name, the round
                <strong>Pray</strong> button, or both, then tap
                <strong>Done</strong>.
              </li>
            </ol>
          </UiDisclosure>
        </div>
      </section>

      <!-- CarPlay -->
      <section id="car" class="voice-section" aria-labelledby="car-title">
        <h2 id="car-title" class="section-title">
          <UiIcon name="headphones" /> CarPlay
        </h2>
        <p>
          Open The Daily Office on your car’s screen to pray the office for the
          time of day, any office, or the day’s readings, read aloud. It keeps
          playing with your phone locked.
        </p>
        <CarScreen system="carplay" />
        <div class="howto">
          <UiDisclosure title="Don’t see it in the car?">
            <ol class="steps">
              <li>
                On your iPhone, open <strong>Settings</strong> ›
                <strong>General</strong> › <strong>CarPlay</strong>, and tap
                your car.
              </li>
              <li>
                Tap <strong>Customize</strong> and make sure
                <strong>The Daily Office</strong> is in the list of apps shown.
              </li>
            </ol>
          </UiDisclosure>
        </div>
      </section>

      <!-- Siri -->
      <section id="voice" class="voice-section" aria-labelledby="siri-title">
        <h2 id="siri-title" class="section-title">
          <UiIcon name="mic" /> Ask Siri
        </h2>
        <p>
          Say “Hey Siri,” then any of these, in the car or anywhere. Each needs
          the app’s name, “The Daily Office” (or just “Daily Office”).
        </p>

        <div class="tip" role="note">
          <UiIcon name="info" />
          <p>
            Say <strong>“Pray”</strong>, not “Play”. Siri can take “Play Morning
            Prayer” to the Daily Office podcast of the same name in the Podcasts
            app.
          </p>
        </div>

        <div
          v-for="group in siriPhrases"
          :key="group.title"
          class="phrase-group"
        >
          <h3 class="phrase-group__title">{{ group.title }}</h3>
          <p v-if="group.note" class="phrase-group__note">{{ group.note }}</p>
          <ul class="phrases">
            <li v-for="phrase in group.phrases" :key="phrase">
              “{{ phrase }}”
            </li>
          </ul>
        </div>

        <p class="voice-note">
          Other names work too: Matins, Noonday Prayer, Evensong, Vespers, Night
          Prayer, and Family Prayer. Needs iOS 17 or later.
        </p>

        <div class="howto">
          <UiDisclosure title="Make your own phrase, such as “Compline”">
            <ol class="steps">
              <li>
                Open the <strong>Shortcuts</strong> app and tap
                <strong>+</strong>.
              </li>
              <li>
                Tap <strong>Add Action</strong>, search for
                <strong>The Daily Office</strong>, and choose
                <strong>Play an Office</strong>.
              </li>
              <li>Tap the office in the action and choose one.</li>
              <li>
                Name the shortcut what you’ll say, such as
                <strong>Compline</strong>, and tap <strong>Done</strong>.
              </li>
            </ol>
            <p class="voice-note">
              The app’s other actions are there too: the day’s feast, collect,
              readings and saints, the next holy day, a psalm read aloud.
            </p>
          </UiDisclosure>
          <UiDisclosure title="Put it on the Action button">
            <p>
              On iPhone 15 Pro and later, open <strong>Settings</strong> ›
              <strong>Action Button</strong>, swipe to
              <strong>Shortcut</strong>, and choose one of The Daily Office’s
              actions, such as <strong>Play an Office</strong>.
            </p>
          </UiDisclosure>
          <UiDisclosure title="Siri Suggestions">
            <p>
              Siri learns when you pray. After you’ve prayed an office in the
              app a few times, it suggests it at that time of day, on the Lock
              Screen and in Search.
            </p>
          </UiDisclosure>
        </div>
      </section>
    </template>

    <template v-else>
      <!-- Widget -->
      <section
        id="widgets"
        class="voice-section"
        aria-labelledby="widgets-title"
      >
        <h2 id="widgets-title" class="section-title">
          <UiIcon name="calendar" /> Home screen widget
        </h2>
        <p>
          Today in the church calendar at a glance: the feast, season and color,
          the saint remembered, and any fast. After 3 p.m. it shows the
          evening’s observance. Tap <strong>Pray</strong> for the office of the
          hour.
        </p>

        <div class="shots shots--single">
          <figure class="shot">
            <img
              :src="androidHome"
              width="720"
              height="553"
              loading="lazy"
              alt="An Android home screen with the Daily Office widget naming the Twenty-fourth Sunday after Pentecost, with Pray and Readings buttons."
            />
            <figcaption>On the home screen</figcaption>
          </figure>
        </div>

        <div class="howto">
          <UiDisclosure title="Add it to your home screen">
            <ol class="steps">
              <li>Touch and hold an empty part of your home screen.</li>
              <li>
                Tap <strong>Widgets</strong> and search for
                <strong>Daily Office</strong>.
              </li>
              <li>
                Tap <strong>Today in the Church Calendar</strong>, then
                <strong>Add</strong>. Resize it by touching and holding it.
              </li>
            </ol>
            <p class="voice-note">
              On a weekday when a saint is remembered, the widget names the
              saint. To show the weekday instead, touch and hold the widget and
              choose <strong>Settings</strong>.
            </p>
          </UiDisclosure>
          <UiDisclosure title="Shortcuts on the app icon">
            <p>
              Touch and hold the Daily Office icon to see
              <strong>Pray now</strong>, <strong>Family Prayer</strong>,
              <strong>Readings</strong> and <strong>Calendar</strong>, and the
              offices you’ve prayed. Drag one onto your home screen to keep it a
              tap away.
            </p>
          </UiDisclosure>
        </div>
      </section>

      <!-- Android Auto -->
      <section id="car" class="voice-section" aria-labelledby="car-title">
        <h2 id="car-title" class="section-title">
          <UiIcon name="headphones" /> Android Auto
        </h2>
        <p>
          Open Daily Office in Android Auto to pray the office for the time of
          day, any office, or the day’s readings, read aloud. It keeps playing
          with your phone locked.
        </p>
        <CarScreen system="auto" />
      </section>

      <!-- Google -->
      <section id="voice" class="voice-section" aria-labelledby="google-title">
        <h2 id="google-title" class="section-title">
          <UiIcon name="mic" /> Ask Google
        </h2>
        <p>
          Say “Hey Google,” then any of these, in the car or anywhere. Each
          needs the app’s name, “Daily Office”.
        </p>
        <div
          v-for="group in googlePhrases"
          :key="group.title"
          class="phrase-group"
        >
          <h3 class="phrase-group__title">{{ group.title }}</h3>
          <p v-if="group.note" class="phrase-group__note">{{ group.note }}</p>
          <ul class="phrases">
            <li v-for="phrase in group.phrases" :key="phrase">
              “{{ phrase }}”
            </li>
          </ul>
        </div>
        <p class="voice-note">
          Other names work too: Matins, Noonday Prayer, Evensong, Vespers, Night
          Prayer, and Family Prayer. Offices you pray in the app are added to
          “Open”, so “Open Compline on Daily Office” works once you’ve prayed
          Compline.
        </p>
        <div class="howto">
          <UiDisclosure title="Gemini">
            <p>
              On Android 16 and later, Gemini can play any office and answer
              questions about the church calendar (the day’s feast, color,
              saints, collect and readings, and when a feast falls), as Google
              opens Gemini to apps.
            </p>
          </UiDisclosure>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, ref } from 'vue';
import { Capacitor } from '@capacitor/core';
import { APP_STORE_URLS } from '@/helpers/appStores';
import UiIcon from '@/ui/UiIcon.vue';
import iosHome from '@/assets/voice/ios-home.webp';
import iosLock from '@/assets/voice/ios-lock.webp';
import androidHome from '@/assets/voice/android-home.webp';

/*
  How to use the apps' widgets, the car, and Siri or Google, in that order.
  The phrases match what the apps understand: the media requests matched by
  VoiceWords (ios/.../Voice/VoiceModel.swift, android/.../voice/VoiceWords.kt),
  the App Shortcuts in ios/App/App/Voice/VoiceIntents.swift, and
  android/.../res/xml/shortcuts.xml. The screenshots (src/assets/voice/) are
  from the iOS 27 simulator and an Android emulator; the car screens are drawn
  here from the apps' CarPlay and Android Auto lists.
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
        title: 'Widgets, CarPlay & Siri',
        lede: 'The day in the church calendar on your Home and Lock Screens, the offices in the car, and prayer by voice.',
      }
    : {
        title: 'Widget, Android Auto & Google',
        lede: 'The day in the church calendar on your home screen, the offices in the car, and prayer by voice.',
      }
);

const jumpLinks = computed(() => [
  { id: 'widgets', label: 'Widgets', icon: 'calendar' },
  {
    id: 'car',
    label: shown.value === 'ios' ? 'CarPlay' : 'Android Auto',
    icon: 'headphones',
  },
  {
    id: 'voice',
    label: shown.value === 'ios' ? 'Siri' : 'Google',
    icon: 'mic',
  },
]);

const siriPhrases = [
  {
    title: 'Pray',
    note: 'Starts the audio straight away, even with your phone locked.',
    phrases: [
      'Pray with The Daily Office',
      'Pray Compline with The Daily Office',
      'Pray Morning Prayer with The Daily Office',
      'Pray Family Prayer with The Daily Office',
      'Read me today’s readings in The Daily Office',
    ],
  },
  {
    title: 'Open',
    note: 'Shows the office to read along.',
    phrases: [
      'Open Evening Prayer in The Daily Office',
      'Open Compline in The Daily Office',
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

const googlePhrases = [
  {
    title: 'Play',
    note: 'Starts the audio straight away, in Android Auto too.',
    phrases: [
      'Play Evening Prayer on Daily Office',
      'Play Compline on Daily Office',
      'Play Daily Office',
      'Play today’s readings on Daily Office',
    ],
  },
  {
    title: 'Open',
    note: 'Shows the page to read along.',
    phrases: [
      'Open Pray now on Daily Office',
      'Open Family Prayer on Daily Office',
      'Open the readings on Daily Office',
      'Open the calendar on Daily Office',
    ],
  },
];

/*
  The apps' car screens, drawn in the page's colors (CarPlay and Android Auto
  can't be captured without a car): the Pray list of
  ios/App/App/Car/CarPlaySceneDelegate.swift and android/.../car/OfficeLibrary.kt.
*/
const CarScreen = defineComponent({
  props: { system: { type: String, default: 'carplay' } },
  setup(props) {
    const rows = [
      { icon: 'sun', title: 'Midday Prayer', detail: 'For this time of day' },
      { icon: 'sun', title: 'Family Prayer at Midday' },
      { header: 'The Daily Office' },
      { icon: 'sunrise', title: 'Morning Prayer' },
      { icon: 'sunset', title: 'Evening Prayer' },
      { icon: 'moon', title: 'Compline' },
    ];
    const tabs = [
      { icon: 'book', label: 'Pray', active: true },
      { icon: 'book-text', label: 'Readings' },
    ];
    return () =>
      h('figure', { class: ['car', `car--${props.system}`] }, [
        h(
          'div',
          {
            class: 'car__screen',
            role: 'img',
            'aria-label':
              props.system === 'carplay'
                ? 'The Daily Office in CarPlay: a Pray tab listing the office for this time of day, Family Prayer, and the Daily Office offices, and a Readings tab.'
                : 'Daily Office in Android Auto: a Pray list with the office for this time of day, Family Prayer, and the Daily Office offices, and a Readings list.',
          },
          [
            h(
              'div',
              { class: 'car__rail', 'aria-hidden': 'true' },
              tabs.map((tab) =>
                h('span', { class: ['car__tab', tab.active && 'is-active'] }, [
                  h(UiIcon, { name: tab.icon }),
                  h('span', tab.label),
                ])
              )
            ),
            h('div', { class: 'car__list', 'aria-hidden': 'true' }, [
              h(
                'div',
                { class: 'car__heading' },
                'Twenty-fourth Sunday after Pentecost'
              ),
              ...rows.map((row) =>
                row.header
                  ? h('div', { class: 'car__section' }, row.header)
                  : h('div', { class: 'car__row' }, [
                      h(UiIcon, { name: row.icon }),
                      h('span', { class: 'car__text' }, [
                        h('span', { class: 'car__title' }, row.title),
                        row.detail &&
                          h('span', { class: 'car__detail' }, row.detail),
                      ]),
                    ])
              ),
            ]),
          ]
        ),
        h(
          'figcaption',
          props.system === 'carplay'
            ? 'On the car’s screen: Pray and Readings'
            : 'In Android Auto: Pray and Readings'
        ),
      ]);
  },
});
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
  margin-bottom: var(--space-5);
}

.voice-guide__get {
  margin: 0;
  color: var(--ink-soft);
  font-size: var(--text-sm);
}

/* Jump links */
.voice-jump {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
  margin: 0 0 var(--space-6);
}

.voice-jump a {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 2.75rem;
  padding: var(--space-1) var(--space-4);
  border: 1px solid var(--rule);
  border-radius: var(--radius-pill);
  background-color: var(--paper-raised);
  color: var(--ink);
  font-size: var(--text-sm);
  text-decoration: none;
}

.voice-jump a:hover,
.voice-jump a:focus-visible {
  border-color: var(--accent);
}

.voice-jump :deep(svg) {
  color: var(--accent);
}

.voice-section {
  margin-bottom: var(--space-7);
  color: var(--ink);
  font-size: var(--text-md);
  line-height: var(--leading-prose);
  scroll-margin-top: calc(var(--header-height, 3.5rem) + var(--space-4));
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

/* Screenshots */
.shots {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: start;
  gap: var(--space-4);
  margin: var(--space-4) 0;
}

.shots--single {
  grid-template-columns: minmax(0, 26rem);
  justify-content: center;
}

@media (max-width: 30rem) {
  .shots {
    grid-template-columns: minmax(0, 1fr);
  }
}

.shot {
  margin: 0;
}

.shot img {
  display: block;
  width: 100%;
  height: auto;
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.shot figcaption,
.voice-section :deep(.car figcaption) {
  margin-top: var(--space-2);
  color: var(--ink-faint);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.06em;
  text-align: center;
}

.howto {
  margin-top: var(--space-3);
  border-top: 1px solid var(--rule);
}

/* Tip */
.tip {
  display: flex;
  gap: var(--space-3);
  align-items: flex-start;
  margin: var(--space-3) 0 var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius);
  background-color: var(--accent-wash);
}

.tip :deep(svg) {
  flex: none;
  margin-top: 0.2em;
  color: var(--accent);
}

.voice-section .tip p {
  margin: 0;
}

/* Phrases */
.phrase-group__title {
  margin: var(--space-4) 0 var(--space-1);
  color: var(--ink-faint);
  font-size: var(--text-sm);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.06em;
}

.voice-section .phrase-group__note {
  margin: 0 0 var(--space-2);
  color: var(--ink-soft);
  font-size: var(--text-sm);
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

/* The car screen, drawn in the page's own colors */
.voice-section :deep(.car) {
  margin: var(--space-4) 0;
}

.voice-section :deep(.car__screen) {
  display: grid;
  grid-template-columns: 4.5rem minmax(0, 1fr);
  overflow: hidden;
  border: 6px solid var(--ink);
  border-radius: var(--radius-lg);
  background-color: var(--paper-sunken);
  box-shadow: var(--shadow-sm);
  font-family:
    system-ui,
    -apple-system,
    'Segoe UI',
    Roboto,
    sans-serif;
}

.voice-section :deep(.car--auto .car__screen) {
  border-radius: var(--radius);
}

.voice-section :deep(.car__rail) {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-1);
  border-right: 1px solid var(--rule);
  background-color: var(--paper-raised);
}

.voice-section :deep(.car__tab) {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: var(--space-2) 0;
  border-radius: var(--radius-sm);
  color: var(--ink-faint);
  font-size: var(--text-xs);
}

.voice-section :deep(.car__tab.is-active) {
  background-color: var(--accent-wash);
  color: var(--accent);
}

.voice-section :deep(.car__list) {
  padding: var(--space-3) var(--space-4) var(--space-2);
}

.voice-section :deep(.car__heading),
.voice-section :deep(.car__section) {
  color: var(--ink-faint);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.voice-section :deep(.car__section) {
  margin-top: var(--space-3);
}

.voice-section :deep(.car__row) {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--rule);
  font-size: var(--text-sm);
  line-height: var(--leading-tight);
}

.voice-section :deep(.car__row:last-child) {
  border-bottom: none;
}

.voice-section :deep(.car__row svg) {
  flex: none;
  color: var(--accent);
}

.voice-section :deep(.car__text) {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.voice-section :deep(.car__title) {
  color: var(--ink);
  font-weight: 600;
}

.voice-section :deep(.car__detail) {
  color: var(--ink-soft);
  font-size: var(--text-xs);
}
</style>
