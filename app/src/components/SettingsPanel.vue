<template>
  <div class="settings-panel">
    <div v-for="setting in availableSettings" :key="setting.uuid" class="setting-group">
      <RadioGroup
        v-if="showSetting(setting)"
        v-model="setting.active"
        class="setting-section"
        @click="changeSetting"
      >
        <div class="setting-header">
          <RadioGroupLabel class="setting-title">
            <div class="title-content">
              <font-awesome-icon 
                :icon="getSettingIcon(setting)" 
                class="setting-icon" 
              />
              <span>{{ setting.title }}</span>
              <el-tag 
                v-if="setting.setting_type == 2" 
                type="info"
                size="small"
                class="minor-tag"
              >
                Advanced
              </el-tag>
            </div>
          </RadioGroupLabel>
          <RadioGroupLabel
            class="setting-description"
            v-html="setting.description"
          />
        </div>

        <div class="setting-options">
          <RadioGroupOption
            v-for="(option, optionIdx) in setting.options"
            :key="option.uuid"
            v-slot="{ checked, active }"
            as="template"
            :value="option.value"
          >
            <div
              :class="[
                'option-card',
                {
                  'first': optionIdx === 0,
                  'last': optionIdx === setting.options.length - 1,
                  'selected': checked,
                  'focused': active
                }
              ]"
            >
              <div class="option-indicator">
                <span
                  :class="[
                    'radio-button',
                    { 'checked': checked, 'focused': active }
                  ]"
                  aria-hidden="true"
                >
                  <span class="radio-dot" />
                </span>
              </div>
              <div class="option-content">
                <RadioGroupLabel
                  as="div"
                  class="option-title"
                >
                  {{ option.name }}
                </RadioGroupLabel>
                <RadioGroupDescription
                  as="div"
                  class="option-description"
                  v-html="option.description"
                />
              </div>
              <div v-if="checked" class="selected-indicator">
                <font-awesome-icon :icon="['fas', 'check']" />
              </div>
            </div>
          </RadioGroupOption>
        </div>
      </RadioGroup>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src

import {
  RadioGroup,
  RadioGroupDescription,
  RadioGroupLabel,
  RadioGroupOption,
} from '@headlessui/vue';
import { ElMessage } from 'element-plus';
import { getMessageOffset } from '@/helpers/getMessageOffest';

export default {
  name: 'SettingsPanel',
  components: {
    RadioGroup,
    RadioGroupDescription,
    RadioGroupLabel,
    RadioGroupOption,
  },
  props: ['availableSettings', 'site', 'name', 'advanced'],
  methods: {
    async changeSetting() {
      const settings = await this.$store.state.settings;
      if (this.availableSettings) {
        this.availableSettings.forEach((setting) => {
          if (setting.active) {
            const name = setting.name;
            const value = setting.active;
            settings[name] = value;
          }
        });
      }
      await this.$store.commit('saveSettings', settings);
      return ElMessage.success({
        title: 'Saved',
        message: 'Your setting has been saved.',
        showClose: true,
        offset: getMessageOffset(),
      });
    },
    showSetting(setting) {
      const correct_site = setting.site_name == this.site;
      const show_advanced = setting.setting_type == 1 || this.advanced;
      return correct_site && show_advanced;
    },
    getSettingIcon(setting) {
      // Return appropriate icons based on setting type or name
      if (setting.name?.includes('bible') || setting.name?.includes('translation')) {
        return ['fas', 'book-bible'];
      } else if (setting.name?.includes('psalm')) {
        return ['fas', 'music'];
      } else if (setting.name?.includes('canticle')) {
        return ['fas', 'scroll'];
      } else if (setting.name?.includes('prayer') || setting.name?.includes('collect')) {
        return ['fas', 'praying-hands'];
      } else if (setting.name?.includes('reading') || setting.name?.includes('lesson')) {
        return ['fas', 'book-open'];
      } else if (setting.name?.includes('time') || setting.name?.includes('date')) {
        return ['fas', 'clock'];
      } else if (setting.name?.includes('language') || setting.name?.includes('version')) {
        return ['fas', 'language'];
      } else if (setting.name?.includes('audio') || setting.name?.includes('sound')) {
        return ['fas', 'volume-up'];
      } else {
        return ['fas', 'cog'];
      }
    },
  },
};
</script>

<style lang="scss" scoped>
.settings-panel {
  max-width: 800px;
  margin: 0 auto;
}

.setting-group {
  margin-bottom: 3rem;
  
  &:last-child {
    margin-bottom: 0;
  }
}

.setting-section {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  
  // Book-like styling
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.02) 0%,
      transparent 50%,
      rgba(0, 0, 0, 0.01) 100%
    );
    border-radius: 12px;
    pointer-events: none;
    z-index: 1;
  }
}

.setting-header {
  background: var(--el-fill-color-lighter);
  padding: 1.5rem;
  border-bottom: 1px solid var(--el-border-color-lighter);
  position: relative;
  z-index: 2;
}

.setting-title {
  margin: 0 0 1rem;
  cursor: default;
}

.title-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.setting-icon {
  font-size: 1.25rem;
  opacity: 0.8;
  color: var(--el-color-primary);
}

.title-content span {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: 0.025em;
  color: var(--font-color);
  
  @media (max-width: 480px) {
    font-size: 1.125rem;
  }
}

.minor-tag {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.setting-description {
  font-size: 0.875rem;
  color: var(--el-text-color-regular);
  line-height: 1.6;
  margin: 0;
  cursor: default;
  
  @media (max-width: 480px) {
    font-size: 0.8125rem;
  }
}

.setting-options {
  position: relative;
  z-index: 2;
}

.option-card {
  background: var(--color-bg);
  border-bottom: 1px solid var(--el-border-color-lighter);
  padding: 1.25rem;
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  
  &:last-child {
    border-bottom: none;
  }
  
  &:hover {
    background: var(--el-fill-color-light);
    transform: translateX(2px);
  }
  
  &.selected {
    background: linear-gradient(
      90deg,
      var(--el-color-primary-light-9) 0%,
      var(--el-color-primary-light-8) 100%
    );
    border-left: 4px solid var(--el-color-primary);
    padding-left: calc(1.25rem - 4px);
    
    &:hover {
      background: linear-gradient(
        90deg,
        var(--el-color-primary-light-8) 0%,
        var(--el-color-primary-light-7) 100%
      );
    }
  }
  
  &.focused {
    outline: 2px solid var(--el-color-primary);
    outline-offset: -2px;
  }
  
  @media (max-width: 640px) {
    padding: 1rem;
    gap: 0.75rem;
    
    &.selected {
      padding-left: calc(1rem - 4px);
    }
  }
}

.option-indicator {
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.radio-button {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--el-border-color);
  background: var(--color-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  position: relative;
  
  &.checked {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary);
    box-shadow: 0 0 0 2px var(--el-color-primary-light-8);
  }
  
  &.focused {
    box-shadow: 0 0 0 3px var(--el-color-primary-light-7);
  }
}

.radio-dot {
  width: 8px;
  height: 8px;
  background: white;
  border-radius: 50%;
  transform: scale(0);
  transition: transform 0.15s ease;
  
  .checked & {
    transform: scale(1);
  }
}

.option-content {
  flex: 1;
  min-width: 0;
}

.option-title {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.025em;
  color: var(--font-color);
  margin: 0 0 0.5rem;
  
  .selected & {
    color: var(--el-color-primary);
  }
  
  @media (max-width: 480px) {
    font-size: 0.875rem;
  }
}

.option-description {
  font-size: 0.875rem;
  color: var(--el-text-color-regular);
  line-height: 1.5;
  margin: 0;
  
  .selected & {
    color: var(--el-text-color-primary);
  }
  
  @media (max-width: 480px) {
    font-size: 0.8125rem;
  }
}

.selected-indicator {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  background: var(--el-color-success);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  animation: checkmark-appear 0.3s ease;
}

@keyframes checkmark-appear {
  0% {
    transform: scale(0) rotate(180deg);
    opacity: 0;
  }
  100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
}

// Dark mode adjustments
:root.dark {
  .setting-section {
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    
    &::before {
      background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.01) 0%,
        transparent 50%,
        rgba(0, 0, 0, 0.02) 100%
      );
    }
  }
  
  .option-card {
    &:hover {
      background: rgba(255, 255, 255, 0.05);
    }
    
    &.selected {
      background: linear-gradient(
        90deg,
        rgba(64, 158, 255, 0.1) 0%,
        rgba(64, 158, 255, 0.05) 100%
      );
      
      &:hover {
        background: linear-gradient(
          90deg,
          rgba(64, 158, 255, 0.15) 0%,
          rgba(64, 158, 255, 0.08) 100%
        );
      }
    }
  }
  
  .radio-button {
    border-color: rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.1);
    
    &.checked {
      border-color: var(--el-color-primary);
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
    }
  }
}

// Responsive adjustments
@media (max-width: 640px) {
  .setting-header {
    padding: 1.25rem;
  }
  
  .settings-panel {
    padding: 0 0.5rem;
  }
  
  .setting-group {
    margin-bottom: 2rem;
  }
  
  .title-content {
    gap: 0.5rem;
  }
}

@media (max-width: 480px) {
  .title-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .setting-icon {
    font-size: 1.125rem;
  }
}
</style>

<style>
.selected-text {
  color: var(--font-on-white-background);
}
</style>
