<template>
  <div class="office">
    <PageNotFound v-if="notFound" />
    <template v-else>
      <section class="office-head">
        <OfficeNav
          :calendar-date="calendarDate"
          :selected-office="office"
          :service-type="serviceType"
        />
        <Loading v-if="loading" />
        <UiAlert v-if="error" tone="error" :title="error" />
        <CalendarCard
          v-if="!loading && !error"
          :office="office"
          :calendar-date="calendarDate"
          :card="card"
          :service-type="serviceType"
        />
        <div
          v-if="!loading"
          class="office-tools"
          role="toolbar"
          aria-label="Reading tools"
        >
          <button
            type="button"
            class="office-tool"
            @click="openPanel('display')"
          >
            <span class="office-tool__glyph" aria-hidden="true">Aa</span>
            Display
          </button>
          <button
            v-if="audioLoadingEnabled"
            type="button"
            class="office-tool"
            :aria-pressed="audioEnabled ? 'true' : 'false'"
            @click="setAudioEnabled(!audioEnabled)"
          >
            <UiIcon name="headphones" />
            {{ audioEnabled ? 'Audio on' : 'Listen' }}
          </button>
          <button
            v-if="modules"
            type="button"
            class="office-tool"
            @click="bookOpen = true"
          >
            <UiIcon name="book" />
            Book view
            <span v-if="discovery.bookViewNew" class="badge-new">New</span>
          </button>
          <router-link to="/settings" class="office-tool">
            <UiIcon name="sliders" />
            Customize
          </router-link>
        </div>
      </section>

      <div v-if="modules" class="book-opening">
        <Ornament glyph="o" />
      </div>

      <div class="office-body">
        <aside class="office-body__margin">
          <OfficeContents v-if="showContents" :source="modules" />
        </aside>
        <!-- The office text, set like the printed book -->
        <div id="main" class="book">
          <OfficeLines :modules="modules || []" />
        </div>
        <div class="office-body__margin" aria-hidden="true" />
      </div>

      <OfficeContinue
        v-if="modules"
        :office="office"
        :calendar-date="calendarDate"
        :service-type="serviceType"
      />

      <DisplayDiscoveryCard
        v-if="modules"
        :audio-available="audioLoadingEnabled"
      />
    </template>
  </div>

  <BookReader
    v-if="modules"
    v-model:open="bookOpen"
    :title="officeTitle"
    :subtitle="longDate"
    :feast="feastHtml"
  >
    <OfficeLines :modules="modules" />
  </BookReader>

  <AudioPlayer
    v-if="
      !loading &&
      audioLoadingEnabled &&
      audioEnabled &&
      audioReady &&
      audioLinks &&
      audioLinks.length &&
      isWithinSevenDays &&
      isEsvOrKjv &&
      isEnglish
    "
    :audio="audioLinks"
    :audioReady="audioReady"
    :office="office"
    :isEsvOrKjv="isEsvOrKjv"
    :isWithinSevenDays="isWithinSevenDays"
    @dismiss-audio="confirmDismissAudio"
    @audio-play="onAudioPlay"
  />
  <AudioPlayerMessage
    v-if="
      !loading &&
      audioLoadingEnabled &&
      audioEnabled &&
      (!isWithinSevenDays ||
        !isEsvOrKjv ||
        !isEnglish ||
        !audioLinks ||
        !audioLinks.length ||
        !audioReady)
    "
    :isEsvOrKjv="isEsvOrKjv"
    :isEnglish="isEnglish"
    :isWithinSevenDays="isWithinSevenDays"
    :audioReady="audioReady"
    :hasAudioLinks="!!(audioLinks && audioLinks.length)"
    @dismiss-audio="confirmDismissAudio"
  />
</template>

<script>
// @ is an alias to /src
import Loading from '@/components/Loading.vue';
import CalendarCard from '@/components/CalendarCard.vue';
import OfficeNav from '@/components/OfficeNav.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import { DynamicStorage } from '@/helpers/storage';
import AudioPlayer from '@/components/AudioPlayer.vue';
import AudioPlayerMessage from '@/components/AudoPlayerMessage.vue';
import OfficeContinue from '@/components/OfficeContinue.vue';
import OfficeLines from '@/components/OfficeLines.vue';
import BookReader from '@/components/BookReader.vue';
import { discoveryState } from '@/helpers/discovery';
import DisplayDiscoveryCard from '@/components/DisplayDiscoveryCard.vue';
import OfficeContents from '@/components/OfficeContents.vue';
import { confirm } from '@/ui/feedback';
import { openPanel, takeBookViewRequest } from '@/helpers/panels';
import { displayState, setAudioEnabled } from '@/helpers/displayPreferences';
import { resolveColorFromCard, setSeasonAccent } from '@/helpers/seasonAccent';
import { trackEvent } from '@/helpers/analytics';
import { getCachedClientId } from '@/helpers/clientId';

export default {
  name: 'Office',
  components: {
    AudioPlayerMessage,
    AudioPlayer,
    OfficeContinue,
    OfficeLines,
    BookReader,
    DisplayDiscoveryCard,
    OfficeContents,
    Loading,
    CalendarCard,
    OfficeNav,
    PageNotFound,
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
      error: false,
      card: '',
      notFound: false,
      audioLinks: [],
      audioReady: false,
      isEsvOrKjv: false,
      isEnglish: false,
      officeDateStr: null,
      bibleTranslation: null,
      audioPlayTracked: false,
      bookOpen: false,
      discovery: discoveryState,
    };
  },
  computed: {
    audioEnabled() {
      return displayState.audioEnabled;
    },
    officeTitle() {
      const daily = {
        morning_prayer: 'Daily Morning Prayer',
        midday_prayer: 'Daily Midday Prayer',
        evening_prayer: 'Daily Evening Prayer',
        compline: 'Compline',
      };
      const family = {
        morning_prayer: 'Family Prayer in the Morning',
        midday_prayer: 'Family Prayer at Midday',
        early_evening_prayer: 'Family Prayer in the Early Evening',
        close_of_day_prayer: 'Family Prayer at the Close of Day',
      };
      return (this.serviceType === 'family' ? family : daily)[this.office];
    },
    longDate() {
      return this.calendarDate.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    },
    feastHtml() {
      if (!this.card) return '';
      return ['evening_prayer', 'compline'].includes(this.office)
        ? this.card.primary_evening_feast
        : this.card.primary_feast;
    },
    showContents() {
      return displayState.showContents;
    },
    audioLoadingEnabled() {
      // Set VITE_FETCH_AUDIO_ON=false to avoid on-demand generation in dev.
      return import.meta.env.VITE_FETCH_AUDIO_ON !== 'false';
    },
    isWithinSevenDays() {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const yesterday = new Date(today);
      yesterday.setDate(today.getDate() - 3);
      const sevenDaysFromNow = new Date(today);
      sevenDaysFromNow.setDate(today.getDate() + 9);
      sevenDaysFromNow.setHours(23, 59, 59, 999);

      return (
        this.calendarDate >= yesterday && this.calendarDate <= sevenDaysFromNow
      );
    },
  },
  async mounted() {
    await DynamicStorage.setItem('serviceType', this.serviceType);
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
    if (
      !Object.prototype.hasOwnProperty.call(settings, 'bible_translation') ||
      !settings.bible_translation
    ) {
      settings.bible_translation = 'esv';
    }
    this.isEsvOrKjv = ['esv', 'kjv'].includes(settings.bible_translation);
    const displayLanguage =
      Object.prototype.hasOwnProperty.call(settings, 'display_language') &&
      settings.display_language
        ? settings.display_language
        : 'english';
    this.isEnglish = displayLanguage === 'english';
    const queryString = Object.keys(settings)
      .map((key) => key + '=' + settings[key])
      .join('&');
    let data;
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
    this.setDocumentTitle();
    this.modules = data.data.modules;
    // ?book=1 opens the book view directly (a shareable deep link). The
    // router takes the flag off the address and leaves a note.
    if (takeBookViewRequest()) {
      this.$nextTick(() => {
        this.bookOpen = true;
      });
    }
    this.card = data.data.calendar_day;
    this.applySeasonAccentFromCard(this.card);
    this.error = false;
    this.loading = false;
    // Fire once, on the text request only, so the include_audio_links request
    // below is never double-counted. Backend logs the view; GA gets the mirror.
    this.officeDateStr = today_str;
    this.bibleTranslation = settings.bible_translation;
    trackEvent(
      'office_view',
      {
        service_type: this.serviceType,
        office: this.office,
        office_date: today_str,
        translation: settings.bible_translation,
      },
      { toBackend: false, toGA: true }
    );
    if (
      this.audioLoadingEnabled &&
      this.isWithinSevenDays &&
      this.isEsvOrKjv &&
      this.isEnglish
    ) {
      this.audioLinks = await this.setAudioLinks(office_url);
    }
    this.audioReady = true;
  },

  methods: {
    openPanel,
    setAudioEnabled,
    setDocumentTitle() {
      const names = {
        morning_prayer: 'Morning Prayer',
        midday_prayer: 'Midday Prayer',
        evening_prayer: 'Evening Prayer',
        compline: 'Compline',
        early_evening_prayer: 'Early Evening',
        close_of_day_prayer: 'Close of Day',
      };
      const date = this.calendarDate.toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
      });
      const site =
        this.serviceType === 'family' ? 'Family Prayer' : 'The Daily Office';
      document.title = `${names[this.office]}, ${date} | ${site}`;
    },
    async confirmDismissAudio() {
      const hide = await confirm({
        title: 'Hide the audio player?',
        message:
          'You can bring it back any time with Listen, just above the prayers, or from Display (Aa) at the top of the page.',
        confirmText: 'Hide',
      });
      if (hide) {
        await setAudioEnabled(false);
      }
    },
    applySeasonAccentFromCard(card) {
      const liturgicalColor = resolveColorFromCard(card, this.office);
      if (liturgicalColor) {
        setSeasonAccent(liturgicalColor);
      }
    },
    resolveAudioUrl(rawUrl) {
      // The backend builds the track URL from Django's Site.domain (e.g.
      // "example.com"), which is not reachable from the client. Resolve it
      // against the same API host the office was fetched from so audio works
      // in every environment.
      if (!rawUrl) {
        return rawUrl;
      }
      try {
        const path = new window.URL(rawUrl, window.location.origin).pathname;
        const base = (import.meta.env.VITE_API_URL || '/').replace(/\/$/, '');
        // Append the anonymous client id so the backend can attribute the
        // "audio loaded" event (the <audio> element can't send custom headers).
        const clientId = getCachedClientId();
        const query = clientId ? `?cid=${encodeURIComponent(clientId)}` : '';
        return `${base}/${path.replace(/^\//, '')}${query}`;
      } catch {
        return rawUrl;
      }
    },
    onAudioPlay() {
      // First real play per office load; the player guards repeat presses too.
      if (this.audioPlayTracked) {
        return;
      }
      this.audioPlayTracked = true;
      trackEvent(
        'audio_play',
        {
          service_type: this.serviceType,
          office: this.office,
          office_date: this.officeDateStr,
          translation: this.bibleTranslation,
        },
        { toBackend: true, toGA: true }
      );
    },
    async setAudioLinks(url) {
      if (import.meta.env.VITE_FETCH_AUDIO_ON === 'false') return [];
      if (!this.isWithinSevenDays) return [];
      url = `${url}&include_audio_links=true`;
      try {
        const data = await this.$http.get(url);
        const singleTrack = data.data.audio.single_track;
        if (Array.isArray(singleTrack) && singleTrack.length) {
          singleTrack[0] = this.resolveAudioUrl(singleTrack[0]);
        }
        this.audioLinks = singleTrack;
        return singleTrack;
      } catch {
        return [];
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
      if (import.meta.env.VITE_FETCH_AUDIO_ON === 'false') return null;
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
          'speaker',
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
.office-head {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  max-width: 46rem;
  margin: 0 auto;
  padding: var(--space-4) var(--gutter) 0;
}

/* Quiet tools under the day's title: they say "these exist" without
   standing between the reader and the prayers. */
.office-tools {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-1) var(--space-2);
}

.office-tool {
  position: relative;
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

/* A 44px touch target around the slimmer pill */
.office-tool::before {
  content: '';
  position: absolute;
  inset: -0.25rem 0;
}

.office-tool:hover {
  border-color: var(--rule-strong);
  color: var(--ink);
}

.office-tool[aria-pressed='true'] {
  border-color: var(--accent-rule);
  background-color: var(--accent-wash);
  color: var(--ink);
}

.office-tool .ui-icon {
  color: var(--accent);
}

.office-tool__glyph {
  font-size: 1.05em;
  line-height: 1;
}

/* Wide screens: a margin index beside the text, like a book's ribbon. */
.office-body__margin {
  display: none;
}

@media (min-width: 1200px) {
  .office-body {
    display: grid;
    grid-template-columns: minmax(11rem, 1fr) minmax(0, auto) minmax(
        11rem,
        1fr
      );
    align-items: start;
  }

  .office-body__margin {
    display: block;
    align-self: stretch;
    padding-left: var(--gutter);
  }
}

.book-opening {
  margin: var(--space-5) auto var(--space-1);
  text-align: center;
  font-size: 1.5rem;
}
</style>
