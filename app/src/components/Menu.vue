<template>
  <el-affix>
    <el-menu
      :default-active="activeIndex"
      mode="horizontal"
      menu-trigger="click"
      :router="menuRouter"
    >
      <el-sub-menu index="1">
        <template #title>
          <router-link to="/">Pray</router-link>
        </template>

        <el-menu-item index="/calendar">Calendar</el-menu-item>

        <el-menu-item-group title="— Daily Office —">
          <el-menu-item index="/evening_prayer/yesterday">
            Evening Prayer (Yesterday)
          </el-menu-item>

          <el-menu-item index="/compline/yesterday">
            Compline (Yesterday)
          </el-menu-item>

          <el-menu-item index="/morning_prayer"> Morning Prayer</el-menu-item>

          <el-menu-item index="/midday_prayer"> Midday Prayer</el-menu-item>

          <el-menu-item index="/evening_prayer"> Evening Prayer</el-menu-item>

          <el-menu-item index="/compline"> Compline</el-menu-item>

          <el-menu-item index="/morning_prayer/tomorrow">
            Morning Prayer (Tomorrow)
          </el-menu-item>
        </el-menu-item-group>
        <!--        <el-menu-item-group title="— Family Prayer —">-->
        <!--          <el-menu-item index="1-9"-->
        <!--            >At the Close of Day (Yesterday)-->
        <!--          </el-menu-item>-->
        <!--          <el-menu-item index="1-10">-->
        <!--            <router-link to="/">In the Morning</router-link>-->
        <!--          </el-menu-item>-->
        <!--          <el-menu-item index="1-11">-->
        <!--            <router-link to="/">At Midday</router-link>-->
        <!--          </el-menu-item>-->
        <!--          <el-menu-item index="1-12">-->
        <!--            <router-link to="/">In the Early Evening</router-link>-->
        <!--          </el-menu-item>-->
        <!--          <el-menu-item index="1-13">-->
        <!--            <router-link to="/">At the Close of Day</router-link>-->
        <!--          </el-menu-item>-->
        <!--          <el-menu-item index="1-14">-->
        <!--            <router-link to="/">In the Morning (Tomorrow)</router-link>-->
        <!--          </el-menu-item>-->
        <!--        </el-menu-item-group>-->
      </el-sub-menu>

      <el-menu-item index="/settings"> Settings</el-menu-item>

      <el-menu-item index="/about"> Resources</el-menu-item>
    </el-menu>
  </el-affix>
  <el-header>
    <Submenu />
  </el-header>
</template>

<style>
.el-menu {
  color: var(--font-color);
  background-color: var(--color-bg);
}

.el-menu-item-group__title {
  padding-left: 10px !important;
  font-size: 1.2em;
}
</style>

<script>
import Submenu from "@/components/Submenu";

export default {
  components: {
    Submenu,
  },
  data() {
    return {
      activeIndex: "1",
      menuRouter: true,
    };
  },
};
</script>
