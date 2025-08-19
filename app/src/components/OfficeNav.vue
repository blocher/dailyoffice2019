<template>
  <!-- Service Type Toggle -->
  <div class="service-type-section" v-if="currentServiceType">
    <div class="service-toggle-card">
      <div class="service-info">
        <div class="current-mode">
          <font-awesome-icon 
            :icon="currentServiceType === 'office' ? ['fas', 'book-open'] : ['fas', 'users']" 
            class="mode-icon" 
          />
          <span class="mode-text">
            {{ currentServiceType === 'office' ? 'Full Daily Office mode' : 'Shorter Family Prayer mode' }}
          </span>
        </div>
        <el-button 
          type="text" 
          size="small" 
          @click="toggleServiceType"
          class="switch-button"
        >
          <font-awesome-icon :icon="['fas', 'arrow-right-arrow-left']" class="switch-icon" />
          {{ currentServiceType === 'office' ? 'Switch to Family Prayer' : 'Switch to full Daily Office' }}
        </el-button>
      </div>
    </div>
  </div>

  <!-- Prayer Office Navigation -->
  <div class="office-navigation">
    <h4 class="nav-section-title">
      <font-awesome-icon :icon="['fas', 'clock']" class="section-icon" />
      Prayer Times
    </h4>
    <div class="prayer-times-grid">
      <div v-for="link in links" :key="link.name" class="prayer-time-card">
        <router-link :to="link.to" class="prayer-link">
          <div 
            class="prayer-card" 
            :class="{ 
              'selected': selectedClass(link.name) === 'selected',
              'current-time': isCurrentTime(link.name)
            }"
          >
            <div class="prayer-icon-container">
              <font-awesome-icon :icon="link.icon" class="prayer-icon" />
            </div>
            <div class="prayer-details">
              <h5 class="prayer-name" v-html="link.text" />
              <span class="prayer-time">{{ getPrayerTime(link.name) }}</span>
            </div>
          </div>
        </router-link>
      </div>
    </div>
  </div>

  <!-- Day's Readings -->
  <div class="readings-section">
    <h4 class="nav-section-title">
      <font-awesome-icon :icon="['fas', 'book-bible']" class="section-icon" />
      Scripture
    </h4>
    <router-link :to="readingsLink.to" class="readings-link">
      <div 
        class="readings-card"
        :class="{ 'selected': selectedClass(readingsLink.name) === 'selected' }"
      >
        <div class="readings-content">
          <font-awesome-icon :icon="readingsLink.icon" class="readings-icon" />
          <span class="readings-text" v-html="readingsLink.text" />
        </div>
        <font-awesome-icon :icon="['fas', 'chevron-right']" class="chevron-icon" />
      </div>
    </router-link>
  </div>

  <!-- Day Navigation -->
  <div class="day-navigation">
    <h4 class="nav-section-title">
      <font-awesome-icon :icon="['fas', 'calendar-days']" class="section-icon" />
      Navigate Days
    </h4>
    <div class="day-nav-grid">
      <div v-for="link in dayLinks" :key="link.text" class="day-nav-item">
        <router-link :to="link.to" @click="scrollToTop" class="day-link">
          <div 
            class="day-card"
            :class="{ 'selected': link.selected, 'today': link.text === 'Today' }"
          >
            <font-awesome-icon
              v-if="link.icon === 'left'"
              :icon="['fas', 'chevron-left']"
              class="day-icon"
            />
            <span class="day-text">{{ link.text }}</span>
            <font-awesome-icon
              v-if="link.icon === 'right'"
              :icon="['fas', 'chevron-right']"
              class="day-icon"
            />
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
// @ is an alias to /src

import { DynamicStorage } from '@/helpers/storage';

export default {
  name: 'OfficeNav',
  components: {},
  props: {
    calendarDate: {
      type: Date,
    },
    selectedOffice: {
      type: String,
    },
    serviceType: {
      default: 'office',
      type: String,
    },
  },
  data() {
    return {
      links: null,
      dayLink: null,
      currentServiceType: this.serviceType,
    };
  },
  async created() {
    const tomorrow = new Date(this.calendarDate);
    tomorrow.setDate(this.calendarDate.getDate() + 1);
    const yesterday = new Date(this.calendarDate);
    yesterday.setDate(this.calendarDate.getDate() - 1);
    this.dailyLinks = [
      {
        to: `/morning_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Morning<br>Prayer',
        name: 'morning_prayer',
        icon: ['fad', 'sunrise'],
      },
      {
        to: `/midday_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Midday<br>Prayer',
        name: 'midday_prayer',
        icon: ['fad', 'sun'],
      },
      {
        to: `/evening_prayer/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Evening<br>Prayer',
        name: 'evening_prayer',
        icon: ['fad', 'sunset'],
      },
      {
        to: `/compline/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: 'Compline<br>(Bedtime)',
        name: 'compline',
        icon: ['fad', 'moon-stars'],
      },
    ];
    ((this.readingsLink = {
      to: `/readings/${this.calendarDate.getFullYear()}/${
        this.calendarDate.getMonth() + 1
      }/${this.calendarDate.getDate()}`,
      text: "Day's Readings",
      name: 'readings',
      icon: ['fad', 'book-bible'],
    }),
      (this.familyLinks = [
        {
          to: `/family/morning_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
          }/${this.calendarDate.getDate()}`,
          text: 'Morning',
          name: 'morning_prayer',
          icon: ['fad', 'sunrise'],
        },
        {
          to: `/family/midday_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
          }/${this.calendarDate.getDate()}`,
          text: 'Midday',
          name: 'midday_prayer',
          icon: ['fad', 'sun'],
        },
        {
          to: `/family/early_evening_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
          }/${this.calendarDate.getDate()}`,
          text: 'Early Evening',
          name: 'early_evening_prayer',
          icon: ['fad', 'sunset'],
        },
        {
          to: `/family/close_of_day_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
          }/${this.calendarDate.getDate()}`,
          text: 'Close of Day',
          name: 'close_of_day_prayer',
          icon: ['fad', 'moon-stars'],
        },
      ]));
    if (this.currentServiceType == 'family') {
      this.links = this.familyLinks;
    } else {
      this.links = this.dailyLinks;
    }
    const servicePart =
      this.currentServiceType == 'family' ? `/${this.currentServiceType}` : '';
    this.dayLinks = [
      {
        to: `${servicePart}/${this.selectedOffice}/${yesterday.getFullYear()}/${
          yesterday.getMonth() + 1
        }/${yesterday.getDate()}`,
        icon: 'left',
        text: yesterday.toLocaleDateString('en-us', { weekday: 'long' }),
      },
      {
        to: `${servicePart}/${this.selectedOffice}/${this.calendarDate.getFullYear()}/${
          this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: this.calendarDate.toLocaleDateString('en-us', {
          weekday: 'long',
        }),
        selected: true,
      },
      {
        to: `${servicePart}/${this.selectedOffice}/${tomorrow.getFullYear()}/${
          tomorrow.getMonth() + 1
        }/${tomorrow.getDate()}`,
        icon: 'right',
        text: tomorrow.toLocaleDateString('en-us', { weekday: 'long' }),
      },
    ];
  },
  methods: {
    scrollToTop() {
      window.scrollTo(0, 0);
    },
    hoverClass(name) {
      return name == this.selectedOffice ? 'always' : 'hover';
    },
    selectedClass(name) {
      return name == this.selectedOffice ? 'selected' : '';
    },
    isCurrentTime(officeName) {
      // Simple time-based logic to highlight current prayer time
      const hour = new Date().getHours();
      
      switch (officeName) {
        case 'morning_prayer':
          return hour >= 6 && hour < 12;
        case 'midday_prayer':
          return hour >= 12 && hour < 15;
        case 'evening_prayer':
          return hour >= 15 && hour < 20;
        case 'compline':
          return hour >= 20 || hour < 6;
        default:
          return false;
      }
    },
    getPrayerTime(officeName) {
      // Return suggested times for each prayer
      const times = {
        morning_prayer: '6:00 AM',
        midday_prayer: '12:00 PM',
        evening_prayer: '6:00 PM',
        compline: '9:00 PM',
        early_evening_prayer: '5:00 PM',
        close_of_day_prayer: '9:00 PM'
      };
      return times[officeName] || '';
    },
    redirectToDaily() {
      if (this.selectedOffice) {
        const lookup = {
          morning_prayer: 'morning_prayer',
          midday_prayer: 'midday_prayer',
          early_evening_prayer: 'evening_prayer',
          close_of_day_prayer: 'compline',
        };
        const new_office = lookup[this.selectedOffice];
        if (new_office) {
          this.$router.push(
            `/office/${new_office}/${this.calendarDate.getFullYear()}/${
              this.calendarDate.getMonth() + 1
            }/${this.calendarDate.getDate()}`
          );
        }
      }
    },
    redirectToFamily() {
      if (this.selectedOffice) {
        const lookup = {
          morning_prayer: 'morning_prayer',
          midday_prayer: 'midday_prayer',
          evening_prayer: 'early_evening_prayer',
          compline: 'close_of_day_prayer',
        };
        const new_office = lookup[this.selectedOffice];
        if (new_office) {
          this.$router.push(
            `/family/${new_office}/${this.calendarDate.getFullYear()}/${
              this.calendarDate.getMonth() + 1
            }/${this.calendarDate.getDate()}`
          );
        }
      }
    },
    async toggleServiceType() {
      if (this.currentServiceType == 'family') {
        this.currentServiceType = 'office';
        this.links = this.dailyLinks;
        await DynamicStorage.setItem('serviceType', 'office');
        this.redirectToDaily();
      } else {
        this.currentServiceType = 'family';
        await DynamicStorage.setItem('serviceType', 'family');
        this.links = this.familyLinks;
        this.redirectToFamily();
      }
    },
  },
};
</script>

<style scoped lang="scss">
.service-type-section {
  margin: 2rem 0;
}

.service-toggle-card {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 1rem;
  position: relative;
  
  // Book-like styling
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
    
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      135deg,
      rgba(255, 255, 255, 0.02) 0%,
      transparent 50%,
      rgba(0, 0, 0, 0.01) 100%
    );
    border-radius: 10px;
    pointer-events: none;
  }
}

.service-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
  
  @media (max-width: 640px) {
    flex-direction: column;
    text-align: center;
  }
}

.current-mode {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
  color: var(--font-color);
}

.mode-icon {
  font-size: 1.125rem;
  opacity: 0.8;
}

.mode-text {
  font-family: 'Adobe Caslon Pro', serif;
  letter-spacing: 0.025em;
}

.switch-button {
  font-family: 'Adobe Caslon Pro', serif;
  font-weight: 500;
  letter-spacing: 0.025em;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  transition: all 0.2s ease;
  
  &:hover {
    background: var(--el-fill-color-light);
    transform: translateY(-1px);
  }
}

.switch-icon {
  margin-right: 0.5rem;
}

.nav-section-title {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--font-color);
  margin: 2rem 0 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  @media (max-width: 480px) {
    font-size: 1rem;
    margin: 1.5rem 0 0.75rem;
  }
}

.section-icon {
  opacity: 0.7;
  font-size: 1rem;
}

// Prayer Times Grid
.prayer-times-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
  
  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }
}

.prayer-time-card {
  position: relative;
}

.prayer-link {
  text-decoration: none;
  color: inherit;
}

.prayer-card {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all 0.3s ease;
  position: relative;
  
  // Book-like styling
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 
      0 4px 16px rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  
  &.selected {
    background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
    color: white;
    border-color: var(--el-color-primary);
    box-shadow: 
      0 4px 16px rgba(0, 0, 0, 0.15),
      0 0 0 1px var(--el-color-primary);
  }
  
  &.current-time {
    border-color: var(--el-color-warning);
    background: linear-gradient(135deg, var(--el-color-warning-light-9) 0%, var(--el-color-warning-light-8) 100%);
    
    &::after {
      content: 'Current';
      position: absolute;
      top: -8px;
      right: -8px;
      background: var(--el-color-warning);
      color: white;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.25rem 0.5rem;
      border-radius: 12px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
  }
}

.prayer-icon-container {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  
  .selected & {
    background: rgba(255, 255, 255, 0.2);
  }
}

.prayer-icon {
  font-size: 1.25rem;
  opacity: 0.8;
  
  .selected & {
    opacity: 1;
  }
}

.prayer-details {
  flex: 1;
  min-width: 0;
}

.prayer-name {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.025em;
  margin: 0 0 0.25rem;
  
  @media (max-width: 480px) {
    font-size: 0.875rem;
  }
}

.prayer-time {
  font-size: 0.875rem;
  opacity: 0.7;
  font-weight: 500;
  
  .selected & {
    opacity: 0.9;
  }
  
  @media (max-width: 480px) {
    font-size: 0.75rem;
  }
}

// Readings Section
.readings-section {
  margin-bottom: 2rem;
}

.readings-link {
  text-decoration: none;
  color: inherit;
}

.readings-card {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  padding: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s ease;
  
  // Book-like styling
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 
      0 4px 16px rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  
  &.selected {
    background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
    color: white;
    border-color: var(--el-color-primary);
  }
}

.readings-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.readings-icon {
  font-size: 1.5rem;
  opacity: 0.8;
  
  .selected & {
    opacity: 1;
  }
}

.readings-text {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: 0.025em;
  
  @media (max-width: 480px) {
    font-size: 1rem;
  }
}

.chevron-icon {
  opacity: 0.5;
  transition: transform 0.2s ease;
  
  .readings-card:hover & {
    transform: translateX(4px);
    opacity: 0.8;
  }
  
  .selected & {
    opacity: 0.9;
  }
}

// Day Navigation
.day-navigation {
  margin-bottom: 2rem;
}

.day-nav-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.day-link {
  text-decoration: none;
  color: inherit;
}

.day-card {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 10px;
  padding: 0.875rem 1rem;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  
  // Book-like styling
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.1),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  
  &.selected {
    background: linear-gradient(135deg, var(--el-color-primary) 0%, var(--el-color-primary-light-3) 100%);
    color: white;
    border-color: var(--el-color-primary);
    font-weight: 600;
  }
  
  &.today {
    border-color: var(--el-color-success);
    background: linear-gradient(135deg, var(--el-color-success-light-9) 0%, var(--el-color-success-light-8) 100%);
  }
}

.day-text {
  font-family: 'Adobe Caslon Pro', serif;
  font-weight: 600;
  letter-spacing: 0.025em;
  font-size: 0.875rem;
  
  @media (max-width: 480px) {
    font-size: 0.75rem;
  }
}

.day-icon {
  font-size: 0.875rem;
  opacity: 0.8;
  
  .selected & {
    opacity: 1;
  }
}

// Dark mode adjustments
:root.dark {
  .service-toggle-card,
  .prayer-card,
  .readings-card,
  .day-card {
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.2),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
    
    &:hover {
      box-shadow: 
        0 4px 16px rgba(0, 0, 0, 0.3),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }
  }
  
  .prayer-icon-container {
    background: rgba(255, 255, 255, 0.1);
  }
}

// Responsive adjustments
@media (max-width: 640px) {
  .prayer-times-grid {
    grid-template-columns: 1fr;
  }
  
  .day-nav-grid {
    gap: 0.5rem;
  }
  
  .prayer-card,
  .readings-card {
    padding: 1rem;
  }
  
  .day-card {
    padding: 0.75rem;
  }
}
</style>
