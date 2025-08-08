<template>
  <div class="feedback-action">
    <button @click.prevent="showFeedbackPanel()" class="action-button">
      <span class="action-icon">💬</span>
      <span class="action-text">Submit Feedback</span>
    </button>
  </div>
  
  <el-drawer v-model="feedbackPanel" :size="panelSize" direction="rtl" class="elegant-drawer">
    <div class="drawer-content">
      <h3 class="drawer-title">Contact Us</h3>
      
      <div class="contact-section">
        <h4 class="contact-method-title">📧 Email Us</h4>
        <p class="contact-description">
          Have feedback or want a new feature? Email us at
          <a target="_blank" href="mailto:feedback@dailyoffice2019.com" class="contact-link">
            feedback@dailyoffice2019.com
          </a>
        </p>
      </div>

      <div class="contact-section">
        <h4 class="contact-method-title">💬 Join the Discussion</h4>
        <p class="contact-description">
          Join us for discussion in our
          <a target="_blank" href="https://www.facebook.com/groups/dailyoffice/" class="contact-link">
            Facebook Group
          </a>
          for a lively discussion.
        </p>
      </div>
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

<style lang="scss" scoped>
.feedback-action {
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
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin: 0 0 2rem 0;
  color: var(--font-color);
  text-align: left;
}

.contact-section {
  margin-bottom: 2rem;
  padding: 1.5rem;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  background-color: rgba(0, 0, 0, 0.02);
  transition: all 0.2s ease;
}

.contact-section:hover {
  background-color: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:root.dark .contact-section {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background-color: rgba(255, 255, 255, 0.02);
}

:root.dark .contact-section:hover {
  background-color: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.contact-method-title {
  font-size: 1.1rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  margin: 0 0 0.75rem 0;
  color: var(--font-color);
  text-align: left;
}

.contact-description {
  font-size: 1rem;
  line-height: 1.5;
  margin: 0;
  color: var(--font-color);
  opacity: 0.9;
  text-align: left;
}

.contact-link {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
}

.contact-link:hover {
  text-decoration: underline;
  opacity: 0.8;
}
</style>
