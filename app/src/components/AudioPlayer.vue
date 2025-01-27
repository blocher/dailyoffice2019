<template>
  <div class="audio-player">
    <div class="controls fixed-controls">
      <div class="menu-and-buttons">
        <select
          v-model="currentHeadingIndex"
          @change="handleTrackChangeForHeading"
        >
          <option key="-1" disabled value="-1">Jump to..</option>
          <option
            v-for="(heading, index) in headings"
            :key="heading.next_id"
            :value="heading.next_id"
          >
            {{ heading.heading }}
          </option>
        </select>
        <div class="button-group">
          <button :disabled="isPlaying && !isPaused" @click="startAudio">
            ▶ Play/Resume
          </button>
          <button :disabled="!isPlaying" @click="pauseAudio">⏸ Pause</button>
          <button
            :disabled="!isPlaying && !isPaused"
            @click="startFromBeginning"
          >
            ⏮ Start from Beginning
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AudioPlayer',
  props: {
    audio: {
      type: Object,
      required: true,
    },
  },
  data() {
    return {
      currentIndex: -1,
      currentHeadingIndex: -1,
      isPlaying: false,
      isPaused: false,
      tracks: [],
      headings: [],
      audioCache: {},
    };
  },
  mounted() {
    this.tracks = this.audio.tracks;
    this.headings = this.audio.headings;
    this.preloadAudio();
  },
  methods: {
    preloadAudio() {
      this.tracks.forEach((track) => {
        const audio = new Audio(track.url);
        audio.preload = 'auto'; // Preload and cache the audio
        this.audioCache[track.url] = audio;
      });
    },
    startAudio() {
      if (this.currentIndex === null || this.isPaused) {
        if (this.currentIndex === null) {
          this.currentIndex = 0; // Start from the beginning
        }
        this.playAudioAtIndex(this.currentIndex);
      }
    },
    playAudioAtIndex(index) {
      const track = this.tracks[index];
      const audio = this.audioCache[track.url];
      if (audio) {
        this.stopAllAudio();
        this.isPlaying = true;
        this.isPaused = false;
        audio.play();
        this.scrollToLineId(track.line_id); // Scroll to the corresponding element
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
        const track = this.tracks[this.currentIndex];
        const audio = this.audioCache[track.url];
        if (audio) {
          audio.pause();
          this.isPaused = true;
          this.isPlaying = false;
        }
      }
    },
    stopAudio() {
      if (this.currentIndex !== null) {
        const track = this.tracks[this.currentIndex];
        const audio = this.audioCache[track.url];
        if (audio) {
          audio.pause();
          audio.currentTime = 0;
          this.isPlaying = false;
          this.isPaused = false;
        }
      }
    },
    stopAllAudio() {
      Object.values(this.audioCache).forEach((audio) => {
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
        if (index !== -1) {
          this.currentIndex = index;
          this.playAudioAtIndex(this.currentIndex);
        }
      }
    },
  },
};
</script>

<style>
.audio-player {
  padding: 10px;
}

.audio-player .playing {
  font-weight: bold;
  color: green;
}

.audio-list {
  margin-bottom: 100px; /* Reserve space for fixed controls */
}

.controls.fixed-controls {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  border-top: 2px solid #ccc;
  background-color: #fff;
  padding: 10px;
  box-shadow: 0 -2px 5px rgba(0, 0, 0, 0.1);
}

.menu-and-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

button {
  padding: 10px 15px;
  font-size: 14px;
  border-radius: 5px;
  border: none;
  cursor: pointer;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style>
