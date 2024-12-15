<template>
  <div class="small-container">
    <h1>Psalms</h1>
    <h4>{{ selectedTopicName }}</h4>
    <Loading v-if="loading" />
    <el-alert v-if="error" :title="error" type="error" />
    <div v-if="!loading && !error">
      <div class="text-center">
        <el-select
          v-model="selectedTopic"
          class="w-full mb-8"
          placeholder="Select"
          size="large"
          filterable
          @change="updateDisplayedTopic"
        >
          <el-option key="all" label="All Categories" value="all" />
          <el-option
            v-for="topic in topics"
            :key="topic.id"
            :label="topic.topic_name"
            :value="topic.id"
          />
        </el-select>
        <div class="flex justify-center full-width">
          <el-switch
            v-model="traditional"
            size="large"
            active-text="Traditional"
            inactive-text="Contemporary"
            class="align-center"
            @change="setTraditional"
          />
        </div>
      </div>
      <div v-for="psalm in displayedPsalms" :key="psalm.number" class="mb-2">
        <p>
          <router-link :to="`/psalm/${psalm.number}`">
            <strong>{{ psalm.number }}</strong
            >&nbsp;
            <small>{{ psalm.latin_title }}</small>
          </router-link>
          <br />
          <small v-if="!traditional">{{
            psalm.verses[0].first_half.replaceAll(/[^a-zA-Z]+$/gi, "")
          }}</small>
          <small v-if="traditional">{{
            psalm.verses[0].first_half_tle.replaceAll(/[^a-zA-Z]+$/gi, "")
          }}</small>
          <br />
          <el-tag
            v-for="topic in psalm.topics"
            :key="topic.id"
            class="mr-2 cursor-pointer"
            type="info"
            size="small"
            @click="handleTagClick(topic.id)"
          >
            {{ topic.topic_name }}
          </el-tag>
        </p>
      </div>
    </div>
  </div>
</template>

<script>
import Loading from "@/components/Loading.vue";
import { DynamicStorage } from "@/helpers/storage";

export default {
  components: { Loading },
  data() {
    return {
      psalms: null,
      loading: true,
      error: false,
      topics: null,
      displayedPsalms: null,
      selectedTopic: "all",
      selectedTopicName: "All Categories",
      traditional: false,
    };
  },
  async created() {
    const traditional = await DynamicStorage.getItem(
      "traditionalPsalms",
      false,
    );
    if (traditional == "true" || traditional == true) {
      this.traditional = true;
    } else {
      this.traditional = false;
    }
    this.setTraditional();
    let data = null;
    try {
      data = await this.$http.get(
        `${import.meta.env.VUE_APP_API_URL}api/v1/psalms`,
      );
    } catch (e) {
      this.error =
        "There was an error retrieving the psalms. Please try again.";
      this.loading = false;
      return;
    }
    this.psalms = data.data;
    this.displayedPsalms = this.psalms;

    try {
      data = await this.$http.get(
        `${import.meta.env.VUE_APP_API_URL}api/v1/psalms/topics`,
      );
    } catch (e) {
      this.error =
        "There was an error retrieving the psalms. Please try again.";
      this.loading = false;
      return;
    }
    this.topics = data.data;
    this.error = false;
    this.loading = false;
  },
  methods: {
    handleTagClick(topic_id) {
      this.selectedTopic = topic_id;
      this.updateDisplayedTopic();
    },
    updateDisplayedTopic() {
      if (this.selectedTopic === "all") {
        this.selectedTopicName = "All Categories";
        this.displayedPsalms = this.psalms;
      } else {
        this.displayedPsalms = this.psalms.filter(
          (psalm) =>
            psalm.topics.map((topic) => topic.id).indexOf(this.selectedTopic) >
            -1,
        );
        this.selectedTopicName = this.topics.find(
          (topic) => topic.id === this.selectedTopic,
        ).topic_name;
      }
    },
    async setTraditional() {
      await DynamicStorage.setItem("traditionalPsalms", this.traditional);
    },
  },
};
</script>
