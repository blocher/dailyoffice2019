<template>
  <el-collapse-item :title="fullTitle(collect)" :name="collect.uuid">
    <div class="collect-versions md:flex gap-8">
      <div
        v-for="version in activeVersions"
        :key="version.key"
        class="collect-version flex-1"
      >
        <h5 v-if="activeVersions.length > 1" class="mb-2 text-gray-500">
          {{ version.label }}
        </h5>
        <span v-html="version.content" />
        <h5 v-if="version.attribution">{{ version.attribution }}</h5>
      </div>
    </div>
    <!-- Fallback if no versions active (shouldn't happen but safe) -->
    <div v-if="activeVersions.length === 0">
      <span v-html="collect.text" />
      <h5>{{ collect.attribution }}</h5>
    </div>

    <el-card
      class="box-card"
      shadow="never"
      style="margin: 15px 0"
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
  props: {
    collect: {
      type: Object,
      required: true,
    },
    traditional: {
      type: Boolean,
      default: false,
    },
    selectedVersions: {
      type: Array,
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
      checkList: [],
      offices: [
        'Morning Prayer',
        'Midday Prayer',
        'Evening Prayer',
        'Compline',
      ],
    };
  },
  computed: {
    activeVersions() {
      const versions = [];
      const sv = this.selectedVersions;

      // Compatibility: if selectedVersions is empty, fallback to traditional prop
      if (!sv || sv.length === 0) {
        if (this.traditional) {
          if (this.collect.traditional_text) {
            versions.push({
              key: 'traditional',
              label: 'Traditional',
              content: this.collect.traditional_text,
              attribution: this.collect.attribution,
            });
          }
        } else {
          if (this.collect.text) {
            versions.push({
              key: 'contemporary',
              label: 'Contemporary',
              content: this.collect.text,
              attribution: this.collect.attribution,
            });
          }
        }
        return versions;
      }

      if (sv.includes('contemporary') && this.collect.text) {
        versions.push({
          key: 'contemporary',
          label: 'Contemporary',
          content: this.collect.text,
          attribution: this.collect.attribution,
        });
      }
      if (sv.includes('traditional') && this.collect.traditional_text) {
        versions.push({
          key: 'traditional',
          label: 'Traditional',
          content: this.collect.traditional_text,
          attribution: this.collect.attribution,
        });
      }
      if (sv.includes('spanish') && this.collect.spanish_text) {
        versions.push({
          key: 'spanish',
          label: 'Spanish',
          content: this.collect.spanish_text,
          attribution:
            this.collect.spanish_attribution || this.collect.attribution,
        });
      }
      return versions;
    },
  },
  async created() {
    this.offices.forEach((office) => {
      if (
        this.extraCollects &&
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
      const sv = this.selectedVersions;
      let title = collect.title;

      const hasEnglish =
        sv && (sv.includes('contemporary') || sv.includes('traditional'));
      const hasSpanish = sv && sv.includes('spanish');

      if (hasEnglish && hasSpanish && collect.spanish_title) {
        title = `${collect.title} / ${collect.spanish_title}`;
      } else if (!hasEnglish && hasSpanish && collect.spanish_title) {
        title = collect.spanish_title;
      }

      if (collect.number) {
        return `${collect.number}. ${title}`;
      } else {
        return title;
      }
    },
  },
};
</script>

<style lang="scss">
.el-collapse-item__header.is-active {
  font-weight: 800 !important;
}
.collect-version h5 {
  margin-top: 0;
  margin-bottom: 0.5rem;
}
</style>
