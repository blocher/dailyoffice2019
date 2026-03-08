<template>
  <button
    type="button"
    @click.prevent="toggleSharePanel"
    class="w-full h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--accent-color) focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-gray-900 rounded-xl"
  >
    <div
      class="flex flex-col items-center justify-center p-3 h-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-colors group cursor-pointer text-center"
    >
      <font-awesome-icon
        :icon="['fad', 'share-nodes']"
        class="text-lg text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200 mb-2 transition-colors"
      />
      <span
        class="text-xs font-semibold text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100 leading-tight"
        >Share Settings</span
      >
    </div>
  </button>

  <el-drawer
    v-model="showSharePanel"
    direction="rtl"
    :size="panelSize"
    title="Share Settings"
  >
    <template #header>
      <div class="drawer-panel flex items-start gap-4">
        <div
          class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-500/15 dark:text-indigo-300"
        >
          <font-awesome-icon :icon="['fad', 'share-nodes']" class="text-lg" />
        </div>
        <div class="space-y-1 text-left">
          <p
            class="m-0 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400"
          >
            Pray Together
          </p>
          <h2 class="m-0 p-0 text-xl font-semibold tracking-tight text-left">
            Share Settings
          </h2>
          <p class="m-0 text-sm leading-6 text-gray-600 dark:text-gray-300">
            Send one link so everyone uses the same Daily Office settings.
          </p>
        </div>
      </div>
    </template>

    <div class="drawer-panel space-y-6 pb-6 text-left">
      <section
        class="rounded-2xl border border-gray-200 bg-gray-50/80 p-5 dark:border-gray-700 dark:bg-gray-800/60"
      >
        <p
          class="m-0 text-[11px] font-semibold uppercase tracking-[0.16em] text-gray-500 dark:text-gray-400"
        >
          How It Works
        </p>
        <ol class="mt-4 space-y-4 list-none p-0">
          <li class="flex items-start gap-3">
            <span
              class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-xs font-semibold text-gray-700 ring-1 ring-gray-200 dark:bg-gray-900 dark:text-gray-200 dark:ring-gray-700"
              >1</span
            >
            <p class="m-0 text-sm leading-6 text-gray-700 dark:text-gray-300">
              Choose the options you want on the
              <router-link
                to="/settings"
                class="font-semibold text-(--accent-color) no-underline hover:underline"
                >Settings</router-link
              >
              page.
            </p>
          </li>
          <li class="flex items-start gap-3">
            <span
              class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-xs font-semibold text-gray-700 ring-1 ring-gray-200 dark:bg-gray-900 dark:text-gray-200 dark:ring-gray-700"
              >2</span
            >
            <p class="m-0 text-sm leading-6 text-gray-700 dark:text-gray-300">
              Copy the link below or share it directly from your device.
            </p>
          </li>
          <li class="flex items-start gap-3">
            <span
              class="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-xs font-semibold text-gray-700 ring-1 ring-gray-200 dark:bg-gray-900 dark:text-gray-200 dark:ring-gray-700"
              >3</span
            >
            <p class="m-0 text-sm leading-6 text-gray-700 dark:text-gray-300">
              When someone opens the link or scans the QR code, their settings
              are automatically matched to yours.
            </p>
          </li>
        </ol>
      </section>

      <section
        class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-900/70"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3
              class="m-0 p-0 text-base font-semibold tracking-tight text-left"
            >
              Share link
            </h3>
            <p
              class="mt-2 mb-0 text-sm leading-6 text-gray-600 dark:text-gray-300"
            >
              Copy and paste this into a text, email, or chat.
            </p>
          </div>
          <font-awesome-icon
            :icon="['fad', 'link']"
            class="mt-1 text-base text-gray-400 dark:text-gray-500"
          />
        </div>

        <div class="mt-4 flex flex-col gap-3 sm:flex-row">
          <el-input
            v-model="shareLink"
            placeholder="Copy and paste share link"
            readonly
            class="flex-1"
          />
          <el-button type="primary" @click="copyLink">
            <font-awesome-icon :icon="['fad', 'copy']" class="mr-2" />
            Copy link
          </el-button>
        </div>
      </section>

      <section
        v-if="canShare"
        class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-900/70"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3
              class="m-0 p-0 text-base font-semibold tracking-tight text-left"
            >
              Share with another app
            </h3>
            <p
              class="mt-2 mb-0 text-sm leading-6 text-gray-600 dark:text-gray-300"
            >
              Use your device share sheet to send the link through email,
              messages, or another app.
            </p>
          </div>
          <font-awesome-icon
            :icon="['fad', 'paper-plane-top']"
            class="mt-1 text-base text-gray-400 dark:text-gray-500"
          />
        </div>

        <div class="mt-4">
          <el-button type="primary" plain @click="share($event)">
            Share with an app
          </el-button>
        </div>
      </section>

      <section
        class="rounded-2xl border border-gray-200 bg-gray-50/80 p-5 dark:border-gray-700 dark:bg-gray-800/60"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3
              class="m-0 p-0 text-base font-semibold tracking-tight text-left"
            >
              QR code
            </h3>
            <p
              class="mt-2 mb-0 text-sm leading-6 text-gray-600 dark:text-gray-300"
            >
              Open this on another device to apply the same settings instantly.
            </p>
          </div>
          <font-awesome-icon
            :icon="['fad', 'qrcode']"
            class="mt-1 text-base text-gray-400 dark:text-gray-500"
          />
        </div>

        <div class="settings-qr-code mt-5 flex justify-center">
          <div
            class="rounded-2xl bg-white p-4 shadow-sm ring-1 ring-gray-200 dark:bg-gray-900 dark:ring-gray-700"
          >
            <qrcode-vue
              :value="shareLink"
              :size="320"
              :render-as="'svg'"
              level="L"
            />
          </div>
        </div>
      </section>
    </div>
  </el-drawer>
</template>

<script>
import { Share } from '@capacitor/share';
import { Clipboard } from '@capacitor/clipboard';
import { ElMessage } from 'element-plus';
import { DynamicStorage } from '@/helpers/storage';
import { getMessageOffset } from '@/helpers/getMessageOffest';
import { createSettingsString } from '@/helpers/createSettingsString';
import { Capacitor } from '@capacitor/core';
import QrcodeVue from 'qrcode.vue';

export default {
  components: {
    QrcodeVue,
  },
  data() {
    return {
      canShare: false,
      sharePanel: false,
      showSharePanel: false,
      panelSize: '37%',
      shareLink: '',
    };
  },
  created: async function () {
    window.addEventListener('resize', this.setPanelSize);
    this.setPanelSize();
    const canShare = await Share.canShare();
    this.canShare = canShare.value;
    this.shareLink = await this.getCompactLink();
  },
  unmounted() {
    window.removeEventListener('resize', this.setPanelSize);
  },
  methods: {
    setPanelSize() {
      if (window.innerWidth < 1024) {
        this.panelSize = '90%';
      } else {
        this.panelSize = '37%';
      }
    },
    async getCollectProps() {
      const extraCollects = JSON.parse(
        await DynamicStorage.getItem('extraCollects')
      );
      if (extraCollects) {
        const queryString = Object.keys(extraCollects)
          .map(
            (key) =>
              key.toLowerCase().replace(' ', '_') +
              '_collects=' +
              extraCollects[key]
          )
          .join('&');
        return `&${queryString}`;
      }
      return '';
    },
    async getCompactLink() {
      await this.$store.dispatch('initializeSettings');
      const settings = await this.$store.state.settings;
      const settingAbbreviations = this.$store.state.settingAbbreviations;
      const compactSettings = createSettingsString(
        settings,
        settingAbbreviations
      );
      if (compactSettings === false) {
        // If there is an error, fallback to using default
        return await this.getShareLink();
      }
      const queryString =
        'settings=' + compactSettings + (await this.getCollectProps());
      const path = this.$route.path;
      const port = parseInt(window.location.port);
      const port_string =
        port && port !== '80' && port !== '443' ? `:${port}` : '';
      if (Capacitor.getPlatform() !== 'web') {
        return `https://www.dailyoffice2019.com${path}?${queryString}`;
      }
      let url = '';
      if (port_string) {
        url = `${window.location.protocol}//${window.location.hostname}${port_string}${path}?${queryString}`;
      } else {
        url = `${window.location.protocol}//${window.location.hostname}${path}?${queryString}`;
      }
      return url;
    },
    async getShareLink() {
      await this.getCollectProps();
      this.availableSettings = await this.$store.state.availableSettings;
      await this.$store.dispatch('initializeSettings');
      const settings = await this.$store.state.settings;
      const queryString =
        Object.keys(settings)
          .map((key) => key + '=' + settings[key])
          .join('&') + (await this.getCollectProps());
      const path = this.$route.path;
      const port = parseInt(window.location.port);
      const port_string = port === 8080 ? ':8080' : '';
      if (Capacitor.getPlatform() !== 'web') {
        return `https://www.dailyoffice2019.com${path}?${queryString}`;
      }
      let url = '';
      if (port_string) {
        url = `${window.location.protocol}//${window.location.hostname}${port_string}${path}?${queryString}`;
      } else {
        url = `${window.location.protocol}//${window.location.hostname}${path}?${queryString}`;
      }
      return url;
    },
    async copyLink() {
      await Clipboard.write({
        string: await this.getCompactLink(),
      });
      ElMessage.success({
        title: 'Saved',
        message: 'The Share Link has been copied to the clipboard.</small>',
        showClose: true,
        dangerouslyUseHTMLString: true,
        offset: getMessageOffset(),
      });
    },
    async toggleSharePanel() {
      this.showSharePanel = !this.showSharePanel;

      this.shareLink = await this.getCompactLink();
    },

    async share(event) {
      event.preventDefault();
      await Share.share({
        title: 'Pray the Daily Office',
        text: 'Join me in praying the Daily Office using my customized settings',
        url: await this.getCompactLink(),
        dialogTitle: 'Pray with others',
      });
    },
  },
};
</script>
<style scoped lang="scss">
.drawer-panel :is(h1, h2, h3, h4),
.drawer-panel .drawer-kicker {
  text-align: left !important;
}

.settings-qr-code {
  svg,
  canvas {
    max-width: 100%;
    height: auto !important;
  }
}
</style>
