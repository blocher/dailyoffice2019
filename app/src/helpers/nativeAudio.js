/*
  Native audio in the Android and iOS apps
  ========================================
  An Android WebView has no media service of its own: once the screen locks
  or another app comes forward, the system can cut the WebView's network and
  an <audio> element plays what it has buffered and then waits forever. On
  iOS, WebKit keeps playing in the background, but a stalled download can't
  be recovered while the app is suspended. Both apps therefore play office
  audio through a native player with the same interface:
  - Android: android/.../audio/NativeAudioPlugin.java (Media3 in a
    media-playback foreground service);
  - iOS: ios/App/App/NativeAudioPlugin.swift (AVPlayer).
  Each reconnects a dropped download by itself, for a few minutes, and shows
  the lock-screen, headset and Now Playing controls.

  NativeAudioElement stands in for the <audio> element AudioPlayer.vue drives:
  the same properties, methods and media events, backed by that plugin. The
  plugin reports its state as `status` events; this class turns changes in
  that state into the media events an <audio> element would fire.

  createAudioElement() returns a real Audio everywhere else (browsers).
*/
import { Capacitor, registerPlugin } from '@capacitor/core';

const NativeAudio = registerPlugin('NativeAudio');

// HTMLMediaElement readyState values.
const HAVE_NOTHING = 0;
const HAVE_METADATA = 1;
const HAVE_CURRENT_DATA = 2;
const HAVE_ENOUGH_DATA = 4;
// MediaError.MEDIA_ERR_NETWORK.
const MEDIA_ERR_NETWORK = 2;
// A seek is settled when the player reports a position this close to it.
const SEEK_TOLERANCE_SECONDS = 1;
// Ignore stale positions for at most this long after a seek is requested.
const SEEK_SETTLE_MS = 3000;

export function nativeAudioAvailable() {
  return (
    ['android', 'ios'].includes(Capacitor.getPlatform()) &&
    Capacitor.isPluginAvailable('NativeAudio')
  );
}

// An <audio>-compatible element: native in the apps, a real Audio elsewhere.
// `metadata` ({ title, artist, artwork }) is shown on the lock screen and
// notification; `artwork` is an image file in the bundled web assets.
export function createAudioElement(metadata = {}) {
  if (nativeAudioAvailable()) {
    return new NativeAudioElement(NativeAudio, metadata);
  }
  return new Audio();
}

function now() {
  return window.performance?.now?.() ?? Date.now();
}

function seconds(value) {
  const number = Number(value);
  return Number.isFinite(number) && number > 0 ? number : 0;
}

function timeRanges(end) {
  return {
    get length() {
      return end() > 0 ? 1 : 0;
    },
    start: () => 0,
    end: () => end(),
  };
}

export class NativeAudioElement extends window.EventTarget {
  constructor(plugin, metadata = {}) {
    super();
    this.plugin = plugin;
    this.metadata = metadata;
    this.preload = 'auto';
    this.defaultPlaybackRate = 1;
    this.rate = 1;
    this.source = '';
    this.listener = null;
    // The native player retries a dropped connection itself; AudioPlayer
    // leaves its buffering alone and only reloads it after an error.
    this.recoversOnItsOwn = true;
    // Commands sent but not yet acknowledged; until they are, a status may
    // predate them and must not undo the play/pause they asked for. The
    // latest such status is kept in case the command fails and never
    // reports a newer one.
    this.pendingCommands = 0;
    this.deferredStatus = null;
    this.seekable = timeRanges(() => this.knownDuration);
    this.buffered = timeRanges(() => this.bufferedEnd);
    this.resetState();
  }

  resetState() {
    this.position = 0;
    this.positionAt = now();
    this.knownDuration = 0;
    this.bufferedEnd = 0;
    this.readyState = HAVE_NOTHING;
    this.paused = true;
    this.ended = false;
    this.playing = false;
    this.playerState = 'idle';
    this.error = null;
    this.seekTarget = null;
  }

  get src() {
    return this.source;
  }

  set src(value) {
    this.source = value ? String(value) : '';
  }

  getAttribute(name) {
    return name === 'src' && this.source ? this.source : null;
  }

  removeAttribute(name) {
    if (name === 'src') this.source = '';
  }

  get duration() {
    return this.knownDuration > 0 ? this.knownDuration : NaN;
  }

  get currentTime() {
    let position = this.position;
    if (this.playing && !this.paused && this.seekTarget === null) {
      position += ((now() - this.positionAt) / 1000) * this.rate;
    }
    return this.knownDuration > 0
      ? Math.min(position, this.knownDuration)
      : position;
  }

  set currentTime(value) {
    const target = Number(value);
    if (!Number.isFinite(target)) return;
    const clamped =
      this.knownDuration > 0
        ? Math.min(Math.max(0, target), this.knownDuration)
        : Math.max(0, target);
    this.setPosition(clamped);
    this.ended = false;
    this.seekTarget = { position: clamped, until: now() + SEEK_SETTLE_MS };
    this.emit('seeking');
    this.emit('timeupdate');
    this.send('seekTo', { position: clamped });
  }

  get playbackRate() {
    return this.rate;
  }

  set playbackRate(value) {
    const rate = Number(value);
    if (!Number.isFinite(rate) || rate <= 0 || rate === this.rate) return;
    this.setPosition(this.currentTime);
    this.rate = rate;
    this.emit('ratechange');
    this.send('setRate', { rate });
  }

  load() {
    this.resetState();
    this.rate = this.defaultPlaybackRate;
    if (!this.source) {
      this.detach();
      this.send('stop');
      return;
    }
    this.attach();
    this.send('setSource', {
      url: this.source,
      title: this.metadata.title || '',
      artist: this.metadata.artist || '',
      artwork: this.metadata.artwork || '',
      rate: this.rate,
    });
  }

  play() {
    if (!this.source) {
      return Promise.reject(
        Object.assign(new Error('No audio source'), {
          name: 'NotSupportedError',
        })
      );
    }
    if (this.ended) {
      this.currentTime = 0;
    }
    if (this.paused) {
      this.paused = false;
      this.setPosition(this.position);
      this.emit('play');
      if (this.readyState < HAVE_ENOUGH_DATA) this.emit('waiting');
    }
    return this.send('play').then(() => undefined);
  }

  pause() {
    if (!this.paused) {
      this.setPosition(this.currentTime);
      this.paused = true;
      this.playing = false;
      this.emit('timeupdate');
      this.emit('pause');
    }
    this.send('pause').catch(() => {});
  }

  // Native calls run in order on the plugin's side and resolve with the
  // player's status, which is applied once the call no longer counts as
  // pending. Errors reject, so play() can report them like a rejected
  // HTMLMediaElement.play().
  send(method, options = {}) {
    this.pendingCommands += 1;
    let call;
    try {
      call = Promise.resolve(this.plugin[method](options));
    } catch (error) {
      call = Promise.reject(error);
    }
    const settled = () => {
      this.pendingCommands = Math.max(0, this.pendingCommands - 1);
    };
    call.then(
      (status) => {
        settled();
        if (status?.state) this.applyStatus(status);
      },
      () => {
        settled();
        // No status came back; catch up with the last one held back.
        if (!this.pendingCommands && this.deferredStatus) {
          this.applyStatus(this.deferredStatus);
        }
      }
    );
    if (method !== 'play') {
      // Other commands never block the caller; failures surface as status.
      call.catch(() => {});
    }
    return call;
  }

  attach() {
    if (this.listener) return;
    this.listener = Promise.resolve(
      this.plugin.addListener('status', (status) => this.applyStatus(status))
    ).catch(() => null);
  }

  detach() {
    const listener = this.listener;
    this.listener = null;
    listener?.then((handle) => handle?.remove?.()).catch(() => {});
  }

  setPosition(position) {
    this.position = position;
    this.positionAt = now();
  }

  emit(name) {
    this.dispatchEvent(new window.Event(name));
  }

  // Bring this element in line with the native player's state, firing the
  // media events an <audio> element would have fired along the way.
  applyStatus(status = {}) {
    // Only this track's status counts; one with no track (the player not
    // connected yet, or stopped) says nothing about it.
    if (!this.source || status.url !== this.source) return;

    const previousState = this.playerState;
    const wasPlaying = this.playing;
    const state = status.state || 'idle';
    this.playerState = state;

    if (status.error) {
      if (!this.error) {
        this.setPosition(seconds(status.position) || this.currentTime);
        this.error = { code: MEDIA_ERR_NETWORK, message: status.error };
        this.playing = false;
        this.readyState = Math.min(this.readyState, HAVE_METADATA);
        this.emit('error');
      }
      return;
    }
    this.error = null;

    const duration = seconds(status.duration);
    if (duration && duration !== this.knownDuration) {
      const first = !this.knownDuration;
      this.knownDuration = duration;
      this.readyState = Math.max(this.readyState, HAVE_METADATA);
      this.emit('durationchange');
      if (first) this.emit('loadedmetadata');
    }

    this.syncPosition(status);

    const buffered = seconds(status.buffered);
    if (buffered > this.bufferedEnd + 0.5) {
      this.bufferedEnd = buffered;
      this.emit('progress');
    } else if (buffered < this.bufferedEnd) {
      this.bufferedEnd = buffered;
    }

    if (state === 'ready' && this.readyState < HAVE_ENOUGH_DATA) {
      this.readyState = HAVE_ENOUGH_DATA;
      this.emit('canplay');
      this.emit('canplaythrough');
    } else if (state === 'buffering' && this.knownDuration) {
      this.readyState = Math.min(this.readyState, HAVE_CURRENT_DATA);
    }

    // Play or pause from outside the page: lock screen, notification,
    // headset buttons, unplugged headphones, a phone call.
    this.deferredStatus = this.pendingCommands ? status : null;
    if (!this.pendingCommands && state !== 'ended') {
      if (status.playWhenReady && this.paused) {
        this.paused = false;
        this.emit('play');
      } else if (!status.playWhenReady && !this.paused) {
        this.paused = true;
        this.playing = false;
        this.emit('timeupdate');
        this.emit('pause');
      }
    }

    this.playing = Boolean(status.isPlaying) && !this.paused;
    if (this.playing && !wasPlaying) {
      this.emit('playing');
    } else if (
      !this.paused &&
      state === 'buffering' &&
      (wasPlaying || previousState !== 'buffering')
    ) {
      this.emit('waiting');
    }

    if (state === 'ended' && previousState !== 'ended') {
      this.ended = true;
      this.playing = false;
      this.setPosition(this.knownDuration || this.position);
      this.emit('timeupdate');
      if (!this.paused) {
        this.paused = true;
        this.emit('pause');
      }
      this.emit('ended');
      return;
    }

    if (this.playing || status.event === 'seeked') this.emit('timeupdate');
  }

  syncPosition(status) {
    const position = seconds(status.position);
    if (this.seekTarget) {
      const landed =
        Math.abs(position - this.seekTarget.position) < SEEK_TOLERANCE_SECONDS;
      if (landed) {
        this.seekTarget = null;
        this.setPosition(position);
        this.emit('seeked');
      } else if (now() > this.seekTarget.until) {
        // The seek was overtaken (a newer seek, a reload); trust the player.
        this.seekTarget = null;
        this.setPosition(position);
      }
      return;
    }
    this.setPosition(position);
  }
}
