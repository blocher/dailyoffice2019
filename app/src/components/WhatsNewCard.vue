<template>
  <li class="whats-new-entry" :class="{ 'is-update': update }">
    <button
      type="button"
      class="whats-new-entry__dismiss"
      :aria-label="`Dismiss: ${entry.title}`"
      data-dismiss
      @click="$emit('dismiss', '[data-dismiss]')"
    >
      <UiIcon name="close" />
    </button>
    <p class="whats-new-entry__new" aria-hidden="true">
      {{ update ? 'Needs the update' : 'New' }}
    </p>
    <h3 class="whats-new-entry__title">{{ entry.title }}</h3>
    <p class="whats-new-entry__text">{{ entry.text }}</p>
    <UiButton
      v-if="entry.link && !update"
      class="whats-new-entry__try"
      size="sm"
      variant="primary"
      icon-right="arrow-right"
      @click="$emit('follow')"
    >
      {{ entry.link_text || 'Try it' }}
      <span class="visually-hidden">: {{ entry.title }}</span>
    </UiButton>
    <div class="whats-new-entry__footer">
      <button
        type="button"
        class="whats-new-entry__got-it"
        data-got-it
        @click="$emit('dismiss', '[data-got-it]')"
      >
        <UiIcon name="check" />
        <span class="whats-new-entry__got-it-label">
          Got it
          <span class="visually-hidden">: {{ entry.title }}</span>
        </span>
      </button>
    </div>
  </li>
</template>

<script setup>
/*
  One new entry in the What's New sheet: what it is and how to try it, with
  the ways to put it away (× and Got it) kept apart from the way in. An
  entry that needs the update has no way in of its own; its section links
  to the store.
*/
defineProps({
  entry: { type: Object, required: true },
  update: { type: Boolean, default: false },
});

defineEmits(['dismiss', 'follow']);
</script>

<style scoped>
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

/* Not yet in this version: plainer paper, and an open lozenge. */
.whats-new-entry.is-update {
  border-color: var(--rule-strong);
  background-image: none;
  background-color: var(--paper-raised);
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

.is-update .whats-new-entry__new::before {
  background-color: transparent;
  box-shadow: inset 0 0 0 1px var(--accent);
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
