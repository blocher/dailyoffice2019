<template>
  <label class="ui-check">
    <input
      type="checkbox"
      :checked="isChecked"
      :value="value"
      :disabled="disabled"
      @change="onChange"
    />
    <span
      ><slot>{{ label }}</slot></span
    >
  </label>
</template>

<script setup>
import { computed } from 'vue';

/*
  Boolean v-model, or an array v-model with `value` (like a checkbox group).
*/
const props = defineProps({
  modelValue: { type: [Boolean, Array], default: false },
  value: { type: [String, Number], default: null },
  label: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
});
const emit = defineEmits(['update:modelValue', 'change']);

const isChecked = computed(() =>
  Array.isArray(props.modelValue)
    ? props.modelValue.includes(props.value)
    : Boolean(props.modelValue)
);

function onChange(event) {
  let next;
  if (Array.isArray(props.modelValue)) {
    next = event.target.checked
      ? [...props.modelValue, props.value]
      : props.modelValue.filter((v) => v !== props.value);
  } else {
    next = event.target.checked;
  }
  emit('update:modelValue', next);
  emit('change', next);
}
</script>
