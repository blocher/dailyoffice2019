<template>
  <div class="text item text-sm sm:text-md">
    <p>
      <strong>{{ commemoration.name }}</strong>
    </p>
    <p>
      <small>
        <span
          class="box"
          v-for="color in commemoration.colors"
          :key="color"
          :class="color"
        ></span>
        <strong>&nbsp;&nbsp;|&nbsp;&nbsp;Rank: </strong>
        {{ commemoration.rank.formatted_name }}
        <a
          v-for="link in commemoration.links"
          :key="link"
          :href="link"
          target="_blank"
          class="float-right link"
          >Biography</a
        >
      </small>
    </p>
  </div>
</template>
<script>
// @ is an alias to /src

export default {
  props: ["commemoration"],
};
</script>
