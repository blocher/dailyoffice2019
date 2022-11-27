<template>

  <span class="sub-menu-item">
    <a
        href="https://classic.dailyoffice2019.com"
        target="_blank"
    >
      <span class="text-xs">Classic site&nbsp;</span>
      <font-awesome-icon :icon="['fad', 'fa-square-up-right']"/>
    </a>
  </span>
  <br/>
  <span class="sub-menu-item">
    <a
        href="" @click.prevent="toggleSharePanel"
    >
      <span class="text-xs">Share Your Settings&nbsp;</span>
      <font-awesome-icon :icon="['fad', 'share-nodes']"/>&nbsp;
    </a>
  </span>
  <el-drawer
      v-model="showSharePanel" direction="rtl"
      :size="panelSize"
  >
    <div class="mt-4">
      <h3 class="text-left">Share Link</h3>
      <p class="text-left pb-3 mx-1">
        This share link allows you to sync your settings with others with whom
        you are praying.
      </p>

      <p class="text-left pt-2 mx-1 my-4">
        <font-awesome-icon :icon="['fad', 'circle-1']"/>&nbsp;Pick the settings you want to use on the <a
          href="/settings">Settings</a> pages.
      </p>
      <p class="text-left pt-2 mx-1 my-4">
        <font-awesome-icon :icon="['fad', 'circle-2']"/>&nbsp;Return here and click the
        <font-awesome-icon :icon="['fad', 'copy']"/>
        button below (or manually
        copy
        the link).
      </p>
      <div @click="copyLink">
        <el-input
            v-model="shareLink"
            placeholder="Copy and paste share link"
            readonly
        >
          <template #append>
            <div class="copyLinkWrapper">
              <font-awesome-icon :icon="['fad', 'copy']"/>
            </div>
          </template>
        </el-input>
      </div>
    </div>
    <p class="text-left pt-2 mx-1 my-4">
      <font-awesome-icon :icon="['fad', 'circle-3']"/>&nbsp;Paste the link in an email, text message, or chat and
      send to whoever you want to pray with.
    </p>
    <p class="text-left pt-2 mx-1 my-4">
      <font-awesome-icon :icon="['fad', 'circle-4']"/>&nbsp;When the recipients click on the link, the site will
      automatically be
      set up so you are all using the same settings.
    </p>

    <a href="" @click="share($event)">
      <div v-if="canShare" class="full-width border-2 my-4 p-4 text-left">
        <h3 class="text-left pt-0">
          <font-awesome-icon :icon="['fad', 'share-nodes']"/>&nbsp; Share using an app
        </h3>
        <p>Click here to use an app on your phone or computer such as your e-mail client, iMessages, or contact
          book</p>
      </div>
    </a>
  </el-drawer>
</template>

<script>
import {Share} from "@capacitor/share";
import {Clipboard} from "@capacitor/clipboard";
import {ElMessage} from "element-plus";
import {DynamicStorage} from "@/helpers/storage";

export default {
  data() {
    return {
      canShare: false,
      sharePanel: false,
      showSharePanel: false,
      panelSize: "37%",
    };
  },
  computed: {
    shareLink() {
      return this.getShareLink();
    },
  },
  created: async function () {
    window.addEventListener("resize", this.setPanelSize);
    this.setPanelSize()
    const canShare = await Share.canShare();
    this.canShare = canShare.value;
  },
  unmounted() {
    window.removeEventListener("resize", this.setPanelSize);
  },
  methods: {
    setPanelSize() {
      if (window.innerWidth < 1024) {
        this.panelSize = "90%";
      } else {
        this.panelSize = "37%";
      }
    },
    async getCollectProps() {
      const extraCollects = JSON.parse(await DynamicStorage.getItem('extraCollects'))
      if (extraCollects) {
        const queryString = Object.keys(extraCollects)
            .map((key) => key.toLowerCase().replace(" ", "_") + "_collects=" + extraCollects[key])
            .join("&");
        return `&${queryString}`;
      }
      return ""
    },
    getShareLink() {
      this.getCollectProps()
      const settings = this.$store.state.settings;
      const queryString = Object.keys(settings)
          .map((key) => key + "=" + settings[key])
          .join("&") + this.getCollectProps();
      const path = this.$route.path;
      const port = parseInt(window.location.port)
      const port_string = port == 80 || port == 443 ? "" : ":" + port
      const url = `${window.location.protocol}//${window.location.hostname}${port_string}${path}?${queryString}`;
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
    toggleSharePanel() {
      this.showSharePanel = !this.showSharePanel;
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
