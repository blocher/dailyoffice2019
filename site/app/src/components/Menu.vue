<template>
  <el-affix>
    <el-menu
      :default-active="activeIndex"
      class="el-menu-demo"
      mode="horizontal"
    >
      <el-sub-menu index="1">
        <template #title index="1">
          <router-link to="/">Pray</router-link>
        </template>

        <router-link :key="$route.fullPath" to="/calendar">
          <el-menu-item index="1-1">Calendar</el-menu-item>
        </router-link>
        <el-menu-item-group title="— Daily Office —">
          <router-link :key="$route.fullPath" to="/evening_prayer/yesterday">
            <el-menu-item index="1-2">
              Evening Prayer (Yesterday)
            </el-menu-item>
          </router-link>
          <router-link :key="$route.fullPath" to="/compline/yesterday">
            <el-menu-item index="1-3"> Compline (Yesterday)</el-menu-item>
          </router-link>
          <router-link :key="$route.fullPath" to="/morning_prayer">
            <el-menu-item index="1-4"> Morning Prayer</el-menu-item>
          </router-link>
          <router-link :key="$route.fullPath" to="/midday_prayer">
            <el-menu-item index="1-5"> Midday Prayer</el-menu-item>
          </router-link>
          <router-link :key="$route.fullPath" to="/evening_prayer">
            <el-menu-item index="1-6"> Evening Prayer</el-menu-item>
          </router-link>
          <router-link :key="$route.fullPath" to="/compline">
            <el-menu-item index="1-7"> Compline</el-menu-item>
          </router-link>
          <router-link :key="$route.fullPath" to="/morning_prayer/tomorrow">
            <el-menu-item index="1-8"> Morning Prayer (Tomorrow)</el-menu-item>
          </router-link>
        </el-menu-item-group>
        <el-menu-item-group title="— Family Prayer —">
          <el-menu-item index="1-9"
            >At the Close of Day (Yesterday)
          </el-menu-item>
          <el-menu-item index="1-10">
            <router-link to="/">In the Morning</router-link>
          </el-menu-item>
          <el-menu-item index="1-11">
            <router-link to="/">At Midday</router-link>
          </el-menu-item>
          <el-menu-item index="1-12">
            <router-link to="/">In the Early Evening</router-link>
          </el-menu-item>
          <el-menu-item index="1-13">
            <router-link to="/">At the Close of Day</router-link>
          </el-menu-item>
          <el-menu-item index="1-14">
            <router-link to="/">In the Morning (Tomorrow)</router-link>
          </el-menu-item>
        </el-menu-item-group>
      </el-sub-menu>
      <router-link to="/settings">
        <el-menu-item index="2"> Settings</el-menu-item>
      </router-link>
      <router-link to="/about">
        <el-menu-item index="3"> Resources</el-menu-item>
      </router-link>
    </el-menu>
  </el-affix>
</template>

<style>
.el-menu-item-group__title {
  padding-left: 10px !important;
  font-size: 1.2em;
}
</style>

<script>
export default {
  data() {
    return {
      activeIndex: "1",
    };
  },
};
</script>
