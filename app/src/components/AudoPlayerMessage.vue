<template>
  <div class="audio-player">
    <div class="controls fixed-controls">
      <div class="menu-and-buttons">
        <UiIcon
          name="headphones"
          class="message-icon"
          :class="{ 'is-preparing': isPreparing }"
        />
        <span
          v-if="context === 'readings' && !isEsvOrKjv"
          class="audio-message"
        >
          <small>
            Audio is available with the English Standard Version (ESV) or King
            James Version (KJV). Choose one under Translation.
          </small>
        </span>
        <span v-else-if="!isEnglish || !isEsvOrKjv" class="audio-message">
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
          <small>
            Audio is not available for
            {{ context === 'readings' ? 'these readings' : 'this office' }}.
          </small>
        </span>
        <button
          class="dismiss-button"
          type="button"
          aria-label="Hide audio controls"
          title="Hide audio controls"
          @click.stop="$emit('dismiss-audio')"
        >
          <UiIcon name="close" />
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import UiIcon from '@/ui/UiIcon.vue';

export default {
  name: 'AudioPlayerMessage',
  components: { UiIcon },
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
    // 'office' or 'readings': what the messages talk about.
    context: {
      type: String,
      default: 'office',
    },
  },
  computed: {
    // Mirrors the template's v-else-if chain: only "Preparing audio…" is
    // a transient state worth animating.
    isPreparing() {
      return (
        this.isEnglish &&
        this.isEsvOrKjv &&
        this.isWithinSevenDays &&
        !this.audioReady
      );
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
/* Matches the AudioPlayer bar: docked to the bottom edge on phones, a
   floating raised card on wider screens. */
.controls.fixed-controls {
  position: fixed;
  inset-inline: 0;
  bottom: 0;
  z-index: 100;
  max-height: calc(var(--vvh) - 2rem - env(safe-area-inset-bottom));
  overflow-y: auto;
  padding: var(--space-2) max(var(--space-2), env(safe-area-inset-right))
    calc(var(--space-2) + env(safe-area-inset-bottom))
    max(var(--space-4), env(safe-area-inset-left));
  border-top: 1px solid var(--rule);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  background-color: var(--paper-raised);
  color: var(--ink);
  font-family: var(--font-book);
  box-shadow: var(--shadow);
}
.menu-and-buttons {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}
.message-icon {
  color: var(--accent);
  font-size: 1.25rem;
}
.message-icon.is-preparing {
  animation: message-pulse 1.6s var(--ease) infinite;
}
@keyframes message-pulse {
  50% {
    opacity: 0.35;
  }
}
.audio-message {
  flex: 1 1 auto;
  min-width: 0;
  color: var(--ink-soft);
  font-size: var(--text-sm);
  line-height: 1.45;
  overflow-wrap: anywhere;
}
.audio-message small {
  font-size: inherit;
}
.audio-message a {
  color: var(--accent);
  white-space: nowrap;
}
.dismiss-button {
  display: grid;
  place-items: center;
  flex: 0 0 2.75rem;
  width: 2.75rem;
  height: 2.75rem;
  margin-left: auto;
  border-radius: var(--radius);
  color: var(--ink-faint);
  font-size: 1.125rem;
  touch-action: manipulation;
  transition:
    background-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}
.dismiss-button:hover {
  background-color: var(--paper-sunken);
  color: var(--ink);
}
.dismiss-button:focus-visible,
a:focus-visible {
  outline: none;
  box-shadow: var(--focus-ring);
}

@media (min-width: 720px) {
  .controls.fixed-controls {
    inset-inline: max(var(--gutter), env(safe-area-inset-left))
      max(var(--gutter), env(safe-area-inset-right));
    bottom: calc(var(--space-3) + env(safe-area-inset-bottom));
    max-width: 58rem;
    margin-inline: auto;
    padding: var(--space-2) var(--space-2) var(--space-2) var(--space-4);
    border: 1px solid var(--rule);
    border-radius: var(--radius-lg);
  }
}

@media (prefers-reduced-motion: reduce) {
  .message-icon.is-preparing {
    animation: none;
  }
}
</style>
