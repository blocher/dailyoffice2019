<template>
  <span class="chant-text"
    ><template v-for="(segment, index) in segments" :key="index"
      ><span v-if="segment.r === 'bar'" class="chant-bar" aria-hidden="true"
        >|</span
      ><span v-else-if="segment.r === 'accent'" class="chant-accent">{{
        segment.t
      }}</span
      ><span v-else-if="isPreparatory(segment.r)" class="chant-prep">{{
        segment.t
      }}</span
      ><template v-else>{{ segment.t }}</template></template
    ></span
  >
</template>

<script setup>
/*
  A half-verse pointed for a plainsong tone. The server sends segments
  ({ t: text, r: role }) from psalter/chant/pointing.py: a bar where the
  inflection begins, accented notes underlined, and preparatory and
  intonation notes underlined with dots. Everything else is sung on the
  reciting note.
*/
defineProps({
  segments: { type: Array, required: true },
});

function isPreparatory(role) {
  return role === 'preparatory' || role === 'intonation';
}
</script>

<style scoped>
.chant-bar {
  color: var(--accent);
  font-weight: normal;
  padding: 0 0.12em;
}

.chant-accent {
  text-decoration-line: underline;
  text-decoration-color: var(--accent);
  text-decoration-thickness: 0.09em;
  text-underline-offset: 0.18em;
}

.chant-prep {
  text-decoration-line: underline;
  text-decoration-style: dotted;
  text-decoration-color: var(--accent);
  text-decoration-thickness: 0.09em;
  text-underline-offset: 0.18em;
}
</style>
