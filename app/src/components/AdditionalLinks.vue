<template>
  <div class="w-full">
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <div class="h-full">
        <ClassicSite />
      </div>

      <div class="h-full">
        <ShareSettings ref="shareSettings" />
      </div>

      <div class="h-full">
        <EmailSignup ref="emailSignup" />
      </div>

      <div class="h-full">
        <SubmitFeedback ref="submitFeedback" />
      </div>
    </div>
  </div>
</template>

<script>
import ShareSettings from '@/components/ShareSettings.vue';
import EmailSignup from '@/components/EmailSignup.vue';
import SubmitFeedback from '@/components/SubmitFeedback.vue';
import ClassicSite from '@/components/ClassicSite.vue';

export default {
  components: {
    ShareSettings,
    EmailSignup,
    SubmitFeedback,
    ClassicSite,
  },
  data() {
    return {};
  },
};
</script>
