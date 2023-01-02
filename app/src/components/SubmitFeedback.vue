<template>
    <span class="sub-menu-item">
      <a
          href="" @click.prevent="showFeedbackPanel()"
      >
        <font-awesome-icon :icon="['fad', 'message-pen']"/><br/>
        <span class="ml-1 text-xs">Submit Feedback&nbsp;</span>

      </a>
    </span>
  <!--  <el-dropdown-item @click.prevent="feedbackPanel = true">Submit Feedback</el-dropdown-item>-->
  <el-drawer
      v-model="feedbackPanel" :size="panelSize"
      direction="rtl"
  >
    <div class="mt-4">
      <h3 class="text-left">Email Us</h3>
      <p class="text-left">
        Have feedback or want a new feature? Email us at <a target="_blank" href="mailto:feedback@dailyoffice2019.com">feedback@dailyoffice2019.com</a>
      </p>

      <h3 class="text-left">Join the Facebook Group</h3>
      <p class="text-left">
        Join us for discussion in our <a tareget="_blank" href="https://www.facebook.com/groups/dailyoffice/">Facebook
        Group</a> for a lively discussion.
      </p>
    </div>
  </el-drawer>
</template>


<script>

export default {
  data() {
    return {
      emailField: null,
      feedbackPanel: false,
      windowWidth: window.innerWidth,
      success: false,
      error: null,
      loading: false,
      panelSize: "37%",
    };
  },
  created: function () {
    window.addEventListener("resize", this.setPanelSize);
    this.setPanelSize()
  },
  unmounted() {
    window.removeEventListener("resize", this.setPanelSize);
  },
  methods: {
    setPanelSize() {
      if (window.innerWidth < 1024) {
        this.panelSize = "90%";
      } else {
        this.panelSize = "37%";
      }
    },
    showFeedbackPanel() {
      this.feedbackPanel = true
    }
  },
};
</script>
