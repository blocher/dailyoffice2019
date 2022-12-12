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

<script>
// @ is an alias to /src

export default {
  name: "Office Leader Dialogue",
  components: {},
  props: ["line"],
};
</script>

<style>
.rubric {
  font-size: .8em;
  line-height: 1.2em;
}

.row {
  display: flex;
  align-items: baseline;
  gap: 20px;
}

.column.left {
  flex: 15%;
}

.column.right {
  flex: 65%;
}

@media (min-width: 500px) {
  .column.left {
    flex: 15%;
  }

  .column.right {
    flex: 65%;
  }
}

</style>
