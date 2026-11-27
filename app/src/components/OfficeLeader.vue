<template>
  <span :data-line-id="line.id"></span>
  <p v-if="!line.extra_space_before" :class="indentClass">
    <sup v-if="line.preface">{{ line.preface }}&nbsp;</sup>
    <template v-if="chant"
      ><ChantText :segments="chant" /><template v-if="asterisk"
        >&nbsp;*</template
      ></template
    >
    <template v-else>{{
      line.content.replace(' *', '*').replace('*', '&nbsp;*')
    }}</template>
  </p>
  <p
    v-if="line.extra_space_before"
    class="extra-space-before"
    :class="indentClass"
  >
    <sup v-if="line.preface">{{ line.preface }}</sup>
    {{ line.content.replace(' *', '*').replace('*', '&nbsp;*') }}
  </p>
</template>

<script>
// @ is an alias to /src
import ChantText from '@/components/ChantText.vue';
import { displayState } from '@/helpers/displayPreferences';

export default {
  name: 'Office Leader',
  components: { ChantText },
  props: ['line'],
  computed: {
    // Psalm lines carry plainsong pointing when the verse has been pointed.
    chant() {
      return displayState.chantMode && this.line.chant ? this.line.chant : null;
    },
    asterisk() {
      return this.line.content.includes('*');
    },
    indentClass() {
      if (!this.line.indented) {
        return '';
      }
      return this.line.indented;
    },
  },
};
</script>

<style>
.extra-space-before {
  margin-top: 0.7em;
}
</style>
