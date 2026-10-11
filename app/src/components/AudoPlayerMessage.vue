<template>
  <div class="audio-player">
    <div class="controls fixed-controls">
      <div class="menu-and-buttons">
        <span v-if="!isEnglish || !isEsvOrKjv" class="audio-message">
          <small>
            Audio is available when English is selected as the display language,
            along with the English Standard Version (ESV) or King James Version
            (KJV) Bible translation.
            <a href="/settings"> Change settings </a>
          </small>
        </span>
        <span v-else-if="!isWithinSevenDays" class="audio-message">
          <small>
            Audio is available from three days ago through nine days ahead.
            <a href="/"> Go to today </a>
          </small>
        </span>
        <span v-else-if="!audioReady" class="audio-message">
          <small> Preparing audio… </small>
        </span>
        <span v-else-if="!hasAudioLinks" class="audio-message">
          <small> Audio is not available for this office. </small>
        </span>
        <button
          class="dismiss-button"
          type="button"
          aria-label="Hide audio controls"
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
      required: true,
      default: false,
    },
    isEnglish: {
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
  },
  computed: {
    faXmark() {
      return faXmark;
    },
  },
  mounted() {
    this.$nextTick(() => {
      this.emitVisibility();
      if (typeof window.ResizeObserver !== 'undefined') {
        this.controlsObserver = new window.ResizeObserver(() =>
          this.emitVisibility()
        );
        this.controlsObserver.observe(
          this.$el.querySelector('.fixed-controls')
        );
      }
    });
  },
  beforeUnmount() {
    this.controlsObserver?.disconnect();
    this.emitVisibility(false);
  },
  methods: {
    emitVisibility(forceState) {
      const isVisible = forceState !== undefined ? forceState : true;
      const controls = this.$el?.querySelector('.controls.fixed-controls');
      const height =
        isVisible && controls
          ? Math.ceil(
              controls.getBoundingClientRect().height +
                (parseFloat(window.getComputedStyle(controls).bottom) || 0)
            )
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
.controls.fixed-controls {
  position: fixed;
  inset-inline: max(8px, env(safe-area-inset-left))
    max(8px, env(safe-area-inset-right));
  bottom: max(8px, env(safe-area-inset-bottom));
  width: auto;
  max-width: 920px;
  max-height: calc(100dvh - 32px - env(safe-area-inset-bottom));
  overflow-y: auto;
  margin-inline: auto;
  padding: 8px 8px 8px 16px;
  border: 1px solid color-mix(in srgb, var(--font-color) 14%, transparent);
  border-radius: 18px;
  background: color-mix(in srgb, var(--color-bg) 94%, transparent);
  -webkit-backdrop-filter: blur(14px) saturate(1.4);
  backdrop-filter: blur(14px) saturate(1.4);
  color: var(--font-color);
  box-shadow:
    0 1px 2px #0000000d,
    0 10px 32px -8px #00000026;
  z-index: 100;
}
.menu-and-buttons {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.audio-message {
  min-width: 0;
  font-size: 0.875rem;
  line-height: 1.5;
  overflow-wrap: anywhere;
}
.audio-message small {
  font-size: inherit;
}
.audio-message a {
  text-decoration: underline;
}
.dismiss-button {
  display: grid;
  place-items: center;
  flex: 0 0 44px;
  width: 44px;
  height: 44px;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: inherit;
  cursor: pointer;
  touch-action: manipulation;
}
.dismiss-button:hover {
  background: color-mix(in srgb, var(--font-color) 8%, transparent);
}
.dismiss-button:focus-visible,
a:focus-visible {
  outline: 2px solid var(--accent-color) !important;
  outline-offset: 2px;
}
</style>
