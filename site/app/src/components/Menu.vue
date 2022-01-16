<template>
  <el-affix>
    <el-menu
      :default-active="activeIndex"
      class="el-menu-demo"
      mode="horizontal"
      @select="handleSelect"
    >
      <el-sub-menu>
        <template #title index="1">
          <router-link to="/">Pray</router-link>
        </template>
        <el-menu-item index="1-1">item one</el-menu-item>
        <el-menu-item index="1-2">item two</el-menu-item>
        <el-menu-item index="1-3">item three</el-menu-item>
      </el-sub-menu>
      <el-menu-item index="2">
        <router-link to="/settings">Settings</router-link>
      </el-menu-item>
      <el-menu-item index="3">
        <router-link to="/about">About</router-link>
      </el-menu-item>
      <el-menu-item index="3">
        <router-link to="/about">Resources</router-link>
      </el-menu-item>
    </el-menu>
  </el-affix>
</template>

<!--<script setup>-->
<!--import {ref} from "vue";-->

<!--const activeIndex = ref("1");-->
<!--const handleSelect = (key, keyPath) => {-->
<!--  console.log(key, keyPath);-->
<!--};-->
<!--</script>-->

<script>
export default {
  data() {
    return {
      activeIndex: "1",
    };
  },
  methods: {
    handleSelect(key, keyPath) {
      console.log(key, keyPath);
    },
  },
};
</script>
