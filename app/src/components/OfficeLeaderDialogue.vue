<template>
  <div class="row">
    <div class="column left">
      <p>
        <em><small>Officiant</small></em>
      </p>
    </div>
    <div class="column right">
      <p>{{ line.content }}</p>
    </div>
  </div>
</template>

<style>
.row {
  display: flex;
}

.column.left {
  flex: 10%;
}

.column.right {
  flex: 75%;
}
</style>

<script>
// @ is an alias to /src

export default {
  name: "Office Leader Dialogue",
  components: {},
  props: ["line"],
};
</script>
