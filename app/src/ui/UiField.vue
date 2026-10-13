<template>
  <div class="ui-field" :class="{ 'has-error': error }">
    <label v-if="label" :for="forId" class="ui-field__label">
      {{ label }}
      <span v-if="optional" class="ui-field__optional">optional</span>
    </label>
    <slot />
    <p v-if="error" class="ui-field__error">{{ error }}</p>
    <p v-else-if="hint" class="ui-field__hint">{{ hint }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, default: '' },
  forId: { type: String, default: null },
  hint: { type: String, default: '' },
  error: { type: String, default: '' },
  optional: { type: Boolean, default: false },
});
</script>

<style scoped>
.ui-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  text-align: left;
}

.ui-field__label {
  font-size: var(--text-sm);
  color: var(--ink);
}

.ui-field__optional {
  margin-left: 0.35em;
  font-style: italic;
  color: var(--ink-faint);
}

.ui-field__hint {
  font-size: var(--text-xs);
  color: var(--ink-faint);
  font-style: italic;
}

.ui-field__error {
  font-size: var(--text-xs);
  color: var(--tone-danger);
}

.has-error :deep(.ui-control) {
  border-color: var(--tone-danger);
}
</style>
