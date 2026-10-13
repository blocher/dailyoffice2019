<template>
  <div class="ui-input" :class="{ 'has-icon': icon, 'has-clear': showClear }">
    <UiIcon v-if="icon" :name="icon" class="ui-input__icon" />
    <textarea
      v-if="multiline"
      :id="id"
      class="ui-control"
      :value="modelValue"
      :placeholder="placeholder"
      :rows="rows"
      :disabled="disabled"
      v-bind="$attrs"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <input
      v-else
      :id="id"
      class="ui-control"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      v-bind="$attrs"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <button
      v-if="showClear"
      type="button"
      class="ui-input__clear"
      aria-label="Clear"
      @click="$emit('update:modelValue', '')"
    >
      <UiIcon name="close" />
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import UiIcon from './UiIcon.vue';

defineOptions({ inheritAttrs: false });

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  id: { type: String, default: null },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  icon: { type: String, default: null },
  clearable: { type: Boolean, default: false },
  multiline: { type: Boolean, default: false },
  rows: { type: Number, default: 4 },
  disabled: { type: Boolean, default: false },
});
defineEmits(['update:modelValue']);

const showClear = computed(
  () => props.clearable && !props.multiline && String(props.modelValue ?? '')
);
</script>

<style scoped>
.ui-input {
  position: relative;
  width: 100%;
}

.ui-input__icon {
  position: absolute;
  left: 0.85rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ink-faint);
  pointer-events: none;
}

.has-icon .ui-control {
  padding-left: 2.4rem;
}

.has-clear .ui-control {
  padding-right: 2.5rem;
}

.ui-input__clear {
  position: absolute;
  right: 0.35rem;
  top: 50%;
  transform: translateY(-50%);
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  color: var(--ink-faint);
}

.ui-input__clear:hover {
  color: var(--ink);
  background-color: var(--paper-sunken);
}
</style>
