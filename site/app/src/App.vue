<template>
  <div class="main" v-if="!loading">
    <div id="nav">
      <center>
        <router-link to="/">Home</router-link>
        |
        <router-link to="/settings">Settings</router-link>
        |
        <router-link to="/about">About</router-link>
      </center>
    </div>
    <router-view/>
  </div>
</template>

<style lang="scss">
#app {
  font-family: "Adobe Caslon Pro", serif;
  font-display: swap;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;

  div.main {
    max-width: 580px;
    display: block;
    text-align: left;
    padding: 1.4rem;
    margin: 0 auto 1rem;
    clear: both;
  }

  h1,
  h2,
  h3,
  h4 {
    font-weight: 600;
    font-style: normal;
    letter-spacing: 0.1rem;
    text-align: center;
    margin: 0.2rem;
    padding-top: 2rem;
  }

  h1,
  h2,
  h3 {
    text-transform: uppercase;
  }

  h1 {
    font-size: 1.3rem;
    line-height: 1.5rem;
  }

  h2 {
    font-size: 1rem;

    &.intro-heading {
      font-size: 0.5rem;
      margin: 1rem 0 0 0;
      padding: 0;
      line-height: 0.6rem;
      letter-spacing: 0.1rem;
    }
  }

  h3 {
    padding-top: 30px;
    margin-bottom: 5px;
    font-size: 1rem;
    line-height: 1.4rem;

    &.intro-heading {
      font-size: 0.4rem;
      margin: 0;
      padding: 0;
      line-height: 0.5rem;
      letter-spacing: 0.1rem;
    }
  }

  h4 {
    margin-top: 0;
    padding-top: 0;
    font-weight: 600;
    font-style: italic;
    font-size: 0.9rem;
    line-height: 1rem;
  }

  h5 {
    font-weight: 300;
    text-align: right;
    font-size: 0.9rem;
    margin: 10px 0;
  }

  p {
    font-family: 'Adobe Caslon Pro', serif;
    font-display: swap;
    font-weight: 300;
    font-style: normal;
    font-size: 1rem;

    line-height: 1.6rem;

    &.rubric {
      line-height: 0.9rem;
      margin: 10px 0;
    }

    &.indent {
      margin: 0 0 0 1rem;

      &.hanging-indent {
        text-indent: -1rem;
        margin: 0 0 0 1rem;
      }
    }


  }
}

#nav {
  padding: 30px;

  a {
    font-weight: bold;
    color: #2c3e50;

    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
</style>
<style src="./assets/tailwind.css"></style>

<script>

export default {
  data() {
    return {
      loading: true,
    };
  },
  async beforeCreate() {

  },
  async created() {
    document.title = "The Daily Office"
    const settings_data = await this.$http.get(
        'http://127.0.0.1:8000/api/v1/available_settings/',
    );
    await this.$store.commit("saveAvailableSettings", settings_data.data);
    await this.$store.commit("initializeSettings")
    this.loading = false;
  },
  components: {},
  watch: {
    '$route'(to) {
      document.title = to.meta.title || 'The Daily Office'
    }
  },
}
</script>
