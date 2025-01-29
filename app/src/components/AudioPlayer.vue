<template>
  <div class="audio-player">
    <div class="controls fixed-controls" style="width: 100%">
      <div v-if="!isEsvOrKjv || !isWithinSevenDays" class="menu-and-buttons">
        <span v-if="!isEsvOrKjv">
          <small
            >&nbsp;&nbsp;Audio is only available if the selected bible
            translation is the English Standard Version (ESV) or the Kings James
            Version.&nbsp;&nbsp;
            <a href="/settings"> Change Settings >>> </a>
          </small>
        </span>
        <span v-if="!isWithinSevenDays">
          <small
            >&nbsp;&nbsp;Audio is for today and the next seven days.&nbsp;&nbsp;
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
          <el-button
            size="small"
            :disabled="!isPlaying && !isPaused"
            @click="startFromBeginning"
          >
            ⏮ Restart
          </el-button>
        </el-button-group>
        <Loading v-if="loading" :small="true" />
        <el-select
          v-if="audioReady && headings.length"
          v-model="currentHeadingIndex"
          class="smallSelector"
          placeholder="Jump to..."
          @change="handleTrackChangeForHeading"
        >
          <el-option
            v-for="(heading, index) in headings"
            :key="heading.next_id"
            size="small"
            :value="heading.next_id"
          >
            {{ heading.heading }}
          </el-option>
        </el-select>
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
      currentIndex: null,
      currentHeadingIndex: null,
      isPlaying: false,
      isPaused: false,
      tracks: [],
      headings: [],
      loading: false,
      audioElements: {},
    };
  },
  mounted() {
    this.tracks = this.audio.tracks;
    this.headings = this.audio.headings;
  },
  updated() {
    this.tracks = this.audio.tracks;
    this.headings = this.audio.headings;
  },
  beforeUnmount() {
    this.stopAllAudio();
  },
  methods: {
    loadAudio(index) {
      if (!this.audioElements[index]) {
        const track = this.tracks[index];
        const audio = new Audio(track.url);
        audio.preload = 'metadata';
        this.audioElements[index] = audio;
      }
      return this.audioElements[index];
    },
    startAudio() {
      if (
        this.currentIndex === null ||
        this.isPaused ||
        this.currentIndex === -1 ||
        this.currentIndex === 0
      ) {
        if (this.currentIndex === null || this.currentIndex === -1) {
          this.currentIndex = 0;
        }
        this.playAudioAtIndex(this.currentIndex);
      }
    },
    playAudioAtIndex(index) {
      const track = this.tracks[index];
      const audio = this.loadAudio(index);

      if (audio) {
        this.stopAllAudio();
        this.isPlaying = true;
        this.isPaused = false;

        audio.onerror = () => {
          this.isPlaying = false;
        };

        audio.onstalled = () => {
          this.loading = true;
        };

        audio.addEventListener('canplay', () => {
          this.loading = false;
        });

        audio.play().catch(() => {
          this.isPlaying = false;
        });

        this.scrollToLineId(track.line_id);

        audio.onended = () => {
          this.currentIndex++;
          if (this.currentIndex < this.tracks.length) {
            this.playAudioAtIndex(this.currentIndex);
          } else {
            this.isPlaying = false;
            this.currentIndex = null;
          }
        };
      }
    },
    pauseAudio() {
      if (this.currentIndex !== null) {
        const audio = this.audioElements[this.currentIndex];
        if (audio) {
          audio.pause();
          this.isPaused = true;
          this.isPlaying = false;
        }
      }
      this.isPaused = true;
      this.isPlaying = false;
    },
    stopAudio() {
      if (this.currentIndex !== null) {
        const audio = this.audioElements[this.currentIndex];
        if (audio) {
          audio.pause();
          audio.currentTime = 0;
          this.isPlaying = false;
          this.isPaused = true;
        }
      }
    },
    stopAllAudio() {
      Object.values(this.audioElements).forEach((audio) => {
        audio.pause();
        audio.currentTime = 0;
      });
      this.isPlaying = false;
      this.isPaused = false;
    },
    startFromBeginning() {
      if (this.currentIndex !== null) {
        this.stopAudio();
        this.currentIndex = 0;
        this.playAudioAtIndex(this.currentIndex);
      }
    },
    scrollToLineId(lineId) {
      if (lineId) {
        const element = document.querySelector(`[data-line-id="${lineId}"]`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    },
    handleTrackChange() {
      if (this.currentIndex !== null) {
        this.playAudioAtIndex(this.currentIndex);
      }
    },
    handleTrackChangeForHeading() {
      if (this.currentHeadingIndex !== null) {
        const index = this.tracks.findIndex(
          (track) => track.line_id === this.currentHeadingIndex
        );
        if (index !== null) {
          this.currentIndex = index;
          this.playAudioAtIndex(this.currentIndex);
        }
      }
      this.currentHeadingIndex = null;
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

.audio-list {
  margin-bottom: 100px;
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
