<template>
  <div class="audio-player">
    <section
      class="controls fixed-controls"
      aria-label="Daily Office audio"
      @keydown.esc="closePanels(true)"
    >
      <div v-if="!isEsvOrKjv || !isWithinSevenDays" class="availability-note">
        <UiIcon name="headphones" class="note-icon" />
        <div class="note-text">
          <p v-if="!isEsvOrKjv">
            Audio is available with the English Standard Version (ESV) or King
            James Version (KJV). <a href="/settings">Change settings</a>
          </p>
          <p v-if="!isWithinSevenDays">
            Audio is available from three days ago through nine days ahead.
            <a href="/">Go to today</a>
          </p>
        </div>
        <button
          v-if="!isPlaying"
          class="dismiss-button"
          type="button"
          aria-label="Hide audio controls"
          title="Hide audio controls"
          @click="$emit('dismiss-audio')"
        >
          <UiIcon name="close" />
        </button>
      </div>

      <div v-else class="player">
        <div v-if="playbackError" role="status" class="audio-error">
          <span>{{ playbackError }}</span>
          <button type="button" @click="retryAudio">Retry audio</button>
        </div>

        <div class="player-bar">
          <div class="timeline">
            <span class="time" aria-hidden="true">{{
              formattedCurrentTime
            }}</span>
            <input
              class="timeline-slider"
              type="range"
              min="0"
              :max="duration || 0"
              step="0.01"
              :value="currentTime"
              :disabled="!duration"
              aria-label="Audio progress"
              :aria-valuetext="`${formattedCurrentTime} of ${formattedDuration}`"
              :style="{ '--progress': progressPercentage + '%' }"
              @input="seekToTime"
            />
            <span class="time time--remaining" aria-hidden="true"
              >-{{ formattedRemainingTime }}</span
            >
          </div>

          <button
            class="skip-button skip-button--back"
            type="button"
            title="Back 15 seconds"
            aria-label="Back 15 seconds"
            :disabled="!audioReady"
            @click="skipBy(-15)"
          >
            <svg class="skip-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path class="skip-arc" d="M12 3.75A8.25 8.25 0 1 1 3.75 12" />
              <path class="skip-arc" d="M14.5 1.25 12 3.75l2.5 2.5" />
              <text x="12" y="15.4" text-anchor="middle">15</text>
            </svg>
          </button>
          <button
            class="primary-play-button"
            :class="{ 'is-buffering': isBuffering }"
            type="button"
            :disabled="!audioReady"
            :aria-label="isPlaying ? 'Pause audio' : 'Play audio'"
            @click="togglePlayback"
          >
            <UiIcon
              :name="isPlaying ? 'pause' : 'play'"
              :class="{ 'icon-play': !isPlaying }"
            />
          </button>
          <button
            class="skip-button skip-button--forward"
            type="button"
            title="Forward 15 seconds"
            aria-label="Forward 15 seconds"
            :disabled="!audioReady"
            @click="skipBy(15)"
          >
            <svg class="skip-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path class="skip-arc" d="M12 3.75A8.25 8.25 0 1 0 20.25 12" />
              <path class="skip-arc" d="M9.5 1.25 12 3.75l-2.5 2.5" />
              <text x="12" y="15.4" text-anchor="middle">15</text>
            </svg>
          </button>

          <div class="now-playing">
            <button
              ref="sectionsControl"
              class="section-button"
              type="button"
              :disabled="!trackSegments.length"
              :aria-label="`Jump to section. Now: ${currentSectionName}`"
              aria-haspopup="true"
              :aria-expanded="showSections"
              aria-controls="audio-section-menu"
              @click="togglePanel('sections')"
            >
              <span class="section-caption">
                <span v-if="transientStatus">{{ transientStatus }}</span>
                <template v-else>
                  <span class="caption-status">{{ playbackStatus }}</span>
                  <span class="caption-time"
                    >{{ formattedCurrentTime }} / {{ formattedDuration }}</span
                  >
                </template>
              </span>
              <span class="section-name">
                <span class="section-name-text" :title="currentSectionName">{{
                  currentSectionName
                }}</span>
                <UiIcon
                  v-if="trackSegments.length"
                  class="section-chevron"
                  name="chevron-up"
                />
              </span>
            </button>
            <div
              v-show="showSections"
              id="audio-section-menu"
              class="popover section-menu"
              role="group"
              aria-label="Jump to section"
              @keydown="handleMenuKeydown"
            >
              <p class="popover-title">Jump to section</p>
              <ul ref="sectionList">
                <li
                  v-for="(segment, index) in trackSegments"
                  :key="segment.start_time"
                >
                  <button
                    class="section-item"
                    :class="{
                      'section-item--current': index === currentSectionIndex,
                    }"
                    type="button"
                    :aria-current="
                      index === currentSectionIndex ? 'true' : undefined
                    "
                    @click="jumpToSection(segment.start_time)"
                  >
                    <span class="section-item-name">{{ segment.name }}</span>
                    <span class="section-item-time">{{
                      formatTime(segment.start_time)
                    }}</span>
                  </button>
                </li>
              </ul>
            </div>
          </div>

          <div class="options-wrap">
            <button
              ref="preferencesControl"
              class="preferences-button"
              type="button"
              title="Listening options"
              aria-label="Listening options"
              aria-haspopup="true"
              :aria-expanded="showPreferences"
              aria-controls="audio-reading-preferences"
              @click="togglePanel('preferences')"
            >
              <UiIcon name="sliders" />
              <span v-if="playbackSpeed !== '1.0x'" class="speed-badge">{{
                speedLabel
              }}</span>
            </button>
            <div
              v-show="showPreferences"
              id="audio-reading-preferences"
              class="popover preferences-panel"
              role="group"
              aria-label="Listening options"
            >
              <div class="preference-row speed-control">
                <span class="preference-label" id="audio-speed-label"
                  >Speed</span
                >
                <div
                  class="stepper"
                  role="group"
                  aria-labelledby="audio-speed-label"
                >
                  <button
                    type="button"
                    aria-label="Slower"
                    :disabled="speedIndex <= 0"
                    @click="stepSpeed(-1)"
                  >
                    <UiIcon name="minus" />
                  </button>
                  <output class="speed-value" aria-live="polite">{{
                    speedLabel
                  }}</output>
                  <button
                    type="button"
                    aria-label="Faster"
                    :disabled="speedIndex >= speeds.length - 1"
                    @click="stepSpeed(1)"
                  >
                    <UiIcon name="plus" />
                  </button>
                </div>
              </div>

              <fieldset class="highlight-control">
                <legend class="preference-label">Highlight text</legend>
                <div class="segmented">
                  <label v-for="mode in highlightOptions" :key="mode.value">
                    <input
                      type="radio"
                      name="audio-highlight-mode"
                      :value="mode.value"
                      :checked="highlightMode === mode.value"
                      @change="changeHighlightMode(mode.value)"
                    />
                    <span>{{ mode.label }}</span>
                  </label>
                </div>
              </fieldset>

              <div class="preference-row">
                <span class="preference-label" id="audio-scroll-label"
                  >Auto-scroll
                  <small>Keep the spoken words in view</small></span
                >
                <button
                  class="scroll-control"
                  type="button"
                  role="switch"
                  :aria-checked="enableScrolling"
                  aria-labelledby="audio-scroll-label"
                  @click="toggleScrolling"
                >
                  <span class="switch-thumb"></span>
                </button>
              </div>

              <button
                v-if="!isPlaying"
                class="hide-player-button"
                type="button"
                @click="$emit('dismiss-audio')"
              >
                <UiIcon name="close" />
                <span>Hide audio player</span>
              </button>
            </div>
          </div>

          <button
            v-if="!isPlaying"
            class="dismiss-button"
            type="button"
            aria-label="Hide audio controls"
            title="Hide audio controls"
            @click="$emit('dismiss-audio')"
          >
            <UiIcon name="close" />
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import {
  beyondTrackEnd,
  endedEarly,
  freshTrackUrl,
  timelineEnd,
} from '@/helpers/audioTrack';
import { DynamicStorage } from '@/helpers/storage';

import UiIcon from '@/ui/UiIcon.vue';

const HIGHLIGHT_STORAGE_KEY = 'audioHighlightMode';
const SPEED_STORAGE_KEY = 'audioPlaybackSpeed';
const SCROLL_STORAGE_KEY = 'audioAutoScroll';
const highlightModes = ['word', 'sentence', 'off'];

// Wrap node.data[start, end) in `wrapper` without a Range. Every live Range
// is updated on each DOM mutation, so wrapping thousands of words through
// Range.surroundContents is quadratic and froze long offices for seconds.
// The original node keeps the text before `start`, so callers working from
// the end of a node backwards can keep using offsets into the original node.
function wrapText(node, start, end, wrapper) {
  const target = start > 0 ? node.splitText(start) : node;
  if (end - start < target.length) target.splitText(end - start);
  target.parentNode.insertBefore(wrapper, target);
  wrapper.appendChild(target);
}

export default {
  name: 'AudioPlayer',
  components: { UiIcon },
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
      highlightSegments: [],
      highlightMode: 'word',
      highlightModeChanged: false,
      lastFollowScrollAt: -Infinity,
      loading: true,
      audioElement: null,
      playbackError: '',
      trackIncomplete: false, // the file ends before its timeline; retry refetches it
      pendingResumeTime: null,
      playbackRequested: false,
      playAttempt: 0,
      playbackSpeed: '1.0x',
      speedChanged: false,
      enableScrolling: true,
      scrollingChanged: false,
      showPreferences: false,
      showSections: false,
      highlightOptions: [
        { value: 'word', label: 'Word' },
        { value: 'sentence', label: 'Sentence' },
        { value: 'off', label: 'Off' },
      ],
      currentTime: 0, // Current playback time
      duration: 0, // Total duration
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
    DynamicStorage.getItem(HIGHLIGHT_STORAGE_KEY).then((value) => {
      if (this.destroyed || this.highlightModeChanged) return;
      this.highlightMode = highlightModes.includes(value) ? value : 'word';
    });
    DynamicStorage.getItem(SPEED_STORAGE_KEY).then((value) => {
      if (this.destroyed || this.speedChanged) return;
      if (this.speeds.includes(value)) this.playbackSpeed = value;
      this.handleSpeedChange();
    });
    DynamicStorage.getItem(SCROLL_STORAGE_KEY).then((value) => {
      if (this.destroyed || this.scrollingChanged) return;
      if (value === 'true' || value === 'false') {
        this.enableScrolling = value === 'true';
      }
    });
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
      this.wordSegments = Array.isArray(this.audio[4]) ? this.audio[4] : [];
      this.$nextTick(() => this.prepareWordElements());
    }

    this.$nextTick(() => {
      this.emitVisibility();
      if (typeof window.ResizeObserver !== 'undefined') {
        this.controlsObserver = new window.ResizeObserver(() =>
          this.emitVisibility()
        );
        this.controlsObserver.observe(
          this.$el.querySelector('.fixed-controls')
        );
      }
    });
  },
  beforeUnmount() {
    this.destroyed = true;
    this.controlsObserver?.disconnect();
    this.stopHighlightClock();
    this.cancelTrackSeek?.();
    this.playbackRequested = false;
    document.removeEventListener('pointerdown', this.handleOutsidePointer);
    document.removeEventListener(
      'visibilitychange',
      this.handleVisibilityChange
    );
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
    this.clearActiveWord();
    this.clearMediaSession();
    this.emitVisibility(false);
  },
  methods: {
    emitVisibility(forceState) {
      const isVisible = forceState !== undefined ? forceState : true;
      const controls = this.$el?.querySelector('.controls.fixed-controls');
      const height =
        isVisible && controls
          ? Math.ceil(
              controls.offsetHeight +
                (parseFloat(window.getComputedStyle(controls).bottom) || 0)
            )
          : 0;
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
    togglePlayback() {
      if (this.isPlaying) {
        this.pauseAudio();
      } else {
        this.startAudio();
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
      this.clearActiveWord();
    },
    startHighlightClock() {
      this.stopHighlightClock();
      const tick = () => {
        if (this.destroyed || !this.isPlaying || !this.audioElement) return;
        if (document.visibilityState !== 'hidden') {
          this.updateActiveWord(this.audioElement.currentTime);
        }
        this.highlightFrame = window.requestAnimationFrame(tick);
      };
      this.highlightFrame = window.requestAnimationFrame(tick);
    },
    stopHighlightClock() {
      if (this.highlightFrame != null)
        window.cancelAnimationFrame(this.highlightFrame);
      this.highlightFrame = null;
    },
    handlePlay() {
      this.playbackRequested = true;
      this.isPlaying = true;
      this.startHighlightClock();
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
      this.stopHighlightClock();
      this.cancelTrackSeek?.();
      this.isPlaying = false;
      this.isPaused = true;
      this.playbackRequested = false;
      this.loading = false;
      this.updateMediaPosition();
    },
    handleEnded() {
      const el = this.audioElement;
      const endedAt = el ? el.currentTime || el.duration : 0;
      const expectedEnd = timelineEnd(
        this.trackSegments,
        this.detailedSegments
      );
      if (el && endedEarly(endedAt, expectedEnd)) {
        // The file is shorter than its timeline (a truncated copy). Keep the
        // place instead of rewinding, so a retry can carry on from here.
        this.pauseAudio();
        this.currentTime = endedAt;
        this.markTrackIncomplete('The audio ended early. Try again?');
        return;
      }
      this.stopAudio();
    },
    markTrackIncomplete(message) {
      this.trackIncomplete = true;
      this.playbackError = message;
      this.updateMediaPosition();
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
      if (this.trackIncomplete) {
        // Bypass the cached short copy and fetch the track again.
        this.trackIncomplete = false;
        this.audioElement.src = freshTrackUrl(this.audio[0]);
      }
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
      if (!this.audioElement) return;
      const rate = parseFloat(this.playbackSpeed.replace(/[^\d.]/g, ''));
      // load() (used by retry) resets playbackRate to defaultPlaybackRate.
      this.audioElement.defaultPlaybackRate = rate;
      this.audioElement.playbackRate = rate;
    },
    stepSpeed(direction) {
      const next = this.speeds[this.speedIndex + direction];
      if (!next) return;
      this.speedChanged = true;
      this.playbackSpeed = next;
      this.handleSpeedChange();
      DynamicStorage.setItem(SPEED_STORAGE_KEY, next).catch(() => {});
    },
    toggleScrolling() {
      this.scrollingChanged = true;
      this.enableScrolling = !this.enableScrolling;
      DynamicStorage.setItem(
        SCROLL_STORAGE_KEY,
        String(this.enableScrolling)
      ).catch(() => {});
    },
    jumpToSection(startTime) {
      this.closePanels(true);
      this.currentTrackSegment = startTime;
      this.handleTrackSegmentChange();
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
      const pastEndMessage = 'The audio ends before this section. Try again?';

      // A truncated file can't reach later sections; say so rather than
      // starting the office over from the top.
      if (beyondTrackEnd(target, el.duration)) {
        this.markTrackIncomplete(pastEndMessage);
        return;
      }

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
        if (settled) return;
        if (beyondTrackEnd(target, el.duration)) {
          // The length only became known after playback was requested.
          cleanup();
          this.pauseAudio();
          this.markTrackIncomplete(pastEndMessage);
          return;
        }
        if (!canReachTarget()) return;
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
      if (this.highlightSegments.length) {
        this.updateActiveWord(this.currentTime);
        return;
      }

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
    normalizeWord(word) {
      return (
        String(word || '')
          .normalize('NFKD')
          .replace(/\p{M}/gu, '')
          .toLocaleLowerCase()
          // The psalter prints the divine name using Unicode small-cap letters.
          .replace(/ᴏ/g, 'o')
          .replace(/ʀ/g, 'r')
          .replace(/ᴅ/g, 'd')
          .replace(/[^\p{L}\p{N}]/gu, '')
      );
    },
    // Look up line anchors and word spans from maps built once per pass,
    // instead of a document-wide query for every one of thousands of words.
    indexDocument() {
      this.lineAnchors = new Map();
      document.querySelectorAll('[data-line-id]').forEach((element) => {
        if (!this.lineAnchors.has(element.dataset.lineId)) {
          this.lineAnchors.set(element.dataset.lineId, element);
        }
      });
      this.wordElements = new Map();
      document
        .querySelectorAll('[data-audio-word-index]')
        .forEach((element) => {
          this.wordElements.set(element.dataset.audioWordIndex, element);
        });
    },
    findLineAnchor(lineId) {
      return this.lineAnchors?.get(lineId);
    },
    wordElement(index) {
      return this.wordElements?.get(String(index));
    },
    wordContainerForAnchor(anchor) {
      if (!anchor) return null;
      if (anchor.nextElementSibling) {
        const sibling = anchor.nextElementSibling;
        return sibling.querySelector('.column.right p') || sibling;
      }
      const parent = anchor.parentElement;
      if (!parent) return null;
      return Array.from(parent.children).find((element) =>
        element.matches('p, div')
      );
    },
    prepareWordElements() {
      if (!this.wordSegments.length) {
        this.prepareHighlightSegments();
        return;
      }
      this.indexDocument();
      const segmentsByLine = new Map();
      this.wordSegments.forEach((segment, index) => {
        if (!segment.id) return;
        if (!segmentsByLine.has(segment.id)) {
          segmentsByLine.set(segment.id, []);
        }
        segmentsByLine.get(segment.id).push({ ...segment, index });
      });

      segmentsByLine.forEach((segments, lineId) => {
        if (segments.every((segment) => this.wordElement(segment.index))) {
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
            tokenIndex = -1;
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
              const word = document.createElement('span');
              word.className = 'audio-word';
              word.dataset.audioWordIndex = String(match.index);
              wrapText(match.node, match.start, match.end, word);
            });
        });
      });
      this.prepareHighlightSegments();
    },
    changeHighlightMode(value) {
      this.highlightModeChanged = true;
      this.highlightMode = highlightModes.includes(value) ? value : 'word';
      // Storage may be unavailable; playback and the current choice still work.
      DynamicStorage.setItem(HIGHLIGHT_STORAGE_KEY, this.highlightMode).catch(
        () => {}
      );
    },
    prepareHighlightSegments() {
      this.clearActiveWord();
      this.indexDocument();
      document
        .querySelectorAll('[data-audio-highlight-index]')
        .forEach((element) => {
          element.removeAttribute('data-audio-highlight-index');
          element.classList.remove('audio-line');
          element.removeAttribute('aria-current');
        });
      this.highlightSegments = [];
      this.highlightElements = new Map();
      const byLine = new Map();
      this.wordSegments.forEach((word, index) => {
        if (!byLine.has(word.id)) byLine.set(word.id, []);
        byLine.get(word.id).push({ ...word, index });
      });
      // Shared clip boundaries can cover several lines. Distribute fallback
      // timing by text length, then retain measured word anchors where present.
      const clips = new Map();
      this.detailedSegments.forEach((segment) => {
        if (segment.highlighting_available === false) return;
        if (!clips.has(segment.start_time)) clips.set(segment.start_time, []);
        clips.get(segment.start_time).push(segment);
      });
      const starts = Array.from(clips.keys()).sort((a, b) => a - b);
      starts.forEach((start, clipIndex) => {
        const members = clips
          .get(start)
          .map((segment) => {
            const container = this.wordContainerForAnchor(
              this.findLineAnchor(segment.id)
            );
            return {
              ...segment,
              weight: container?.textContent.trim().length || 0,
            };
          })
          .filter((segment) => segment.weight);
        const total = members.reduce((sum, member) => sum + member.weight, 0);
        const end =
          members[0]?.end_time ?? starts[clipIndex + 1] ?? start + total / 12;
        let cursor = start;
        members.forEach((member) => {
          const next = cursor + ((end - start) * member.weight) / total;
          if (!byLine.has(member.id)) {
            byLine.set(member.id, [
              { start_time: cursor, end_time: next, estimated: true },
            ]);
          }
          cursor = next;
        });
      });
      byLine.forEach((words, id) => {
        const container = this.wordContainerForAnchor(this.findLineAnchor(id));
        if (!container) return;
        // ElevenLabs supplies direct character timestamps. Trace each measured
        // word instead of grouping these reliable anchors into a sentence.
        if (
          this.highlightMode !== 'sentence' &&
          words.every(
            (word) => word.provider === 'elevenlabs' && !word.estimated
          )
        ) {
          words.forEach((word) => {
            const element = this.wordElement(word.index);
            if (!element) return;
            const index = this.highlightSegments.length;
            this.registerHighlight(element, index);
            this.highlightSegments.push({
              index,
              exactWord: true,
              start_time: word.start_time,
              end_time: word.end_time,
            });
          });
          return;
        }
        const text = container.textContent;
        const isLongReading =
          this.highlightMode === 'sentence' ||
          (words.some((word) => word.speaker === 'reader') &&
            text.length > 180);
        const sentences = isLongReading
          ? Array.from(
              new Intl.Segmenter('en', { granularity: 'sentence' }).segment(
                text
              )
            )
          : [];
        if (
          isLongReading &&
          !container.querySelector('[data-audio-sentence]')
        ) {
          const walker = document.createTreeWalker(
            container,
            window.NodeFilter.SHOW_TEXT
          );
          const nodes = [];
          let offset = 0;
          let node;
          while ((node = walker.nextNode())) {
            nodes.push({ node, offset });
            offset += node.length;
          }
          // Wrap each text-node fragment separately to preserve inline markup.
          nodes.forEach(({ node, offset }) => {
            sentences
              .slice()
              .reverse()
              .forEach((sentence, reverseIndex) => {
                const start = Math.max(0, sentence.index - offset);
                const end = Math.min(
                  node.length,
                  sentence.index + sentence.segment.length - offset
                );
                if (start >= end) return;
                const span = document.createElement('span');
                span.dataset.audioSentence = String(
                  sentences.length - reverseIndex - 1
                );
                wrapText(node, start, end, span);
              });
          });
        }
        const groups = new Map();
        words.forEach((word) => {
          const element = this.wordElement(word.index);
          const sentence = (
            element?.closest('[data-audio-sentence]') ||
            element?.querySelector('[data-audio-sentence]')
          )?.dataset.audioSentence;
          const key = isLongReading ? sentence : 'line';
          if (key === undefined) return;
          if (!groups.has(key)) groups.set(key, []);
          groups.get(key).push(word);
        });
        // Without word anchors, retain the existing clip estimate. Sentence
        // boundaries divide that estimate by text length, never precise words.
        if (isLongReading && words.every((word) => word.estimated)) {
          const start = words[0].start_time;
          const duration = words[words.length - 1].end_time - start;
          sentences.forEach((sentence, index) => {
            groups.set(String(index), [
              {
                estimated: true,
                start_time: start + (duration * sentence.index) / text.length,
                end_time:
                  start +
                  (duration * (sentence.index + sentence.segment.length)) /
                    text.length,
              },
            ]);
          });
        }
        groups.forEach((anchors, key) => {
          const index = this.highlightSegments.length;
          // Highlight inline content so hanging indents follow each rendered
          // line instead of painting the paragraph's rectangular box.
          if (
            key === 'line' &&
            !container.querySelector('[data-audio-line-content]')
          ) {
            const content = document.createElement('span');
            content.dataset.audioLineContent = '';
            while (container.firstChild)
              content.appendChild(container.firstChild);
            container.appendChild(content);
          }
          const elements =
            key === 'line'
              ? [container.querySelector('[data-audio-line-content]')]
              : container.querySelectorAll(`[data-audio-sentence='${key}']`);
          elements.forEach((element) => {
            this.registerHighlight(element, index);
          });
          this.highlightSegments.push({
            index,
            estimated: anchors[0].estimated,
            start_time: anchors[0].start_time,
            end_time: anchors[anchors.length - 1].end_time,
          });
        });
      });
      this.highlightSegments.sort((a, b) => a.start_time - b.start_time);
    },
    registerHighlight(element, index) {
      element.dataset.audioHighlightIndex = String(index);
      element.classList.add('audio-line');
      if (!this.highlightElements.has(index)) {
        this.highlightElements.set(index, []);
      }
      this.highlightElements.get(index).push(element);
    },
    activeWordAt(time) {
      if (
        this.detailedSegments.some(
          (segment) =>
            segment.highlighting_available === false &&
            time >= segment.start_time &&
            time < segment.end_time
        )
      )
        return -1;
      let candidate = null;
      for (const segment of this.highlightSegments) {
        if (segment.start_time > time) break;
        candidate = segment;
      }
      // Hold through short gaps, but clear during bells and extended silence.
      return candidate &&
        time <=
          candidate.end_time +
            (candidate.estimated || candidate.exactWord ? 0 : 2)
        ? candidate.index
        : -1;
    },
    clearActiveWord() {
      document.querySelectorAll('.audio-line--active').forEach((element) => {
        element.classList.remove('audio-line--active');
        element.removeAttribute('aria-current');
      });
      this.activeWordIndex = -1;
    },
    updateActiveWord(time) {
      const nextIndex = this.activeWordAt(time);
      if (this.highlightMode === 'off') {
        if (this.activeWordIndex >= 0) this.clearActiveWord();
      } else if (nextIndex !== this.activeWordIndex) {
        this.clearActiveWord();
        if (nextIndex >= 0) {
          this.activeWordIndex = nextIndex;
          const elements = this.highlightElements?.get(nextIndex) || [];
          elements.forEach((element) =>
            element.classList.add('audio-line--active')
          );
          elements[0]?.setAttribute('aria-current', 'true');
        }
      }
      if (nextIndex < 0 || !this.enableScrolling || !this.isPlaying) return;
      const active = this.highlightElements?.get(nextIndex)?.[0];
      if (!active) return;
      // Follow measured words even while the sentence highlight stays unchanged.
      // Missing timing falls back to the highlighted text rather than another line.
      let wordIndex = -1;
      let low = 0;
      let high = this.wordSegments.length - 1;
      while (low <= high) {
        const middle = Math.floor((low + high) / 2);
        if (this.wordSegments[middle].start_time <= time) {
          wordIndex = middle;
          low = middle + 1;
        } else high = middle - 1;
      }
      const word = this.wordElement(wordIndex);
      const belongsToHighlight =
        word &&
        (word.closest(`[data-audio-highlight-index='${nextIndex}']`) ||
          word.querySelector(`[data-audio-highlight-index='${nextIndex}']`));
      this.followActiveWord(belongsToHighlight ? word : active);
    },
    followActiveWord(element) {
      const rect = element.getBoundingClientRect();
      const controlsHeight =
        this.$el?.querySelector('.controls.fixed-controls')?.offsetHeight || 0;
      const readingHeight = window.innerHeight - controlsHeight;
      const center = (rect.top + rect.bottom) / 2;
      const now = window.performance.now();
      // A middle-third dead band and cooldown avoid restarting smooth scrolling
      // for every word or reacting to intermediate positions during an animation.
      if (
        (center < readingHeight / 3 || center > (readingHeight * 2) / 3) &&
        now - this.lastFollowScrollAt >= 800
      ) {
        this.lastFollowScrollAt = now;
        element.scrollIntoView({
          behavior: window.matchMedia?.('(prefers-reduced-motion: reduce)')
            .matches
            ? 'auto'
            : 'smooth',
          block: 'center',
        });
      }
    },
    scrollToSegment(segmentId) {
      if (!this.enableScrolling) return;
      const element = document.querySelector(`[data-line-id='${segmentId}']`);
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    },
    togglePanel(panel) {
      const opening =
        panel === 'sections' ? !this.showSections : !this.showPreferences;
      this.showSections = opening && panel === 'sections';
      this.showPreferences = opening && panel === 'preferences';
      document.removeEventListener('pointerdown', this.handleOutsidePointer);
      if (!opening) return;
      document.addEventListener('pointerdown', this.handleOutsidePointer);
      if (panel === 'sections') {
        // Start keyboard and visual focus at the section now playing.
        this.$nextTick(() => {
          const current =
            this.$refs.sectionList?.querySelector('[aria-current]') ||
            this.$refs.sectionList?.querySelector('button');
          current?.scrollIntoView?.({ block: 'nearest' });
          current?.focus({ preventScroll: true });
        });
      }
    },
    closePanels(restoreFocus = false) {
      const control = this.showSections
        ? 'sectionsControl'
        : this.showPreferences
          ? 'preferencesControl'
          : null;
      this.showSections = false;
      this.showPreferences = false;
      document.removeEventListener('pointerdown', this.handleOutsidePointer);
      if (restoreFocus && control) this.$refs[control]?.focus();
    },
    handleOutsidePointer(event) {
      const panels = this.$el?.querySelectorAll('.now-playing, .options-wrap');
      if (Array.from(panels || []).some((el) => el.contains(event.target))) {
        return;
      }
      this.closePanels();
    },
    handleMenuKeydown(event) {
      const items = Array.from(
        this.$refs.sectionList?.querySelectorAll('button') || []
      );
      const index = items.indexOf(document.activeElement);
      const target = {
        ArrowDown: items[Math.min(index + 1, items.length - 1)],
        ArrowUp: items[Math.max(index - 1, 0)],
        Home: items[0],
        End: items[items.length - 1],
      }[event.key];
      if (!target) return;
      event.preventDefault();
      target.focus();
    },
    formatTime(seconds) {
      if (!seconds || isNaN(seconds)) return '0:00';
      const mins = Math.floor(seconds / 60);
      const secs = Math.floor(seconds % 60);
      return `${mins}:${secs.toString().padStart(2, '0')}`;
    },
  },
  computed: {
    playbackStatus() {
      if (this.transientStatus) return this.transientStatus;
      if (this.isPlaying) return 'Now listening';
      return this.isPaused ? 'Paused' : 'Daily Office audio';
    },
    // Short-lived states shown in place of the clock on every screen size.
    transientStatus() {
      if (!this.audioReady) return 'Preparing audio…';
      if (this.seeking) return 'Jumping…';
      if (this.isBuffering) return 'Buffering…';
      return '';
    },
    isBuffering() {
      return this.audioReady && this.loading && this.playbackRequested;
    },
    speedIndex() {
      return this.speeds.indexOf(this.playbackSpeed);
    },
    speedLabel() {
      return this.playbackSpeed.replace('x', '×');
    },
    formattedCurrentTime() {
      return this.formatTime(this.currentTime);
    },
    formattedDuration() {
      return this.formatTime(this.duration);
    },
    formattedRemainingTime() {
      return this.formatTime(Math.max(0, this.duration - this.currentTime));
    },
    currentSectionIndex() {
      let current = 0;
      this.trackSegments.forEach((segment, index) => {
        if (segment.start_time <= this.currentTime) current = index;
      });
      return current;
    },
    currentSectionName() {
      if (!this.trackSegments.length) {
        return this.office.replaceAll('_', ' ');
      }
      return this.trackSegments[this.currentSectionIndex].name;
    },
    progressPercentage() {
      if (!this.duration) return 0;
      return (this.currentTime / this.duration) * 100;
    },
  },
  watch: {
    highlightMode() {
      this.prepareHighlightSegments();
      this.updateActiveWord(this.audioElement?.currentTime ?? this.currentTime);
    },
  },
};
</script>

<style scoped>
/* One compact bar on every screen: transport, the current section (which
   opens a jump menu), a timeline, and a listening-options popover. Popovers
   float above the bar so opening them never moves a control.

   Phones dock the bar to the bottom edge (it absorbs the safe area); wider
   screens float it as a raised card. Every color is a theme token, so the bar
   follows light, sepia, and dark without overrides. */
.audio-player {
  color: var(--ink);
  font-family: var(--font-book);
  font-size: var(--text-md);
  line-height: var(--leading-ui);
}
.controls.fixed-controls {
  position: fixed;
  inset-inline: 0;
  bottom: 0;
  z-index: 100;
  padding: var(--space-2) max(var(--space-3), env(safe-area-inset-right))
    calc(var(--space-2) + env(safe-area-inset-bottom))
    max(var(--space-3), env(safe-area-inset-left));
  border-top: 1px solid var(--rule);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  background-color: var(--paper-raised);
  box-shadow: var(--shadow);
  transition:
    background-color var(--duration) var(--ease),
    border-color var(--duration) var(--ease);
}
button,
input {
  font-family: inherit;
  touch-action: manipulation;
}
button {
  color: inherit;
}
button:disabled,
input:disabled {
  opacity: 0.45;
}
button:focus-visible,
input:focus-visible,
a:focus-visible,
.segmented input:focus-visible + span {
  outline: none;
  box-shadow: var(--focus-ring);
}

/* ---- Bar layout ---------------------------------------------------- */
.player-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-1);
}
.timeline {
  order: -1;
  display: flex;
  flex: 1 0 100%;
  align-items: center;
  gap: var(--space-3);
  min-width: 0;
}
.primary-play-button {
  order: 0;
}
.now-playing {
  order: 1;
  flex: 1 1 0;
  min-width: 0;
  margin-inline: var(--space-1);
}
.skip-button--back {
  order: 2;
}
.skip-button--forward {
  order: 3;
}
.options-wrap {
  order: 4;
}
.dismiss-button {
  order: 5;
}

/* ---- Buttons ------------------------------------------------------- */
.primary-play-button {
  position: relative;
  display: grid;
  place-items: center;
  width: 3rem;
  height: 3rem;
  flex: 0 0 3rem;
  border-radius: 50%;
  background-color: var(--accent);
  color: var(--on-accent);
  font-size: 1.125rem;
  box-shadow: var(--shadow-sm);
  transition:
    transform 120ms var(--ease),
    filter var(--duration) var(--ease);
}
/* The line icons read better solid at this size. */
.primary-play-button .ui-icon {
  fill: currentColor;
}
.primary-play-button .icon-play {
  margin-left: 2px; /* optical centre */
}
.primary-play-button:hover:not(:disabled) {
  filter: brightness(1.08) saturate(1.05);
}
.primary-play-button:active:not(:disabled) {
  transform: scale(0.94);
}
.primary-play-button.is-buffering::after {
  content: '';
  position: absolute;
  inset: -4px;
  border: 2px solid transparent;
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: player-spin 0.9s linear infinite;
}
@keyframes player-spin {
  to {
    transform: rotate(360deg);
  }
}
.skip-button,
.preferences-button,
.dismiss-button {
  position: relative;
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.75rem;
  flex: 0 0 auto;
  border-radius: var(--radius);
  color: var(--ink-soft);
  transition:
    background-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}
.skip-button:hover:not(:disabled),
.preferences-button:hover,
.dismiss-button:hover,
.section-button:hover:not(:disabled) {
  background-color: var(--paper-sunken);
  color: var(--ink);
}
.skip-icon {
  width: 1.75rem;
  height: 1.75rem;
  overflow: visible;
}
.skip-arc {
  fill: none;
  stroke: currentColor;
  stroke-width: 1.5;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.skip-icon text {
  fill: currentColor;
  font-family: var(--font-book);
  font-size: 8.5px;
  font-weight: 600;
  font-variant-numeric: lining-nums;
}
.preferences-button {
  width: auto;
  min-width: 2.75rem;
  padding-inline: var(--space-3);
  grid-auto-flow: column;
  gap: var(--space-2);
  font-size: 1.25rem;
}
.preferences-button[aria-expanded='true'] {
  background-color: var(--accent-wash);
  color: var(--accent);
}
.speed-badge {
  font-size: var(--text-sm);
  font-variant-numeric: lining-nums tabular-nums;
}
.dismiss-button {
  color: var(--ink-faint);
  font-size: 1.125rem;
}

/* ---- Current section / jump menu ----------------------------------- */
.now-playing,
.options-wrap {
  position: static;
}
.section-button {
  display: flex;
  width: 100%;
  min-height: 2.75rem;
  flex-direction: column;
  justify-content: center;
  padding: 2px var(--space-2);
  border-radius: var(--radius);
  text-align: left;
  transition: background-color var(--duration) var(--ease);
}
.section-button:disabled {
  opacity: 1;
}
.section-caption {
  display: block;
  overflow: hidden;
  color: var(--ink-faint);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  font-variant-numeric: oldstyle-nums tabular-nums;
  letter-spacing: var(--tracking-caps);
  line-height: 1.15;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.caption-status {
  display: none;
}
.section-name {
  display: flex;
  min-width: 0;
  max-width: 100%;
  align-items: center;
  gap: var(--space-2);
  color: var(--ink);
  font-size: var(--text-md);
  line-height: var(--leading-tight);
}
.section-name-text {
  overflow: hidden;
  padding-top: 0.08em;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.section-chevron {
  flex: 0 0 auto;
  color: var(--ink-faint);
  font-size: var(--text-xs);
  transition: transform var(--duration) var(--ease);
}
.section-button[aria-expanded='true'] .section-chevron {
  transform: rotate(180deg);
}

/* ---- Popovers ------------------------------------------------------- */
.popover {
  position: absolute;
  bottom: calc(100% + var(--space-2));
  z-index: 1;
  max-height: min(60dvh, 440px);
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: var(--space-2);
  border: 1px solid var(--rule);
  border-radius: var(--radius-lg);
  background-color: var(--paper-raised);
  box-shadow: var(--shadow);
  animation: popover-in 140ms var(--ease);
}
@keyframes popover-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
}
.popover-title {
  margin: var(--space-1) var(--space-2) var(--space-2);
  color: var(--ink-faint);
  font-size: var(--text-sm);
  font-variant-caps: all-small-caps;
  letter-spacing: 0.12em;
  line-height: 1.2;
}
.section-menu {
  inset-inline: var(--space-2);
}
.section-item {
  display: flex;
  width: 100%;
  min-height: 2.75rem;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius);
  color: var(--ink);
  font-size: var(--text-md);
  line-height: var(--leading-tight);
  text-align: left;
  transition: background-color var(--duration) var(--ease);
}
.section-item:hover,
.section-item:focus-visible {
  background-color: var(--paper-sunken);
}
.section-item--current,
.section-item--current:hover {
  background-color: var(--accent-wash);
  color: var(--accent);
}
.section-item-name {
  padding-top: 0.08em;
}
.section-item-time {
  flex: 0 0 auto;
  color: var(--ink-faint);
  font-size: var(--text-sm);
  font-variant-numeric: oldstyle-nums tabular-nums;
}
.preferences-panel {
  right: var(--space-2);
  width: min(20rem, calc(100% - 2 * var(--space-2)));
  padding: var(--space-1) var(--space-4);
}

/* ---- Listening options --------------------------------------------- */
.preference-row,
.highlight-control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  min-height: 3.5rem;
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--rule);
}
.highlight-control {
  display: block;
  padding-block: var(--space-3);
}
.highlight-control legend {
  float: left; /* keeps the legend inside the fieldset's padding box */
  width: 100%;
}
.preference-label {
  display: flex;
  flex-direction: column;
  color: var(--ink);
  font-size: var(--text-md);
  font-variant-caps: all-small-caps;
  letter-spacing: var(--tracking-caps);
  line-height: var(--leading-tight);
}
.preference-label small {
  margin-top: 2px;
  color: var(--ink-faint);
  font-size: var(--text-sm);
  font-style: italic;
  font-variant-caps: normal;
  letter-spacing: normal;
}
.stepper {
  display: flex;
  align-items: center;
  border: 1px solid var(--rule-strong);
  border-radius: var(--radius-pill);
  background-color: var(--paper-raised);
}
.stepper button {
  display: grid;
  place-items: center;
  width: 2.75rem;
  height: 2.5rem;
  border-radius: var(--radius-pill);
  color: var(--ink-soft);
  font-size: var(--text-sm);
  transition: background-color var(--duration) var(--ease);
}
.stepper button:hover:not(:disabled) {
  background-color: var(--paper-sunken);
  color: var(--ink);
}
.speed-value {
  min-width: 3.25em;
  font-size: var(--text-md);
  font-variant-numeric: lining-nums tabular-nums;
  text-align: center;
}
/* Mirrors UiSegmented's pill (native radios keep form semantics). */
.segmented {
  display: grid;
  clear: both;
  grid-template-columns: repeat(3, 1fr);
  gap: 2px;
  margin-top: var(--space-2);
  padding: 3px;
  border: 1px solid var(--rule);
  border-radius: var(--radius);
  background-color: var(--paper-sunken);
}
.segmented label {
  position: relative;
}
.segmented input {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}
.segmented span {
  display: grid;
  place-items: center;
  min-height: 2.5rem;
  padding-top: 0.08em;
  border-radius: calc(var(--radius) - 3px);
  color: var(--ink-soft);
  cursor: pointer;
  font-size: var(--text-sm);
  transition:
    background-color var(--duration) var(--ease),
    color var(--duration) var(--ease);
}
.segmented span:hover {
  color: var(--ink);
}
.segmented input:checked + span {
  background-color: var(--paper-raised);
  color: var(--ink);
  box-shadow:
    var(--shadow-sm),
    0 0 0 1px var(--rule);
}
/* Mirrors UiSwitch. */
.scroll-control {
  position: relative;
  flex: 0 0 auto;
  width: 2.75rem;
  height: 1.625rem;
  border-radius: var(--radius-pill);
  background-color: var(--rule-strong);
  transition: background-color var(--duration) var(--ease);
}
.scroll-control::before {
  content: '';
  position: absolute;
  inset: -0.5625rem 0; /* a 44px-tall tap target */
}
.scroll-control[aria-checked='true'] {
  background-color: var(--accent);
}
.switch-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  background-color: var(--paper-raised);
  box-shadow: var(--shadow-sm);
  transition: transform var(--duration) var(--ease);
}
.scroll-control[aria-checked='true'] .switch-thumb {
  transform: translateX(1.125rem);
}
.preferences-panel > :last-child {
  border-bottom: 0;
}
.hide-player-button {
  display: flex;
  width: 100%;
  min-height: 3rem;
  align-items: center;
  gap: var(--space-2);
  color: var(--ink-soft);
  font-size: var(--text-md);
  line-height: 1;
  transition: color var(--duration) var(--ease);
}
.hide-player-button:hover {
  color: var(--ink);
}

/* ---- Timeline ------------------------------------------------------- */
.time {
  display: none;
  flex: 0 0 auto;
  min-width: 2.75em;
  color: var(--ink-faint);
  font-size: var(--text-sm);
  font-variant-numeric: oldstyle-nums tabular-nums;
}
.time--remaining {
  text-align: right;
}
.timeline-slider {
  display: block;
  flex: 1;
  min-width: 0;
  height: 1.5rem;
  margin: -0.25rem 0 0;
  appearance: none;
  -webkit-appearance: none;
  background: transparent;
  cursor: pointer;
}
.timeline-slider:disabled {
  opacity: 1;
  cursor: default;
}
.timeline-slider::-webkit-slider-runnable-track {
  height: 3px;
  border-radius: 2px;
  background: linear-gradient(
    to right,
    var(--accent) 0 var(--progress),
    var(--rule-strong) var(--progress) 100%
  );
}
.timeline-slider::-moz-range-track {
  height: 3px;
  border-radius: 2px;
  background: var(--rule-strong);
}
.timeline-slider::-moz-range-progress {
  height: 3px;
  border-radius: 2px;
  background: var(--accent);
}
.timeline-slider::-webkit-slider-thumb {
  width: 0.875rem;
  height: 0.875rem;
  margin-top: calc((3px - 0.875rem) / 2);
  appearance: none;
  -webkit-appearance: none;
  border: 1.5px solid var(--accent);
  border-radius: 50%;
  background: var(--paper-raised);
  box-shadow: var(--shadow-sm);
  transition: transform 120ms var(--ease);
}
.timeline-slider::-moz-range-thumb {
  width: 0.875rem;
  height: 0.875rem;
  box-sizing: border-box;
  border: 1.5px solid var(--accent);
  border-radius: 50%;
  background: var(--paper-raised);
}
.timeline-slider:hover::-webkit-slider-thumb,
.timeline-slider:active::-webkit-slider-thumb {
  transform: scale(1.2);
}
.timeline-slider:focus-visible {
  box-shadow: none;
}
.timeline-slider:focus-visible::-webkit-slider-thumb {
  box-shadow: var(--focus-ring);
}
.timeline-slider:focus-visible::-moz-range-thumb {
  box-shadow: var(--focus-ring);
}

/* ---- Messages ------------------------------------------------------- */
.audio-error,
.availability-note {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--text-sm);
  line-height: 1.45;
}
.audio-error {
  flex-wrap: wrap;
  margin-bottom: var(--space-2);
  padding: 2px 2px 2px var(--space-3);
  border: 1px solid var(--accent-rule);
  border-radius: var(--radius);
  background-color: var(--accent-wash);
  color: var(--ink);
}
.audio-error span {
  flex: 1 1 12rem;
}
.audio-error button {
  min-height: 2.75rem;
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--accent);
  font-size: var(--text-md);
  font-variant-caps: all-small-caps;
  letter-spacing: var(--tracking-caps);
}
.availability-note {
  color: var(--ink-soft);
}
.note-icon {
  color: var(--accent);
  font-size: 1.25rem;
}
.note-text {
  flex: 1 1 auto;
  min-width: 0;
}
.availability-note a {
  color: var(--accent);
}

/* Small phones: the options popover carries "Hide audio player". */
@media (max-width: 479px) {
  .controls.fixed-controls {
    padding-inline: max(var(--space-2), env(safe-area-inset-left))
      max(var(--space-2), env(safe-area-inset-right));
  }
  .player-bar > .dismiss-button {
    display: none;
  }
  .preferences-button {
    padding-inline: var(--space-2);
  }
}

/* Wide screens: a floating card, a single row with the timeline inline. */
@media (min-width: 720px) {
  .controls.fixed-controls {
    inset-inline: max(var(--gutter), env(safe-area-inset-left))
      max(var(--gutter), env(safe-area-inset-right));
    bottom: calc(var(--space-3) + env(safe-area-inset-bottom));
    max-width: 58rem;
    margin-inline: auto;
    padding: var(--space-2) var(--space-3);
    border: 1px solid var(--rule);
    border-radius: var(--radius-lg);
  }
  .player-bar {
    flex-wrap: nowrap;
    gap: var(--space-1);
  }
  .skip-button--back {
    order: 0;
  }
  .primary-play-button {
    order: 1;
  }
  .skip-button--forward {
    order: 2;
  }
  .now-playing {
    position: relative;
    order: 3;
    flex: 0 1 14rem;
    margin-inline: var(--space-2) 2px;
  }
  .timeline {
    order: 4;
    flex: 1 1 auto;
    padding-inline: var(--space-2);
    border-inline-start: 1px solid var(--rule);
  }
  .options-wrap {
    position: relative;
    order: 5;
  }
  .dismiss-button {
    order: 6;
  }
  .time {
    display: block;
  }
  .timeline-slider {
    margin: 0;
  }
  .caption-status {
    display: inline;
  }
  .caption-time {
    display: none;
  }
  /* Anchor popovers to their trigger, clear of the bar's top edge. */
  .popover {
    bottom: calc(100% + var(--space-5));
  }
  .section-menu {
    inset-inline: 0 auto;
    width: 21rem;
  }
  .preferences-panel {
    right: 0;
    width: 20rem;
  }
}

/* Follow-along highlighting inside the office text. */
:global(.audio-line) {
  position: relative;
  /* Paint breathing room without changing text width or punctuation spacing. */
  padding: 0;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
  border-radius: 0.2em;
  transition:
    color 100ms ease,
    background-color 140ms ease,
    box-shadow 140ms ease;
}

:global(.audio-line--active) {
  background: color-mix(in srgb, var(--accent) 22%, transparent);
  box-shadow:
    -0.12em 0 0 0.035em color-mix(in srgb, var(--accent) 22%, transparent),
    0.12em 0 0 0.035em color-mix(in srgb, var(--accent) 22%, transparent);
  color: color-mix(in srgb, var(--ink) 88%, var(--accent));
}

/* Sentence fragments meet at word and markup boundaries. Do not extend
   translucent paint across those boundaries: overlapping paint creates seams. */
:global([data-audio-sentence].audio-line) {
  padding-block: 0;
  border-radius: 0;
}

:global([data-audio-sentence].audio-line--active) {
  background: color-mix(in srgb, var(--accent) 22%, var(--paper));
  box-shadow: none;
}

@media (prefers-reduced-motion: reduce) {
  :global(.audio-line),
  .primary-play-button,
  .switch-thumb,
  .popover {
    transition: none;
    animation: none;
  }
}
</style>
