<template>
  <div class="app-store-section">
    <h4 class="app-store-heading">Download the Apps</h4>
    <div class="app-store-container">
      <a 
        href="https://apps.apple.com/us/app/the-daily-office/id1513851259" 
        target="_blank"
        class="app-store-badge"
        aria-label="Download on the App Store"
      >
        <img 
          src="https://developer.apple.com/assets/elements/badges/download-on-the-app-store.svg"
          alt="Download on the App Store"
          class="badge-image"
        />
      </a>
      <a 
        href="https://play.google.com/store/apps/details?id=com.dailyoffice2019.app&hl=en_US&pli=1" 
        target="_blank"
        class="app-store-badge"
        aria-label="Get it on Google Play"
      >
        <img 
          src="https://play.google.com/intl/en_us/badges/static/images/badges/en_badge_web_generic.png"
          alt="Get it on Google Play"
          class="badge-image"
        />
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AppStoreLinks',
  components: {},
  data() {
    return {};
  },
};
</script>

<style scoped lang="scss">
.app-store-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  text-align: center;
}

.app-store-heading {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--font-color);
  margin: 0;
  opacity: 0.9;
}

.app-store-container {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  align-items: center;
  
  @media (min-width: 640px) {
    flex-direction: row;
    justify-content: center;
    gap: 1rem;
  }
}

.app-store-badge {
  display: block;
  transition: transform 0.2s ease, opacity 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    opacity: 0.9;
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:focus {
    outline: 2px solid var(--link-color);
    outline-offset: 4px;
    border-radius: 8px;
  }
}

.badge-image {
  height: 40px;
  width: auto;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  @media (min-width: 640px) {
    height: 48px;
  }
  
  // Book-like styling
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      135deg,
      transparent 0%,
      rgba(255, 255, 255, 0.1) 25%,
      transparent 50%,
      rgba(0, 0, 0, 0.05) 100%
    );
    border-radius: 8px;
    pointer-events: none;
  }
}

// Dark mode adjustments
:root.dark {
  .badge-image {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    
    &::after {
      background: linear-gradient(
        135deg,
        transparent 0%,
        rgba(255, 255, 255, 0.05) 25%,
        transparent 50%,
        rgba(0, 0, 0, 0.1) 100%
      );
    }
  }
}

// Responsive adjustments
@media (max-width: 480px) {
  .app-store-section {
    padding: 0.75rem;
  }
  
  .app-store-heading {
    font-size: 0.875rem;
  }
  
  .badge-image {
    height: 36px;
  }
}
</style>