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
          class="bio_link float-right"
        >
          &nbsp;<el-button type="success">
            <font-awesome-icon :icon="['fad', 'books']" />
            &nbsp; Learn More&nbsp;&nbsp;<small><em>New!!</em></small>
          </el-button>
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
  margin: 1em;
}

.bio_link:hover,
.bio_link:focus,
.bio_link:active {
  text-decoration: none !important;
  text-decoration-line: none !important;
  text-decoration-thickness: 0;
}
</style>
