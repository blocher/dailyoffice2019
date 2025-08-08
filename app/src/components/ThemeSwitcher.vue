<template>
  <div class="theme-switcher">
    <span class="theme-label">Light</span>
    <el-switch
      v-model="userTheme"
      class="theme-toggle"
      active-value="dark"
      inactive-value="light"
      :active-icon="'🌙'"
      :inactive-icon="'☀️'"
    />
    <span class="theme-label">Dark</span>
  </div>
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
.theme-switcher {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: 8px;
  background-color: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(4px);
  transition: all 0.2s ease;
}

:root.dark .theme-switcher {
  background-color: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.theme-switcher:hover {
  background-color: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.15);
}

:root.dark .theme-switcher:hover {
  background-color: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.theme-label {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--font-color);
  opacity: 0.8;
}

.theme-toggle {
  margin: 0;
}

/* Make the switch smaller and more elegant */
.theme-toggle.el-switch {
  --el-switch-width: 40px;
  --el-switch-height: 20px;
  --el-switch-border-radius: 10px;
}

/* Custom styling for icons if needed */
.theme-toggle .el-switch__core {
  border: 1px solid rgba(0, 0, 0, 0.2);
}

:root.dark .theme-toggle .el-switch__core {
  border: 1px solid rgba(255, 255, 255, 0.2);
}
</style>
