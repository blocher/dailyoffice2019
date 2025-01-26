<template>
  <div class="home office">
    <div class="small-container">
      <PageNotFound v-if="notFound" />
      <div v-if="!notFound">
        <Loading v-if="loading" />
        <CalendarCard
          :office="office"
          :calendar-date="calendarDate"
          :card="card"
          :service-type="serviceType"
        />
        <el-alert v-if="error" :title="error" type="error" />
        <OfficeNav
          :calendar-date="calendarDate"
          :selected-office="office"
          :service-type="serviceType"
        />
        <FontSizer v-if="readyToSetFontSize" />
      </div>
    </div>
    <div id="main">
      <div v-for="module in modules" :key="module.name">
        <div v-for="line in module.lines" :key="line.content">
          <OfficeHeading v-if="line.line_type === 'heading'" :line="line" />
          <OfficeSubheading
            v-if="line.line_type === 'subheading'"
            :line="line"
          />
          <OfficeCitation v-if="line.line_type === 'citation'" :line="line" />
          <OfficeHTML
            v-if="line.line_type === 'html' || line.line_type === 'audio'"
            :line="line"
          />
          <OfficeLeader
            v-if="line.line_type === 'leader' || line.line_type === 'reader'"
            :line="line"
          />
          <OfficeLeaderDialogue
            v-if="line.line_type === 'leader_dialogue'"
            :line="line"
          />
          <OfficeCongregation
            v-if="line.line_type === 'congregation'"
            :line="line"
          />

          <OfficeCongregationDialogue
            v-if="line.line_type === 'congregation_dialogue'"
            :line="line"
          />

          <OfficeRubric v-if="line.line_type === 'rubric'" :line="line" />
          <OfficeSpacer v-if="line.line_type === 'spacer'" />
        </div>
      </div>
    </div>
  </div>

  <AudioPlayer v-if="!loading && audioReady" :urls="audioLinks" />
</template>

<script>
// @ is an alias to /src
import OfficeHeading from '@/components/OfficeHeading.vue';
import OfficeSubheading from '@/components/OfficeSubheading.vue';
import OfficeCitation from '@/components/OfficeCitation.vue';
import OfficeHTML from '@/components/OfficeHTML.vue';
import OfficeCongregation from '@/components/OfficeCongregation.vue';
import OfficeLeader from '@/components/OfficeLeader.vue';
import OfficeCongregationDialogue from '@/components/OfficeCongregationDialogue.vue';
import OfficeLeaderDialogue from '@/components/OfficeLeaderDialogue.vue';
import OfficeRubric from '@/components/OfficeRubric.vue';
import OfficeSpacer from '@/components/OfficeSpacer.vue';
import Loading from '@/components/Loading.vue';
import CalendarCard from '@/components/CalendarCard.vue';
import OfficeNav from '@/components/OfficeNav.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import FontSizer from '@/components/FontSizer.vue';
import { DynamicStorage } from '@/helpers/storage';
import AudioPlayer from '@/components/AudioPlayer.vue'; // import AudioPlayer from '@/components/AudioPlayer.vue';
// import AudioPlayer from '@/components/AudioPlayer.vue';

export default {
  name: 'Office',
  components: {
    AudioPlayer,
    // AudioPlayer,
    OfficeHeading,
    OfficeSubheading,
    OfficeCitation,
    OfficeHTML,
    OfficeCongregation,
    OfficeLeader,
    OfficeCongregationDialogue,
    OfficeLeaderDialogue,
    OfficeRubric,
    OfficeSpacer,
    Loading,
    CalendarCard,
    OfficeNav,
    PageNotFound,
    FontSizer,
  },
  props: {
    office: {
      type: String,
    },
    calendarDate: {
      type: Date,
    },
    serviceType: {
      default: 'office',
      type: String,
    },
  },
  data() {
    return {
      counter: 0,
      modules: null,
      loading: true,
      readyToSetFontSize: false,
      error: false,
      card: '',
      notFound: false,
      audioLinks: [],
      audioReady: false,
    };
  },
  async mounted() {
    await DynamicStorage.setItem('serviceType', 'office');
  },

  async created() {
    const valid_daily_offices = [
      'morning_prayer',
      'midday_prayer',
      'evening_prayer',
      'compline',
    ];
    const valid_family_offices = [
      'morning_prayer',
      'midday_prayer',
      'early_evening_prayer',
      'close_of_day_prayer',
    ];
    const valid_offices =
      this.serviceType == 'office' ? valid_daily_offices : valid_family_offices;
    if (!valid_offices.includes(this.$props.office)) {
      this.notFound = true;
      return;
    }
    const today_str =
      this.calendarDate.getFullYear() +
      '-' +
      (this.calendarDate.getMonth() + 1) +
      '-' +
      this.calendarDate.getDate();
    this.availableSettings = await this.$store.state.availableSettings;
    await this.$store.dispatch('initializeSettings');
    const settings = await this.$store.state.settings;
    const queryString = Object.keys(settings)
      .map((key) => key + '=' + settings[key])
      .join('&');
    let data = null;
    const office_url =
      `${import.meta.env.VITE_API_URL}api/v1/${this.serviceType}/${this.office}/` +
      today_str +
      '?' +
      queryString +
      '&extra_collects=' +
      (await this.extraCollects());
    try {
      data = await this.$http.get(office_url);
    } catch {
      this.error =
        'There was an error retrieving the office. Please try again.';
      this.loading = false;
      return;
    }
    this.modules = data.data.modules;
    this.card = data.data.calendar_day;
    this.error = false;
    this.loading = false;
    await this.$nextTick();
    this.readyToSetFontSize = true;
    this.audioLinks = await this.setAudioLinks(office_url);
    this.audioReady = true;
  },
  methods: {
    async setAudioLinks(url) {
      url = `${url}&include_audio_links=true`;
      try {
        const data = await this.$http.get(url);
        this.audioLinks = data.data.audio;
        return data.data.audio;
      } catch {
        return;
      }
    },
    async setAudioLinksBak() {
      const audio_links = [];
      for (const module of this.modules) {
        audio_links.push(...(await this.getAudioLinksForModule(module)));
      }
      return audio_links;
    },
    async getAudioLinksForModule(module) {
      const links = [];
      for (const line of module.lines) {
        const url = await this.getAudioLinkForLine(line);
        if (url) {
          links.push(url);
        }
      }
      return links;
    },
    async getAudioLinkForLine(line) {
      if (!('content' in line) || !line.content) {
        return null;
      }

      if (!('line_type' in line) || !line.line_type) {
        return null;
      }

      if (
        ![
          'html',
          'audio',
          'congregation',
          'leader',
          'leader_dialogue',
          'congregation_dialogue',
          'reader',
        ].includes(line.line_type)
      ) {
        return null;
      }

      const data = await this.$http.post(
        `${import.meta.env.VITE_API_URL}api/v1/audio`,
        {
          content: line.content,
          line_type: line.line_type,
        },
        {
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );
      try {
        return data.data.path;
      } catch {
        return null;
      }
    },
    async extraCollects() {
      if (this.serviceType !== 'office') {
        return '';
      }
      const full_office_name = this.office
        .replace('_', ' ')
        .toLowerCase()
        .split(' ')
        .map((s) => s.charAt(0).toUpperCase() + s.substring(1))
        .join(' ');
      const extraCollects =
        JSON.parse(await DynamicStorage.getItem('extraCollects')) || '';
      if (!extraCollects) {
        return '';
      }
      return Object.prototype.hasOwnProperty.call(
        extraCollects,
        full_office_name
      )
        ? extraCollects[full_office_name].join(',')
        : [];
    },
  },
};
</script>

<style scoped>
.el-alert {
  margin-top: 2em;
}
</style>
