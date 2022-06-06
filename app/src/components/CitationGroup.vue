<template>
  <p>
  <span v-for="(citation, index) in citationGroup" :key="index">
    <a href="poop">{{ citation.full }}</a>
    <span v-if="citation.abbreviated && citation.abbreviated != citation.full">
      &nbsp;[or <a href="poop">{{ citation.abbreviated }}</a>]
    </span>
    <span v-if="index != Object.keys(citationGroup).length - 1">&nbsp;<em>or</em>&nbsp;</span>
  </span>
  </p>

</template>

<script>

export default {
  props: [
    "citationGroup",
  ],
};
</script>

<style scoped lang="scss">
a {
  display: inline;
}
</style>

<style lang="scss">


</style>
