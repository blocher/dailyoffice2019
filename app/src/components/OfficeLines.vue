<template>
  <div v-for="module in modules" :key="module.name">
    <div
      v-for="line in module.lines.filter((l) => l.line_type !== 'speaker')"
      :key="line.content"
    >
      <OfficeHeading v-if="line.line_type === 'heading'" :line="line" />
      <OfficeSubheading v-if="line.line_type === 'subheading'" :line="line" />
      <OfficeCitation v-if="line.line_type === 'citation'" :line="line" />
      <OfficeHTML
        v-if="line.line_type === 'html' || line.line_type === 'audio'"
        :line="line"
      />
      <OfficeLeader
        v-if="line.line_type === 'leader' || line.line_type === 'reader'"
        :line="line"
      />
      <OfficeLeaderDialogue
        v-if="line.line_type === 'leader_dialogue'"
        :line="line"
      />
      <OfficeCongregation
        v-if="line.line_type === 'congregation'"
        :line="line"
      />
      <OfficeCongregationDialogue
        v-if="line.line_type === 'congregation_dialogue'"
        :line="line"
      />
      <OfficeRubric v-if="line.line_type === 'rubric'" :line="line" />
      <OfficeSpacer v-if="line.line_type === 'spacer'" />
    </div>
    <PrayerRequests v-if="module.name === INTERCESSION_MODULE" />
  </div>
</template>

<script setup>
import OfficeCitation from '@/components/OfficeCitation.vue';
import OfficeCongregation from '@/components/OfficeCongregation.vue';
import OfficeCongregationDialogue from '@/components/OfficeCongregationDialogue.vue';
import OfficeHTML from '@/components/OfficeHTML.vue';
import OfficeHeading from '@/components/OfficeHeading.vue';
import OfficeLeader from '@/components/OfficeLeader.vue';
import OfficeLeaderDialogue from '@/components/OfficeLeaderDialogue.vue';
import OfficeRubric from '@/components/OfficeRubric.vue';
import OfficeSpacer from '@/components/OfficeSpacer.vue';
import OfficeSubheading from '@/components/OfficeSubheading.vue';
import PrayerRequests from '@/components/PrayerRequests.vue';

// Matches the module name the API sends (site/office/audio_ceremony.py).
const INTERCESSION_MODULE = 'Intercessions, Thanksgivings, and Praise';

/*
  The lines of an office, drawn with the book styles. Used by the office
  page and by the book reader.
*/
defineProps({
  modules: { type: Array, default: () => [] },
});
</script>
