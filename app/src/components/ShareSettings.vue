<template>
  <UiSheet
    :open="panels.share"
    side="auto"
    eyebrow="Pray together"
    title="Share your settings"
    subtitle="One link gives everyone the same Daily Office."
    @update:open="(value) => (panels.share = value)"
  >
    <section class="sheet-block">
      <h3 class="sheet-block__title"><UiIcon name="link" /> Share link</h3>
      <p class="sheet-block__text">
        Anyone who opens this link — in a text, an email, or a chat — has their
        settings matched to yours. Adjust what it carries on the
        <router-link to="/settings" @click="panels.share = false"
          >Settings</router-link
        >
        page.
      </p>
      <div class="share-link">
        <UiInput
          :model-value="shareLink"
          readonly
          aria-label="Share link"
          @focus="$event.target.select()"
        />
        <UiButton variant="primary" icon="copy" @click="copyLink">
          Copy
        </UiButton>
      </div>
      <div v-if="canShare" class="sheet-block__actions">
        <UiButton icon="send" @click="share">Send with another app</UiButton>
      </div>
    </section>

    <section class="sheet-block">
      <h3 class="sheet-block__title"><UiIcon name="qr" /> QR code</h3>
      <p class="sheet-block__text">
        Scan it with another phone to apply the same settings there.
      </p>
      <div class="share-qr">
        <qrcode-vue
          v-if="shareLink"
          :value="shareLink"
          :size="240"
          render-as="svg"
          level="L"
        />
      </div>
    </section>
  </UiSheet>
</template>

<script>
import { Share } from '@capacitor/share';
import { Clipboard } from '@capacitor/clipboard';
import { Capacitor } from '@capacitor/core';
import QrcodeVue from 'qrcode.vue';
import { DynamicStorage } from '@/helpers/storage';
import { createSettingsString } from '@/helpers/createSettingsString';
import { panels } from '@/helpers/panels';
import { toast } from '@/ui/feedback';

export default {
  components: {
    QrcodeVue,
  },
  data() {
    return {
      canShare: false,
      shareLink: '',
      panels,
    };
  },
  watch: {
    async 'panels.share'(open) {
      if (open) {
        this.shareLink = await this.getCompactLink();
      }
    },
  },
  async created() {
    try {
      const canShare = await Share.canShare();
      this.canShare = canShare.value;
    } catch {
      this.canShare = false;
    }
  },
  methods: {
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
    buildUrl(path, queryString) {
      if (Capacitor.getPlatform() !== 'web') {
        return `https://www.dailyoffice2019.com${path}?${queryString}`;
      }
      const port = parseInt(window.location.port);
      const portString = port && port !== 80 && port !== 443 ? `:${port}` : '';
      return `${window.location.protocol}//${window.location.hostname}${portString}${path}?${queryString}`;
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
        // If there is an error, fall back to the long form
        return await this.getShareLink();
      }
      const queryString =
        'settings=' + compactSettings + (await this.getCollectProps());
      return this.buildUrl(this.$route.path, queryString);
    },
    async getShareLink() {
      await this.$store.dispatch('initializeSettings');
      const settings = await this.$store.state.settings;
      const queryString =
        Object.keys(settings)
          .map((key) => key + '=' + settings[key])
          .join('&') + (await this.getCollectProps());
      return this.buildUrl(this.$route.path, queryString);
    },
    async copyLink() {
      await Clipboard.write({
        string: await this.getCompactLink(),
      });
      toast.success('The share link is copied to your clipboard.');
    },
    // Kept for callers that open the panel directly.
    async toggleSharePanel() {
      panels.share = !panels.share;
    },
    async share() {
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

<style scoped>
.share-link {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.share-link :deep(.ui-input) {
  flex: 1;
  min-width: 0;
}

.share-link :deep(.ui-control) {
  font-size: var(--text-sm);
  color: var(--ink-soft);
}

.share-qr {
  display: flex;
  justify-content: center;
  margin-top: var(--space-4);
  padding: var(--space-4);
  border-radius: var(--radius);
  background-color: #fff;
  border: 1px solid var(--rule);
}

.share-qr :deep(svg) {
  width: 100%;
  max-width: 240px;
  height: auto;
}
</style>
