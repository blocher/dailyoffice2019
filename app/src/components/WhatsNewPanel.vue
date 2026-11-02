<template>
  <UiSheet
    :open="panels.whatsNew"
    side="auto"
    size="sm"
    title="What’s new"
    :subtitle="subtitle"
    @update:open="(value) => (panels.whatsNew = value)"
  >
    <p class="visually-hidden" aria-live="polite">{{ announcement }}</p>

    <p v-if="whatsNewState.status === 'loading'" class="sheet-intro">
      Loading…
    </p>
    <p v-else-if="whatsNewState.status === 'failed'" class="sheet-intro">
      What’s new couldn’t load. Check your connection and try again.
    </p>
    <p v-else-if="!whatsNewState.entries.length" class="sheet-intro">
      Nothing new just now.
    </p>

    <div v-if="fresh.length > 1" class="whats-new__toolbar">
      <UiButton variant="quiet" size="sm" icon="check" @click="dismissAll">
        Dismiss all
      </UiButton>
    </div>

    <div ref="cards">
      <TransitionGroup
        v-if="features.length"
        name="whats-new-entry"
        tag="ul"
        class="whats-new__list"
      >
        <WhatsNewCard
          v-for="(entry, index) in features"
          :key="entry.uuid"
          :entry="entry"
          :style="{ '--i': index }"
          @dismiss="(button) => gotIt(entry, index, button)"
          @follow="follow(entry)"
        />
      </TransitionGroup>

      <section
        v-if="updates.length"
        class="whats-new__updates"
        :class="{ 'is-first': !features.length }"
        aria-labelledby="whats-new-updates-title"
      >
        <h3 id="whats-new-updates-title" class="whats-new__section-title">
          Update to get
        </h3>
        <p class="whats-new__updates-intro">
          {{
            updates.length === 1
              ? 'This comes with the latest version of the app.'
              : 'These come with the latest version of the app.'
          }}
        </p>
        <UiButton
          class="whats-new__store"
          variant="primary"
          icon="download"
          @click="openStore"
        >
          {{ store.label }}
        </UiButton>
        <TransitionGroup
          name="whats-new-entry"
          tag="ul"
          class="whats-new__list"
        >
          <WhatsNewCard
            v-for="(entry, index) in updates"
            :key="entry.uuid"
            :entry="entry"
            update
            :style="{ '--i': features.length + index }"
            @dismiss="(button) => gotIt(entry, features.length + index, button)"
          />
        </TransitionGroup>
      </section>
    </div>

    <section
      v-if="earlier.length"
      class="whats-new__earlier"
      :class="{ 'is-first': !fresh.length }"
    >
      <Ornament
        v-if="!fresh.length"
        glyph="o"
        class="whats-new__caught-up-ornament"
      />
      <h3 ref="earlierTitle" class="whats-new__earlier-title" tabindex="-1">
        {{ fresh.length ? 'Earlier' : 'You’re all caught up' }}
      </h3>
      <ul class="whats-new__list whats-new__list--earlier">
        <li
          v-for="entry in earlier"
          :key="entry.uuid"
          class="whats-new-earlier"
        >
          <h4 class="whats-new-earlier__title">{{ entry.title }}</h4>
          <p class="whats-new-earlier__text">{{ entry.text }}</p>
          <button
            v-if="entry.link || needsUpdate(entry)"
            type="button"
            class="whats-new-earlier__link"
            @click="follow(entry)"
          >
            {{
              needsUpdate(entry)
                ? 'Update to get it'
                : entry.link_text || 'Try it'
            }}
            <span class="visually-hidden">: {{ entry.title }}</span>
            <UiIcon name="arrow-right" />
          </button>
        </li>
      </ul>
    </section>
  </UiSheet>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue';
import { useRouter } from 'vue-router';
import { Browser } from '@capacitor/browser';
import { Capacitor } from '@capacitor/core';
import WhatsNewCard from '@/components/WhatsNewCard.vue';
import { APP_STORE_URLS } from '@/helpers/appStores';
import { panels } from '@/helpers/panels';
import {
  dismissAllWhatsNew,
  dismissWhatsNew,
  earlierWhatsNew,
  needsUpdate,
  newWhatsNew,
  whatsNewState,
} from '@/helpers/whatsNew';

/*
  Every current What's New entry: the new ones first, each dismissed on its
  own ("Got it", or by trying it), then the ones already dismissed. Opening
  the sheet dismisses nothing.

  New features that need a newer app have a section of their own, with one
  link to the store. Updating doesn't dismiss them: once the app has the
  feature, the server stops sending them.
*/
const router = useRouter();
const fresh = newWhatsNew;
const features = computed(() =>
  fresh.value.filter((entry) => !needsUpdate(entry))
);
const updates = computed(() => fresh.value.filter(needsUpdate));
const earlier = earlierWhatsNew;
const cards = ref(null);
const earlierTitle = ref(null);
const announcement = ref('');

const store =
  Capacitor.getPlatform() === 'android'
    ? { url: APP_STORE_URLS.android, label: 'Update on Google Play' }
    : { url: APP_STORE_URLS.ios, label: 'Update in the App Store' };

const subtitle = computed(() => {
  const count = fresh.value.length;
  if (!whatsNewState.entries.length) return '';
  if (count === 0) return 'Nothing unread';
  return count === 1 ? '1 new feature' : `${count} new features`;
});

// The dismissed entry leaves its list, taking the focused button with it,
// so focus goes on to the same button (× or Got it) of the next new entry,
// in either section, or to the "Earlier" heading.
async function gotIt(entry, index, button = '[data-got-it]') {
  dismissWhatsNew(entry);
  announcement.value = `${entry.title} dismissed.`;
  await nextTick();
  const buttons =
    cards.value?.querySelectorAll?.(
      `li:not(.whats-new-entry-leave-active) ${button}`
    ) || [];
  const next = buttons[Math.min(index, buttons.length - 1)];
  (next || earlierTitle.value)?.focus({ preventScroll: false });
}

async function dismissAll() {
  dismissAllWhatsNew();
  announcement.value = 'All dismissed.';
  await nextTick();
  earlierTitle.value?.focus();
}

async function openStore() {
  panels.whatsNew = false;
  await Browser.open({ url: store.url });
}

async function follow(entry) {
  if (needsUpdate(entry)) {
    await openStore();
    return;
  }
  dismissWhatsNew(entry);
  panels.whatsNew = false;
  if (/^(https?:\/\/|mailto:)/i.test(entry.link)) {
    await Browser.open({ url: entry.link });
  } else {
    await router.push(entry.link);
  }
}
</script>

<style scoped>
.whats-new__toolbar {
  display: flex;
  justify-content: flex-end;
  margin: calc(var(--space-2) * -1) 0 var(--space-2);
}

.whats-new__list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  position: relative;
  margin: 0;
  padding: 0;
  list-style: none;
}

/* Features that need the update: a heading, the way to the store, then
   the entries themselves. */
.whats-new__updates {
  margin-top: var(--space-6);
}

.whats-new__updates.is-first {
  margin-top: 0;
}

.whats-new__section-title,
.whats-new__earlier-title {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-sm);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  color: var(--ink-faint);
}

.whats-new__section-title {
  color: var(--accent);
}

.whats-new__section-title::after,
.whats-new__earlier-title::after {
  content: '';
  flex: 1;
  border-top: 1px solid var(--rule);
}

.whats-new__updates-intro {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  line-height: 1.45;
  color: var(--ink-soft);
}

.whats-new__store {
  margin: var(--space-3) 0 var(--space-4);
}

.whats-new__earlier {
  margin-top: var(--space-6);
}

.whats-new__earlier.is-first {
  margin-top: var(--space-2);
  text-align: center;
}

.whats-new__caught-up-ornament {
  display: block;
  margin-bottom: var(--space-2);
  font-size: 1.75rem;
}

.whats-new__earlier-title {
  margin-bottom: var(--space-1);
}

.whats-new__earlier.is-first .whats-new__earlier-title {
  justify-content: center;
  margin-bottom: var(--space-4);
}

.whats-new__earlier.is-first .whats-new__earlier-title::after {
  display: none;
}

.whats-new__list--earlier {
  gap: 0;
  text-align: start;
}

.whats-new-earlier {
  padding: var(--space-3) 0;
}

.whats-new-earlier + .whats-new-earlier {
  border-top: 1px solid var(--rule);
}

.whats-new-earlier__title {
  font-size: var(--text-md);
  font-weight: 400;
  line-height: var(--leading-tight);
  color: var(--ink-soft);
}

.whats-new-earlier__text {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  line-height: 1.5;
  color: var(--ink-faint);
}

.whats-new-earlier__link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  min-height: 2.75rem;
  font-size: var(--text-sm);
  color: var(--accent);
}

.whats-new-earlier__link .ui-icon {
  transition: transform var(--duration) var(--ease);
}

.whats-new-earlier__link:hover .ui-icon {
  transform: translateX(3px);
}
</style>
