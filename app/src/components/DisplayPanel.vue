<template>
  <UiSheet
    :open="panels.display"
    side="float"
    title="Display"
    @update:open="(value) => (panels.display = value)"
  >
    <DisplaySettings compact :show-audio="showAudio" />
    <p class="display-panel__more">
      <router-link to="/settings" @click="panels.display = false">
        More settings for the offices
        <UiIcon name="arrow-right" />
      </router-link>
    </p>
  </UiSheet>
</template>

<script setup>
import { watch } from 'vue';
import DisplaySettings from '@/components/DisplaySettings.vue';
import { markDisplaySeen } from '@/helpers/discovery';
import { panels } from '@/helpers/panels';

watch(
  () => panels.display,
  (open) => {
    if (open) markDisplaySeen();
  }
);

defineProps({
  showAudio: { type: Boolean, default: true },
});
</script>

<style scoped>
.display-panel__more {
  margin-top: var(--space-5);
  padding-top: var(--space-3);
  border-top: 1px solid var(--rule);
  font-size: var(--text-sm);
}

.display-panel__more a {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  text-decoration: none;
}
</style>
