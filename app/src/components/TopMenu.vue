<template>
  <el-menu
    :default-active="activeIndex"
    mode="horizontal"
    menu-trigger="click"
    :router="menuRouter"
    :unique-opened="uniqueOpened"
    class="fixed top-0 left-0 right-0 account-for-notch"
  >
    <el-sub-menu index="1">
      <template #title>Pray</template>

      <el-menu-item index="/"> Current Day and Time</el-menu-item>
      <el-menu-item index="/readings"> Today's Readings</el-menu-item>

      <el-menu-item-group title="— Daily Office —">
        <el-menu-item index="/office/evening_prayer/yesterday">
          Evening Prayer (Yesterday)
        </el-menu-item>

        <el-menu-item index="/office/compline/yesterday">
          Compline (Yesterday)
        </el-menu-item>

        <el-menu-item index="/office/morning_prayer">
          Morning Prayer
        </el-menu-item>

        <el-menu-item index="/office/midday_prayer">
          Midday Prayer
        </el-menu-item>

        <el-menu-item index="/office/evening_prayer">
          Evening Prayer
        </el-menu-item>

        <el-menu-item index="/office/compline"> Compline</el-menu-item>

        <el-menu-item index="/office/morning_prayer/tomorrow">
          Morning Prayer (Tomorrow)
        </el-menu-item>
      </el-menu-item-group>
      <el-menu-item-group title="— Family Prayer —">
        <el-menu-item index="/family/early_evening_prayer/yesterday">
          Early Evening (Yesterday)
        </el-menu-item>

        <el-menu-item index="/family/close_of_day_prayer/yesterday">
          Close of Day (Yesterday)
        </el-menu-item>

        <el-menu-item index="/family/morning_prayer"> Morning</el-menu-item>

        <el-menu-item index="/family/midday_prayer"> Midday</el-menu-item>

        <el-menu-item index="/family/early_evening_prayer">
          Early Evening
        </el-menu-item>

        <el-menu-item index="/family/close_of_day_prayer">
          Close of Day
        </el-menu-item>

        <el-menu-item index="/family/morning_prayer/tomorrow">
          Morning (Tomorrow)
        </el-menu-item>
      </el-menu-item-group>
    </el-sub-menu>

    <el-menu-item index="/settings"> Settings</el-menu-item>

    <el-sub-menu index="3">
      <template #title> Resources</template>
      <el-menu-item index="/calendar"> Calendar </el-menu-item>
      <el-menu-item index="/about"> About</el-menu-item>
      <el-menu-item index="/collects"> Collects</el-menu-item>
      <el-menu-item index="/psalms"> Psalms</el-menu-item>
      <el-menu-item index="/litany"> Great Litany</el-menu-item>
    </el-sub-menu>
  </el-menu>

  <el-header>
    <Submenu />
  </el-header>
</template>

<script>
import Submenu from '@/components/Submenu.vue';

export default {
  components: {
    Submenu,
  },
  data() {
    return {
      activeIndex: '1',
      menuRouter: true,
      uniqueOpened: false,
    };
  },
};
</script>

<style scoped="true" lang="scss">
.el-menu {
  margin-top: env(safe-area-inset-top);
  color: var(--font-color);
  background-color: var(--color-bg);
}

.account-for-notch {
  margin-top: env(safe-area-inset-top);
}

.el-menu-item-group__title {
  padding-left: 10px !important;
  font-size: 1.2em;
}
</style>
