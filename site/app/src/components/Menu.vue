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
        <el-menu-item index="1-1">
          <router-link to="/">Full Calendar</router-link>
        </el-menu-item>
        <el-menu-item-group title="— Daily Office —">
          <el-menu-item index="1-2">
            <router-link :key="$route.fullPath" to="/evening_prayer/yesterday"
              >Evening Prayer (Yesterday)
            </router-link>
          </el-menu-item>
          <el-menu-item index="1-3">
            <router-link :key="$route.fullPath" to="/compline/yesterday"
              >Compline (Yesterday)
            </router-link>
          </el-menu-item>
          <el-menu-item index="1-4">
            <router-link :key="$route.fullPath" to="/morning_prayer"
              >Morning Prayer
            </router-link>
          </el-menu-item>
          <el-menu-item index="1-5">
            <router-link :key="$route.fullPath" to="/noonday_prayer"
              >Noonday Prayer
            </router-link>
          </el-menu-item>
          <el-menu-item index="1-6">
            <router-link :key="$route.fullPath" to="/evening_prayer"
              >Evening Prayer
            </router-link>
          </el-menu-item>
          <el-menu-item index="1-7">
            <router-link :key="$route.fullPath" to="/compline"
              >Compline
            </router-link>
          </el-menu-item>
          <el-menu-item index="1-8">
            <router-link :key="$route.fullPath" to="/morning_prayer/tomorrow"
              >Morning Prayer (Tomorrow)
            </router-link>
          </el-menu-item>
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
      <el-menu-item index="2">
        <router-link to="/settings">Settings</router-link>
      </el-menu-item>
      <el-menu-item index="3">
        <router-link to="/about">Resources</router-link>
      </el-menu-item>
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
