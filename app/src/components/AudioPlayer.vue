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
        <!-- Dismiss button (not-playing state only) -->
        <button
          v-if="!isPlaying"
          class="dismiss-button"
          title="Hide audio controls"
          @click.stop="$emit('dismiss-audio')"
        >
          <font-awesome-icon :icon="faXmark" />
        </button>
      </div>

      <div v-if="isEsvOrKjv" class="menu-and-buttons">
        <!-- Mini Player View (Mobile Only - Collapsed) -->
        <div
          v-if="isMobile && !isExpanded"
          class="mini-player"
          @click="toggleExpanded"
        >
          <div class="mini-player-content">
            <span class="mini-player-icon">
              <font-awesome-icon
                :icon="isPlaying && !isPaused ? faPause : faPlay"
              />
            </span>
            <span class="mini-player-text">
              <template v-if="isPlaying && !isPaused">
                Now Playing
                <span class="mini-player-time">
                  {{ formattedCurrentTime }} / {{ formattedDuration }}
                </span>
              </template>
              <template v-else> Audio Available </template>
            </span>
            <span class="mini-player-expand">
              <font-awesome-icon :icon="faChevronUp" />
            </span>
            <!-- Dismiss X on mini player (only when not playing) -->
            <button
              v-if="!isPlaying"
              class="dismiss-button dismiss-button--mini"
              title="Hide audio controls"
              @click.stop="$emit('dismiss-audio')"
            >
              <font-awesome-icon :icon="faXmark" />
            </button>
          </div>
          <!-- Progress bar when playing -->
          <div v-if="isPlaying && !isPaused" class="mini-player-progress">
            <div
              class="mini-player-progress-bar"
              :style="{ width: progressPercentage + '%' }"
            ></div>
          </div>
        </div>

        <!-- Full Player View (Always on Desktop, Expandable on Mobile) -->
        <template v-else>
          <div v-if="isMobile" class="player-header">
            <span class="player-title">Audio Player</span>
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
                class="collapse-button"
                @click="toggleExpanded"
                title="Minimize"
              >
                <font-awesome-icon :icon="faChevronDown" />
              </button>
            </div>
          </div>
          <div class="button-row">
            <el-button-group v-if="audioReady" class="playback-buttons">
              <el-button
                size="large"
                type="primary"
                :disabled="isPlaying && !isPaused"
                @click="startAudio"
                class="play-button"
              >
                <span class="button-icon">
                  <font-awesome-icon :icon="faPlay" />
                </span>
                <span class="button-text">Play</span>
              </el-button>
              <el-button
                size="large"
                type="primary"
                :disabled="!isPlaying"
                @click="pauseAudio"
                class="pause-button"
              >
                <span class="button-icon">
                  <font-awesome-icon :icon="faPause" />
                </span>
                <span class="button-text">Pause</span>
              </el-button>
            </el-button-group>
            <Loading v-if="loading" :small="true" />
            <span v-if="playbackError" role="status" class="audio-error">
              {{ playbackError }}
              <button type="button" @click="retryAudio">Retry audio</button>
            </span>

            <!-- Desktop dismiss button (inline in button row) -->
            <button
              v-if="!isMobile && !isPlaying"
              class="dismiss-button dismiss-button--desktop"
              title="Hide audio controls"
              @click.stop="$emit('dismiss-audio')"
            >
              <font-awesome-icon :icon="faXmark" />
            </button>
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
            <div class="segment-selector-wrap">
              <el-select
                v-model="currentTrackSegment"
                class="segment-selector"
                placeholder="Jump to..."
                :disabled="seeking"
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
            <el-switch
              v-model="enableScrolling"
              active-text="Scroll"
              inactive-text="No Scroll"
              class="scroll-toggle"
            ></el-switch>
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
      seeking: false, // true while a "Jump to" seek is waiting to become reachable
      trackSegments: [],
      detailedSegments: [],
      loading: true,
      audioElement: null,
      playbackError: '',
      pendingResumeTime: null,
      playbackRequested: false,
      playAttempt: 0,
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
      // Audio has no constructor options argument. Subscribe before loading
      // so cached media events cannot race past the handlers.
      this.audioElement = new Audio();
      this.audioElement.preload = 'auto';
      this.audioElement.src = this.audio[0] || '';
      this.mediaListeners = {
        canplay: this.handleCanPlay,
        canplaythrough: this.handleCanPlay,
        timeupdate: this.handleTimeUpdate,
        ended: this.handleEnded,
        loadedmetadata: this.handleMetadata,
        durationchange: this.handleMetadata,
        progress: this.restorePosition,
        play: this.handlePlay,
        playing: this.handlePlaying,
        pause: this.handlePause,
        waiting: this.handleWaiting,
        stalled: this.handleStalled,
        error: this.handleAudioError,
        ratechange: this.updateMediaPosition,
      };
      for (const [event, listener] of Object.entries(this.mediaListeners)) {
        this.audioElement.addEventListener(event, listener);
      }
      this.setupMediaSession();
      document.addEventListener(
        'visibilitychange',
        this.handleVisibilityChange
      );
      this.audioElement.load();
      if (this.audioElement.readyState >= 3) this.loading = false;

      this.trackSegments = this.audio[2];
      this.detailedSegments = this.audio[3];
    }

    this.$nextTick(() => this.emitVisibility());
  },
  beforeUnmount() {
    this.destroyed = true;
    this.cancelTrackSeek?.();
    this.playbackRequested = false;
    document.removeEventListener(
      'visibilitychange',
      this.handleVisibilityChange
    );
    window.removeEventListener('resize', this.checkMobile);
    window.visualViewport?.removeEventListener('resize', this.emitVisibility);
    window.visualViewport?.removeEventListener('scroll', this.emitVisibility);
    if (this.audioElement) {
      for (const [event, listener] of Object.entries(
        this.mediaListeners || {}
      )) {
        this.audioElement.removeEventListener(event, listener);
      }
      this.audioElement.pause();
      this.audioElement.removeAttribute('src');
      this.audioElement.load();
    }
    this.clearMediaSession();
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
      if (!this.audioElement) return;
      this.playbackError = '';
      const attempt = ++this.playAttempt;
      this.playbackRequested = true;
      this.loading = this.audioElement.readyState < 3;
      // Call play directly in the user gesture for mobile autoplay policies.
      // Media events, rather than optimistic clicks, determine playing state.
      try {
        const promise = this.audioElement.play();
        promise?.catch((error) => {
          if (
            this.destroyed ||
            !this.playbackRequested ||
            attempt !== this.playAttempt
          )
            return;
          this.playbackRequested = false;
          this.isPlaying = false;
          this.isPaused = true;
          this.loading = false;
          this.isExpanded = true;
          this.playbackError =
            error.name === 'NotAllowedError'
              ? 'Playback was interrupted. Press Play to continue.'
              : 'Audio could not start. Please retry.';
          this.updateMediaPosition();
        });
      } catch {
        this.handleAudioError();
      }
    },
    pauseAudio() {
      this.cancelTrackSeek?.();
      this.playAttempt += 1;
      this.playbackRequested = false;
      this.pendingResumeTime = null;
      this.audioElement?.pause();
      this.handlePause();
    },
    stopAudio() {
      this.pauseAudio();
      if (this.audioElement) this.audioElement.currentTime = 0;
      this.currentTime = 0;
      this.isPaused = false;
      this.playbackError = '';
      this.updateMediaPosition();
    },
    handlePlay() {
      this.playbackRequested = true;
      this.isPlaying = true;
      this.isPaused = false;
      this.updateMediaPosition();
    },
    handlePlaying() {
      this.handlePlay();
      if (!this.hasEmittedPlay) {
        this.hasEmittedPlay = true;
        this.$emit('audio-play');
      }
      this.loading = false;
      this.playbackError = '';
    },
    handlePause() {
      this.cancelTrackSeek?.();
      this.isPlaying = false;
      this.isPaused = true;
      this.playbackRequested = false;
      this.loading = false;
      this.updateMediaPosition();
    },
    handleEnded() {
      this.stopAudio();
    },
    handleCanPlay() {
      this.loading = false;
      this.restorePosition();
    },
    handleMetadata() {
      const duration = this.audioElement?.duration;
      this.duration = Number.isFinite(duration) ? duration : 0;
      this.restorePosition();
      this.updateMediaPosition();
    },
    handleWaiting() {
      if (this.playbackRequested) this.loading = true;
    },
    handleStalled() {
      if (!this.playbackRequested) return;
      this.loading = true;
      this.isExpanded = true;
      this.playbackError =
        'Audio is buffering. Check your connection if it does not resume.';
    },
    handleAudioError() {
      if (!this.audioElement) return;
      this.currentTime = this.audioElement.currentTime || this.currentTime;
      this.playbackRequested = false;
      this.isPlaying = false;
      this.isPaused = true;
      this.loading = false;
      this.isExpanded = true;
      this.playbackError =
        'Audio stopped loading. Retry to continue from your place.';
      this.updateMediaPosition();
    },
    retryAudio() {
      if (!this.audioElement) return;
      this.cancelTrackSeek?.();
      this.pendingResumeTime =
        this.pendingResumeTime ??
        (this.audioElement.currentTime || this.currentTime);
      this.audioElement.load();
      this.startAudio();
    },
    restorePosition() {
      if (this.pendingResumeTime === null || !this.audioElement) return;
      const duration = this.audioElement.duration;
      if (!Number.isFinite(duration) || duration <= 0) return;
      try {
        const target = Math.min(
          this.pendingResumeTime,
          Math.max(0, duration - 0.05)
        );
        this.audioElement.currentTime = target;
        // Some engines silently clamp seeks to the buffered end. Keep the
        // target for a later progress/canplay event until it actually lands.
        if (Math.abs(this.audioElement.currentTime - target) < 0.25) {
          this.pendingResumeTime = null;
        }
      } catch {
        // Retry at canplay/progress when the media is seekable.
      }
    },
    handleVisibilityChange() {
      if (document.visibilityState !== 'visible' || !this.audioElement) return;
      // Respect a user/OS pause; foregrounding must not restart playback.
      this.isPlaying = !this.audioElement.paused && !this.audioElement.ended;
      this.isPaused = this.audioElement.paused;
      this.currentTime = this.audioElement.currentTime;
      this.updateMediaPosition();
    },
    setupMediaSession() {
      if (!navigator.mediaSession) return;
      const session = navigator.mediaSession;
      if (window.MediaMetadata) {
        session.metadata = new window.MediaMetadata({
          title: this.office.replace(/_/g, ' '),
          artist: 'The Daily Office',
        });
      }
      const actions = {
        play: this.startAudio,
        pause: this.pauseAudio,
        stop: this.stopAudio,
        seekbackward: (details) =>
          this.seekTo(
            this.audioElement.currentTime - (details.seekOffset || 10)
          ),
        seekforward: (details) =>
          this.seekTo(
            this.audioElement.currentTime + (details.seekOffset || 10)
          ),
        seekto: (details) => this.seekTo(details.seekTime),
      };
      this.mediaActions = [];
      for (const [action, handler] of Object.entries(actions)) {
        try {
          session.setActionHandler(action, handler);
          this.mediaActions.push(action);
        } catch {
          // Browsers support different subsets of Media Session actions.
        }
      }
    },
    clearMediaSession() {
      if (!navigator.mediaSession) return;
      for (const action of this.mediaActions || []) {
        try {
          navigator.mediaSession.setActionHandler(action, null);
        } catch {
          // A WebView may lose support during activity shutdown.
        }
      }
      navigator.mediaSession.metadata = null;
      navigator.mediaSession.playbackState = 'none';
      try {
        navigator.mediaSession.setPositionState?.();
      } catch {
        // Position state is optional in older WebViews.
      }
    },
    updateMediaPosition() {
      if (!navigator.mediaSession || !this.audioElement) return;
      navigator.mediaSession.playbackState = this.isPlaying
        ? 'playing'
        : 'paused';
      const { duration, currentTime, playbackRate } = this.audioElement;
      if (!Number.isFinite(duration) || duration <= 0) return;
      try {
        navigator.mediaSession.setPositionState?.({
          duration,
          position: Math.max(0, Math.min(currentTime, duration)),
          playbackRate,
        });
      } catch {
        // Partial Media Session support must never stop playback.
      }
    },
    seekTo(value) {
      if (!this.audioElement || !Number.isFinite(value)) return;
      this.cancelTrackSeek?.();
      const duration = this.audioElement.duration;
      if (!Number.isFinite(duration) || duration <= 0) {
        this.pendingResumeTime = Math.max(0, value);
        return;
      }
      this.pendingResumeTime = Math.max(0, Math.min(value, duration));
      this.restorePosition();
      this.currentTime = this.audioElement.currentTime;
      this.updateMediaPosition();
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

      this.cancelTrackSeek?.();
      this.pendingResumeTime = null;
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
      let expiryTimer;
      // Only surface the spinner if the seek can't land quickly, so short
      // offices (Compline) never flash an indicator for an instant jump.
      const spinnerTimer = window.setTimeout(() => {
        if (!settled) this.seeking = true;
      }, 250);
      const cleanup = () => {
        if (settled) return;
        settled = true;
        window.clearTimeout(spinnerTimer);
        window.clearTimeout(expiryTimer);
        this.cancelTrackSeek = null;
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

      this.cancelTrackSeek = cleanup;
      el.addEventListener('loadedmetadata', trySeek);
      el.addEventListener('durationchange', trySeek);
      el.addEventListener('canplay', trySeek);
      el.addEventListener('progress', trySeek);
      el.addEventListener('seeked', onSeeked);
      // Safety valve so listeners don't linger forever if the seek never lands.
      expiryTimer = window.setTimeout(cleanup, 15000);

      // Play first to satisfy iOS's user-activation requirement, then seek.
      this.startAudio();
      trySeek();
    },
    handleTimeUpdate() {
      if (!this.audioElement) return;

      this.currentTime = this.audioElement.currentTime;
      this.updateMediaPosition();

      if (document.visibilityState === 'hidden') return;
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
</style>
