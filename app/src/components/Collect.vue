<template>
  <h3><span v-if="collect.number">{{ collect.number }}. </span>{{ collect.title }}</h3>
  <div class="text-center py-2">
    <el-tag v-for="tag in collect.tags" :key="tag.uuid" class="ml-2" type="info">{{ tag.name }}</el-tag>
  </div>
  <el-card class="box-card" shadow="never" style="margin:0 0 15px;" body-style="padding:10px;">
    <p><em>Pray during:</em>
      <el-checkbox-group v-model="checkList" v-on:change="handleCheckChange">
        <el-checkbox v-for="office in this.offices" :key="office" :label="office"/>
      </el-checkbox-group>
    </p>
  </el-card>
  <span v-if="traditional" v-html="collect.traditional_text"/>
  <span v-if="!traditional" v-html="collect.text"/>
  <h5>{{ collect.attribution }}</h5>
</template>

<script>
export default {
  name: "Collect",
  props: ["collect", "traditional"],
  methods: {
    handleCheckChange() {
      const extraCollects = JSON.parse(localStorage.getItem('extraCollects')) || this.defaultDict;
      console.log(extraCollects)
      this.offices.forEach((office) => {
        if (this.checkList.includes(office) && !(extraCollects[office].includes(this.collect.uuid))) {
          extraCollects[office].push(this.collect.uuid)
        } else if (!this.checkList.includes(office) && extraCollects[office].includes(this.collect.uuid)) {
          extraCollects[office].splice(extraCollects[office].indexOf(this.collect.uuid), 1);
        }
      });
      localStorage.setItem('extraCollects', JSON.stringify(extraCollects));
    },
  },
  async created() {
    this.defaultDict = {}
    this.offices.forEach((office) => {
      this.defaultDict[office] = []
    })
    const extraCollects = JSON.parse(localStorage.getItem('extraCollects')) || this.defaultDict;
    this.offices.forEach((office) => {
      if (extraCollects[office].includes(this.collect.uuid)) {
        this.checkList.push(office)
      }
    });
  },
  data() {
    return {
      checkList: [],
      offices: ["Morning Prayer", "Midday Prayer", "Evening Prayer", "Compline"],
    };
  },
};
</script>
