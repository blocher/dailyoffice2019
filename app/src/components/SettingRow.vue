<template>
  <div class="setting-row" :class="{ 'is-open': open }">
    <button
      :id="`${baseId}-toggle`"
      type="button"
      class="setting-row__summary"
      :aria-expanded="open ? 'true' : 'false'"
      :aria-controls="`${baseId}-panel`"
      @click="$emit('update:open', !open)"
    >
      <span class="setting-row__title">
        {{ setting.title }}
        <span
          v-if="isChanged"
          class="setting-row__changed"
          title="Changed from the default"
        >
          <span class="visually-hidden">(changed from default)</span>
        </span>
      </span>
      <span class="setting-row__value">
        <Transition name="setting-saved" mode="out-in">
          <span v-if="saved" key="saved" class="setting-row__saved">
            <UiIcon name="check" /> Saved
          </span>
          <span v-else key="value">{{ currentLabel }}</span>
        </Transition>
      </span>
      <UiIcon name="chevron-down" class="setting-row__chevron" />
    </button>

    <div
      v-if="open"
      :id="`${baseId}-panel`"
      class="setting-row__panel"
      role="region"
      :aria-labelledby="`${baseId}-toggle`"
    >
      <div
        v-if="setting.description"
        class="setting-row__description"
        v-html="setting.description"
      />
      <p v-if="setting.helpShort" class="setting-row__help">
        {{ setting.helpShort }}
      </p>

      <div
        class="setting-options"
        role="radiogroup"
        :aria-label="setting.title"
      >
        <label
          v-for="(option, index) in setting.options"
          :key="option.uuid || option.value"
          class="setting-option"
          :class="{ 'is-selected': option.value === value }"
        >
          <input
            type="radio"
            class="setting-option__input"
            :name="baseId"
            :value="option.value"
            :checked="option.value === value"
            @change="$emit('change', option.value)"
          />
          <span class="setting-option__mark" aria-hidden="true" />
          <span class="setting-option__text">
            <span class="setting-option__name">
              {{ option.name }}
              <span v-if="index === 0" class="setting-option__default"
                >default</span
              >
            </span>
            <span
              v-if="option.description"
              class="setting-option__description"
              v-html="option.description"
            />
          </span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, useId } from 'vue';

/*
  One setting on the Settings page. Closed, it shows the title and the
  current choice; open, it explains the setting and lists every option.
  The first option is the default (the store initializes settings that way).
*/
const props = defineProps({
  setting: { type: Object, required: true },
  value: { type: [String, Number, Boolean], default: null },
  open: { type: Boolean, default: false },
  saved: { type: Boolean, default: false },
});
defineEmits(['update:open', 'change']);

const baseId = `setting-${useId()}`;

const currentLabel = computed(() => {
  const match = (props.setting.options || []).find(
    (o) => o.value === props.value
  );
  return match ? match.name : '';
});

const isChanged = computed(() => {
  const first = (props.setting.options || [])[0];
  return Boolean(first) && props.value !== first.value;
});
</script>

<style scoped>
.setting-row + .setting-row {
  border-top: 1px solid var(--rule);
}

.setting-row__summary {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  min-height: 3.5rem;
  padding: var(--space-3) var(--space-4);
  text-align: left;
  transition: background-color var(--duration) var(--ease);
}

.setting-row__summary:hover {
  background-color: var(--paper-sunken);
}

.setting-row__summary:focus-visible {
  outline: none;
  box-shadow: inset 0 0 0 2px var(--accent);
}

.setting-row__title {
  flex: 1 1 auto;
  min-width: 0;
  color: var(--ink);
  line-height: 1.3;
}

.setting-row__changed {
  display: inline-block;
  width: 0.4rem;
  height: 0.4rem;
  margin-left: 0.35rem;
  border-radius: 50%;
  background-color: var(--accent);
  vertical-align: 0.15em;
}

.setting-row__value {
  flex: 0 0 auto;
  min-width: 0;
  max-width: 48%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-soft);
  text-align: right;
}

@media (max-width: 479px) {
  .setting-row__summary {
    display: grid;
    grid-template-columns: 1fr auto;
    grid-template-areas:
      'title chevron'
      'value chevron';
    row-gap: 0.1rem;
  }

  .setting-row__title {
    grid-area: title;
  }

  .setting-row__value {
    grid-area: value;
    max-width: none;
    text-align: left;
  }

  .setting-row__chevron {
    grid-area: chevron;
  }
}

.setting-row__saved {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-style: normal;
  color: var(--tone-success);
}

.setting-row__chevron {
  flex-shrink: 0;
  color: var(--ink-faint);
  font-size: 0.9rem;
  transition: transform var(--duration) var(--ease);
}

.setting-row.is-open .setting-row__chevron {
  transform: rotate(180deg);
}

.setting-row.is-open .setting-row__summary {
  background-color: var(--paper-sunken);
}

.setting-row__panel {
  padding: var(--space-2) var(--space-4) var(--space-4);
  background-color: var(--paper-sunken);
}

.setting-row__description,
.setting-row__help {
  max-width: 40rem;
  font-size: var(--text-sm);
  color: var(--ink-soft);
  line-height: 1.45;
}

.setting-row__description :deep(p + p) {
  margin-top: var(--space-2);
}

.setting-row__description :deep(ul),
.setting-row__description :deep(ol) {
  margin-top: var(--space-2);
  padding-left: 1.2rem;
  list-style: disc;
}

.setting-row__help {
  margin-top: var(--space-2);
  font-style: italic;
}

/* Options */
.setting-options {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.setting-option {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-3);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background-color: var(--paper-raised);
  cursor: pointer;
  transition:
    border-color var(--duration) var(--ease),
    box-shadow var(--duration) var(--ease);
}

.setting-option:hover {
  border-color: var(--rule-strong);
}

.setting-option.is-selected {
  border-color: var(--accent);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.setting-option__input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.setting-option__mark {
  flex-shrink: 0;
  display: grid;
  place-items: center;
  width: 1.15rem;
  height: 1.15rem;
  margin-top: 0.1rem;
  border: 1px solid var(--rule-strong);
  border-radius: 50%;
  background-color: var(--paper-raised);
}

.setting-option.is-selected .setting-option__mark {
  border-color: var(--accent);
  background-color: var(--accent);
  box-shadow: inset 0 0 0 3px var(--paper-raised);
}

.setting-option__input:focus-visible + .setting-option__mark {
  box-shadow: var(--focus-ring);
}

.setting-option__text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.setting-option__name {
  color: var(--ink);
  line-height: 1.3;
}

.setting-option__default {
  margin-left: 0.4rem;
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.setting-option__description {
  font-size: var(--text-sm);
  color: var(--ink-soft);
  line-height: 1.4;
}

.setting-option__description :deep(p + p) {
  margin-top: var(--space-1);
}

.setting-saved-enter-active,
.setting-saved-leave-active {
  transition: opacity 150ms var(--ease);
}

.setting-saved-enter-from,
.setting-saved-leave-to {
  opacity: 0;
}
</style>
