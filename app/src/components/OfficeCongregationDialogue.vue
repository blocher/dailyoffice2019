<template>
  <span :data-line-id="line.id"></span>
  <div class="row">
    <div class="column left">
      <p class="rubric">
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

<script>
// @ is an alias to /src

export default {
  name: 'Office Leader Dialogue',
  components: {},
  props: ['line'],
};
</script>

<style>
.rubric {
  font-size: 0.8em;
  line-height: 1.2em;
}

.row {
  display: flex;
  align-items: baseline;
}

.column.left {
  flex: 50%;
}

.column.right {
  flex: 75%;
}
</style>
