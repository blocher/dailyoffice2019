<template>
  <p :class="indentClass">
    <strong>{{ line.content }}</strong>
  </p>
</template>

<script>
// @ is an alias to /src

export default {
  name: "Office Congregation",
  components: {},
  props: ["line"],
  computed: {
    indentClass() {

      if (!this.line.indented) {
        return "";
      }
      return this.line.indented;
    }
  }
};
</script>
