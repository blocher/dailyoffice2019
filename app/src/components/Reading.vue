<template>
  <div v-show="show" :id="id" :class="wrapperClass">
    <h3>
      {{ reading.full.name }}
    </h3>
    <h4 v-if="!abbreviated" :id="readingID(reading.full)">{{ reading.full.citation }} <span v-html="scriptureLink()"/>
    </h4>
    <h4 v-if="abbreviated" :id="readingID(reading.abbreviated)">{{ reading.abbreviated.citation }} <span
        v-html="scriptureLink(abbreviated=true)"/></h4>
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
    <div v-if="!abbreviated" class="readingText" v-html="reading.full.text"></div>
    <div v-if="abbreviated" class="readingText" v-html="reading.abbreviated.text"></div>
  </div>

</template>

<script>

export default {

  props: [
    "reading",
    "id",
    "psalmCycle",
    "length",
    "translation",
    "psalmsTranslation",
    "psalmStyle",
  ],
  data() {
    return {
      abbreviated: false,
      psalmCycle60: false,
    };
  },
  computed: {
    showAbbreviatedToggle() {
      return this.reading.full.citation != this.reading.abbreviated.citation
    },
    showPsalterCycleToggle() {
      return this.reading.full.cycle == 30 || this.reading.full.cycle == 60;
    },
    show() {
      return this.reading.full.cycle == null || (this.reading.full.cycle == 30 && !this.psalmCycle60) || (this.reading.full.cycle == 60 && this.psalmCycle60)
    },
    wrapperClass() {
      return this.reading.full.name.replace(" ", "_", "g").toLowerCase();
    }
  },
  watch: {
    psalmCycle: function () {
      this.psalmCycle60 = this.psalmCycle == "60"
    },
    length: function () {
      this.abbreviated = this.length == "abbreviated"
    }
  },
  created() {
    this.psalmCycle60 = this.psalmCycle == "60"
    this.abbreviated = this.length == "abbreviated"
  },

  methods: {
    readingID: function (reading) {
      const readingId = reading.citation.replace(/[\W_]+/g, "_")
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
      const reading = abbreviated ? this.reading.abbreviated : this.reading.full;
      if (reading.name.includes("The Psalm")) {
        const psalmsTranslation = this.psalmsTranslation;
        if (psalmsTranslation == "traditional") {
          return "(Traditional)"
        }
        return "(Contemporary)"
      }
      let url = ""
      let abbreviation = this.translation.toLowerCase()
      if (['esv', 'niv', 'nasb'].includes(abbreviation) && this.reading.full.testament == "DC") {
        abbreviation = 'nrsvce'
      }
      if (abbreviation == 'kjv' && this.reading.full.testament == "DC") {
        url = `https://bible.oremus.org/?version=AV&passage=${reading.citation}`
      } else if (abbreviation == "esv") {
        url = `https://www.esv.org/${reading.citation}`
      } else {
        url = `https://www.biblegateway.com/passage/?search=${reading.citation}&version=${abbreviation}`
      }
      abbreviation = abbreviation == "nrsvce" ? "nrsv" : abbreviation;
      return `<a target="_blank" href="${url}">(${abbreviation.toUpperCase()})</a>`

    }
  },
};
</script>

<style scoped lang="scss">

h1, h2, h3, h4 {
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


  h3, h4 {
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

.psalm, .the_psalm, .the_psalms {
  p {
    margin-bottom: .25rem !important;
  }
}


</style>
