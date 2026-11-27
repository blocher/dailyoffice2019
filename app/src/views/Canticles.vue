<template>
  <div class="page canticles">
    <header class="page-header">
      <p class="eyebrow">The Canticles</p>
      <h1 class="page-title">Canticles</h1>
      <p class="page-lede">
        The songs of Morning and Evening Prayer, from the 2019 Book of Common
        Prayer
      </p>
    </header>

    <Loading v-if="loading" />
    <UiAlert v-if="error" tone="error" :title="error" />

    <template v-if="library">
      <UiSegmented
        class="canticles-views"
        :model-value="view"
        :options="viewOptions"
        variant="underline"
        block
        aria-label="View"
        @update:model-value="setView"
      />

      <!-- Every canticle, searchable and filterable -->
      <template v-if="view === 'library'">
        <section class="canticle-filters" aria-label="Find a canticle">
          <UiInput
            :model-value="filters.search"
            icon="search"
            clearable
            type="search"
            placeholder="Name, citation, or a line of the text"
            aria-label="Search the canticles"
            @update:model-value="setFilter('search', $event)"
          />
          <div class="canticle-filters__grid">
            <UiField label="Office" for-id="canticle-office">
              <UiSelect
                id="canticle-office"
                :model-value="filters.office"
                :options="officeOptions"
                @update:model-value="setFilter('office', $event)"
              />
            </UiField>
            <UiField label="Rotation" for-id="canticle-rotation">
              <UiSelect
                id="canticle-rotation"
                :model-value="filters.rotation"
                :options="rotationOptions"
                @update:model-value="setFilter('rotation', $event)"
              />
            </UiField>
            <UiField label="Season" for-id="canticle-season">
              <UiSelect
                id="canticle-season"
                :model-value="filters.season"
                :options="seasonOptions"
                @update:model-value="setFilter('season', $event)"
              />
            </UiField>
            <UiField label="Day" for-id="canticle-day">
              <UiSelect
                id="canticle-day"
                :model-value="filters.day"
                :options="dayOptions"
                @update:model-value="setFilter('day', $event)"
              />
            </UiField>
          </div>
          <UiField label="Language" class="canticle-filters__language">
            <UiSegmented
              :model-value="style"
              :options="styleOptions"
              aria-label="Language"
              @update:model-value="changeStyle"
            />
          </UiField>
        </section>

        <p class="canticle-count" aria-live="polite">
          {{ resultsLabel }}
          <button
            v-if="filtered"
            type="button"
            class="canticle-count__reset"
            @click="resetFilters"
          >
            Show all
          </button>
        </p>

        <template v-if="results.length">
          <section
            v-for="group in groupedResults"
            :key="group.category.key"
            class="canticle-group"
            :aria-labelledby="`canticle-group-${group.category.key}`"
          >
            <h2
              :id="`canticle-group-${group.category.key}`"
              class="section-title canticle-group__title"
            >
              {{ group.category.label }}
            </h2>
            <p v-if="group.category.description" class="canticle-group__lede">
              {{ group.category.description }}
            </p>
            <ol class="canticle-list">
              <li
                v-for="{ canticle, match } in group.items"
                :key="canticle.slug"
              >
                <router-link
                  :to="{ name: 'Canticle', params: { slug: canticle.slug } }"
                  class="canticle-entry"
                >
                  <span class="canticle-entry__latin">{{
                    canticle.latin_name
                  }}</span>
                  <span class="canticle-entry__english">{{
                    canticle.english_name
                  }}</span>
                  <span
                    v-if="match.where === 'text'"
                    class="canticle-entry__snippet"
                  >
                    <template
                      v-for="(part, index) in highlight(match.line)"
                      :key="index"
                    >
                      <mark v-if="part.hit">{{ part.text }}</mark>
                      <template v-else>{{ part.text }}</template>
                    </template>
                  </span>
                  <span v-else class="canticle-entry__first">{{
                    firstLine(canticle)
                  }}</span>
                  <span class="canticle-entry__meta">
                    <span v-if="canticle.citation">{{
                      canticle.citation
                    }}</span>
                    <span
                      v-for="office in canticle.offices"
                      :key="office"
                      class="canticle-entry__office"
                      >{{ officeShort[office] }}</span
                    >
                  </span>
                </router-link>
              </li>
            </ol>
          </section>
        </template>

        <div v-else class="canticle-empty">
          <Ornament glyph="o" />
          <p>No canticles match.</p>
          <UiButton variant="quiet" size="sm" @click="resetFilters">
            Show all canticles
          </UiButton>
        </div>
      </template>

      <!-- The rotation tables: what is said on each day -->
      <template v-else>
        <section class="rotation-controls" aria-label="Choose a rotation">
          <UiField label="Canticle rotation">
            <UiSegmented
              :model-value="schedule.rotation"
              :options="scheduleRotationOptions"
              block
              aria-label="Canticle rotation"
              @update:model-value="setSchedule('rotation', $event)"
            />
          </UiField>
          <p class="rotation-controls__description">
            <strong>{{ currentRotation.name }}.</strong>
            {{ currentRotation.description }}
            <UiTag
              v-if="currentRotation.key === userRotation"
              tone="accent"
              class="rotation-controls__yours"
              >Your setting</UiTag
            >
          </p>
          <div class="rotation-controls__row">
            <UiField label="Office">
              <UiSegmented
                :model-value="schedule.office"
                :options="scheduleOfficeOptions"
                aria-label="Office"
                @update:model-value="setSchedule('office', $event)"
              />
            </UiField>
            <UiField label="Season" for-id="rotation-season" class="grow">
              <UiSelect
                id="rotation-season"
                :model-value="schedule.season"
                :options="seasonOptions"
                @update:model-value="setSchedule('season', $event)"
              />
            </UiField>
          </div>
        </section>

        <!-- Said before the rotation's canticles, whatever it is -->
        <section
          v-if="schedule.office === 'morning'"
          class="rotation-opening"
          aria-labelledby="rotation-invitatory"
        >
          <h2 id="rotation-invitatory" class="section-title">The Invitatory</h2>
          <UiField
            label="Invitatory setting"
            for-id="rotation-invitatory-setting"
          >
            <UiSelect
              id="rotation-invitatory-setting"
              :model-value="schedule.invitatory"
              :options="invitatoryOptions"
              @update:model-value="setSchedule('invitatory', $event)"
            />
          </UiField>
          <p class="rotation-opening__description">
            {{ currentInvitatory.description }}
            <UiTag
              v-if="currentInvitatory.key === userInvitatory"
              tone="accent"
              class="rotation-controls__yours"
              >Your setting</UiTag
            >
          </p>
          <ul class="rotation-invitatories">
            <li
              v-for="appointment in currentInvitatory.appointments"
              :key="appointment.when"
            >
              <span class="rotation-invitatories__when">{{
                appointment.when
              }}</span>
              <span class="rotation-invitatories__what">
                <template
                  v-for="(slug, index) in appointment.canticles"
                  :key="slug"
                >
                  <span v-if="index" class="rotation-or"> or </span>
                  <router-link :to="canticleLink(slug)" class="rotation-link">{{
                    nameOf(slug)
                  }}</router-link>
                </template>
              </span>
            </li>
          </ul>
          <p class="rotation-note">{{ library.invitatory_note }}</p>
        </section>
        <p v-else class="rotation-opening rotation-opening--evening">
          Every evening opens with the
          <router-link
            :to="canticleLink('phos-hilaron')"
            class="rotation-link"
            >{{ nameOf('phos-hilaron') }}</router-link
          >, and Compline closes the day with the
          <router-link
            :to="canticleLink('nunc-dimittis')"
            class="rotation-link"
            >{{ nameOf('nunc-dimittis') }}</router-link
          >.
        </p>

        <section
          class="rotation-table"
          :aria-label="`${currentRotation.name}, ${officeLabel(schedule.office)}`"
        >
          <div class="rotation-table__head" aria-hidden="true">
            <span>Day</span>
            <span v-for="slot in scheduleSlots" :key="slot.key">{{
              slot.label
            }}</span>
          </div>
          <div
            v-for="row in currentRotation.rows"
            :key="row.key"
            class="rotation-row"
            :class="{
              'is-today': row.days.includes(today) && row.key !== 'feast',
            }"
          >
            <h3 class="rotation-row__day">
              {{ row.label }}
              <span
                v-if="row.days.includes(today) && row.key !== 'feast'"
                class="rotation-row__today"
                >Today</span
              >
            </h3>
            <div
              v-for="slot in scheduleSlots"
              :key="slot.key"
              class="rotation-cell"
            >
              <span class="rotation-cell__slot">{{ slot.label }}</span>
              <ul>
                <li
                  v-for="(group, index) in visibleGroups(row.cells[slot.key])"
                  :key="index"
                >
                  <template v-for="(slug, i) in group.canticles" :key="slug">
                    <span v-if="i" class="rotation-or"> or </span>
                    <router-link
                      :to="canticleLink(slug)"
                      class="rotation-link"
                      >{{ nameOf(slug) }}</router-link
                    >
                  </template>
                  <span
                    v-if="group.seasons.length && !schedule.season"
                    class="rotation-cell__seasons"
                    >{{ seasonList(group.seasons) }}</span
                  >
                </li>
              </ul>
            </div>
          </div>
        </section>

        <ul v-if="scheduleNotes.length" class="rotation-notes">
          <li
            v-for="note in scheduleNotes"
            :key="note.text"
            class="rotation-note"
          >
            {{ note.text }}
          </li>
        </ul>
        <p class="rotation-settings">
          <UiButton variant="quiet" size="sm" icon="settings" to="/settings">
            Change your canticle settings
          </UiButton>
        </p>
      </template>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useStore } from 'vuex';
import Loading from '@/components/Loading.vue';
import { SessionStore } from '@/helpers/sessionStore';
import {
  buildAppointments,
  dayKey,
  filterCanticles,
  getCanticleStyle,
  hasFilters,
  listLabel,
  loadCanticleLibrary,
  normalize,
  setCanticleStyle,
} from '@/helpers/canticles';

const route = useRoute();
const router = useRouter();
const store = useStore();

const library = ref(null);
const appointments = ref({});
const loading = ref(true);
const error = ref('');
const style = ref('contemporary');
const today = dayKey();

const FILTER_KEYS = ['search', 'office', 'rotation', 'season', 'day'];
const filters = reactive({
  search: '',
  office: '',
  rotation: '',
  season: '',
  day: '',
});
const schedule = reactive({
  rotation: '1979',
  office: 'morning',
  season: '',
  invitatory: 'invitatory_traditional',
});

const view = computed(() =>
  route.query.view === 'rotations' ? 'rotations' : 'library'
);
const viewOptions = [
  { value: 'library', label: 'All Canticles' },
  { value: 'rotations', label: 'Rotations' },
];
const styleOptions = [
  { value: 'contemporary', label: 'Contemporary' },
  { value: 'traditional', label: 'Traditional' },
];
const officeShort = {
  morning: 'Morning',
  evening: 'Evening',
  compline: 'Compline',
};

const userRotation = computed(
  () => store.state.settings?.canticle_rotation || 'default'
);
const userInvitatory = computed(
  () =>
    store.state.settings?.morning_prayer_invitatory || 'invitatory_traditional'
);

const officeOptions = computed(() => [
  { value: '', label: 'Any office' },
  ...library.value.offices.map((o) => ({ value: o.key, label: o.label })),
]);
const rotationOptions = computed(() => [
  { value: '', label: 'Any rotation' },
  ...library.value.rotations.map((r) => ({
    value: r.key,
    label: r.key === userRotation.value ? `${r.name} (yours)` : r.name,
  })),
]);
const seasonOptions = computed(() => [
  { value: '', label: 'All seasons' },
  ...library.value.seasons.map((s) => ({ value: s.key, label: s.label })),
]);
const DAY_OPTIONS = [
  ['sunday', 'Sunday'],
  ['monday', 'Monday'],
  ['tuesday', 'Tuesday'],
  ['wednesday', 'Wednesday'],
  ['thursday', 'Thursday'],
  ['friday', 'Friday'],
  ['saturday', 'Saturday'],
  ['feast', 'Principal Feasts'],
];
const dayOptions = computed(() => [
  { value: '', label: 'Any day' },
  ...DAY_OPTIONS.map(([value, label]) => ({
    value,
    label: value === today ? `${label} (today)` : label,
  })),
]);

const results = computed(() =>
  library.value
    ? filterCanticles(library.value, appointments.value, filters, style.value)
    : []
);
const groupedResults = computed(() =>
  library.value.categories
    .map((category) => ({
      category,
      items: results.value.filter((r) => r.canticle.category === category.key),
    }))
    .filter((group) => group.items.length)
);
const filtered = computed(() => Boolean(filters.search) || hasFilters(filters));
const resultsLabel = computed(() => {
  const count = results.value.length;
  return `${count} ${count === 1 ? 'canticle' : 'canticles'}`;
});

// Rotations view
const scheduleRotationOptions = computed(() =>
  // "Seasonal Rotation" -> "Seasonal", so three fit across a phone.
  library.value.rotations.map((r) => ({
    value: r.key,
    label: r.name.replace(/ Rotation$/, ''),
  }))
);
const scheduleOfficeOptions = [
  { value: 'morning', label: 'Morning' },
  { value: 'evening', label: 'Evening' },
];
const currentRotation = computed(
  () =>
    library.value.rotations.find((r) => r.key === schedule.rotation) ||
    library.value.rotations[0]
);
const scheduleSlots = computed(() =>
  library.value.slots.filter((slot) => slot.office === schedule.office)
);
const scheduleNotes = computed(() => {
  const slots = scheduleSlots.value.map((slot) => slot.key);
  return currentRotation.value.notes.filter((note) =>
    slots.includes(note.slot)
  );
});
const invitatoryOptions = computed(() =>
  library.value.invitatory_rotations.map((r) => ({
    value: r.key,
    label: r.key === userInvitatory.value ? `${r.name} (yours)` : r.name,
  }))
);
const currentInvitatory = computed(
  () =>
    library.value.invitatory_rotations.find(
      (r) => r.key === schedule.invitatory
    ) || library.value.invitatory_rotations[0]
);

function visibleGroups(groups) {
  if (!schedule.season) return groups;
  return groups.filter(
    (group) => !group.seasons.length || group.seasons.includes(schedule.season)
  );
}

function seasonList(seasons) {
  return listLabel(seasons, library.value.seasons);
}

function officeLabel(key) {
  return (library.value.offices.find((o) => o.key === key) || {}).label || '';
}

const bySlug = computed(() =>
  Object.fromEntries((library.value?.canticles || []).map((c) => [c.slug, c]))
);

function nameOf(slug) {
  return bySlug.value[slug]?.latin_name || slug;
}

function canticleLink(slug) {
  return { name: 'Canticle', params: { slug } };
}

function firstLine(canticle) {
  const line = (canticle.texts[style.value] || []).find(
    (l) => l.line_type === 'congregation' || l.line_type === 'leader'
  );
  return (line?.content || '').replace(/[\s*;:,]+$/, '');
}

// Splits a line around the search so the match can be marked.
function highlight(text) {
  const query = normalize(filters.search);
  if (!query) return [{ text, hit: false }];
  // Search the normalized text, then map the match back onto the original
  // (normalizing keeps one character per character for these texts).
  const plain = String(text)
    .toLowerCase()
    .replace(/[‘’ʼ]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[–—]/g, '-');
  const index = plain.indexOf(query);
  if (index < 0) return [{ text, hit: false }];
  return [
    { text: text.slice(0, index), hit: false },
    { text: text.slice(index, index + query.length), hit: true },
    { text: text.slice(index + query.length), hit: false },
  ];
}

// Filters live in the URL, so a filtered list can be shared.
function readQuery() {
  for (const key of FILTER_KEYS) {
    const value = route.query[key === 'search' ? 'q' : key];
    filters[key] = typeof value === 'string' ? value : '';
  }
  if (typeof route.query.r === 'string') schedule.rotation = route.query.r;
  if (route.query.o === 'evening' || route.query.o === 'morning')
    schedule.office = route.query.o;
  if (typeof route.query.s === 'string') schedule.season = route.query.s;
}

function writeQuery() {
  const query = {};
  if (view.value === 'rotations') {
    query.view = 'rotations';
    query.r = schedule.rotation;
    query.o = schedule.office;
    if (schedule.season) query.s = schedule.season;
  } else {
    for (const key of FILTER_KEYS) {
      if (filters[key]) query[key === 'search' ? 'q' : key] = filters[key];
    }
  }
  SessionStore.setItem('preventScroll', 'true');
  router.replace({ name: 'Canticles', query });
}

function setFilter(key, value) {
  filters[key] = value || '';
  writeQuery();
}

function resetFilters() {
  for (const key of FILTER_KEYS) filters[key] = '';
  writeQuery();
}

function setView(value) {
  SessionStore.setItem('preventScroll', 'true');
  const query = value === 'rotations' ? { view: 'rotations' } : {};
  router.replace({ name: 'Canticles', query }).then(writeQuery);
}

function setSchedule(key, value) {
  schedule[key] = value;
  if (key !== 'invitatory') writeQuery();
}

async function changeStyle(value) {
  style.value = value;
  await setCanticleStyle(value);
}

watch(
  () => route.query,
  () => {
    if (route.name === 'Canticles') readQuery();
  }
);

onMounted(async () => {
  schedule.rotation = userRotation.value;
  schedule.invitatory = userInvitatory.value;
  readQuery();
  style.value = await getCanticleStyle(store.state.settings);
  try {
    library.value = await loadCanticleLibrary();
    appointments.value = buildAppointments(library.value);
    if (!library.value.rotations.some((r) => r.key === schedule.rotation)) {
      schedule.rotation = library.value.rotations[0].key;
    }
  } catch (e) {
    error.value = e?.isOffline
      ? 'You’re offline, and the canticles haven’t been downloaded to this device yet.'
      : 'There was an error retrieving the canticles. Please try again.';
  }
  loading.value = false;
});
</script>

<style scoped>
.canticles-views {
  margin-bottom: var(--space-5);
}

.canticle-filters,
.rotation-controls {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--rule);
}

.canticle-filters__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 9.5rem), 1fr));
  gap: var(--space-3) var(--space-4);
}

.canticle-filters :deep(.ui-field__label),
.rotation-controls :deep(.ui-field__label),
.rotation-opening :deep(.ui-field__label) {
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.canticle-count {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 2.75rem;
  margin-top: var(--space-2);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.canticle-count__reset {
  min-height: 2.75rem;
  color: var(--accent);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
}

.canticle-count__reset:hover {
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

.canticle-group {
  margin-top: var(--space-5);
}

.canticle-group__title {
  margin-bottom: var(--space-1);
}

.canticle-group__lede {
  margin-bottom: var(--space-3);
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-soft);
}

/* Two calm columns on wider screens; one on phones. */
.canticle-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 19rem), 1fr));
  column-gap: var(--space-6);
}

.canticle-list > li {
  border-top: 1px solid var(--rule);
  min-width: 0;
}

.canticle-entry {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-height: 2.75rem;
  padding: var(--space-3) var(--space-2);
  color: var(--ink);
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: background-color var(--duration) var(--ease);
}

.canticle-entry:hover {
  background-color: var(--accent-wash);
}

.canticle-entry__latin {
  font-style: italic;
  font-size: var(--text-lg);
  line-height: var(--leading-tight);
  color: var(--accent);
}

.canticle-entry__english {
  font-size: var(--text-md);
  line-height: var(--leading-tight);
}

.canticle-entry__first,
.canticle-entry__snippet {
  font-size: var(--text-sm);
  line-height: 1.35;
  color: var(--ink-soft);
}

.canticle-entry__snippet {
  font-style: italic;
}

.canticle-entry__snippet mark {
  background-color: color-mix(in srgb, var(--accent) 18%, transparent);
  color: var(--ink);
  border-radius: 2px;
  padding: 0 0.1em;
}

.canticle-entry__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0 var(--space-3);
  margin-top: 0.15rem;
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
}

.canticle-filters__language {
  align-self: flex-start;
}

.canticle-entry__office {
  color: var(--accent);
}

.canticle-empty {
  padding: var(--space-7) 0;
  text-align: center;
  font-style: italic;
  color: var(--ink-soft);
}

.canticle-empty .ornament {
  font-size: 1.5rem;
  margin-bottom: var(--space-3);
}

/* Rotations */
.rotation-controls__description strong {
  font-weight: 400;
  font-style: normal;
  color: var(--ink);
}

.rotation-controls__description,
.rotation-opening__description {
  font-style: italic;
  color: var(--ink-soft);
}

.rotation-controls__yours {
  margin-left: var(--space-2);
  font-style: normal;
  vertical-align: 0.1em;
}

.rotation-controls__row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-4);
}

.rotation-controls__row .grow {
  flex: 1 1 12rem;
  min-width: 0;
}

.rotation-opening {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-top: var(--space-5);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid var(--rule);
}

.rotation-opening--evening {
  display: block;
  font-style: italic;
  color: var(--ink-soft);
}

.rotation-invitatories {
  display: flex;
  flex-direction: column;
}

.rotation-invitatories li {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--space-4);
  padding: var(--space-2) 0;
  border-top: 1px solid var(--rule);
}

.rotation-invitatories__when {
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.08em;
  color: var(--ink-soft);
}

.rotation-link {
  font-style: italic;
  color: var(--ink);
  text-decoration: underline;
  text-decoration-color: var(--accent-rule);
  text-underline-offset: 0.18em;
}

.rotation-link:hover {
  color: var(--accent);
  text-decoration-color: currentColor;
}

.rotation-or {
  color: var(--ink-faint);
  font-size: var(--text-sm);
}

.rotation-note {
  font-size: var(--text-sm);
  font-style: italic;
  color: var(--ink-soft);
}

/* The table: a day per row, a canticle per column. On phones the day sits
   above its two canticles. */
.rotation-table {
  margin-top: var(--space-5);
}

.rotation-table__head,
.rotation-row {
  display: grid;
  grid-template-columns: minmax(7rem, 0.8fr) 1fr 1fr;
  gap: var(--space-4);
}

.rotation-table__head {
  padding: 0 var(--space-2) var(--space-2);
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.rotation-row {
  padding: var(--space-3) var(--space-2);
  border-top: 1px solid var(--rule);
  border-radius: var(--radius-sm);
}

.rotation-row.is-today {
  background-color: var(--accent-wash);
}

.rotation-row__day {
  font-size: var(--text-md);
  font-weight: 400;
  line-height: var(--leading-tight);
}

.rotation-row__today {
  display: block;
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--accent);
}

.rotation-cell {
  min-width: 0;
}

.rotation-cell ul {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.rotation-cell__slot {
  display: none;
}

.rotation-cell__seasons {
  display: block;
  font-size: var(--text-xs);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
}

.rotation-notes {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-top: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--rule);
}

.rotation-settings {
  margin-top: var(--space-5);
  text-align: center;
}

@media (max-width: 559px) {
  .rotation-table__head {
    display: none;
  }

  .rotation-row {
    grid-template-columns: 1fr 1fr;
    gap: var(--space-2) var(--space-4);
  }

  .rotation-row__day {
    grid-column: 1 / -1;
  }

  .rotation-row__today {
    display: inline;
    margin-left: var(--space-2);
  }

  .rotation-cell__slot {
    display: block;
    font-size: var(--text-xs);
    font-variant-caps: all-small-caps;
    letter-spacing: 0.1em;
    color: var(--ink-faint);
  }
}
</style>
