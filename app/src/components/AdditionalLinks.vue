<template>
  <footer class="additional-links-footer">
    <div class="footer-container">
      <h3 class="footer-title">Additional Resources</h3>
      <div class="footer-content">
        <div class="footer-section">
          <h4 class="section-title">Mobile Apps</h4>
          <AppStoreLinks />
        </div>
        <div class="footer-section">
          <h4 class="section-title">Settings</h4>
          <ShareSettings ref="shareSettings" />
        </div>
        <div class="footer-section">
          <h4 class="section-title">Updates</h4>
          <EmailSignup ref="emailSignup" />
        </div>
        <div class="footer-section">
          <h4 class="section-title">Feedback</h4>
          <SubmitFeedback ref="submitFeedback" />
        </div>
      </div>
    </div>
  </footer>
</template>

<script>
import ShareSettings from '@/components/ShareSettings.vue';
import EmailSignup from '@/components/EmailSignup.vue';
import SubmitFeedback from '@/components/SubmitFeedback.vue';
import AppStoreLinks from '@/components/AppStoreLinks.vue';

export default {
  components: {
    ShareSettings,
    EmailSignup,
    SubmitFeedback,
    AppStoreLinks,
  },
  data() {
    return {};
  },
};
</script>

<style scoped>
.additional-links-footer {
  margin-top: 4rem;
  padding: 3rem 2rem 2rem 2rem;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  background-color: rgba(0, 0, 0, 0.02);
}

:root.dark .additional-links-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background-color: rgba(255, 255, 255, 0.02);
}

.footer-container {
  max-width: 900px;
  margin: 0 auto;
}

.footer-title {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-align: center;
  margin: 0 0 2rem 0;
  color: var(--font-color);
}

.footer-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  align-items: start;
}

.footer-section {
  text-align: center;
  padding: 1rem;
  border-radius: 8px;
  background-color: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

:root.dark .footer-section {
  background-color: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.footer-section:hover {
  background-color: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:root.dark .footer-section:hover {
  background-color: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.section-title {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin: 0 0 1rem 0;
  color: var(--font-color);
  opacity: 0.8;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .additional-links-footer {
    padding: 2rem 1rem;
  }
  
  .footer-content {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
  }
  
  .footer-section {
    padding: 0.75rem;
  }
  
  .footer-title {
    font-size: 1.25rem;
    margin-bottom: 1.5rem;
  }
  
  .section-title {
    font-size: 0.9rem;
    margin-bottom: 0.75rem;
  }
}

@media (max-width: 480px) {
  .footer-content {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .footer-section {
    padding: 0.5rem;
  }
  
  .footer-title {
    font-size: 1.1rem;
  }
  
  .section-title {
    font-size: 0.8rem;
  }
}
</style>
