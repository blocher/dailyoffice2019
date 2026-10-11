<template>
  <button
    type="button"
    @click.prevent="showFeedbackPanel()"
    class="w-full h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--accent-color) focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-gray-900 rounded-xl"
  >
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

  <el-drawer
    v-model="feedbackPanel"
    :size="panelSize"
    direction="rtl"
    title="Submit Feedback"
  >
    <template #header>
      <div class="drawer-panel flex items-start gap-4">
        <div
          class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-300"
        >
          <font-awesome-icon :icon="['fad', 'message-pen']" class="text-lg" />
        </div>
        <div class="space-y-1 text-left">
          <p
            class="m-0 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400"
          >
            We'd Love To Hear From You
          </p>
          <h2 class="m-0 p-0 text-xl font-semibold tracking-tight text-left">
            Submit Feedback
          </h2>
          <p class="m-0 text-sm leading-6 text-gray-600 dark:text-gray-300">
            Share bug reports, corrections, feature ideas, or general feedback.
          </p>
        </div>
      </div>
    </template>

    <div class="drawer-panel space-y-6 pb-6 text-left">
      <section
        class="rounded-2xl border border-gray-200 bg-gray-50/80 p-5 dark:border-gray-700 dark:bg-gray-800/60"
      >
        <p class="m-0 text-sm leading-6 text-gray-700 dark:text-gray-300">
          The fastest way to reach us is by email. If you prefer community
          conversation, the Facebook group is also available.
        </p>
      </section>

      <section
        class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-900/70"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3
              class="m-0 p-0 text-base font-semibold tracking-tight text-left"
            >
              Email us
            </h3>
            <p
              class="mt-2 mb-0 text-sm leading-6 text-gray-600 dark:text-gray-300"
            >
              Send feature requests, factual corrections, or anything else to
              our team.
            </p>
          </div>
          <font-awesome-icon
            :icon="['fad', 'envelope-open-text']"
            class="mt-1 text-base text-gray-400 dark:text-gray-500"
          />
        </div>

        <div class="mt-4">
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="mailto:feedback@dailyoffice2019.com"
            class="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-800 no-underline transition-colors hover:bg-gray-50 hover:text-gray-900 dark:border-gray-700 dark:text-gray-100 dark:hover:bg-gray-800"
          >
            <font-awesome-icon :icon="['fad', 'paper-plane-top']" />
            feedback@dailyoffice2019.com
          </a>
        </div>
      </section>

      <section
        class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-900/70"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <h3
              class="m-0 p-0 text-base font-semibold tracking-tight text-left"
            >
              Join the Facebook group
            </h3>
            <p
              class="mt-2 mb-0 text-sm leading-6 text-gray-600 dark:text-gray-300"
            >
              Join other Daily Office users for discussion and shared ideas.
            </p>
          </div>
          <font-awesome-icon
            :icon="['fab', 'facebook-f']"
            class="mt-1 text-base text-gray-400 dark:text-gray-500"
          />
        </div>

        <div class="mt-4">
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://www.facebook.com/groups/dailyoffice/"
            class="inline-flex items-center gap-2 rounded-xl border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-800 no-underline transition-colors hover:bg-gray-50 hover:text-gray-900 dark:border-gray-700 dark:text-gray-100 dark:hover:bg-gray-800"
          >
            <font-awesome-icon :icon="['fab', 'facebook-f']" />
            Open Facebook Group
          </a>
        </div>
      </section>
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
<style scoped lang="scss">
.drawer-panel :is(h1, h2, h3, h4),
.drawer-panel .drawer-kicker {
  text-align: left !important;
}
</style>
