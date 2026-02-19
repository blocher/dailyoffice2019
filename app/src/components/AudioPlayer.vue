<template>
  <div class="audio-player">
    <div class="controls fixed-controls" style="width: 100%">
      <div v-if="!isEsvOrKjv || !isWithinSevenDays" class="menu-and-buttons">
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
            &nbsp;&nbsp;Audio is for today and the next seven days.&nbsp;&nbsp;
            <a href="/"> Go to Today >>> </a>
          </small>
        </span>
      </div>

      <div v-if="isEsvOrKjv" class="menu-and-buttons">
        <div class="button-row">
          <el-button-group v-if="audioReady" class="playback-buttons">
            <el-button
              size="large"
              type="primary"
              :disabled="isPlaying && !isPaused"
              @click="startAudio"
              class="play-button"
            >
              <span class="button-icon">▶</span>
              <span class="button-text">Play</span>
            </el-button>
            <el-button
              size="large"
              type="primary"
              :disabled="!isPlaying"
              @click="pauseAudio"
              class="pause-button"
            >
              <span class="button-icon">⏸</span>
              <span class="button-text">Pause</span>
            </el-button>
          </el-button-group>
          <Loading v-if="loading" :small="true" />
        </div>

        <div class="controls-row" v-if="audioReady && trackSegments.length">
          <el-select
            v-model="playbackSpeed"
            class="speed-selector"
            placeholder="Speed"
            @change="handleSpeedChange"
          >
            <el-option v-for="speed in speeds" :key="speed" :value="speed">
              {{ speed }}
            </el-option>
          </el-select>
          <el-select
            v-model="currentTrackSegment"
            class="segment-selector"
            placeholder="Jump to..."
            @change="handleTrackSegmentChange"
          >
            <el-option
              v-for="segment in trackSegments"
              :key="segment.start_time"
              :value="segment.start_time"
            >
              {{ segment.name }}
            </el-option>
          </el-select>
          <el-switch
            v-model="enableScrolling"
            active-text="Scroll"
            inactive-text="No Scroll"
            class="scroll-toggle"
          ></el-switch>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';

export default {
  name: 'AudioPlayer',
  components: { Loading },
  props: {
    audio: {
      type: Object,
      required: true,
    },
    audioReady: {
      type: Boolean,
      required: true,
    },
    office: {
      type: String,
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
  data() {
    return {
      currentTrackSegment: null,
      isPlaying: false,
      isPaused: false,
      trackSegments: [],
      detailedSegments: [],
      loading: true,
      audioElement: null,
      playbackSpeed: '1.0x',
      enableScrolling: true,
      speeds: [
        '0.5x',
        '0.6x',
        '0.7x',
        '0.8x',
        '0.9x',
        '1.0x',
        '1.1x',
        '1.2x',
        '1.3x',
        '1.4x',
        '1.5x',
        '1.6x',
        '1.7x',
        '1.8x',
        '1.9x',
        '2.0x',
      ],
    };
  },
  mounted() {
    if (
      this.audio &&
      Array.isArray(this.audio[2]) &&
      Array.isArray(this.audio[3])
    ) {
      this.audioElement = new Audio(this.audio[0] || '', { preload: 'auto' });
      this.audioElement.load();
      if (this.audioElement.readyState === this.audioElement.HAVE_ENOUGH_DATA) {
        this.loading = false;
      }
      this.audioElement.addEventListener('canplaythrough', () => {
        this.loading = false;
      });
      this.audioElement.addEventListener('timeupdate', this.handleTimeUpdate);
      this.audioElement.addEventListener('ended', this.stopAudio);

      this.trackSegments = this.audio[2];
      this.detailedSegments = this.audio[3];
    }
  },
  beforeUnmount() {
    this.stopAudio();
    if (this.audioElement) {
      this.audioElement.removeEventListener(
        'timeupdate',
        this.handleTimeUpdate
      );
    }
  },
  methods: {
    startAudio() {
      if (this.audioElement) {
        this.audioElement.play();
        this.isPlaying = true;
        this.isPaused = false;
      }
    },
    pauseAudio() {
      if (this.audioElement) {
        this.audioElement.pause();
        this.isPaused = true;
        this.isPlaying = false;
      }
    },
    stopAudio() {
      if (this.audioElement) {
        this.audioElement.pause();
        this.audioElement.currentTime = 0;
        this.isPlaying = false;
        this.isPaused = false;
      }
    },
    handleSpeedChange() {
      if (this.audioElement) {
        this.audioElement.playbackRate = parseFloat(
          this.playbackSpeed.replace(/[^\d.]/g, '')
        );
      }
    },
    handleTrackSegmentChange() {
      if (this.audioElement && this.currentTrackSegment !== null) {
        this.audioElement.currentTime = parseFloat(this.currentTrackSegment);
        this.startAudio();
        this.currentTrackSegment = null;
      }
    },
    handleTimeUpdate() {
      if (!this.isPlaying || !this.enableScrolling) return;
      const currentTime = this.audioElement.currentTime;
      for (const segment of this.detailedSegments) {
        if (Math.abs(currentTime - segment.start_time) < 0.5) {
          this.scrollToSegment(segment.id);
          break;
        }
      }
    },
    scrollToSegment(segmentId) {
      if (!this.enableScrolling) return;
      const element = document.querySelector(`[data-line-id='${segmentId}']`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    },
  },
};
</script>

<style scoped>
/* Prevent iOS/Android zoom on input focus - CRITICAL for Capacitor apps */
select,
input,
textarea,
button,
.el-select :deep(input),
.el-switch :deep(input),
.el-button :deep(span),
.el-select :deep(.el-input__wrapper),
.el-select :deep(.el-select__wrapper) {
  font-size: 16px !important; /* iOS/Android won't zoom if font-size >= 16px */
  touch-action: manipulation; /* Disable double-tap zoom */
  -webkit-user-select: none; /* Prevent text selection zoom on iOS */
  user-select: none;
}

/* Prevent zoom on all interactive elements */
.audio-player *,
.controls *,
.menu-and-buttons *,
button,
.el-button,
.el-select,
.el-switch {
  touch-action: manipulation !important;
  -webkit-tap-highlight-color: transparent; /* Remove tap highlight on mobile */
}

.audio-player {
  padding: 0;
}

.audio-player .playing {
  font-weight: bold;
  color: green;
}

.audio-list {
  margin-bottom: 120px; /* Increased to account for larger controls */
}

.controls.fixed-controls {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  border-top: 2px solid #ccc;
  background-color: var(--color-bg);
  /* Safe area padding for iPhone notch and rounded corners */
  padding: 14px 18px; /* Increased horizontal padding */
  padding-left: max(18px, env(safe-area-inset-left));
  padding-right: max(18px, env(safe-area-inset-right));
  padding-bottom: max(14px, env(safe-area-inset-bottom));
  z-index: 100;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  touch-action: manipulation;
}

.menu-and-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  touch-action: manipulation;
}

.button-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  touch-action: manipulation;
}

.controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  touch-action: manipulation;
}

/* Playback buttons - large and touch-friendly */
.playback-buttons {
  display: flex;
  gap: 8px;
  flex: 1;
  max-width: 100%;
  touch-action: manipulation;
}

.playback-buttons .el-button {
  flex: 1;
  min-height: 48px; /* iOS HIG recommends 44px minimum */
  font-size: 16px !important;
  font-weight: 600;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s ease;
  touch-action: manipulation !important;
  -webkit-tap-highlight-color: transparent;
}

.button-icon {
  font-size: 18px;
  touch-action: manipulation;
  user-select: none;
}

.button-text {
  font-size: 16px;
  touch-action: manipulation;
  user-select: none;
}

.playback-buttons .el-button:active {
  transform: scale(0.98);
}

/* Speed selector - compact but touch-friendly */
.speed-selector {
  min-width: 85px;
  max-width: 85px;
  flex-shrink: 0;
  touch-action: manipulation;
}

.speed-selector :deep(.el-input__inner),
.speed-selector :deep(.el-input__wrapper),
.speed-selector :deep(input) {
  font-size: 16px !important;
  min-height: 40px;
  touch-action: manipulation !important;
}

/* Segment selector - flexible width */
.segment-selector {
  flex: 1;
  min-width: 0;
  touch-action: manipulation;
}

.segment-selector :deep(.el-input__inner),
.segment-selector :deep(.el-input__wrapper),
.segment-selector :deep(input) {
  font-size: 16px !important;
  min-height: 40px;
  touch-action: manipulation !important;
}

/* Scroll toggle switch */
.scroll-toggle {
  flex-shrink: 0;
  touch-action: manipulation !important;
}

.scroll-toggle :deep(.el-switch__label),
.scroll-toggle :deep(span) {
  font-size: 14px !important;
  touch-action: manipulation !important;
  user-select: none;
}

.scroll-toggle :deep(.el-switch__core) {
  touch-action: manipulation !important;
}

/* Select dropdown options - prevent zoom */
.el-select :deep(.el-select-dropdown__item) {
  font-size: 16px !important;
  min-height: 40px;
  padding: 10px 20px;
  touch-action: manipulation !important;
}

/* Ensure all Element Plus components don't zoom */
:deep(.el-button),
:deep(.el-select),
:deep(.el-switch),
:deep(.el-input),
:deep(.el-select-dropdown) {
  touch-action: manipulation !important;
}

:deep(.el-button span),
:deep(.el-select span),
:deep(.el-switch span) {
  font-size: 16px !important;
  touch-action: manipulation !important;
  user-select: none;
}

/* Tablet/Medium/Large Desktop - Consistent wrapping behavior for all desktop sizes */
@media (min-width: 769px) {
  .controls.fixed-controls {
    padding: 16px 20px;
    padding-left: max(20px, env(safe-area-inset-left));
    padding-right: max(20px, env(safe-area-inset-right));
    padding-bottom: max(16px, env(safe-area-inset-bottom));
  }

  .menu-and-buttons {
    flex-direction: row;
    align-items: center;
    gap: 14px;
    flex-wrap: wrap;
  }

  .button-row {
    flex: 0 1 auto; /* Allow shrinking to trigger wrap */
    flex-basis: 260px; /* Preferred size */
    min-width: 220px; /* But not smaller than this */
  }

  .controls-row {
    display: flex !important;
    flex: 1 1 auto; /* Allow both grow and shrink */
    flex-basis: 400px; /* Preferred size - will wrap if not available */
    justify-content: flex-end;
    gap: 10px;
    min-width: 300px; /* Minimum before wrapping */
  }

  .playback-buttons {
    width: 100%;
    min-width: 220px;
    max-width: 100%;
  }

  .playback-buttons .el-button {
    min-width: 95px;
    flex: 1;
  }

  .speed-selector {
    min-width: 80px;
    max-width: 90px;
    flex-shrink: 0;
  }

  .segment-selector {
    flex: 1 1 auto;
    min-width: 130px;
    max-width: 220px;
  }

  .scroll-toggle {
    flex-shrink: 0;
    min-width: fit-content;
  }
}

/* Mobile optimizations */
@media (max-width: 768px) {
  .controls.fixed-controls {
    padding: 12px 16px; /* Increased horizontal padding */
    padding-left: max(16px, env(safe-area-inset-left));
    padding-right: max(16px, env(safe-area-inset-right));
    padding-bottom: max(12px, env(safe-area-inset-bottom));
  }

  .button-text {
    display: inline; /* Always show text on mobile */
  }

  .playback-buttons .el-button {
    min-height: 52px; /* Slightly larger on mobile for easier tapping */
  }
}

/* Very small screens */
@media (max-width: 360px) {
  .button-text {
    display: none; /* Hide text, show only icons on very small screens */
  }

  .button-icon {
    font-size: 20px;
  }

  .scroll-toggle :deep(.el-switch__label) {
    display: none; /* Simplified switch on small screens */
  }
}
</style>
