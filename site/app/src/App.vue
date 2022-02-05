<template>
  <Menu />
  <div class="main">
    <Loading v-if="loading" />
    <router-view v-if="!loading" :key="$route.fullPath" />
  </div>
  <el-backtop />
</template>

<style src="./assets/tailwind.css"></style>
<style lang="scss">
* {
  font-family: "Adobe Caslon Pro", serif;
  font-display: swap;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  color: #2c3e50;

  .main {
    // max-width: 620px;
    max-width: 1800px;
    display: block;
    text-align: left;
    padding: 1.4em;
    margin: 0 auto;
    clear: both;
    overflow-y: scroll;
  }

  .small-container {
    max-width: 550px;
    display: block;
    text-align: left;
    padding: 1.4em;
    margin: 0 auto;
    clear: both;
    overflow-y: scroll;
  }

  h1,
  h2,
  h3,
  h4 {
    font-weight: 600;
    font-style: normal;
    letter-spacing: 0.1em;
    text-align: center;
    margin: 0.2em;
    padding-top: 2em;
  }

  h1,
  h2,
  h3 {
    text-transform: uppercase;
  }

  h1 {
    font-size: 1.3em;
    line-height: 1.5em;
  }

  h2 {
    font-size: 1em;

    &.intro-heading {
      font-size: 0.5em;
      margin: 1em 0 0 0;
      padding: 0;
      line-height: 0.6em;
      letter-spacing: 0.1em;
    }
  }

  h3 {
    padding-top: 30px;
    margin-bottom: 5px;
    font-size: 1em;
    line-height: 1.4em;

    &.intro-heading {
      font-size: 0.4em;
      margin: 0;
      padding: 0;
      line-height: 0.5em;
      letter-spacing: 0.1em;
    }
  }

  h4 {
    margin-top: 0;
    padding-top: 0;
    font-weight: 600;
    font-style: italic;
    font-size: 0.9em;
    line-height: 1em;
    margin-bottom: 1em;
  }

  h5 {
    font-weight: 300;
    text-align: right;
    font-size: 0.9em;
    margin: 10px 0;
    text-transform: uppercase;
  }

  p {
    font-family: "Adobe Caslon Pro", serif;
    font-display: swap;
    font-weight: 300;
    font-style: normal;
    font-size: 1em;

    line-height: 1.6em;

    &.rubric {
      line-height: 0.9em;
      margin: 10px 0;
    }

    &.indent {
      margin: 0 0 0 1em;

      &.hanging-indent {
        text-indent: -1em;
        margin: 0 0 0 1em;
      }
    }

    strong {
      font-weight: 700;
    }
  }

  #container {
    max-width: 580px;
    display: block;
    text-align: left;
    padding: 1.4em;
    margin: 0 auto 1em;
    clear: both;
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

<script>
import Menu from "@/components/Menu";
import Loading from "@/components/Loading";

export default {
  data() {
    return {
      loading: true,
      open: false,
      isActive: true,
      name: this.$route.name,
    };
  },
  async created() {
    document.title = "The Daily Office";
    const settings_data = await this.$http.get(
      "http://127.0.0.1:8000/api/v1/available_settings/"
    );
    await this.$store.commit("saveAvailableSettings", settings_data.data);
    await this.$store.commit("initializeSettings");
    this.loading = false;
  },
  methods: {
    toggleMenu: function () {
      this.open = !this.open;
    },
  },
  components: {
    Menu,
    Loading,
  },
};
</script>
