<template>
  <div class="home">
    <img alt="Vue logo" src="../assets/logo.png" />
    Counter: {{ counter }}
  </div>
</template>

<script>
// @ is an alias to /src

export default {
  data() {
    return {
      counter: 0
    }
  },
  name: "Home",
  components: {
  },
  mounted() {
    setInterval(() => {
      this.counter++
    }, 1000)
  }
};
</script>
