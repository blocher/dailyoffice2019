<template>
  <div class="small-container">
    <div v-if="!loading && !error">
      <h1>Psalm {{ psalm.number }}</h1>
      <h4>{{ psalm.latin_title }}</h4>
      <FontSizer/>
      <div class="flex justify-center full-width">
        <el-switch
            v-model="traditional"
            size="large"
            active-text="Traditional"
            inactive-text="Contemporary"
            class="align-center"
            @change="setTradtional"
        />
      </div>
    </div>
    <div v-if="loading || error">
      <h1>Psalm</h1>
    </div>
    <Loading v-if="loading"/>
    <el-alert
        v-if="error" :title="error"
        type="error"
    />
  </div>
  <div v-if="!loading && !error" id="main">
    <div v-if="!traditional">
        <span
            v-for="verse in psalm.verses" :key="verse.number"
        >
          <span v-if="verse.first_half">
          <p class="hangingIndent extra-space-before">
            <sup>{{ verse.number }}</sup> {{ verse.first_half }} *
          </p>
          <p class="indent">
            {{ verse.second_half }}
          </p>
            </span>
        </span>
    </div>
    <div v-if="traditional">
        <span
            v-for="verse in psalm.verses" :key="verse.number"
        >
          <span v-if="verse.first_half_tle">
          <p class="hangingIndent extra-space-before">
            <sup>{{ verse.number }}</sup> {{ verse.first_half_tle }} *
          </p>
          <p class="indent">
            {{ verse.second_half_tle }}
          </p>
            </span>
        </span>
    </div>
    <el-divider/>
    <div class="mt-3">
      <router-link
          v-if="psalm.number > 1"
          class="float-left"
          :to="`/psalm/${psalm.number - 1}`"
      >
        <font-awesome-icon :icon="['fad', 'left']"/>
        Psalm
        {{ psalm.number - 1 }}
      </router-link>

      <router-link
          v-if="psalm.number < 150"
          class="float-right"
          :to="`/psalm/${psalm.number + 1}`"
      >
        Psalm {{ psalm.number + 1 }}
        <font-awesome-icon :icon="['fad', 'right']"/>
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
import FontSizer from "@/components/FontSizer";
import {DynamicStorage} from "@/helpers/storage";
import {getURL} from "@/utils/request";

export default {
  components: {Loading, FontSizer},
  data() {
    return {
      psalm: null,
      loading: true,
      error: false,
      traditional: false,
    };
  },
  async created() {
    const traditional = await DynamicStorage.getItem("traditionalPsalms", false);
    if (traditional == "true" || traditional == true) {
      this.traditional = true;
    } else {
      this.traditional = false;
    }
    this.setTradtional();
    let data = null;
    try {
      data = await getURL(
          `${process.env.VUE_APP_API_URL}api/v1/psalms/${this.$route.params.number}/`
      );
    } catch (e) {
      this.error =
          "There was an error retrieving the psalms. Please try again.";
      this.loading = false;
      return;
    }
    this.psalm = data;
    this.error = false;
    this.loading = false;
  },
  methods: {
    async setTradtional() {
      await DynamicStorage.setItem("traditionalPsalms", this.traditional);
    }
  }
};
</script>
