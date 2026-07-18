<template>
  <div class="audio-player">
    <div class="controls fixed-controls" style="width: 100%">
      <div class="menu-and-buttons">
        <span v-if="!isAudioEligible">
          <small>
            &nbsp;&nbsp;{{
              unavailableMessage ||
              'Audio is only available for English contemporary or traditional offices with the ESV or KJV Bible. Support for other languages is still in progress.'
            }}&nbsp;&nbsp;
            <a href="/settings"> Change Settings >>> </a>
          </small>
        </span>
        <span v-else-if="!isWithinSevenDays">
          <small>
            &nbsp;&nbsp;Audio is available for today and the next seven days
            only.&nbsp;&nbsp;
            <a href="/"> Go to Today >>> </a>
          </small>
        </span>
        <span v-else-if="!audioReady">
          <small>
            &nbsp;&nbsp;Audio is loading...it may take a few
            moments.&nbsp;&nbsp;
          </small>
        </span>
        <span v-else-if="!hasAudioLinks">
          <small>
            &nbsp;&nbsp;{{
              unavailableMessage || 'Audio is not available for this office.'
            }}&nbsp;&nbsp;
          </small>
        </span>
        <button
          class="dismiss-button"
          title="Hide audio controls"
          @click.stop="$emit('dismiss-audio')"
        >
          <font-awesome-icon :icon="faXmark" />
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { faXmark } from '@fortawesome/free-solid-svg-icons';

export default {
  name: 'AudioPlayerMessage',
  emits: ['dismiss-audio'],
  props: {
    audioReady: {
      type: Boolean,
      required: true,
    },
    isEsvOrKjv: {
      type: Boolean,
      required: false,
      default: false,
    },
    isAudioEligible: {
      type: Boolean,
      required: false,
      default: false,
    },
    isWithinSevenDays: {
      type: Boolean,
      required: true,
      default: false,
    },
    hasAudioLinks: {
      type: Boolean,
      required: false,
      default: false,
    },
    unavailableMessage: {
      type: String,
      required: false,
      default: '',
    },
  },
  computed: {
    faXmark() {
      return faXmark;
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
  gap: 16px;
}

.dismiss-button {
  background: transparent;
  border: none;
  font-size: 18px;
  padding: 0 0 0 16px;
  width: auto;
  height: 32px;
  min-width: 32px;
  flex-shrink: 0;
  border-left: 1px solid rgba(0, 0, 0, 0.1);
  cursor: pointer;
  color: var(--color-text, #333);
  opacity: 0.5;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}

.dismiss-button:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.08);
}

.dismiss-button:active {
  transform: scale(0.92);
}
</style>
