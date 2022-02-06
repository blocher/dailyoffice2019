<template>
  <el-row :gutter="5" class="mt-2 text-center text-xs sm:text-sm mx-auto">
    <el-col v-for="link in links" v-bind:key="link.name" :span="6">
      <div class="grid-content bg-purple">
        <router-link :to="link.to">
          <el-card
            v-bind:class="selectedClass(link.name)"
            :shadow="hoverClass(link.name)"
          >
            <p class="text-xs sm:text-sm">
              <font-awesome-icon :icon="link.icon" />
            </p>
            <p v-html="link.text" class="text-xs sm:text-sm"></p>
          </el-card>
        </router-link>
      </div>
    </el-col>
  </el-row>
  <el-row :gutter="5" class="mt-2 text-center">
    <el-col v-for="link in dayLinks" v-bind:key="link.text" :span="8">
      <div class="grid-content bg-purple">
        <router-link :to="link.to" :v-on:click="scrollToTop">
          <el-card
            v-bind:class="link.selected ? 'selected' : ''"
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
  data() {
    return {
      links: null,
      dayLink: null,
    };
  },
  async created() {
    const tomorrow = new Date(this.calendarDate);
    tomorrow.setDate(this.calendarDate.getDate() + 1);
    const yesterday = new Date(this.calendarDate);
    yesterday.setDate(this.calendarDate.getDate() - 1);
    this.links = [
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
    this.dayLinks = [
      {
        to: `/day/${yesterday.getFullYear()}/${
          yesterday.getMonth() + 1
        }/${yesterday.getDate()}`,
        icon: "left",
        text: yesterday.toLocaleDateString("en-us", { weekday: "long" }),
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
        text: tomorrow.toLocaleDateString("en-us", { weekday: "long" }),
      },
    ];
  },
  name: "OfficeNav",
  components: {},
  props: ["calendarDate", "selectedOffice"],
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
  },
};
</script>
