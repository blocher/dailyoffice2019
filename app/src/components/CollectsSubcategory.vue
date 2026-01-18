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
  <el-collapse v-model="openedItems" class="collects-collapse">
    <div
      v-for="collect in subcategory.collects"
      :key="collect.uuid"
      class="mb-2"
    >
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
  margin-top: 0.5rem !important; /* Reduced from 1.5rem to be more balanced with new padding */
  padding-bottom: 0.5rem;
  font-size: 1.1rem;
}

.el-collapse {
  --el-collapse-header-height: auto !important;
  border: none; /* Remove default border to rely on item separation */
}
</style>
