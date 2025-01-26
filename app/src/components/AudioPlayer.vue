<template>
  <div class="audio-player">
    <div
      v-for="(url, index) in urls"
      :key="index"
      :class="{ playing: index === currentIndex }"
    >
      <p>Track {{ index + 1 }}: {{ url }}</p>
    </div>
    <div class="controls">
      <button :disabled="isPlaying && !isPaused" @click="startAudio">
        ▶ Play
      </button>
      <button :disabled="!isPlaying" @click="pauseAudio">⏸ Pause</button>
      <button :disabled="!isPlaying" @click="stopAudio">⏹ Stop</button>
      <button :disabled="!isPlaying && !isPaused" @click="startFromBeginning">
        ⏮ Start from Beginning
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AudioPlayer',
  props: {
    urls: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      audioElements: [],
      currentIndex: null,
      isPlaying: false,
      isPaused: false,
    };
  },
  mounted() {
    this.preloadAudio();
  },
  methods: {
    preloadAudio() {
      this.audioElements = this.urls.map((url) => {
        const audio = new Audio(url.url);
        audio.preload = 'auto'; // Preload and use cached copies if available
        return audio;
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
      const audio = this.audioElements[index];
      if (audio) {
        this.isPlaying = true;
        this.isPaused = false;
        audio.play();
        this.scrollToLineId(this.urls[index].line_id); // Scroll to the corresponding element
        audio.onended = () => {
          this.currentIndex++;
          if (this.currentIndex < this.audioElements.length) {
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
    },
    stopAudio() {
      if (this.currentIndex !== null) {
        const audio = this.audioElements[this.currentIndex];
        if (audio) {
          audio.pause();
          audio.currentTime = 0;
          this.isPlaying = false;
          this.isPaused = false;
          this.currentIndex = null;
        }
      }
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

.controls {
  margin-top: 10px;
}

button {
  margin-right: 10px;
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
