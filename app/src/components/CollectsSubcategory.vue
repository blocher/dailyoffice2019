<template>
  <h4
    class="text-xl font-semibold text-[var(--el-text-color-primary)] mt-8 mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 sm:gap-2"
  >
    <span>{{ subcategory.name }}</span>
    <span class="flex gap-2">
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
    traditional: {
      type: Boolean,
      required: false,
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
}

.upside-down span {
  transform: scale(-1, 1);
}

.el-collapse-item__header {
  margin-top: 1.5rem !important;
}

.el-collapse {
  --el-collapse-header-height: auto !important;
  border-top: none;
  border-bottom: none;
}
</style>

<style lang="scss">
.el-collapse-item__header {
  padding: 0.75rem 1rem !important;
  border-radius: 0.5rem;
  transition: background-color 0.2s;
  background-color: var(--el-fill-color-blank);
  font-size: 1rem !important;
  line-height: 1.5 !important;
  font-weight: 600 !important;
  color: var(--el-text-color-primary) !important;
}

.el-collapse-item__header:hover {
  background-color: var(--el-fill-color-light);
}

.el-collapse-item {
  margin: 0 0 0.5rem !important;
  border: 1px solid var(--el-border-color-light);
  border-radius: 0.5rem;
  background-color: var(--el-fill-color-blank);
  overflow: hidden;
}

.el-collapse-item__wrap {
  border-bottom: none;
  background-color: var(--el-fill-color-blank);
}
</style>
