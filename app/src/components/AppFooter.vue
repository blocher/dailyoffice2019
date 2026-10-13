<template>
  <footer class="app-footer">
    <div class="app-footer__inner">
      <div class="divider"><Ornament glyph="v" /></div>

      <div class="app-footer__cards">
        <DonationPrompt />
        <AHPLogo />
      </div>

      <nav class="app-footer__links" aria-label="Footer">
        <router-link to="/about">About</router-link>
        <button type="button" @click="openPanel('share')">
          Share settings
        </button>
        <button type="button" @click="openPanel('email')">Email updates</button>
        <button type="button" @click="openPanel('feedback')">
          Send feedback
        </button>
        <router-link to="/privacy-policy">Privacy</router-link>
        <a href="#" @click.prevent="open(links.github)">Source code</a>
        <template v-if="isWeb">
          <a href="#" @click.prevent="open(links.ios)">iOS app</a>
          <a href="#" @click.prevent="open(links.android)">Android app</a>
        </template>
        <a v-else href="#" @click.prevent="open(links.web)">Web version</a>
      </nav>

      <p class="app-footer__credit">
        The Book of Common Prayer (2019) is used by permission of the Anglican
        Church in North America.
      </p>
    </div>
  </footer>
</template>

<script setup>
import { Browser } from '@capacitor/browser';
import { Capacitor } from '@capacitor/core';
import AHPLogo from '@/components/AHPLogo.vue';
import DonationPrompt from '@/components/DonationPrompt.vue';
import { openPanel } from '@/helpers/panels';

const isWeb = Capacitor.getPlatform() === 'web';

const links = {
  github: 'https://github.com/blocher/dailyoffice2019',
  ios: 'https://apps.apple.com/us/app/the-daily-office/id1513851259',
  android:
    'https://play.google.com/store/apps/details?id=com.dailyoffice2019.app&hl=en_US',
  web: 'https://dailyoffice2019.com/',
};

async function open(url) {
  await Browser.open({ url });
}
</script>

<style scoped>
.app-footer {
  margin-top: var(--space-7);
  padding-bottom: calc(var(--space-6) + env(safe-area-inset-bottom));
}

.app-footer__inner {
  max-width: 52rem;
  margin: 0 auto;
  padding: 0 var(--gutter);
}

.app-footer__inner .divider {
  font-size: 1.4rem;
  margin-bottom: var(--space-6);
}

.app-footer__cards {
  display: grid;
  gap: var(--space-4);
}

@media (min-width: 720px) {
  .app-footer__cards {
    grid-template-columns: 1fr 1fr;
  }
}

.app-footer__links {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0 var(--space-4);
  margin-top: var(--space-5);
  font-size: var(--text-sm);
}

.app-footer__links a,
.app-footer__links button {
  display: inline-flex;
  align-items: center;
  min-height: 2.75rem;
  color: var(--ink-soft);
  text-decoration: none;
}

.app-footer__links a:hover,
.app-footer__links button:hover {
  color: var(--accent);
}

.app-footer__credit {
  margin-top: var(--space-4);
  font-size: var(--text-xs);
  font-style: italic;
  text-align: center;
  color: var(--ink-faint);
}
</style>
