<template>
  <div class="audio-player">
    <div>
      <button @click="start">Play</button>
      <button @click="stop">Stop</button>
      <button @click="pause">Pause</button>
      <button @click="resume">Resume</button>
    </div>
    <p v-if="currentTrack">Now Playing: {{ currentTrack }}</p>
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
      audio: null,
      currentIndex: 0,
      currentTrack: '',
    };
  },
  mounted() {
    this.audio = new Audio();
    this.audio.addEventListener('ended', this.playNext);
  },
  beforeUnmount() {
    if (this.audio) {
      this.audio.pause();
      this.audio.removeEventListener('ended', this.playNext);
      this.audio = null;
    }
  },
  methods: {
    playNext() {
      this.currentIndex++;
      if (this.currentIndex < this.urls.length) {
        this.play();
      } else {
        // console.log('All tracks have been played.');
        this.currentTrack = '';
      }
    },
    play() {
      if (this.urls[this.currentIndex]) {
        this.currentTrack = this.urls[this.currentIndex];
        this.audio.src = this.currentTrack;
        this.audio
          .play()
          .then(() => {}) //console.log(`Playing: ${this.currentTrack}`))
          .catch(() => {}); //console.error('Error playing audio:', error));
      }
    },
    start() {
      this.currentIndex = 0;
      this.play();
    },
    stop() {
      if (this.audio) {
        this.audio.pause();
        this.audio.currentTime = 0;
        this.currentIndex = 0;
        this.currentTrack = '';
      }
    },
    pause() {
      if (this.audio) {
        this.audio.pause();
      }
    },
    resume() {
      if (this.audio && this.audio.paused) {
        this.audio.play();
      }
    },
  },
};
</script>

<style scoped>
.audio-player {
  margin: 20px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 5px;
  max-width: 300px;
}

button {
  margin-right: 10px;
}
</style>
