<template>
  <PageNotFound v-if="notFound" />
  <div v-else class="canticle-page">
    <header class="page canticle-head">
      <div class="page-header">
        <p class="eyebrow">
          <router-link :to="{ name: 'Canticles' }" class="canticle-head__up">
            The Canticles
          </router-link>
        </p>
        <h1 class="page-title">
          {{ canticle ? canticle.latin_name : 'Canticle' }}
        </h1>
        <p v-if="canticle" class="page-lede">{{ canticle.english_name }}</p>
      </div>

      <Loading v-if="loading" />
      <UiAlert v-if="error" tone="error" :title="error" />

      <template v-if="canticle">
        <p class="canticle-facts">
          <span v-if="canticle.citation">{{ canticle.citation }}</span>
          <span v-if="category">{{ category.label }}</span>
          <span v-for="office in officeLabels" :key="office">{{ office }}</span>
        </p>

        <div class="canticle-tools">
          <UiSegmented
            :model-value="style"
            :options="styleOptions"
            size="sm"
            aria-label="Language"
            @update:model-value="changeStyle"
          />
        </div>

        <UiDisclosure
          v-if="uses.length || canticle.suggested.length"
          class="canticle-uses"
          title="When it is said"
        >
          <p v-if="canticle.suggested.length" class="canticle-uses__suggested">
            <span class="canticle-uses__label">Suggested</span>
            {{ canticle.suggested.join(' · ') }}
          </p>
          <div
            v-for="use in uses"
            :key="use.key"
            class="canticle-uses__rotation"
          >
            <h2 class="canticle-uses__name">
              <router-link
                v-if="use.rotation"
                :to="{
                  name: 'Canticles',
                  query: { view: 'rotations', r: use.rotation, o: use.office },
                }"
                >{{ use.name }}</router-link
              >
              <template v-else>{{ use.name }}</template>
              <UiTag v-if="use.yours" tone="accent">Your setting</UiTag>
            </h2>
            <ul>
              <li v-for="line in use.lines" :key="line.label">
                <span class="canticle-uses__slot">{{ line.label }}</span>
                {{ line.when.join('; ') }}
              </li>
            </ul>
          </div>
          <p
            v-for="note in canticle.notes"
            :key="note"
            class="canticle-uses__note"
          >
            {{ note }}
          </p>
          <p
            v-for="note in rotationNotes"
            :key="note"
            class="canticle-uses__note"
          >
            {{ note }}
          </p>
        </UiDisclosure>
      </template>
    </header>

    <template v-if="canticle">
      <nav class="canticle-nav" aria-label="Canticles">
        <router-link
          v-if="previous"
          :to="{ name: 'Canticle', params: { slug: previous.slug } }"
          class="canticle-nav__link canticle-nav__link--prev"
        >
          <UiIcon name="chevron-left" />
          <span>{{ previous.latin_name }}</span>
        </router-link>
        <span v-else />
        <router-link
          :to="{ name: 'Canticles' }"
          class="canticle-nav__link canticle-nav__link--all"
        >
          All
        </router-link>
        <router-link
          v-if="next"
          :to="{ name: 'Canticle', params: { slug: next.slug } }"
          class="canticle-nav__link canticle-nav__link--next"
        >
          <span>{{ next.latin_name }}</span>
          <UiIcon name="chevron-right" />
        </router-link>
        <span v-else />
      </nav>

      <div class="book-opening">
        <Ornament glyph="o" />
      </div>

      <div id="main" class="book canticle-text">
        <OfficeLines :modules="modules" />
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { useStore } from 'vuex';
import Loading from '@/components/Loading.vue';
import OfficeLines from '@/components/OfficeLines.vue';
import PageNotFound from '@/views/PageNotFound.vue';
import {
  buildAppointments,
  describeAppointments,
  getCanticleStyle,
  loadCanticleLibrary,
  setCanticleStyle,
} from '@/helpers/canticles';

const route = useRoute();
const store = useStore();

const library = ref(null);
const appointments = ref({});
const loading = ref(true);
const error = ref('');
const notFound = ref(false);
const style = ref('contemporary');

const styleOptions = [
  { value: 'contemporary', label: 'Contemporary' },
  { value: 'traditional', label: 'Traditional' },
];

const canticle = computed(() =>
  library.value?.canticles.find((c) => c.slug === route.params.slug)
);
const index = computed(() =>
  library.value ? library.value.canticles.indexOf(canticle.value) : -1
);
const previous = computed(() =>
  index.value > 0 ? library.value.canticles[index.value - 1] : null
);
const next = computed(() =>
  index.value >= 0 && index.value < library.value.canticles.length - 1
    ? library.value.canticles[index.value + 1]
    : null
);
const category = computed(() =>
  library.value?.categories.find((c) => c.key === canticle.value?.category)
);
const officeLabels = computed(() =>
  (canticle.value?.offices || []).map(
    (key) => library.value.offices.find((o) => o.key === key)?.label || key
  )
);

// Set with the office's own line components, as the office sets it, with
// the citation closing the text.
const modules = computed(() => {
  const lines = [...(canticle.value.texts[style.value] || [])];
  if (canticle.value.citation) {
    lines.push({ content: canticle.value.citation, line_type: 'citation' });
  }
  return [{ name: canticle.value.slug, lines }];
});

const own = computed(() => appointments.value[canticle.value?.slug] || []);

const uses = computed(() => {
  if (!canticle.value) return [];
  const settings = store.state.settings || {};
  const result = [];
  for (const rotation of library.value.rotations) {
    const lines = describeAppointments(library.value, own.value, rotation.key);
    if (!lines.length) continue;
    result.push({
      key: rotation.key,
      rotation: rotation.key,
      office: own.value.find((a) => a.rotation === rotation.key)?.office,
      name: rotation.name,
      yours: (settings.canticle_rotation || 'default') === rotation.key,
      lines,
    });
  }
  const always = own.value.filter((a) => !a.rotation);
  if (always.length) {
    const labels = {
      invitatory: 'Morning Prayer, the invitatory',
      evening_hymn: 'Evening Prayer, at the opening',
      compline: 'Compline, the Song of Simeon',
    };
    const invitatoryWhen = library.value.invitatory_rotations.flatMap((r) =>
      r.appointments
        .filter((a) => a.canticles.includes(canticle.value.slug))
        .map((a) => a.when)
    );
    result.push({
      key: 'always',
      rotation: null,
      name: 'Whatever the rotation',
      yours: false,
      lines: always.map((a) => ({
        label: labels[a.slot] || a.slot,
        when:
          a.slot === 'invitatory'
            ? [...new Set(invitatoryWhen)]
            : ['Every day'],
      })),
    });
  }
  return result;
});

const rotationNotes = computed(() =>
  own.value.filter((a) => a.note).map((a) => a.note)
);

async function changeStyle(value) {
  style.value = value;
  await setCanticleStyle(value);
}

function setTitle() {
  if (canticle.value) {
    document.title = `${canticle.value.latin_name} | The Daily Office`;
  }
}

watch(() => route.params.slug, setTitle);

(async () => {
  style.value = await getCanticleStyle(store.state.settings);
  try {
    library.value = await loadCanticleLibrary();
    appointments.value = buildAppointments(library.value);
    if (!canticle.value) notFound.value = true;
    setTitle();
  } catch (e) {
    error.value = e?.isOffline
      ? 'You’re offline, and the canticles haven’t been downloaded to this device yet.'
      : 'There was an error retrieving this canticle. Please try again.';
  }
  loading.value = false;
})();
</script>

<style scoped>
.canticle-head {
  padding-bottom: 0;
}

.canticle-head .page-header {
  margin-bottom: var(--space-4);
}

.canticle-head__up {
  color: inherit;
  text-decoration: none;
}

.canticle-head__up:hover {
  color: var(--accent);
}

.canticle-facts {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0 var(--space-4);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-soft);
}

.canticle-tools {
  display: flex;
  justify-content: center;
  margin-top: var(--space-4);
}

.canticle-uses {
  margin-top: var(--space-4);
}

.canticle-uses__suggested,
.canticle-uses__note {
  font-size: var(--text-sm);
  color: var(--ink-soft);
}

.canticle-uses__note {
  margin-top: var(--space-2);
  font-style: italic;
}

.canticle-uses__label,
.canticle-uses__slot {
  display: block;
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.canticle-uses__rotation {
  margin-top: var(--space-3);
  padding-top: var(--space-3);
  border-top: 1px solid var(--rule);
}

.canticle-uses__name {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-md);
  font-weight: 400;
  margin-bottom: var(--space-2);
}

.canticle-uses__name a {
  color: var(--ink);
  text-decoration: underline;
  text-decoration-color: var(--accent-rule);
  text-underline-offset: 0.18em;
}

.canticle-uses__name a:hover {
  color: var(--accent);
}

.canticle-uses ul {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--text-sm);
}

.canticle-nav {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: var(--space-2);
  width: min(calc(100% - 2 * var(--gutter)), var(--content-width));
  margin: var(--space-5) auto 0;
  font-size: var(--text-sm);
}

.canticle-nav__link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-width: 0;
  min-height: 2.75rem;
  padding: 0 var(--space-2);
  color: var(--ink-soft);
  font-style: italic;
  text-decoration: none;
}

.canticle-nav__link span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.canticle-nav__link:hover {
  color: var(--accent);
}

.canticle-nav__link .ui-icon {
  flex: none;
  color: var(--accent);
}

.canticle-nav__link--prev {
  justify-self: start;
}

.canticle-nav__link--all {
  justify-self: center;
  font-style: normal;
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
}

.canticle-nav__link--next {
  justify-self: end;
}

.canticle-text {
  margin-bottom: var(--space-7);
}
</style>
