<template>
  <el-card class="box-card" :class="card.primary_color">
    <template #header>
      <div class="card-header">
        <h1>{{ officeName }}</h1>
        <h3>{{ formattedDate }}</h3>
        <h4>{{ card.primary_feast }}</h4>
      </div>
    </template>
    <div
      v-for="commemoration in card.commemorations"
      :key="commemoration.name"
      class="text item"
    >
      <p>
        <strong>{{ commemoration.name }}</strong>
      </p>
      <p>
        <small>
          <span
            class="box"
            v-for="color in commemoration.colors"
            :key="color"
            :class="color"
          ></span>
          <strong>&nbsp;&nbsp;|&nbsp;&nbsp;Rank: </strong
          >{{ commemoration.rank.formatted_name }}
          <a
            v-for="link in commemoration.links"
            :key="link"
            :href="link"
            target="_blank"
            class="float-right link"
            >Biography</a
          >
        </small>
      </p>
    </div>
    <!--    <div class="card-header">-->
    <!--      <h1>{{ officeName }}</h1>-->
    <!--      <h3>{{ formattedDate }}</h3>-->
    <!--      <h4>{{ card.primary_feast }}</h4>-->
    <!--    </div>-->
  </el-card>
</template>

<style lang="scss">
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

.box.red {
  background-color: #c21c13;
  color: white;
}

.box.green {
  background-color: #077339;
  color: white;
}

.box.white {
  background-color: white;
  color: black;
}

.box.purple {
  background-color: #64147d;
  color: white;
}

.box.black {
  background-color: black;
  color: white;
}

.box.rose {
  background-color: pink;
  color: black;
}
</style>

<script>
// @ is an alias to /src

export default {
  data() {
    return {
      officeName: "The Daily Office",
    };
  },
  async created() {
    const offices = {
      morning_prayer: "Daily Morning Prayer",
      midday_prayer: "Daily Midday Prayer",
      evening_prayer: "Daily Evening Prayer",
      compline: "Compline",
    };
    if (offices[this.$props.office] !== undefined) {
      this.officeName = offices[this.$props.office];
    }
  },
  name: "CalenderCard",
  components: {},
  props: ["card", "formattedDate", "office"],
};
</script>
