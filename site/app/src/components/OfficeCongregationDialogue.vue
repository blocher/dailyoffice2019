<template>
  <div class="row">
    <div class="column left">
      <p>
        <em><small>People</small></em>
      </p>
    </div>
    <div class="column right">
      <p>
        <strong>{{ line.content }}</strong>
      </p>
    </div>
  </div>
</template>

<style>
.row {
  display: flex;
}

.column.left {
  flex: 50%;
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
