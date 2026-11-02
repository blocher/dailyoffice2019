<template>
  <Transition name="whats-new-banner" appear>
    <section
      v-if="entries.length"
      class="whats-new-banner"
      :class="{ 'is-many': entries.length > 3 }"
      aria-labelledby="whats-new-banner-label"
    >
      <span class="whats-new-banner__shine" aria-hidden="true" />
      <span class="whats-new-banner__seal" aria-hidden="true">
        <span class="whats-new-banner__count">{{ entries.length }}</span>
      </span>
      <div class="whats-new-banner__copy">
        <p id="whats-new-banner-label" class="whats-new-banner__label">
          What’s new
          <span class="visually-hidden">: {{ countLabel }}</span>
        </p>
        <ul class="whats-new-banner__titles">
          <li
            v-for="(entry, index) in named.shown"
            :key="entry.uuid"
            class="whats-new-banner__title"
            :class="{
              'is-wide-only': index >= namedOnPhone.shown.length,
              'is-update': needsUpdate(entry),
            }"
            :style="{ '--i': index }"
          >
            {{ entry.title || entry.text }}
            <span v-if="needsUpdate(entry)" class="visually-hidden">
              (needs an update)
            </span>
          </li>
          <li
            v-if="named.more"
            class="whats-new-banner__title is-more is-wide-only"
            :style="{ '--i': named.shown.length }"
          >
            and {{ named.more }} more
          </li>
          <li
            v-if="namedOnPhone.more"
            class="whats-new-banner__title is-more is-phone-only"
            :style="{ '--i': namedOnPhone.shown.length }"
          >
            and {{ namedOnPhone.more }} more
          </li>
        </ul>
      </div>
      <button
        type="button"
        class="whats-new-banner__open"
        @click="openPanel('whatsNew')"
      >
        <span class="whats-new-banner__open-label">See what’s new</span>
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
  nameForBanner,
  needsUpdate,
  newWhatsNew,
} from '@/helpers/whatsNew';

/*
  One banner for every new feature: how many there are, their names, and a
  way into the What's New sheet. The × dismisses them all; the sheet
  dismisses them one at a time.

  It arrives with a little ceremony, once: the count settles in, a light
  passes over, and the names follow one by one.
*/
const entries = newWhatsNew;
// Six names where there's room for columns of them; on phones, where they
// stack, three lines at most, so the banner doesn't push the office away.
const named = computed(() => nameForBanner(entries.value, 6));
const namedOnPhone = computed(() => nameForBanner(entries.value, 3));
const countLabel = computed(() =>
  entries.value.length === 1
    ? '1 new feature'
    : `${entries.value.length} new features`
);
</script>

<style scoped>
.whats-new-banner {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto;
  grid-template-areas: 'seal copy open close';
  align-items: center;
  column-gap: var(--space-4);
  padding: var(--space-3) var(--space-2) var(--space-3) var(--space-4);
  border: 1px solid var(--accent-rule);
  border-radius: var(--radius-lg);
  background-image: linear-gradient(
    100deg,
    color-mix(in srgb, var(--accent) 11%, var(--paper-raised)) 0%,
    color-mix(in srgb, var(--accent) 4%, var(--paper-raised)) 40%,
    var(--paper-raised) 100%
  );
}

/* A band of light that crosses the banner once, as it arrives. */
.whats-new-banner__shine {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  overflow: hidden;
  pointer-events: none;
}

.whats-new-banner__shine::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 40%;
  background-image: linear-gradient(
    100deg,
    transparent,
    color-mix(in srgb, var(--accent) 14%, transparent),
    transparent
  );
  transform: translateX(-100%);
  animation: whats-new-shine 1600ms var(--ease) 350ms 1 both;
}

@keyframes whats-new-shine {
  to {
    transform: translateX(260%);
  }
}

.whats-new-banner__seal {
  grid-area: seal;
  position: relative;
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 50%;
  background-color: var(--accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--accent) 16%, transparent);
  animation: whats-new-seal 520ms cubic-bezier(0.34, 1.5, 0.64, 1) both;
}

/* Two soft ripples go out from the count, then it rests. */
.whats-new-banner__seal::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid var(--accent);
  opacity: 0;
  animation: whats-new-ripple 1500ms var(--ease) 500ms 2;
}

@keyframes whats-new-seal {
  from {
    transform: scale(0.55);
    opacity: 0;
  }
}

@keyframes whats-new-ripple {
  from {
    transform: scale(1);
    opacity: 0.55;
  }
  to {
    transform: scale(1.9);
    opacity: 0;
  }
}

/* Caslon's figures ride about 0.2em above the middle of their line box. */
.whats-new-banner__count {
  position: relative;
  top: 0.19em;
  color: var(--on-accent);
  font-size: var(--text-md);
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
  letter-spacing: 0.14em;
  color: var(--accent);
  line-height: 1.3;
}

.whats-new-banner__titles {
  display: flex;
  flex-wrap: wrap;
  column-gap: var(--space-4);
  row-gap: 0.1rem;
  margin: 0.1rem 0 0;
  padding: 0;
  list-style: none;
}

/* Beyond phones, a long list lines up in columns, as many as fit, rather
   than running on. */
@media (min-width: 560px) {
  .whats-new-banner.is-many .whats-new-banner__titles {
    display: grid;
    grid-template-columns: repeat(auto-fill, min(100%, 12.5rem));
    column-gap: var(--space-5);
  }
}

.whats-new-banner__title {
  display: flex;
  align-items: baseline;
  gap: 0.5em;
  font-size: var(--text-md);
  line-height: 1.35;
  color: var(--ink);
  overflow-wrap: anywhere;
  animation: whats-new-rise 480ms var(--ease) both;
  animation-delay: calc(260ms + var(--i, 0) * 110ms);
}

/* A small lozenge before each name, so they read as a list. */
.whats-new-banner__title::before {
  content: '';
  flex-shrink: 0;
  width: 0.36em;
  height: 0.36em;
  background-color: var(--accent);
  transform: translateY(-0.12em) rotate(45deg);
}

/* A feature that needs an update: an open lozenge, as in the sheet. */
.whats-new-banner__title.is-update::before {
  background-color: transparent;
  box-shadow: inset 0 0 0 1px var(--accent);
}

.whats-new-banner__title.is-more {
  color: var(--ink-faint);
  font-style: italic;
}

/* In columns, "and 2 more" lines up with the names, not their lozenges. */
.whats-new-banner.is-many .whats-new-banner__title.is-more {
  padding-left: 0.86em;
}

.whats-new-banner__title.is-more::before {
  display: none;
}

@keyframes whats-new-rise {
  from {
    opacity: 0;
    transform: translateY(5px);
  }
}

.whats-new-banner__open {
  grid-area: open;
  display: inline-flex;
  align-items: center;
  gap: 0.4em;
  min-height: 2.75rem;
  padding: 0 var(--space-4);
  border: 1px solid color-mix(in srgb, var(--accent) 45%, transparent);
  border-radius: var(--radius-pill);
  background-color: color-mix(in srgb, var(--accent) 8%, transparent);
  color: var(--accent);
  font-size: var(--text-sm);
  line-height: 1;
  white-space: nowrap;
  transition:
    background-color var(--duration) var(--ease),
    border-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}

/* Lowercase sits a little above the middle of the line box. */
.whats-new-banner__open-label {
  position: relative;
  top: 0.1em;
}

.whats-new-banner__open:hover {
  border-color: var(--accent);
  background-color: var(--accent);
  color: var(--on-accent);
}

.whats-new-banner__open:focus-visible,
.whats-new-banner__close:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.whats-new-banner__arrow {
  transition: transform var(--duration) var(--ease);
}

.whats-new-banner__open:hover .whats-new-banner__arrow {
  transform: translateX(3px);
}

.whats-new-banner__close {
  grid-area: close;
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

.whats-new-banner__close:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

/* Phones, and a long list anywhere: the button gets its own line under the
   names, so the names have the banner's full width. */
.whats-new-banner.is-many {
  grid-template-columns: auto minmax(0, 1fr) auto;
  grid-template-areas:
    'seal copy close'
    '. open open';
  align-items: start;
  row-gap: var(--space-3);
  padding-bottom: var(--space-4);
}

.whats-new-banner.is-many .whats-new-banner__seal {
  margin-top: 0.15rem;
}

.whats-new-banner.is-many .whats-new-banner__close {
  margin-top: -0.25rem;
}

.whats-new-banner.is-many .whats-new-banner__open {
  justify-self: start;
}

@media (max-width: 559px) {
  .whats-new-banner {
    grid-template-columns: auto minmax(0, 1fr) auto;
    grid-template-areas:
      'seal copy close'
      '. open open';
    align-items: start;
    column-gap: var(--space-3);
    row-gap: var(--space-3);
    padding: var(--space-3) var(--space-1) var(--space-4) var(--space-3);
  }

  .whats-new-banner__seal {
    margin-top: 0.15rem;
  }

  .whats-new-banner__close {
    margin: -0.25rem 0 0;
  }

  .whats-new-banner__open {
    justify-self: start;
  }

  .whats-new-banner__title.is-wide-only {
    display: none;
  }
}

@media (min-width: 560px) {
  .whats-new-banner__title.is-phone-only {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .whats-new-banner__shine::before,
  .whats-new-banner__seal,
  .whats-new-banner__seal::after,
  .whats-new-banner__title {
    animation: none;
  }
}

.whats-new-banner-enter-active,
.whats-new-banner-leave-active {
  transition:
    opacity 260ms var(--ease),
    transform 260ms var(--ease);
}

.whats-new-banner-enter-from,
.whats-new-banner-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
