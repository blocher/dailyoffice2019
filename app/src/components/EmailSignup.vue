<template>
  <button
    type="button"
    @click.prevent="showEmailPanel()"
    class="w-full h-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-(--accent-color) focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-gray-900 rounded-xl"
  >
    <div
      class="flex flex-col items-center justify-center p-3 h-full bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-colors group cursor-pointer text-center"
    >
      <font-awesome-icon
        :icon="['fad', 'envelopes']"
        class="text-lg text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-200 mb-2 transition-colors"
      />
      <span
        class="text-xs font-semibold text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100 leading-tight"
        >Get Email Updates</span
      >
    </div>
  </button>

  <el-drawer
    v-model="emailPanel"
    :size="panelSize"
    direction="rtl"
    title="Get Email Updates"
  >
    <template #header>
      <div class="drawer-panel flex items-start gap-4">
        <div
          class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-sky-50 text-sky-600 dark:bg-sky-500/15 dark:text-sky-300"
        >
          <font-awesome-icon :icon="['fad', 'envelopes']" class="text-lg" />
        </div>
        <div class="space-y-1 text-left">
          <p
            class="m-0 text-[11px] font-semibold uppercase tracking-[0.18em] text-gray-500 dark:text-gray-400"
          >
            Stay In Touch
          </p>
          <h2 class="m-0 p-0 text-xl font-semibold tracking-tight text-left">
            Get Email Updates
          </h2>
          <p class="m-0 text-sm leading-6 text-gray-600 dark:text-gray-300">
            Receive a very occasional note when a new feature or major update is
            released.
          </p>
        </div>
      </div>
    </template>

    <div class="drawer-panel space-y-6 pb-6 text-left">
      <section
        class="rounded-2xl border border-gray-200 bg-gray-50/80 p-5 dark:border-gray-700 dark:bg-gray-800/60"
      >
        <div
          class="space-y-3 text-sm leading-6 text-gray-700 dark:text-gray-300"
        >
          <p class="m-0">
            We only send emails every few months when there is something worth
            sharing.
          </p>
          <p class="m-0">
            Your email address will never be shared with anyone else.
          </p>
        </div>
      </section>

      <section
        class="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-900/70"
      >
        <h3 class="m-0 p-0 text-base font-semibold tracking-tight text-left">
          Sign up
        </h3>
        <p class="mt-2 mb-0 text-sm leading-6 text-gray-600 dark:text-gray-300">
          Enter your email address and we will let you know when something new
          launches.
        </p>

        <el-form class="mt-5">
          <el-form-item class="mb-4">
            <el-input
              v-model="emailField"
              type="email"
              placeholder="name@example.com"
              autocomplete="email"
              clearable
              required
              @keyup.enter="onSubmit"
            />
          </el-form-item>

          <el-form-item class="mb-0">
            <el-button
              type="primary"
              :loading="loading"
              :disabled="loading || !emailField"
              @click="onSubmit"
            >
              Sign up
            </el-button>
          </el-form-item>
        </el-form>
      </section>

      <el-alert
        v-if="success"
        class="text-left"
        :title="success"
        type="success"
        :closable="false"
        show-icon
      />
      <el-alert
        v-if="error"
        class="text-left"
        :title="error"
        type="error"
        :closable="false"
        show-icon
      />
      <Loading v-if="loading" />
    </div>
  </el-drawer>
</template>

<script>
import Loading from '@/components/Loading.vue';

export default {
  components: {
    Loading,
  },
  data() {
    return {
      emailField: null,
      emailPanel: false,
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
    showEmailPanel() {
      this.emailPanel = true;
    },
    onSubmit() {
      if (!this.emailField || this.loading) {
        return;
      }
      this.loading = true;
      this.success = false;
      this.error = null;
      const url = `${import.meta.env.VITE_API_URL}api/v1/email_signup`;
      const params = {
        email: this.emailField,
      };
      this.$http
        .post(url, params)
        .then(() => {
          this.success = `Thanks for signing up! We'll send an occasional email to ${this.emailField} when a new feature is launched.`;
          this.emailField = null;
          this.loading = false;
        })
        .catch((error) => {
          try {
            this.error = error.response.data[0];
            this.loading = false;
          } catch {
            this.error =
              'There was an unknown error. Please contact feedback@dailyoffice2019.com';
          }
          this.loading = false;
        });
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
