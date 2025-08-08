<template>
  <header class="daily-office-header">
    <!-- App Bar for mobile notch support -->
    <div id="notch" class="notch"></div>
    
    <!-- Main Header Section -->
    <div class="header-container">
      <!-- Theme Switcher in top right -->
      <div class="theme-switcher-container">
        <ThemeSwitcher />
      </div>
      
      <!-- Main Title Section -->
      <div class="title-section">
        <h1 class="main-title">The Daily Office</h1>
        <div class="subtitle">
          Book of Common Prayer 2019
        </div>
      </div>
      
      <!-- Primary Navigation -->
      <nav class="primary-navigation" role="navigation" aria-label="Main navigation">
        <div class="nav-buttons">
          <a href="/" class="nav-link">
            <el-button :type="isPray" round size="large" class="nav-button">
              <font-awesome-icon :icon="['fas', 'fa-praying-hands']" class="nav-icon" />
              Pray
            </el-button>
          </a>
          <a href="/settings" class="nav-link">
            <el-button :type="isSettings" round size="large" class="nav-button">
              <font-awesome-icon :icon="['fas', 'fa-cog']" class="nav-icon" />
              Settings
            </el-button>
          </a>
          <a href="/calendar" class="nav-link">
            <el-button :type="isCalendar" round size="large" class="nav-button">
              <font-awesome-icon :icon="['fas', 'fa-calendar']" class="nav-icon" />
              Calendar
            </el-button>
          </a>
        </div>
      </nav>
      
      <!-- Secondary Navigation -->
      <div class="secondary-navigation">
        <el-button v-if="showLinks" :type="isOther" class="resources-button">
          <el-dropdown :hide-on-click="true" trigger="click" placement="bottom">
            <span class="el-dropdown-link">
              <font-awesome-icon :icon="['fas', 'fa-book-open']" class="dropdown-icon" />
              More Resources
              <el-icon class="el-icon--right">
                <arrow-down />
              </el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu class="resources-dropdown">
                <a href="/about">
                  <el-dropdown-item>
                    <font-awesome-icon :icon="['fas', 'fa-info-circle']" class="menu-icon" />
                    About
                  </el-dropdown-item>
                </a>
                <el-dropdown-item disabled class="section-divider">Prayer Resources</el-dropdown-item>
                <a href="/collects">
                  <el-dropdown-item>
                    <font-awesome-icon :icon="['fas', 'fa-scroll']" class="menu-icon" />
                    Collects
                  </el-dropdown-item>
                </a>
                <a href="/psalms">
                  <el-dropdown-item>
                    <font-awesome-icon :icon="['fas', 'fa-music']" class="menu-icon" />
                    Psalms
                  </el-dropdown-item>
                </a>
                <a href="/litany">
                  <el-dropdown-item>
                    <font-awesome-icon :icon="['fas', 'fa-list']" class="menu-icon" />
                    Great Litany
                  </el-dropdown-item>
                </a>
                <a href="/readings">
                  <el-dropdown-item>
                    <font-awesome-icon :icon="['fas', 'fa-book-bible']" class="menu-icon" />
                    Readings
                  </el-dropdown-item>
                </a>
                <el-dropdown-item disabled class="section-divider">More</el-dropdown-item>
                <el-dropdown-item
                  @click="
                    $emit('share-settings')
                  "
                >
                  <font-awesome-icon :icon="['fas', 'fa-share']" class="menu-icon" />
                  Share Settings
                </el-dropdown-item>
                <el-dropdown-item
                  @click="
                    $emit('submit-feedback')
                  "
                >
                  <font-awesome-icon :icon="['fas', 'fa-comment']" class="menu-icon" />
                  Submit Feedback
                </el-dropdown-item>
                <el-dropdown-item
                  @click="$emit('email-signup')"
                >
                  <font-awesome-icon :icon="['fas', 'fa-envelope']" class="menu-icon" />
                  Get Email Updates
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-button>
      </div>
    </div>
  </header>
</template>

<script>
import ThemeSwitcher from '@/components/ThemeSwitcher.vue';
import { ArrowDown } from '@element-plus/icons-vue';

export default {
  name: 'DailyOfficeHeader',
  components: {
    ThemeSwitcher,
    ArrowDown,
  },
  props: {
    showLinks: {
      type: Boolean,
      default: false,
    },
    isPray: {
      type: String,
      default: '',
    },
    isSettings: {
      type: String,
      default: '',
    },
    isCalendar: {
      type: String,
      default: '',
    },
    isOther: {
      type: String,
      default: '',
    },
  },
  emits: ['share-settings', 'submit-feedback', 'email-signup'],
};
</script>

<style scoped lang="scss">
.daily-office-header {
  position: relative;
  background-color: var(--color-bg);
  border-bottom: 1px solid var(--el-border-color-lighter);
  margin-bottom: 2rem;
}

.notch {
  display: block;
  position: fixed;
  height: env(safe-area-inset-top);
  width: 100%;
  margin: 0;
  top: 0;
  left: 0;
  z-index: 9999;
  background-color: #26282a;
}

.header-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
  position: relative;
}

.theme-switcher-container {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 10;
}

.title-section {
  text-align: center;
  margin: 2rem 0;
  padding-top: calc(env(safe-area-inset-top) + 1rem);
}

.main-title {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 2.5rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  margin: 0;
  color: var(--font-color);
  line-height: 1.2;

  @media (max-width: 768px) {
    font-size: 2rem;
  }

  @media (max-width: 480px) {
    font-size: 1.75rem;
  }
}

.subtitle {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 0.875rem;
  font-weight: 400;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--el-text-color-regular);
  margin-top: 0.5rem;
  opacity: 0.8;
}

.primary-navigation {
  margin: 2rem 0;
}

.nav-buttons {
  display: flex;
  justify-content: center;
  gap: 1rem;
  flex-wrap: wrap;

  @media (max-width: 768px) {
    gap: 0.75rem;
  }

  @media (max-width: 480px) {
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
  }
}

.nav-link {
  text-decoration: none;
}

.nav-button {
  font-family: 'Adobe Caslon Pro', serif;
  font-weight: 600;
  letter-spacing: 0.05em;
  min-width: 120px;
  
  @media (max-width: 480px) {
    width: 200px;
  }
}

.nav-icon {
  margin-right: 0.5rem;
}

.secondary-navigation {
  display: flex;
  justify-content: center;
  margin-bottom: 1rem;
}

.resources-button {
  font-family: 'Adobe Caslon Pro', serif;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.dropdown-icon {
  margin-right: 0.5rem;
}

.resources-dropdown {
  .menu-icon {
    margin-right: 0.5rem;
    width: 1rem;
    opacity: 0.7;
  }

  .section-divider {
    font-weight: 600;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--el-text-color-secondary);
    border-top: 1px solid var(--el-border-color-lighter);
    margin-top: 0.5rem;
    padding-top: 0.5rem;

    &:first-of-type {
      border-top: none;
      margin-top: 0;
      padding-top: 0;
    }
  }
}

// Book-like styling enhancements
.daily-office-header {
  // Add subtle paper texture feel
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(0, 0, 0, 0.01) 50%,
      transparent 100%
    );
    pointer-events: none;
  }
}

// Seasonal color integration (placeholder for seasonal styling)
.header-container {
  position: relative;
  
  &.seasonal-accent {
    &::after {
      content: '';
      position: absolute;
      bottom: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 60px;
      height: 3px;
      background: var(--seasonal-color, var(--link-color));
      border-radius: 2px;
    }
  }
}
</style>