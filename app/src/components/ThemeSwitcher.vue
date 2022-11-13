<template>
  <div class="fixed top-3 right-3 z-200">
    <el-tag size="default" type="warning">Beta site</el-tag>
    <br>
    <small class="float-right"><a href="https://dailyoffice2019.com">Classic site
      <font-awesome-icon :icon="['fad', 'fa-square-up-right']"/>&nbsp;</a></small>
  </div>
  <span class="sub-menu-item">

    <span class="text-xs">Light</span>&nbsp;
    <el-switch
        v-model="userTheme"
        class="text-right"
        active-value="dark"
        inactive-value="light"
    />&nbsp;
    <span class="text-xs">Dark</span>
    <br/>


  </span>
</template>

<script>
export default {
  data() {
    return {
      userTheme: "light",
    };
  },
  mounted() {
    let activeTheme = localStorage.getItem("user-theme");
    if (!activeTheme) {
      activeTheme = this.getMediaPreference();
    }
    this.setTheme(activeTheme, false);
    this.$watch("userTheme", this.setTheme);
  },
  methods: {
    setTheme(theme, store = true) {
      if (store) {
        localStorage.setItem("user-theme", theme);
      }
      this.userTheme = theme;
      document.documentElement.className = this.getUserThemeClass();
    },
    getUserThemeClass() {
      return this.userTheme;
    },
    getMediaPreference() {
      const hasDarkPreference = window.matchMedia(
          "(prefers-color-scheme: dark)"
      ).matches;
      if (hasDarkPreference) {
        return "dark";
      } else {
        return "light";
      }
    },
  },
};
</script>

<style scoped lang="scss">

.z-200 {
  z-index: 200;
}

small {
  font-size: .6rem;
}

</style>
