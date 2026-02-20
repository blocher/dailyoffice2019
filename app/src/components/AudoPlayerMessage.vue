<template>
  <div class="audio-player">
    <div class="controls fixed-controls" style="width: 100%">
      <div
        v-if="!isEsvOrKjv || !isWithinSevenDays || !audioReady"
        class="menu-and-buttons"
      >
        <span v-if="!isEsvOrKjv">
          <small>
            &nbsp;&nbsp;Audio is only available if the selected bible
            translation is the English Standard Version (ESV) or the Kings James
            Version.&nbsp;&nbsp;
            <a href="/settings"> Change Settings >>> </a>
          </small>
        </span>
        <span v-if="!isWithinSevenDays">
          <small>
            &nbsp;&nbsp;Audio is available for today and the next seven days
            only.&nbsp;&nbsp;
            <a href="/"> Go to Today >>> </a>
          </small>
        </span>
        <span v-if="!audioReady && isEsvOrKjv && isWithinSevenDays">
          <small>
            &nbsp;&nbsp;Audio is loading...it may take a few
            moments.&nbsp;&nbsp;
          </small>
        </span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AudioPlayerMessage',
  props: {
    audioReady: {
      type: Boolean,
      required: true,
    },
    isEsvOrKjv: {
      type: Boolean,
      required: true,
      default: false,
    },
    isWithinSevenDays: {
      type: Boolean,
      required: true,
      default: false,
    },
  },
  mounted() {
    this.$nextTick(() => this.emitVisibility());
  },
  beforeUnmount() {
    this.emitVisibility(false);
  },
  methods: {
    emitVisibility(forceState) {
      const isVisible = forceState !== undefined ? forceState : true;
      const controls = this.$el?.querySelector('.controls.fixed-controls');
      const height =
        isVisible && controls
          ? Math.ceil(controls.getBoundingClientRect().height)
          : 0;
      const event = new window.CustomEvent('audio-player-visibility', {
        detail: { visible: isVisible, height },
      });
      document.dispatchEvent(event);
    },
  },
};
</script>

<style scoped>
.audio-player {
  padding: 10px;
}

.audio-player .playing {
  font-weight: bold;
  color: green;
}

.el-button-group {
  width: 100%;
}

.audio-list {
  margin-bottom: 100px;
}

.el-switch {
  margin-left: 10px;
}

.controls.fixed-controls {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  display: flex;
  flex-direction: row;
  border-top: 2px solid #ccc;
  background-color: var(--color-bg);
  padding: 10px;
  z-index: 100;
  flex-wrap: nowrap;
}

.menu-and-buttons {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  flex-wrap: nowrap;
}

button {
  padding: 10px 15px;
  font-size: 14px;
  border-radius: 5px;
  border: none;
  cursor: pointer;
}

button:disabled {
  cursor: not-allowed;
}

.smallSelector {
  max-width: 200px;
  flex-shrink: 1;
}

.smallestSelector {
  max-width: 75px;
  flex-shrink: 1;
  margin-right: 5px;
}

@media (max-width: 768px) {
  .smallSelector {
    max-width: 150px;
  }

  .menu-and-buttons {
    flex-wrap: nowrap;
    gap: 5px;
  }

  button {
    flex-shrink: 0;
  }
}
</style>
