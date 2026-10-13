<template>
  <div class="ui-toasts" aria-live="polite" aria-atomic="false">
    <TransitionGroup name="ui-toast">
      <div
        v-for="item in state.toasts"
        :key="item.id"
        class="ui-toast"
        :class="`ui-toast--${item.tone}`"
        role="status"
      >
        <UiIcon :name="iconFor(item.tone)" class="ui-toast__icon" />
        <div class="ui-toast__copy">
          <p v-if="item.title" class="ui-toast__title">{{ item.title }}</p>
          <p v-if="item.message" class="ui-toast__message">
            {{ item.message }}
          </p>
          <router-link
            v-if="item.link && item.link.to"
            :to="item.link.to"
            class="ui-toast__link"
            @click="dismissToast(item.id)"
            >{{ item.link.label }}</router-link
          >
          <a
            v-else-if="item.link && item.link.href"
            :href="item.link.href"
            class="ui-toast__link"
            >{{ item.link.label }}</a
          >
        </div>
        <button
          type="button"
          class="ui-toast__close"
          aria-label="Dismiss"
          @click="dismissToast(item.id)"
        >
          <UiIcon name="close" />
        </button>
      </div>
    </TransitionGroup>
  </div>

  <UiSheet
    :open="Boolean(state.confirmation)"
    side="center"
    size="sm"
    :title="state.confirmation?.title || ''"
    @update:open="(value) => !value && answer(false)"
  >
    <p class="ui-confirm__message">{{ state.confirmation?.message }}</p>
    <template #footer>
      <UiButton variant="ghost" @click="answer(false)">
        {{ state.confirmation?.cancelText }}
      </UiButton>
      <UiButton
        :variant="state.confirmation?.tone === 'danger' ? 'danger' : 'primary'"
        autofocus
        @click="answer(true)"
      >
        {{ state.confirmation?.confirmText }}
      </UiButton>
    </template>
  </UiSheet>
</template>

<script setup>
import UiSheet from './UiSheet.vue';
import UiButton from './UiButton.vue';
import UiIcon from './UiIcon.vue';
import { dismissToast, feedbackState as state } from './feedback';

const ICONS = {
  info: 'info',
  success: 'check-circle',
  warning: 'warning',
  error: 'error',
};

function iconFor(tone) {
  return ICONS[tone] || ICONS.info;
}

function answer(value) {
  state.confirmation?.resolve(value);
}
</script>

<style scoped>
.ui-toasts {
  position: fixed;
  z-index: 1100;
  top: calc(var(--header-height) + env(safe-area-inset-top) + 0.75rem);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  width: min(calc(100% - 2rem), 28rem);
  pointer-events: none;
}

.ui-toast {
  --tone: var(--tone-info);
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-2) var(--space-3) var(--space-4);
  border: 1px solid var(--rule);
  border-left: 3px solid var(--tone);
  border-radius: var(--radius);
  background-color: var(--paper-raised);
  box-shadow: var(--shadow);
  pointer-events: auto;
}

.ui-toast--success {
  --tone: var(--tone-success);
}

.ui-toast--warning {
  --tone: var(--tone-warning);
}

.ui-toast--error {
  --tone: var(--tone-danger);
}

.ui-toast__icon {
  margin-top: 0.2rem;
  color: var(--tone);
}

.ui-toast__copy {
  flex: 1;
  min-width: 0;
  font-size: var(--text-sm);
  line-height: 1.35;
}

.ui-toast__title {
  font-weight: 600;
}

.ui-toast__message {
  color: var(--ink-soft);
}

.ui-toast__link {
  display: inline-block;
  margin-top: var(--space-1);
}

.ui-toast__close {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  color: var(--ink-faint);
}

.ui-toast__close:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

.ui-confirm__message {
  color: var(--ink-soft);
}

.ui-toast-enter-active,
.ui-toast-leave-active {
  transition:
    opacity 200ms var(--ease),
    transform 200ms var(--ease);
}

.ui-toast-enter-from,
.ui-toast-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>
