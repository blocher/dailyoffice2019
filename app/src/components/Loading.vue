<template>
  <div :class="wrapperClass">
    <div :class="loadingSizeClass">
      <div />
      <div />
      <div />
      <div />
    </div>
  </div>
</template>

<script>
// @ is an alias to /src

export default {
  name: 'Loading',
  components: {},
  props: { small: { type: Boolean, default: false } },
  computed: {
    loadingSizeClass() {
      return this.small ? 'lds-ellipsis size-small' : 'lds-ellipsis size-large';
    },
    wrapperClass() {
      return this.small
        ? 'lds-ellipsis-wrapper size-small'
        : 'lds-ellipsis-wrapper size-large';
    },
  },
};
</script>

<style lang="scss">
.lds-ellipsis-wrapper {
  width: 100%;
  margin: auto;
  text-align: center;
  padding: 2rem 0;
}

.lds-ellipsis-wrapper.size-small {
  width: 15px;
  margin: inherit;
  text-align: center;
  padding: 0.5rem 0;
}

.lds-ellipsis {
  display: inline-block;
  position: relative;
  width: 80px;
  height: 80px;
}

.lds-ellipsis.size-small {
  display: inline-block;
  position: relative;
  width: 15px;
  height: 15px;
}

.lds-ellipsis div {
  position: absolute;
  top: 33px;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--font-color);
  animation-timing-function: cubic-bezier(0, 1, 1, 0);
  opacity: 0.8;
}

.lds-ellipsis.size-small div {
  position: absolute;
  top: 12px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--font-color);
  animation-timing-function: cubic-bezier(0, 1, 1, 0);
  opacity: 0.8;
}

.lds-ellipsis div:nth-child(1) {
  left: 8px;
  animation: lds-ellipsis1 0.6s infinite;
}

.lds-ellipsis div:nth-child(2) {
  left: 8px;
  animation: lds-ellipsis2 0.6s infinite;
}

.lds-ellipsis div:nth-child(3) {
  left: 32px;
  animation: lds-ellipsis2 0.6s infinite;
}

.lds-ellipsis div:nth-child(4) {
  left: 56px;
  animation: lds-ellipsis3 0.6s infinite;
}

// Size-specific positioning for small loading indicator
.lds-ellipsis.size-small div:nth-child(1) {
  left: 2px;
}

.lds-ellipsis.size-small div:nth-child(2) {
  left: 2px;
}

.lds-ellipsis.size-small div:nth-child(3) {
  left: 8px;
}

.lds-ellipsis.size-small div:nth-child(4) {
  left: 14px;
}

@keyframes lds-ellipsis1 {
  0% {
    transform: scale(0);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes lds-ellipsis3 {
  0% {
    transform: scale(1);
  }
  100% {
    transform: scale(0);
  }
}

@keyframes lds-ellipsis2 {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(24px, 0);
  }
}

// Small size animation adjustment
.lds-ellipsis.size-small div:nth-child(2),
.lds-ellipsis.size-small div:nth-child(3) {
  animation: lds-ellipsis2-small 0.6s infinite;
}

@keyframes lds-ellipsis2-small {
  0% {
    transform: translate(0, 0);
  }
  100% {
    transform: translate(6px, 0);
  }
}
</style>
