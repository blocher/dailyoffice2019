<template>
  <a class="skip-link" href="#content" @click.prevent="skipToContent"
    >Skip to content</a
  >
  <AppHeader />

  <main id="content" class="app-main" tabindex="-1" :style="mainStyle">
    <Loading v-if="loading" />
    <div v-if="error" class="app-error">
      <UiAlert tone="error" :title="error" />
    </div>
    <SiteMessages v-if="!loading" />
    <router-view v-if="!loading" :key="routeKey" />
  </main>

  <AppFooter v-if="showLinks" :style="mainStyle" />
  <BackToTop :offset="audioBarHeight" />

  <AppMenu />
  <DisplayPanel />
  <ShareSettings />
  <EmailSignup />
  <SubmitFeedback />
  <UiFeedbackHost />
</template>

<script>
import { defineAsyncComponent } from 'vue';
import { useActiveMeta, useMeta } from 'vue-meta';
import { useRoute } from 'vue-router';
import AppFooter from '@/components/AppFooter.vue';
import AppHeader from '@/components/AppHeader.vue';
import AppMenu from '@/components/AppMenu.vue';
import BackToTop from '@/components/BackToTop.vue';
import DisplayPanel from '@/components/DisplayPanel.vue';
import EmailSignup from '@/components/EmailSignup.vue';
import Loading from '@/components/Loading.vue';
import SiteMessages from '@/components/SiteMessages.vue';
import SubmitFeedback from '@/components/SubmitFeedback.vue';
import UiFeedbackHost from '@/ui/UiFeedbackHost.vue';
import { applyAll } from '@/helpers/displayPreferences';

// The share panel (with its QR code library) loads after the first page.
const ShareSettings = defineAsyncComponent(
  () => import('@/components/ShareSettings.vue')
);

export default {
  components: {
    AppFooter,
    AppHeader,
    AppMenu,
    BackToTop,
    DisplayPanel,
    EmailSignup,
    Loading,
    ShareSettings,
    SiteMessages,
    SubmitFeedback,
    UiFeedbackHost,
  },
  setup() {
    const route = useRoute();
    // Bind title to current route meta so it doesn't revert to the default
    useMeta(() => ({
      title: route.meta?.title || 'The Daily Office',
      htmlAttrs: { lang: 'en' },
      viewport: 'width=device-width, initial-scale=1.0, viewport-fit=cover',
    }));
    useActiveMeta();
  },
  data() {
    return {
      loading: true,
      error: false,
      showLinks: false,
      audioBarHeight: 0,
    };
  },
  computed: {
    routeKey() {
      if (this.$route.name && this.$route.name.startsWith('readings')) {
        const d = new Date();
        const y = this.$route.params.year || d.getFullYear();
        const m = this.$route.params.month || d.getMonth() + 1;
        const day = this.$route.params.day || d.getDate();
        return `readings-${y}-${m}-${day}`;
      }
      // Stable key so /calendar, /calendar?…, and /calendar/:y/:m/ reuse the
      // same instance (e.g. subscription drawer stays open when query/path updates).
      if (this.$route.name === 'calendar') {
        return 'calendar';
      }
      // The Psalter filters by ?topic= in place.
      if (this.$route.name === 'Psalms') {
        return 'psalms';
      }
      return this.$route.fullPath;
    },
    // Keep content clear of the fixed audio bar when it is showing.
    mainStyle() {
      return this.audioBarHeight > 0
        ? { paddingBottom: `${this.audioBarHeight + 16}px` }
        : null;
    },
  },
  watch: {
    async '$route.fullPath'() {
      await this.$nextTick();
      applyAll();
    },
  },
  mounted() {
    document.addEventListener(
      'audio-player-visibility',
      this.onAudioVisibilityEvent
    );
  },
  unmounted() {
    document.removeEventListener(
      'audio-player-visibility',
      this.onAudioVisibilityEvent
    );
  },
  async created() {
    try {
      const settingsData = await this.$http.get(
        `${import.meta.env.VITE_API_URL}api/v1/available_settings/`
      );
      await this.$store.commit('saveAvailableSettings', settingsData.data);
      await this.$store.dispatch('initializeSettings');
    } catch {
      this.error =
        'There was an error loading the settings. Please try refreshing the page.';
    }
    this.loading = false;
    await this.$nextTick();
    this.showLinks = true;
  },
  methods: {
    // Move focus without changing the address, which would reload the page.
    skipToContent() {
      document.getElementById('content').focus();
    },
    onAudioVisibilityEvent(event) {
      const payload = event.detail || {};
      this.audioBarHeight = payload.visible ? Number(payload.height) || 0 : 0;
    },
  },
};
</script>

<style>
.skip-link {
  position: absolute;
  left: var(--space-3);
  top: -3rem;
  z-index: 200;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius);
  background-color: var(--paper-raised);
}

/* The shadow only while showing, so none spills from off-screen. */
.skip-link:focus {
  top: calc(env(safe-area-inset-top) + var(--space-2));
  box-shadow: var(--shadow);
}

.app-main {
  min-height: calc(var(--vvh) - var(--header-height) - 10rem);
}

/* Focused only as a skip-link target, not as a control. */
.app-main:focus {
  outline: none;
}

.app-error {
  max-width: var(--content-width);
  margin: var(--space-4) auto 0;
  padding: 0 var(--gutter);
}
</style>
