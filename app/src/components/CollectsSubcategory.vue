<template>
  <UiDisclosure
    class="collects-group"
    meta-tone="neutral"
    :open="groupOpen"
    @update:open="groupOpen = $event"
  >
    <template #title>
      <span class="collects-group__title">{{ subcategory.name }}</span>
    </template>
    <template #meta>
      <span class="collects-group__meta">
        <span v-if="chosenCount" class="collects-group__chosen"
          >{{ chosenCount }} chosen ·
        </span>
        {{ subcategory.collects.length }}
      </span>
    </template>

    <div v-if="subcategory.collects.length > 1" class="collects-group__tools">
      <button
        type="button"
        class="collects-group__tool"
        :disabled="disableShowAll"
        @click="expandAll()"
      >
        Open all
      </button>
      <span aria-hidden="true">·</span>
      <button
        type="button"
        class="collects-group__tool"
        :disabled="disableHideAll"
        @click="collapseAll(false)"
      >
        Close all
      </button>
    </div>

    <div class="collects-group__list">
      <Collect
        v-for="collect in subcategory.collects"
        :key="collect.uuid"
        :collect="collect"
        :traditional="traditional"
        :extra-collects="extraCollects"
        :open="openedItems.includes(collect.uuid)"
        @update:open="setOpen(collect.uuid, $event)"
        @extra-collects-changed="emit('extraCollectsChanged')"
      />
    </div>
  </UiDisclosure>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import Collect from '@/components/Collect.vue';

/*
  One subcategory of collects ("Advent", "The Church"…), folded by default.
  The parent drives it through expandAll / collapseAll / showOnlySelected.
*/
const props = defineProps({
  subcategory: { type: Object, required: true },
  traditional: { type: Boolean, default: false },
  extraCollects: { type: Object, default: () => ({}) },
  // While a search is active, groups open to show the matching titles.
  searching: { type: Boolean, default: false },
});
const emit = defineEmits(['extraCollectsChanged']);

const groupOpen = ref(false);
const openedItems = ref([]);

watch(
  () => props.searching,
  (searching) => {
    groupOpen.value = searching;
  }
);

const chosenCount = computed(() => {
  const chosen = new Set(
    Object.values(props.extraCollects || {}).flatMap((uuids) =>
      Array.isArray(uuids) ? uuids : []
    )
  );
  return props.subcategory.collects.filter((c) => chosen.has(c.uuid)).length;
});

const disableShowAll = computed(
  () => openedItems.value.length === props.subcategory.collects.length
);
const disableHideAll = computed(() => openedItems.value.length === 0);

function setOpen(uuid, value) {
  const without = openedItems.value.filter((id) => id !== uuid);
  openedItems.value = value ? [...without, uuid] : without;
}

function expandAll() {
  groupOpen.value = true;
  openedItems.value = props.subcategory.collects.map((c) => c.uuid);
}

// closeGroup: also fold the subcategory itself (the page-level "Collapse all").
function collapseAll(closeGroup = true) {
  openedItems.value = [];
  if (closeGroup) groupOpen.value = false;
}

function showOnlySelected(checkList) {
  const uuids = props.subcategory.collects.map((c) => c.uuid);
  openedItems.value = checkList.filter((uuid) => uuids.includes(uuid));
  groupOpen.value = openedItems.value.length > 0;
}

defineExpose({ expandAll, collapseAll, showOnlySelected });
</script>

<style scoped>
.collects-group__title {
  font-size: var(--text-lg);
  line-height: 1.25;
}

.collects-group__meta {
  font-variant-numeric: oldstyle-nums;
}

.collects-group__chosen {
  font-style: italic;
  color: var(--accent);
}

.collects-group__tools {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-1);
  margin-top: calc(-1 * var(--space-2));
  font-size: var(--text-sm);
  color: var(--ink-faint);
}

.collects-group__tool {
  min-height: 2.75rem;
  padding: 0 var(--space-2);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--accent);
}

.collects-group__tool:disabled {
  color: var(--ink-faint);
  opacity: 0.6;
}

.collects-group__tool:not(:disabled):hover {
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

/* The collects sit indented under their group, separated by hairlines. */
.collects-group__list {
  border-top: 1px solid var(--rule);
}

@media (min-width: 640px) {
  .collects-group__list {
    padding-left: var(--space-4);
  }
}

.collects-group__list > :last-child {
  border-bottom: 0;
}
</style>
