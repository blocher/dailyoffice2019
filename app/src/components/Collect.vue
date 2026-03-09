<template>
  <el-collapse-item :title="fullTitle(collect)" :name="collect.uuid">
    <div
      class="collect-content text-(--el-text-color-primary) bg-(--el-fill-color-blank)"
    >
      <div class="collect-panels" :class="collectPanelsClasses">
        <section
          v-for="panel in languagePanels"
          :key="panel.key"
          class="collect-panel"
          :class="{ 'collect-panel--placeholder': !panel.text }"
        >
          <div v-if="showLanguageLabels" class="collect-panel__label">
            {{ panel.label }}
          </div>
          <div
            :class="{
              'collect-panel__body--placeholder': !panel.text,
            }"
            class="collect-panel__body text-(--main-font-size) leading-(--main-line-height) font-serif wrap-break-word"
            v-html="panel.text || panel.placeholder"
          ></div>
          <h5 v-if="panel.attribution" class="collect-panel__attribution">
            {{ panel.attribution }}
          </h5>
          <p v-if="panel.note" class="collect-panel__note">
            {{ panel.note }}
          </p>
        </section>
      </div>

      <el-card
        class="box-card mt-4 mx-4 mb-4 bg-(--el-fill-color-light) border-(--el-border-color-lighter)"
        shadow="never"
        body-style="padding: 1rem;"
      >
        <div>
          <p
            class="mb-2 font-sans font-medium text-(--el-text-color-regular)"
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

const LANGUAGE_VARIANTS = {
  contemporary: {
    label: 'Contemporary',
    textKey: 'text',
    attributionKey: 'attribution',
  },
  traditional: {
    label: 'Traditional',
    textKey: 'traditional_text',
    attributionKey: 'attribution',
  },
  spanish: {
    label: 'Spanish',
    textKey: 'spanish_text',
    attributionKey: 'spanish_attribution',
  },
};

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
    selectedLanguages: {
      type: Array,
      default: null,
    },
    extraCollects: {
      type: Object,
      default: () => ({}),
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
    normalizedSelectedLanguages() {
      if (
        Array.isArray(this.selectedLanguages) &&
        this.selectedLanguages.length
      ) {
        return this.selectedLanguages;
      }
      return [this.traditional ? 'traditional' : 'contemporary'];
    },
    languagePanels() {
      return this.normalizedSelectedLanguages
        .map((languageKey) => {
          const config = LANGUAGE_VARIANTS[languageKey];
          if (!config) {
            return null;
          }

          const text = this.collect?.[config.textKey];
          return {
            key: languageKey,
            label: config.label,
            text,
            placeholder:
              '<p>This collect is not yet available in this version.</p>',
            attribution: text
              ? this.collect?.[config.attributionKey] ||
                this.collect?.attribution
              : null,
            note: text ? null : `${config.label} text coming soon.`,
          };
        })
        .filter(Boolean);
    },
    showLanguageLabels() {
      return this.normalizedSelectedLanguages.length > 1;
    },
    collectPanelsClasses() {
      return {
        'collect-panels--single': !this.showLanguageLabels,
        'collect-panels--double': this.normalizedSelectedLanguages.length === 2,
        'collect-panels--triple': this.normalizedSelectedLanguages.length >= 3,
      };
    },
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

.collect-panels {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(17rem, 1fr));
  gap: 1rem;
  padding: 1rem;
}

.collect-panels--single {
  grid-template-columns: 1fr;
  gap: 0;
}

.collect-panels--double {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.collect-panels--triple {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.collect-panel {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 0.75rem;
  background: var(--el-fill-color-blank);
  overflow: hidden;
}

.collect-panels--single .collect-panel {
  border: none;
  border-radius: 0;
}

.collect-panel--placeholder {
  border-style: dashed;
  color: var(--el-text-color-secondary);
  background: var(--el-fill-color-light);
}

.collect-panel__label {
  display: inline-flex;
  align-items: center;
  margin: 1rem 1rem 0;
  padding: 0.18rem 0.6rem;
  border-radius: 999px;
  background: var(--el-fill-color-light);
  color: var(--el-text-color-regular);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.collect-panel__body {
  padding: 1rem;
}

.collect-panel__body--placeholder {
  font-family: var(--el-font-family);
  font-size: 0.96rem;
  line-height: 1.6;
}

.collect-panel__attribution {
  margin: 0;
  padding: 0 1rem 1rem;
  font-size: 0.875rem;
  color: var(--el-text-color-secondary);
}

.collect-panel__note {
  margin: 0;
  padding: 0 1rem 1rem;
  color: var(--el-text-color-secondary);
  font-size: 0.83rem;
  line-height: 1.4;
}

@media (max-width: 1024px) {
  .collect-panels--triple {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .collect-panels {
    grid-template-columns: 1fr;
    padding: 0.75rem;
    gap: 0.75rem;
  }
}
</style>
