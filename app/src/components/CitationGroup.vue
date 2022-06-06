<template>
  <p>
  <span v-for="(reading, index) in readings" :key="index">
    <a :href="readingID(reading.full)" @click.prevent="goToReading(reading.full,'full')">{{
        reading.full.citation
      }}</a>
    <span v-if="reading.abbreviated && reading.abbreviated.citation != reading.full.citation">
      &nbsp;<em>[or <a
:href="readingID(reading.abbreviated)"
                       @click.prevent="goToReading(reading.abbreviated,'abbreviated')">{{
        reading.abbreviated.citation
      }}</a>]</em>
    </span>
    <span v-if="index != Object.keys(readings).length - 1">&nbsp;<em>or</em>&nbsp;</span>
  </span>
  </p>

</template>

<script>

export default {
  props: [
    "readings",
  ],
  methods: {
    readingID: function (reading) {
      const readingId = reading.citation.replace(/[\W_]+/g, "_")
      return `#reading_${readingId}`.toLowerCase();
    },
    goToReading: function (reading, length) {
      this.$emit('readingLinkClick', {reading: reading, length: length});
    }
  },
};
</script>

<style scoped lang="scss">
a {
  display: inline;
  font-weight: bold;
  color: var(--el-menu-hover-text-color);
}
</style>

<style lang="scss">


</style>
