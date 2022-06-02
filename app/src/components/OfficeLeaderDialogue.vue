<template>
  <div class="row">
    <div class="column left">
      <p class="rubric">
        <em><small>Officiant</small></em>
      </p>
    </div>
    <div class="column right">
      <p>{{ line.content }}</p>
    </div>
  </div>
</template>

<style>
.rubric {
  font-size: .8em;
  line-height: 1.2em;
}

.row {
  display: flex;
}

.column.left {
  flex: 25%;
}

.column.right {
  flex: 55%;
}

@media (min-width: 500px) {
  .column.left {
    flex: 10%;
  }

  .column.right {
    flex: 75%;
  }
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
