<template>
  <span class="chant-text"
    ><template v-for="(segment, index) in segments" :key="index"
      ><span v-if="segment.r === 'bar'" class="chant-bar" aria-hidden="true"
        >|</span
      ><span
        v-else-if="segment.p || roleClass(segment.r)"
        :class="[roleClass(segment.r), { 'is-sung': index === active }]"
        >{{ segment.t }}</span
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
  reciting note. Older responses have no pitches ("p"); their marks show
  the same way, but only sung segments can be highlighted.
*/
defineProps({
  segments: { type: Array, required: true },
  // Index of the segment being sung by the chant player, if any.
  active: { type: Number, default: -1 },
});

function roleClass(role) {
  if (role === 'accent') return 'chant-accent';
  if (role === 'preparatory' || role === 'intonation') return 'chant-prep';
  return null;
}
</script>

<style scoped>
.is-sung {
  background-color: color-mix(in srgb, var(--accent) 18%, transparent);
  border-radius: var(--radius-sm);
}

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
