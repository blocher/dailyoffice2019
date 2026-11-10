<template>
  <div class="prayer-requests">
    <UiButton size="sm" variant="quiet" icon="hand-heart" @click="openDrawer">
      Prayer requests
      <span v-if="items.length" class="prayer-requests__count">
        {{ items.length }}
      </span>
    </UiButton>

    <UiSheet
      v-model:open="drawerOpen"
      side="right"
      eyebrow="Intercessions"
      :title="drawerTitle"
      subtitle="Saved only on this device, to pray at this point in the office."
    >
      <form v-if="editing" class="stack" @submit.prevent="save">
        <UiField label="Name" for-id="prayer-request-name">
          <UiInput
            id="prayer-request-name"
            v-model="name"
            placeholder="Who are you praying for?"
            autocomplete="off"
            maxlength="120"
          />
        </UiField>
        <UiField label="Prayer request" for-id="prayer-request-text" optional>
          <UiInput
            id="prayer-request-text"
            v-model="request"
            multiline
            :rows="4"
            placeholder="Healing, guidance, thanksgiving…"
            maxlength="1000"
          />
        </UiField>
        <p v-if="error" class="prayer-requests__error">{{ error }}</p>
        <div class="cluster prayer-requests__form-actions">
          <UiButton variant="ghost" @click="closeForm">Cancel</UiButton>
          <UiButton type="submit" variant="primary" icon="check">Save</UiButton>
        </div>
      </form>

      <div v-else class="stack">
        <ul v-if="items.length" class="prayer-requests__list">
          <li
            v-for="item in items"
            :key="item.id"
            class="prayer-requests__item"
          >
            <div class="prayer-requests__text">
              <p v-if="item.name" class="prayer-requests__name">
                {{ item.name }}
              </p>
              <p v-if="item.request" class="prayer-requests__request">
                {{ item.request }}
              </p>
            </div>
            <div class="prayer-requests__item-actions">
              <button
                type="button"
                class="prayer-requests__icon-button"
                :aria-label="`Edit prayer for ${item.name || 'this request'}`"
                @click="openEdit(item)"
              >
                <UiIcon name="pen" />
              </button>
              <button
                type="button"
                class="prayer-requests__icon-button"
                :aria-label="`Remove prayer for ${item.name || 'this request'}`"
                @click="remove(item)"
              >
                <UiIcon name="close" />
              </button>
            </div>
          </li>
        </ul>
        <p v-else class="prayer-requests__empty">
          No prayer requests yet. Add the people and needs you want to remember
          here.
        </p>
        <div>
          <UiButton variant="primary" icon="plus" @click="openAdd">
            Add a prayer request
          </UiButton>
        </div>
      </div>
    </UiSheet>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import {
  addPrayerRequest,
  prayerRequests,
  removePrayerRequest,
  updatePrayerRequest,
} from '@/helpers/prayerRequests';
import { confirm, toast } from '@/ui/feedback';

const items = computed(() => prayerRequests.items);

const drawerOpen = ref(false);
// The drawer shows the list, or the form while adding or editing.
const editing = ref(false);
const editingId = ref(null);
const name = ref('');
const request = ref('');
const error = ref('');

const drawerTitle = computed(() => {
  if (!editing.value) return 'Prayer requests';
  return editingId.value ? 'Edit prayer request' : 'Add a prayer request';
});

function openDrawer() {
  editing.value = false;
  drawerOpen.value = true;
}

function closeForm() {
  editing.value = false;
  editingId.value = null;
}

function openAdd() {
  editingId.value = null;
  name.value = '';
  request.value = '';
  error.value = '';
  editing.value = true;
}

function openEdit(item) {
  editingId.value = item.id;
  name.value = item.name;
  request.value = item.request;
  error.value = '';
  editing.value = true;
}

function save() {
  if (!name.value.trim() && !request.value.trim()) {
    error.value = 'Enter a name or a prayer request.';
    return;
  }
  if (editingId.value) {
    updatePrayerRequest(editingId.value, {
      name: name.value,
      request: request.value,
    });
  } else {
    addPrayerRequest({ name: name.value, request: request.value });
    toast.success('Prayer request saved');
  }
  closeForm();
}

async function remove(item) {
  const ok = await confirm({
    title: 'Remove this prayer request?',
    message: item.name || item.request,
    confirmText: 'Remove',
  });
  if (ok) removePrayerRequest(item.id);
}
</script>

<style scoped>
.prayer-requests {
  margin: var(--space-3) 0 var(--space-5);
}

.prayer-requests__count {
  margin-left: 0.25em;
  color: var(--ink-faint);
}

.prayer-requests__empty {
  margin: 0;
  font-style: italic;
  color: var(--ink-soft);
}

.prayer-requests__list {
  list-style: none;
  margin: 0;
  padding: 0;
  border-top: 1px solid var(--rule);
}

.prayer-requests__item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--rule);
}

.prayer-requests__text {
  flex: 1;
  min-width: 0;
  font-size: 1em;
}

.prayer-requests__text p {
  margin: 0;
  overflow-wrap: anywhere;
}

.prayer-requests__name {
  font-weight: 600;
}

.prayer-requests__request {
  color: var(--ink-soft);
  white-space: pre-line;
}

.prayer-requests__item-actions {
  display: flex;
  gap: var(--space-1);
  flex-shrink: 0;
}

.prayer-requests__icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--ink-faint);
  cursor: pointer;
}

.prayer-requests__icon-button:hover,
.prayer-requests__icon-button:focus-visible {
  color: var(--ink);
  background: var(--paper-sunken);
}

.prayer-requests__error {
  margin: 0;
  font-size: var(--text-sm);
  color: var(--tone-danger);
}

.prayer-requests__form-actions {
  justify-content: flex-end;
}
</style>
