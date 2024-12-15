<template>
  <div class="small-container">
    <el-row justify="center" class="text-center mx-auto">
      <el-col :span="6">
        <ClassicSite />
      </el-col>
      <el-col :span="6">
        <ShareSettings ref="shareSettings" />
      </el-col>
      <el-col :span="6">
        <EmailSignup ref="emailSignup" />
      </el-col>
      <el-col :span="6">
        <SubmitFeedback ref="submitFeedback" />
      </el-col>
    </el-row>
  </div>
</template>

<script>
import ShareSettings from '@/components/ShareSettings.vue';
import EmailSignup from '@/components/EmailSignup.vue';
import SubmitFeedback from '@/components/SubmitFeedback.vue';
import ClassicSite from '@/components/ClassicSite.vue';

export default {
  components: {
    ShareSettings,
    EmailSignup,
    SubmitFeedback,
    ClassicSite,
  },
  data() {
    return {};
  },
};
</script>
