<template>
  <div class="saint-page" :style="markStyle">
    <Loading v-if="loading" />

    <div v-if="error" class="saint-page__error">
      <UiAlert tone="error" :title="error" />
    </div>

    <article v-if="!loading && commemoration" class="saint">
      <!-- Title block -->
      <header class="saint-header">
        <p v-if="commemoration.date_string" class="saint-header__date">
          {{ commemoration.date_string }}
        </p>
        <h1 class="saint-header__name">
          {{ title.name }}
          <span v-if="title.subtitle" class="saint-header__subtitle">
            {{ title.subtitle }}
          </span>
        </h1>
        <p v-if="rankName || colorName" class="saint-header__meta">
          <span
            class="swatch saint-swatch"
            :class="`swatch--${colorName || 'white'}`"
            aria-hidden="true"
          />
          <span v-if="rankName">{{ rankName }}</span
          ><span v-if="rankName && colorName" aria-hidden="true">&nbsp;· </span>
          <span v-if="colorName" class="saint-header__color">
            <span class="visually-hidden">Liturgical color:</span>
            {{ colorName }}
          </span>
        </p>

        <figure v-if="portrait" class="saint-portrait">
          <img :src="portrait" :alt="commemoration.name" loading="lazy" />
        </figure>

        <p v-if="commemoration.ai_one_sentence" class="saint-header__summary">
          {{ commemoration.ai_one_sentence }}
        </p>
      </header>

      <aside v-if="hasStory" class="saint-notice" aria-label="About this page">
        <UiIcon name="info" class="saint-notice__icon" />
        <p>
          This is an <em>experimental</em> feature. The information is compiled
          from <em>unofficial</em> sources, and was built with assistance by AI.
          While we attempt to cite and link to all original sources, there may
          still be errors. Please report any factual or theological errors to
          <a href="mailto:feedback@dailyoffice2019.com"
            >feedback@dailyoffice2019.com</a
          >
          for correction. This behavior can be changed or disabled in
          <router-link to="/settings">Settings</router-link> under
          <span class="smallcaps">Commemoration Info</span>.
        </p>
      </aside>

      <div v-if="hasStory" class="saint-opening">
        <Ornament glyph="o" />
      </div>

      <div class="saint-layout" :class="{ 'has-toc': showToc }">
        <nav v-if="showToc" class="saint-toc" aria-label="On this page">
          <p class="saint-toc__title">On this page</p>
          <ul>
            <li v-for="section in sections" :key="section.id">
              <a
                :href="`#${section.id}`"
                @click.prevent="scrollToSection(section.id)"
                >{{ section.label }}</a
              >
            </li>
          </ul>
        </nav>

        <div class="saint-text">
          <blockquote v-if="article.quote" class="saint-epigraph">
            <p v-html="article.quote"></p>
            <footer v-if="commemoration.ai_quote_by">
              — {{ commemoration.ai_quote_by }}
            </footer>
          </blockquote>

          <figure v-if="validImages.image_link" class="saint-figure">
            <img
              :src="commemoration.image_link"
              :alt="commemoration.name"
              loading="lazy"
            />
          </figure>

          <section v-if="article.facts.length" id="key-facts">
            <h2>Key Facts</h2>
            <ul class="saint-list">
              <li
                v-for="(point, index) in article.facts"
                :key="index"
                v-html="point"
              ></li>
            </ul>
          </section>

          <section v-if="article.life.length" id="life" class="saint-life">
            <h2>The Life of {{ shortName }}</h2>
            <p
              v-for="(paragraph, index) in article.life"
              :key="index"
              v-html="paragraph"
            ></p>
          </section>

          <section v-if="commemoration.collect" id="collect">
            <h2>The Collect</h2>
            <p class="saint-collect">{{ commemoration.collect }}</p>
          </section>

          <section v-if="article.traditions.length" id="traditions">
            <h2>Traditions</h2>
            <ul class="saint-list">
              <li
                v-for="(point, index) in article.traditions"
                :key="index"
                v-html="point"
              ></li>
            </ul>
          </section>

          <section v-if="article.foods.length" id="foods">
            <h2>Foods</h2>
            <ul class="saint-list">
              <li
                v-for="(point, index) in article.foods"
                :key="index"
                v-html="point"
              ></li>
            </ul>
          </section>

          <figure v-if="verse" class="saint-verse">
            <Ornament glyph="v" class="saint-verse__ornament" />
            <blockquote>
              <p>“{{ verse }}”</p>
            </blockquote>
            <figcaption v-if="commemoration.ai_verse_citation">
              {{ commemoration.ai_verse_citation }}
            </figcaption>
          </figure>

          <p v-if="!hasStory" class="saint-empty">
            A fuller account of this commemoration is not yet available.
          </p>

          <section
            v-if="links.length || article.sources.length"
            id="sources"
            class="saint-sources"
          >
            <h2>Sources</h2>
            <template v-if="links.length">
              <h3>Further reading</h3>
              <ul class="saint-sources__links">
                <li v-for="link in links" :key="link.href">
                  <a :href="link.href" target="_blank" rel="noopener">
                    <UiIcon :name="link.icon" />
                    <span>{{ link.label }}</span>
                  </a>
                </li>
              </ul>
            </template>
            <template v-if="article.sources.length">
              <h3>Citations</h3>
              <ol class="saint-sources__citations">
                <li
                  v-for="source in article.sources"
                  :id="`source-${source.number}`"
                  :key="source.number"
                >
                  <span class="saint-sources__number"
                    >{{ source.number }}.</span
                  >
                  <a :href="source.url" target="_blank" rel="noopener">
                    {{ source.label }}
                  </a>
                </li>
              </ol>
            </template>
          </section>
        </div>
      </div>
    </article>

    <nav
      v-if="!loading && (previousLink || nextLink)"
      class="saint-pager"
      aria-label="Other commemorations"
    >
      <router-link
        v-if="previousLink"
        :to="previousLink.to"
        class="saint-pager__link saint-pager__link--previous"
      >
        <UiIcon name="chevron-left" class="saint-pager__icon" />
        <span class="saint-pager__copy">
          <span class="saint-pager__label">Previous</span>
          <span class="saint-pager__name">{{ previousLink.name }}</span>
        </span>
      </router-link>
      <router-link
        v-if="nextLink"
        :to="nextLink.to"
        class="saint-pager__link saint-pager__link--next"
      >
        <span class="saint-pager__copy">
          <span class="saint-pager__label">Next</span>
          <span class="saint-pager__name">{{ nextLink.name }}</span>
        </span>
        <UiIcon name="chevron-right" class="saint-pager__icon" />
      </router-link>
    </nav>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import DOMPurify from 'dompurify';

const LITURGICAL_COLORS = [
  'red',
  'green',
  'white',
  'purple',
  'black',
  'rose',
  'blue',
];

// Words that end in a full stop without ending the sentence.
const ABBREVIATION =
  /(?:\b(?:St|Sts|Ss|Mt|Dr|Mr|Mrs|Ms|Fr|Rev|Bp|Abp|Br|Sr|Jr|ca|cf|vs|viz|No|Vol|ch|vv?)|\b[A-Z]|\be\.g|\bi\.e|\bc)\.$/;
const SENTENCE_BREAK = /([.!?]["'”’)]*(?:\[\d+\])*)\s+(?=["“‘(]?[A-Z0-9])/g;
const PARAGRAPH_LENGTH = 520;

function escapeAttribute(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function asList(value) {
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function isWebUrl(value) {
  return typeof value === 'string' && /^https?:\/\//i.test(value);
}

/** "en.wikipedia.org › Philip the Evangelist" */
export function describeUrl(url) {
  try {
    const parsed = new window.URL(url);
    const host = parsed.hostname.replace(/^www\./, '');
    const segments = parsed.pathname.split('/').filter(Boolean);
    let tail = segments.length ? segments[segments.length - 1] : '';
    try {
      tail = decodeURIComponent(tail);
    } catch {
      /* keep the raw segment */
    }
    tail = tail
      .replace(/\.(html?|php|aspx?)$/i, '')
      .replace(/[_-]+/g, ' ')
      .trim();
    return tail ? `${host} › ${tail}` : host;
  } catch {
    return url;
  }
}

/*
  The biographies arrive as one long block. Break them into paragraphs of a
  few sentences at sentence boundaries so they read like an article. Text
  that already has paragraph breaks keeps them.
*/
export function splitParagraphs(text) {
  if (!text || typeof text !== 'string') return [];
  const trimmed = text.trim();
  if (/<p[\s>]/i.test(trimmed)) {
    return trimmed
      .split(/<\/p>\s*/i)
      .map((part) => part.replace(/<p[^>]*>/i, '').trim())
      .filter(Boolean);
  }
  if (/\n/.test(trimmed)) {
    return trimmed
      .split(/\s*\n\s*/)
      .map((part) => part.trim())
      .filter(Boolean);
  }

  const pieces = trimmed.split(SENTENCE_BREAK);
  // split() with a capture group interleaves the punctuation; stitch it back.
  const sentences = [];
  for (let i = 0; i < pieces.length; i += 2) {
    const sentence = `${pieces[i]}${pieces[i + 1] || ''}`;
    const previous = sentences[sentences.length - 1];
    if (previous && ABBREVIATION.test(previous)) {
      sentences[sentences.length - 1] = `${previous} ${sentence}`;
    } else {
      sentences.push(sentence);
    }
  }

  const paragraphs = [];
  let current = '';
  for (const sentence of sentences) {
    current = current ? `${current} ${sentence}` : sentence;
    if (current.length >= PARAGRAPH_LENGTH) {
      paragraphs.push(current);
      current = '';
    }
  }
  if (current) {
    // Fold a short tail into the previous paragraph.
    if (paragraphs.length && current.length < PARAGRAPH_LENGTH / 3) {
      paragraphs[paragraphs.length - 1] += ` ${current}`;
    } else {
      paragraphs.push(current);
    }
  }
  return paragraphs;
}

/*
  Turns "[2]" markers into superscript links. Each field has its own list of
  citation URLs; sources are numbered once across the whole page, in the
  order they are first cited, and collected into `sources` for the list at
  the end.
*/
export function createCiter() {
  const sources = [];
  const numbers = new Map();

  function numberFor(url) {
    if (!numbers.has(url)) {
      const number = sources.length + 1;
      numbers.set(url, number);
      sources.push({ number, url, label: describeUrl(url) });
    }
    return numbers.get(url);
  }

  function cite(text, citations) {
    if (!text || typeof text !== 'string') return '';
    const clean = DOMPurify.sanitize(text);
    const list = Array.isArray(citations) ? citations : [];
    return clean.replace(/\[(\d+)\]/g, (match, index) => {
      const url = list[parseInt(index, 10) - 1];
      if (!isWebUrl(url)) return '';
      const number = numberFor(url);
      return `<sup class="cite"><a href="${escapeAttribute(url)}" target="_blank" rel="noopener" title="${escapeAttribute(describeUrl(url))}">${number}</a></sup>`;
    });
  }

  return { cite, sources };
}

export default {
  name: 'Commemoration',
  components: {
    Loading,
  },
  data() {
    return {
      commemoration: null,
      loading: true,
      error: null,
      validImages: {
        ai_image_1: false,
        ai_image_2: false,
        image_link: false,
      },
    };
  },
  computed: {
    colorName() {
      const colors = this.commemoration?.colors;
      const color = Array.isArray(colors) && colors[0];
      const normalized = String(color || '').toLowerCase();
      return LITURGICAL_COLORS.includes(normalized) ? normalized : '';
    },
    // The saint's liturgical color, used for the swatch, initial and rules.
    markStyle() {
      if (!this.colorName) return null;
      return { '--saint-mark': `var(--season-${this.colorName})` };
    },
    rankName() {
      return this.commemoration?.rank?.formatted_name || '';
    },
    // "Paulinus, Bishop of York and Missionary, 644" → name + subtitle
    title() {
      const name = String(this.commemoration?.name || '').trim();
      const comma = name.indexOf(', ');
      if (comma === -1) return { name, subtitle: '' };
      return {
        name: name.slice(0, comma),
        subtitle: name.slice(comma + 2),
      };
    },
    shortName() {
      return this.commemoration?.saint_name || this.title.name;
    },
    portrait() {
      if (this.validImages.ai_image_1) return this.commemoration.ai_image_1;
      if (this.validImages.ai_image_2) return this.commemoration.ai_image_2;
      return null;
    },
    verse() {
      const verse = this.commemoration?.ai_verse;
      if (!verse || typeof verse !== 'string') return '';
      return verse.trim().replace(/^["“']+|["”']+$/g, '');
    },
    article() {
      const c = this.commemoration || {};
      const { cite, sources } = createCiter();
      return {
        quote: cite(c.ai_quote, c.ai_quote_citations),
        facts: asList(c.ai_bullet_points).map((point) =>
          cite(point, c.ai_bullet_points_citations)
        ),
        life: splitParagraphs(c.ai_hagiography).map((paragraph) =>
          cite(paragraph, c.ai_hagiography_citations)
        ),
        traditions: asList(c.ai_traditions).map((point) =>
          cite(point, c.ai_traditions_citations)
        ),
        foods: asList(c.ai_foods).map((point) =>
          cite(point, c.ai_foods_citations)
        ),
        sources,
      };
    },
    links() {
      return asList(this.commemoration?.links)
        .filter(isWebUrl)
        .map((href) => {
          const wikipedia = /wikipedia\.org/i.test(href);
          return {
            href,
            icon: wikipedia ? 'wikipedia' : 'external',
            label: wikipedia
              ? `Wikipedia: ${describeUrl(href).split(' › ')[1] || 'article'}`
              : describeUrl(href),
          };
        });
    },
    hasStory() {
      const a = this.article;
      return Boolean(
        a.quote ||
        a.facts.length ||
        a.life.length ||
        a.traditions.length ||
        a.foods.length ||
        this.verse ||
        this.commemoration?.collect
      );
    },
    sections() {
      const a = this.article;
      return [
        a.facts.length && { id: 'key-facts', label: 'Key Facts' },
        a.life.length && { id: 'life', label: 'Life' },
        this.commemoration?.collect && { id: 'collect', label: 'Collect' },
        a.traditions.length && { id: 'traditions', label: 'Traditions' },
        a.foods.length && { id: 'foods', label: 'Foods' },
        (this.links.length || a.sources.length) && {
          id: 'sources',
          label: 'Sources',
        },
      ].filter(Boolean);
    },
    showToc() {
      return this.sections.length >= 3;
    },
    previousLink() {
      const previous = this.commemoration?.previous_commemoration;
      if (!previous?.uuid) return null;
      return { name: previous.name, to: `/commemorations/${previous.uuid}` };
    },
    nextLink() {
      const next = this.commemoration?.next_commemoration;
      if (!next?.uuid) return null;
      return { name: next.name, to: `/commemorations/${next.uuid}` };
    },
  },
  async mounted() {
    await this.initialize();
  },
  methods: {
    async initialize() {
      this.loading = true;
      this.error = null;
      try {
        const commemoration = await this.$http.get(
          `${import.meta.env.VITE_API_URL}api/v1/commemorations/${this.$route.params.uuid}`
        );
        this.commemoration = commemoration.data;
        document.title = `${String(this.commemoration?.name || 'Commemoration').replace(/<[^>]*>/g, '')} | The Daily Office`;
        this.checkImages();
      } catch {
        this.error =
          'There was an error retrieving the commemoration. Please try again.';
        this.loading = false;
        return;
      }
      this.loading = false;
    },
    checkImages() {
      for (const key of Object.keys(this.validImages)) {
        if (isWebUrl(this.commemoration[key])) {
          this.validateImageUrl(this.commemoration[key], key);
        }
      }
    },
    validateImageUrl(url, key) {
      const img = new window.Image();
      img.onload = () => {
        this.validImages[key] = true;
      };
      img.onerror = () => {
        this.validImages[key] = false;
      };
      img.src = url;
    },
    scrollToSection(id) {
      const target = document.getElementById(id);
      if (!target) return;
      const reduce = window.matchMedia?.(
        '(prefers-reduced-motion: reduce)'
      ).matches;
      target.scrollIntoView({
        behavior: reduce ? 'auto' : 'smooth',
        block: 'start',
      });
    },
  },
};
</script>

<style scoped>
/*
  A long-form article. The title block and body follow the reader's text
  size and reading face; navigation and notes stay at UI sizes.
*/
.saint-page {
  --saint-mark: var(--accent);
  --saint-size: max(
    17px,
    calc(var(--main-font-size) * var(--reading-scale) * 0.82)
  );

  width: 100%;
  max-width: var(--page-width);
  margin-inline: auto;
  padding: var(--space-6) var(--gutter) var(--space-7);
  overflow-wrap: break-word;
}

.saint-page__error {
  max-width: var(--content-width);
  margin: 0 auto;
}

/* ── Title block ─────────────────────────────────────── */
.saint-header {
  max-width: 40rem;
  margin: 0 auto;
  font-size: max(15px, calc(var(--main-font-size) * 0.75));
  text-align: center;
}

.saint-header__date {
  font-size: 0.9em;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  color: var(--ink-faint);
}

.saint-header__name {
  margin-top: 0.3em;
  font-size: min(2em, 11vw);
  font-weight: 400;
  line-height: 1.12;
  color: var(--ink);
  text-wrap: balance;
}

@media (min-width: 720px) {
  .saint-header__name {
    font-size: 2.3em;
  }
}

.saint-header__subtitle {
  display: block;
  margin-top: 0.35em;
  font-size: 0.52em;
  font-style: italic;
  line-height: 1.3;
  color: var(--ink-soft);
}

.saint-header__meta {
  margin-top: 0.9em;
  line-height: 1.4;
  font-size: 0.85em;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-soft);
}

.saint-header__color {
  text-transform: capitalize;
}

.saint-swatch {
  margin-right: 0.45em;
  vertical-align: 0.05em;
}

.saint-portrait {
  margin: 1.4em auto 0;
  max-width: min(17rem, 100%);
}

.saint-portrait img,
.saint-figure img {
  display: block;
  margin: 0 auto;
  max-height: min(24rem, 55vh);
  width: auto;
  object-fit: contain;
  border-radius: var(--radius-sm);
  box-shadow: 0 0 0 1px var(--rule);
}

.saint-header__summary {
  margin: 1.2em auto 0;
  max-width: 32em;
  font-family: var(--font-reading);
  font-size: 1.1em;
  font-style: italic;
  line-height: 1.45;
  color: var(--ink-soft);
  text-wrap: pretty;
}

/* ── Experimental note ───────────────────────────────── */
.saint-notice {
  display: flex;
  gap: var(--space-3);
  max-width: 36rem;
  margin: var(--space-6) auto 0;
  padding-top: var(--space-4);
  border-top: 1px solid var(--rule);
  font-size: var(--text-xs);
  line-height: 1.5;
  color: var(--ink-faint);
}

.saint-notice__icon {
  margin-top: 0.15rem;
  font-size: var(--text-sm);
  color: var(--tone-warning);
}

.saint-notice a {
  color: var(--ink-soft);
}

.saint-opening {
  margin: var(--space-6) auto var(--space-2);
  text-align: center;
  font-size: 1.5rem;
}

.saint-opening .ornament {
  color: var(--saint-mark);
}

/* ── Layout: one column; a sticky contents list on wide screens ── */
.saint-layout {
  font-size: var(--saint-size);
}

.saint-text {
  max-width: 34em;
  margin: 0 auto;
  font-family: var(--font-reading);
  line-height: 1.6;
  color: var(--ink);
}

.saint-toc {
  display: none;
}

@media (min-width: 1100px) {
  .saint-layout.has-toc {
    display: grid;
    grid-template-columns:
      minmax(11rem, 1fr) minmax(0, 34em)
      minmax(0, 1fr);
    column-gap: var(--space-6);
    align-items: start;
  }

  .saint-layout.has-toc .saint-text {
    grid-column: 2;
    margin: 0;
  }

  .saint-toc {
    display: block;
    position: sticky;
    top: calc(var(--header-height) + var(--sat) + var(--space-5));
    justify-self: end;
    width: 11rem;
    margin-top: var(--space-6);
    font-family: var(--font-book);
    font-size: var(--text-sm);
  }
}

.saint-toc__title {
  padding-bottom: var(--space-2);
  border-bottom: 1px solid var(--rule);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
}

.saint-toc ul {
  margin-top: var(--space-1);
}

.saint-toc a {
  display: flex;
  align-items: center;
  min-height: 2.75rem;
  color: var(--ink-soft);
  text-decoration: none;
}

.saint-toc a:hover {
  color: var(--accent);
}

/* ── Body text ───────────────────────────────────────── */
.saint-text section {
  scroll-margin-top: calc(var(--header-height) + var(--sat) + 1rem);
}

.saint-text h2 {
  margin: 2.4em 0 0.9em;
  font-size: 1em;
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  line-height: 1.3;
  text-align: center;
  color: var(--ink);
  text-wrap: balance;
}

.saint-text h2::after {
  content: '';
  display: block;
  width: 2.5em;
  margin: 0.5em auto 0;
  border-top: 1px solid var(--saint-mark);
  opacity: 0.6;
}

.saint-text section:first-of-type h2 {
  margin-top: 1.6em;
}

.saint-epigraph {
  max-width: 26em;
  margin: 0 auto;
  font-style: italic;
  line-height: 1.5;
  color: var(--ink-soft);
  text-align: center;
  text-wrap: pretty;
}

.saint-epigraph footer {
  margin-top: 0.5em;
  font-style: normal;
  font-size: 0.85em;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.saint-figure {
  margin: 2em auto 0;
}

.saint-life p {
  text-indent: 1.4em;
  hyphens: auto;
  -webkit-hyphens: auto;
  text-wrap: pretty;
}

.saint-life h2 + p {
  text-indent: 0;
}

/* A quiet initial in the day's color */
.saint-life h2 + p::first-letter {
  float: left;
  margin: 0.06em 0.08em 0 0;
  font-size: 3.1em;
  line-height: 0.82;
  color: var(--saint-mark);
}

.saint-collect {
  text-wrap: pretty;
}

.saint-list {
  display: flex;
  flex-direction: column;
  gap: 0.55em;
}

.saint-list li {
  position: relative;
  padding-left: 1.3em;
  line-height: 1.5;
}

.saint-list li::before {
  content: '';
  position: absolute;
  left: 0.2em;
  top: 0.62em;
  width: 0.32em;
  height: 0.32em;
  background-color: var(--saint-mark);
  transform: rotate(45deg);
  opacity: 0.75;
}

.saint-verse {
  margin: 3em auto 0;
  max-width: 26em;
  text-align: center;
}

.saint-verse__ornament {
  display: block;
  margin-bottom: 0.6em;
  font-size: 1.2em;
  color: var(--saint-mark);
}

.saint-verse blockquote {
  font-style: italic;
  line-height: 1.5;
  text-wrap: balance;
}

.saint-verse figcaption {
  margin-top: 0.4em;
  font-size: 0.85em;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-soft);
}

.saint-empty {
  margin-top: 1em;
  font-style: italic;
  text-align: center;
  color: var(--ink-soft);
}

/* Citations inside the API text */
.saint-text :deep(.cite) {
  font-family: var(--font-book);
  font-size: 0.6em;
  line-height: 0;
  vertical-align: 0.65em;
  font-variant-numeric: lining-nums;
}

.saint-text :deep(.cite a) {
  padding: 0 0.12em;
  text-decoration: none;
}

.saint-text :deep(.cite + .cite)::before {
  content: ',';
  color: var(--ink-faint);
}

/* ── Sources ─────────────────────────────────────────── */
.saint-sources {
  margin-top: 1em;
  font-size: max(15px, 0.78em);
  line-height: 1.45;
}

.saint-sources h3 {
  margin: 1.4em 0 0.4em;
  font-size: 1em;
  font-weight: 400;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
}

.saint-sources ul,
.saint-sources ol {
  border-top: 1px solid var(--rule);
}

.saint-sources li {
  border-bottom: 1px solid var(--rule);
}

.saint-sources__links a {
  display: flex;
  align-items: center;
  gap: 0.55em;
  min-height: 2.75rem;
  padding: 0.35em 0;
  text-decoration: none;
}

.saint-sources__links a:hover span {
  text-decoration: underline;
}

.saint-sources__citations li {
  display: flex;
  gap: 0.6em;
  align-items: baseline;
  padding: 0.55em 0;
  min-height: 2.75rem;
}

.saint-sources__number {
  flex: 0 0 1.6em;
  text-align: right;
  color: var(--ink-faint);
  font-variant-numeric: lining-nums tabular-nums;
}

.saint-sources__citations a {
  min-width: 0;
  overflow-wrap: anywhere;
  color: var(--ink-soft);
}

.saint-sources__citations li:target a {
  color: var(--accent);
}

/* ── Previous / next ─────────────────────────────────── */
.saint-pager {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  max-width: 40rem;
  margin: var(--space-7) auto 0;
  border-top: 1px solid var(--rule);
}

.saint-pager__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 3.5rem;
  padding: var(--space-3) var(--space-1);
  border-bottom: 1px solid var(--rule);
  color: var(--ink);
  text-decoration: none;
}

.saint-pager__link--next {
  justify-content: flex-end;
  text-align: right;
}

.saint-pager__link:hover .saint-pager__name {
  color: var(--accent);
}

.saint-pager__icon {
  flex-shrink: 0;
  color: var(--ink-faint);
}

.saint-pager__copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.saint-pager__label {
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  color: var(--ink-faint);
}

.saint-pager__name {
  font-size: var(--text-md);
  line-height: 1.3;
  text-wrap: balance;
  transition: color var(--duration) var(--ease);
}

@media (min-width: 640px) {
  .saint-pager {
    grid-template-columns: 1fr 1fr;
    column-gap: var(--space-6);
  }

  .saint-pager__link--next {
    grid-column: 2;
  }
}
</style>
