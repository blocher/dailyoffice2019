<template>
  <h4 class="subheading" :class="{ 'psalm-section': line.psalm_section }">
    {{ line.content }}
  </h4>
</template>

<script>
// @ is an alias to /src

export default {
  name: 'Office SubHeading',
  components: {},
  props: ['line'],
};
</script>
