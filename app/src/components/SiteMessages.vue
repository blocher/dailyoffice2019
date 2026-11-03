<template>
  <Transition name="site-messages">
    <div v-if="visibleMessages.length || hasNew" class="site-messages">
      <WhatsNewBanner />
      <div
        v-for="message in visibleMessages"
        :key="message.uuid"
        class="site-message"
        role="region"
        aria-label="Announcement"
      >
        <UiTag
          v-if="message.tag_text"
          class="site-message__tag"
          :class="{ 'is-link': message.link }"
          :tone="tagTone(message.tag_color)"
          @click="follow(message)"
        >
          {{ message.tag_text }}
        </UiTag>
        <p class="site-message__text">
          <router-link
            v-if="message.link && !isExternal(message.link)"
            :to="message.link"
          >
            {{ message.text }}
          </router-link>
          <a v-else-if="message.link" href="#" @click.prevent="follow(message)">
            {{ message.text }}
          </a>
          <span v-else>{{ message.text }}</span>
        </p>
        <button
          v-if="message.dismissible"
          type="button"
          class="site-message__close"
          aria-label="Dismiss"
          @click="dismiss(message)"
        >
          <UiIcon name="close" />
        </button>
      </div>
    </div>
  </Transition>
</template>

<script>
import { App } from '@capacitor/app';
import { openExternalLink } from '@/helpers/externalLink';
import { Capacitor } from '@capacitor/core';

import WhatsNewBanner from '@/components/WhatsNewBanner.vue';
import { addToStoredList, readStoredList } from '@/helpers/storedList';
import { KIND_UPDATE, newWhatsNew, setWhatsNew } from '@/helpers/whatsNew';

const PERMANENT_STORAGE_KEY = 'dismissedSiteMessages';
const SESSION_STORAGE_KEY = 'dismissedSiteMessages';
const WHATS_NEW = 'whats_new';
// Both kinds share the What's New banner and sheet.
const GROUPED = [WHATS_NEW, KIND_UPDATE];

// Admin-chosen tag colors mapped onto the app's tones.
const TAG_TONES = {
  emerald: 'success',
  blue: 'info',
  amber: 'warning',
  red: 'error',
  purple: 'accent',
  gray: 'neutral',
};

// The store version (iOS CFBundleShortVersionString, Android versionName),
// so the server can limit messages to some app versions. The web has none.
async function nativeAppVersion() {
  if (!Capacitor.isNativePlatform()) {
    return null;
  }
  try {
    const info = await App.getInfo();
    return info.version || null;
  } catch {
    return null;
  }
}

export default {
  name: 'SiteMessages',
  components: { WhatsNewBanner },
  data() {
    return {
      messages: [],
      dismissedIds: [],
    };
  },
  computed: {
    // Notices, each its own banner. What's New and Update entries share one.
    visibleMessages() {
      return this.messages.filter(
        (message) =>
          !GROUPED.includes(message.kind) &&
          !this.dismissedIds.includes(message.uuid)
      );
    },
    hasNew() {
      return newWhatsNew.value.length > 0;
    },
  },
  async created() {
    this.loadDismissed();
    await this.fetchMessages();
  },
  methods: {
    loadDismissed() {
      this.dismissedIds = Array.from(
        new Set([
          ...readStoredList('localStorage', PERMANENT_STORAGE_KEY),
          ...readStoredList('sessionStorage', SESSION_STORAGE_KEY),
        ])
      );
    },
    async fetchMessages() {
      try {
        const platform = Capacitor.getPlatform();
        // Asking for What's New and Update entries too; without ?kinds= the
        // server sends notices only, as the 4.0.0 apps expect. The website
        // never gets Update entries.
        const params = { platform, kinds: ['notice', ...GROUPED].join(',') };
        const appVersion = await nativeAppVersion();
        if (appVersion) {
          params.app_version = appVersion;
        }
        const response = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/site_messages/`,
          { params }
        );
        this.messages = Array.isArray(response.data) ? response.data : [];
      } catch {
        this.messages = [];
        setWhatsNew([], { failed: true });
        return;
      }
      setWhatsNew(
        this.messages.filter((message) => GROUPED.includes(message.kind))
      );
    },
    tagTone(color) {
      return TAG_TONES[color] || 'neutral';
    },
    isExternal(link) {
      return /^https?:\/\//i.test(link) || /^mailto:/i.test(link);
    },
    // The tag follows the link too: it reads like a button ("Book View!").
    async follow(message) {
      if (!message.link) return;
      if (this.isExternal(message.link)) {
        await openExternalLink(message.link);
      } else {
        await this.$router.push(message.link);
      }
    },
    dismiss(message) {
      if (this.dismissedIds.includes(message.uuid)) {
        return;
      }
      this.dismissedIds = [...this.dismissedIds, message.uuid];
      addToStoredList(
        message.dismiss_permanent ? 'localStorage' : 'sessionStorage',
        message.dismiss_permanent ? PERMANENT_STORAGE_KEY : SESSION_STORAGE_KEY,
        [message.uuid]
      );
    },
  },
};
</script>

<style scoped>
/* The whole block fades when its last banner goes. */
.site-messages-leave-active {
  transition: opacity 220ms var(--ease);
}

.site-messages-leave-to {
  opacity: 0;
}

.site-messages {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-width: 46rem;
  margin: var(--space-3) auto 0;
  padding: 0 var(--gutter);
}

.site-message {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-2) var(--space-2) var(--space-4);
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background-color: var(--paper-raised);
  font-size: var(--text-sm);
  line-height: 1.35;
}

.site-message__tag.is-link {
  cursor: pointer;
}

.site-message__text {
  flex: 1;
  min-width: 0;
  overflow-wrap: break-word;
  color: var(--ink-soft);
}

/* Phones: the tag sits above the text so the text gets the full width. */
@media (max-width: 559px) {
  .site-message {
    display: grid;
    grid-template-columns: 1fr auto;
    grid-template-areas:
      'tag close'
      'text text';
    row-gap: var(--space-1);
  }

  .site-message__tag {
    grid-area: tag;
    justify-self: start;
  }

  .site-message__text {
    grid-area: text;
  }

  .site-message__close {
    grid-area: close;
  }

  .site-message:not(:has(.site-message__tag)) {
    grid-template-areas: 'text close';
  }
}

.site-message__close {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 2.75rem;
  height: 2.75rem;
  margin: -0.4rem -0.3rem -0.4rem 0;
  border-radius: 50%;
  color: var(--ink-faint);
}

.site-message__close:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}
</style>
