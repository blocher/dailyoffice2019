<template>
  <svg
    class="ui-icon"
    viewBox="0 0 24 24"
    width="1em"
    height="1em"
    :fill="icon.fill ? 'currentColor' : 'none'"
    :stroke="icon.fill ? 'none' : 'currentColor'"
    :stroke-width="icon.fill ? null : strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    :aria-hidden="label ? null : 'true'"
    :role="label ? 'img' : null"
    :aria-label="label || null"
    focusable="false"
    v-html="icon.body"
  />
</template>

<script setup>
import { computed } from 'vue';
import { ICONS } from './iconData';

/*
  <UiIcon name="calendar" />  — sized by the surrounding font-size.
  Pass `label` only when the icon stands alone and carries meaning.
*/
const props = defineProps({
  name: { type: String, required: true },
  label: { type: String, default: '' },
  strokeWidth: { type: [Number, String], default: 1.5 },
});

const icon = computed(() => ICONS[props.name] || ICONS.more);
</script>

<style scoped>
.ui-icon {
  display: inline-block;
  flex-shrink: 0;
  vertical-align: -0.125em;
}
</style>
