<template>
  <h4>{{ subcategory.name }}
    <span class="float-right">
    <el-button size="small" :disabled="disableShowAll" @click="expandAll()">Show All</el-button>
    <el-button size="small" class="upside-down" :disabled="disableHideAll" @click="collapseAll()">Hide All</el-button>
      </span>
  </h4>
  <el-collapse v-model="openedItems">
    <div v-for="collect in subcategory.collects" :key="collect.uuid">
      <Collect :key="collect.uuid" :collect="collect" :traditional="traditional"/>
    </div>
  </el-collapse>
</template>

<script>

import Collect from "@/components/Collect";


export default {
  components: {Collect},
  props: {
    subcategory: {
      type: Object,
      required: true,
    },
    traditional: {
      type: Boolean,
      required: false,
    },
  },
  data() {
    return {
      openedItems: [],
    };
  },
  computed: {
    disableShowAll() {
      return this.openedItems.length === this.subcategory.collects.length;
    },
    disableHideAll() {
      return this.openedItems.length === 0;
    },
  },

  async mounted() {
  },
  methods: {
    collapseAll() {
      this.openedItems = [];
    },
    expandAll() {
      this.openedItems = this.subcategory.collects.map((collect) => {
        return collect.uuid;
      });
    },
    showOnlySelected(checkList) {
      this.openedItems = checkList;
    },
  },
};
</script>

<style scoped lang="scss">
body h4 {
  text-align: left;
  margin: 2em 0;
}

.upside-down span {
  transform: scale(-1, 1);
}
</style>
