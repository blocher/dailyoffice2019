<template>
  <div
    v-if="visible"
    class="ui-alert"
    :class="`ui-alert--${tone}`"
    :role="tone === 'error' ? 'alert' : 'status'"
  >
    <UiIcon :name="icon" class="ui-alert__icon" />
    <div class="ui-alert__copy">
      <p v-if="title" class="ui-alert__title">{{ title }}</p>
      <div v-if="$slots.default" class="ui-alert__body"><slot /></div>
    </div>
    <button
      v-if="closable"
      type="button"
      class="ui-alert__close"
      aria-label="Dismiss"
      @click="dismiss"
    >
      <UiIcon name="close" />
    </button>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import UiIcon from './UiIcon.vue';

const props = defineProps({
  /** info | success | warning | error */
  tone: { type: String, default: 'info' },
  title: { type: String, default: '' },
  closable: { type: Boolean, default: false },
});
const emit = defineEmits(['close']);
const visible = ref(true);

const ICONS = {
  info: 'info',
  success: 'check-circle',
  warning: 'warning',
  error: 'error',
};
const icon = computed(() => ICONS[props.tone] || ICONS.info);

function dismiss() {
  visible.value = false;
  emit('close');
}
</script>

<style scoped>
.ui-alert {
  --tone: var(--tone-info);
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1px solid color-mix(in srgb, var(--tone) 30%, var(--rule));
  border-radius: var(--radius);
  background-color: color-mix(in srgb, var(--tone) 7%, var(--paper));
  color: var(--ink);
  font-size: var(--text-sm);
  line-height: 1.4;
  text-align: left;
}

.ui-alert--success {
  --tone: var(--tone-success);
}

.ui-alert--warning {
  --tone: var(--tone-warning);
}

.ui-alert--error {
  --tone: var(--tone-danger);
}

.ui-alert__icon {
  margin-top: 0.2rem;
  color: var(--tone);
}

.ui-alert__copy {
  flex: 1;
  min-width: 0;
}

.ui-alert__title {
  font-weight: 600;
}

.ui-alert__body {
  color: var(--ink-soft);
}

.ui-alert__title + .ui-alert__body {
  margin-top: var(--space-1);
}

.ui-alert__close {
  display: grid;
  place-items: center;
  width: 1.75rem;
  height: 1.75rem;
  margin: -0.15rem -0.4rem 0 0;
  border-radius: 50%;
  color: var(--ink-faint);
}

.ui-alert__close:hover {
  color: var(--ink);
  background-color: var(--paper-sunken);
}
</style>
