<template>
  <!--  <div class="fixed top-3 right-3 z-200">-->
  <!--    &lt;!&ndash;      <el-tag size="default" type="warning">Beta site</el-tag>&ndash;&gt;-->
  <!--    &lt;!&ndash;      <br>&ndash;&gt;-->
  <!--    <small class="float-right"><a href="https://dailyoffice2019.com">Classic site-->
  <!--      <font-awesome-icon :icon="['fad', 'fa-square-up-right']"/>&nbsp;</a></small>-->
  <!--  </div>-->
  <span class="sub-menu-item">
    <span class="text-xs">Light</span>&nbsp;
    <el-switch
      v-model="userTheme"
      class="text-right"
      active-value="dark"
      inactive-value="light"
    />&nbsp;
    <span class="text-xs">Dark</span>
    <br />
  </span>
</template>

<script>
import { DynamicStorage } from '@/helpers/storage';

export default {
  data() {
    return {
      userTheme: 'light',
    };
  },
  async mounted() {
    let activeTheme = await DynamicStorage.getItem('user-theme');
    if (!activeTheme) {
      activeTheme = this.getMediaPreference();
    }
    this.setTheme(activeTheme, false);
    this.$watch('userTheme', this.setTheme);
  },
  methods: {
    async setTheme(theme, store = true) {
      if (store) {
        await DynamicStorage.setItem('user-theme', theme);
      }
      this.userTheme = theme;
      document.documentElement.className = this.getUserThemeClass();
    },
    getUserThemeClass() {
      return this.userTheme;
    },
    getMediaPreference() {
      const hasDarkPreference = window.matchMedia(
        '(prefers-color-scheme: dark)'
      ).matches;
      if (hasDarkPreference) {
        return 'dark';
      } else {
        return 'light';
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
  font-size: 0.6rem;
}
</style>
