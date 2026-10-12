<template>
  <div class="readings">
    <PageNotFound v-if="notFound" />
    <template v-else>
      <section class="readings-head">
        <div v-if="services" id="readings-settings" class="readings-choice">
          <UiSegmented
            v-if="serviceGroups.length > 1"
            class="readings-tabs"
            variant="underline"
            block
            :model-value="currentGroup"
            :options="serviceGroups"
            aria-label="Service"
            @update:model-value="changeGroup"
          >
            <template #option="{ option }">
              <span class="readings-tabs__long">{{ option.label }}</span>
              <span class="readings-tabs__short" aria-hidden="true">{{
                option.short
              }}</span>
            </template>
          </UiSegmented>

          <fieldset v-if="groupServices.length > 1" class="service-choices">
            <legend class="eyebrow service-choices__legend">Choose one</legend>
            <label
              v-for="item in groupServices"
              :key="item.name"
              class="ui-check service-choice"
              :class="{ 'is-selected': item.name === service }"
            >
              <input
                type="radio"
                name="readings-service"
                :value="item.name"
                :checked="item.name === service"
                @change="changeService(item.name)"
              />
              <span class="service-choice__name">{{ item.name }}</span>
            </label>
          </fieldset>
        </div>

        <nav class="day-line" aria-label="Choose a day">
          <router-link
            :to="dayLink(-1)"
            class="day-line__step"
            aria-label="Previous day"
            @click="scrollToTop"
          >
            <UiIcon name="chevron-left" />
          </router-link>
          <div class="day-line__center">
            <router-link :to="calendarLink" class="day-line__date">
              {{ formattedDate }}
            </router-link>
            <router-link
              v-if="!isViewingToday"
              :to="todayLink"
              class="day-line__today"
              @click="scrollToTop"
            >
              Return to today
            </router-link>
          </div>
          <router-link
            :to="dayLink(1)"
            class="day-line__step"
            aria-label="Next day"
            @click="scrollToTop"
          >
            <UiIcon name="chevron-right" />
          </router-link>
        </nav>

        <Loading v-if="loading" />
        <UiAlert v-if="error" tone="error" :title="error" />

        <CalendarCard
          v-if="!loading && card"
          :calendar-date="calendarDate"
          :card="card"
          service-type="readings"
          office="readings"
        />

        <div
          v-if="!loading && services"
          class="readings-tools"
          role="toolbar"
          aria-label="Reading tools"
        >
          <button
            type="button"
            class="readings-tool"
            @click="openPanel('display')"
          >
            <span class="readings-tool__glyph" aria-hidden="true">Aa</span>
            Display
          </button>
          <router-link
            v-if="officeLink"
            :to="officeLink.to"
            class="readings-tool"
          >
            <UiIcon :name="officeLink.icon" />
            {{ officeLink.label }}
          </router-link>
          <router-link to="/settings" class="readings-tool">
            <UiIcon name="sliders" />
            Customize
          </router-link>
        </div>

        <UiDisclosure
          v-if="!loading && services"
          class="readings-versions"
          title="Translation"
          :meta="versionsSummary"
        >
          <div class="readings-versions__grid">
            <UiField label="Bible translation" for-id="readings-translation">
              <UiSelect
                id="readings-translation"
                v-model="translation"
                :options="translations"
                @change="changeTranslation"
              />
            </UiField>
            <UiField label="Psalter" for-id="readings-psalter">
              <UiSelect
                id="readings-psalter"
                v-model="psalmsTranslation"
                :options="psalmsTranslations"
                @change="changeTranslation"
              />
            </UiField>
            <UiField label="Psalm style" for-id="readings-psalm-style">
              <UiSelect
                id="readings-psalm-style"
                v-model="psalmStyle"
                :options="psalmStyles"
                @change="changeStyle"
              />
            </UiField>
          </div>
        </UiDisclosure>
      </section>

      <template v-if="!loading && services">
        <div class="book-opening">
          <Ornament glyph="o" />
        </div>

        <!-- The readings, set like the office text -->
        <div
          id="main"
          class="book readings-text"
          :class="{ 'is-busy': readingsLoading }"
          :aria-busy="readingsLoading ? 'true' : null"
        >
          <h2 class="readings-service">{{ serviceTitle.title }}</h2>
          <h4 v-if="serviceTitle.subtitle" class="readings-service">
            {{ serviceTitle.subtitle }}
          </h4>
          <CitationGroup
            v-for="(readings, number) in groupedReadings"
            :key="number"
            :readings="readings"
            @reading-link-click="handleReadingLinkClick"
          />

          <Collects
            v-if="showCollects"
            :collects="collectsToShow"
            :style="'Contemporary'"
          />
          <Collects
            v-if="showTraditionalCollects"
            :collects="traditionalCollectsToShow"
            :style="'Traditional'"
          />
          <Reading
            v-for="(reading, index) in readingsToShow"
            :id="readingName(index)"
            :key="index"
            :reading="reading"
            :psalm-cycle="psalmCycle"
            :length="reading.length"
            :translation="translation"
            :psalms-translation="psalmsTranslation"
            @cycle-60="setCycle60"
            @cycle-30="setCycle30"
          />
          <div class="readings-credit">
            <a href="https://www.esv.org/">
              Scripture quotations are from the ESV® Bible (The Holy Bible,
              English Standard Version®), copyright © 2001 by Crossway, a
              publishing ministry of Good News Publishers. Used by permission.
              All rights reserved.
            </a>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
// @ is an alias to /src
import CalendarCard from '@/components/CalendarCard.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import Loading from '@/components/Loading.vue';
import setCalendarDate from '@/helpers/setCalendarDate';
import CitationGroup from '@/components/CitationGroup.vue';
import Reading from '@/components/Reading.vue';
import Collects from '@/components/Collects.vue';
import { DynamicStorage } from '@/helpers/storage';
import { resolveColorFromCard, setSeasonAccent } from '@/helpers/seasonAccent';
import { openPanel } from '@/helpers/panels';
import { nextTick } from 'vue';

const SERVICE_GROUPS = [
  {
    value: 'morning_prayer',
    label: 'Morning Prayer',
    short: 'Morning',
    icon: 'sunrise',
  },
  {
    value: 'evening_prayer',
    label: 'Evening Prayer',
    short: 'Evening',
    icon: 'sunset',
  },
  {
    value: 'holy_eucharist',
    label: 'Holy Eucharist',
    short: 'Eucharist',
    icon: 'cross',
  },
];

function datePath(date) {
  return `${date.getFullYear()}/${date.getMonth() + 1}/${date.getDate()}`;
}

export default {
  name: 'Readings',
  components: {
    CalendarCard,
    PageNotFound,
    Loading,
    CitationGroup,
    Reading,
    Collects,
  },
  props: {},
  data() {
    return {
      loading: true,
      readingsLoading: false,
      error: false,
      calendarDate: null,
      card: null,
      services: null,
      daily_office: [],
      morning_prayer: [],
      evening_prayer: [],
      holy_eucharist: [],
      service: null,
      readings: null,
      full: true,
      psalmCycle: '30',
      readingsToShow: [],
      translation: 'esv',
      translations: [
        { value: 'esv', label: 'ESV: English Standard Version' },
        { value: 'kjv', label: 'KJV: King James Version' },
        { value: 'rsv', label: 'RSV: Revised Standard Version' },
        { value: 'nasb', label: 'NASB: New American Standard Bible' },
        { value: 'niv', label: 'NIV: New International Version' },
        { value: 'nrsvce', label: 'NRSV: New Revised Standard Version' },
        { value: 'nabre', label: 'NAB-RE: New American Bible Revised Edition' },
        { value: 'cuvs', label: 'CUVS: 和合本（简体）' },
        { value: 'cuv', label: 'CUV: 和合本（繁體）' },
        { value: 'znsigao', label: '思高本（简体）' },
        { value: 'sigao', label: '思高本（繁體）' },
        { value: 'nvi', label: 'NVI: Nueva Versión Internacional' },
        { value: 'rv1960', label: 'RVR1960: Reina-Valera 1960' },
      ],
      psalmsTranslation: 'contemporary',
      psalmsTranslations: [
        {
          label: 'Contemporary Psalms',
          value: 'contemporary',
        },
        {
          label: 'Traditional Psalms',
          value: 'traditional',
        },
      ],
      psalmStyle: 'whole_verse',
      psalmStyles: [
        {
          label: 'Antiphonally by Whole Verse',
          value: 'whole_verse',
        },
        {
          label: 'Antiphonally by Half Verse',
          value: 'half_verse',
        },
        {
          label: 'In Unison',
          value: 'unison',
        },
      ],
      notFound: false,
    };
  },
  computed: {
    // Morning Prayer, Evening Prayer, and Holy Eucharist, as tabs
    serviceGroups() {
      return SERVICE_GROUPS.filter((group) => this[group.value].length);
    },
    currentGroup() {
      if (!this.service) return null;
      return this.getPositionAndServiceName(this.service).service_name;
    },
    // The services in the selected group (e.g. a Sunday and a holy day)
    groupServices() {
      return this.currentGroup ? this[this.currentGroup] || [] : [];
    },
    // "Evening Prayer (The Twenty-first Sunday after Pentecost)" is set as
    // a title with its occasion beneath, as the book sets an office's day.
    serviceTitle() {
      const name = this.service || '';
      const match = name.match(/^(.+?)\s+\((.+)\)$/);
      if (match && !/^Proper \d+$/.test(match[2])) {
        return { title: match[1], subtitle: match[2] };
      }
      return { title: name, subtitle: '' };
    },
    versionsSummary() {
      const translation = this.translations.find(
        (item) => item.value === this.translation
      );
      const psalter =
        this.psalmsTranslation === 'traditional'
          ? 'Traditional'
          : 'Contemporary';
      const name = translation ? translation.label.split(':')[0] : '';
      return [name, psalter].filter(Boolean).join(' · ');
    },
    // Pray the office these readings belong to
    officeLink() {
      const group = SERVICE_GROUPS.find((g) => g.value === this.currentGroup);
      if (!group || group.value === 'holy_eucharist') return null;
      return {
        to: `/${group.value}/${datePath(this.calendarDate)}`,
        label: 'Pray the office',
        icon: group.icon,
      };
    },
    isViewingToday() {
      const today = new Date();
      return (
        this.calendarDate.getFullYear() === today.getFullYear() &&
        this.calendarDate.getMonth() === today.getMonth() &&
        this.calendarDate.getDate() === today.getDate()
      );
    },
    formattedDate() {
      return this.calendarDate.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    },
    calendarLink() {
      return `/calendar/${this.calendarDate.getFullYear()}/${
        this.calendarDate.getMonth() + 1
      }/`;
    },
    todayLink() {
      return this.readingsPath(new Date());
    },
    groupedReadings: function () {
      const groups = {};
      this.readingsToShow.forEach((reading) => {
        if (reading.full.reading_number in groups) {
          groups[reading.full.reading_number].push(reading);
        } else {
          groups[reading.full.reading_number] = [reading];
        }
      });
      return groups;
    },
    collectsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        let collects = serviceItems['collects'];
        collects = collects.map((collect) => {
          return collect.replace(' Amen.', '');
        });
        return collects;
      }
      return [];
    },
    showCollects: function () {
      return this.collectsToShow.length > 0;
    },
    traditionalCollectsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        let collects;
        try {
          collects = serviceItems['traditional_collects'];
        } catch {
          return [];
        }
        collects = collects.map((collect) => {
          return collect.replace(' Amen.', '');
        });
        return collects;
      }
      return [];
    },
    showTraditionalCollects: function () {
      return this.traditionalCollectsToShow.length > 0;
    },
  },
  watch: {
    '$route.params': {
      handler(newParams, oldParams) {
        if (this.$route.name && this.$route.name.startsWith('readings')) {
          if (
            newParams.service !== oldParams?.service ||
            newParams.position !== oldParams?.position
          ) {
            // Handle native route changes without reloading data
            if (this.services) {
              if (newParams.service) {
                const serviceRaw = newParams.service
                  .toLowerCase()
                  .replace('-', '_');
                const position = parseInt(newParams.position || 0);

                if (
                  serviceRaw === 'morning_prayer' &&
                  this.morning_prayer[position]
                ) {
                  this.service = this.morning_prayer[position].name;
                } else if (
                  serviceRaw === 'evening_prayer' &&
                  this.evening_prayer[position]
                ) {
                  this.service = this.evening_prayer[position].name;
                } else if (
                  serviceRaw === 'daily_office' &&
                  this.daily_office[position]
                ) {
                  this.service = this.daily_office[position].name;
                } else if (
                  serviceRaw === 'holy_eucharist' &&
                  this.holy_eucharist[position]
                ) {
                  this.service = this.holy_eucharist[position].name;
                }
              }
              this.setReadingsToShow();
            }
          }
        }
      },
      deep: true,
    },
  },
  async created() {
    this.calendarDate = setCalendarDate(this.$route);
    await this.$store.dispatch('initializeSettings');

    let translation = await DynamicStorage.getItem('readings_translation');
    if (!translation || translation === 'undefined') {
      translation = this.$store.state.settings['bible_translation'];
    }
    if (!translation || translation === 'undefined') {
      translation = 'esv';
    }
    await DynamicStorage.setItem('readings_translation', translation);
    this.translation = translation;

    let psalmsTranslation = await DynamicStorage.getItem('psalms_translation');
    if (!psalmsTranslation) {
      const settings = this.$store.state.settings;
      psalmsTranslation = settings['language_style'];
    }
    await DynamicStorage.setItem('psalms_translation', psalmsTranslation);
    this.psalmsTranslation = psalmsTranslation;

    let psalmCycle = await DynamicStorage.getItem('psalter');
    if (!psalmCycle) {
      const settings = this.$store.state.settings;
      psalmCycle = settings['psalter'];
    }
    await DynamicStorage.setItem('psalter', psalmCycle);
    this.psalmCycle = psalmCycle;

    let psalmStyle = await DynamicStorage.getItem('psalm_style');
    if (!psalmStyle) {
      const settings = this.$store.state.settings;
      psalmStyle = settings['psalm_style'];
    }
    await DynamicStorage.setItem('psalm_style', psalmStyle);
    this.psalmStyle = psalmStyle;

    await this.initialize();
  },
  methods: {
    applySeasonAccentFromCard(card) {
      const liturgicalColor = resolveColorFromCard(card, 'readings');
      if (liturgicalColor) {
        setSeasonAccent(liturgicalColor);
      }
    },
    initialize: async function () {
      this.readingsLoading = true;
      let data;
      try {
        this.availableSettings = await this.$store.state.availableSettings;
        await this.$store.dispatch('initializeSettings');
        const settings = await this.$store.state.settings;
        const queryString = Object.keys(settings)
          .map((key) => key + '=' + settings[key])
          .join('&');

        const today_str =
          this.calendarDate.getFullYear() +
          '-' +
          (this.calendarDate.getMonth() + 1) +
          '-' +
          this.calendarDate.getDate();
        data = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/readings/${today_str}?translation=${this.translation}&psalms=${this.psalmsTranslation}&style=${this.psalmStyle}&` +
            queryString
        );
      } catch {
        this.error =
          'There was an error retrieving the readings. Please try again.';
        this.loading = false;
        this.readingsLoading = false;
        return;
      }
      this.card = data.data.calendarDate;
      this.applySeasonAccentFromCard(this.card);
      this.services = data.data.services;
      // iterate through keys and values of this.services
      this.morning_prayer = [];
      this.evening_prayer = [];
      this.daily_office = [];
      this.holy_eucharist = [];
      for (const [key, value] of Object.entries(this.services)) {
        if (value.type == 'daily_office') {
          this.daily_office.push(value);
        } else if (value.type == 'mass') {
          this.holy_eucharist.push(value);
        }
        if (key.includes('Morning Prayer')) {
          this.morning_prayer.push(value);
        } else if (key.includes('Evening Prayer')) {
          this.evening_prayer.push(value);
        }
      }
      if (this.$route.params.service) {
        try {
          const service = this.$route.params.service
            .toLowerCase()
            .replace('-', '_');
          const position = parseInt(this.$route.params.position || 0);
          if (service == 'morning_prayer') {
            this.service = this.morning_prayer[position].name;
          } else if (service == 'evening_prayer') {
            this.service = this.evening_prayer[position].name;
          } else if (service == 'daily_office') {
            this.service = this.daily_office[position].name;
          } else if (service == 'holy_eucharist') {
            this.service = this.holy_eucharist[position].name;
          } else {
            this.service = this.morning_prayer[position].name;
          }
        } catch {
          this.notFound = true;
        }
      } else {
        this.service = this.morning_prayer[0].name;
      }
      this.setReadingsToShow();
      this.error = false;
      this.loading = false;
      this.readingsLoading = false;
    },
    readingID: function (reading) {
      const readingId = reading.citation.replace(/[\W_]+/g, '_');
      return `reading_${readingId}`.toLowerCase();
    },
    changeTranslation: async function () {
      await DynamicStorage.setItem(
        'psalms_translation',
        this.psalmsTranslation
      );
      await DynamicStorage.setItem('readings_translation', this.translation);
      await this.initialize();
    },
    changeStyle: async function () {
      await DynamicStorage.setItem('psalm_style', this.psalmStyle);
      await this.initialize();
    },
    // Readings for another day, keeping the kind of service (not its
    // position, which may not exist on that day).
    readingsPath(date) {
      const service = this.$route.params.service;
      return service
        ? `/readings/${service}/${datePath(date)}`
        : `/readings/${datePath(date)}`;
    },
    dayLink(offset) {
      const date = new Date(this.calendarDate);
      date.setDate(date.getDate() + offset);
      return this.readingsPath(date);
    },
    scrollToTop() {
      window.scrollTo(0, 0);
    },
    openPanel,
    changeGroup: async function (group) {
      const services = this[group] || [];
      if (services.length) {
        await this.changeService(services[0].name);
      }
    },
    getPositionAndServiceName: function (service) {
      let position;
      let service_name;
      if (service.includes('Morning Prayer')) {
        service_name = 'morning_prayer';
        position = this.morning_prayer.findIndex((p) => p.name == service);
      } else if (service.includes('Evening Prayer')) {
        service_name = 'evening_prayer';
        position = this.evening_prayer.findIndex((p) => p.name == service);
      } else {
        service_name = 'holy_eucharist';
        position = this.holy_eucharist.findIndex((p) => p.name == service);
      }
      return { position: position, service_name: service_name };
    },
    changeService: async function (service) {
      this.service = service;
      let serviceValues = this.getPositionAndServiceName(service);
      let routeName = 'readingsByServiceAndDate';
      if (serviceValues.position > 0) {
        routeName = 'readingsByServicePositionAndDate';
      }

      // Use route params if available, otherwise use calendarDate
      const year = this.$route.params.year || this.calendarDate.getFullYear();
      const month =
        this.$route.params.month || this.calendarDate.getMonth() + 1;
      const day = this.$route.params.day || this.calendarDate.getDate();

      // Only push route if it's changing
      if (
        this.$route.name !== routeName ||
        this.$route.params.service !== serviceValues.service_name ||
        this.$route.params.position !== serviceValues.position
      ) {
        window.sessionStorage.setItem('preventScroll', 'true');
        await this.$router.push({
          name: routeName,
          params: {
            service: serviceValues.service_name,
            year: year,
            month: month,
            day: day,
            position: serviceValues.position,
          },
        });
      }

      // No need to call initialize() here manually since we added a route watcher
      // that will fire when the route changes. If the route didn't change (rare),
      // we still need to update the view.
      this.setReadingsToShow();

      await nextTick();
      this.goto('readings-settings');
    },
    setReadingsToShow: function () {
      if (this.service) {
        let serviceItems = this.services[this.service];
        this.readingsToShow = serviceItems['readings'].map((reading) => {
          return reading;
        });
        return;
      }
      this.readingsToShow = [];
    },
    handleReadingLinkClick: async function (data) {
      this.readingsToShow = this.readingsToShow.map((reading) => {
        if (
          reading.full.citation == data.reading.citation &&
          data.length == 'full'
        ) {
          reading.length = data.length;
        }
        if (
          reading.abbreviated.citation == data.reading.citation &&
          data.length == 'abbreviated'
        ) {
          reading.length = data.length;
        }
        return reading;
      });
      if (data.reading.cycle == '60') {
        this.setCycle60();
      }
      if (data.reading.cycle == '30') {
        this.setCycle30();
      }
      await nextTick();
      this.goto(this.readingID(data.reading));
    },
    readingName: function (index) {
      return `reading_${index}`;
    },
    goto(id) {
      const menu =
        document.getElementById('topMenu') ||
        document.querySelector('.app-header');
      const menuHeight = menu ? menu.offsetHeight : 0;
      const element = document.getElementById(id);
      if (!element) return;
      const top = element.getBoundingClientRect().top + window.scrollY;
      window.scrollTo({
        top: top - menuHeight - 15,
        left: 0,
        behavior: 'smooth',
      });
    },
    setCycle30: async function () {
      this.psalmCycle = '30';
      await DynamicStorage.setItem('psalter', this.psalmCycle);
    },
    setCycle60: async function () {
      this.psalmCycle = '60';
      await DynamicStorage.setItem('psalter', this.psalmCycle);
    },
  },
};
</script>

<style scoped>
.readings-head {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 46rem;
  margin: 0 auto;
  padding: var(--space-4) var(--gutter) 0;
}

/* Service: Morning Prayer · Evening Prayer · Holy Eucharist */
.readings-choice {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
}

.readings-choice .readings-tabs {
  width: 100%;
  max-width: 34rem;
}

.readings-tabs__short {
  display: none;
}

/* Phones: short names, no icons, so all three fit at 320px */
@media (max-width: 479px) {
  .readings-tabs__long,
  .readings-tabs :deep(.ui-segmented__icon) {
    display: none;
  }

  .readings-tabs__short {
    display: inline;
  }

  .readings-tabs :deep(.ui-segmented__option) {
    padding-inline: var(--space-1);
  }
}

/* When a group has more than one set of readings (a Sunday and a holy
   day, say), list them in full: their names are too long for tabs. */
.service-choices {
  width: 100%;
  max-width: 34rem;
  min-width: 0;
  padding: 0;
  margin: 0;
  border: 0;
}

.service-choices__legend {
  width: 100%;
  margin-bottom: var(--space-1);
  text-align: center;
}

.service-choice {
  display: flex;
  width: 100%;
  min-height: 2.75rem;
  padding: var(--space-2) var(--space-1);
  border-bottom: 1px solid var(--rule);
  color: var(--ink-soft);
  transition: color var(--duration) var(--ease);
}

.service-choice:first-of-type {
  border-top: 1px solid var(--rule);
}

.service-choice input {
  margin-top: 0.2rem;
}

.service-choice:hover,
.service-choice.is-selected {
  color: var(--ink);
}

.service-choice__name {
  min-width: 0;
  line-height: 1.3;
  text-wrap: pretty;
}

/* Day line: ‹ Sunday, October 11, 2026 › (as on the office page) */
.day-line {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  max-width: 34rem;
  margin: 0 auto;
}

.day-line__step {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  border-radius: 50%;
  color: var(--ink-soft);
  font-size: 1.15rem;
  text-decoration: none;
  transition: background-color var(--duration) var(--ease);
}

.day-line__step:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}

.day-line__center {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
  flex: 1;
}

.day-line__date {
  font-size: var(--text-md);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-soft);
  text-decoration: none;
  text-align: center;
}

.day-line__date:hover {
  color: var(--accent);
}

.day-line__today {
  font-size: var(--text-xs);
  font-style: italic;
}

/* Quiet tools under the day's title */
.readings-tools {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-1) var(--space-2);
}

.readings-tool {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  min-height: 2.25rem;
  padding: 0.2rem 0.7rem;
  border: 1px solid var(--rule);
  border-radius: var(--radius-pill);
  background-color: var(--paper);
  color: var(--ink-soft);
  font-size: var(--text-sm);
  text-decoration: none;
  transition:
    border-color var(--duration) var(--ease),
    color var(--duration) var(--ease),
    background-color var(--duration) var(--ease);
}

/* A 44px tap target around the quieter 36px pill */
.readings-tool {
  position: relative;
}

.readings-tool::after {
  content: '';
  position: absolute;
  inset: -0.25rem 0;
}

.readings-tool:hover {
  border-color: var(--rule-strong);
  color: var(--ink);
}

.readings-tool .ui-icon {
  color: var(--accent);
}

.readings-tool__glyph {
  font-size: 1.05em;
  line-height: 1;
}

/* Translation and psalter */
.readings-versions {
  width: 100%;
  max-width: 34rem;
  margin: 0 auto;
  border-top: 1px solid var(--rule);
}

.readings-versions__grid {
  display: grid;
  gap: var(--space-4);
  padding-top: var(--space-2);
}

@media (min-width: 640px) {
  .readings-versions__grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .readings-versions__grid > :first-child {
    grid-column: 1 / -1;
  }
}

.book-opening {
  margin: var(--space-5) auto var(--space-1);
  text-align: center;
  font-size: 1.5rem;
}

/* The text dims while a new translation loads */
.readings-text {
  transition: opacity var(--duration) var(--ease);
}

.readings-text.is-busy {
  opacity: 0.5;
  pointer-events: none;
}

.readings-service {
  text-wrap: balance;
}

.readings-credit {
  margin-top: 3em;
  padding-top: 1.25em;
  border-top: 1px solid var(--rule);
  font-size: 0.6em;
  line-height: var(--leading-ui);
  font-style: italic;
  text-align: center;
}

.readings-credit a {
  color: var(--ink-faint);
}
</style>
