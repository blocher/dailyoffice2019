<template>
  <div class="text text-sm sm:text-md">
    <div class="w-full mt-2">
      <p>
        <strong
          ><span class="box" :class="commemoration.colors[0]" /> &nbsp;<span
            v-html="commemoration.name"
          ></span
        ></strong>
        <a
          v-if="commemoration.ai_one_sentence"
          :href="link"
          class="link bio_link float-right"
        >
          &nbsp;<el-button type="success">Read More</el-button> &nbsp;<el-tag
            type="warning"
            >New!
          </el-tag>
        </a>
      </p>
      <p v-if="commemoration.ai_one_sentence">
        {{ commemoration.ai_one_sentence }}
      </p>
    </div>
    <!--    <div class="w-full mb-2">-->
    <!--      <em>{{ commemoration.rank.formatted_name }}</em>-->
    <!--    </div>-->
  </div>
</template>

<script>
// @ is an alias to /src

export default {
  props: ['commemoration'],
  computed: {
    link: function () {
      return `/commemorations/${this.commemoration.uuid}`;
    },
  },
};
</script>
<style>
.bio_link {
  margin-right: 0.5em;
}
</style>
