<template>
  <UiDisclosure
    class="collect"
    :open="isOpen"
    :meta="chosenSummary"
    @update:open="onToggle"
  >
    <template #title>
      <span class="collect__title">
        <span v-if="collect.number" class="collect__number">{{
          collect.number
        }}</span>
        <span>{{ collect.title }}</span>
      </span>
    </template>

    <!-- Rendered only while open: hundreds of collects stay light. -->
    <template v-if="isOpen">
      <div class="book collect__text">
        <div v-html="traditional ? collect.traditional_text : collect.text" />
        <h5 v-if="collect.attribution">{{ collect.attribution }}</h5>
      </div>

      <fieldset class="collect__offices">
        <legend class="collect__offices-label">
          Add this prayer near the end of
        </legend>
        <div class="collect__office-options">
          <UiCheckbox
            v-for="office in OFFICES"
            :key="office"
            v-model="checkList"
            :value="office"
            :label="office"
            @change="handleCheckChange"
          />
        </div>
      </fieldset>
    </template>
  </UiDisclosure>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { DynamicStorage } from '@/helpers/storage';
import { toast } from '@/ui/feedback';

/*
  One collect in the library. Choosing offices stores the collect's uuid in
  DynamicStorage 'extraCollects', a JSON object of office name -> [uuid].
*/
const OFFICES = [
  'Morning Prayer',
  'Midday Prayer',
  'Evening Prayer',
  'Compline',
];

const props = defineProps({
  collect: { type: Object, required: true },
  traditional: { type: Boolean, default: false },
  extraCollects: { type: Object, default: () => ({}) },
  open: { type: Boolean, default: false },
});
const emit = defineEmits(['extraCollectsChanged', 'update:open']);

function officesFor(extraCollects) {
  return OFFICES.filter(
    (office) =>
      Object.prototype.hasOwnProperty.call(extraCollects || {}, office) &&
      extraCollects[office].includes(props.collect.uuid)
  );
}

const isOpen = ref(props.open);
watch(
  () => props.open,
  (value) => {
    isOpen.value = value;
  }
);

function onToggle(value) {
  if (value === isOpen.value) return;
  isOpen.value = value;
  emit('update:open', value);
}

const checkList = ref(officesFor(props.extraCollects));

watch(
  () => props.extraCollects,
  (value) => {
    checkList.value = officesFor(value);
  }
);

const chosenSummary = computed(() =>
  checkList.value.map((office) => office.replace(' Prayer', '')).join(', ')
);

async function handleCheckChange() {
  const defaultDict = {};
  OFFICES.forEach((office) => {
    defaultDict[office] = [];
  });
  const extraCollects =
    JSON.parse(await DynamicStorage.getItem('extraCollects')) || defaultDict;
  OFFICES.forEach((office) => {
    if (!extraCollects[office]) extraCollects[office] = [];
    if (
      checkList.value.includes(office) &&
      !extraCollects[office].includes(props.collect.uuid)
    ) {
      extraCollects[office].push(props.collect.uuid);
    } else if (
      !checkList.value.includes(office) &&
      extraCollects[office].includes(props.collect.uuid)
    ) {
      extraCollects[office].splice(
        extraCollects[office].indexOf(props.collect.uuid),
        1
      );
    }
  });
  await DynamicStorage.setItem('extraCollects', JSON.stringify(extraCollects));
  emit('extraCollectsChanged');
  toast.success({
    title: 'Saved',
    message: 'Your prayer settings have been updated.',
  });
}
</script>

<style scoped>
.collect :deep(.ui-disclosure__summary) {
  min-height: 2.75rem;
  padding-block: var(--space-2);
}

.collect__title {
  display: flex;
  font-size: var(--text-md);
  align-items: baseline;
  gap: var(--space-3);
  line-height: 1.3;
}

.collect__number {
  flex: 0 0 1.75rem;
  text-align: right;
  font-variant-numeric: oldstyle-nums tabular-nums;
  color: var(--accent);
}

/* The prayer itself, in the reader's chosen size and face. */
.collect__text {
  max-width: none;
  margin: var(--space-2) 0 0;
  padding: 0;
  overflow-wrap: break-word;
}

.collect__offices {
  margin-top: var(--space-4);
  padding-top: var(--space-3);
  border-top: 1px solid var(--rule);
}

.collect__offices-label {
  padding: 0;
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.1em;
  color: var(--ink-faint);
}

.collect__office-options {
  display: flex;
  flex-wrap: wrap;
  column-gap: var(--space-5);
}

.collect__office-options :deep(.ui-check) {
  align-items: center;
  min-height: 2.75rem;
  font-size: var(--text-sm);
}

.collect__office-options :deep(.ui-check input) {
  margin-top: 0;
}
</style>
