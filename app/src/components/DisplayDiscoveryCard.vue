<template>
  <aside
    v-if="discovery.showDisplayCard"
    class="make-it-yours surface"
    aria-labelledby="make-it-yours-title"
  >
    <button
      type="button"
      class="make-it-yours__close"
      aria-label="Dismiss"
      @click="dismissDisplayCard"
    >
      <UiIcon name="close" />
    </button>

    <h2 id="make-it-yours-title" class="make-it-yours__title">Make it yours</h2>
    <p class="make-it-yours__lede">
      Change how the prayers look. Tap to try; everything lives under
      <span class="make-it-yours__aa">Aa</span> at the top of the page.
    </p>

    <div class="make-it-yours__rows">
      <div class="make-it-yours__row">
        <p class="make-it-yours__label">Theme</p>
        <div class="make-it-yours__choices">
          <button
            v-for="theme in themes"
            :key="theme.value"
            type="button"
            class="swatch-choice"
            :class="[
              `swatch-choice--${theme.value}`,
              { 'is-selected': state.resolvedTheme === theme.value },
            ]"
            :aria-pressed="
              state.resolvedTheme === theme.value ? 'true' : 'false'
            "
            @click="setTheme(theme.value)"
          >
            <span class="swatch-choice__paper" aria-hidden="true">Aa</span>
            <span class="swatch-choice__name">{{ theme.label }}</span>
          </button>
        </div>
      </div>

      <div class="make-it-yours__row">
        <p class="make-it-yours__label">Text size</p>
        <TextSizeControl class="make-it-yours__size" />
      </div>

      <div class="make-it-yours__row">
        <p class="make-it-yours__label">Typeface</p>
        <div class="make-it-yours__choices">
          <button
            v-for="font in fonts"
            :key="font.value"
            type="button"
            class="text-choice"
            :class="{ 'is-selected': state.readingFont === font.value }"
            :aria-pressed="state.readingFont === font.value ? 'true' : 'false'"
            :style="{ fontFamily: font.family }"
            @click="setReadingFont(font.value)"
          >
            Glory be
            <span class="visually-hidden">({{ font.label }})</span>
          </button>
          <button
            type="button"
            class="text-choice text-choice--more"
            @click="openPanel('display')"
          >
            More…
            <span class="visually-hidden">typefaces</span>
          </button>
        </div>
      </div>

      <div class="make-it-yours__row">
        <p class="make-it-yours__label">Rubrics</p>
        <div class="make-it-yours__choices">
          <button
            type="button"
            class="text-choice text-choice--italic"
            :class="{ 'is-selected': state.rubricStyle === 'italic' }"
            :aria-pressed="state.rubricStyle === 'italic' ? 'true' : 'false'"
            @click="setRubricStyle('italic')"
          >
            All stand.
            <span class="visually-hidden">(italic rubrics)</span>
          </button>
          <button
            type="button"
            class="text-choice text-choice--red"
            :class="{ 'is-selected': state.rubricStyle === 'red' }"
            :aria-pressed="state.rubricStyle === 'red' ? 'true' : 'false'"
            @click="setRubricStyle('red')"
          >
            All stand.
            <span class="visually-hidden">(red rubrics)</span>
          </button>
        </div>
      </div>

      <div v-if="audioAvailable" class="make-it-yours__row">
        <p class="make-it-yours__label">Audio</p>
        <label class="make-it-yours__audio">
          <UiSwitch
            :model-value="state.audioEnabled"
            label="Show the audio player"
            @update:model-value="setAudioEnabled"
          />
          <span>Listen along with the office</span>
        </label>
      </div>
    </div>

    <UiButton
      class="make-it-yours__customize"
      to="/settings"
      variant="primary"
      size="lg"
      icon="sliders"
      block
    >
      Customize
    </UiButton>

    <div class="make-it-yours__actions">
      <UiButton variant="quiet" size="sm" @click="openPanel('display')">
        All display options
      </UiButton>
      <UiButton variant="ghost" size="sm" @click="dismissDisplayCard">
        Done
      </UiButton>
    </div>
  </aside>
</template>

<script setup>
import {
  READING_FONTS,
  displayState as state,
  setAudioEnabled,
  setReadingFont,
  setRubricStyle,
  setTheme,
} from '@/helpers/displayPreferences';
import TextSizeControl from '@/components/TextSizeControl.vue';
import {
  discoveryState as discovery,
  dismissDisplayCard,
} from '@/helpers/discovery';
import { openPanel } from '@/helpers/panels';

/*
  Shown at the end of an office until dismissed: a small, tappable sample
  of the Display options, offered after the prayers rather than before them.
*/
defineProps({
  // Hide the audio row where audio isn't offered (e.g. in development).
  audioAvailable: { type: Boolean, default: true },
});

const themes = [
  { value: 'light', label: 'Light' },
  { value: 'sepia', label: 'Sepia' },
  { value: 'dark', label: 'Dark' },
];

// A few faces with distinct character; the panel has the rest.
const fonts = READING_FONTS.filter((f) =>
  ['caslon', 'baskerville', 'blackletter'].includes(f.value)
);
</script>

<style scoped>
.make-it-yours {
  position: relative;
  max-width: 40rem;
  margin: var(--space-6) auto 0;
  padding: var(--space-5);
}

@media (max-width: 559px) {
  .make-it-yours {
    margin-inline: var(--gutter);
    padding: var(--space-4);
  }
}

.make-it-yours__close {
  position: absolute;
  top: var(--space-2);
  right: var(--space-2);
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  color: var(--ink-faint);
}

.make-it-yours__close:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

.make-it-yours__title {
  font-size: var(--text-lg);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
}

.make-it-yours__lede {
  margin-top: var(--space-1);
  padding-right: var(--space-6);
  font-size: var(--text-sm);
  color: var(--ink-soft);
}

.make-it-yours__aa {
  color: var(--ink);
}

.make-it-yours__rows {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.make-it-yours__row {
  display: grid;
  grid-template-columns: 5.5rem 1fr;
  align-items: center;
  gap: var(--space-3);
}

@media (max-width: 479px) {
  .make-it-yours__row {
    grid-template-columns: 1fr;
    gap: var(--space-1);
  }
}

.make-it-yours__label {
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.make-it-yours__choices {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

/* Theme samples: a little square of each paper. These show each theme's
   own colors whatever the current theme is, so they repeat the paper and
   ink values from tokens.css rather than using the live tokens. */
.swatch-choice {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 2.75rem;
  padding: 0.25rem 0.75rem 0.25rem 0.3rem;
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background-color: var(--paper-raised);
  font-size: var(--text-sm);
  color: var(--ink);
}

.swatch-choice__paper {
  display: grid;
  place-items: center;
  width: 2rem;
  height: 2rem;
  border-radius: var(--radius-sm);
  box-shadow: inset 0 0 0 1px rgb(0 0 0 / 0.12);
  font-size: 0.95rem;
}

.swatch-choice--light .swatch-choice__paper {
  background-color: #fdfcf9;
  color: #1c1a17;
}

.swatch-choice--sepia .swatch-choice__paper {
  background-color: #f4ecd9;
  color: #36291b;
}

.swatch-choice--dark .swatch-choice__paper {
  background-color: #161513;
  color: #e9e4da;
}

/* Text samples: typefaces and rubric styles */
.text-choice {
  min-height: 2.75rem;
  padding: 0.3rem 0.85rem;
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background-color: var(--paper-raised);
  font-size: 1.15rem;
  line-height: 1.2;
  color: var(--ink);
}

.text-choice--italic {
  font-style: italic;
}

.text-choice--red {
  color: var(--season-red);
}

.swatch-choice:hover,
.text-choice:hover {
  border-color: var(--rule-strong);
}

.swatch-choice.is-selected,
.text-choice.is-selected {
  border-color: var(--accent);
  box-shadow: inset 0 0 0 1px var(--accent);
}

.make-it-yours__size {
  max-width: 24rem;
}

.text-choice--more {
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--accent);
}

.make-it-yours__audio {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 2.75rem;
  font-size: var(--text-sm);
  color: var(--ink-soft);
  cursor: pointer;
}

.make-it-yours__customize {
  margin-top: var(--space-5);
}

.make-it-yours__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-2);
  margin-top: var(--space-2);
}
</style>
