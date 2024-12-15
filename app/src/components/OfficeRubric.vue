<template>
  <p class="rubric">
    <em>{{ line.content }}</em>
  </p>
</template>

<script>
// @ is an alias to /src
export default {
  name: 'Office Rubric',
  components: {},
  props: ['line'],
};
</script>

<style lang="scss" scoped>
.rubric {
  font-size: 0.8em;
  line-height: 1.2em;
}
</style>
