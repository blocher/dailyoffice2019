<template>
  <div v-show="show" :id="id" :class="wrapperClass">
    <h3>
      {{ displayName }}
    </h3>
    <h4 v-if="!abbreviated" :id="readingID(reading.full)">
      {{ reading.full.citation }} <span v-html="scriptureLink()" />
    </h4>
    <h4 v-if="abbreviated" :id="readingID(reading.abbreviated)">
      {{ reading.abbreviated.citation }}
      <span v-html="scriptureLink((abbreviated = true))" />
    </h4>
    <div class="full-width text-center">
      <el-switch
        v-if="showAbbreviatedToggle"
        v-model="abbreviated"
        size="small"
        inactive-text="Full Length"
        active-text="Suggested Shortening"
        class="content-center mb-5"
      />
      <el-switch
        v-if="showPsalterCycleToggle"
        v-model="psalmCycle60"
        size="small"
        inactive-text="30 day cycle"
        active-text="60 day cycle"
        class="content-center mb-5"
        @change="setCycle"
      />
    </div>
    <div
      v-if="!abbreviated"
      class="readingText"
      v-html="reading.full.text"
    ></div>
    <div
      v-if="abbreviated"
      class="readingText"
      v-html="reading.abbreviated.text"
    ></div>
  </div>
</template>

<script>
export default {
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
    };
  },
  computed: {
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
    scriptureLink(abbreviated = false) {
      const reading = abbreviated
        ? this.reading.abbreviated
        : this.reading.full;
      if (reading.name.includes('The Psalm')) {
        const psalmsTranslation = this.psalmsTranslation;
        if (psalmsTranslation == 'traditional') {
          return '(Traditional)';
        }
        return '(Contemporary)';
      }
      let url = '';
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
      return `<a target="_blank" href="${url}">(${displayName.toUpperCase()})</a>`;
    },
  },
};
</script>

<style scoped lang="scss">
h1,
h2,
h3,
h4 {
  margin: 0 0 0 !important;
  padding: 0 !important;
}

h3 {
  margin-top: 4rem !important;
}

h4 {
  margin-bottom: 1rem !important;
}
</style>

<style lang="scss">
//body h3.reading-heading {
//  margin-top: 1rem !important;
//  font-size: .75em !important;
//  padding-top: 0 !important;
//}

.readingText {
  p {
    margin-bottom: 1rem !important;
  }

  h3,
  h4 {
    display: none !important;
  }

  .psalm {
    h3 {
      text-align: left !important;
      display: block !important;
      margin: 0 !important;
      padding-top: 1rem !important;
    }
  }
}

.psalm,
.the_psalm,
.the_psalms {
  p {
    margin-bottom: 0.25rem !important;
  }
}
</style>
