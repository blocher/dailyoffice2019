<template>
  <p v-bind:class="{ indent: line.indented, hangingIndent: !line.indented }"><strong>{{ line.content }}</strong></p>
</template>

<script>
// @ is an alias to /src

export default {
  name: "Office Congregation",
  components: {},
  props: ["line"]
};
</script>
