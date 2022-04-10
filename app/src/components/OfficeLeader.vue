<template>
  <p v-if="!line.extra_space_before">
    {{ line.content }}
  </p>
  <p
v-if="line.extra_space_before" class="extra-space-before"
>
    {{ line.content }}
  </p>
</template>

<style>
.extra-space-before {
  margin-top: 0.7em;
}
</style>

<script>
// @ is an alias to /src

export default {
  name: "Office Leader",
  components: {},
  props: ["line"],
};
</script>
