<template>
  <div class="theme-switcher-wrapper w-full text-right mt-2 pr-6">
    <ShareSettings />
    <EmailSignup />
    <ThemeSwitcher />
  </div>
</template>

<style>
.sub-menu-item {
  margin-left: 35px;
}
</style>

<script>

import EmailSignup from "@/components/EmailSignup";
import ShareSettings from "@/components/ShareSettings";
import ThemeSwitcher from "@/components/ThemeSwitcher";

export default {
  components: {
    EmailSignup,
    ShareSettings,
    ThemeSwitcher,
  },
};
</script>
