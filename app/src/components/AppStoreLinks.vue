<template>
  <span class="sub-menu-item app-store-links">
    <div class="app-store-container">
      <a 
        href="https://apps.apple.com/us/app/the-daily-office/id1513851259" 
        target="_blank"
        class="app-store-link"
        aria-label="Download on the App Store"
      >
        <font-awesome-icon :icon="['fab', 'fa-apple']" size="lg" />
        <br />
        <span class="text-xs">iOS App</span>
      </a>
      <a 
        href="https://play.google.com/store/apps/details?id=com.dailyoffice2019.app&hl=en_US&pli=1" 
        target="_blank"
        class="app-store-link"
        aria-label="Get it on Google Play"
      >
        <font-awesome-icon :icon="['fab', 'fa-google-play']" size="lg" />
        <br />
        <span class="text-xs">Android App</span>
      </a>
    </div>
  </span>
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

<style scoped>
.app-store-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;
}

.app-store-link {
  display: block;
  text-decoration: none;
  color: inherit;
  transition: opacity 0.2s ease;
  text-align: center;
}

.app-store-link:hover {
  opacity: 0.8;
}

.app-store-link:focus {
  outline: 2px solid var(--link-color);
  outline-offset: 2px;
}

@media (min-width: 640px) {
  .app-store-container {
    flex-direction: row;
    justify-content: center;
    gap: 1rem;
  }
}
</style>