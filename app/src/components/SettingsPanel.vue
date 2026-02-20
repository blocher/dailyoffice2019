<template>
  <form>
    <div v-for="setting in availableSettings" :key="setting.uuid">
      <RadioGroup
        v-if="showSetting(setting)"
        v-model="setting.active"
        class="mt-8"
        @click="changeSetting"
      >
        <RadioGroupLabel class="mt-8 text-lg font-medium">
          {{ setting.title }}
          <el-tag v-if="setting.setting_type == 2"> Minor Setting</el-tag>
          <br />
        </RadioGroupLabel>
        <RadioGroupLabel
          class="mt-8 text-xs font-medium"
          v-html="setting.description"
        />

        <div class="mt-1 rounded-md shadow-sm -space-y-px">
          <RadioGroupOption
            v-for="(option, optionIdx) in setting.options"
            :key="option.uuid"
            v-slot="{ checked, active }"
            as="template"
            :value="option.value"
          >
            <div
              :class="[
                optionIdx === 0 ? 'rounded-tl-md rounded-tr-md' : '',
                optionIdx === availableSettings.length - 1
                  ? 'rounded-bl-md rounded-br-md'
                  : '',
                checked
                  ? 'bg-sky-50 dark:bg-sky-900/30 border-sky-200 dark:border-sky-500/50 z-10'
                  : 'border-gray-200 dark:border-gray-600',
                'relative border p-4 flex cursor-pointer focus:outline-none',
              ]"
            >
              <span
                :class="[
                  checked
                    ? 'bg-sky-600 border-transparent'
                    : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-500',
                  active
                    ? 'ring-2 ring-offset-2 ring-sky-500 dark:ring-offset-gray-800'
                    : '',
                  'h-4 w-4 mt-0.5 cursor-pointer rounded-full border flex items-center justify-center',
                ]"
                aria-hidden="true"
              >
                <span class="rounded-full bg-white w-1.5 h-1.5" />
              </span>
              <div class="ml-3 flex flex-col">
                <RadioGroupLabel
                  as="span"
                  :class="[
                    checked ? 'selected-text' : '',
                    'block text-sm font-medium',
                  ]"
                >
                  <strong>{{ option.name }}</strong>
                </RadioGroupLabel>
                <RadioGroupDescription
                  as="span"
                  :class="[checked ? 'selected-text' : '', 'block text-sm']"
                  v-html="option.description"
                />
              </div>
            </div>
          </RadioGroupOption>
        </div>
      </RadioGroup>
    </div>
  </form>
</template>

<script>
// @ is an alias to /src

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
  },
};
</script>

<style>
.selected-text {
  color: var(--font-on-white-background);
}
</style>
