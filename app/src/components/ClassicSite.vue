<template>
  <span v-if="isNative" class="sub-menu-item">
    <a :href="webLink" @click="openLink($event, webLink)">
      <font-awesome-icon :icon="['fad', 'fa-globe']" /><br />
      <span class="text-xs">Web Version&nbsp;</span>
    </a>
  </span>
  <span v-else class="sub-menu-item-group">
    <span class="sub-menu-item">
      <a :href="iosLink" @click="openLink($event, iosLink)">
        <font-awesome-icon :icon="['fab', 'fa-apple']" /><br />
        <span class="text-xs">iOS App&nbsp;</span>
      </a>
    </span>
    <span class="sub-menu-item">
      <a :href="androidLink" @click="openLink($event, androidLink)">
        <font-awesome-icon :icon="['fab', 'fa-android']" /><br />
        <span class="text-xs">Android App&nbsp;</span>
      </a>
    </span>
  </span>
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
