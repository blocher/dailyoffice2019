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
        <el-button-group v-if="audioReady">
          <el-button
            size="small"
            :disabled="isPlaying && !isPaused"
            @click="startAudio"
          >
            ▶ Play
          </el-button>
          <el-button size="small" :disabled="!isPlaying" @click="pauseAudio">
            ⏸ Pause
          </el-button>
        </el-button-group>
        <Loading v-if="loading" :small="true" />
        <el-select
          v-if="audioReady && trackSegments.length"
          v-model="playbackSpeed"
          class="smallestSelector"
          placeholder="Speed"
          @change="handleSpeedChange"
        >
          <el-option
            v-for="(speed, index) in speeds"
            :key="speed"
            size="small"
            :value="speed"
          >
            {{ speed }}
          </el-option>
        </el-select>
        <el-select
          v-if="audioReady && trackSegments.length"
          v-model="currentTrackSegment"
          class="smallSelector"
          placeholder="Jump to..."
          @change="handleTrackSegmentChange"
        >
          <el-option
            v-for="(segment, index) in trackSegments"
            :key="segment.start_time"
            size="small"
            :value="segment.start_time"
          >
            {{ segment.name }}
          </el-option>
        </el-select>
        <el-switch
          v-model="enableScrolling"
          active-text="Scroll On"
          inactive-text="Scroll Off"
          class="scroll-toggle"
        ></el-switch>
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
.audio-player {
  padding: 0;
}

.audio-player .playing {
  font-weight: bold;
  color: green;
}

.controls.fixed-controls {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  background-color: var(--color-bg);
  border-top: 1px solid rgba(0, 0, 0, 0.15);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  padding: 12px 16px;
  z-index: 100;
  backdrop-filter: blur(8px);
}

:root.dark .controls.fixed-controls {
  border-top: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.3);
}

.menu-and-buttons {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  flex-wrap: nowrap;
  gap: 8px;
  max-width: 900px;
  margin: 0 auto;
}

/* Enhanced button styling */
.el-button-group {
  display: flex;
  gap: 4px;
}

.el-button-group .el-button {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  border-radius: 6px;
  padding: 8px 12px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  background-color: var(--color-bg);
  color: var(--font-color);
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:root.dark .el-button-group .el-button {
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.el-button-group .el-button:hover:not(:disabled) {
  background-color: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
}

:root.dark .el-button-group .el-button:hover:not(:disabled) {
  background-color: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.4);
}

.el-button-group .el-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Enhanced select styling */
.smallSelector,
.smallestSelector {
  font-family: 'Adobe Caslon Pro', serif;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.smallSelector {
  max-width: 180px;
  flex-shrink: 1;
}

.smallestSelector {
  max-width: 70px;
  flex-shrink: 1;
  margin-right: 4px;
}

/* Enhanced switch styling */
.el-switch {
  margin-left: 8px;
}

.scroll-toggle {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 0.8rem;
}

/* Error/info messages styling */
.menu-and-buttons small {
  font-family: 'Adobe Caslon Pro', serif;
  font-size: 0.8rem;
  color: var(--font-color);
  opacity: 0.8;
  line-height: 1.3;
  text-align: center;
  flex: 1;
}

.menu-and-buttons small a {
  color: var(--link-color);
  text-decoration: none;
  font-weight: 600;
}

.menu-and-buttons small a:hover {
  text-decoration: underline;
}

/* Responsive design improvements */
@media (max-width: 768px) {
  .controls.fixed-controls {
    padding: 10px 12px;
  }
  
  .menu-and-buttons {
    gap: 6px;
  }
  
  .smallSelector {
    max-width: 140px;
    font-size: 0.8rem;
  }
  
  .smallestSelector {
    max-width: 60px;
    font-size: 0.8rem;
  }
  
  .el-button-group .el-button {
    font-size: 0.8rem;
    padding: 6px 10px;
  }
  
  .menu-and-buttons small {
    font-size: 0.75rem;
  }
}

@media (max-width: 480px) {
  .controls.fixed-controls {
    padding: 8px 10px;
  }
  
  .menu-and-buttons {
    flex-wrap: wrap;
    gap: 4px;
    justify-content: center;
  }
  
  .el-button-group {
    order: 1;
    width: 100%;
    justify-content: center;
    margin-bottom: 6px;
  }
  
  .smallSelector,
  .smallestSelector {
    order: 2;
    max-width: 120px;
    font-size: 0.75rem;
  }
  
  .el-switch {
    order: 3;
    margin: 0;
  }
  
  .menu-and-buttons small {
    order: 0;
    width: 100%;
    margin-bottom: 6px;
    font-size: 0.7rem;
  }
}

/* Loading component styling within audio player */
.audio-player .loading-container {
  display: inline-flex;
  align-items: center;
  margin: 0 8px;
}
</style>
