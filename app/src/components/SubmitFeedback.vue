<template>
  <UiSheet
    :open="panels.feedback"
    side="auto"
    eyebrow="We’d love to hear from you"
    title="Send feedback"
    subtitle="Bug reports, corrections, ideas, or a word of thanks."
    @update:open="(value) => (panels.feedback = value)"
  >
    <section class="sheet-block">
      <h3 class="sheet-block__title"><UiIcon name="mail" /> Email us</h3>
      <p class="sheet-block__text">
        The fastest way to reach us. Feature requests, factual corrections, or
        anything else.
      </p>
      <div class="sheet-block__actions">
        <UiButton
          href="mailto:feedback@dailyoffice2019.com"
          variant="primary"
          icon="send"
        >
          feedback@dailyoffice2019.com
        </UiButton>
      </div>
    </section>

    <section class="sheet-block">
      <h3 class="sheet-block__title">
        <UiIcon name="facebook" /> Facebook group
      </h3>
      <p class="sheet-block__text">
        Talk with others who pray the Daily Office and share ideas.
      </p>
      <div class="sheet-block__actions">
        <UiButton
          href="https://www.facebook.com/groups/dailyoffice/"
          target="_blank"
          icon-right="external"
        >
          Open the group
        </UiButton>
      </div>
    </section>
  </UiSheet>
</template>

<script>
import { panels } from '@/helpers/panels';

export default {
  data() {
    return { panels };
  },
  methods: {
    // Kept for callers that open the panel directly.
    showFeedbackPanel() {
      panels.feedback = true;
    },
  },
};
</script>
