<template>
  <div class="officeHTML" v-html="line.content" />
</template>

<script>
// @ is an alias to /src

export default {
  name: 'Office Citation',
  components: {},
  props: ['line'],
};
</script>

<style lang="scss">
body .officeHTML p,
body .officeHTML iframe {
  margin-bottom: 0.8em;
}

body .officeHTML h3 {
  font-size: 0.75em !important;
}
</style>
