<template>
  <span class="sub-menu-item">
    <a href="" @click.prevent="showEmailPanel()">
      <font-awesome-icon :icon="['fad', 'envelopes']" /><br />
      <span class="ml-1 text-xs">Get Email Updates&nbsp;</span>
    </a>
  </span>
  <!--  <el-dropdown-item @click.prevent="emailPanel = true">Get Email Updates</el-dropdown-item>-->
  <el-drawer v-model="emailPanel" :size="panelSize" direction="rtl">
    <div class="mt-4">
      <h3>Get Occasional Email Updates</h3>
      <p class="text-left">
        Receive a very occasional email when a new feature is launched. We send
        an email only once every few months and will never share your
        information with anyone.
      </p>

      <el-form>
        <p class="mt-2">
          <el-input
            v-model="emailField"
            type="email"
            placeholder="Email address..."
            required
          />
        </p>
        <p class="mt-2">
          <el-form-item>
            <el-button type="primary" :disabled="loading" @click="onSubmit">
              Sign Up
            </el-button>
          </el-form-item>
        </p>
        <el-alert
          v-if="success"
          class="text-left"
          :title="success"
          type="success"
        />
        <el-alert v-if="error" class="text-left" :title="error" type="error" />
        <Loading v-if="loading" />
      </el-form>
    </div>
  </el-drawer>
</template>

<script>
export default {
  data() {
    return {
      emailField: null,
      emailPanel: false,
      windowWidth: window.innerWidth,
      success: false,
      error: null,
      loading: false,
      panelSize: "37%",
    };
  },
  created: function () {
    window.addEventListener("resize", this.setPanelSize);
    this.setPanelSize();
  },
  unmounted() {
    window.removeEventListener("resize", this.setPanelSize);
  },
  methods: {
    setPanelSize() {
      if (window.innerWidth < 1024) {
        this.panelSize = "90%";
      } else {
        this.panelSize = "37%";
      }
    },
    showEmailPanel() {
      this.emailPanel = true;
    },
    onSubmit() {
      this.loading = true;
      this.success = false;
      this.error = null;
      const url = `${import.meta.env.VUE_APP_API_URL}api/v1/email_signup`;
      const params = {
        email: this.emailField,
      };
      this.$http
        .post(url, params)
        .then((response) => {
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
              "There was an unknown error. Please contact feedback@dailyoffice2019.com";
          }
          this.loading = false;
        });
    },
  },
};
</script>
