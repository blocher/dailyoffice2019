<template>
  <form>
    <div
        v-for="setting in availableSettings" :key="setting.uuid"
    >
      <RadioGroup
          v-if="showSetting(setting)"
          v-model="setting.active"
          class="mt-8"
          @click="changeSetting"
      >
        <RadioGroupLabel class="mt-8 text-lg font-medium">
          {{ setting.title }}
          <el-tag v-if="setting.setting_type == 2"> Minor Setting</el-tag>
          <br>
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
                checked ? 'bg-sky-50 border-sky-200 z-10' : 'border-gray-200',
                'relative border p-4 flex cursor-pointer focus:outline-none',
              ]"
            >
              <span
                  :class="[
                  checked
                    ? 'bg-sky-600 border-transparent'
                    : 'bg-white border-gray-300',
                  active ? 'ring-2 ring-offset-2 ring-sky-500' : '',
                  'h-4 w-4 mt-0.5 cursor-pointer rounded-full border flex items-center justify-center',
                ]"
                  aria-hidden="true"
              >
                <span class="rounded-full bg-white w-1.5 h-1.5"/>
              </span>
              <div class="ml-3 flex flex-col">
                <RadioGroupLabel
                    as="span"
                    :class="[
                    checked ? 'selected-text' : '',
                    'block text-sm font-medium',
                  ]"
                >
                  {{ option.name }}
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

import {RadioGroup, RadioGroupDescription, RadioGroupLabel, RadioGroupOption,} from "@headlessui/vue";
import {ElMessage} from "element-plus";

export default {
  name: "SettingsPanel",
  components: {
    RadioGroup,
    RadioGroupDescription,
    RadioGroupLabel,
    RadioGroupOption,
  },
  props: ["availableSettings", "site", "name", "advanced"],
  methods: {
    changeSetting() {
      const settings = this.$store.state.settings;
      this.availableSettings.forEach((setting) => {
        if (setting.active) {
          const name = setting.name;
          const value = setting.active;
          settings[name] = value;
        }
      });
      this.$store.commit("saveSettings", settings);
      return ElMessage.success({
        title: "Saved",
        message: "Your setting has been saved.",
        showClose: true,
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
