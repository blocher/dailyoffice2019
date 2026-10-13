<template>
  <header class="app-header" :class="{ 'is-hidden': hidden }">
    <div class="app-header__bar">
      <router-link to="/" class="wordmark" aria-label="The Daily Office, home">
        <span class="wordmark__title">The Daily Office</span>
        <span class="wordmark__subtitle">Book of Common Prayer 2019</span>
      </router-link>

      <nav class="primary-nav" aria-label="Primary">
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="primary-nav__link"
          :class="{ 'is-active': item.active }"
          :aria-current="item.active ? 'page' : null"
        >
          {{ item.label }}
        </router-link>
      </nav>

      <div class="header-actions">
        <button
          type="button"
          class="header-action"
          :class="{ 'is-open': panels.display }"
          aria-label="Display: theme, text size, typeface, audio"
          :aria-expanded="panels.display ? 'true' : 'false'"
          @click="toggle('display')"
        >
          <span class="header-action__glyph" aria-hidden="true">Aa</span>
          <span class="header-action__label">Display</span>
        </button>
        <button
          type="button"
          class="header-action header-action--support"
          aria-label="Support the Daily Office"
          @click="openSupport"
        >
          <UiIcon
            name="heart"
            class="header-action__icon header-action__heart"
          />
          <span class="header-action__label header-action__label--always"
            >Support</span
          >
        </button>
        <button
          type="button"
          class="header-action"
          :class="{ 'is-open': panels.menu }"
          aria-label="Menu"
          :aria-expanded="panels.menu ? 'true' : 'false'"
          @click="toggle('menu')"
        >
          <UiIcon name="menu" class="header-action__icon" />
          <span class="header-action__label">Menu</span>
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { Browser } from '@capacitor/browser';
import { openPanel, panels } from '@/helpers/panels';

const PRAY_ROUTES = [
  'Home',
  'PrayWithDate',
  'FamilyPrayer',
  'FamilyPrayerToday',
  'FamilyPrayerWithDate',
  'readings',
  'readingsByService',
  'readingsByServiceAndDate',
  'readingsByServicePositionAndDate',
  'readingsByDate',
];

const route = useRoute();
const hidden = ref(false);
let lastY = 0;

const navItems = computed(() => [
  { to: '/', label: 'Pray', active: PRAY_ROUTES.includes(route.name) },
  {
    to: '/calendar',
    label: 'Calendar',
    active: route.name === 'calendar' || route.name === 'day',
  },
  { to: '/settings', label: 'Settings', active: route.name === 'Settings' },
]);

function toggle(name) {
  if (panels[name]) {
    panels[name] = false;
  } else {
    openPanel(name);
  }
}

async function openSupport() {
  await Browser.open({ url: 'https://ko-fi.com/dailyoffice' });
}

// Slide away while reading down the page; come back on any upward scroll.
function onScroll() {
  const y = window.scrollY || document.documentElement.scrollTop || 0;
  if (y < 80) {
    hidden.value = false;
  } else if (Math.abs(y - lastY) > 6) {
    hidden.value = y > lastY;
  }
  lastY = y;
}

watch(
  () => route.fullPath,
  () => {
    hidden.value = false;
  }
);

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }));
onBeforeUnmount(() => window.removeEventListener('scroll', onScroll));
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  padding-top: env(safe-area-inset-top);
  background-color: var(--paper-overlay);
  backdrop-filter: saturate(1.2) blur(10px);
  -webkit-backdrop-filter: saturate(1.2) blur(10px);
  border-bottom: 1px solid var(--rule);
  transition: transform 260ms var(--ease);
}

.app-header.is-hidden {
  transform: translateY(-100%);
}

.app-header__bar {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  max-width: var(--page-width);
  height: var(--header-height);
  margin: 0 auto;
  padding: 0 max(var(--space-2), calc(var(--gutter) - var(--space-2)));
}

/* Wordmark */
.wordmark {
  display: none;
  flex-direction: column;
  justify-content: center;
  padding: 0 var(--space-2);
  color: var(--ink);
  text-decoration: none;
  line-height: 1;
}

.wordmark__title {
  font-size: 1.15rem;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
}

.wordmark__subtitle {
  margin-top: 0.2rem;
  font-size: 0.72rem;
  font-style: italic;
  color: var(--ink-faint);
  letter-spacing: 0.02em;
}

/* Primary nav */
.primary-nav {
  display: flex;
  align-items: stretch;
  height: 100%;
  gap: var(--space-1);
}

.primary-nav__link {
  position: relative;
  display: flex;
  align-items: center;
  padding: 0 0.6rem;
  color: var(--ink-soft);
  font-size: var(--text-md);
  text-decoration: none;
  transition: color var(--duration) var(--ease);
}

.primary-nav__link::after {
  content: '';
  position: absolute;
  left: 0.6rem;
  right: 0.6rem;
  bottom: -1px;
  height: 2px;
  border-radius: 2px;
  background-color: transparent;
  transition: background-color var(--duration) var(--ease);
}

.primary-nav__link:hover {
  color: var(--ink);
}

.primary-nav__link.is-active {
  color: var(--ink);
}

.primary-nav__link.is-active::after {
  background-color: var(--accent);
}

/* Actions */
.header-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  margin-left: auto;
}

/* With labels showing, keep each icon close to its word and the actions
   clearly apart from one another. */
@media (min-width: 860px) {
  .header-actions {
    gap: var(--space-3);
  }
}

.header-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  line-height: 1;
  min-width: 2.5rem;
  height: 2.5rem;
  padding: 0 0.55rem;
  border-radius: var(--radius);
  color: var(--ink-soft);
  font-size: var(--text-sm);
  transition:
    background-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}

.header-action:hover,
.header-action.is-open {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

.header-action__icon {
  position: relative;
  /* Optical: center on the words' lowercase, not their full line box */
  top: -0.09em;
  font-size: 1.1rem;
}

.header-action__glyph {
  position: relative;
  top: 0.06em;
  font-size: 1.15rem;
  line-height: 1;
  letter-spacing: 0.02em;
}

.header-action--support .header-action__icon {
  color: var(--accent);
}

.header-action__label {
  display: none;
}

/* Support is always named. On phones the heart gives way to the word,
   which takes the accent color instead. */
.header-action__label--always {
  display: inline;
}

@media (max-width: 639px) {
  .header-action__heart {
    display: none;
  }

  .header-action--support {
    color: var(--accent);
  }
}

@media (min-width: 860px) {
  .wordmark {
    display: flex;
    margin-right: var(--space-4);
  }

  .header-action__label {
    display: inline;
  }
}

@media (max-width: 479px) {
  .app-header__bar {
    gap: var(--space-1);
  }

  .primary-nav {
    gap: 0;
  }

  .primary-nav__link {
    padding: 0 0.45rem;
  }

  .primary-nav__link::after {
    left: 0.45rem;
    right: 0.45rem;
  }

  .header-action {
    padding: 0 0.45rem;
  }
}

@media (max-width: 359px) {
  .primary-nav__link {
    padding: 0 0.3rem;
    font-size: var(--text-sm);
  }

  .primary-nav__link::after {
    left: 0.3rem;
    right: 0.3rem;
  }

  .header-action {
    min-width: 2.25rem;
    padding: 0 0.35rem;
  }
}
</style>
