<template>
  <div
    class="display-settings"
    :class="{ 'display-settings--compact': compact }"
  >
    <section class="display-row">
      <div class="display-row__head">
        <h3 class="display-row__label">Theme</h3>
        <span class="display-row__value">{{ themeLabel }}</span>
      </div>
      <UiSegmented
        :model-value="state.theme"
        :options="themes"
        block
        aria-label="Theme"
        @update:model-value="setTheme"
      />
    </section>

    <section class="display-row">
      <div class="display-row__head">
        <h3 class="display-row__label">Text size</h3>
        <span class="display-row__value">
          {{ percent }}%
          <button
            v-if="state.fontSize !== defaultSize"
            type="button"
            class="display-row__reset"
            @click="setFontSize(defaultSize)"
          >
            Reset
          </button>
        </span>
      </div>
      <TextSizeControl />
    </section>

    <section class="display-row">
      <div class="display-row__head">
        <h3 class="display-row__label">Typeface</h3>
        <span class="display-row__value">{{ fontLabel }}</span>
      </div>
      <div class="font-grid" role="radiogroup" aria-label="Typeface">
        <button
          v-for="font in fonts"
          :key="font.value"
          type="button"
          role="radio"
          class="font-tile"
          :class="{ 'is-selected': font.value === state.readingFont }"
          :aria-checked="font.value === state.readingFont ? 'true' : 'false'"
          @click="setReadingFont(font.value)"
        >
          <span class="font-tile__sample" :style="{ fontFamily: font.family }"
            >Glory be</span
          >
          <span class="font-tile__name">{{ font.label }}</span>
          <span class="font-tile__note">{{ font.note }}</span>
        </button>
      </div>
    </section>

    <section class="display-row">
      <div class="display-row__head">
        <h3 class="display-row__label">Rubrics</h3>
        <span class="display-row__value">{{ rubricNote }}</span>
      </div>
      <UiSegmented
        :model-value="state.rubricStyle"
        :options="rubricOptions"
        block
        aria-label="Rubrics"
        @update:model-value="setRubricStyle"
      />
    </section>

    <section class="display-row display-row--inline">
      <div class="display-row__copy">
        <h3 class="display-row__label">Contents in the margin</h3>
        <p class="display-row__hint">
          On wide screens, a list of the office’s sections beside the text.
        </p>
      </div>
      <UiSwitch
        :model-value="state.showContents"
        label="Show contents in the margin"
        @update:model-value="setShowContents"
      />
    </section>

    <section v-if="showAudio" class="display-row display-row--inline">
      <div class="display-row__copy">
        <h3 class="display-row__label">Audio player</h3>
        <p class="display-row__hint">
          Listen along with the office. Available for recent and upcoming days
          in English with the ESV or KJV.
        </p>
      </div>
      <UiSwitch
        :model-value="state.audioEnabled"
        label="Show audio player"
        @update:model-value="setAudioEnabled"
      />
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import TextSizeControl from '@/components/TextSizeControl.vue';
import {
  DEFAULT_FONT_SIZE,
  READING_FONTS,
  RUBRIC_STYLES,
  THEMES,
  displayState as state,
  fontSizePercent,
  setAudioEnabled,
  setFontSize,
  setReadingFont,
  setRubricStyle,
  setShowContents,
  setTheme,
} from '@/helpers/displayPreferences';

defineProps({
  showAudio: { type: Boolean, default: true },
  compact: { type: Boolean, default: false },
});

const themes = THEMES;
const fonts = READING_FONTS;
const defaultSize = DEFAULT_FONT_SIZE;

const percent = computed(() => fontSizePercent(state.fontSize));

const themeLabel = computed(() => {
  if (state.theme !== 'auto') return '';
  return `Following device · ${state.resolvedTheme === 'dark' ? 'Dark' : 'Light'}`;
});

// Each option previews itself: italic, or red and upright.
const rubricOptions = RUBRIC_STYLES.map((r) => ({
  value: r.value,
  label: r.label,
  style:
    r.value === 'italic'
      ? { fontStyle: 'italic' }
      : { color: 'var(--season-red)' },
}));

const rubricNote = computed(
  () => RUBRIC_STYLES.find((r) => r.value === state.rubricStyle)?.note || ''
);

const fontLabel = computed(
  () => fonts.find((f) => f.value === state.readingFont)?.label || ''
);
</script>

<style scoped>
.display-settings {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.display-settings--compact {
  gap: var(--space-4);
}

.display-row__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}

.display-row__label {
  font-size: var(--text-md);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink);
}

.display-row__value {
  display: inline-flex;
  align-items: baseline;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-faint);
}

.display-row__reset {
  font-style: normal;
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 0.15em;
  text-decoration-color: color-mix(in srgb, currentColor 35%, transparent);
}

.display-row--inline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.display-row__hint {
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  color: var(--ink-soft);
  line-height: 1.35;
}

/* Typeface tiles */
.font-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-2);
}

@media (min-width: 640px) {
  .display-settings:not(.display-settings--compact) .font-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

.font-tile {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
  min-width: 0;
  padding: var(--space-3);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background-color: var(--paper-raised);
  text-align: left;
  transition:
    border-color var(--duration) var(--ease),
    box-shadow var(--duration) var(--ease);
}

.font-tile:hover {
  border-color: var(--rule-strong);
}

.font-tile.is-selected {
  border-color: var(--accent);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.font-tile:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.font-tile__sample {
  display: block;
  height: 1.75rem;
  font-size: 1.35rem;
  line-height: 1.75rem;
  color: var(--ink);
  white-space: nowrap;
}

.font-tile__name {
  font-size: var(--text-sm);
  color: var(--ink);
}

.font-tile__note {
  font-size: var(--text-xs);
  font-style: italic;
  color: var(--ink-faint);
  line-height: 1.25;
}
</style>
