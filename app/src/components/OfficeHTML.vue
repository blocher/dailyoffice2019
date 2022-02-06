<template>
  <div v-html="line.content"></div>
</template>

<script>
// @ is an alias to /src

export default {
  name: "Office Citation",
  components: {},
  props: ["line"],
};
</script>
