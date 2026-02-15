<template>
  <div class="settings-page">
    <div class="settings-header">
      <h1 class="settings-title">
        <font-awesome-icon :icon="['fas', 'cog']" class="title-icon" />
        Settings
      </h1>
      <p class="settings-description">
        Customize your Daily Office experience with these prayer and liturgical options
      </p>
    </div>

    <Loading v-if="loading" />
    
    <main v-if="!loading" class="settings-main">
      <div class="settings-container">
        <!-- Advanced Settings Toggle -->
        <div class="settings-controls">
          <div class="advanced-toggle">
            <el-switch
              v-model="advanced"
              size="large"
              active-text="Show Advanced Options"
              inactive-text="Basic Settings Only"
              @change="toggleAdvanced"
            >
              <template #active-action>
                <font-awesome-icon :icon="['fas', 'cogs']" />
              </template>
              <template #inactive-action>
                <font-awesome-icon :icon="['fas', 'cog']" />
              </template>
            </el-switch>
          </div>
        </div>

        <!-- Settings Tabs -->
        <div class="settings-tabs">
          <el-tabs
            v-model="openTab"
            :tab-position="tabPosition"
            class="enhanced-tabs"
            @tab-change="toggleOffice"
          >
            <el-tab-pane name="office">
              <template #label>
                <div class="tab-label">
                  <font-awesome-icon :icon="['fas', 'book-open']" class="tab-icon" />
                  <span>Daily Office</span>
                </div>
              </template>
              <div class="tab-content">
                <div class="tab-description">
                  <h3>Daily Office Settings</h3>
                  <p>Configure options for Morning Prayer, Midday Prayer, Evening Prayer, and Compline</p>
                </div>
                <SettingsPanel
                  :available-settings="availableSettings"
                  site="Daily Office"
                  name="Daily Office Settings"
                  :advanced="advanced"
                />
              </div>
            </el-tab-pane>
            <el-tab-pane name="family">
              <template #label>
                <div class="tab-label">
                  <font-awesome-icon :icon="['fas', 'users']" class="tab-icon" />
                  <span>Family Prayer</span>
                </div>
              </template>
              <div class="tab-content">
                <div class="tab-description">
                  <h3>Family Prayer Settings</h3>
                  <p>Shorter, family-friendly prayer services suitable for households with children</p>
                </div>
                <SettingsPanel
                  :available-settings="availableSettings"
                  site="Family Prayer"
                  name="Family Prayer Settings"
                  :advanced="advanced"
                />
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </main>
  </div>

  <!-- Bottom Drawer (keeping original functionality) -->
  <el-drawer
    v-model="drawerOpen"
    modal-class="pointer-events-none"
    direction="btt"
    :close-on-click-modal="false"
    :lock-scroll="false"
    :close-on-press-escape="false"
    :show-close="false"
    :with-header="false"
    size="auto"
    :modal="false"
    :z-index="100"
  >
    <div class="drawer-header" @click="toggleBottomPanel">
      <font-awesome-icon :icon="['fas', 'chevron-up']" class="drawer-icon" />
      <span>Show/Hide Settings</span>
      <span class="drawer-toggle">
        <font-awesome-icon 
          :icon="drawerOpen ? ['fas', 'chevron-down'] : ['fas', 'chevron-up']" 
        />
      </span>
    </div>
    <div v-if="bottomPanelExpanded" class="drawer-content">
      <div class="drawer-controls">
        <div class="control-group">
          <span class="control-label">Daily Office</span>
          <el-switch
            v-model="openTab"
            active-value="family"
            inactive-value="office"
            @change="toggleOffice"
          />
          <span class="control-label">Family Prayer</span>
        </div>
        <div class="control-group">
          <span class="control-label">Basic</span>
          <el-switch
            v-model="advanced"
            @change="toggleAdvanced"
          />
          <span class="control-label">Advanced</span>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script>
// @ is an alias to /src

// @ is an alias to /src
import Loading from '@/components/Loading.vue';
import SettingsPanel from '@/components/SettingsPanel.vue';
import { DynamicStorage } from '@/helpers/storage';

export default {
  name: 'Settings',
  components: {
    Loading,
    SettingsPanel,
  },
  data() {
    return {
      counter: 0,
      availableSettings: null,
      familyPrayerSettings: null,
      dailyOfficeSettings: null,
      loading: true,
      windowWidth: 0,
      drawerOpen: true,
      advanced: false,
      openTab: 'office',
      bottomPanelExpanded: true,
    };
  },
  computed: {
    // a computed getter
    tabPosition: function () {
      return 'top';
      // return this.windowWidth > 780 ? "left" : "top";
    },
  },
  async mounted() {
    await this.initialize();
  },
  unmounted() {
    window.removeEventListener('resize', () => {
      this.windowWidth = window.innerWidth;
    });
  },
  methods: {
    async initialize() {
      this.loading = true;
      this.windowWidth = window.innerWidth;
      window.addEventListener('resize', () => {
        this.windowWidth = window.innerWidth;
      });
      this.availableSettings = await this.$store.state.availableSettings;
      await this.$store.dispatch('initializeSettings');
      const settings = await this.$store.state.settings;
      if (this.availableSettings) {
        this.availableSettings.forEach((setting, i) => {
          const name = setting.name;
          this.availableSettings[i].active = settings[name];
        });

        this.dailyOfficeSettings = this.availableSettings.filter(
          (setting) => setting.site_name == 'Daily Office'
        );
        this.familyPrayerSettings = this.availableSettings.filter(
          (setting) => setting.site_name == 'Family Prayer'
        );
      }
      if (await DynamicStorage.getItem('advancedSettings')) {
        const stored = await DynamicStorage.getItem('advancedSettings');
        this.advanced = stored == 'true' ? true : false;
      } else {
        await DynamicStorage.setItem('advancedSettings', false);
      }
      if (await DynamicStorage.getItem('settingsPane')) {
        const stored = await DynamicStorage.getItem('settingsPane');
        if (stored) {
          this.openTab = stored;
        } else {
          await DynamicStorage.setItem('settingsPane', 'office');
        }
      }
      this.loading = false;
    },
    async toggleAdvanced(value) {
      await DynamicStorage.setItem('advancedSettings', value);
    },
    async toggleOffice(value) {
      this.openTab = value;
      await DynamicStorage.setItem('settingsPane', value);
    },
    toggleBottomPanel() {
      this.bottomPanelExpanded = !this.bottomPanelExpanded;
    },
  },
};
</script>

<style lang="scss">
[v-cloak] {
  display: none;
}

.pointer-events-none {
  pointer-events: none;
}

.el-drawer {
  pointer-events: auto;
}

// Settings Page Styles
.settings-page {
  min-height: 100vh;
  background: linear-gradient(
    180deg,
    var(--color-bg) 0%,
    var(--el-fill-color-lighter) 100%
  );
}

.settings-header {
  text-align: center;
  padding: 2rem 1rem;
  background: var(--color-bg);
  border-bottom: 1px solid var(--el-border-color-lighter);
  position: relative;
  
  // Book-like paper texture
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      45deg,
      transparent 0%,
      rgba(255, 255, 255, 0.02) 25%,
      transparent 50%,
      rgba(0, 0, 0, 0.01) 100%
    );
    pointer-events: none;
  }
}

.settings-title {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 2.5rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--font-color);
  margin: 0 0 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  
  @media (max-width: 768px) {
    font-size: 2rem;
  }
  
  @media (max-width: 480px) {
    font-size: 1.75rem;
    flex-direction: column;
    gap: 0.5rem;
  }
}

.title-icon {
  opacity: 0.8;
  
  @media (max-width: 480px) {
    font-size: 1.5rem;
  }
}

.settings-description {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1.125rem;
  color: var(--el-text-color-regular);
  margin: 0;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
  
  @media (max-width: 480px) {
    font-size: 1rem;
  }
}

.settings-main {
  padding: 2rem 1rem;
}

.settings-container {
  max-width: 1200px;
  margin: 0 auto;
}

.settings-controls {
  margin-bottom: 2rem;
  display: flex;
  justify-content: center;
}

.advanced-toggle {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  
  .el-switch {
    --el-switch-on-color: var(--el-color-primary);
    --el-switch-off-color: var(--el-fill-color);
    
    .el-switch__label {
      font-family: 'Adobe Caslon Pro', serif;
      font-weight: 600;
      letter-spacing: 0.025em;
    }
  }
}

.settings-tabs {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.enhanced-tabs {
  .el-tabs__header {
    background: var(--el-fill-color-lighter);
    margin: 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
  }
  
  .el-tabs__nav-wrap {
    padding: 0;
  }
  
  .el-tabs__item {
    font-family: 'Adobe Caslon Pro', serif;
    font-weight: 600;
    letter-spacing: 0.025em;
    padding: 1rem 2rem;
    height: auto;
    line-height: 1.5;
    
    &.is-active {
      background: var(--color-bg);
      border-bottom: 3px solid var(--el-color-primary);
    }
    
    &:hover:not(.is-active) {
      background: var(--el-fill-color-light);
    }
  }
  
  .el-tabs__content {
    padding: 0;
  }
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  @media (max-width: 640px) {
    flex-direction: column;
    gap: 0.25rem;
  }
}

.tab-icon {
  font-size: 1.125rem;
  opacity: 0.8;
  
  @media (max-width: 640px) {
    font-size: 1rem;
  }
}

.tab-content {
  padding: 2rem;
  
  @media (max-width: 640px) {
    padding: 1.5rem;
  }
}

.tab-description {
  text-align: center;
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--el-border-color-lighter);
  
  h3 {
    font-family: 'Adobe Caslon Pro', serif;
    font-size: 1.5rem;
    font-weight: 600;
    letter-spacing: 0.025em;
    color: var(--font-color);
    margin: 0 0 0.5rem;
  }
  
  p {
    font-size: 1rem;
    color: var(--el-text-color-regular);
    margin: 0;
    line-height: 1.6;
  }
}

// Bottom Drawer Styles
.drawer-header {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px 12px 0 0;
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: 'Adobe Caslon Pro', serif;
  font-weight: 600;
  letter-spacing: 0.025em;
  
  &:hover {
    background: var(--el-fill-color-light);
  }
}

.drawer-icon {
  opacity: 0.7;
}

.drawer-toggle {
  opacity: 0.5;
  transition: transform 0.2s ease;
  
  .drawer-header:hover & {
    opacity: 0.8;
    transform: scale(1.1);
  }
}

.drawer-content {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-top: none;
  padding: 1.5rem;
}

.drawer-controls {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: center;
  
  @media (min-width: 640px) {
    flex-direction: row;
    justify-content: center;
    gap: 3rem;
  }
}

.control-group {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.control-label {
  font-family: 'Adobe Caslon Pro', serif;
  font-weight: 600;
  font-size: 0.875rem;
  letter-spacing: 0.025em;
  color: var(--el-text-color-regular);
  text-transform: uppercase;
}

// Dark mode adjustments
:root.dark {
  .settings-page {
    background: linear-gradient(
      180deg,
      var(--color-bg) 0%,
      rgba(255, 255, 255, 0.02) 100%
    );
  }
  
  .settings-header::before {
    background: linear-gradient(
      45deg,
      transparent 0%,
      rgba(255, 255, 255, 0.01) 25%,
      transparent 50%,
      rgba(0, 0, 0, 0.02) 100%
    );
  }
  
  .advanced-toggle,
  .settings-tabs,
  .drawer-header,
  .drawer-content {
    box-shadow: 
      0 4px 16px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
}

// Responsive adjustments
@media (max-width: 768px) {
  .settings-header {
    padding: 1.5rem 1rem;
  }
  
  .settings-main {
    padding: 1.5rem 0.75rem;
  }
  
  .advanced-toggle {
    padding: 0.75rem 1rem;
  }
  
  .enhanced-tabs .el-tabs__item {
    padding: 0.75rem 1rem;
  }
}

@media (max-width: 480px) {
  .settings-controls {
    margin-bottom: 1.5rem;
  }
  
  .tab-description {
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    
    h3 {
      font-size: 1.25rem;
    }
    
    p {
      font-size: 0.875rem;
    }
  }
}
</style>
