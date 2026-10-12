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
          <template v-for="(topic, index) in psalm.topics" :key="topic.id">
            <span v-if="index" class="psalm-topics__sep" aria-hidden="true"
              >·</span
            >
            <router-link
              :to="{ name: 'Psalms', query: { topic: topic.id } }"
              class="psalm-topics__link"
            >
              {{ topic.topic_name }}
            </router-link>
          </template>
        </p>

        <div class="psalm-tools">
          <UiSegmented
            :model-value="traditional"
            :options="languageOptions"
            size="sm"
            aria-label="Language"
            @update:model-value="changeLanguage"
          />
        </div>
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
            <span v-if="verse.first_half">
              <p class="hangingIndent extra-space-before">
                <sup>{{ verse.number }}</sup> {{ verse.first_half }} *
              </p>
              <p class="indent">
                {{ verse.second_half }}
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
import Loading from '@/components/Loading.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  components: { Loading },
  data() {
    return {
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
  methods: {
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
  column-gap: var(--space-2);
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

.psalm-topics__sep {
  color: var(--ink-faint);
}

.psalm-tools {
  display: flex;
  justify-content: center;
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
