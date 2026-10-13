<template>
  <div class="row">
    <div class="column left">
      <p class="rubric">
        <em><small>Officiant</small></em>
      </p>
    </div>
    <div class="column right">
      <span :data-line-id="line.id"></span>
      <p>{{ line.content }}</p>
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
