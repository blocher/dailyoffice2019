<template>
  <el-row class="mt-4">
    <el-col :span="12">
      <ThemeSwitcher />
    </el-col>
    <el-col :span="12" class="text-right">
      <ShareSettings />
      <br />
      <EmailSignup />
      <br />
      <SubmitFeedback />
    </el-col>
  </el-row>
  <!--        <span class="sub-menu-item">-->
  <!--          <span>-->
  <!--            <a-->
  <!--              href="https://www.facebook.com/groups/dailyoffice"-->
  <!--              target="_blank:"-->
  <!--            >-->
  <!--              <font-awesome-icon :icon="['fab', 'facebook']" />-->
  <!--            </a>-->
  <!--          </span>-->
  <!--        </span>-->
</template>

<script>
import EmailSignup from '@/components/EmailSignup.vue';
import ShareSettings from '@/components/ShareSettings.vue';
import ThemeSwitcher from '@/components/ThemeSwitcher.vue';
import SubmitFeedback from '@/components/SubmitFeedback.vue';

export default {
  components: {
    EmailSignup,
    ShareSettings,
    ThemeSwitcher,
    SubmitFeedback,
  },
};
</script>
