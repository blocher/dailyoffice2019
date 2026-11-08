<template>
  <div class="psalm-page">
    <header class="page psalm-head">
      <div class="page-header">
        <p class="eyebrow">
          <router-link to="/psalms/" class="psalm-head__up">
            The Psalter
          </router-link>
        </p>
        <h1 class="page-title">
          {{ psalm ? `Psalm ${psalm.number}` : 'Psalm' }}
        </h1>
        <p v-if="psalm && psalm.latin_title" class="page-lede">
          {{ psalm.latin_title }}
        </p>
      </div>

      <Loading v-if="loading" />
      <UiAlert v-if="error" tone="error" :title="error" />

      <template v-if="!loading && !error">
        <p v-if="psalm.topics && psalm.topics.length" class="psalm-topics">
          <router-link
            v-for="topic in psalm.topics"
            :key="topic.id"
            :to="{ name: 'Psalms', query: { topic: topic.id } }"
            class="psalm-topics__link"
          >
            {{ topic.topic_name }}
          </router-link>
        </p>

        <div class="psalm-tools">
          <UiSegmented
            :model-value="traditional"
            :options="languageOptions"
            size="sm"
            aria-label="Language"
            @update:model-value="changeLanguage"
          />
          <label v-if="hasChant" class="psalm-chant-toggle">
            <span>Chant</span>
            <UiSwitch
              :model-value="display.chantMode"
              label="Point this psalm for chant"
              @update:model-value="setChantMode"
            />
          </label>
        </div>
        <p
          v-if="display.chantMode && hasChant && traditional"
          class="psalm-chant-legend"
        >
          Chant pointing is for the Contemporary text.
          <button
            type="button"
            class="psalm-chant-legend__switch"
            @click="changeLanguage(false)"
          >
            Show Contemporary
          </button>
        </p>
        <ChantPlayer
          v-if="showChant"
          ref="chantPlayer"
          :verses="psalm.verses"
          :tone="psalm.chant_tone"
          @position="onChantPosition"
        />
        <p v-if="showChant" class="psalm-chant-legend">
          Pointed for {{ psalm.chant_tone.label }}.
          <span class="psalm-chant-legend__key"
            ><span class="psalm-chant-legend__bar">|</span> the tone turns</span
          >
          ·
          <span class="psalm-chant-legend__key"
            ><span class="psalm-chant-legend__accent">accent</span></span
          >
          ·
          <span class="psalm-chant-legend__key"
            ><span class="psalm-chant-legend__prep">preparatory</span></span
          >
        </p>
      </template>
    </header>

    <template v-if="!loading && !error">
      <nav class="psalm-nav" aria-label="Psalms">
        <router-link
          v-if="psalm.number > 1"
          :to="`/psalm/${psalm.number - 1}`"
          class="psalm-nav__link psalm-nav__link--prev"
        >
          <UiIcon name="chevron-left" />
          <span
            ><span class="psalm-nav__word">Psalm </span
            >{{ psalm.number - 1 }}</span
          >
        </router-link>
        <span v-else class="psalm-nav__spacer" />
        <router-link to="/psalms/" class="psalm-nav__link psalm-nav__link--all">
          All Psalms
        </router-link>
        <router-link
          v-if="psalm.number < 150"
          :to="`/psalm/${psalm.number + 1}`"
          class="psalm-nav__link psalm-nav__link--next"
        >
          <span
            ><span class="psalm-nav__word">Psalm </span
            >{{ psalm.number + 1 }}</span
          >
          <UiIcon name="chevron-right" />
        </router-link>
        <span v-else class="psalm-nav__spacer" />
      </nav>

      <div class="book-opening">
        <Ornament glyph="o" />
      </div>

      <!-- The psalm, set like the printed book -->
      <div id="main" class="book psalm-text">
        <div v-if="!traditional">
          <span v-for="verse in psalm.verses" :key="verse.number">
            <span
              v-if="verse.first_half"
              :ref="(el) => setVerseRef(verse.number, el)"
            >
              <p class="hangingIndent extra-space-before">
                <sup v-if="!(showChant && verse.chant)">{{ verse.number }}</sup>
                <sup v-else
                  ><button
                    type="button"
                    class="psalm-verse-play"
                    :aria-label="`Play from verse ${verse.number}`"
                    @click="playFrom(verse.number)"
                  >
                    {{ verse.number }}
                  </button></sup
                >
                <ChantText
                  v-if="showChant && verse.chant"
                  :segments="verse.chant.first_half"
                  :active="activeIndex(verse.number, 0)"
                />
                <template v-else>{{ verse.first_half }}</template> *
              </p>
              <p class="indent">
                <ChantText
                  v-if="showChant && verse.chant"
                  :segments="verse.chant.second_half"
                  :active="activeIndex(verse.number, 1)"
                />
                <template v-else>{{ verse.second_half }}</template>
              </p>
            </span>
          </span>
        </div>
        <div v-if="traditional">
          <span v-for="verse in psalm.verses" :key="verse.number">
            <span v-if="verse.first_half_tle">
              <p class="hangingIndent extra-space-before">
                <sup>{{ verse.number }}</sup> {{ verse.first_half_tle }} *
              </p>
              <p class="indent">
                {{ verse.second_half_tle }}
              </p>
            </span>
          </span>
        </div>
      </div>

      <nav class="psalm-nav psalm-nav--bottom" aria-label="Psalms">
        <router-link
          v-if="psalm.number > 1"
          :to="`/psalm/${psalm.number - 1}`"
          class="psalm-nav__link psalm-nav__link--prev"
        >
          <UiIcon name="chevron-left" />
          <span
            ><span class="psalm-nav__word">Psalm </span
            >{{ psalm.number - 1 }}</span
          >
        </router-link>
        <span v-else class="psalm-nav__spacer" />
        <router-link to="/psalms/" class="psalm-nav__link psalm-nav__link--all">
          All Psalms
        </router-link>
        <router-link
          v-if="psalm.number < 150"
          :to="`/psalm/${psalm.number + 1}`"
          class="psalm-nav__link psalm-nav__link--next"
        >
          <span
            ><span class="psalm-nav__word">Psalm </span
            >{{ psalm.number + 1 }}</span
          >
          <UiIcon name="chevron-right" />
        </router-link>
        <span v-else class="psalm-nav__spacer" />
      </nav>
    </template>
  </div>
</template>

<script>
import ChantPlayer from '@/components/ChantPlayer.vue';
import ChantText from '@/components/ChantText.vue';
import Loading from '@/components/Loading.vue';
import { displayState, setChantMode } from '@/helpers/displayPreferences';
import { DynamicStorage } from '@/helpers/storage';

export default {
  components: { ChantPlayer, ChantText, Loading },
  data() {
    return {
      display: displayState,
      // The syllable the chant player is sounding: { verse, half, index }.
      chantPosition: null,
      psalm: null,
      loading: true,
      error: false,
      traditional: false,
      languageOptions: [
        { value: false, label: 'Contemporary' },
        { value: true, label: 'Traditional' },
      ],
    };
  },
  async created() {
    // Verse elements by number, to keep the verse being sung in view.
    this.verseRefs = {};
    const traditional = await DynamicStorage.getItem(
      'traditionalPsalms',
      false
    );
    if (traditional === 'true' || traditional === true) {
      this.traditional = true;
    } else {
      this.traditional = false;
    }
    this.setTradtional();
    let data;
    try {
      data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/psalms/${this.$route.params.number}/`
      );
    } catch {
      this.error =
        'There was an error retrieving the psalms. Please try again.';
      this.loading = false;
      return;
    }
    this.psalm = data.data;
    this.error = false;
    this.loading = false;
  },
  computed: {
    hasChant() {
      return Boolean(this.psalm?.verses?.some((verse) => verse.chant));
    },
    showChant() {
      return this.display.chantMode && this.hasChant && !this.traditional;
    },
  },
  watch: {
    showChant(shown) {
      if (!shown) this.chantPosition = null;
    },
  },
  methods: {
    setChantMode,
    setVerseRef(number, el) {
      if (el) this.verseRefs[number] = el;
      else delete this.verseRefs[number];
    },
    activeIndex(number, half) {
      const position = this.chantPosition;
      return position && position.verse === number && position.half === half
        ? position.index
        : -1;
    },
    onChantPosition(position) {
      const previous = this.chantPosition;
      this.chantPosition = position;
      if (position && position.verse !== previous?.verse) {
        this.verseRefs[position.verse]?.scrollIntoView?.({
          block: 'nearest',
          behavior: 'smooth',
        });
      }
    },
    playFrom(number) {
      this.$refs.chantPlayer?.playFrom(number);
    },
    changeLanguage(value) {
      this.traditional = value;
      this.setTradtional();
    },
    async setTradtional() {
      await DynamicStorage.setItem('traditionalPsalms', this.traditional);
    },
  },
};
</script>

<style scoped>
.psalm-head {
  padding-bottom: 0;
}

.psalm-head .page-header {
  margin-bottom: var(--space-4);
}

.psalm-head__up {
  color: inherit;
  text-decoration: none;
}

.psalm-head__up:hover {
  color: var(--accent);
}

.psalm-topics {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  column-gap: var(--space-4);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
}

.psalm-topics__link {
  display: inline-flex;
  align-items: center;
  min-height: 2.75rem;
  color: var(--ink-soft);
  text-decoration: none;
}

.psalm-topics__link:hover {
  color: var(--accent);
}

.psalm-chant-toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--ink-soft);
  font-variant-caps: all-small-caps;
  letter-spacing: var(--tracking-caps);
}

.psalm-chant-legend {
  margin: var(--space-3) 0 0;
  font-size: var(--text-sm);
  color: var(--ink-soft);
  text-align: center;
}

.psalm-verse-play {
  position: relative;
  font: inherit;
  line-height: 1;
  color: var(--accent);
  padding: 0 0.1em;
  border-radius: var(--radius-sm);
}

/* Verse numbers are small; give the finger a bigger target. */
.psalm-verse-play::before {
  content: '';
  position: absolute;
  inset: -0.6rem -0.5rem;
}

.psalm-verse-play:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

.psalm-chant-legend__switch {
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

.psalm-chant-legend__key {
  white-space: nowrap;
}

.psalm-chant-legend__bar {
  color: var(--accent);
}

.psalm-chant-legend__accent,
.psalm-chant-legend__prep {
  text-decoration-line: underline;
  text-decoration-color: var(--accent);
  text-decoration-thickness: 0.09em;
  text-underline-offset: 0.18em;
}

.psalm-chant-legend__prep {
  text-decoration-style: dotted;
}

.psalm-tools {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: var(--space-3) var(--space-4);
  margin-top: var(--space-2);
}

/* Previous · All · Next */
.psalm-nav {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: var(--space-2);
  width: min(calc(100% - 2 * var(--gutter)), var(--content-width));
  margin: var(--space-5) auto 0;
  font-size: var(--text-sm);
}

.psalm-nav--bottom {
  margin-top: 0;
  margin-bottom: var(--space-7);
  padding-top: var(--space-4);
  border-top: 1px solid var(--rule);
}

.psalm-nav__link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: 2.75rem;
  padding: 0 var(--space-2);
  color: var(--ink-soft);
  text-decoration: none;
  white-space: nowrap;
}

.psalm-nav__link:hover {
  color: var(--accent);
}

.psalm-nav__link .ui-icon {
  color: var(--accent);
}

.psalm-nav__link--prev {
  justify-self: start;
}

.psalm-nav__link--all {
  justify-self: center;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
}

.psalm-nav__link--next {
  justify-self: end;
}

@media (max-width: 359px) {
  .psalm-nav__word {
    display: none;
  }
}

/* The verse spacing the office uses (kept here so this page does not
   depend on the office components being loaded). */
.psalm-text .extra-space-before {
  margin-top: 0.7em;
}

/* The bottom navigation supplies the space after the psalm. */
.psalm-text {
  margin-bottom: var(--space-6);
}
</style>
