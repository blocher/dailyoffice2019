<template>
  <div class="home">
    <h1>Settings</h1>
    <Loading v-if="loading" />
    <main
      v-if="!loading"
      v-cloak
      class="max-w-lg mx-auto pt-10 pb-12 px-4 lg:pb-16"
    >
      <form>
        <div v-for="setting in availableSettings" v-bind:key="setting.uuid">
          <RadioGroup
            class="mt-8"
            v-model="setting.active"
            v-on:click="changeSetting"
          >
            <RadioGroupLabel class="mt-8 text-lg font-medium text-gray-900">
              {{ setting.title }}<br />
            </RadioGroupLabel>
            <RadioGroupLabel
              class="mt-8 text-xs font-medium text-gray-900"
              v-html="setting.description"
            >
            </RadioGroupLabel>

            <div class="mt-1 bg-white rounded-md shadow-sm -space-y-px">
              <RadioGroupOption
                as="template"
                v-for="(option, optionIdx) in setting.options"
                :key="option.uuid"
                :value="option.value"
                v-slot="{ checked, active }"
              >
                <div
                  :class="[
                    optionIdx === 0 ? 'rounded-tl-md rounded-tr-md' : '',
                    optionIdx === availableSettings.length - 1
                      ? 'rounded-bl-md rounded-br-md'
                      : '',
                    checked
                      ? 'bg-sky-50 border-sky-200 z-10'
                      : 'border-gray-200',
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
                    <span class="rounded-full bg-white w-1.5 h-1.5" />
                  </span>
                  <div class="ml-3 flex flex-col">
                    <RadioGroupLabel
                      as="span"
                      :class="[
                        checked ? 'text-sky-900' : 'text-gray-900',
                        'block text-sm font-medium',
                      ]"
                    >
                      {{ option.name }}
                    </RadioGroupLabel>
                    <RadioGroupDescription
                      as="span"
                      :class="[
                        checked ? 'text-sky-700' : 'text-gray-500',
                        'block text-sm',
                      ]"
                      v-html="option.description"
                    >
                    </RadioGroupDescription>
                  </div>
                </div>
              </RadioGroupOption>
            </div>
          </RadioGroup>
        </div>
      </form>
    </main>
  </div>
</template>

<style>
[v-cloak] {
  display: none;
}
</style>

<script>
// @ is an alias to /src

import {
  RadioGroup,
  RadioGroupDescription,
  RadioGroupLabel,
  RadioGroupOption,
} from "@headlessui/vue";
import Loading from "@/components/Loading";

export default {
  data() {
    return {
      counter: 0,
      availableSettings: null,
      loading: true,
    };
  },
  mounted() {
    this.loading = true;
    this.availableSettings = this.$store.state.availableSettings;
    console.log(this.availableSettings);
    const settings = this.$store.state.settings;
    this.availableSettings.forEach((setting, i) => {
      const name = setting.name;
      this.availableSettings[i].active = settings[name];
    });
    this.loading = false;
  },

  name: "Settings",
  components: {
    RadioGroup,
    RadioGroupDescription,
    RadioGroupLabel,
    RadioGroupOption,
    Loading,
  },
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
    },
  },
};
</script>
