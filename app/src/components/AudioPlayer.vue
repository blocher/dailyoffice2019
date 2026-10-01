<template>
  <div class="audio-player">
    <div class="controls fixed-controls" style="width: 100%">
      <div v-if="!isEsvOrKjv || !isWithinSevenDays" class="availability-note">
        <span v-if="!isEsvOrKjv">
          <small>
            Audio is only available if the selected Bible translation is the
            English Standard Version (ESV) or the Kings James Version.
            <a href="/settings">Change settings</a>
          </small>
        </span>
        <span v-if="!isWithinSevenDays">
          <small>
            Audio is for today and the next seven days.
            <a href="/">Go to today</a>
          </small>
        </span>
        <button
          v-if="!isPlaying"
          class="dismiss-button"
          title="Hide audio controls"
          @click.stop="$emit('dismiss-audio')"
        >
          <font-awesome-icon :icon="faXmark" />
        </button>
      </div>

      <div v-if="isEsvOrKjv" class="player-shell">
        <button
          v-if="isMobile && !isExpanded"
          class="mini-player"
          type="button"
          aria-label="Expand audio player"
          @click="toggleExpanded"
        >
          <div class="mini-player-content">
            <span class="mini-player-icon">
              <font-awesome-icon
                :icon="isPlaying && !isPaused ? faPause : faPlay"
              />
            </span>
            <span class="mini-player-text">
              <span class="mini-player-eyebrow">
                {{ isPlaying ? 'Now listening' : 'Audio ready' }}
              </span>
              <strong>{{ currentSectionName }}</strong>
            </span>
            <span class="mini-player-time">
              {{ formattedCurrentTime }} / {{ formattedDuration }}
            </span>
            <span class="mini-player-expand">
              <font-awesome-icon :icon="faChevronUp" />
            </span>
          </div>
          <div class="mini-player-progress">
            <div
              class="mini-player-progress-bar"
              :style="{ width: progressPercentage + '%' }"
            ></div>
          </div>
        </button>

        <template v-else>
          <div class="player-header">
            <div class="player-now">
              <span class="player-kicker">
                {{ isPlaying ? 'Now listening' : 'Daily Office audio' }}
              </span>
              <strong class="player-section">{{ currentSectionName }}</strong>
            </div>
            <div class="player-header-actions">
              <button
                v-if="!isPlaying"
                class="dismiss-button"
                title="Hide audio controls"
                @click.stop="$emit('dismiss-audio')"
              >
                <font-awesome-icon :icon="faXmark" />
              </button>
              <button
                v-if="isMobile"
                class="collapse-button"
                title="Minimize"
                type="button"
                @click="toggleExpanded"
              >
                <font-awesome-icon :icon="faChevronDown" />
              </button>
            </div>
          </div>

          <div v-if="audioReady" class="player-main">
            <div class="transport-controls">
              <button
                class="skip-button"
                type="button"
                title="Back 15 seconds"
                aria-label="Back 15 seconds"
                @click="skipBy(-15)"
              >
                <font-awesome-icon :icon="faBackwardStep" />
                <span>15</span>
              </button>
              <button
                class="primary-play-button"
                type="button"
                :aria-label="isPlaying ? 'Pause audio' : 'Play audio'"
                @click="togglePlayback"
              >
                <font-awesome-icon :icon="isPlaying ? faPause : faPlay" />
              </button>
              <button
                class="skip-button"
                type="button"
                title="Forward 15 seconds"
                aria-label="Forward 15 seconds"
                @click="skipBy(15)"
              >
                <font-awesome-icon :icon="faForwardStep" />
                <span>15</span>
              </button>
            </div>

            <div class="timeline">
              <input
                class="timeline-slider"
                type="range"
                min="0"
                :max="duration || 0"
                step="0.01"
                :value="currentTime"
                aria-label="Audio progress"
                :style="{ '--progress': progressPercentage + '%' }"
                @input="seekToTime"
              />
              <div class="timeline-times" aria-hidden="true">
                <span>{{ formattedCurrentTime }}</span>
                <span>-{{ formattedRemainingTime }}</span>
              </div>
            </div>

            <div v-if="trackSegments.length" class="utility-controls">
              <el-select
                v-model="playbackSpeed"
                class="speed-selector"
                aria-label="Playback speed"
                @change="handleSpeedChange"
              >
                <el-option v-for="speed in speeds" :key="speed" :value="speed">
                  {{ speed }}
                </el-option>
              </el-select>
              <div class="segment-selector-wrap">
                <span class="control-label">Section</span>
                <el-select
                  v-model="currentTrackSegment"
                  class="segment-selector"
                  placeholder="Jump to…"
                  :disabled="seeking"
                  aria-label="Jump to section"
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
                <div v-if="seeking" class="seeking-overlay">
                  <Loading :small="true" />
                  <span class="seeking-text">Jumping…</span>
                </div>
              </div>
              <button
                class="scroll-control"
                :class="{ 'scroll-control--active': enableScrolling }"
                type="button"
                :aria-pressed="enableScrolling"
                @click="enableScrolling = !enableScrolling"
              >
                <span class="scroll-control-mark" aria-hidden="true">↹</span>
                Auto-scroll
              </button>
            </div>
          </div>
          <div v-else class="player-loading">
            <Loading :small="true" />
            <span>Preparing audio…</span>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
import Loading from '@/components/Loading.vue';
import {
  faBackwardStep,
  faChevronDown,
  faChevronUp,
  faForwardStep,
  faPause,
  faPlay,
  faVolumeHigh,
  faVolumeMute,
  faXmark,
} from '@fortawesome/free-solid-svg-icons';

export default {
  name: 'AudioPlayer',
  components: {
    Loading,
  },
  emits: ['dismiss-audio', 'audio-play'],
  props: {
    audio: {
      type: Array,
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
      seeking: false, // true while a "Jump to" seek is waiting to become reachable
      trackSegments: [],
      detailedSegments: [],
      wordSegments: [],
      activeWordIndex: -1,
      loading: true,
      audioElement: null,
      playbackSpeed: '1.0x',
      enableScrolling: true,
      isExpanded: false, // Track if player is expanded or minimized (mobile only)
      currentTime: 0, // Current playback time
      duration: 0, // Total duration
      isMobile: false, // Track if we're on mobile
      hasEmittedPlay: false, // analytics: emit audio-play once per office load
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
    // Check if mobile on mount
    this.checkMobile();
    window.addEventListener('resize', this.checkMobile);
    window.visualViewport?.addEventListener('resize', this.emitVisibility);
    window.visualViewport?.addEventListener('scroll', this.emitVisibility);

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
      this.audioElement.addEventListener('loadedmetadata', () => {
        this.duration = this.audioElement.duration;
      });

      this.trackSegments = this.audio[2];
      this.detailedSegments = this.audio[3];
      this.wordSegments = Array.isArray(this.audio[4]) ? this.audio[4] : [];
      this.$nextTick(() => this.prepareWordElements());
    }

    this.$nextTick(() => this.emitVisibility());
  },
  beforeUnmount() {
    this.stopAudio();
    window.removeEventListener('resize', this.checkMobile);
    window.visualViewport?.removeEventListener('resize', this.emitVisibility);
    window.visualViewport?.removeEventListener('scroll', this.emitVisibility);
    if (this.audioElement) {
      this.audioElement.removeEventListener(
        'timeupdate',
        this.handleTimeUpdate
      );
    }
    this.clearActiveWord();
    this.emitVisibility(false);
  },
  methods: {
    emitVisibility(forceState) {
      const isVisible = forceState !== undefined ? forceState : true;
      const controls = this.$el?.querySelector('.controls.fixed-controls');
      const height =
        isVisible && controls ? Math.ceil(controls.offsetHeight) : 0;
      const event = new window.CustomEvent('audio-player-visibility', {
        detail: { visible: isVisible, height },
      });
      document.dispatchEvent(event);
    },
    startAudio() {
      if (this.audioElement) {
        // play() rejects (e.g. NotSupportedError) when the source can't be
        // loaded; catch it so it doesn't surface as an uncaught promise error.
        const playPromise = this.audioElement.play();
        if (playPromise && typeof playPromise.catch === 'function') {
          playPromise.catch(() => {
            this.isPlaying = false;
            this.isPaused = false;
          });
        }
        this.isPlaying = true;
        this.isPaused = false;
        if (!this.hasEmittedPlay) {
          this.hasEmittedPlay = true;
          this.$emit('audio-play');
        }
      }
    },
    togglePlayback() {
      if (this.isPlaying) {
        this.pauseAudio();
      } else {
        this.startAudio();
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
        this.currentTime = 0;
        this.clearActiveWord();
      }
    },
    skipBy(seconds) {
      if (!this.audioElement) return;
      const duration = Number.isFinite(this.audioElement.duration)
        ? this.audioElement.duration
        : this.duration;
      this.audioElement.currentTime = Math.min(
        Math.max(0, this.audioElement.currentTime + seconds),
        duration || 0
      );
      this.currentTime = this.audioElement.currentTime;
      this.updateActiveWord(this.currentTime);
    },
    seekToTime(event) {
      if (!this.audioElement) return;
      const target = Number.parseFloat(event.target.value);
      if (Number.isNaN(target)) return;
      this.audioElement.currentTime = target;
      this.currentTime = target;
      this.updateActiveWord(target);
    },
    handleSpeedChange() {
      if (this.audioElement) {
        this.audioElement.playbackRate = parseFloat(
          this.playbackSpeed.replace(/[^\d.]/g, '')
        );
      }
    },
    handleTrackSegmentChange() {
      if (!this.audioElement || this.currentTrackSegment === null) return;

      const el = this.audioElement;
      const rawTarget = parseFloat(this.currentTrackSegment);
      // Reset immediately so the same segment can be selected again.
      this.currentTrackSegment = null;
      if (Number.isNaN(rawTarget)) return;

      // Seeks consistently land a beat *past* the segment start (encoder frame
      // snapping + accumulated re-encode drift), clipping the first words. Each
      // segment in the "Jump to" list is preceded by a silence gap, so nudging
      // the seek slightly earlier lands in that silence instead of mid-word.
      const LEAD_IN = 1.0;
      const target = Math.max(0, rawTarget - LEAD_IN);

      // iOS (Safari & Chrome both run on WebKit) gates seeking on a known,
      // finite `duration` AND a `seekable` range that already reaches the
      // target; writing currentTime too early is silently clamped to the
      // buffered end. Short offices (e.g. Compline) buffer instantly so a
      // single seek works, but long ones (e.g. Evening Prayer, with the
      // lessons) aren't seekable to a late chapter yet — so we retry the seek
      // as the media reports it can reach the target. Desktop is permissive
      // and simply seeks on the first attempt.
      let settled = false;
      // Only surface the spinner if the seek can't land quickly, so short
      // offices (Compline) never flash an indicator for an instant jump.
      const spinnerTimer = window.setTimeout(() => {
        if (!settled) this.seeking = true;
      }, 250);
      const cleanup = () => {
        if (settled) return;
        settled = true;
        window.clearTimeout(spinnerTimer);
        this.seeking = false;
        el.removeEventListener('loadedmetadata', trySeek);
        el.removeEventListener('durationchange', trySeek);
        el.removeEventListener('canplay', trySeek);
        el.removeEventListener('progress', trySeek);
        el.removeEventListener('seeked', onSeeked);
      };
      const canReachTarget = () => {
        if (!Number.isFinite(el.duration) || el.duration <= 0) return false;
        for (let i = 0; i < el.seekable.length; i += 1) {
          if (target <= el.seekable.end(i) + 0.25) return true;
        }
        return false;
      };
      const onSeeked = () => {
        if (Math.abs(el.currentTime - target) < 1) cleanup();
      };
      const trySeek = () => {
        if (settled || !canReachTarget()) return;
        try {
          el.currentTime = Math.min(target, el.duration - 0.05);
        } catch {
          /* not seekable yet; a later event will retry */
        }
      };

      el.addEventListener('loadedmetadata', trySeek);
      el.addEventListener('durationchange', trySeek);
      el.addEventListener('canplay', trySeek);
      el.addEventListener('progress', trySeek);
      el.addEventListener('seeked', onSeeked);
      // Safety valve so listeners don't linger forever if the seek never lands.
      window.setTimeout(cleanup, 15000);

      // Play first to satisfy iOS's user-activation requirement, then seek.
      const playPromise = el.play();
      this.isPlaying = true;
      this.isPaused = false;
      if (playPromise && typeof playPromise.then === 'function') {
        playPromise.then(trySeek).catch(trySeek);
      } else {
        trySeek();
      }
    },
    handleTimeUpdate() {
      if (!this.audioElement) return;

      this.currentTime = this.audioElement.currentTime;
      if (this.wordSegments.length) {
        this.updateActiveWord(this.currentTime);
        return;
      }

      if (!this.isPlaying || !this.enableScrolling) return;

      const currentTime = this.audioElement.currentTime;
      for (const segment of this.detailedSegments) {
        if (Math.abs(currentTime - segment.start_time) < 0.5) {
          this.scrollToSegment(segment.id);
          break;
        }
      }
    },
    normalizeWord(word) {
      return String(word || '')
        .normalize('NFKD')
        .replace(/\p{M}/gu, '')
        .toLocaleLowerCase()
        .replace(/[^\p{L}\p{N}]/gu, '');
    },
    findLineAnchor(lineId) {
      return Array.from(document.querySelectorAll('[data-line-id]')).find(
        (element) => element.dataset.lineId === lineId
      );
    },
    wordContainerForAnchor(anchor) {
      if (!anchor) return null;
      if (anchor.nextElementSibling) return anchor.nextElementSibling;
      const parent = anchor.parentElement;
      if (!parent) return null;
      return Array.from(parent.children).find((element) =>
        element.matches('p, div')
      );
    },
    prepareWordElements() {
      if (!this.wordSegments.length) return;
      const segmentsByLine = new Map();
      this.wordSegments.forEach((segment, index) => {
        if (!segment.id) return;
        if (!segmentsByLine.has(segment.id)) {
          segmentsByLine.set(segment.id, []);
        }
        segmentsByLine.get(segment.id).push({ ...segment, index });
      });

      segmentsByLine.forEach((segments, lineId) => {
        if (
          segments.every((segment) =>
            document.querySelector(`[data-audio-word-index='${segment.index}']`)
          )
        ) {
          return;
        }
        const container = this.wordContainerForAnchor(
          this.findLineAnchor(lineId)
        );
        if (!container) return;

        const walker = document.createTreeWalker(
          container,
          window.NodeFilter.SHOW_TEXT
        );
        const tokens = [];
        let node = walker.nextNode();
        while (node) {
          if (!node.parentElement?.closest('.audio-word')) {
            for (const match of node.data.matchAll(
              /[\p{L}\p{N}]+(?:[’'][\p{L}\p{N}]+)*/gu
            )) {
              tokens.push({
                node,
                start: match.index,
                end: match.index + match[0].length,
                normalized: this.normalizeWord(match[0]),
              });
            }
          }
          node = walker.nextNode();
        }

        const matches = [];
        let cursor = 0;
        segments.forEach((segment) => {
          const normalized = this.normalizeWord(segment.word);
          let tokenIndex = tokens.findIndex(
            (token, index) =>
              index >= cursor &&
              index < cursor + 24 &&
              token.normalized === normalized
          );
          if (tokenIndex < 0) {
            while (
              cursor < tokens.length &&
              /^\d+$/.test(tokens[cursor].normalized) &&
              !/^\d+$/.test(normalized)
            ) {
              cursor += 1;
            }
            tokenIndex = cursor < tokens.length ? cursor : -1;
          }
          if (tokenIndex >= 0) {
            matches.push({ ...tokens[tokenIndex], index: segment.index });
            cursor = tokenIndex + 1;
          }
        });

        const matchesByNode = new Map();
        matches.forEach((match) => {
          if (!matchesByNode.has(match.node)) {
            matchesByNode.set(match.node, []);
          }
          matchesByNode.get(match.node).push(match);
        });
        matchesByNode.forEach((nodeMatches) => {
          nodeMatches
            .sort((left, right) => right.start - left.start)
            .forEach((match) => {
              const range = document.createRange();
              range.setStart(match.node, match.start);
              range.setEnd(match.node, match.end);
              const word = document.createElement('span');
              word.className = 'audio-word';
              word.dataset.audioWordIndex = String(match.index);
              range.surroundContents(word);
            });
        });
      });
    },
    activeWordAt(time) {
      let low = 0;
      let high = this.wordSegments.length - 1;
      let candidate = -1;
      while (low <= high) {
        const middle = Math.floor((low + high) / 2);
        if (this.wordSegments[middle].start_time <= time) {
          candidate = middle;
          low = middle + 1;
        } else {
          high = middle - 1;
        }
      }
      if (
        candidate >= 0 &&
        time <= this.wordSegments[candidate].end_time + 0.08
      ) {
        return candidate;
      }
      return -1;
    },
    clearActiveWord() {
      if (this.activeWordIndex < 0) return;
      const previous = document.querySelector(
        `[data-audio-word-index='${this.activeWordIndex}']`
      );
      previous?.classList.remove('audio-word--active');
      previous?.removeAttribute('aria-current');
      this.activeWordIndex = -1;
    },
    updateActiveWord(time) {
      const nextIndex = this.activeWordAt(time);
      if (nextIndex === this.activeWordIndex) return;
      this.clearActiveWord();
      if (nextIndex < 0) return;

      this.activeWordIndex = nextIndex;
      const active = document.querySelector(
        `[data-audio-word-index='${nextIndex}']`
      );
      if (!active) {
        this.scrollToSegment(this.wordSegments[nextIndex].id);
        return;
      }
      active.classList.add('audio-word--active');
      active.setAttribute('aria-current', 'true');
      if (this.enableScrolling && this.isPlaying) {
        this.followActiveWord(active);
      }
    },
    followActiveWord(element) {
      const rect = element.getBoundingClientRect();
      const controlsHeight =
        this.$el?.querySelector('.controls.fixed-controls')?.offsetHeight || 0;
      const safeTop = window.innerHeight * 0.24;
      const safeBottom = window.innerHeight - controlsHeight - 48;
      if (rect.top < safeTop || rect.bottom > safeBottom) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    },
    scrollToSegment(segmentId) {
      if (!this.enableScrolling) return;
      const element = document.querySelector(`[data-line-id='${segmentId}']`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    },
    toggleExpanded() {
      this.isExpanded = !this.isExpanded;
      this.$nextTick(() => this.emitVisibility());
    },
    checkMobile() {
      this.isMobile = window.innerWidth <= 768;
      // Always show full player on desktop
      if (!this.isMobile) {
        this.isExpanded = true;
      }
      this.$nextTick(() => this.emitVisibility());
    },
    formatTime(seconds) {
      if (!seconds || isNaN(seconds)) return '0:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
  },
  computed: {
    formattedCurrentTime() {
      return this.formatTime(this.currentTime);
    },
    formattedDuration() {
      return this.formatTime(this.duration);
    },
    formattedRemainingTime() {
      return this.formatTime(Math.max(0, this.duration - this.currentTime));
    },
    currentSectionName() {
      if (!this.trackSegments.length) {
        return this.office.replaceAll('_', ' ');
      }
      let current = this.trackSegments[0];
      for (const segment of this.trackSegments) {
        if (segment.start_time > this.currentTime) break;
        current = segment;
      }
      return current.name;
    },
    progressPercentage() {
      if (!this.duration) return 0;
      return (this.currentTime / this.duration) * 100;
    },
    // FontAwesome icons
    faPlay() {
      return faPlay;
    },
    faPause() {
      return faPause;
    },
    faChevronUp() {
      return faChevronUp;
    },
    faChevronDown() {
      return faChevronDown;
    },
    faBackwardStep() {
      return faBackwardStep;
    },
    faForwardStep() {
      return faForwardStep;
    },
    faVolumeHigh() {
      return faVolumeHigh;
    },
    faVolumeMute() {
      return faVolumeMute;
    },
    faXmark() {
      return faXmark;
    },
  },
  watch: {
    isPlaying(newVal) {
      // Auto-expand when audio starts playing (mobile only)
      if (newVal && !this.isExpanded && this.isMobile) {
        this.isExpanded = true;
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
  margin-bottom: 120px; /* Default for desktop (always full) */
  transition: margin-bottom 0.3s ease;
}

/* Mobile gets smaller margin when collapsed */
@media (max-width: 768px) {
  .audio-list {
    margin-bottom: 60px; /* Smaller for mini player on mobile */
  }
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
  transition: all 0.3s ease; /* Smooth transition for expand/collapse */
}

.menu-and-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
  touch-action: manipulation;
}

/* Mini Player Styles (Collapsed State) */
.mini-player {
  cursor: pointer;
  padding: 8px 12px;
  background: var(--color-bg);
  border-radius: 8px;
  transition: all 0.2s ease;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
}

.mini-player:hover {
  background: rgba(0, 0, 0, 0.05);
}

.mini-player:active {
  transform: scale(0.99);
}

.mini-player-content {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
}

.mini-player-icon {
  font-size: 20px;
  min-width: 24px;
  text-align: center;
  color: var(--accent-color);
}

.mini-player-text {
  flex: 1;
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-player-chapters {
  font-weight: 400;
  opacity: 0.7;
  font-size: 14px;
}

.mini-player-time {
  font-weight: 400;
  opacity: 0.7;
  font-size: 13px;
  margin-left: 4px;
}

.mini-player-expand {
  font-size: 20px;
  opacity: 0.5;
  transition: opacity 0.2s ease;
}

.mini-player:hover .mini-player-expand {
  opacity: 1;
}

/* Mini Player Progress Bar */
.mini-player-progress {
  margin-top: 8px;
  height: 3px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.mini-player-progress-bar {
  height: 100%;
  background: var(--accent-color);
  transition: width 0.3s ease;
  border-radius: 2px;
}

/* Player Header (Expanded State - Mobile Only) */
.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding: 0 4px;
}

/* Hide player header on desktop */
@media (min-width: 769px) {
  .player-header {
    display: none;
  }
}

.player-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  opacity: 0.7;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.collapse-button {
  background: transparent;
  border: none;
  font-size: 24px;
  padding: 0;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--color-text);
  opacity: 0.6;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}

.collapse-button:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.05);
}

.collapse-button:active {
  transform: scale(0.95);
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

.play-button,
.pause-button {
  --el-button-bg-color: var(--accent-color);
  --el-button-border-color: var(--accent-color);
  --el-button-text-color: var(--accent-contrast);
  --el-button-hover-bg-color: var(--accent-color);
  --el-button-hover-border-color: var(--accent-color);
  --el-button-hover-text-color: var(--accent-contrast);
  --el-button-active-bg-color: var(--accent-color);
  --el-button-active-border-color: var(--accent-color);
  --el-button-active-text-color: var(--accent-contrast);
  --el-button-disabled-bg-color: var(--accent-color);
  --el-button-disabled-border-color: var(--accent-color);
  --el-button-disabled-text-color: var(--accent-contrast);
}

.play-button:not(.is-disabled):hover,
.pause-button:not(.is-disabled):hover {
  filter: brightness(0.95);
}

.play-button.is-disabled,
.pause-button.is-disabled {
  opacity: 0.55;
}

.play-button :deep(.button-icon),
.play-button :deep(.button-text),
.pause-button :deep(.button-icon),
.pause-button :deep(.button-text) {
  color: var(--accent-contrast);
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
.segment-selector-wrap {
  position: relative;
  flex: 1;
  min-width: 0;
  touch-action: manipulation;
}

.segment-selector {
  width: 100%;
  min-width: 0;
  touch-action: manipulation;
}

/* Spinner shown over the "Jump to" control while a long-office seek settles */
.seeking-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: var(--el-border-radius-base, 4px);
  background: var(--color-bg);
  border: 1px solid var(--el-border-color, #dcdfe6);
  color: var(--color-text);
  cursor: progress;
  z-index: 2;
}

.seeking-text {
  font-size: 14px;
  font-weight: 500;
  opacity: 0.85;
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
  --el-switch-on-color: var(--accent-color);
  --el-switch-border-color: var(--accent-color);
}

.scroll-toggle :deep(.el-switch__label),
.scroll-toggle :deep(span) {
  font-size: 14px !important;
  touch-action: manipulation !important;
  user-select: none;
}

.scroll-toggle :deep(.el-switch__label) {
  color: var(--el-text-color-regular);
  transition: color 0.2s ease;
}

.scroll-toggle :deep(.el-switch__label.is-active) {
  color: var(--accent-color);
  font-weight: 600;
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

  .segment-selector-wrap {
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

/* ── Dismiss (X) button ── */
.dismiss-button {
  background: transparent;
  border: none;
  font-size: 18px;
  padding: 0;
  width: 32px;
  height: 32px;
  min-width: 32px;
  border-radius: 6px;
  cursor: pointer;
  color: var(--color-text);
  opacity: 0.5;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}

.dismiss-button:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.08);
}

.dismiss-button:active {
  transform: scale(0.92);
}

/* Mini-player variant sits inline after the expand chevron */
.dismiss-button--mini {
  margin-left: 12px;
  padding-left: 12px;
  border-left: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 0;
  height: 24px;
}

:deep(.dark) .dismiss-button--mini {
  border-left-color: rgba(255, 255, 255, 0.1);
}

/* Desktop variant — push to far right flex-end, ensure it doesn't overlap content */
.dismiss-button--desktop {
  margin-left: auto; /* Push to right in flex container */
  position: relative; /* Remove absolute positioning */
  top: auto;
  right: auto;
  transform: none;
  order: 10; /* Ensure it's last visually if needed */
}

.player-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 12ui direction C: warm book paper, restrained gold, quiet green transport. */
.controls.fixed-controls {
  left: 50%;
  right: auto;
  bottom: max(12px, env(safe-area-inset-bottom));
  width: min(calc(100% - 24px), 1120px) !important;
  padding: 14px 18px;
  transform: translateX(-50%);
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--color-text) 14%, transparent);
  border-radius: 16px;
  background: color-mix(in srgb, var(--color-bg) 96%, transparent);
  box-shadow:
    0 18px 50px rgba(48, 40, 28, 0.16),
    0 2px 8px rgba(48, 40, 28, 0.08);
  backdrop-filter: blur(18px);
}

.player-shell {
  display: grid;
  grid-template-columns: minmax(140px, 190px) minmax(0, 1fr);
  align-items: center;
  gap: 22px;
  width: 100%;
}

.player-header {
  display: flex !important;
  align-items: center;
  justify-content: space-between;
  min-width: 0;
  margin: 0;
  padding: 0 16px 0 2px;
  border-right: 1px solid color-mix(in srgb, var(--color-text) 10%, transparent);
}

.player-now,
.mini-player-text {
  display: flex;
  min-width: 0;
  flex-direction: column;
  text-align: left;
}

.player-kicker,
.mini-player-eyebrow,
.control-label {
  color: color-mix(in srgb, var(--color-text) 58%, transparent);
  font-size: 0.68rem;
  font-weight: 650;
  letter-spacing: 0.12em;
  line-height: 1.2;
  text-transform: uppercase;
}

.player-section {
  display: block;
  margin-top: 5px;
  overflow: hidden;
  color: var(--color-text);
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 1.08rem;
  font-weight: 500;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.player-main {
  display: grid;
  grid-template-columns: auto minmax(180px, 1fr) auto;
  align-items: center;
  gap: 22px;
  min-width: 0;
}

.transport-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.primary-play-button,
.skip-button,
.scroll-control {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 0;
  cursor: pointer;
}

.primary-play-button {
  width: 54px;
  height: 54px;
  flex: 0 0 54px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--accent-color) 72%, #315844);
  color: var(--accent-contrast);
  font-size: 1.1rem;
  box-shadow: 0 6px 18px
    color-mix(in srgb, var(--accent-color) 26%, transparent);
  transition:
    transform 160ms ease,
    filter 160ms ease;
}

.primary-play-button:hover {
  filter: brightness(1.06);
  transform: translateY(-1px);
}

.primary-play-button:active {
  transform: scale(0.96);
}

.skip-button {
  position: relative;
  width: 38px;
  height: 38px;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  color: color-mix(in srgb, var(--color-text) 72%, transparent);
  font-size: 0.9rem;
}

.skip-button span {
  position: absolute;
  bottom: 2px;
  font-size: 0.48rem !important;
  font-weight: 700;
}

.skip-button:hover {
  background: color-mix(in srgb, var(--color-text) 7%, transparent);
  color: var(--color-text);
}

.timeline {
  min-width: 0;
}

.timeline-slider {
  width: 100%;
  height: 30px;
  margin: 0;
  appearance: none;
  background: transparent;
  cursor: pointer;
}

.timeline-slider::-webkit-slider-runnable-track {
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(
    to right,
    var(--accent-color) 0 var(--progress),
    color-mix(in srgb, var(--color-text) 16%, transparent) var(--progress) 100%
  );
}

.timeline-slider::-moz-range-track {
  height: 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--color-text) 16%, transparent);
}

.timeline-slider::-moz-range-progress {
  height: 4px;
  border-radius: 999px;
  background: var(--accent-color);
}

.timeline-slider::-webkit-slider-thumb {
  width: 16px;
  height: 16px;
  margin-top: -6px;
  appearance: none;
  border: 2px solid var(--color-bg);
  border-radius: 50%;
  background: var(--accent-color);
  box-shadow: 0 1px 5px rgba(50, 40, 24, 0.28);
}

.timeline-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-bg);
  border-radius: 50%;
  background: var(--accent-color);
}

.timeline-times {
  display: flex;
  justify-content: space-between;
  margin-top: -3px;
  color: color-mix(in srgb, var(--color-text) 54%, transparent);
  font-size: 0.7rem;
  font-variant-numeric: tabular-nums;
}

.utility-controls {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.utility-controls .speed-selector {
  width: 76px;
  min-width: 76px;
}

.utility-controls .segment-selector-wrap {
  display: grid;
  grid-template-columns: auto minmax(104px, 160px);
  align-items: center;
  gap: 7px;
  max-width: none;
}

.scroll-control {
  min-height: 40px;
  gap: 6px;
  padding: 0 12px;
  border: 1px solid color-mix(in srgb, var(--color-text) 12%, transparent);
  border-radius: 11px;
  background: color-mix(in srgb, var(--color-bg) 80%, transparent);
  color: color-mix(in srgb, var(--color-text) 72%, transparent);
  font-size: 0.78rem !important;
  white-space: nowrap;
}

.scroll-control--active {
  border-color: color-mix(in srgb, var(--accent-color) 34%, transparent);
  background: color-mix(in srgb, var(--accent-color) 17%, var(--color-bg));
  color: var(--color-text);
}

.scroll-control-mark {
  color: var(--accent-color);
  font-size: 1rem !important;
}

.availability-note,
.player-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.mini-player {
  width: 100%;
  padding: 3px 2px;
  border: 0;
}

.mini-player-content {
  gap: 10px;
}

.mini-player-icon {
  display: grid;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 50%;
  background: color-mix(in srgb, var(--accent-color) 16%, var(--color-bg));
}

.mini-player-time {
  margin-left: auto;
  font-variant-numeric: tabular-nums;
}

:global(.audio-word) {
  position: relative;
  margin-inline: -0.015em;
  padding-inline: 0.015em;
  border-radius: 0.2em;
  transition:
    color 100ms ease,
    background-color 140ms ease,
    box-shadow 140ms ease;
}

:global(.audio-word--active) {
  background: color-mix(in srgb, var(--accent-color) 22%, transparent);
  box-shadow:
    0 0 0 0.13em color-mix(in srgb, var(--accent-color) 22%, transparent),
    inset 0 -0.08em 0 color-mix(in srgb, var(--accent-color) 65%, transparent);
  color: color-mix(in srgb, var(--color-text) 88%, var(--accent-color));
}

@media (prefers-reduced-motion: reduce) {
  :global(.audio-word),
  .primary-play-button {
    transition: none;
  }
}

@media (max-width: 900px) {
  .player-shell {
    grid-template-columns: 130px minmax(0, 1fr);
    gap: 14px;
  }

  .player-main {
    grid-template-columns: auto minmax(150px, 1fr);
    gap: 14px;
  }

  .utility-controls {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .controls.fixed-controls {
    bottom: max(8px, env(safe-area-inset-bottom));
    width: calc(100% - 16px) !important;
    padding: 12px 14px;
    border-radius: 14px;
  }

  .player-shell {
    display: block;
  }

  .player-header {
    margin-bottom: 10px;
    padding: 0 0 9px;
    border-right: 0;
    border-bottom: 1px solid
      color-mix(in srgb, var(--color-text) 9%, transparent);
  }

  .player-main {
    grid-template-columns: auto minmax(0, 1fr);
    gap: 10px 14px;
  }

  .primary-play-button {
    width: 50px;
    height: 50px;
    flex-basis: 50px;
  }

  .utility-controls {
    display: grid;
    grid-template-columns: 72px minmax(0, 1fr) auto;
    width: 100%;
  }

  .utility-controls .speed-selector {
    width: 72px;
    min-width: 72px;
  }

  .utility-controls .segment-selector-wrap {
    display: block;
    min-width: 0;
  }

  .control-label {
    display: none;
  }

  .scroll-control {
    min-width: 44px;
    padding: 0 10px;
    font-size: 0 !important;
  }

  .scroll-control-mark {
    font-size: 1.05rem !important;
  }
}
</style>
