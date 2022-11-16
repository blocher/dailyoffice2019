<template>
  <div class="font-size-block my-2">
    <div class="w-1/6 inline-block">
      <font-awesome-icon
          :icon="['fad', 'font-case']" size="sm"
      />
    </div>
    <div class="w-2/3 inline-block">
      <el-slider
          v-model="fontSize"
          class="w-3/4"
          :min="sliderMin"
          :max="sliderMax"
          :format-tooltip="displayFontSize"
          @input="setFontSize"
      />
    </div>
    <div class="w-1/6 inline-block text-right">
      <font-awesome-icon
          :icon="['fad', 'font-case']" size="lg"
      />
    </div>
  </div>
</template>

<script>
export default {
  name: "FontSizer",
  components: {},
  props: {},
  data() {
    return {
      fontSize: 20,
      sliderMin: 10,
      sliderMax: 40,
    };
  },
  mounted() {
    this.resetFontSize()
  },
  methods: {
    resetFontSize() {
      if (localStorage.fontSize) {
        this.fontSize = parseInt(localStorage.fontSize);
      } else {
        localStorage.fontSize = this.fontSize;
      }
      this.setFontSize(this.fontSize)
    },
    setFontSize(value) {
      const main = document.getElementById("main")
      if (main) {
        main.style["font-size"] = `${value}px`;
        document.querySelectorAll("h2,h3, main p, .el-collapse-item__header, .el-collapse-item p").forEach((p) => {
          p.style["font-size"] = `${value}px`;
          p.style["line-height"] = `${value * 1.6}px`;
        });
      }
      localStorage.fontSize = this.fontSize;
    },
    displayFontSize(value) {
      return `${value}px`;
    },
  },
};
</script>
