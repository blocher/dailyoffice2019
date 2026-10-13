<template>
  <section v-show="show" :id="id" class="reading" :class="wrapperClass">
    <h2>{{ displayName }}</h2>
    <h4 :id="readingID(current)">
      {{ current.citation }}
      <a
        v-if="source.url"
        class="reading__source"
        :href="source.url"
        target="_blank"
        rel="noopener noreferrer"
        >({{ source.label }})</a
      >
      <span v-else class="reading__source">({{ source.label }})</span>
    </h4>
    <div
      v-if="showAbbreviatedToggle || showPsalterCycleToggle"
      class="reading__options"
    >
      <UiSegmented
        v-if="showAbbreviatedToggle"
        v-model="abbreviated"
        size="sm"
        :options="lengthOptions"
        aria-label="Length of the reading"
      />
      <UiSegmented
        v-if="showPsalterCycleToggle"
        v-model="psalmCycle60"
        size="sm"
        :options="cycleOptions"
        aria-label="Psalter cycle"
        @change="setCycle"
      />
    </div>
    <div class="readingText" v-html="current.text"></div>
  </section>
</template>

<script>
export default {
  emits: ['cycle-30', 'cycle-60'],
  props: [
    'reading',
    'id',
    'psalmCycle',
    'length',
    'translation',
    'psalmsTranslation',
    'psalmStyle',
  ],
  data() {
    return {
      abbreviated: false,
      psalmCycle60: false,
      lengthOptions: [
        { value: false, label: 'Full length' },
        { value: true, label: 'Suggested shortening' },
      ],
      cycleOptions: [
        { value: false, label: '30-day cycle' },
        { value: true, label: '60-day cycle' },
      ],
    };
  },
  computed: {
    current() {
      return this.abbreviated ? this.reading.abbreviated : this.reading.full;
    },
    source() {
      return this.scriptureLink(this.abbreviated);
    },
    isChinese() {
      return ['cuvs', 'cuv', 'znsigao', 'sigao'].includes(this.translation);
    },
    isSpanish() {
      return ['nvi', 'rv1960'].includes(this.translation);
    },
    chineseNameMap() {
      return {
        'The First Lesson': '第一篇經課',
        'The Second Lesson': '第二篇經課',
        'The Third Lesson': '第三篇經課',
        'The Psalm': '詩篇',
        'The Psalms': '詩篇',
        'The Psalm Appointed': '指定詩篇',
        'The Psalms Appointed': '指定詩篇',
        'The Epistle': '書信經課',
        'The Gospel': '福音經課',
        'The Old Testament': '舊約經課',
        'The New Testament': '新約經課',
      };
    },
    spanishNameMap() {
      return {
        'The First Lesson': 'La Primera Lectura',
        'The Second Lesson': 'La Segunda Lectura',
        'The Third Lesson': 'La Tercera Lectura',
        'The Psalm': 'El Salmo',
        'The Psalms': 'Los Salmos',
        'The Psalm Appointed': 'El Salmo Designado',
        'The Psalms Appointed': 'Los Salmos Designados',
        'The Epistle': 'La Epístola',
        'The Gospel': 'El Evangelio',
        'The Old Testament': 'El Antiguo Testamento',
        'The New Testament': 'El Nuevo Testamento',
      };
    },
    displayName() {
      if (this.isChinese && this.chineseNameMap[this.reading.full.name]) {
        return this.chineseNameMap[this.reading.full.name];
      }
      if (this.isSpanish && this.spanishNameMap[this.reading.full.name]) {
        return this.spanishNameMap[this.reading.full.name];
      }
      return this.reading.full.name;
    },
    showAbbreviatedToggle() {
      return this.reading.full.citation != this.reading.abbreviated.citation;
    },
    showPsalterCycleToggle() {
      return this.reading.full.cycle == 30 || this.reading.full.cycle == 60;
    },
    show() {
      return (
        this.reading.full.cycle == null ||
        (this.reading.full.cycle == 30 && !this.psalmCycle60) ||
        (this.reading.full.cycle == 60 && this.psalmCycle60)
      );
    },
    wrapperClass() {
      return this.reading.full.name.replace(' ', '_', 'g').toLowerCase();
    },
  },
  watch: {
    psalmCycle: function () {
      this.psalmCycle60 = this.psalmCycle == '60';
    },
    length: function () {
      this.abbreviated = this.length == 'abbreviated';
    },
  },
  created() {
    this.psalmCycle60 = this.psalmCycle == '60';
    this.abbreviated = this.length == 'abbreviated';
  },

  methods: {
    readingID: function (reading) {
      const readingId = reading.citation.replace(/[\W_]+/g, '_');
      return `reading_${readingId}`.toLowerCase();
    },
    setCycle(status) {
      if (status) {
        this.$emit('cycle-60');
      } else {
        this.$emit('cycle-30');
      }
    },
    // The translation shown after the citation, linked to the passage on
    // the publisher's site (psalms name the psalter instead).
    scriptureLink(abbreviated = false) {
      const reading = abbreviated
        ? this.reading.abbreviated
        : this.reading.full;
      if (reading.name.includes('The Psalm')) {
        const psalmsTranslation = this.psalmsTranslation;
        if (psalmsTranslation == 'traditional') {
          return { url: null, label: 'Traditional' };
        }
        return { url: null, label: 'Contemporary' };
      }
      let url;
      let abbreviation = this.translation.toLowerCase();
      if (
        ['cuvs', 'cuv'].includes(abbreviation) &&
        this.reading.full.testament == 'DC'
      ) {
        // Fall back to 思高本 for deuterocanonical books when using 和合本
        abbreviation = abbreviation == 'cuvs' ? 'znsigao' : 'sigao';
      }
      if (
        ['esv', 'niv', 'nasb', 'nvi', 'rv1960'].includes(abbreviation) &&
        this.reading.full.testament == 'DC'
      ) {
        abbreviation = 'nrsvce';
      }
      if (abbreviation == 'kjv' && this.reading.full.testament == 'DC') {
        url = `https://bible.oremus.org/?version=AV&passage=${reading.citation}`;
      } else if (abbreviation == 'esv') {
        url = `https://www.esv.org/${reading.citation}`;
      } else if (['sigao', 'znsigao'].includes(abbreviation)) {
        const variant = abbreviation == 'znsigao' ? 'znsigao' : 'sigao';
        url = `https://www.ccreadbible.org/chinesebible/${variant}`;
      } else {
        url = `https://www.biblegateway.com/passage/?search=${reading.citation}&version=${abbreviation}`;
      }
      let displayName = abbreviation;
      if (abbreviation == 'nrsvce') displayName = 'nrsv';
      else if (abbreviation == 'sigao') displayName = '思高本（繁體）';
      else if (abbreviation == 'znsigao') displayName = '思高本（简体）';
      return { url, label: displayName.toUpperCase() };
    },
  },
};
</script>

<style scoped>
.reading {
  margin-top: 1.5em;
}

.reading__source {
  font-style: normal;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.06em;
}

span.reading__source {
  color: var(--ink-soft);
}

.reading__options {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-2);
  margin: 0 0 1em;
}

/*
  Passage text from the API. The citation above already names the reading,
  so the API's own headings are hidden, except psalm numbers. book.css
  styles .book headings with an id selector, hence !important to override.
*/
.readingText :deep(p) {
  margin-bottom: 0.8em;
}

.readingText :deep(h3),
.readingText :deep(h4) {
  display: none;
}

.readingText :deep(.psalm h3) {
  display: block;
  margin: 0 !important;
  padding-top: 0.6em !important;
  text-align: left !important;
}

.reading:is(.psalm, .the_psalm, .the_psalms) .readingText :deep(p),
.readingText :deep(.psalm p) {
  margin-bottom: 0.1em;
}
</style>
