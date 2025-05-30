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
