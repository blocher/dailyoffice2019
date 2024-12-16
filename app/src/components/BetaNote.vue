<template>
  <div
    v-if="displayBetaNote"
    class="full-width flex justify-center items-center"
  >
    <el-alert
      class="max-w-lg"
      title="Beta Version"
      description="You are viewing the beta version of the Daily Office site, which lets you preview features before they are launched. Please submit any suggestions or bug reports to feedback@dailyoffice2019.com."
      type="warning"
      effect="dark"
      @close="dismissNote"
    />
  </div>
</template>

<script>
// @ is an alias to /src

// @ is an alias to /src
import { DynamicStorage } from '@/helpers/storage';

export default {
  name: 'BetaNote',
  components: {},
  data() {
    return {
      displayBetaNote: true,
    };
  },
  async created() {
    if ((await DynamicStorage.getItem('betaNoteDismissed')) === 'true') {
      this.displayBetaNote = false;
    } else {
      this.displayBetaNote = true;
    }
  },
  methods: {
    dismissNote: async function () {
      await DynamicStorage.setItem('betaNoteDismissed', 'true');
    },
  },
};
</script>

<style lang="scss"></style>
