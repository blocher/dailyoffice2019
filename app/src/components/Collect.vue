<template>
  <el-collapse-item :title="fullTitle(collect)" :name="collect.uuid">
    <div
      class="collect-content text-[var(--el-text-color-primary)] bg-[var(--el-fill-color-blank)]"
    >
      <div
        class="text-[var(--main-font-size)] leading-[var(--main-line-height)] p-4 font-serif break-words"
      >
        <div
          v-html="traditional ? collect.traditional_text : collect.text"
        ></div>
      </div>
      <h5
        v-if="collect.attribution"
        class="mt-2 px-4 text-sm text-[var(--el-text-color-secondary)]"
      >
        {{ collect.attribution }}
      </h5>

      <el-card
        class="box-card mt-4 mx-4 mb-4 bg-[var(--el-fill-color-light)] border-[var(--el-border-color-lighter)]"
        shadow="never"
        body-style="padding: 1rem;"
      >
        <div>
          <p
            class="mb-2 font-sans font-medium text-[var(--el-text-color-regular)]"
            style="
              font-size: calc(var(--main-font-size) * 0.85) !important;
              line-height: 1.5 !important;
            "
          >
            <em>Add this prayer near the end of:</em>
          </p>
          <el-checkbox-group v-model="checkList" @change="handleCheckChange">
            <el-checkbox
              v-for="office in offices"
              :key="office"
              :label="office"
            />
          </el-checkbox-group>
        </div>
      </el-card>
    </div>
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

.collect-content {
  padding: 0;
}
</style>
