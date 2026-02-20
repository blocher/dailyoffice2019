<template>
  <div class="main-card font-sans my-6 max-w-xl mx-auto">
    <div
      class="card-shell bg-white dark:bg-gray-800 border-2 border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center shadow-sm"
      :class="cardColorClass"
    >
      <div class="p-6 text-center">
        <h1
          v-if="officeName"
          class="text-xl font-bold text-gray-900 dark:text-gray-100 uppercase tracking-wide mb-2"
        >
          {{ officeName }}
        </h1>
        <h3
          class="card-date-heading text-3xl font-serif text-gray-800 dark:text-gray-200 mb-6 font-medium border-b border-gray-100 dark:border-gray-700 pb-4"
        >
          {{ formattedDate }}
        </h3>

        <div class="card-info space-y-4">
          <div
            v-if="card && office !== 'evening_prayer' && office !== 'compline'"
          >
            <h4
              class="card-feast-name text-lg font-semibold text-gray-800 dark:text-gray-200 leading-tight"
              v-html="card.primary_feast"
            ></h4>
          </div>

          <div
            v-if="card && (office == 'evening_prayer' || office == 'compline')"
          >
            <h4
              class="card-feast-name text-lg font-semibold text-gray-800 dark:text-gray-200 leading-tight"
              v-html="card.primary_evening_feast"
            ></h4>
          </div>

          <h5
            v-if="card && card.fast && card.fast.fast_day"
            class="inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 mt-2"
          >
            Fast Day
          </h5>
        </div>
      </div>

      <!-- Commemorations Section -->
      <div
        v-if="
          card &&
          card.commemorations.length > 1 &&
          office != 'evening_prayer' &&
          office != 'compline'
        "
        class="bg-gray-50 dark:bg-gray-700/50 border-t border-gray-100 dark:border-gray-700 p-4"
      >
        <div
          v-for="commemoration in card.commemorations"
          :key="commemoration.name"
          class="text-sm text-gray-600 dark:text-gray-300 py-1 text-center"
        >
          <Commemoration :commemoration="commemoration" />
        </div>
      </div>

      <div
        v-if="
          card &&
          card.evening_commemorations.length > 1 &&
          (office == 'evening_prayer' || office == 'compline')
        "
        class="bg-gray-50 dark:bg-gray-700/50 border-t border-gray-100 dark:border-gray-700 p-4"
      >
        <div
          v-for="commemoration in card.evening_commemorations"
          :key="commemoration.name"
          class="text-sm text-gray-600 dark:text-gray-300 py-1 text-center"
        >
          <Commemoration :commemoration="commemoration" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src
import Commemoration from '@/components/Commemoration.vue';

export default {
  name: 'CalenderCard',
  components: { Commemoration },
  props: ['card', 'calendarDate', 'office', 'serviceType'],
  data() {
    return {
      officeName: null,
      formattedDate: null,
      currentServiceType: this.serviceType,
    };
  },
  computed: {
    cardColor: function () {
      if (!this.card) return 'white'; // default
      if (this.office !== 'evening_prayer' && this.office !== 'compline') {
        return this.card.primary_color || 'green';
      } else {
        return this.card.primary_evening_color || 'green';
      }
    },
    // Keep liturgical season accents visible in both themes.
    cardColorClass() {
      const colorMap = {
        red: 'season-border-red',
        green: 'season-border-green',
        white: 'season-border-white',
        purple: 'season-border-purple',
        black: 'season-border-black',
        rose: 'season-border-rose',
        blue: 'season-border-blue',
      };
      const color = this.cardColor ? this.cardColor.toLowerCase() : 'green';
      return colorMap[color] || 'season-border-green';
    },
    hideBody: function () {
      if (!this.card) return true;
      if (this.office === 'evening_prayer' || this.office === 'compline') {
        return this.card.evening_commemorations.length < 2;
      } else {
        return this.card.commemorations.length < 2;
      }
    },
  },
  async created() {
    if (!this.currentServiceType) {
      this.currentServiceType = 'office';
    }

    const options = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };
    this.formattedDate = this.$props.calendarDate.toLocaleDateString(
      'en-US',
      options
    );
    const daily_offices = {
      morning_prayer: 'Daily Morning Prayer',
      midday_prayer: 'Daily Midday Prayer',
      evening_prayer: 'Daily Evening Prayer',
      compline: 'Compline',
    };
    const family_offices = {
      morning_prayer: 'Family Prayer in the Morning',
      midday_prayer: 'Family Prayer at Midday',
      early_evening_prayer: 'Family Prayer in the Early Evening',
      close_of_day_prayer: 'Family Prayer at the Close of Day',
    };
    const readings = {
      readings: 'Readings',
    };
    const offices =
      this.currentServiceType == 'readings'
        ? readings
        : this.currentServiceType == 'office'
          ? daily_offices
          : family_offices;
    if (offices[this.$props.office] !== undefined) {
      this.officeName = offices[this.$props.office];
    }
  },
};
</script>

<style scoped>
.card-shell {
  border-top-width: 4px;
}

.card-shell h3.card-date-heading {
  margin-top: 0;
  margin-bottom: 1rem;
  padding-top: 0;
  padding-bottom: 0.9rem;
}

.card-shell h4.card-feast-name {
  margin-top: 0.65rem;
  margin-bottom: 0;
  padding-top: 0;
  line-height: 1.35;
}

.season-border-red {
  border-top-color: var(--season-red);
}

.season-border-green {
  border-top-color: var(--season-green);
}

.season-border-purple {
  border-top-color: var(--season-purple);
}

.season-border-white {
  border-top-color: var(--season-white);
}

.season-border-black {
  border-top-color: var(--season-black);
}

.season-border-rose {
  border-top-color: var(--season-rose);
}

.season-border-blue {
  border-top-color: var(--season-blue);
}
</style>
