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

    <TransitionGroup
      v-if="fresh.length"
      ref="list"
      name="whats-new-entry"
      tag="ul"
      class="whats-new__list"
    >
      <li
        v-for="(entry, index) in fresh"
        :key="entry.uuid"
        class="whats-new-entry"
        :style="{ '--i': index }"
      >
        <button
          type="button"
          class="whats-new-entry__dismiss"
          :aria-label="`Dismiss: ${entry.title}`"
          data-dismiss
          @click="gotIt(entry, index, '[data-dismiss]')"
        >
          <UiIcon name="close" />
        </button>
        <p class="whats-new-entry__new" aria-hidden="true">New</p>
        <h3 class="whats-new-entry__title">{{ entry.title }}</h3>
        <p class="whats-new-entry__text">{{ entry.text }}</p>
        <UiButton
          v-if="entry.link"
          class="whats-new-entry__try"
          size="sm"
          variant="primary"
          icon-right="arrow-right"
          @click="follow(entry)"
        >
          {{ entry.link_text || 'Try it' }}
          <span class="visually-hidden">: {{ entry.title }}</span>
        </UiButton>
        <div class="whats-new-entry__footer">
          <button
            type="button"
            class="whats-new-entry__got-it"
            data-got-it
            @click="gotIt(entry, index, '[data-got-it]')"
          >
            <UiIcon name="check" />
            <span class="whats-new-entry__got-it-label">
              Got it
              <span class="visually-hidden">: {{ entry.title }}</span>
            </span>
          </button>
        </div>
      </li>
    </TransitionGroup>

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
      <ul class="whats-new__list">
        <li
          v-for="entry in earlier"
          :key="entry.uuid"
          class="whats-new-entry whats-new-entry--earlier"
        >
          <h4 class="whats-new-entry__title">{{ entry.title }}</h4>
          <p class="whats-new-entry__text">{{ entry.text }}</p>
          <button
            v-if="entry.link"
            type="button"
            class="whats-new-entry__link"
            @click="follow(entry)"
          >
            {{ entry.link_text || 'Try it' }}
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
import { panels } from '@/helpers/panels';
import {
  dismissAllWhatsNew,
  dismissWhatsNew,
  earlierWhatsNew,
  newWhatsNew,
  whatsNewState,
} from '@/helpers/whatsNew';

/*
  Every current What's New entry: the new ones first, each dismissed on its
  own ("Got it", or by trying it), then the ones already dismissed. Opening
  the sheet dismisses nothing.
*/
const router = useRouter();
const fresh = newWhatsNew;
const earlier = earlierWhatsNew;
const list = ref(null);
const earlierTitle = ref(null);
const announcement = ref('');

const subtitle = computed(() => {
  const count = fresh.value.length;
  if (!whatsNewState.entries.length) return '';
  if (count === 0) return 'Nothing unread';
  return count === 1 ? '1 new feature' : `${count} new features`;
});

// The dismissed entry leaves the list, taking the focused button with it,
// so focus goes on to the same button (× or Got it) of the next new entry,
// or to the "Earlier" heading.
async function gotIt(entry, index, button = '[data-got-it]') {
  dismissWhatsNew(entry);
  announcement.value = `${entry.title} dismissed.`;
  await nextTick();
  const buttons =
    list.value?.$el?.querySelectorAll?.(
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

async function follow(entry) {
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

/*
  A new entry: what it is and how to try it, with the ways to put it away
  (× and Got it) kept apart from the way in.
*/
.whats-new-entry {
  position: relative;
  padding: var(--space-4) var(--space-4) 0;
  border: 1px solid var(--accent-rule);
  border-radius: var(--radius-lg);
  background-image: linear-gradient(
    170deg,
    color-mix(in srgb, var(--accent) 9%, var(--paper-raised)) 0%,
    var(--paper-raised) 55%
  );
  animation: whats-new-card 420ms var(--ease) both;
  animation-delay: calc(120ms + var(--i, 0) * 80ms);
}

@keyframes whats-new-card {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
}

.whats-new-entry__dismiss {
  position: absolute;
  top: var(--space-1);
  right: var(--space-1);
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  color: var(--ink-faint);
  transition:
    background-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}

.whats-new-entry__dismiss:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

.whats-new-entry__new {
  display: flex;
  align-items: center;
  gap: 0.5em;
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  line-height: 1.3;
  color: var(--accent);
}

.whats-new-entry__new::before {
  content: '';
  width: 0.4em;
  height: 0.4em;
  background-color: var(--accent);
  transform: rotate(45deg);
}

.whats-new-entry__title {
  margin-top: 0.15rem;
  padding-right: var(--space-6);
  font-size: var(--text-lg);
  font-weight: 400;
  line-height: var(--leading-tight);
  color: var(--ink);
}

.whats-new-entry__text {
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  line-height: 1.5;
  color: var(--ink-soft);
}

.whats-new-entry__try {
  margin-top: var(--space-4);
}

.whats-new-entry__try :deep(.ui-button__icon:last-child) {
  transition: transform var(--duration) var(--ease);
}

.whats-new-entry__try:hover :deep(.ui-button__icon:last-child) {
  transform: translateX(3px);
}

.whats-new-entry__footer {
  display: flex;
  justify-content: flex-end;
  margin: var(--space-4) calc(var(--space-4) * -1) 0;
  padding: var(--space-1) var(--space-2);
  border-top: 1px solid var(--rule);
}

.whats-new-entry__got-it {
  display: inline-flex;
  align-items: center;
  gap: 0.4em;
  min-height: 2.5rem;
  padding: 0 var(--space-3);
  border-radius: var(--radius-pill);
  color: var(--ink-faint);
  font-size: var(--text-sm);
  line-height: 1;
  transition:
    background-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}

.whats-new-entry__got-it-label {
  position: relative;
  top: 0.1em;
}

.whats-new-entry__got-it:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

.whats-new-entry__dismiss:focus-visible,
.whats-new-entry__got-it:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

@media (pointer: coarse) {
  .whats-new-entry__got-it {
    min-height: 2.75rem;
  }
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
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-1);
  font-size: var(--text-sm);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  color: var(--ink-faint);
}

.whats-new__earlier-title::after {
  content: '';
  flex: 1;
  border-top: 1px solid var(--rule);
}

.whats-new__earlier.is-first .whats-new__earlier-title {
  justify-content: center;
  margin-bottom: var(--space-4);
}

.whats-new__earlier.is-first .whats-new__earlier-title::after {
  display: none;
}

.whats-new__earlier.is-first .whats-new__list {
  text-align: start;
}

.whats-new-entry--earlier {
  padding: var(--space-3) 0;
  border: 0;
  border-radius: 0;
  background: none;
  animation: none;
}

.whats-new-entry--earlier + .whats-new-entry--earlier {
  border-top: 1px solid var(--rule);
}

.whats-new__earlier .whats-new__list {
  gap: 0;
}

.whats-new-entry--earlier .whats-new-entry__title {
  padding-right: 0;
  font-size: var(--text-md);
  color: var(--ink-soft);
}

.whats-new-entry--earlier .whats-new-entry__text {
  margin-top: var(--space-1);
  color: var(--ink-faint);
}

.whats-new-entry__link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  min-height: 2.75rem;
  font-size: var(--text-sm);
  color: var(--accent);
}

.whats-new-entry__link .ui-icon {
  transition: transform var(--duration) var(--ease);
}

.whats-new-entry__link:hover .ui-icon {
  transform: translateX(3px);
}

@media (prefers-reduced-motion: reduce) {
  .whats-new-entry {
    animation: none;
  }
}

.whats-new-entry-enter-active,
.whats-new-entry-leave-active {
  transition:
    opacity 240ms var(--ease),
    transform 240ms var(--ease);
}

.whats-new-entry-leave-active {
  position: absolute;
  left: 0;
  right: 0;
}

.whats-new-entry-move {
  transition: transform 280ms var(--ease);
}

.whats-new-entry-enter-from,
.whats-new-entry-leave-to {
  opacity: 0;
  transform: translateX(16px) scale(0.98);
}
</style>
