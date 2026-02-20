<template>
  <div
    class="font-size-block my-4 p-4 bg-gray-50 dark:bg-gray-700/50 border border-gray-100 dark:border-gray-600 rounded-lg shadow-inner max-w-md mx-auto"
  >
    <div class="flex items-center justify-between gap-4">
      <div class="text-gray-400 dark:text-gray-500">
        <font-awesome-icon :icon="['fad', 'font-case']" size="sm" />
      </div>
      <div class="grow">
        <el-slider
          v-model="fontSize"
          :min="sliderMin"
          :max="sliderMax"
          :format-tooltip="displayFontSize"
          @input="setFontSize"
          size="small"
        />
      </div>
      <div class="text-gray-600 dark:text-gray-300">
        <font-awesome-icon :icon="['fad', 'font-case']" size="lg" />
      </div>
    </div>
  </div>
</template>

<script>
import { DynamicStorage } from '@/helpers/storage';

export default {
  name: 'FontSizer',
  components: {},
  props: {},
  data() {
    return {
      fontSize: 24,
      sliderMin: 10,
      sliderMax: 40,
    };
  },
  async mounted() {
    await this.resetFontSize();
  },
  methods: {
    async resetFontSize() {
      await this.$nextTick();
      this.fontSize = parseInt(
        (await DynamicStorage.getItem('fontSize')) || 24
      );
      await this.setFontSize(this.fontSize);
    },
    async setFontSize(value) {
      const main = document.getElementById('main');
      if (main) {
        main.style['font-size'] = `${value}px`;
        document
          .querySelectorAll(
            '#main h2, #main h3, #main p, .el-collapse-item__header, .el-collapse-item p'
          )
          .forEach((p) => {
            p.style['font-size'] = `${value}px`;
            p.style['line-height'] = `${value * 1.6}px`;
          });
      }
      await DynamicStorage.setItem('fontSize', this.fontSize);
      await DynamicStorage.getItem('fontSize');
    },
    fontSizeToPercent(value) {
      if (this.sliderMax === this.sliderMin) {
        return 0;
      }
      const normalized = Math.min(
        this.sliderMax,
        Math.max(this.sliderMin, value)
      );
      return Math.round(
        ((normalized - this.sliderMin) / (this.sliderMax - this.sliderMin)) *
          100
      );
    },
    displayFontSize(value) {
      return `${this.fontSizeToPercent(value)}%`;
    },
  },
};
</script>
