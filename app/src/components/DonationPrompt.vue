<template>
  <section class="support-card surface" aria-labelledby="support-card-title">
    <p class="eyebrow">Free, always</p>
    <h2 id="support-card-title" class="support-card__title">
      <UiIcon name="heart" class="support-card__heart" />
      Support the Daily Office
    </h2>
    <p class="support-card__copy">
      Your gifts pay for hosting, Bible licensing, daily audio, and new work
      like saints’ lives and Spanish editions. There is no paywall, no
      obligation, and no guilt.
    </p>
    <UiButton variant="primary" icon="coffee" @click="openLink">
      Give on Ko-fi
    </UiButton>
    <p class="support-card__fine">
      Secure payments through Ko-fi ·
      <a href="mailto:feedback@dailyoffice2019.com">Questions?</a>
    </p>
  </section>
</template>

<script setup>
import { openExternalLink } from '@/helpers/externalLink';

async function openLink() {
  await openExternalLink('https://ko-fi.com/dailyoffice');
}
</script>

<style scoped>
.support-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  height: 100%;
  padding: var(--space-5);
  text-align: center;
}

.support-card__title {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  font-size: var(--text-lg);
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.08em;
}

.support-card__heart {
  color: var(--accent);
}

.support-card__copy {
  max-width: 24rem;
  font-size: var(--text-sm);
  color: var(--ink-soft);
  line-height: 1.4;
}

.support-card__fine {
  margin-top: auto;
  font-size: var(--text-xs);
  color: var(--ink-faint);
}
</style>
