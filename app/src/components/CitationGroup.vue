<template>
  <div class="citations">
    <span v-for="(reading, index) in readings" :key="index">
      <a
        :href="readingID(reading.full)"
        @click.prevent="goToReading(reading.full, 'full')"
        >{{ reading.full.citation }}</a
      >
      <span v-if="reading.full.cycle == '30'" class="citations__note">
        (30-day cycle)</span
      ><span v-if="reading.full.cycle == '60'" class="citations__note">
        (60-day cycle)</span
      >
      <span
        v-if="
          reading.abbreviated &&
          reading.abbreviated.citation != reading.full.citation
        "
      >
        &nbsp;<em
          >[or
          <a
            :href="readingID(reading.abbreviated)"
            @click.prevent="goToReading(reading.abbreviated, 'abbreviated')"
            >{{ reading.abbreviated.citation }}</a
          >]</em
        >
      </span>
      <span v-if="index != Object.keys(readings).length - 1"
        >&nbsp;<em>or</em>&nbsp;</span
      >
    </span>
  </div>
</template>

<script>
export default {
  props: ['readings'],
  emits: ['readingLinkClick'],
  methods: {
    readingID: function (reading) {
      const readingId = reading.citation.replace(/[\W_]+/g, '_');
      return `#reading_${readingId}`.toLowerCase();
    },
    goToReading: function (reading, length) {
      this.$emit('readingLinkClick', { reading: reading, length: length });
    },
  },
};
</script>

<style scoped>
/* The day's citations, centered under the service name, as a contents
   line: each one jumps to its reading. */
.citations {
  margin-bottom: 0.4em;
  font-size: 0.9em;
  line-height: var(--leading-prose);
  text-align: center;
  text-wrap: balance;
}

.citations a {
  text-decoration: none;
}

.citations a:hover {
  text-decoration: underline;
}

.citations__note {
  font-style: italic;
  color: var(--ink-soft);
}
</style>
