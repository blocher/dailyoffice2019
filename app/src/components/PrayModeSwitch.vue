<template>
  <UiSegmented
    class="pray-mode"
    :model-value="mode"
    :options="options"
    size="sm"
    aria-label="Daily Office, Family Prayer, or the day's readings"
    @update:model-value="go"
  />
</template>

<script setup>
import { useRouter } from 'vue-router';
import { DynamicStorage } from '@/helpers/storage';

/*
  The three ways into a day: the full Daily Office, short Family Prayer, or
  the day's Scripture readings. Switching keeps the date and the nearest
  matching time of day.
*/
const props = defineProps({
  /** 'office' | 'family' | 'readings' */
  mode: { type: String, required: true },
  date: { type: Date, required: true },
  /**
   * The current office, the readings service (morning/evening/eucharist),
   * or 'day' on the Day page.
   */
  office: { type: String, default: '' },
});

const emit = defineEmits(['change']);

const router = useRouter();

const options = [
  { value: 'office', label: 'Daily Office' },
  { value: 'family', label: 'Family Prayer' },
  { value: 'readings', label: 'Readings' },
];

const EVENING = [
  'evening_prayer',
  'compline',
  'early_evening_prayer',
  'close_of_day_prayer',
];

const TO_DAILY = {
  morning_prayer: 'morning_prayer',
  midday_prayer: 'midday_prayer',
  early_evening_prayer: 'evening_prayer',
  close_of_day_prayer: 'compline',
  evening_prayer: 'evening_prayer',
  compline: 'compline',
};

const TO_FAMILY = {
  morning_prayer: 'morning_prayer',
  midday_prayer: 'midday_prayer',
  evening_prayer: 'early_evening_prayer',
  compline: 'close_of_day_prayer',
  early_evening_prayer: 'early_evening_prayer',
  close_of_day_prayer: 'close_of_day_prayer',
};

function datePath() {
  const d = props.date;
  return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()}`;
}

function isEvening() {
  return EVENING.includes(props.office);
}

async function go(target) {
  if (target === props.mode) return;
  if (target === 'readings') {
    const service = isEvening() ? 'evening_prayer' : 'morning_prayer';
    router.push(`/readings/${service}/${datePath()}`);
    return;
  }
  await DynamicStorage.setItem('serviceType', target);
  // On a page that isn't an office (the Day page), switch the office
  // links in place rather than leaving the page.
  if (props.office === 'day') {
    emit('change', target);
    return;
  }
  if (target === 'family') {
    const office =
      TO_FAMILY[props.office] ||
      (isEvening() ? 'early_evening_prayer' : 'morning_prayer');
    router.push(`/family/${office}/${datePath()}`);
  } else {
    const office =
      TO_DAILY[props.office] ||
      (isEvening() ? 'evening_prayer' : 'morning_prayer');
    router.push(`/${office}/${datePath()}`);
  }
}
</script>
