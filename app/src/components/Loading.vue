<template>
  <div
    class="loading"
    :class="{ 'loading--small': small }"
    role="status"
    aria-live="polite"
  >
    <span class="loading__dots" aria-hidden="true">
      <span class="ornament">t</span>
      <span class="ornament">t</span>
      <span class="ornament">t</span>
    </span>
    <span class="visually-hidden">Loading…</span>
  </div>
</template>

<script setup>
defineProps({ small: { type: Boolean, default: false } });
</script>

<style scoped>
.loading {
  display: flex;
  justify-content: center;
  padding: var(--space-7) 0;
}

.loading--small {
  display: inline-flex;
  padding: 0;
}

.loading__dots {
  display: inline-flex;
  gap: 0.6em;
  font-size: 1.1rem;
}

.loading--small .loading__dots {
  gap: 0.3em;
  font-size: 0.75rem;
}

.loading__dots .ornament {
  opacity: 0.25;
  animation: loading-pulse 1.2s var(--ease) infinite;
}

.loading__dots .ornament:nth-child(2) {
  animation-delay: 0.2s;
}

.loading__dots .ornament:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes loading-pulse {
  0%,
  100% {
    opacity: 0.25;
    transform: scale(0.9);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}
</style>
