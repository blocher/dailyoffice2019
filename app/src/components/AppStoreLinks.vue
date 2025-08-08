<template>
  <div class="app-store-links">
    <div class="app-link">
      <a 
        href="https://apps.apple.com/us/app/the-daily-office/id1513851259"
        target="_blank"
        class="store-link ios-link"
      >
        <div class="store-icon">📱</div>
        <span class="text-xs">iOS App</span>
      </a>
    </div>
    <div class="app-link">
      <a 
        href="https://play.google.com/store/apps/details?id=com.dailyoffice2019.app&hl=en_US&pli=1"
        target="_blank"
        class="store-link android-link"
      >
        <div class="store-icon">🤖</div>
        <span class="text-xs">Android App</span>
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AppStoreLinks',
  data() {
    return {};
  },
};
</script>

<style scoped>
.app-store-links {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.app-link {
  width: 100%;
}

.store-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-decoration: none;
  color: var(--font-color);
  padding: 4px;
  border-radius: 6px;
  transition: background-color 0.2s ease;
}

.store-link:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

:root.dark .store-link:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.store-icon {
  font-size: 1.2em;
  margin-bottom: 2px;
}

.text-xs {
  font-size: 0.75rem;
  line-height: 1rem;
}
</style>