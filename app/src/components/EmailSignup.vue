<template>
  <div class="email-action">
    <button @click.prevent="showEmailPanel()" class="action-button">
      <span class="action-icon">📧</span>
      <span class="action-text">Get Email Updates</span>
    </button>
  </div>
  
  <el-drawer v-model="emailPanel" :size="panelSize" direction="rtl" class="elegant-drawer">
    <div class="drawer-content">
      <h3 class="drawer-title">Get Occasional Email Updates</h3>
      <p class="drawer-description">
        Receive a very occasional email when a new feature is launched. We send
        an email only once every few months and will never share your
        information with anyone.
      </p>

      <el-form class="email-form">
        <div class="form-field">
          <el-input
            v-model="emailField"
            type="email"
            placeholder="Email address..."
            required
            class="email-input"
          />
        </div>
        <div class="form-field">
          <el-form-item>
            <el-button type="primary" :disabled="loading" @click="onSubmit" class="submit-button">
              Sign Up
            </el-button>
          </el-form-item>
        </div>
        <el-alert
          v-if="success"
          class="response-alert"
          :title="success"
          type="success"
        />
        <el-alert v-if="error" class="response-alert" :title="error" type="error" />
        <Loading v-if="loading" />
      </el-form>
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

<style lang="scss" scoped>
.email-action {
  display: flex;
  justify-content: center;
}

.action-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  color: var(--font-color);
  font-family: 'Adobe Caslon Pro', serif;
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
  min-width: 100px;
}

.action-button:hover {
  background-color: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.2);
  transform: translateY(-2px);
}

:root.dark .action-button {
  border: 1px solid rgba(255, 255, 255, 0.1);
}

:root.dark .action-button:hover {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.action-icon {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.action-text {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  text-align: center;
  line-height: 1.2;
}

.elegant-drawer {
  .el-drawer__body {
    padding: 0;
  }
}

.drawer-content {
  padding: 2rem;
  font-family: 'Adobe Caslon Pro', serif;
}

.drawer-title {
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin: 0 0 1rem 0;
  color: var(--font-color);
  text-align: left;
}

.drawer-description {
  font-size: 1rem;
  line-height: 1.5;
  margin-bottom: 2rem;
  color: var(--font-color);
  opacity: 0.9;
  text-align: left;
}

.email-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-field {
  margin: 0;
}

.email-input {
  font-family: 'Adobe Caslon Pro', serif;
  width: 100%;
}

.submit-button {
  font-family: 'Adobe Caslon Pro', serif;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  padding: 0.75rem 2rem;
  border-radius: 6px;
}

.response-alert {
  text-align: left;
  margin-top: 1rem;
  font-family: 'Adobe Caslon Pro', serif;
}
</style>
