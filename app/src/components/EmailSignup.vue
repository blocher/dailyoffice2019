<template>
  <span class="sub-menu-item">
    <a href="" v-on:click.prevent="emailPanel = true">
      <font-awesome-icon :icon="['fad', 'envelopes']" />
      <span class="ml-1 text-xs">Get Email Updates</span>
    </a>
  </span>
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
            type="email"
            v-model="emailField"
            placeholder="Email address..."
            required
          />
        </p>
        <p class="mt-2">
          <el-form-item>
            <el-button type="primary" @click="onSubmit" :disabled="loading"
              >Sign Up
            </el-button>
          </el-form-item>
        </p>
        <el-alert
          class="text-left"
          v-if="success"
          :title="success"
          type="success"
        />
        <el-alert class="text-left" v-if="error" :title="error" type="error" />
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
    };
  },
  computed: {
    panelSize() {
      if (this.windowWidth < 1024) {
        return "90%";
      }
      return "37%";
    },
  },
  mounted() {
    this.$nextTick(() => {
      window.addEventListener("resize", this.onResize);
    });
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.onResize);
  },
  methods: {
    validateEmail(email) {
      return true;
      //return /^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/.test(email);
    },
    onResize() {
      this.windowWidth = window.innerWidth;
    },
    onError() {
      alert("error");
    },
    onSubmit() {
      this.loading = true;
      this.success = false;
      this.error = null;
      const url = `${process.env.VUE_APP_API_URL}api/v1/email_signup`;
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
          console.error("There was an error!", error);
          console.log(error.response);
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
