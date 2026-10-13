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
