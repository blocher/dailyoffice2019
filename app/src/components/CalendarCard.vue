<template>
  <div class="enhanced-calendar-card" :class="{ hideBody: hideBody }">
    <div class="calendar-header" :class="cardColor">
      <!-- Office Type Banner -->
      <div class="office-banner">
        <h1 v-if="officeName" class="office-title">
          {{ officeName }}
        </h1>
        <div class="office-meta">
          <h2 class="calendar-date">{{ formattedDate }}</h2>
          <div v-if="card && card.fast && card.fast.fast_day" class="fast-day-indicator">
            <font-awesome-icon :icon="['fas', 'cross']" class="fast-icon" />
            <span>Fast Day</span>
          </div>
        </div>
      </div>

      <!-- Feast Information -->
      <div class="feast-section" v-if="card">
        <div class="primary-feast">
          <h3
            v-if="office != 'evening_prayer' && office != 'compline'"
            class="feast-heading"
            v-html="card.primary_feast"
          ></h3>
          <h3
            v-if="office == 'evening_prayer' || office == 'compline'"
            class="feast-heading"
            v-html="card.primary_evening_feast"
          ></h3>
        </div>

        <!-- Learn More Button -->
        <div
          v-if="
            card &&
            office != 'evening_prayer' &&
            office != 'compline' &&
            card.commemorations[0].links.length > 0
          "
          class="feast-actions"
        >
          <el-button 
            type="primary" 
            size="small" 
            round
            class="learn-more-btn"
          >
            <font-awesome-icon :icon="['fas', 'book-open']" class="btn-icon" />
            Learn More
            <span class="new-badge">New!</span>
          </el-button>
        </div>
        <div
          v-if="
            card &&
            (office == 'evening_prayer' || office == 'compline') &&
            card.evening_commemorations[0].links.length > 0
          "
          class="feast-actions"
        >
          <el-button 
            type="primary" 
            size="small" 
            round
            class="learn-more-btn"
          >
            <font-awesome-icon :icon="['fas', 'book-open']" class="btn-icon" />
            Learn More
            <span class="new-badge">New!</span>
          </el-button>
        </div>
      </div>
    </div>

    <!-- Commemorations Body -->
    <div class="commemorations-body" v-if="card">
      <div
        v-if="
          card.commemorations.length > 1 &&
          office != 'evening_prayer' &&
          office != 'compline'
        "
        class="commemorations-list"
      >
        <div
          v-for="commemoration in card.commemorations"
          :key="commemoration.name"
        >
          <Commemoration :commemoration="commemoration" />
        </div>
      </div>
      <div
        v-if="
          card.evening_commemorations.length > 1 &&
          (office == 'evening_prayer' || office == 'compline')
        "
        class="commemorations-list"
      >
        <div
          v-for="commemoration in card.evening_commemorations"
          :key="commemoration.name"
        >
          <Commemoration :commemoration="commemoration" />
        </div>
      </div>
    </div>
  </div>
</template>
      <!--      >-->
      <!--        <h4>{{ card.season.name }}</h4>-->
      <!--      </div>-->
      <!--    </div>-->
    </el-card>
  </div>
</template>

<script>
// @ is an alias to /src

// @ is an alias to /src
// @ is an alias to /src
// @ is an alias to /src
// @ is an alias to /src
// @ is an alias to /src
// @ is an alias to /src
import Commemoration from '@/components/Commemoration.vue';

export default {
  name: 'CalenderCard',
  components: { Commemoration },
  props: ['card', 'calendarDate', 'office', 'serviceType'],
  data() {
    return {
      officeName: null,
      formattedDate: null,
      currentServiceType: this.serviceType,
    };
  },
  computed: {
    cardColor: function () {
      if (!this.card) return true;
      if (this.office !== 'evening_prayer' && this.office !== 'compline') {
        return this.card.primary_color;
      } else {
        return this.card.primary_evening_color;
      }
    },
    hideBody: function () {
      if (!this.card) return true;
      if (this.office === 'evening_prayer' || this.office === 'compline') {
        return this.card.evening_commemorations.length < 2;
      } else {
        return this.card.commemorations.length < 2;
      }
    },
  },
  async created() {
    if (!this.currentServiceType) {
      this.currentServiceType = 'office';
    }

    const options = {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    };
    this.formattedDate = this.$props.calendarDate.toLocaleDateString(
      'en-US',
      options
    );
    const daily_offices = {
      morning_prayer: 'Daily Morning Prayer',
      midday_prayer: 'Daily Midday Prayer',
      evening_prayer: 'Daily Evening Prayer',
      compline: 'Compline',
    };
    const family_offices = {
      morning_prayer: 'Family Prayer in the Morning',
      midday_prayer: 'Family Prayer at Midday',
      early_evening_prayer: 'Family Prayer in the Early Evening',
      close_of_day_prayer: 'Family Prayer at the Close of Day',
    };
    const readings = {
      readings: 'Readings',
    };
    const offices =
      this.currentServiceType == 'readings'
        ? readings
        : this.currentServiceType == 'office'
          ? daily_offices
          : family_offices;
    if (offices[this.$props.office] !== undefined) {
      this.officeName = offices[this.$props.office];
    }
  },
};
</script>

<style lang="scss" scoped>
.enhanced-calendar-card {
  margin-bottom: 2rem;
  
  &.hideBody .commemorations-body {
    display: none;
  }
}

.calendar-header {
  background: linear-gradient(
    135deg,
    var(--color-bg) 0%,
    var(--el-fill-color-lighter) 100%
  );
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 12px;
  padding: 2rem;
  text-align: center;
  position: relative;
  margin-bottom: 1rem;
  
  // Book-like paper texture
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      45deg,
      transparent 0%,
      rgba(255, 255, 255, 0.02) 25%,
      transparent 50%,
      rgba(0, 0, 0, 0.01) 100%
    );
    border-radius: 12px;
    pointer-events: none;
  }
}

.office-banner {
  margin-bottom: 1.5rem;
}

.office-title {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 2rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--font-color);
  margin: 0 0 1rem;
  line-height: 1.2;
  
  @media (max-width: 768px) {
    font-size: 1.75rem;
  }
  
  @media (max-width: 480px) {
    font-size: 1.5rem;
  }
}

.office-meta {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  
  @media (min-width: 640px) {
    flex-direction: row;
    justify-content: center;
    gap: 2rem;
  }
}

.calendar-date {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1.25rem;
  font-weight: 500;
  letter-spacing: 0.025em;
  color: var(--el-text-color-regular);
  margin: 0;
  
  @media (max-width: 480px) {
    font-size: 1.125rem;
  }
}

.fast-day-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--el-color-warning);
  background: var(--el-color-warning-light-9);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  border: 1px solid var(--el-color-warning-light-7);
}

.fast-icon {
  font-size: 0.75rem;
}

.feast-section {
  position: relative;
}

.primary-feast {
  margin-bottom: 1rem;
}

.feast-heading {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 0.025em;
  color: var(--font-color);
  margin: 0;
  line-height: 1.3;
  
  @media (max-width: 768px) {
    font-size: 1.25rem;
  }
  
  @media (max-width: 480px) {
    font-size: 1.125rem;
  }
}

.feast-actions {
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.learn-more-btn {
  font-family: 'Adobe Caslon Pro', serif;
  font-weight: 600;
  letter-spacing: 0.025em;
  position: relative;
  
  .btn-icon {
    margin-right: 0.5rem;
  }
  
  .new-badge {
    font-size: 0.75rem;
    font-weight: 700;
    background: var(--el-color-success);
    color: white;
    padding: 0.125rem 0.375rem;
    border-radius: 10px;
    margin-left: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }
}

.commemorations-body {
  padding: 0 1rem;
}

.commemorations-list {
  background: var(--color-bg);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
  
  // Subtle book-like styling
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

// Seasonal color support
.calendar-header {
  &.advent {
    background: linear-gradient(135deg, #4a5d7a 0%, #6b7fa8 100%);
    color: white;
    
    .office-title,
    .calendar-date,
    .feast-heading {
      color: white;
    }
  }
  
  &.christmas {
    background: linear-gradient(135deg, #b8860b 0%, #daa520 100%);
    color: white;
    
    .office-title,
    .calendar-date,
    .feast-heading {
      color: white;
    }
  }
  
  &.epiphany {
    background: linear-gradient(135deg, #228b22 0%, #32cd32 100%);
    color: white;
    
    .office-title,
    .calendar-date,
    .feast-heading {
      color: white;
    }
  }
  
  &.lent {
    background: linear-gradient(135deg, #8b0000 0%, #a52a2a 100%);
    color: white;
    
    .office-title,
    .calendar-date,
    .feast-heading {
      color: white;
    }
  }
  
  &.easter {
    background: linear-gradient(135deg, #ffd700 0%, #ffffe0 100%);
    color: #333;
    
    .office-title,
    .calendar-date,
    .feast-heading {
      color: #333;
    }
  }
  
  &.pentecost {
    background: linear-gradient(135deg, #dc143c 0%, #ff6347 100%);
    color: white;
    
    .office-title,
    .calendar-date,
    .feast-heading {
      color: white;
    }
  }
}

// Dark mode adjustments
:root.dark {
  .calendar-header {
    background: linear-gradient(
      135deg,
      var(--color-bg) 0%,
      rgba(255, 255, 255, 0.03) 100%
    );
    
    &::before {
      background: linear-gradient(
        45deg,
        transparent 0%,
        rgba(255, 255, 255, 0.01) 25%,
        transparent 50%,
        rgba(0, 0, 0, 0.02) 100%
      );
    }
  }
  
  .commemorations-list {
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }
}

// Mobile optimizations
@media (max-width: 640px) {
  .calendar-header {
    padding: 1.5rem 1rem;
  }
  
  .office-banner {
    margin-bottom: 1rem;
  }
  
  .commemorations-body {
    padding: 0 0.5rem;
  }
}
</style>

<style lang="scss">
// Global styles that need to cascade
.primary-feast-heading {
  margin-bottom: 0;
}

h1,
h2,
h3 {
  margin: 0;
  padding-top: 0;
  padding-bottom: 0;
}

h1 {
  margin: 2rem 0 3rem;
}

h3 {
  margin-bottom: 20px;
}

h4 {
  margin-bottom: 0;
}

.card-footer {
  border-radius: var(--el-card-border-radius);
  border: 1px solid var(--el-card-border-color);
  background-color: var(--el-card-bg-color);
  overflow: hidden;
  color: var(--el-text-color-primary);
  transition: var(--el-transition-duration);
  padding: 1em;
  width: 100%;
}

a:link.link {
  color: blue;
}

a:visited.link {
  color: purple;
}

a:focus.link,
a:hover.link {
  border-bottom: 1px solid;
}

a:active.link {
  color: red;
}

.box {
  width: 0.8em;
  height: 0.8em;
  border: 1px solid rgba(0, 0, 0, 0.2);
  display: inline-block;
}

.red {
  .el-card__header {
    background-color: #c21c13;
    color: white;
  }
}

.green {
  .el-card__header {
    background-color: #077339;
    color: white;
  }
}

.white {
  .el-card__header {
    background-color: white;
    color: black;
  }
}

.purple {
  .el-card__header {
    background-color: #64147d;
    color: white;
  }
}

.black {
  .el-card__header {
    background-color: black;
    color: white;
  }
}

.rose {
  .el-card__header {
    background-color: pink;
    color: black;
  }
}

.box,
.card-footer {
  &.red {
    background-color: #c21c13;
    color: white;
  }

  &.green {
    background-color: #077339;
    color: white;
  }

  &.white {
    background-color: white;
    color: black;
  }

  &.purple {
    background-color: #64147d;
    color: white;
  }

  &.black {
    background-color: black;
    color: white;
  }

  &.rose {
    background-color: pink;
    color: black;
  }
}

.hideBody .el-card__body {
  display: none;
}
</style>
