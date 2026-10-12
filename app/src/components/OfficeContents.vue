<template>
  <nav
    v-if="sections.length > 2"
    class="office-contents"
    aria-label="Sections of this office"
  >
    <p class="office-contents__title">In this office</p>
    <ol class="office-contents__list">
      <li v-for="section in sections" :key="section.id">
        <a
          :href="`#${section.id}`"
          class="office-contents__link"
          :class="{ 'is-current': section.id === currentId }"
          :aria-current="section.id === currentId ? 'location' : null"
          @click.prevent="jump(section.id)"
          >{{ section.title
          }}<span v-if="section.note" class="office-contents__note">{{
            section.note
          }}</span></a
        >
      </li>
    </ol>
  </nav>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';

/*
  A margin index of the office's headings for wide screens, like a ribbon in
  a printed book. It reads the headings from the rendered text, so it needs no
  changes to how lines are drawn.
*/
const props = defineProps({
  // Anything that changes when the text is re-rendered (e.g. the modules).
  source: { type: [Array, Object], default: null },
  container: { type: String, default: '#main' },
});

const sections = ref([]);
const currentId = ref('');
let observer = null;

function slug(text, index) {
  const base = text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
  return `section-${index}-${base || 'part'}`;
}

function collect() {
  observer?.disconnect();
  const root = document.querySelector(props.container);
  if (!root) {
    sections.value = [];
    return;
  }
  const headings = [...root.querySelectorAll('h2')];
  const list = headings.map((heading, index) => {
    if (!heading.id) heading.id = slug(heading.textContent || '', index);
    // A subheading directly after the heading (e.g. which feast a collect
    // belongs to) tells repeated headings apart.
    const next = heading.parentElement?.nextElementSibling?.firstElementChild;
    const note =
      next && next.tagName === 'H4' ? (next.textContent || '').trim() : '';
    return { id: heading.id, title: (heading.textContent || '').trim(), note };
  });
  const counts = {};
  list.forEach((s) => (counts[s.title] = (counts[s.title] || 0) + 1));
  sections.value = list.map((s) => ({
    ...s,
    note: counts[s.title] > 1 ? s.note : '',
  }));
  if (typeof window.IntersectionObserver === 'undefined') return;
  observer = new window.IntersectionObserver(
    (entries) => {
      const visible = entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (visible.length) currentId.value = visible[0].target.id;
    },
    { rootMargin: '-10% 0px -70% 0px' }
  );
  headings.forEach((heading) => observer.observe(heading));
}

function jump(id) {
  const target = document.getElementById(id);
  if (!target) return;
  target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  currentId.value = id;
}

watch(
  () => props.source,
  async () => {
    await nextTick();
    collect();
  }
);

onMounted(async () => {
  await nextTick();
  collect();
});

onBeforeUnmount(() => observer?.disconnect());
</script>

<style scoped>
.office-contents {
  position: sticky;
  top: calc(env(safe-area-inset-top) + var(--space-6));
  max-height: calc(var(--vvh) - var(--space-8));
  overflow-y: auto;
  padding: 0 var(--space-4) var(--space-4) 0;
  scrollbar-width: thin;
}

.office-contents__title {
  margin-bottom: var(--space-2);
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.14em;
  color: var(--ink-faint);
}

.office-contents__list {
  border-left: 1px solid var(--rule);
}

.office-contents__link {
  display: block;
  margin-left: -1px;
  padding: 0.3rem 0 0.3rem var(--space-3);
  border-left: 2px solid transparent;
  font-size: var(--text-md);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.08em;
  line-height: 1.25;
  color: var(--ink-faint);
  text-decoration: none;
  transition:
    color var(--duration) var(--ease),
    border-color var(--duration) var(--ease);
}

.office-contents__note {
  display: block;
  margin-top: 0.1rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--text-xs);
  font-style: italic;
  font-variant-caps: normal;
  letter-spacing: 0;
}

.office-contents__link:hover {
  color: var(--ink);
}

.office-contents__link.is-current {
  border-left-color: var(--accent);
  color: var(--ink);
}
</style>
