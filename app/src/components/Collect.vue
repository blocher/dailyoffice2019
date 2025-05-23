<template>
  <el-collapse-item :title="fullTitle(collect)" :name="collect.uuid">
    <span v-if="traditional" v-html="collect.traditional_text" />
    <span v-if="!traditional" v-html="collect.text" />
    <h5>{{ collect.attribution }}</h5>
    <el-card
      class="box-card"
      shadow="never"
      style="margin: 0 0 15px"
      body-style="padding:10px;"
    >
      <p>
        <em>Add this prayer near the end of:</em>
        <el-checkbox-group v-model="checkList" @change="handleCheckChange">
          <el-checkbox
            v-for="office in offices"
            :key="office"
            :label="office"
          />
        </el-checkbox-group>
      </p>
    </el-card>
  </el-collapse-item>
</template>

<script>
import { DynamicStorage } from '@/helpers/storage';
import { ElMessage } from 'element-plus';
import { getMessageOffset } from '@/helpers/getMessageOffest';

export default {
  name: 'Collect',
  props: ['collect', 'traditional', 'extraCollects'],
  emits: ['extraCollectsChanged'],
  data() {
    return {
      checkList: [],
      offices: [
        'Morning Prayer',
        'Midday Prayer',
        'Evening Prayer',
        'Compline',
      ],
    };
  },
  async created() {
    this.offices.forEach((office) => {
      if (
        Object.prototype.hasOwnProperty.call(this.extraCollects, office) &&
        this.extraCollects[office].includes(this.collect.uuid)
      ) {
        this.checkList.push(office);
      }
    });
  },
  methods: {
    async handleCheckChange() {
      const defaultDict = {};
      this.offices.forEach((office) => {
        defaultDict[office] = [];
      });
      const extraCollects =
        JSON.parse(await DynamicStorage.getItem('extraCollects')) ||
        defaultDict;
      this.offices.forEach((office) => {
        if (
          this.checkList.includes(office) &&
          !extraCollects[office].includes(this.collect.uuid)
        ) {
          extraCollects[office].push(this.collect.uuid);
        } else if (
          !this.checkList.includes(office) &&
          extraCollects[office].includes(this.collect.uuid)
        ) {
          extraCollects[office].splice(
            extraCollects[office].indexOf(this.collect.uuid),
            1
          );
        }
      });
      await DynamicStorage.setItem(
        'extraCollects',
        JSON.stringify(extraCollects)
      );
      this.$emit('extraCollectsChanged');
      ElMessage.success({
        title: 'Saved',
        message: '<small>Your prayer settings have been updated.</small>',
        showClose: true,
        dangerouslyUseHTMLString: true,
        offset: getMessageOffset(),
      });
    },
    fullTitle(collect) {
      if (collect.number) {
        return `${collect.number}. ${collect.title}`;
      } else {
        return collect.title;
      }
    },
  },
};
</script>

<style lang="scss">
.el-collapse-item__header.is-active {
  font-weight: 800 !important;
}
</style>
