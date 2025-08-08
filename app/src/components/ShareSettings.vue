<template>
  <div class="settings-action">
    <button @click.prevent="toggleSharePanel" class="action-button">
      <span class="action-icon">🔗</span>
      <span class="action-text">Share Settings</span>
    </button>
  </div>
  
  <el-drawer v-model="showSharePanel" direction="rtl" :size="panelSize" class="elegant-drawer">
    <div class="drawer-content">
      <h2 class="drawer-title">
        🔗 Share Link
      </h2>
      <p class="drawer-description">
        This share link allows you to sync your settings with others with whom
        you are praying.
      </p>

      <div class="step-instructions">
        <p class="instruction-step">
          <span class="step-number">1</span>Pick the settings
          you want to use on the <a href="/settings">Settings</a> pages.
        </p>
        <p class="instruction-step">
          <span class="step-number">2</span>Return here and
          click the copy button below (or manually copy the link).
        </p>
        <div @click="copyLink" class="link-input-container">
          <el-input
            v-model="shareLink"
            placeholder="Copy and paste share link"
            readonly
            class="share-input"
          >
            <template #append>
              <div class="copy-button">
                📋
              </div>
            </template>
          </el-input>
        </div>
        <p class="instruction-step">
          <span class="step-number">3</span>Paste the link in
          an email, text message, or chat and send to whoever you want to pray
          with.
        </p>
        <p class="instruction-step">
          <span class="step-number">4</span>When the
          recipients click on the link, the site will automatically be set up so
          you are all using the same settings.
        </p>
      </div>

      <div class="link-details">
        <el-collapse>
          <el-collapse-item title="🔧 Advanced Options" name="1">
            <p>
              <a target="_blank" :href="shareLink">{{ shareLink }}</a>
            </p>
            <QrcodeVue :value="shareLink" :size="200" level="M" />
          </el-collapse-item>
        </el-collapse>
      </div>
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

<style lang="scss" scoped>
.settings-action {
  display: flex;
  justify-content: center;
}

.action-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  color: var(--font-color);
  font-family: 'Adobe Caslon Pro', serif;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  min-width: 100px;
}

.action-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

:root.dark .action-button {
  border: 1px solid rgba(255, 255, 255, 0.1);
}

:root.dark .action-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.action-icon {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.action-text {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  text-align: center;
  line-height: 1.2;
}

.elegant-drawer {
  .el-drawer__body {
    padding: 0;
  }
}

.drawer-content {
  padding: 2rem;
  font-family: 'Adobe Caslon Pro', serif;
}

.drawer-title {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin: 0 0 1rem 0;
  color: var(--font-color);
  text-align: left;
  padding-top: 0;
}

.drawer-description {
  font-size: 1rem;
  line-height: 1.5;
  margin-bottom: 2rem;
  color: var(--font-color);
  opacity: 0.9;
  text-align: left;
  padding-bottom: 0.5rem;
  margin: 0 0.25rem 2rem 0.25rem;
}

.step-instructions {
  margin-bottom: 2rem;
}

.instruction-step {
  display: flex;
  align-items: flex-start;
  margin: 1rem 0.25rem;
  padding: 0.5rem 0;
  text-align: left;
  line-height: 1.5;
}

.step-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background-color: rgba(0, 0, 0, 0.1);
  color: var(--font-color);
  border-radius: 50%;
  font-weight: 600;
  font-size: 0.8rem;
  margin-right: 0.75rem;
  flex-shrink: 0;
  margin-top: 0.1rem;
}

:root.dark .step-number {
  background-color: rgba(255, 255, 255, 0.2);
}

.link-input-container {
  margin: 1rem 0;
}

.share-input {
  font-family: 'Adobe Caslon Pro', serif;
}

.copy-button {
  cursor: pointer;
  padding: 0.5rem;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  transition: background-color 0.2s ease;
}

.copy-button:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

:root.dark .copy-button {
  background-color: rgba(255, 255, 255, 0.1);
}

:root.dark .copy-button:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.link-details {
  margin-top: 2rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  padding-top: 1rem;
}

:root.dark .link-details {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.settings-qr-code {
  svg,
  canvas {
    max-width: 100%;
    height: auto !important;
  }
}
</style>
