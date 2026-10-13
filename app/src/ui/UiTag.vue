<template>
  <span class="ui-tag" :class="`ui-tag--${tone}`"><slot /></span>
</template>

<script setup>
defineProps({
  /** neutral | accent | info | success | warning | error */
  tone: { type: String, default: 'neutral' },
});
</script>

<style scoped>
.ui-tag {
  --tone: var(--ink-soft);
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  padding: 0.1rem 0.55rem 0.05rem;
  border: 1px solid color-mix(in srgb, var(--tone) 35%, var(--rule));
  border-radius: var(--radius-pill);
  background-color: color-mix(in srgb, var(--tone) 8%, var(--paper));
  color: var(--tone);
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  line-height: 1.5;
  white-space: nowrap;
}

.ui-tag--accent {
  --tone: var(--accent);
}

.ui-tag--info {
  --tone: var(--tone-info);
}

.ui-tag--success {
  --tone: var(--tone-success);
}

.ui-tag--warning {
  --tone: var(--tone-warning);
}

.ui-tag--error {
  --tone: var(--tone-danger);
}
</style>
