<template>
  <h4>
    {{ subcategory.name }}
    <span class="float-right">
      <el-button size="small" :disabled="disableShowAll" @click="expandAll()"
        >Show All</el-button
      >
      <el-button
        size="small"
        class="upside-down"
        :disabled="disableHideAll"
        @click="collapseAll()"
        >Hide All</el-button
      >
    </span>
  </h4>
  <el-collapse v-model="openedItems">
    <div v-for="collect in subcategory.collects" :key="collect.uuid">
      <Collect
        :key="collect.uuid"
        :collect="collect"
        :selected-versions="selectedVersions"
        :traditional="traditional"
        :extra-collects="extraCollects"
        @extra-collects-changed="extraCollectsChanged"
      />
    </div>
  </el-collapse>
</template>

<script>
import Collect from '@/components/Collect.vue';

export default {
  components: { Collect },
  props: {
    subcategory: {
      type: Object,
      required: true,
    },
    // Deprecated but kept for compatibility if needed (though we updated parent)
    traditional: {
      type: Boolean,
      required: false,
      default: false,
    },
    selectedVersions: {
      type: Array,
      required: false,
      default: () => [],
    },
    extraCollects: {
      type: Object,
      required: false,
    },
  },
  emits: ['extraCollectsChanged'],
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
  methods: {
    extraCollectsChanged() {
      this.$emit('extraCollectsChanged');
    },
    async collapseAll() {
      this.openedItems = [];
      await this.$nextTick();
    },
    async expandAll() {
      this.openedItems = this.subcategory.collects.map((collect) => {
        return collect.uuid;
      });
      await this.$nextTick();
    },
    async showOnlySelected(checkList) {
      this.openedItems = checkList;
      await this.$nextTick();
    },
  },
};
</script>

<style scoped lang="scss">
body h4 {
  text-align: left;
  margin: 2em 0;
}

.el-collapse-item__header {
  margin-top: 1.5rem !important;
}

.el-collapse {
  --el-collapse-header-height: auto !important;
}
</style>
