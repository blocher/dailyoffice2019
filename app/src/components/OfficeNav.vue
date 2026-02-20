<template>
  <div class="office-nav max-w-xl mx-auto space-y-4 mb-8">
    <!-- Mode Switcher -->
    <div
      class="flex items-center justify-between bg-gray-50 dark:bg-gray-800 p-3 rounded-lg border border-gray-100 dark:border-gray-700 shadow-sm"
    >
      <div class="mode-switch-meta">
        <span class="mode-switch-label">Mode</span>
        <span class="mode-switch-current">{{ currentModeLabel }}</span>
      </div>
      <button
        @click.stop.prevent="toggleServiceType"
        class="mode-switch-button font-medium rounded px-2 py-0.5 transition-colors"
        :aria-label="switchModeLabel"
      >
        {{ switchModeLabel }}
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
          class="h-full rounded-xl p-3 flex flex-col items-center justify-center transition-all duration-200 border"
          :class="selectedClass(link.name)"
        >
          <div
            class="text-xl mb-2 transition-colors"
            :class="iconClass(link.name)"
          >
            <font-awesome-icon :icon="link.icon" />
          </div>
          <p
            class="text-xs font-semibold leading-tight"
            :class="textClass(link.name)"
            v-html="link.text"
          ></p>
        </div>
      </router-link>
    </div>

    <!-- Readings Link -->
    <div v-if="readingsLink">
      <router-link :to="readingsLink.to" class="block group">
        <div
          class="rounded-xl p-3 flex items-center justify-center gap-3 transition-all duration-200 border"
          :class="selectedClass(readingsLink.name)"
        >
          <font-awesome-icon
            :icon="readingsLink.icon"
            class="transition-colors"
            :class="iconClass(readingsLink.name)"
          />
          <span
            class="text-sm font-semibold"
            :class="textClass(readingsLink.name)"
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
          class="h-full rounded-lg p-2 flex flex-col sm:flex-row items-center justify-center text-center gap-2 transition-colors border"
          :class="{
            'office-nav-selected': link.selected,
            'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700':
              !link.selected,
          }"
        >
          <font-awesome-icon
            v-if="link.icon === 'left'"
            :icon="['fad', 'left']"
            :class="
              link.selected
                ? 'office-nav-selected-icon'
                : 'text-gray-500 dark:text-gray-400'
            "
          />
          <span class="text-xs font-medium">{{ link.text }}</span>
          <font-awesome-icon
            v-if="link.icon === 'right'"
            :icon="['fad', 'right']"
            :class="
              link.selected
                ? 'office-nav-selected-icon'
                : 'text-gray-500 dark:text-gray-400'
            "
          />
        </div>
      </router-link>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src

// @ is an alias to /src
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
  computed: {
    currentModeLabel() {
      return this.currentServiceType === 'family'
        ? 'Family Prayer'
        : 'Full Daily Office';
    },
    switchModeLabel() {
      const targetMode =
        this.currentServiceType === 'family'
          ? 'Full Daily Office'
          : 'Family Prayer';
      return `Switch to ${targetMode}`;
    },
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
        return 'office-nav-selected';
      }
      return 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50 hover:border-gray-300 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:border-gray-500';
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
    iconClass(name) {
      if (this.selectedOffice === name) {
        return 'office-nav-selected-icon';
      }
      return 'text-gray-500 dark:text-gray-400';
    },
    textClass(name) {
      if (this.selectedOffice === name) {
        return 'office-nav-selected-text';
      }
      return 'text-gray-700 dark:text-gray-300';
    },
  },
};
</script>

<style scoped>
.office-nav-selected {
  background-color: var(--accent-color);
  border-color: var(--accent-color);
  color: var(--accent-contrast);
}

.office-nav-selected:hover {
  filter: brightness(0.95);
}

.office-nav-selected-text,
.office-nav-selected-icon {
  color: var(--accent-contrast);
}

.mode-switch-button {
  color: var(--accent-color);
  border: 1px solid var(--accent-color);
  background-color: transparent;
  line-height: 1.1;
  font-size: 0.75rem;
  padding: 0.4rem;
  white-space: nowrap;
}

.mode-switch-button:hover {
  color: var(--accent-color);
  background-color: var(--el-fill-color-light);
}

:root.dark .mode-switch-meta {
  color: var(--el-text-color-primary);
}

.mode-switch-label {
  display: block;
  font-size: 0.7rem;
  line-height: 1;
  color: var(--el-text-color-secondary);
  margin-bottom: 0.3rem;
  letter-spacing: 0.02em;
}

.mode-switch-current {
  display: block;
  font-size: 0.88rem;
  line-height: 1.1;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

:root.dark .mode-switch-button {
  border-color: var(--accent-color);
}

:root.dark .mode-switch-button:hover {
  background-color: var(--el-fill-color-light);
}
</style>
