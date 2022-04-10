<template>
  <div class="small-container">
    <div v-if="!loading && !error">
      <div class="about">
        <h1>Psalm {{ psalm.number }}</h1>
        <h4>{{ psalm.latin_title }}</h4>
      </div>
    </div>
    <div v-if="loading || error">
      <h1>Psalm</h1>
    </div>
    <Loading v-if="loading" />
    <el-alert
v-if="error" :title="error"
type="error"
/>
    <div v-if="!loading && !error">
      <span
v-for="verse in psalm.verses" :key="verse.number"
>
        <p class="-indent-3 pl-2">
          <sup class="position-relative -left-4">{{
            verse.number.toString().padStart(3, "&nbsp;")
          }}</sup
          >{{ verse.first_half }} *
        </p>
        <p class="-indent-2.5 pl-2 ml-3">{{ verse.second_half }}</p>
      </span>
    </div>
    <el-divider />
    <div class="mt-3">
      <router-link
        v-if="psalm.number > 1"
        class="float-left"
        :to="`/psalm/${psalm.number - 1}`"
      >
        <font-awesome-icon :icon="['fad', 'left']" />
        Psalm
        {{ psalm.number - 1 }}
      </router-link>

      <router-link
        v-if="psalm.number < 150"
        class="float-right"
        :to="`/psalm/${psalm.number + 1}`"
      >
        Psalm {{ psalm.number + 1 }}
        <font-awesome-icon :icon="['fad', 'right']" />
      </router-link>
      <br>
      <router-link
        v-if="psalm.number < 150"
        class="float-none content-center w-full"
        :to="`/psalms/`"
      >
        All Psalms
      </router-link>
    </div>
  </div>
</template>

<script>
import Loading from "@/components/Loading";

export default {
  components: { Loading },
  data() {
    return {
      psalm: null,
      loading: true,
      error: false,
    };
  },
  async created() {
    let data = null;
    try {
      data = await this.$http.get(
        `${process.env.VUE_APP_API_URL}api/v1/psalms/${this.$route.params.number}/`
      );
    } catch (e) {
      this.error =
        "There was an error retrieving the psalms. Please try again.";
      this.loading = false;
      return;
    }
    this.psalm = data.data;
    this.error = false;
    this.loading = false;
  },
};
</script>
