<template>
  <button @click.prevent="showFeedbackPanel()" class="w-full h-full">
    <div
      class="flex flex-col items-center justify-center p-3 h-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-colors group cursor-pointer text-center"
    >
      <font-awesome-icon
        :icon="['fad', 'message-pen']"
        class="text-lg text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200 mb-2 transition-colors"
      />
      <span
        class="text-xs font-semibold text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100 leading-tight"
        >Submit Feedback</span
      >
    </div>
  </button>

  <el-drawer v-model="feedbackPanel" :size="panelSize" direction="rtl">
    <div class="mt-4">
      <h3 class="text-left">Email Us</h3>
      <p class="text-left">
        Have feedback or want a new feature? Email us at
        <a target="_blank" href="mailto:feedback@dailyoffice2019.com"
          >feedback@dailyoffice2019.com</a
        >
      </p>

      <h3 class="text-left">Join the Facebook Group</h3>
      <p class="text-left">
        Join us for discussion in our
        <a target="_blank" href="https://www.facebook.com/groups/dailyoffice/"
          >Facebook Group</a
        >
        for a lively discussion.
      </p>
    </div>
  </el-drawer>
</template>

<script>
export default {
  data() {
    return {
      emailField: null,
      feedbackPanel: false,
      windowWidth: window.innerWidth,
      success: false,
      error: null,
      loading: false,
      panelSize: '37%',
    };
  },
  created: function () {
    window.addEventListener('resize', this.setPanelSize);
    this.setPanelSize();
  },
  unmounted() {
    window.removeEventListener('resize', this.setPanelSize);
  },
  methods: {
    setPanelSize() {
      if (window.innerWidth < 1024) {
        this.panelSize = '90%';
      } else {
        this.panelSize = '37%';
      }
    },
    showFeedbackPanel() {
      this.feedbackPanel = true;
    },
  },
};
</script>
