<template>
  <el-row
      v-if="currentServiceType == 'office'"
      :gutter="5"
      class="mt-6 text-xs mx-auto"
  >
    <el-col
        :span="12" class="text-left"> Full Daily Office
    </el-col>
    <el-col
        :span="12" class="text-right"
    >
      <a
          href=""
          @click.stop.prevent="toggleServiceType"
      >Switch to Family Prayer</a>
    </el-col>
  </el-row>
  <el-row
      v-else :gutter="5"
      class="mt-6 text-xs mx-auto"
  >
    <el-col
        :span="12" class="text-left"
    >
      <a
          href="" @click.stop.prevent="toggleServiceType"
      >Switch to Full Daily Office</a
      >
    </el-col>
    <el-col
        :span="12" class="text-right"> Family Prayer
    </el-col>
  </el-row>
  <el-row
      :gutter="5" class="mt-2 text-center text-xs sm:text-sm mx-auto"
  >
    <el-col
        v-for="link in links" :key="link.name"
        :span="6"
    >
      <div class="grid-content bg-purple">
        <router-link :to="link.to">
          <el-card
              :class="selectedClass(link.name)"
              :shadow="hoverClass(link.name)"
          >
            <p class="text-xs sm:text-sm">
              <font-awesome-icon :icon="link.icon"/>
            </p>
            <p
                class="text-xs sm:text-sm" v-html="link.text"/>
          </el-card>
        </router-link>
      </div>
    </el-col>
  </el-row>
  <el-row
      :gutter="5" class="mt-2 text-center"
  >
    <el-col
        v-for="link in dayLinks" :key="link.text"
        :span="8"
    >
      <div class="grid-content bg-purple">
        <router-link
            :to="link.to" :v-on:click="scrollToTop"
        >
          <el-card
              :class="link.selected ? 'selected' : ''"
              shadow="hover"
              class="text-xs sm:text-sm"
          >
            <font-awesome-icon
                v-if="link.icon == 'left'"
                :icon="['fad', 'left']"
            />
            {{ link.text }}
            <font-awesome-icon
                v-if="link.icon == 'right'"
                :icon="['fad', 'right']"
            />
          </el-card>
        </router-link>
      </div>
    </el-col>
  </el-row>
</template>

<style scoped>
.selected {
  background-color: rgb(229, 231, 235);
  border-color: rgb(44, 62, 80);
  color: var(--font-on-white-background);
}

.el-card {
  --el-card-padding: 10px;
  height: 100%;
}

.el-card__body {
  padding: 5px !important;
}
</style>

<script>
// @ is an alias to /src

export default {
  name: "OfficeNav",
  components: {},
  props: {
    calendarDate: {
      type: Date,
    },
    selectedOffice: {
      type: String,
    },
    serviceType: {
      default: "office",
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
        text: "Morning<br>Prayer",
        name: "morning_prayer",
        icon: ["fad", "sunrise"],
      },
      {
        to: `/midday_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: "Midday<br>Prayer",
        name: "midday_prayer",
        icon: ["fad", "sun"],
      },
      {
        to: `/evening_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: "Evening<br>Prayer",
        name: "evening_prayer",
        icon: ["fad", "sunset"],
      },
      {
        to: `/compline/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: "Compline<br>(Bedtime)",
        name: "compline",
        icon: ["fad", "moon-stars"],
      },
    ];
    this.familyLinks = [
      {
        to: `/family/morning_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: "Morning",
        name: "morning_prayer",
        icon: ["fad", "sunrise"],
      },
      {
        to: `/family/midday_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: "Midday",
        name: "midday_prayer",
        icon: ["fad", "sun"],
      },
      {
        to: `/family/early_evening_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: "Early Evening",
        name: "early_evening_prayer",
        icon: ["fad", "sunset"],
      },
      {
        to: `/family/close_of_day_prayer/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: "Close of Day",
        name: "close_of_day_prayer",
        icon: ["fad", "moon-stars"],
      },
    ];
    if (this.currentServiceType == "family") {
      this.links = this.familyLinks;
    } else {
      this.links = this.dailyLinks;
    }
    this.dayLinks = [
      {
        to: `/day/${yesterday.getFullYear()}/${
            yesterday.getMonth() + 1
        }/${yesterday.getDate()}`,
        icon: "left",
        text: yesterday.toLocaleDateString("en-us", {weekday: "long"}),
      },
      {
        to: `/day/${this.calendarDate.getFullYear()}/${
            this.calendarDate.getMonth() + 1
        }/${this.calendarDate.getDate()}`,
        text: this.calendarDate.toLocaleDateString("en-us", {
          weekday: "long",
        }),
        selected: true,
      },
      {
        to: `/day/${tomorrow.getFullYear()}/${
            tomorrow.getMonth() + 1
        }/${tomorrow.getDate()}`,
        icon: "right",
        text: tomorrow.toLocaleDateString("en-us", {weekday: "long"}),
      },
    ];
  },
  methods: {
    scrollToTop() {
      window.scrollTo(0, 0);
    },
    hoverClass(name) {
      return name == this.selectedOffice ? "always" : "hover";
    },
    selectedClass(name) {
      return name == this.selectedOffice ? "selected" : "";
    },
    redirectToDaily() {
      if (this.selectedOffice) {
        const lookup = {
          morning_prayer: "morning_prayer",
          midday_prayer: "midday_prayer",
          early_evening_prayer: "evening_prayer",
          close_of_day_prayer: "compline",
        };
        const new_office = lookup[this.selectedOffice];
        this.$router.push(
            `/office/${new_office}/${this.calendarDate.getFullYear()}/${
                this.calendarDate.getMonth() + 1
            }/${this.calendarDate.getDate()}`
        );
      }
    },
    redirectToFamily() {
      if (this.selectedOffice) {
        const lookup = {
          morning_prayer: "morning_prayer",
          midday_prayer: "midday_prayer",
          evening_prayer: "early_evening_prayer",
          compline: "close_of_day_prayer",
        };
        const new_office = lookup[this.selectedOffice];
        this.$router.push(
            `/family/${new_office}/${this.calendarDate.getFullYear()}/${
                this.calendarDate.getMonth() + 1
            }/${this.calendarDate.getDate()}`
        );
      }
    },
    toggleServiceType() {
      if (this.currentServiceType == "family") {
        this.currentServiceType = "office";
        this.links = this.dailyLinks;
        localStorage.setItem("serviceType", "office");
        this.redirectToDaily();
      } else {
        this.currentServiceType = "family";
        localStorage.setItem("serviceType", "family");
        this.links = this.familyLinks;
        this.redirectToFamily();
      }
    },
  },
};
</script>
