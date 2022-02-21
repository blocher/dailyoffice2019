<template>
  <span class="sub-menu-item">
    <span class="text-xs">Light</span>&nbsp;
    <el-switch
      v-model="userTheme"
      class="text-right"
      active-value="dark-theme"
      inactive-value="light-theme"
    ></el-switch
    >&nbsp;
    <span class="text-xs">Dark</span>
  </span>
</template>

<script>
export default {
  data() {
    return {
      userTheme: "light-theme",
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
      document.documentElement.className = theme;
    },
    getMediaPreference() {
      const hasDarkPreference = window.matchMedia(
        "(prefers-color-scheme: dark)"
      ).matches;
      if (hasDarkPreference) {
        return "dark-theme";
      } else {
        return "light-theme";
      }
    },
  },
};
</script>
