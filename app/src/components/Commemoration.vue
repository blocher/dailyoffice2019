<template>
  <article class="commemoration">
    <h2 class="commemoration__name">
      <span
        class="commemoration__swatch"
        :class="`swatch--${colorName}`"
        aria-hidden="true"
      />
      <span v-html="commemoration.name" />
    </h2>
    <p v-if="commemoration.ai_one_sentence" class="commemoration__bio">
      {{ commemoration.ai_one_sentence }}
      <template v-if="infoSetting === 'full_hagiography' && hasBio">
        <router-link :to="link" class="commemoration__more">
          Read the life&nbsp;›
        </router-link>
      </template>
    </p>
    <p
      v-if="infoSetting === 'wikipedia' && wikipediaLinks.length"
      class="commemoration__links"
    >
      <a
        v-for="(href, index) in wikipediaLinks"
        :key="index"
        :href="href"
        target="_blank"
        rel="noopener"
        class="commemoration__more"
      >
        <UiIcon name="wikipedia" /> Wikipedia
      </a>
    </p>
  </article>
</template>

<script>
export default {
  props: ['commemoration'],
  computed: {
    link() {
      return `/commemorations/${this.commemoration.uuid}`;
    },
    hasBio() {
      return Boolean(this.commemoration.ai_one_sentence);
    },
    colorName() {
      const colors = this.commemoration.colors || [];
      return String(colors[0] || 'white').toLowerCase();
    },
    wikipediaLinks() {
      return Array.isArray(this.commemoration.links)
        ? this.commemoration.links
        : [];
    },
    infoSetting() {
      return (
        this.$store.state.settings?.commemoration_info || 'full_hagiography'
      );
    },
  },
};
</script>

<style scoped>
/* Inherits its size from the office title block, which follows the reader's
   text size. */
.commemoration__name {
  display: flex;
  align-items: baseline;
  gap: 0.5em;
  font-size: 1em;
  font-weight: 600;
  line-height: 1.3;
  color: var(--ink);
}

.commemoration__swatch {
  flex-shrink: 0;
  width: 0.55em;
  height: 0.55em;
  border-radius: 2px;
  background-color: var(--paper-raised);
  box-shadow: inset 0 0 0 1px var(--season-white);
}

.swatch--red {
  background-color: var(--season-red);
  box-shadow: none;
}

.swatch--green {
  background-color: var(--season-green);
  box-shadow: none;
}

.swatch--purple {
  background-color: var(--season-purple);
  box-shadow: none;
}

.swatch--black {
  background-color: var(--season-black);
  box-shadow: none;
}

.swatch--rose {
  background-color: var(--season-rose);
  box-shadow: none;
}

.swatch--blue {
  background-color: var(--season-blue);
  box-shadow: none;
}

.commemoration__bio,
.commemoration__links {
  margin-top: 0.2em;
  padding-left: 1.05em;
  font-size: 0.94em;
  line-height: 1.45;
  color: var(--ink-soft);
}

.commemoration__more {
  white-space: nowrap;
  font-style: italic;
  text-decoration: none;
}

.commemoration__more:hover {
  text-decoration: underline;
}

.commemoration__links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75em;
}

.commemoration__links .ui-icon {
  vertical-align: -0.1em;
}
</style>
