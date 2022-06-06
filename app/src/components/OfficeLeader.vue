<template>
  <p v-if="!line.extra_space_before" :class="indentClass">
    <sup v-if="line.preface">{{ line.preface }}</sup>
    {{ line.content.replace(" *", "*").replace("*", "&nbsp;*") }}
  </p>
  <p
      v-if="line.extra_space_before" class="extra-space-before"
      :class="indentClass">

    <sup v-if="line.preface">{{ line.preface }}</sup>
    {{ line.content.replace(" *", "*").replace("*", "&nbsp;*") }}
  </p>
</template>

<script>
// @ is an alias to /src

export default {
  name: "Office Leader",
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

<style>
.extra-space-before {
  margin-top: 0.7em;
}
</style>
