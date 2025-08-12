<template>
  <footer class="additional-links-footer">
    <div class="footer-container">
      <div class="footer-section">
        <h3 class="footer-heading">Connect</h3>
        <div class="footer-grid">
          <div class="footer-item">
            <AppStoreLinks />
          </div>
          <div class="footer-item">
            <ShareSettings ref="shareSettings" />
          </div>
          <div class="footer-item">
            <EmailSignup ref="emailSignup" />
          </div>
          <div class="footer-item">
            <SubmitFeedback ref="submitFeedback" />
          </div>
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
  name: 'AdditionalLinks',
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

<style scoped lang="scss">
.additional-links-footer {
  margin-top: 3rem;
  padding: 2rem 0;
  border-top: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(
    180deg,
    transparent 0%,
    rgba(0, 0, 0, 0.01) 100%
  );
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.footer-section {
  text-align: center;
}

.footer-heading {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--font-color);
  margin-bottom: 2rem;
  opacity: 0.9;
}

.footer-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  justify-items: center;
  align-items: start;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }
  
  @media (max-width: 480px) {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}

.footer-item {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 80px;
  width: 100%;
  
  // Add subtle paper-like styling
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 80%;
    height: 1px;
    background: linear-gradient(
      90deg,
      transparent 0%,
      var(--el-border-color-lighter) 50%,
      transparent 100%
    );
    opacity: 0.5;
  }
  
  @media (max-width: 480px) {
    min-height: 60px;
    
    &::before {
      width: 90%;
    }
  }
}

// Hover effects for better interactivity
.footer-item {
  transition: transform 0.2s ease, opacity 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
  }
  
  &:active {
    transform: translateY(0);
  }
}

// Book-like styling enhancements
.additional-links-footer {
  position: relative;
  
  // Add subtle page texture
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(
      circle at 50% 50%,
      rgba(0, 0, 0, 0.01) 0%,
      transparent 70%
    );
    pointer-events: none;
  }
  
  // Add bottom margin for audio player
  margin-bottom: 120px;
  
  @media (max-width: 768px) {
    margin-bottom: 140px;
  }
  
  @media (max-width: 480px) {
    margin-bottom: 160px;
  }
}

// Dark mode adjustments
:root.dark {
  .additional-links-footer {
    background: linear-gradient(
      180deg,
      transparent 0%,
      rgba(255, 255, 255, 0.01) 100%
    );
    
    &::after {
      background: radial-gradient(
        circle at 50% 50%,
        rgba(255, 255, 255, 0.01) 0%,
        transparent 70%
      );
    }
  }
  
  .footer-item::before {
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.1) 50%,
      transparent 100%
    );
  }
}

// Responsive grid adjustments
@media (max-width: 1024px) {
  .footer-grid {
    grid-template-columns: repeat(2, 1fr);
    max-width: 600px;
    margin: 0 auto;
  }
}

@media (max-width: 640px) {
  .footer-container {
    padding: 0 0.75rem;
  }
  
  .footer-heading {
    font-size: 1.125rem;
    margin-bottom: 1.5rem;
  }
}
</style>
