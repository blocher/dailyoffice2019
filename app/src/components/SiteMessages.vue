<template>
  <div
    v-if="visibleMessages.length"
    class="mx-auto mt-2 mb-3 max-w-[700px] space-y-2 px-4 sm:mt-3 sm:mb-4 sm:px-5"
  >
    <div
      v-for="message in visibleMessages"
      :key="message.uuid"
      class="flex flex-wrap items-center gap-2 rounded-lg border border-slate-200/90 bg-slate-50/90 px-3 py-2.5 text-left text-slate-600 shadow-sm dark:border-slate-600/50 dark:bg-slate-800/40 dark:text-slate-300 sm:gap-3"
      role="region"
      aria-label="Announcement"
    >
      <span
        v-if="message.tag_text"
        class="inline-flex shrink-0 items-center rounded-md px-2 py-1 text-[10px] font-semibold uppercase leading-none tracking-wide"
        :class="tagClasses(message.tag_color)"
      >
        {{ message.tag_text }}
      </span>

      <p class="m-0 min-w-0 flex-1 text-xs leading-snug sm:text-sm">
        <router-link
          v-if="message.link && !isExternal(message.link)"
          class="font-medium text-(--accent-color) underline decoration-(--accent-color)/30 underline-offset-2 transition hover:decoration-(--accent-color)"
          :to="message.link"
        >
          {{ message.text }}
        </router-link>
        <a
          v-else-if="message.link"
          href="#"
          class="font-medium text-(--accent-color) underline decoration-(--accent-color)/30 underline-offset-2 transition hover:decoration-(--accent-color)"
          @click.prevent="openExternal(message.link)"
        >
          {{ message.text }}
        </a>
        <span v-else>{{ message.text }}</span>
      </p>

      <button
        v-if="message.dismissible"
        type="button"
        class="ml-auto shrink-0 rounded-md px-2 py-1 text-sm leading-none text-slate-400 transition hover:bg-slate-200/80 hover:text-slate-700 dark:hover:bg-slate-700/60 dark:hover:text-slate-200"
        aria-label="Dismiss"
        @click="dismiss(message)"
      >
        ×
      </button>
    </div>
  </div>
</template>

<script>
import { Browser } from '@capacitor/browser';
import { Capacitor } from '@capacitor/core';

const PERMANENT_STORAGE_KEY = 'dismissedSiteMessages';
const SESSION_STORAGE_KEY = 'dismissedSiteMessages';

const TAG_COLOR_CLASSES = {
  emerald:
    'bg-emerald-100/90 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200',
  blue: 'bg-blue-100/90 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200',
  amber:
    'bg-amber-100/90 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200',
  red: 'bg-red-100/90 text-red-800 dark:bg-red-900/50 dark:text-red-200',
  purple:
    'bg-purple-100/90 text-purple-800 dark:bg-purple-900/50 dark:text-purple-200',
  gray: 'bg-slate-200/90 text-slate-700 dark:bg-slate-700/60 dark:text-slate-200',
};

function readStorage(storage, key) {
  try {
    const raw = storage.getItem(key);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export default {
  name: 'SiteMessages',
  data() {
    return {
      messages: [],
      dismissedIds: [],
    };
  },
  computed: {
    visibleMessages() {
      return this.messages.filter(
        (message) => !this.dismissedIds.includes(message.uuid)
      );
    },
  },
  async created() {
    this.loadDismissed();
    await this.fetchMessages();
  },
  methods: {
    loadDismissed() {
      const ids = new Set();
      if (typeof window !== 'undefined') {
        if (window.localStorage) {
          readStorage(window.localStorage, PERMANENT_STORAGE_KEY).forEach(
            (id) => ids.add(id)
          );
        }
        if (window.sessionStorage) {
          readStorage(window.sessionStorage, SESSION_STORAGE_KEY).forEach(
            (id) => ids.add(id)
          );
        }
      }
      this.dismissedIds = Array.from(ids);
    },
    async fetchMessages() {
      try {
        const platform = Capacitor.getPlatform();
        const response = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/site_messages/`,
          { params: { platform } }
        );
        this.messages = Array.isArray(response.data) ? response.data : [];
      } catch {
        this.messages = [];
      }
    },
    tagClasses(color) {
      return TAG_COLOR_CLASSES[color] || TAG_COLOR_CLASSES.gray;
    },
    isExternal(link) {
      return /^https?:\/\//i.test(link) || /^mailto:/i.test(link);
    },
    async openExternal(link) {
      await Browser.open({ url: link });
    },
    dismiss(message) {
      if (this.dismissedIds.includes(message.uuid)) {
        return;
      }
      this.dismissedIds = [...this.dismissedIds, message.uuid];
      if (typeof window === 'undefined') {
        return;
      }
      const storage = message.dismiss_permanent
        ? window.localStorage
        : window.sessionStorage;
      if (!storage) {
        return;
      }
      const stored = readStorage(
        storage,
        message.dismiss_permanent ? PERMANENT_STORAGE_KEY : SESSION_STORAGE_KEY
      );
      if (!stored.includes(message.uuid)) {
        stored.push(message.uuid);
        storage.setItem(
          message.dismiss_permanent
            ? PERMANENT_STORAGE_KEY
            : SESSION_STORAGE_KEY,
          JSON.stringify(stored)
        );
      }
    },
  },
};
</script>
