<template>
  <div class="home">
    <h1>Settings</h1>

    <main class="max-w-lg mx-auto pt-10 pb-12 px-4 lg:pb-16">
      <form>
        <RadioGroup
          v-bind:key="setting.uuid"
          v-for="setting in settings"
          class="mt-8"
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
              v-bind:key="option.uuid"
              :value="option"
              v-slot="{ checked, active }"
            >
              <div
                :class="[
                  optionIdx === 0 ? 'rounded-tl-md rounded-tr-md' : '',
                  optionIdx === settings.length - 1
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
      </form>
    </main>
  </div>
</template>

<script>
// @ is an alias to /src

// import { ref } from "vue";
import {
  RadioGroup,
  RadioGroupDescription,
  RadioGroupLabel,
  RadioGroupOption,
} from "@headlessui/vue";

export default {
  data() {
    return {
      counter: 0,
      settings: null,
    };
  },
  async created() {
      const settings = await this.$http.get(
        'http://127.0.0.1:8000/api/v1/available_settings/',
      );
      console.log(settings);
      this.settings = settings.data;
    },

  name: "Settings",
  components: {
    RadioGroup,
    RadioGroupDescription,
    RadioGroupLabel,
    RadioGroupOption,
  },
  mounted() {
    setInterval(() => {
      this.counter++;
    }, 1000);
  },
  // setup() {
  //   const settings = this.retrieveSettings();
  //   const selected = ref(settings[0]);
  //   return {
  //     settings,
  //     selected,
  //   };
  // },
  // methods: {
  //   async retrieveSettings () {
  //     console.log('here')
  //     return
  //   }
  // }
};
</script>
