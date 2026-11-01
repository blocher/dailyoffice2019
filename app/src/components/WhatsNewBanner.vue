<template>
  <Transition name="whats-new-banner" appear>
    <section
      v-if="entries.length"
      class="whats-new-banner"
      aria-labelledby="whats-new-banner-label"
    >
      <span class="whats-new-banner__count" aria-hidden="true">
        {{ entries.length }}
      </span>
      <div class="whats-new-banner__copy">
        <p id="whats-new-banner-label" class="whats-new-banner__label">
          What’s new
          <span class="visually-hidden">: {{ countLabel }}</span>
        </p>
        <p class="whats-new-banner__titles">{{ summary }}</p>
      </div>
      <button
        type="button"
        class="whats-new-banner__open"
        @click="openPanel('whatsNew')"
      >
        <span>See what’s new</span>
        <UiIcon name="arrow-right" class="whats-new-banner__arrow" />
      </button>
      <button
        type="button"
        class="whats-new-banner__close"
        :aria-label="entries.length > 1 ? 'Dismiss all' : 'Dismiss'"
        @click="dismissAllWhatsNew"
      >
        <UiIcon name="close" />
      </button>
    </section>
  </Transition>
</template>

<script setup>
import { computed } from 'vue';
import { openPanel } from '@/helpers/panels';
import {
  dismissAllWhatsNew,
  newWhatsNew,
  summarizeTitles,
} from '@/helpers/whatsNew';

/*
  One banner for every new feature: how many there are, their names, and a
  way into the What's New sheet. The × dismisses them all; the sheet
  dismisses them one at a time.
*/
const entries = newWhatsNew;
const summary = computed(() => summarizeTitles(entries.value));
const countLabel = computed(() =>
  entries.value.length === 1
    ? '1 new feature'
    : `${entries.value.length} new features`
);
</script>

<style scoped>
.whats-new-banner {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  grid-template-areas: 'count copy open close';
  align-items: center;
  column-gap: var(--space-3);
  padding: var(--space-2) var(--space-2) var(--space-2) var(--space-3);
  border: 1px solid color-mix(in srgb, var(--accent) 30%, var(--rule));
  border-radius: var(--radius);
  background-color: color-mix(in srgb, var(--accent) 5%, var(--paper-raised));
}

.whats-new-banner__count {
  grid-area: count;
  display: grid;
  place-items: center;
  min-width: 1.9rem;
  height: 1.9rem;
  padding: 0 0.45rem;
  border-radius: var(--radius-pill);
  background-color: var(--accent);
  color: var(--on-accent);
  font-size: var(--text-sm);
  font-variant-numeric: lining-nums tabular-nums;
  line-height: 1;
}

.whats-new-banner__copy {
  grid-area: copy;
  min-width: 0;
}

.whats-new-banner__label {
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--accent);
  line-height: 1.3;
}

.whats-new-banner__titles {
  font-size: var(--text-sm);
  line-height: 1.35;
  color: var(--ink);
  overflow-wrap: break-word;
}

.whats-new-banner__open {
  grid-area: open;
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  min-height: 2.75rem;
  padding: 0 var(--space-3);
  border: 1px solid color-mix(in srgb, var(--accent) 40%, var(--rule));
  border-radius: var(--radius-pill);
  background-color: var(--paper);
  color: var(--accent);
  font-size: var(--text-sm);
  white-space: nowrap;
  transition:
    background-color 150ms var(--ease),
    border-color 150ms var(--ease);
}

.whats-new-banner__open:hover {
  border-color: var(--accent);
  background-color: color-mix(in srgb, var(--accent) 8%, var(--paper));
}

.whats-new-banner__arrow {
  transition: transform 150ms var(--ease);
}

.whats-new-banner__open:hover .whats-new-banner__arrow {
  transform: translateX(2px);
}

.whats-new-banner__close {
  grid-area: close;
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  color: var(--ink-faint);
}

.whats-new-banner__close:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

/* Phones: the button gets its own line under the names. */
@media (max-width: 559px) {
  .whats-new-banner {
    grid-template-columns: auto minmax(0, 1fr) auto;
    grid-template-areas:
      'count copy close'
      '. open open';
    row-gap: var(--space-1);
    padding-bottom: var(--space-3);
  }

  .whats-new-banner__open {
    justify-self: start;
  }
}

.whats-new-banner-enter-active,
.whats-new-banner-leave-active {
  transition:
    opacity 220ms var(--ease),
    transform 220ms var(--ease);
}

.whats-new-banner-enter-from,
.whats-new-banner-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
