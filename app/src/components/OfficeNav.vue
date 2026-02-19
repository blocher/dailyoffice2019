<template>
  <div class="office-nav max-w-xl mx-auto space-y-4 mb-8">
    <!-- Mode Switcher -->
    <div
      class="flex items-center justify-between bg-gray-50 p-3 rounded-lg border border-gray-100 shadow-sm"
    >
      <div class="text-sm font-medium text-gray-700">
        <span v-if="currentServiceType === 'office'">Daily Office Mode</span>
        <span v-else>Family Prayer Mode</span>
      </div>
      <button
        @click.stop.prevent="toggleServiceType"
        class="text-xs text-indigo-600 font-semibold hover:text-indigo-800 transition-colors uppercase tracking-wide border border-indigo-200 rounded px-2 py-1 hover:bg-indigo-50"
      >
        Switch Mode
      </button>
    </div>

    <!-- Main Office Links Grid -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
      <router-link
        v-for="link in links"
        :key="link.name"
        :to="link.to"
        class="group"
      >
        <div
          class="h-full bg-white border rounded-xl p-3 flex flex-col items-center justify-center transition-all duration-200 shadow-sm hover:shadow-md hover:border-indigo-300"
          :class="selectedClass(link.name)"
        >
          <div
            class="text-xl mb-2 text-gray-500 group-hover:text-indigo-600 transition-colors"
          >
            <font-awesome-icon :icon="link.icon" />
          </div>
          <p
            class="text-xs font-semibold text-gray-700 leading-tight"
            v-html="link.text"
          ></p>
        </div>
      </router-link>
    </div>

    <!-- Readings Link -->
    <div v-if="readingsLink">
      <router-link :to="readingsLink.to" class="block group">
        <div
          class="bg-white border rounded-xl p-3 flex items-center justify-center gap-3 transition-all duration-200 shadow-sm hover:shadow-md hover:border-indigo-300"
          :class="selectedClass(readingsLink.name)"
        >
          <font-awesome-icon
            :icon="readingsLink.icon"
            class="text-indigo-500"
          />
          <span
            class="text-sm font-semibold text-gray-700"
            v-html="readingsLink.text"
          ></span>
        </div>
      </router-link>
    </div>

    <!-- Day Navigation -->
    <div class="grid grid-cols-3 gap-3 pt-2">
      <router-link
        v-for="link in dayLinks"
        :key="link.text"
        :to="link.to"
        :v-on:click="scrollToTop"
        class="block"
      >
        <div
          class="h-full bg-white border border-gray-200 rounded-lg p-2 flex flex-col sm:flex-row items-center justify-center text-center gap-2 hover:bg-gray-50 transition-colors"
          :class="{
            'bg-indigo-50 border-indigo-200 text-indigo-700': link.selected,
          }"
        >
          <font-awesome-icon
            v-if="link.icon === 'left'"
            :icon="['fad', 'left']"
            class="text-gray-400"
          />
          <span class="text-xs font-medium">{{ link.text }}</span>
          <font-awesome-icon
            v-if="link.icon === 'right'"
            :icon="['fad', 'right']"
            class="text-gray-400"
          />
        </div>
      </router-link>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src

import { DynamicStorage } from '@/helpers/storage';

export default {
  name: 'OfficeNav',
  components: {},
  props: {
    calendarDate: {
      type: Date,
    },
    selectedOffice: {
      type: String,
    },
    serviceType: {
      default: 'office',
      type: String,
    },
  },
  data() {
    return {
      links: null,
      dayLink: null,
      readingsLink: null, // Add to data to prevent reactivity issues
      dailyLinks: [], // Store options
      familyLinks: [], // Store options
      dayLinks: [], // Add to data
      currentServiceType: this.serviceType,
    };
  },
  async created() {
    const tomorrow = new Date(this.calendarDate);
    tomorrow.setDate(this.calendarDate.getDate() + 1);
    const yesterday = new Date(this.calendarDate);
    yesterday.setDate(this.calendarDate.getDate() - 1);
    this.dailyLinks = [
      {
        to: `/morning_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Morning',
        name: 'morning_prayer',
        icon: ['fad', 'sunrise'],
      },
      {
        to: `/midday_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Midday',
        name: 'midday_prayer',
        icon: ['fad', 'sun'],
      },
      {
        to: `/evening_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Evening',
        name: 'evening_prayer',
        icon: ['fad', 'sunset'],
      },
      {
        to: `/compline/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Compline',
        name: 'compline',
        icon: ['fad', 'moon-stars'],
      },
    ];
    this.readingsLink = {
      to: `/readings/${this.calendarDate.getFullYear()}/${
        this.calendarDate.getMonth() + 1
      }/${this.calendarDate.getDate()}`,
      text: "Day's Readings",
      name: 'readings',
      icon: ['fad', 'book-bible'],
    };
    this.familyLinks = [
      {
        to: `/family/morning_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Morning',
        name: 'morning_prayer',
        icon: ['fad', 'sunrise'],
      },
      {
        to: `/family/midday_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Midday',
        name: 'midday_prayer',
        icon: ['fad', 'sun'],
      },
      {
        to: `/family/early_evening_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Early Evening',
        name: 'early_evening_prayer',
        icon: ['fad', 'sunset'],
      },
      {
        to: `/family/close_of_day_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Close of Day',
        name: 'close_of_day_prayer',
        icon: ['fad', 'moon-stars'],
      },
    ];
    if (this.currentServiceType === 'family') {
      this.links = this.familyLinks;
    } else {
      this.links = this.dailyLinks;
    }
    const servicePart =
      this.currentServiceType === 'family' ? `/${this.currentServiceType}` : '';
    this.dayLinks = [
      {
        to: `${servicePart}/${this.selectedOffice}/${yesterday.getFullYear()}/${
          yesterday.getMonth() + 1
        }/${yesterday.getDate()}`,
        text: 'Yesterday',
        icon: 'left',
        selected: false,
      },
      {
        to: `${servicePart}/${this.selectedOffice}/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Today',
        icon: '',
        selected: true,
      },
      {
        to: `${servicePart}/${this.selectedOffice}/${tomorrow.getFullYear()}/${
          tomorrow.getMonth() + 1
        }/${tomorrow.getDate()}`,
        text: 'Tomorrow',
        icon: 'right',
        selected: false,
      },
    ];
  },
  methods: {
    selectedClass(name) {
      if (this.selectedOffice === name) {
        return 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-200';
      }
      return 'border-gray-200 hover:border-indigo-300';
    },
    hoverClass(name) {
      // Not used with new tailwind classes, but kept for compatibility if needed
      if (this.selectedOffice === name) {
        return 'always';
      }
      return 'hover';
    },
    redirectToDaily() {
      if (this.selectedOffice) {
        const lookup = {
          morning_prayer: 'morning_prayer',
          midday_prayer: 'midday_prayer',
          early_evening_prayer: 'evening_prayer',
          close_of_day_prayer: 'compline',
        };
        const new_office = lookup[this.selectedOffice];
        if (new_office) {
          this.$router.push(
            `/office/${new_office}/${this.calendarDate.getFullYear()}/${
              this.calendarDate.getMonth() + 1
            }/${this.calendarDate.getDate()}`
          );
        }
      }
    },
    redirectToFamily() {
      if (this.selectedOffice) {
        const lookup = {
          morning_prayer: 'morning_prayer',
          midday_prayer: 'midday_prayer',
          evening_prayer: 'early_evening_prayer',
          compline: 'close_of_day_prayer',
        };
        const new_office = lookup[this.selectedOffice];
        if (new_office) {
          this.$router.push(
            `/family/${new_office}/${this.calendarDate.getFullYear()}/${
              this.calendarDate.getMonth() + 1
            }/${this.calendarDate.getDate()}`
          );
        }
      }
    },
    async toggleServiceType() {
      if (this.currentServiceType === 'family') {
        this.currentServiceType = 'office';
        this.links = this.dailyLinks;
        await DynamicStorage.setItem('serviceType', 'office');
        this.redirectToDaily();
      } else {
        this.currentServiceType = 'family';
        await DynamicStorage.setItem('serviceType', 'family');
        this.links = this.familyLinks;
        this.redirectToFamily();
      }
    },
    scrollToTop() {
      window.scrollTo(0, 0);
    },
  },
};
</script>

<style scoped>
/* Scoped styles replaced by Tailwind classes */
</style>
