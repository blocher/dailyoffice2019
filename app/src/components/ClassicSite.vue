<template>
  <div v-if="isNative" class="w-full h-full">
    <a
      :href="webLink"
      @click="openLink($event, webLink)"
      class="block w-full h-full"
    >
      <div
        class="flex flex-col items-center justify-center p-3 h-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-colors group cursor-pointer text-center"
      >
        <font-awesome-icon
          :icon="['fad', 'fa-globe']"
          class="text-lg text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200 mb-2 transition-colors"
        />
        <span
          class="text-xs font-semibold text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100 leading-tight"
          >Web Version</span
        >
      </div>
    </a>
  </div>
  <div v-else class="flex gap-4 w-full h-full justify-center">
    <a
      :href="iosLink"
      @click="openLink($event, iosLink)"
      class="block w-full h-full"
    >
      <div
        class="flex flex-col items-center justify-center p-3 h-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-colors group cursor-pointer text-center"
      >
        <font-awesome-icon
          :icon="['fab', 'fa-apple']"
          class="text-lg text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200 mb-2 transition-colors"
        />
        <span
          class="text-xs font-semibold text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100 leading-tight"
          >iOS App</span
        >
      </div>
    </a>
    <a
      :href="androidLink"
      @click="openLink($event, androidLink)"
      class="block w-full h-full"
    >
      <div
        class="flex flex-col items-center justify-center p-3 h-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-colors group cursor-pointer text-center"
      >
        <font-awesome-icon
          :icon="['fab', 'fa-android']"
          class="text-lg text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200 mb-2 transition-colors"
        />
        <span
          class="text-xs font-semibold text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100 leading-tight"
          >Android App</span
        >
      </div>
    </a>
  </div>
</template>

<script>
import { Capacitor } from '@capacitor/core';
import { Browser } from '@capacitor/browser';

export default {
  data() {
    return {
      webLink: 'https://dailyoffice2019.com/',
      iosLink: 'https://apps.apple.com/us/app/the-daily-office/id1513851259',
      androidLink:
        'https://play.google.com/store/apps/details?id=com.dailyoffice2019.app&hl=en_US',
      isNative: false,
    };
  },
  mounted() {
    // Check if we're running on a native platform (iOS or Android)
    const platform = Capacitor.getPlatform();
    this.isNative = platform === 'ios' || platform === 'android';
  },
  methods: {
    async openLink(event, url) {
      event.preventDefault();
      await Browser.open({ url });
    },
  },
};
</script>

<style scoped>
.sub-menu-item-group {
  display: flex;
  gap: 1rem;
}
</style>
