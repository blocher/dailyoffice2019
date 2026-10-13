<template>
  <UiSheet
    :open="panels.email"
    side="auto"
    eyebrow="Stay in touch"
    title="Email updates"
    subtitle="A very occasional note when something new arrives."
    @update:open="(value) => (panels.email = value)"
  >
    <p class="sheet-intro">
      We write every few months, only when there is something worth sharing.
      Your address is never shared with anyone.
    </p>

    <form class="email-form" @submit.prevent="onSubmit">
      <UiField label="Email address" for-id="email-signup-field">
        <UiInput
          id="email-signup-field"
          v-model="emailField"
          type="email"
          placeholder="name@example.com"
          autocomplete="email"
          icon="mail"
          required
        />
      </UiField>
      <UiButton
        type="submit"
        variant="primary"
        :loading="loading"
        :disabled="!emailField"
      >
        Sign up
      </UiButton>
    </form>

    <UiAlert v-if="success" tone="success" class="email-result">
      {{ success }}
    </UiAlert>
    <UiAlert v-if="error" tone="error" class="email-result">
      {{ error }}
    </UiAlert>
  </UiSheet>
</template>

<script>
import { panels } from '@/helpers/panels';

export default {
  data() {
    return {
      emailField: '',
      success: false,
      error: null,
      loading: false,
      panels,
    };
  },
  methods: {
    // Kept for callers that open the panel directly.
    showEmailPanel() {
      panels.email = true;
    },
    onSubmit() {
      if (!this.emailField || this.loading) {
        return;
      }
      this.loading = true;
      this.success = false;
      this.error = null;
      const url = `${import.meta.env.VITE_API_URL}api/v1/email_signup`;
      this.$http
        .post(url, { email: this.emailField })
        .then(() => {
          this.success = `Thank you! We’ll write to ${this.emailField} when something new launches.`;
          this.emailField = '';
        })
        .catch((error) => {
          this.error =
            error?.response?.data?.[0] ||
            'Something went wrong. Please write to feedback@dailyoffice2019.com.';
        })
        .finally(() => {
          this.loading = false;
        });
    },
  },
};
</script>

<style scoped>
.email-form {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-3);
}

.email-form :deep(.ui-field) {
  width: 100%;
}

.email-result {
  margin-top: var(--space-4);
}
</style>
