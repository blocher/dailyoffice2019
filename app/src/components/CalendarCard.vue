<template>
  <el-card
      class="box-card" :class="cardColor"
  >
    <template #header>
      <div class="card-header">
        <h1 v-if="officeName">
          {{ officeName }}
        </h1>
        <h3>{{ formattedDate }}</h3>
        <div
            class="card-info" :v-if="card"
        >
          <h4 v-if="card && office != 'evening_prayer' && office != 'compline'">
            {{ card.primary_feast }}
          </h4>
          <h4
              v-if="card && (office == 'evening_prayer' || office == 'compline')"
          >
            {{ card.primary_evening_feast }}
          </h4>
          <h5
              v-if="card && card.fast && card.fast.fast_day"
              class="text-center"
          >
            Fast Day
          </h5>
        </div>
      </div>
    </template>
    <div
        v-if="
        card &&
        card.commemorations &&
        office != 'evening_prayer' &&
        office != 'compline'
      "
    >
      <div
          v-for="commemoration in card.commemorations"
          :key="commemoration.name"
      >
        <Commemoration :commemoration="commemoration"/>
      </div>
    </div>
    <div
        v-if="
        card &&
        card.commemorations &&
        (office == 'evening_prayer' || office == 'compline')
      "
    >
      <div
          v-for="commemoration in card.evening_commemorations"
          :key="commemoration.name"
      >
        <Commemoration :commemoration="commemoration"/>
      </div>
    </div>
    <div
        v-if="card && card.season" class="width:10"
    >
      <div
          class="card-footer mt-2" :class="card.season.colors[0]"
      >
        <h4>{{ card.season.name }}</h4>
      </div>
    </div>
  </el-card>
</template>

<script>
// @ is an alias to /src

import Commemoration from "@/components/Commemoration";

export default {
  name: "CalenderCard",
  components: {Commemoration},
  props: ["card", "calendarDate", "office", "serviceType"],
  data() {
    return {
      officeName: null,
      formattedDate: null,
      currentServiceType: this.serviceType,
    };
  },
  computed: {
    cardColor: function () {
      if (this.office != 'evening_prayer' && this.office != 'compline') {
        return this.card.primary_color
      } else {
        return this.card.primary_evening_color
      }
    }
  },
  async created() {
    if (!this.currentServiceType) {
      this.currentServiceType = "office";
    }
    const options = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    };
    this.formattedDate = this.$props.calendarDate.toLocaleDateString(
        "en-US",
        options
    );
    const daily_offices = {
      morning_prayer: "Daily Morning Prayer",
      midday_prayer: "Daily Midday Prayer",
      evening_prayer: "Daily Evening Prayer",
      compline: "Compline",
    };
    const family_offices = {
      morning_prayer: "Family Prayer in the Morning",
      midday_prayer: "Family Prayer at Midday",
      early_evening_prayer: "Family Prayer in the Early Evening",
      close_of_day_prayer: "Family Prayer at the Close of Day",
    };
    const offices =
        this.currentServiceType == "office" ? daily_offices : family_offices;
    if (offices[this.$props.office] !== undefined) {
      this.officeName = offices[this.$props.office];
    }
  },
};
</script>

<style lang="scss">
.card-footer {
  border-radius: var(--el-card-border-radius);
  border: 1px solid var(--el-card-border-color);
  background-color: var(--el-card-bg-color);
  overflow: hidden;
  color: var(--el-text-color-primary);
  transition: var(--el-transition-duration);
  padding: 1em;
  width: 100%;

  h4 {
    margin-bottom: 0;
  }
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
</style>
