<template>
  <span class="sub-menu-item">
    <a href="" @click.prevent="sharePanel = true">
      <font-awesome-icon :icon="['fad', 'share-nodes']" />&nbsp;
      <span class="text-xs">Share Settings</span>
    </a>
  </span>
  <el-drawer v-model="sharePanel" direction="rtl" :size="panelSize">
    <div class="mt-4">
      <h3>Share Link</h3>
      <p class="text-left pb-3 mx-1">
        This share link allows you to sync your settings with others with whom
        you are praying.
      </p>
      <div @click="copyLink">
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
      then paste it into an email or text message and send it to those with whom
      you are praying. When they receive the link, they can click on it to open
      this page with your settings already preselected.
    </p>
    <p v-if="canShare" class="text-left mt-4">
      <a href="" @click="share($event)">
        <font-awesome-icon :icon="['fad', 'share-nodes']" />&nbsp;
        <span class="text-xs"
          >Share using an app installed on your computer or device</span
        >
      </a>
    </p>
  </el-drawer>
</template>

<script setup>
import { useFlexibleDrawer } from "@/components/useFlexibleDrawer";

const { panelSize } = useFlexibleDrawer();
</script>

<script>
import { Share } from "@capacitor/share";
import { Clipboard } from "@capacitor/clipboard";
import { ElMessage } from "element-plus";

export default {
  data() {
    return {
      canShare: false,
      sharePanel: false,
    };
  },
  computed: {
    shareLink() {
      return this.getShareLink();
    },
  },
  created: async function () {
    const canShare = await Share.canShare();
    this.canShare = canShare.value;
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
