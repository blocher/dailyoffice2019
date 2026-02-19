<template>
  <div class="main-card font-sans my-6 max-w-xl mx-auto">
    <div
      class="bg-white rounded-xl shadow-sm border-t-8 overflow-hidden transition-all duration-300 hover:shadow-md"
      :class="[cardColorClass]"
    >
      <div class="p-6 text-center">
        <h1
          v-if="officeName"
          class="text-xl font-bold text-gray-900 uppercase tracking-wide mb-2"
        >
          {{ officeName }}
        </h1>
        <h3
          class="text-3xl font-serif text-gray-800 mb-6 font-medium border-b border-gray-100 pb-4"
        >
          {{ formattedDate }}
        </h3>

        <div class="card-info space-y-4">
          <div
            v-if="card && office !== 'evening_prayer' && office !== 'compline'"
          >
            <h4
              class="text-lg font-semibold text-gray-800 leading-tight"
              v-html="card.primary_feast"
            ></h4>
          </div>

          <div
            v-if="card && (office == 'evening_prayer' || office == 'compline')"
          >
            <h4
              class="text-lg font-semibold text-gray-800 leading-tight"
              v-html="card.primary_evening_feast"
            ></h4>
          </div>

          <h5
            v-if="card && card.fast && card.fast.fast_day"
            class="inline-block px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-gray-100 text-gray-600 mt-2"
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
        class="bg-gray-50 border-t border-gray-100 p-4"
      >
        <div
          v-for="commemoration in card.commemorations"
          :key="commemoration.name"
          class="text-sm text-gray-600 py-1 text-center"
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
        class="bg-gray-50 border-t border-gray-100 p-4"
      >
        <div
          v-for="commemoration in card.evening_commemorations"
          :key="commemoration.name"
          class="text-sm text-gray-600 py-1 text-center"
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
    // Map liturgical colors to Tailwind border classes
    cardColorClass() {
      const colorMap = {
        red: 'border-red-700',
        green: 'border-green-700',
        white: 'border-yellow-400', // Gold/Yellow often used for white/gold feasts, or just gray-200 if strict white
        purple: 'border-purple-800',
        black: 'border-gray-900',
        rose: 'border-pink-400',
        blue: 'border-blue-600',
      };

      // Handle the 'white' case specially if we want it to be distinct from background
      // Liturgical white is often represented with Gold or just White.
      // If we use white border on white bg it's invisible.
      // Let's use a Gold-ish color for White feasts as is common.

      const color = this.cardColor ? this.cardColor.toLowerCase() : 'green';
      return colorMap[color] || 'border-green-700';
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
/* Scoped overrides if necessary, but relying mostly on Tailwind */
/* Custom colors that might not be in default Tailwind palette if strict adherence is needed */
.border-red-700 {
  border-color: #c21c13;
}
.border-green-700 {
  border-color: #077339;
}
.border-purple-800 {
  border-color: #64147d;
}
/* For white, let's use a border that shows up - maybe a gold or silver?
   The original CSS used: background-color: white; color: black;
   If I want a visual indicator, gold is good for "White" feasts.
*/
.border-yellow-400 {
  border-color: #d4af37;
} /* Metallic Gold */
</style>
