<template>
  <component
    :is="tag"
    v-bind="linkAttrs"
    class="ui-button"
    :class="[
      `ui-button--${variant}`,
      `ui-button--${size}`,
      {
        'ui-button--block': block,
        'ui-button--icon-only': iconOnly,
        'is-loading': loading,
      },
    ]"
    :aria-busy="loading || undefined"
  >
    <UiIcon v-if="icon" :name="icon" class="ui-button__icon" />
    <span v-if="$slots.default" class="ui-button__label"><slot /></span>
    <UiIcon v-if="iconRight" :name="iconRight" class="ui-button__icon" />
  </component>
</template>

<script setup>
import { computed, useSlots } from 'vue';
import UiIcon from './UiIcon.vue';

const props = defineProps({
  /** primary | secondary | ghost | quiet | danger */
  variant: { type: String, default: 'secondary' },
  /** sm | md | lg */
  size: { type: String, default: 'md' },
  /** icon name from iconData.js */
  icon: { type: String, default: null },
  iconRight: { type: String, default: null },
  to: { type: [String, Object], default: null },
  href: { type: String, default: null },
  target: { type: String, default: null },
  type: { type: String, default: 'button' },
  block: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
});

const slots = useSlots();

const tag = computed(() => {
  if (props.to) return 'router-link';
  if (props.href) return 'a';
  return 'button';
});

const iconOnly = computed(
  () => !slots.default && (props.icon || props.iconRight)
);

const linkAttrs = computed(() => {
  if (props.to) return { to: props.to };
  if (props.href) {
    return {
      href: props.href,
      target: props.target,
      rel: props.target === '_blank' ? 'noopener noreferrer' : null,
    };
  }
  return { type: props.type, disabled: props.disabled || props.loading };
});
</script>

<style scoped>
.ui-button {
  --btn-bg: transparent;
  --btn-ink: var(--ink);
  --btn-border: transparent;
  --btn-hover-bg: var(--paper-sunken);

  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5em;
  min-height: 2.5rem;
  padding: 0.45rem 1rem;
  border: 1px solid var(--btn-border);
  border-radius: var(--radius);
  background-color: var(--btn-bg);
  color: var(--btn-ink);
  font-family: var(--font-book);
  font-size: var(--text-md);
  line-height: 1.1;
  text-decoration: none;
  white-space: nowrap;
  transition:
    background-color var(--duration) var(--ease),
    border-color var(--duration) var(--ease),
    color var(--duration) var(--ease),
    filter var(--duration) var(--ease);
}

.ui-button:hover:not(:disabled) {
  background-color: var(--btn-hover-bg);
}

.ui-button:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.ui-button:disabled {
  opacity: 0.5;
}

.ui-button__icon {
  flex-shrink: 0;
  font-size: 0.95em;
}

.ui-button__label {
  padding-top: 0.08em;
}

.is-loading {
  opacity: 0.7;
  cursor: progress;
}

/* Variants */
.ui-button--primary {
  --btn-bg: var(--accent);
  --btn-ink: var(--on-accent);
  --btn-border: var(--accent);
  --btn-hover-bg: var(--accent);
}

.ui-button--primary:hover:not(:disabled) {
  filter: brightness(1.08) saturate(1.05);
}

.ui-button--secondary {
  --btn-bg: var(--paper-raised);
  --btn-border: var(--rule-strong);
}

.ui-button--secondary:hover:not(:disabled) {
  border-color: var(--ink-faint);
}

.ui-button--ghost {
  --btn-ink: var(--ink-soft);
}

.ui-button--ghost:hover:not(:disabled) {
  color: var(--ink);
}

.ui-button--quiet {
  --btn-ink: var(--accent);
  --btn-hover-bg: var(--accent-wash);
}

.ui-button--danger {
  --btn-ink: var(--tone-danger);
  --btn-border: color-mix(in srgb, var(--tone-danger) 45%, var(--rule));
  --btn-hover-bg: color-mix(in srgb, var(--tone-danger) 8%, var(--paper));
}

/* Sizes */
.ui-button--sm {
  min-height: 2.125rem;
  padding: 0.3rem 0.7rem;
  font-size: var(--text-sm);
}

.ui-button--lg {
  min-height: 3rem;
  padding: 0.6rem 1.35rem;
  font-size: var(--text-lg);
}

.ui-button--block {
  display: flex;
  width: 100%;
}

.ui-button--icon-only {
  padding: 0;
  width: 2.5rem;
}

.ui-button--icon-only.ui-button--sm {
  width: 2.125rem;
}

.ui-button--icon-only.ui-button--lg {
  width: 3rem;
}
</style>
