<template>
  <div class="collectsWrapper">
    <div v-for="(collect, index) in collects" :key="index">
      <div>
        <em>{{ style }}</em
        ><br /><span v-html="collect"></span>
      </div>
      <p v-if="index != collects.length - 1"><em>or</em></p>
    </div>
  </div>
</template>

<script>
export default {
  props: ['collects', 'style'],
};
</script>

<style scoped>
p {
  margin-bottom: 0.5rem;
}

/* Set off between hairlines, not boxed. */
.collectsWrapper {
  margin: 1em 0;
  padding: 0.75em 0;
  border-top: 1px solid var(--rule);
  border-bottom: 1px solid var(--rule);
}
</style>
