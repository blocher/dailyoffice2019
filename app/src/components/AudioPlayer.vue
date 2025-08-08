<template>
  <div class="audio-player">
    <div class="controls fixed-controls" style="width: 100%">
      <!-- Warning/Info Messages -->
      <div v-if="!isEsvOrKjv || !isWithinSevenDays" class="audio-warning">
        <span v-if="!isEsvOrKjv">
          <small>
            Audio is only available if the selected bible translation is the English Standard Version (ESV) or the Kings James Version.
            <a href="/settings" class="settings-link">Change Settings</a>
          </small>
        </span>
        <span v-if="!isWithinSevenDays">
          <small>
            Audio is for today and the next seven days.
            <a href="/" class="today-link">Go to Today</a>
          </small>
        </span>
      </div>

      <!-- Main Audio Controls -->
      <div v-if="isEsvOrKjv" class="menu-and-buttons">
        <div class="audio-controls-container">
          <!-- Play/Pause Controls -->
          <el-button-group v-if="audioReady">
            <el-button
              size="small"
              :disabled="isPlaying && !isPaused"
              @click="startAudio"
            >
              <font-awesome-icon :icon="['fas', 'fa-play']" />
              Play
            </el-button>
            <el-button size="small" :disabled="!isPlaying" @click="pauseAudio">
              <font-awesome-icon :icon="['fas', 'fa-pause']" />
              Pause
            </el-button>
          </el-button-group>
          
          <!-- Loading Indicator -->
          <Loading v-if="loading" :small="true" />
          
          <!-- Speed Control -->
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
          
          <!-- Jump to Section -->
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
          
          <!-- Auto-scroll Toggle -->
          <el-switch
            v-model="enableScrolling"
            active-text="Scroll On"
            inactive-text="Scroll Off"
            class="scroll-toggle"
          />
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
.audio-player {
  padding: 0;
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
  flex-direction: column;
  border-top: 2px solid var(--el-border-color);
  background-color: var(--color-bg);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 0.75rem;
  z-index: 100;
  box-shadow: 0 -4px 6px -1px rgba(0, 0, 0, 0.1);
  font-family: 'Adobe Caslon Pro', serif;
  
  @media (max-width: 768px) {
    padding: 0.5rem;
  }
}

.menu-and-buttons {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 0.5rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  @media (max-width: 480px) {
    gap: 0.25rem;
  }
}

.el-button-group {
  display: flex;
  gap: 0.25rem;
  flex-shrink: 0;
  
  .el-button {
    font-family: 'Adobe Caslon Pro', serif;
    font-weight: 600;
    font-size: 0.875rem;
    letter-spacing: 0.025em;
    min-width: 70px;
    
    @media (max-width: 480px) {
      min-width: 60px;
      font-size: 0.75rem;
      padding: 0.5rem 0.75rem;
    }
  }
}

.audio-controls-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  justify-content: space-between;
  
  @media (max-width: 768px) {
    width: 100%;
    justify-content: center;
  }
}

.smallSelector {
  max-width: 180px;
  flex-shrink: 1;
  font-family: 'Adobe Caslon Pro', serif;
  
  @media (max-width: 768px) {
    max-width: 140px;
  }
  
  @media (max-width: 480px) {
    max-width: 120px;
    font-size: 0.75rem;
  }
}

.smallestSelector {
  max-width: 80px;
  flex-shrink: 1;
  margin-right: 0.5rem;
  font-family: 'Adobe Caslon Pro', serif;
  
  @media (max-width: 480px) {
    max-width: 70px;
    margin-right: 0.25rem;
  }
}

.scroll-toggle {
  flex-shrink: 0;
  
  .el-switch__label {
    font-family: 'Adobe Caslon Pro', serif;
    font-size: 0.75rem;
    
    @media (max-width: 480px) {
      font-size: 0.625rem;
    }
  }
}

// Warning/info text styling
.audio-warning {
  background: var(--el-color-warning-light-9);
  border: 1px solid var(--el-color-warning-light-7);
  border-radius: 0.375rem;
  padding: 0.75rem;
  text-align: center;
  font-size: 0.875rem;
  
  small {
    font-family: 'Adobe Caslon Pro', serif;
    color: var(--el-color-warning-dark-2);
    
    a {
      color: var(--el-color-warning);
      text-decoration: underline;
      font-weight: 600;
      
      &:hover {
        color: var(--el-color-warning-dark-1);
      }
    }
  }
}

// Book-like enhancements
.controls.fixed-controls {
  // Add subtle paper-like texture
  position: relative;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      180deg,
      rgba(0, 0, 0, 0.02) 0%,
      transparent 100%
    );
    pointer-events: none;
  }
  
  // Add page edge shadow
  &::after {
    content: '';
    position: absolute;
    top: -2px;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(
      180deg,
      rgba(0, 0, 0, 0.1) 0%,
      transparent 100%
    );
  }
}

// Responsive breakpoints for better mobile experience
@media (max-width: 1024px) {
  .menu-and-buttons {
    flex-wrap: wrap;
  }
}

@media (max-width: 768px) {
  .controls.fixed-controls {
    padding: 0.5rem;
  }
  
  .audio-controls-container {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .el-button-group {
    width: 100%;
    justify-content: center;
  }
  
  .smallSelector,
  .smallestSelector {
    width: 100%;
    max-width: none;
  }
}

@media (max-width: 480px) {
  .controls.fixed-controls {
    padding: 0.375rem;
  }
  
  .menu-and-buttons {
    gap: 0.25rem;
  }
  
  .audio-controls-container {
    gap: 0.375rem;
  }
}
</style>
