<template>
  <select
    :id="id"
    class="ui-control"
    :value="modelValue"
    :disabled="disabled"
    @change="onChange"
  >
    <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
    <template v-for="item in options" :key="item.label + (item.value ?? '')">
      <optgroup v-if="item.options" :label="item.label">
        <option
          v-for="option in item.options"
          :key="option.value"
          :value="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </option>
      </optgroup>
      <option v-else :value="item.value" :disabled="item.disabled">
        {{ item.label }}
      </option>
    </template>
  </select>
</template>

<script setup>
/*
  options: [{ value, label }] or grouped [{ label, options: [{ value, label }] }]
*/
const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  options: { type: Array, default: () => [] },
  id: { type: String, default: null },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
});
const emit = defineEmits(['update:modelValue', 'change']);

function findOption(raw) {
  for (const item of props.options) {
    if (item.options) {
      const match = item.options.find((o) => String(o.value) === raw);
      if (match) return match;
    } else if (String(item.value) === raw) {
      return item;
    }
  }
  return null;
}

function onChange(event) {
  const option = findOption(event.target.value);
  const value = option ? option.value : event.target.value;
  emit('update:modelValue', value);
  emit('change', value);
}
</script>
