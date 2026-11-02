<template>
  <UiSheet
    :open="panels.menu"
    side="auto"
    size="sm"
    title="Menu"
    @update:open="(value) => (panels.menu = value)"
  >
    <nav class="app-menu" aria-label="Site">
      <section v-for="group in groups" :key="group.title" class="menu-group">
        <h3 class="menu-group__title">{{ group.title }}</h3>
        <ul class="menu-group__list">
          <li v-for="item in group.items" :key="item.label">
            <router-link
              v-if="item.to"
              :to="item.to"
              class="menu-item"
              @click="close"
            >
              <UiIcon :name="item.icon" class="menu-item__icon" />
              <span class="menu-item__label">{{ item.label }}</span>
              <span v-if="item.hint" class="menu-item__hint">{{
                item.hint
              }}</span>
            </router-link>
            <button v-else type="button" class="menu-item" @click="item.action">
              <UiIcon :name="item.icon" class="menu-item__icon" />
              <span class="menu-item__label">{{ item.label }}</span>
              <span v-if="item.hint" class="menu-item__hint">{{
                item.hint
              }}</span>
              <UiIcon
                v-if="item.external"
                name="external"
                class="menu-item__external"
              />
            </button>
          </li>
        </ul>
      </section>
    </nav>
  </UiSheet>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Browser } from '@capacitor/browser';
import { Capacitor } from '@capacitor/core';
import { openPanel, panels } from '@/helpers/panels';
import { SessionStore } from '@/helpers/sessionStore';
import { effectiveDays, network, syncState } from '@/offline';
import { friendlyDate } from '@/offline/format';
import { pwaState } from '@/offline/pwa';
import { newWhatsNew, whatsNewState } from '@/helpers/whatsNew';
import { APP_STORE_URLS } from '@/helpers/appStores';

const route = useRoute();
const router = useRouter();
const platform = Capacitor.getPlatform();
const isWeb = platform === 'web';

const LINKS = {
  kofi: 'https://ko-fi.com/dailyoffice',
  github: 'https://github.com/blocher/dailyoffice2019',
  ...APP_STORE_URLS,
  web: 'https://dailyoffice2019.com/',
};

function close() {
  panels.menu = false;
}

async function openExternal(url) {
  close();
  await Browser.open({ url });
}

async function openCalendarSubscription() {
  close();
  SessionStore.setItem('calendarSubscriptionPanelMode', 'quick');
  const fire = () =>
    window.dispatchEvent(
      new window.CustomEvent('open-calendar-subscription', {
        detail: { source: 'menu', mode: 'quick' },
      })
    );
  if (route.path.startsWith('/calendar')) {
    fire();
    return;
  }
  await router.push({
    path: '/calendar',
    query: { subscribe: '1', panel: 'quick' },
  });
  await nextTick();
  await nextTick();
  fire();
}

// "Ready through tomorrow" is reckoned from when the menu opens, so it moves
// on after midnight (the menu stays mounted).
const openedAt = ref(Date.now());
watch(
  () => panels.menu,
  (open) => {
    if (open) openedAt.value = Date.now();
  }
);

const offlineHint = computed(() => {
  const readyThrough = friendlyDate(
    syncState.readyThrough,
    new Date(openedAt.value)
  );
  if (!network.online) {
    return readyThrough ? `Offline · ready through ${readyThrough}` : 'Offline';
  }
  if (effectiveDays() === 0) return 'Downloads off';
  if (syncState.status === 'syncing') return 'Downloading…';
  return readyThrough ? `Ready through ${readyThrough}` : 'Keep the days ahead';
});

const groups = computed(() => {
  const apps = isWeb
    ? [
        {
          label: 'iPhone & iPad app',
          icon: 'apple',
          external: true,
          action: () => openExternal(LINKS.ios),
        },
        {
          label: 'Android app',
          icon: 'android',
          external: true,
          action: () => openExternal(LINKS.android),
        },
      ]
    : [
        {
          label: 'Web version',
          icon: 'globe',
          external: true,
          action: () => openExternal(LINKS.web),
        },
      ];

  return [
    {
      title: 'Pray',
      items: [
        { label: 'Daily Office', icon: 'book', to: '/office' },
        { label: 'Family Prayer', icon: 'home', to: '/family' },
        { label: "Today's Readings", icon: 'book-text', to: '/readings' },
        { label: 'The Great Litany', icon: 'scroll', to: '/litany' },
        {
          label: 'Podcasts',
          hint: 'Every office, every day',
          icon: 'podcast',
          to: '/podcasts',
        },
      ],
    },
    {
      title: 'Library',
      items: [
        { label: 'Calendar', icon: 'calendar', to: '/calendar' },
        { label: 'The Psalter', icon: 'library', to: '/psalms' },
        { label: 'Collects', icon: 'bookmark', to: '/collects' },
      ],
    },
    {
      title: 'Make it yours',
      items: [
        { label: 'Settings', icon: 'settings', to: '/settings' },
        {
          label: 'Display',
          hint: 'Theme, size, typeface',
          icon: 'text-size',
          action: () => openPanel('display'),
        },
        {
          label: 'Share your settings',
          icon: 'share',
          action: () => openPanel('share'),
        },
        {
          label: 'Add to your calendar app',
          icon: 'calendar-plus',
          action: openCalendarSubscription,
        },
        {
          label: 'Offline',
          hint: offlineHint.value,
          icon: network.online ? 'cloud-check' : 'cloud-off',
          action: () => openPanel('offline'),
        },
        ...(isWeb &&
        !pwaState.installed &&
        (pwaState.canPrompt || pwaState.iosManual)
          ? [
              {
                label: 'Install the app',
                hint: 'Home screen, works offline',
                icon: 'download',
                action: () => openPanel('offline'),
              },
            ]
          : []),
      ],
    },
    {
      title: 'Stay in touch',
      items: [
        ...(whatsNewState.entries.length
          ? [
              {
                label: 'What’s new',
                hint: newWhatsNew.value.length
                  ? `${newWhatsNew.value.length} new`
                  : '',
                icon: 'star',
                action: () => openPanel('whatsNew'),
              },
            ]
          : []),
        {
          label: 'Support the Daily Office',
          icon: 'heart',
          external: true,
          action: () => openExternal(LINKS.kofi),
        },
        {
          label: 'Email updates',
          icon: 'mail',
          action: () => openPanel('email'),
        },
        {
          label: 'Send feedback',
          icon: 'message',
          action: () => openPanel('feedback'),
        },
        { label: 'About', icon: 'info', to: '/about' },
        {
          label: 'Source code',
          icon: 'github',
          external: true,
          action: () => openExternal(LINKS.github),
        },
        ...apps,
      ],
    },
  ];
});
</script>

<style scoped>
.app-menu {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.menu-group__title {
  margin: 0 0 var(--space-1) var(--space-2);
  font-size: var(--text-sm);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  color: var(--ink-faint);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-height: 2.75rem;
  padding: var(--space-2);
  border-radius: var(--radius);
  color: var(--ink);
  text-align: left;
  text-decoration: none;
  transition: background-color var(--duration) var(--ease);
}

.menu-item:hover {
  background-color: var(--paper-sunken);
}

.menu-item.router-link-exact-active {
  background-color: var(--accent-wash);
}

.menu-item__icon {
  font-size: 1.15rem;
  color: var(--accent);
}

.menu-item__label {
  flex: 1 1 auto;
  padding-top: 0.08em;
}

.menu-item__hint {
  font-size: var(--text-xs);
  font-style: italic;
  color: var(--ink-faint);
}

.menu-item__external {
  font-size: 0.85rem;
  color: var(--ink-faint);
}
</style>
