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
        class="whats-new-entry surface"
      >
        <div class="whats-new-entry__head">
          <h3 class="whats-new-entry__title">{{ entry.title }}</h3>
          <UiTag tone="accent" aria-hidden="true">New</UiTag>
        </div>
        <p class="whats-new-entry__text">{{ entry.text }}</p>
        <div class="whats-new-entry__actions">
          <UiButton
            v-if="entry.link"
            size="sm"
            variant="primary"
            icon-right="arrow-right"
            @click="follow(entry)"
          >
            {{ entry.link_text || 'Try it' }}
            <span class="visually-hidden">: {{ entry.title }}</span>
          </UiButton>
          <UiButton
            size="sm"
            variant="ghost"
            icon="check"
            data-got-it
            @click="gotIt(entry, index)"
          >
            Got it
            <span class="visually-hidden">: {{ entry.title }}</span>
          </UiButton>
        </div>
      </li>
    </TransitionGroup>

    <section
      v-if="earlier.length"
      class="whats-new__earlier"
      :class="{ 'is-first': !fresh.length }"
    >
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
// so focus goes on to the next new entry, or to the "Earlier" heading.
async function gotIt(entry, index) {
  dismissWhatsNew(entry);
  announcement.value = `${entry.title} dismissed.`;
  await nextTick();
  const buttons =
    list.value?.$el?.querySelectorAll?.(
      'li:not(.whats-new-entry-leave-active) [data-got-it]'
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

.whats-new-entry {
  padding: var(--space-4);
}

.whats-new-entry__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
}

.whats-new-entry__title {
  font-size: var(--text-md);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink);
}

.whats-new-entry__text {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  line-height: 1.45;
  color: var(--ink-soft);
}

.whats-new-entry__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.whats-new__earlier {
  margin-top: var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--rule);
}

.whats-new__earlier.is-first {
  margin-top: 0;
  padding-top: 0;
  border-top: 0;
}

.whats-new__earlier-title {
  margin-bottom: var(--space-2);
  font-size: var(--text-sm);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  color: var(--ink-faint);
}

.whats-new-entry--earlier {
  padding: var(--space-2) 0;
}

.whats-new-entry--earlier .whats-new-entry__title {
  font-size: var(--text-sm);
  color: var(--ink-soft);
}

.whats-new-entry__link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  min-height: 2.75rem;
  font-size: var(--text-sm);
  color: var(--accent);
}

.whats-new-entry-enter-active,
.whats-new-entry-leave-active {
  transition:
    opacity 200ms var(--ease),
    transform 200ms var(--ease);
}

.whats-new-entry-leave-active {
  position: absolute;
  left: 0;
  right: 0;
}

.whats-new-entry-move {
  transition: transform 220ms var(--ease);
}

.whats-new-entry-enter-from,
.whats-new-entry-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
</style>
