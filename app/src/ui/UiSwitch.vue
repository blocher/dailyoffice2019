<template>
  <button
    type="button"
    role="switch"
    class="ui-switch"
    :class="{ 'is-on': modelValue }"
    :aria-checked="modelValue ? 'true' : 'false'"
    :aria-label="label || null"
    :disabled="disabled"
    @click="$emit('update:modelValue', !modelValue)"
  >
    <span class="ui-switch__thumb" aria-hidden="true" />
  </button>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  label: { type: String, default: null },
  disabled: { type: Boolean, default: false },
});
defineEmits(['update:modelValue']);
</script>

<style scoped>
.ui-switch {
  position: relative;
  flex-shrink: 0;
  width: 2.75rem;
  height: 1.625rem;
  border-radius: var(--radius-pill);
  background-color: var(--rule-strong);
  transition: background-color var(--duration) var(--ease);
}

.ui-switch.is-on {
  background-color: var(--accent);
}

.ui-switch:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.ui-switch:disabled {
  opacity: 0.5;
}

.ui-switch__thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  background-color: var(--paper-raised);
  box-shadow: var(--shadow-sm);
  transition: transform var(--duration) var(--ease);
}

.ui-switch.is-on .ui-switch__thumb {
  transform: translateX(1.125rem);
}
</style>
