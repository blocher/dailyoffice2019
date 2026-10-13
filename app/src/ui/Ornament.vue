<template>
  <span class="ornament" aria-hidden="true">{{ glyph }}</span>
</template>

<script setup>
/*
  A fleuron from Adobe Caslon Pro's ornament set (the `ornm` feature maps
  letters to ornaments). Useful glyphs:
    o  leafy sprig (section break)     t  rosette
    y  sunburst rosette                r  snowflake
    v  heart-shaped vine               [ ]  flourishes for flanking a title
    W  w  arched headpieces             i  diamond lattice
*/
defineProps({
  glyph: { type: String, default: 'o' },
});
</script>
