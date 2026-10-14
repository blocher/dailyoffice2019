<template>
  <div class="page page--wide podcasts">
    <header class="page-header">
      <p class="eyebrow">Listen</p>
      <h1 class="page-title">Podcasts</h1>
      <p class="page-lede">
        Pray the Daily Office from your podcast app. A new episode of every
        office arrives each day, with the same prayers, readings, and voices as
        Listen in the app, and a link to pray along with the text.
      </p>
    </header>

    <ul class="podcast-points" aria-label="About the podcasts">
      <li>
        <UiIcon name="calendar" class="podcast-points__icon" />
        <span
          ><strong>New every day.</strong> Each day’s episodes are ready by
          3&nbsp;a.m. Eastern.</span
        >
      </li>
      <li>
        <UiIcon name="book" class="podcast-points__icon" />
        <span
          ><strong>Pray along.</strong> Every episode links to that day’s office
          with the podcast’s settings.</span
        >
      </li>
      <li>
        <UiIcon name="heart" class="podcast-points__icon" />
        <span
          ><strong>Free.</strong> No ads, no account, in any podcast app.</span
        >
      </li>
    </ul>

    <div class="podcasts-style">
      <UiSegmented
        v-model="style"
        :options="styleOptions"
        aria-label="Language of the podcasts"
      />
      <p class="podcasts-style__note">{{ styleNote }}</p>
    </div>

    <Loading v-if="loading" />
    <UiAlert v-if="error" tone="error" :title="error">
      <UiButton variant="secondary" size="sm" @click="load">Try again</UiButton>
    </UiAlert>

    <template v-if="!loading && !error">
      <section
        v-for="group in groups"
        :key="group.slug"
        class="podcast-group"
        :aria-labelledby="`podcast-group-${group.slug}`"
      >
        <div class="podcast-group__head">
          <h2 :id="`podcast-group-${group.slug}`" class="section-title">
            {{ group.title }}
          </h2>
          <p class="podcast-group__lede">{{ group.description }}</p>
        </div>
        <ul class="podcast-grid">
          <li
            v-for="feed in feedsIn(group.slug)"
            :key="feed.slug"
            class="podcast-card surface"
          >
            <img
              class="podcast-card__art"
              :src="feed.artwork_small_url"
              alt=""
              width="600"
              height="600"
              loading="lazy"
            />
            <div class="podcast-card__body">
              <h3 class="podcast-card__title">{{ feed.title }}</h3>
              <p class="podcast-card__subtitle">{{ feed.subtitle }}</p>
              <p v-if="feed.latest_episode" class="podcast-card__latest">
                <span class="eyebrow">Latest</span>
                {{ feed.latest_episode.title }}
                <span class="podcast-card__duration"
                  >({{ minutes(feed.latest_episode.duration) }})</span
                >
              </p>
              <p v-else class="podcast-card__latest podcast-card__latest--soon">
                The first episodes are on their way.
              </p>
            </div>
            <div class="cluster podcast-card__actions">
              <UiButton
                variant="primary"
                size="sm"
                icon="podcast"
                @click="openSubscribe(feed)"
              >
                Subscribe
              </UiButton>
              <UiButton
                v-if="feed.latest_episode"
                variant="ghost"
                size="sm"
                :icon="playing === feed.slug ? 'pause' : 'play'"
                :aria-pressed="playing === feed.slug ? 'true' : 'false'"
                @click="togglePreview(feed)"
              >
                {{ playing === feed.slug ? 'Pause' : 'Play latest' }}
              </UiButton>
              <UiButton
                v-if="feed.latest_episode"
                variant="quiet"
                size="sm"
                :to="followAlongHref(feed)"
              >
                {{ feed.is_readings ? 'Read along' : 'Pray along' }}
              </UiButton>
            </div>
          </li>
        </ul>
      </section>
    </template>

    <div class="divider"><Ornament glyph="v" /></div>

    <section
      v-if="alternative"
      class="podcast-alternative surface"
      aria-labelledby="podcast-alternative-title"
    >
      <UiIcon name="mic" class="podcast-alternative__icon" />
      <div>
        <h2 id="podcast-alternative-title" class="section-title">
          Prefer a human voice?
        </h2>
        <p>
          <strong>{{ alternative.title }}.</strong>
          {{ alternative.description }}
        </p>
        <div class="cluster">
          <UiButton
            v-for="link in alternative.links"
            :key="link.platform"
            variant="secondary"
            size="sm"
            :icon="platformIcon(link.platform)"
            :href="link.url"
            target="_blank"
          >
            {{ platformLabel(link.platform) }}
          </UiButton>
        </div>
      </div>
    </section>

    <section class="podcast-faq" aria-labelledby="podcast-faq-title">
      <h2 id="podcast-faq-title" class="section-title">Questions</h2>
      <UiDisclosure title="Which settings do the podcasts use?">
        <p>
          Every office podcast uses one fixed set of settings, the same ones its
          “Pray along” link applies: the sixty-day psalter, the one-year Daily
          Office lectionary with full-length readings, the long confession on
          fast days, the lay form of the absolution, rotating suffrages and
          collects, the General Thanksgiving and the Prayer of St. John
          Chrysostom, and the Great Litany at Morning Prayer on Wednesdays,
          Fridays, and Sundays.
        </p>
        <p>
          The contemporary podcasts, readings included, use the English Standard
          Version and the contemporary psalter; the traditional-language
          podcasts use the King James Version and the traditional psalter. To
          pray with your own settings, turn on
          <router-link to="/">Listen</router-link> in any office.
        </p>
      </UiDisclosure>
      <UiDisclosure title="When do new episodes appear?">
        <p>
          Each day’s episodes are published at 3&nbsp;a.m. Eastern Time, so they
          are waiting in your app when you wake. Episodes stay in the feed for
          good.
        </p>
      </UiDisclosure>
      <UiDisclosure title="Who is reading?">
        <p>
          The offices are read with synthesized (AI) voices, generated by the
          Daily Office so that every office is ready every day of the year,
          including the Great Litany, the collects of each saint’s day, and the
          full appointed readings.
        </p>
      </UiDisclosure>
      <UiDisclosure
        title="Why doesn’t the Holy Eucharist podcast have an episode every day?"
      >
        <p>
          It is published only for days with their own Eucharistic readings:
          Sundays, the principal feasts, the holy days, and the days of Holy
          Week and Easter Week. Other weekdays repeat the previous Sunday’s
          readings or use the readings common to all saints.
        </p>
      </UiDisclosure>
      <UiDisclosure title="My app isn’t listed. How do I subscribe?">
        <p>
          Choose Subscribe, then copy the RSS link and paste it into your app’s
          “Add by URL” or “Follow a show by URL” option.
        </p>
      </UiDisclosure>
    </section>

    <UiSheet
      :open="!!selected"
      size="sm"
      eyebrow="Subscribe"
      :title="selected ? selected.title : ''"
      :subtitle="selected ? selected.subtitle : ''"
      @update:open="(open) => !open && (selected = null)"
    >
      <div v-if="selected" class="subscribe">
        <section v-if="selected.listings.length" class="subscribe__section">
          <h3 class="eyebrow">Listen on</h3>
          <ul class="subscribe__list">
            <li v-for="listing in selected.listings" :key="listing.platform">
              <a
                class="subscribe__link"
                :href="listing.url"
                target="_blank"
                rel="noopener noreferrer"
              >
                <UiIcon :name="platformIcon(listing.platform)" />
                <span>{{ listing.label }}</span>
                <UiIcon name="external" class="subscribe__external" />
              </a>
            </li>
          </ul>
        </section>
        <section class="subscribe__section">
          <h3 class="eyebrow">Open in your app</h3>
          <ul class="subscribe__list">
            <li v-for="app in appLinks(selected)" :key="app.name">
              <a class="subscribe__link" :href="app.href">
                <UiIcon :name="app.icon" />
                <span
                  >{{ app.name }} <small>{{ app.platforms }}</small></span
                >
              </a>
            </li>
          </ul>
        </section>
        <section class="subscribe__section">
          <h3 class="eyebrow">Any other app</h3>
          <p class="subscribe__hint">
            Paste this RSS link into your app’s “Add by URL” option.
          </p>
          <div class="subscribe__feed">
            <input
              class="ui-control"
              type="text"
              readonly
              :value="selected.feed_url"
              aria-label="RSS feed link"
              @focus="$event.target.select()"
            />
            <UiButton variant="secondary" icon="copy" @click="copyFeed">
              Copy
            </UiButton>
          </div>
        </section>
      </div>
    </UiSheet>

    <audio
      ref="preview"
      preload="none"
      @ended="playing = null"
      @pause="onPreviewPause"
    />
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useStore } from 'vuex';
import axios from 'axios';
import { Clipboard } from '@capacitor/clipboard';
import Loading from '@/components/Loading.vue';
import { toast } from '@/ui/feedback';
import { DynamicStorage } from '@/helpers/storage';

const STYLE_KEY = 'podcastStyle';

const store = useStore();
const loading = ref(true);
const error = ref('');
const catalog = ref({ groups: [], feeds: [], live_alternative: null });
const style = ref('contemporary');
const selected = ref(null);
const playing = ref(null);
const preview = ref(null);

const styleOptions = [
  { value: 'contemporary', label: 'Contemporary' },
  { value: 'traditional', label: 'Traditional language' },
];

const styleNote = computed(() =>
  style.value === 'traditional'
    ? 'King James Version, traditional psalter, thee and thou.'
    : 'English Standard Version, contemporary psalter.'
);

const groups = computed(() => catalog.value.groups);
const alternative = computed(() => catalog.value.live_alternative);

// Every podcast comes in both languages; show the chosen one.
function feedsIn(group) {
  return catalog.value.feeds.filter(
    (feed) => feed.group === group && feed.style === style.value
  );
}

function minutes(seconds) {
  return `${Math.max(1, Math.round(seconds / 60))} min`;
}

function followAlongHref(feed) {
  // Episode links point at the public site; stay inside this app or site.
  const url = new window.URL(feed.latest_episode.follow_along_url);
  return `${url.pathname}${url.search}`;
}

const PLATFORMS = {
  apple: { label: 'Apple Podcasts', icon: 'apple' },
  spotify: { label: 'Spotify', icon: 'spotify' },
  youtube_music: { label: 'YouTube Music', icon: 'play' },
  amazon: { label: 'Amazon Music', icon: 'headphones' },
  pocket_casts: { label: 'Pocket Casts', icon: 'podcast' },
  overcast: { label: 'Overcast', icon: 'podcast' },
  castro: { label: 'Castro', icon: 'podcast' },
  goodpods: { label: 'Goodpods', icon: 'podcast' },
  website: { label: 'Website', icon: 'globe' },
  rss: { label: 'RSS', icon: 'rss' },
};

function platformLabel(platform) {
  return PLATFORMS[platform]?.label || platform;
}

function platformIcon(platform) {
  return PLATFORMS[platform]?.icon || 'podcast';
}

// Subscribe links that work before (and without) a directory listing.
function appLinks(feed) {
  const url = feed.feed_url;
  const bare = url.replace(/^https?:\/\//, '');
  const encoded = encodeURIComponent(url);
  const apple = feed.listings.find((listing) => listing.platform === 'apple');
  return [
    {
      name: 'Apple Podcasts',
      platforms: 'iPhone, iPad, Mac',
      icon: 'apple',
      href: apple ? apple.url : `podcast://${bare}`,
    },
    {
      name: 'Overcast',
      platforms: 'iPhone, iPad',
      icon: 'podcast',
      href: `overcast://x-callback-url/add?url=${encoded}`,
    },
    {
      name: 'Pocket Casts',
      platforms: 'iPhone, Android',
      icon: 'podcast',
      href: `pktc://subscribe/${bare}`,
    },
    {
      name: 'Castro',
      platforms: 'iPhone',
      icon: 'podcast',
      href: `castros://subscribe/${bare}`,
    },
    {
      name: 'AntennaPod',
      platforms: 'Android',
      icon: 'android',
      href: `https://antennapod.org/deeplink/subscribe?url=${encoded}&title=${encodeURIComponent(feed.title)}`,
    },
    {
      name: 'Podcast Addict',
      platforms: 'Android',
      icon: 'android',
      href: `podcastaddict://${bare}`,
    },
  ];
}

function openSubscribe(feed) {
  selected.value = feed;
}

async function copyFeed() {
  try {
    await Clipboard.write({ string: selected.value.feed_url });
    toast.success('The RSS link is copied to your clipboard.');
  } catch {
    toast.error('Couldn’t copy the link. Select it and copy it instead.');
  }
}

function togglePreview(feed) {
  const audio = preview.value;
  if (!audio) return;
  if (playing.value === feed.slug) {
    audio.pause();
    playing.value = null;
    return;
  }
  audio.src = feed.latest_episode.audio_url;
  playing.value = feed.slug;
  audio.play().catch(() => {
    playing.value = null;
    toast.error('That episode couldn’t be played. Please try again.');
  });
}

function onPreviewPause() {
  if (preview.value && !preview.value.ended) playing.value = null;
}

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const response = await axios.get(
      `${import.meta.env.VITE_API_URL}api/v1/podcasts`
    );
    catalog.value = response.data;
  } catch {
    error.value = 'The podcasts couldn’t be loaded. Please try again.';
  } finally {
    loading.value = false;
  }
}

watch(style, (value) => {
  DynamicStorage.setItem(STYLE_KEY, value);
});

onMounted(async () => {
  const saved = await DynamicStorage.getItem(STYLE_KEY);
  if (saved === 'contemporary' || saved === 'traditional') {
    style.value = saved;
  } else if (store.state.settings?.language_style === 'traditional') {
    style.value = 'traditional';
  }
  await load();
});

onBeforeUnmount(() => {
  preview.value?.pause();
});
</script>

<style scoped>
.podcast-points {
  display: grid;
  gap: var(--space-3);
  margin: 0 auto var(--space-6);
  padding: 0;
  max-width: 52rem;
  list-style: none;
}

.podcast-points li {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  color: var(--ink-soft);
  font-size: var(--text-md);
  line-height: var(--leading-ui);
}

.podcast-points strong {
  color: var(--ink);
  font-weight: 600;
}

.podcast-points__icon {
  flex: 0 0 auto;
  margin-top: 0.2em;
  font-size: 1.15rem;
  color: var(--accent);
}

@media (min-width: 768px) {
  .podcast-points {
    grid-template-columns: repeat(3, 1fr);
  }
}

.podcasts-style {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-6);
}

.podcasts-style__note {
  margin: 0;
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-faint);
  text-align: center;
}

.podcast-group {
  margin-bottom: var(--space-7);
}

.podcast-group__head {
  margin-bottom: var(--space-4);
  text-align: center;
}

.podcast-group__lede {
  margin: var(--space-1) 0 0;
  color: var(--ink-soft);
  font-style: italic;
}

.podcast-grid {
  display: grid;
  gap: var(--space-4);
  margin: 0;
  padding: 0;
  list-style: none;
}

@media (min-width: 768px) {
  .podcast-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.podcast-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  grid-template-rows: auto 1fr;
  gap: var(--space-3) var(--space-4);
  padding: var(--space-4);
  min-width: 0;
}

.podcast-card__art {
  grid-row: 1 / span 2;
}

.podcast-card__art {
  flex: 0 0 auto;
  width: clamp(4.5rem, 22vw, 6.5rem);
  height: clamp(4.5rem, 22vw, 6.5rem);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  object-fit: cover;
  background-color: var(--paper-sunken);
}

@media (max-width: 480px) {
  .podcast-card {
    gap: var(--space-3);
    padding: var(--space-3);
  }

  .podcast-card .podcast-card__art {
    grid-row: auto;
  }

  .podcast-card .podcast-card__actions {
    grid-column: 1 / -1;
  }
}

.podcast-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  min-width: 0;
}

.podcast-card__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
  line-height: var(--leading-tight);
  color: var(--ink);
}

.podcast-card__subtitle {
  margin: 0;
  color: var(--ink-soft);
  font-size: var(--text-sm);
  line-height: var(--leading-ui);
}

.podcast-card__latest {
  margin: 0;
  font-size: var(--text-sm);
  line-height: var(--leading-ui);
  color: var(--ink);
}

.podcast-card__latest--soon {
  font-style: italic;
  color: var(--ink-faint);
}

.podcast-card__latest .eyebrow {
  display: block;
}

.podcast-card__duration {
  color: var(--ink-faint);
  white-space: nowrap;
}

.podcast-card__actions {
  grid-column: 2;
  align-self: end;
}

.podcast-alternative {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-5);
  margin-bottom: var(--space-7);
}

.podcast-alternative p {
  margin: var(--space-2) 0 var(--space-4);
  color: var(--ink-soft);
  line-height: var(--leading-prose);
}

.podcast-alternative strong {
  color: var(--ink);
}

.podcast-alternative__icon {
  flex: 0 0 auto;
  font-size: 1.5rem;
  color: var(--accent);
}

.podcast-faq {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  max-width: var(--content-width);
  margin: 0 auto;
}

.podcast-faq .section-title {
  margin-bottom: var(--space-2);
  text-align: center;
}

.podcast-faq p {
  margin: 0 0 var(--space-3);
  color: var(--ink-soft);
  line-height: var(--leading-prose);
}

.subscribe {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.subscribe__section .eyebrow {
  margin: 0 0 var(--space-2);
}

.subscribe__list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.subscribe__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 2.75rem;
  padding: var(--space-2);
  border-radius: var(--radius);
  color: var(--ink);
  text-decoration: none;
  transition: background-color var(--duration) var(--ease);
}

.subscribe__link:hover {
  background-color: var(--paper-sunken);
}

.subscribe__link > .ui-icon {
  font-size: 1.15rem;
  color: var(--accent);
}

.subscribe__link span {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
}

.subscribe__link small {
  font-size: var(--text-xs);
  font-style: italic;
  color: var(--ink-faint);
}

.subscribe__external {
  font-size: 0.85rem;
  color: var(--ink-faint);
}

.subscribe__hint {
  margin: 0 0 var(--space-2);
  font-size: var(--text-sm);
  color: var(--ink-soft);
}

.subscribe__feed {
  display: flex;
  gap: var(--space-2);
}

.subscribe__feed input {
  flex: 1 1 auto;
  min-width: 0;
  font-size: var(--text-sm);
}
</style>
