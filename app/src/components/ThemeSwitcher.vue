<template>
  <div class="theme-switcher-wrapper w-full text-right mt-2 pr-6">
    <span class="sub-menu-item">
      <a href="" v-on:click.prevent="panel = true">
        <font-awesome-icon :icon="['fad', 'share-nodes']" />&nbsp;
        <span class="text-xs">Share your settings</span>
      </a>
    </span>
    <el-drawer v-model="panel" direction="rtl">
      <div class="mt-4">
        <h3>Share Link</h3>
        <p class="text-left pb-3 mx-1">
          This share link allows you to sync your settings with others with whom
          you are praying.
        </p>
        <div v-on:click="copyLink">
          <el-input
            v-model="shareLink"
            placeholder="Copy and paste share link"
            readonly
          >
            <template #append>
              <div class="copyLinkWrapper">
                <font-awesome-icon :icon="['fad', 'copy']" />
              </div>
            </template>
          </el-input>
        </div>
      </div>
      <p class="text-left text-sm pt-2 mx-1">
        Click on the share link above to copy it to your clipboard. You can then
        then paste it into an email or text message and send it to those with
        whom you are praying. When they receive the link, they can click on it
        to open this page with your settings already preselected.
      </p>
      <p class="text-left mt-4" v-if="canShare">
        <a href="" v-on:click="share($event)">
          <font-awesome-icon :icon="['fad', 'share-nodes']" />&nbsp;
          <span class="text-xs"
            >Share using an app installed on your computer or device</span
          >
        </a>
      </p>
    </el-drawer>
    <span class="sub-menu-item">
      <span class="text-xs">Light Mode</span>&nbsp;
      <el-switch
        v-model="userTheme"
        class="text-right"
        active-value="dark-theme"
        inactive-value="light-theme"
      ></el-switch
      >&nbsp;
      <span class="text-xs">Dark Mode</span>
    </span>
    <span class="sub-menu-item">
      <span>
        <a href="https://www.facebook.com/groups/dailyoffice" target="_blank:">
          <font-awesome-icon :icon="['fab', 'facebook']" />
        </a>
      </span>
    </span>
  </div>
</template>

<style>
.sub-menu-item {
  margin-left: 35px;
}
</style>

<script>
import { Share } from "@capacitor/share";
import { Clipboard } from "@capacitor/clipboard";
import { ElMessage } from "element-plus";

export default {
  data() {
    return {
      userTheme: "light-theme",
      canShare: false,
      panel: false,
    };
  },
  created: async function () {
    const canShare = await Share.canShare();
    this.canShare = canShare.value;
  },
  mounted() {
    let activeTheme = localStorage.getItem("user-theme");
    if (!activeTheme) {
      activeTheme = this.getMediaPreference();
    }
    this.setTheme(activeTheme, false);
    this.$watch("userTheme", this.setTheme);
  },
  computed: {
    shareLink() {
      return this.getShareLink();
    },
  },
  methods: {
    getShareLink() {
      const settings = this.$store.state.settings;
      const queryString = Object.keys(settings)
        .map((key) => key + "=" + settings[key])
        .join("&");
      const path = this.$route.path;
      const url = `${window.location.protocol}//${window.location.hostname}${path}?${queryString}`;
      return url;
    },
    async copyLink() {
      await Clipboard.write({
        string: this.getShareLink(),
      });
      ElMessage.success({
        title: "Saved",
        message: "The Share Link has been copied to the clipboard.</small>",
        showClose: true,
        dangerouslyUseHTMLString: true,
      });
    },
    setTheme(theme, store = true) {
      if (store) {
        localStorage.setItem("user-theme", theme);
      }
      this.userTheme = theme;
      document.documentElement.className = theme;
    },
    getMediaPreference() {
      const hasDarkPreference = window.matchMedia(
        "(prefers-color-scheme: dark)"
      ).matches;
      if (hasDarkPreference) {
        return "dark-theme";
      } else {
        return "light-theme";
      }
    },

    async share(event) {
      event.preventDefault();
      await Share.share({
        title: "Pray the Daily Office",
        text: "Join me in praying the Daily Office using my customized settings",
        url: this.getShareLink(),
        dialogTitle: "Pray with others",
      });
    },
  },
};
</script>
