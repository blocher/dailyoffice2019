<template>
  <div class="collectsWrapper">
    <div v-for="(collect, index) in collects" :key="index">
      <p>{{ collect }} <strong>Amen.</strong></p>
      <p v-if="index != collects.length - 1"><em>or</em></p>
    </div>
  </div>

</template>

<script>

export default {
  props: [
    "collects",
  ],
};
</script>

<style scoped lang="scss">
p {
  margin-bottom: .5rem;
}

.collectsWrapper {
  padding: 1rem;
  border: 1px solid var(--font-color);
  border-radius: .25rem;
  margin: 1rem 0;
}

</style>

<style lang="scss">


</style>
