<template>
  <span :data-line-id="line.id"></span>
  <p :class="indentClass">
    <sup v-if="line.preface">{{ line.preface }}&nbsp;</sup>
    <strong v-if="chant"
      ><ChantText :segments="chant" /><template v-if="asterisk"
        >&nbsp;*</template
      ></strong
    >
    <strong v-else>{{
      line.content.replace(' *', '*').replace('*', '&nbsp;*')
    }}</strong>
  </p>
</template>

<script>
// @ is an alias to /src
import ChantText from '@/components/ChantText.vue';
import { displayState } from '@/helpers/displayPreferences';

export default {
  name: 'Office Congregation',
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
