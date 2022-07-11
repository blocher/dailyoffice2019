<!--
  This example requires Tailwind CSS v2.0+

  This example requires some changes to your config:

  ```
  // tailwind.config.js
  module.exports = {
    // ...
    plugins: [
      // ...
      require('@tailwindcss/forms'),
    ],
  }
  ```
-->
<template>
  <div class="themed-background">
    <!-- Mobile filter dialog -->
    <Dialog as="div" class="relative z-40 sm:hidden" :open="open" @close="open = false">


      <div class="fixed inset-0 flex z-40">

        <DialogPanel
            class="ml-auto relative max-w-xs w-full h-full themed-background shadow-xl py-4 pb-12 flex flex-col overflow-y-auto">
          <div class="px-4 flex items-center justify-between">
            <h2 class="text-lg font-medium text-themed-500">Filters</h2>
            <button
                type="button"
                class="-mr-2 w-10 h-10 themed-background p-2 rounded-md flex items-center justify-center text-themed-400"
                @click="open = false">
              <span class="sr-only">Close menu</span>
              <XIcon class="h-6 w-6" aria-hidden="true"/>
            </button>
          </div>

          <!-- Filters -->
          <form class="mt-4">
            <Disclosure
                v-for="section in filters" :key="section.name" v-slot="{ open }"
                as="div" class="border-t border-gray-200 px-4 py-6">
              <h3 class="-mx-2 -my-3 flow-root">
                <DisclosureButton
                    class="px-2 py-3 themed-background w-full flex items-center justify-between text-sm text-themed-400">
                      <span class="font-medium text-themed-500">
                        {{ section.name }}
                      </span>
                  <span class="ml-6 flex items-center">
                        <ChevronDownIcon
                            :class="[open ? '-rotate-180' : 'rotate-0', 'h-5 w-5 transform']"
                            aria-hidden="true"/>
                      </span>
                </DisclosureButton>
              </h3>
              <DisclosurePanel class="pt-6">
                <div class="space-y-6">
                  <div
                      v-for="(option, optionIdx) in section.options" :key="option.value"
                      class="flex items-center">
                    <input
                        :id="`filter-mobile-${section.id}-${optionIdx}`" :name="`${section.id}[]`"
                        :value="option.value" type="checkbox" :checked="option.checked"
                        class="h-4 w-4 border-gray-300 rounded text-indigo-600 focus:ring-indigo-500"/>
                    <label :for="`filter-mobile-${section.id}-${optionIdx}`" class="ml-3 text-sm text-themed-500">
                      {{ option.label }}
                    </label>
                  </div>
                </div>
              </DisclosurePanel>
            </Disclosure>
          </form>
        </DialogPanel>
      </div>
    </Dialog>


    <!-- Filters -->
    <section aria-labelledby="filter-heading">
      <h2 id="filter-heading" class="sr-only">Filters</h2>

      <div class="themed-background border-b border-gray-200 pb-4 full-width">
        <div class="mx-auto px-4 flex basis-full items-center justify-center sm:px-6 lg:px-8 ful-width">

          <button
              type="button" class="inline-block text-sm font-medium text-themed-500 hover:text-themed-500 sm:hidden"
              @click="open = true">Filters
          </button>

          <div class="hidden sm:block">
            <div class="flow-root">
              <PopoverGroup class="-mx-4 flex items-center divide-x divide-gray-200 overflow-visible">
                <Popover
                    v-for="(section) in filters" :key="section.id"
                    class="px-4 relative inline-block text-center overflow-visible">
                  <PopoverButton
                      class="group inline-flex justify-center text-sm font-medium text-themed-500 hover:text-themed-500">
                    <span>{{ section.name }}</span>
                    <span
                        v-if="sectionCount(section.id) > 0"
                        class="ml-1.5 rounded py-0.5 px-1.5 bg-themed-200 text-xs font-semibold text-themed-500 tabular-nums">{{
                        sectionCount(section.id)
                      }}</span>
                    <ChevronDownIcon
                        class="flex-shrink-0 -mr-1 ml-1 h-5 w-5 text-themed-400 group-hover:text-themed-500"
                        aria-hidden="true"/>
                  </PopoverButton>

                  <PopoverPanel
                      class="origin-top-right absolute right-0 mt-2 themed-background rounded-md shadow-2xl p-4 ring-1 ring-black ring-opacity-5 focus:outline-none overflow-visible">
                    <form class="space-y-4">
                      <div
                          v-for="(option, optionIdx) in section.options" :key="option.value"
                          class="flex items-center">
                        <input
                            :id="`filter-${section.id}-${optionIdx}`" :name="`${section.id}[]`"
                            :value="option.value" type="checkbox" :checked="isChecked(option.value)"
                            class="h-4 w-4 border-gray-300 rounded text-indigo-600 focus:ring-indigo-500"
                            @change="setSelectedCategory($event)"/>
                        <label
                            :for="`filter-${section.id}-${optionIdx}`"
                            class="ml-3 pr-6 text-sm font-medium text-themed-500 whitespace-nowrap">
                          {{ option.label }}
                        </label>
                      </div>
                    </form>
                  </PopoverPanel>
                </Popover>
              </PopoverGroup>
            </div>
          </div>
        </div>
      </div>

      <!-- Active filters -->
      <!--      <div class="bg-gray-100">-->
      <!--        <div class="max-w-7xl mx-auto py-3 px-4 sm:flex sm:items-center sm:px-6 lg:px-8">-->
      <!--          <h3 class="text-xs font-semibold uppercase tracking-wide text-themed-500">-->
      <!--            Filters-->
      <!--            <span class="sr-only">, active</span>-->
      <!--          </h3>-->

      <!--          <div aria-hidden="true" class="hidden w-px h-5 bg-gray-300 sm:block sm:ml-4"/>-->

      <!--          <div class="mt-2 sm:mt-0 sm:ml-4">-->
      <!--            <div class="-m-1 flex flex-wrap items-center">-->
      <!--              <span-->
      <!--                  v-for="activeFilter in activeFilters" :key="activeFilter.value"-->
      <!--                  class="m-1 inline-flex rounded-full border border-gray-200 items-center py-1.5 pl-3 pr-2 text-sm font-medium themed-background text-themed-500">-->
      <!--                <span>{{ activeFilter.label }}</span>-->
      <!--                <button-->
      <!--                    type="button"-->
      <!--                    class="flex-shrink-0 ml-1 h-4 w-4 p-1 rounded-full inline-flex text-themed-400 hover:bg-themed-200 hover:text-themed-500">-->
      <!--                  <span class="sr-only">Remove filter for {{ activeFilter.label }}</span>-->
      <!--                  <svg class="h-2 w-2" stroke="currentColor" fill="none" viewBox="0 0 8 8">-->
      <!--                    <path stroke-linecap="round" stroke-width="1.5" d="M1 1l6 6m0-6L1 7"/>-->
      <!--                  </svg>-->
      <!--                </button>-->
      <!--              </span>-->
      <!--            </div>-->
      <!--          </div>-->
      <!--        </div>-->
      <!--      </div>-->
    </section>
  </div>
</template>

<script setup>


const activeFilters = [{value: 'objects', label: 'Objects'}]

const open = ref(false)
</script>

<script>


import {ref} from 'vue'
import {
  Dialog,
  DialogPanel,
  Disclosure,
  DisclosureButton,
  DisclosurePanel,
  Menu,
  MenuButton,
  MenuItem,
  MenuItems,
  Popover,
  PopoverButton,
  PopoverGroup,
  PopoverPanel,
  TransitionChild,
  TransitionRoot,
} from '@headlessui/vue'
import {XIcon} from '@heroicons/vue/outline'
import {ChevronDownIcon} from '@heroicons/vue/solid'

export default {
  components: {
    // eslint-disable-next-line vue/no-reserved-component-names
    Dialog,
    DialogPanel,
    Disclosure,
    DisclosureButton,
    DisclosurePanel,
    // eslint-disable-next-line vue/no-reserved-component-names
    Menu,
    MenuButton,
    MenuItem,
    MenuItems,
    Popover,
    PopoverButton,
    PopoverGroup,
    PopoverPanel,
    TransitionChild,
    TransitionRoot,
    XIcon,
    ChevronDownIcon
  },
  props: {
    filters: {
      type: Array,
      required: true,
    },
    // activeFilters: {
    //   type: Array,
    //   required: true,
    // },
  },
  data() {
    return {
      show: true,
      selectedCategories: [],
    };
  },
  async created() {

  },
  methods: {
    setSelectedCategory: function (event) {
      const checked = event.target.checked
      const value = event.target.value
      if (checked) {
        this.selectedCategories.push(value)
      } else {
        this.selectedCategories = this.selectedCategories.filter(category => category !== value)
      }
      this.$emit('update:activeFilters', this.selectedCategories)
    },
    isChecked: function (uuid) {
      return this.selectedCategories.includes(uuid)
    },
    sectionCount: function (uuid) {
      console.log(uuid);
      const optionsInCategory = this.filters.filter(filter => filter.id === uuid)[0].options;
      return optionsInCategory.filter(option => this.selectedCategories.includes(option.value)).length;
    },
  },
};
</script>


<style lang="scss">

.themed-background {
  background-color: var(--color-bg);
}


.text-themed-400 {
  font-weight: 400;
  color: var(--font-color)
}

.text-themed-500 {
  font-weight: 500;
  color: var(--font-color)
}

.bg-themed-200 {
  font-weight: 900;
  color: var(--el-color-info);
  background-color: var(--el-color-info-light-9);
  border-color: var(--el-color-info-light-8);
  border-width: 3px;
}

</style>
