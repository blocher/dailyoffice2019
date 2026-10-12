<template>
  <div class="page psalter">
    <header class="page-header">
      <p class="eyebrow">The Psalter</p>
      <h1 class="page-title">Psalms</h1>
      <p class="page-lede">
        {{
          selectedTopic === 'all'
            ? 'The Psalms of David, from the 2019 Book of Common Prayer'
            : selectedTopicName
        }}
      </p>
    </header>

    <Loading v-if="loading" />
    <UiAlert v-if="error" tone="error" :title="error" />

    <template v-if="!loading && !error">
      <section class="psalter-filters" aria-label="Find a psalm">
        <UiInput
          v-model="search"
          icon="search"
          clearable
          type="search"
          placeholder="Number, Latin title, or first line"
          aria-label="Search the psalms"
        />
        <div class="psalter-filters__row">
          <UiField label="Category" for-id="psalter-topic" class="grow">
            <UiSelect
              id="psalter-topic"
              v-model="selectedTopic"
              :options="topicOptions"
              @change="selectTopic"
            />
          </UiField>
          <UiField label="Language">
            <UiSegmented
              :model-value="traditional"
              :options="languageOptions"
              aria-label="Language"
              @update:model-value="changeLanguage"
            />
          </UiField>
        </div>
      </section>

      <p class="psalter-count" aria-live="polite">
        {{ resultsLabel }}
        <button
          v-if="selectedTopic !== 'all' || search"
          type="button"
          class="psalter-count__reset"
          @click="resetFilters"
        >
          Show all
        </button>
      </p>

      <ol v-if="filteredPsalms.length" class="psalter-list">
        <li v-for="psalm in filteredPsalms" :key="psalm.number">
          <router-link :to="`/psalm/${psalm.number}`" class="psalm-entry">
            <span class="psalm-entry__number">{{ psalm.number }}</span>
            <span class="psalm-entry__body">
              <span class="psalm-entry__latin">{{ psalm.latin_title }}</span>
              <span class="psalm-entry__first">{{ firstLine(psalm) }}</span>
              <span v-if="psalm.topics.length" class="psalm-entry__topics">
                {{ psalm.topics.map((t) => t.topic_name).join(' · ') }}
              </span>
            </span>
          </router-link>
        </li>
      </ol>

      <div v-else class="psalter-empty">
        <Ornament glyph="o" />
        <p>No psalms match your search.</p>
      </div>
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
      psalms: null,
      loading: true,
      error: false,
      topics: null,
      displayedPsalms: null,
      selectedTopic: 'all',
      selectedTopicName: 'All Categories',
      traditional: false,
      search: '',
      languageOptions: [
        { value: false, label: 'Contemporary' },
        { value: true, label: 'Traditional' },
      ],
    };
  },
  computed: {
    topicOptions() {
      return [
        { value: 'all', label: 'All Categories' },
        ...(this.topics || []).map((topic) => ({
          value: topic.id,
          label: topic.topic_name,
        })),
      ];
    },
    filteredPsalms() {
      const psalms = this.displayedPsalms || [];
      const query = this.search.toLowerCase().trim();
      if (!query) return psalms;
      return psalms.filter((psalm) => {
        if (String(psalm.number) === query) return true;
        const first = psalm.verses[0] || {};
        return [psalm.latin_title, first.first_half, first.first_half_tle]
          .filter(Boolean)
          .some((text) => text.toLowerCase().includes(query));
      });
    },
    resultsLabel() {
      const count = this.filteredPsalms.length;
      return `${count} ${count === 1 ? 'psalm' : 'psalms'}`;
    },
  },
  async created() {
    const traditional = await DynamicStorage.getItem(
      'traditionalPsalms',
      false
    );
    if (traditional == 'true' || traditional == true) {
      this.traditional = true;
    } else {
      this.traditional = false;
    }
    this.setTraditional();
    let data;
    try {
      data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/psalms`
      );
    } catch {
      this.error =
        'There was an error retrieving the psalms. Please try again.';
      this.loading = false;
      return;
    }
    this.psalms = data.data;
    this.displayedPsalms = this.psalms;

    try {
      data = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/psalms/topics/`
      );
    } catch {
      this.error =
        'There was an error retrieving the psalms. Please try again.';
      this.loading = false;
      return;
    }
    this.topics = data.data;
    if (this.$route.query.topic) {
      const topicId = this.$route.query.topic;
      const t = this.topics.find((topic) => topic.id == topicId);
      if (t) {
        this.selectedTopic = t.id;
        this.updateDisplayedTopic();
      }
    }
    this.error = false;
    this.loading = false;
  },
  watch: {
    '$route.query.topic': function (newTopic) {
      if (newTopic && this.topics) {
        const t = this.topics.find((topic) => topic.id == newTopic);
        if (t) {
          this.selectedTopic = t.id;
          this.updateDisplayedTopic();
        }
      } else if (!newTopic && this.topics) {
        this.selectedTopic = 'all';
        this.updateDisplayedTopic();
      }
    },
  },
  methods: {
    firstLine(psalm) {
      const verse = psalm.verses[0];
      if (!verse) return '';
      const text = this.traditional ? verse.first_half_tle : verse.first_half;
      return (text || '').trim().replace(/[^\p{L}]+$/gu, '');
    },
    // Keep the chosen category in the URL so it can be shared and so the
    // topic links on a psalm page land on the same filtered list.
    selectTopic(topicId) {
      const query = topicId === 'all' ? {} : { topic: topicId };
      this.$router.replace({ name: 'Psalms', query });
      this.updateDisplayedTopic();
    },
    resetFilters() {
      this.search = '';
      if (this.selectedTopic !== 'all') {
        this.selectedTopic = 'all';
        this.selectTopic('all');
      }
    },
    updateDisplayedTopic() {
      if (this.selectedTopic === 'all') {
        this.selectedTopicName = 'All Categories';
        this.displayedPsalms = this.psalms;
      } else {
        this.displayedPsalms = this.psalms.filter(
          (psalm) =>
            psalm.topics.map((topic) => topic.id).indexOf(this.selectedTopic) >
            -1
        );
        this.selectedTopicName = this.topics.find(
          (topic) => topic.id === this.selectedTopic
        ).topic_name;
      }
    },
    changeLanguage(value) {
      this.traditional = value;
      this.setTraditional();
    },
    async setTraditional() {
      await DynamicStorage.setItem('traditionalPsalms', this.traditional);
    },
  },
};
</script>

<style scoped>
.psalter-filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--rule);
}

.psalter-filters__row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-4);
}

.psalter-filters__row .grow {
  flex: 1 1 14rem;
  min-width: 0;
}

.psalter-filters :deep(.ui-field__label) {
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.psalter-filters :deep(.ui-segmented--pill .ui-segmented__option) {
  min-height: 2.375rem;
}

.psalter-count {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 2.75rem;
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.psalter-count__reset {
  min-height: 2.75rem;
  color: var(--accent);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
}

.psalter-count__reset:hover {
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

/* Two calm columns on wider screens; one on phones. */
.psalter-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 19rem), 1fr));
  column-gap: var(--space-6);
}

.psalter-list > li {
  border-top: 1px solid var(--rule);
  min-width: 0;
}

.psalm-entry {
  display: flex;
  align-items: baseline;
  gap: var(--space-4);
  min-height: 2.75rem;
  padding: var(--space-3) var(--space-1);
  color: var(--ink);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: background-color var(--duration) var(--ease);
}

.psalm-entry:hover {
  background-color: var(--accent-wash);
}

.psalm-entry__number {
  flex: 0 0 2.25rem;
  text-align: right;
  font-size: var(--text-xl);
  line-height: 1;
  font-variant-numeric: oldstyle-nums tabular-nums;
  color: var(--accent);
}

.psalm-entry__body {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.psalm-entry__latin {
  font-style: italic;
  font-size: var(--text-md);
  line-height: var(--leading-tight);
}

.psalm-entry__first {
  font-size: var(--text-sm);
  line-height: 1.35;
  color: var(--ink-soft);
}

.psalm-entry__topics {
  margin-top: 0.15rem;
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
}

.psalter-empty {
  padding: var(--space-7) 0;
  text-align: center;
  font-style: italic;
  color: var(--ink-soft);
}

.psalter-empty .ornament {
  font-size: 1.5rem;
  margin-bottom: var(--space-3);
}
</style>
