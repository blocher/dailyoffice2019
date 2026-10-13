<template>
  <div class="page not-found">
    <header class="page-header">
      <p class="eyebrow">Error 404</p>
      <h1 class="page-title">Page not found</h1>
      <p class="page-lede">
        We can’t find this page. It may have moved, or the address may be
        mistyped.
      </p>
    </header>

    <div class="divider"><Ornament glyph="o" /></div>

    <nav class="not-found__ways" aria-label="Ways back">
      <UiButton to="/" variant="primary" size="lg" icon="sunrise">
        Pray today
      </UiButton>
      <UiButton to="/calendar" size="lg" icon="calendar">Calendar</UiButton>
      <UiButton size="lg" icon="menu" @click="openPanel('menu')">
        Menu
      </UiButton>
    </nav>

    <ul class="not-found__more">
      <li v-for="link in more" :key="link.to">
        <router-link :to="link.to">
          <UiIcon :name="link.icon" />
          {{ link.label }}
        </router-link>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { openPanel } from '@/helpers/panels';

defineOptions({ name: 'PageNotFound' });

const more = [
  { label: 'Daily Office', icon: 'book', to: '/office' },
  { label: 'Family Prayer', icon: 'home', to: '/family' },
  { label: "Today's Readings", icon: 'book-text', to: '/readings' },
  { label: 'The Psalter', icon: 'library', to: '/psalms' },
  { label: 'Collects', icon: 'bookmark', to: '/collects' },
  { label: 'Settings', icon: 'settings', to: '/settings' },
];
</script>

<style scoped>
.not-found .divider {
  max-width: 16rem;
  margin-inline: auto;
  font-size: 1.4rem;
}

.not-found__ways {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-3);
}

@media (max-width: 479px) {
  .not-found__ways {
    flex-direction: column;
    align-items: stretch;
  }
}

.not-found__more {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0 var(--space-5);
  max-width: 34rem;
  margin: var(--space-6) auto 0;
  padding-top: var(--space-4);
  border-top: 1px solid var(--rule);
}

.not-found__more a {
  display: inline-flex;
  align-items: center;
  gap: 0.45em;
  min-height: 2.75rem;
  color: var(--ink-soft);
  text-decoration: none;
}

.not-found__more a:hover {
  color: var(--accent);
}

.not-found__more .ui-icon {
  color: var(--accent);
}
</style>
