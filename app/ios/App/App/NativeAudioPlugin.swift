import AVFoundation
import Capacitor
import MediaPlayer
import Network
import UIKit

/// Plays office audio natively in the iOS app, so it keeps playing, and keeps reconnecting, with
/// the screen locked or another app in front.
///
/// WebKit's own audio plays on in the background, but when its download drops there nothing
/// recovers it until the listener returns to the app. AVPlayer runs in the app itself: it
/// reconnects a dropped download (for up to five minutes, like the Android player), shows the
/// office in Now Playing (lock screen, Control Center, Dynamic Island), and answers the headset and
/// lock-screen controls. Closing the app ends the office.
///
/// It speaks the same protocol as android/.../audio/NativeAudioPlugin.java, which
/// app/src/helpers/nativeAudio.js wraps for the page: every method resolves with the player's
/// status, and a "status" event reports each change (and, while audio plays in the foreground,
/// every quarter second):
///
///     { url, state: idle|buffering|ready|ended, playWhenReady, isPlaying,
///       position, duration, buffered (seconds), rate, error, event }
@objc(NativeAudioPlugin)
public class NativeAudioPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "NativeAudioPlugin"
    public let jsName = "NativeAudio"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "setSource", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "play", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "pause", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "seekTo", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "setRate", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "stop", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getStatus", returnType: CAPPluginReturnPromise),
    ]

    // Reconnect for this long without playing before giving up (OfficeLoadErrorPolicy on Android).
    // Trying holds the app awake, so it mustn't go on all night.
    private static let giveUpAfter: TimeInterval = 5 * 60
    // Waiting this long for data that never comes counts as a dropped connection.
    private static let silentStallLimit: TimeInterval = 20
    // Before Play, fetch only enough to start at once (each office page would otherwise download
    // about 25 MB); once playing, as much of the office as AVPlayer will hold.
    private static let pausedBuffer: TimeInterval = 30
    private static let playingBuffer: TimeInterval = 45 * 60
    private static let skipInterval: Double = 15

    private let player = AVPlayer()
    private var source: String?
    private var item: AVPlayerItem?
    private var itemObservation: NSKeyValueObservation?
    private var timeControlObservation: NSKeyValueObservation?
    private var observers: [NSObjectProtocol] = []
    private let pathMonitor = NWPathMonitor()
    private var networkAvailable = true

    private var title = ""
    private var artist = ""
    private var artwork: MPMediaItemArtwork?
    private var rate: Float = 1
    private var playWhenReady = false
    private var ended = false
    private var error: String?
    // Where the playhead goes once the item can seek: a seek made before it was ready, or the
    // place to return to after reconnecting. Reported as the position until then.
    private var pendingSeek: Double?
    private var lastPosition: Double = 0

    private var failingSince: Date?
    private var reconnectAttempts = 0
    private var reconnectWork: DispatchWorkItem?
    private var reconnectOnPlay = false
    private var waitingSince: Date?
    private var waitingBufferedEnd: Double = 0
    private var backgroundTask: UIBackgroundTaskIdentifier = .invalid

    private var resumeAfterInterruption = false
    private var inForeground = true
    private var timer: Timer?

    override public func load() {
        player.automaticallyWaitsToMinimizeStalling = true
        timeControlObservation = player.observe(\.timeControlStatus) { [weak self] _, _ in
            DispatchQueue.main.async { self?.timeControlChanged() }
        }
        let center = NotificationCenter.default
        let session = AVAudioSession.sharedInstance()
        observers = [
            center.addObserver(forName: AVAudioSession.interruptionNotification, object: session, queue: .main) { [weak self] in
                self?.handleInterruption($0)
            },
            center.addObserver(forName: AVAudioSession.routeChangeNotification, object: session, queue: .main) { [weak self] in
                self?.handleRouteChange($0)
            },
            center.addObserver(forName: .AVPlayerItemDidPlayToEndTime, object: nil, queue: .main) { [weak self] in
                self?.itemEnded($0)
            },
            center.addObserver(forName: .AVPlayerItemFailedToPlayToEndTime, object: nil, queue: .main) { [weak self] note in
                guard let self, note.object as? AVPlayerItem === self.item else { return }
                self.connectionFailed(note.userInfo?[AVPlayerItemFailedToPlayToEndTimeErrorKey] as? Error)
            },
            center.addObserver(forName: UIApplication.didBecomeActiveNotification, object: nil, queue: .main) { [weak self] _ in
                guard let self else { return }
                self.inForeground = true
                self.emit("resume")
                self.scheduleTimer()
            },
            center.addObserver(forName: UIApplication.didEnterBackgroundNotification, object: nil, queue: .main) { [weak self] _ in
                // State changes still arrive; only the quarter-second clock slows while hidden.
                guard let self else { return }
                self.inForeground = false
                self.scheduleTimer()
                // Already waiting for data: ask for time to reconnect before iOS suspends the app.
                if self.playWhenReady, self.player.timeControlStatus == .waitingToPlayAtSpecifiedRate {
                    self.beginBackgroundTask()
                }
            },
        ]
        pathMonitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async { self?.networkChanged(available: path.status == .satisfied) }
        }
        pathMonitor.start(queue: DispatchQueue(label: "NativeAudio.network"))
        setUpRemoteCommands()
    }

    deinit {
        pathMonitor.cancel()
        timer?.invalidate()
        observers.forEach { NotificationCenter.default.removeObserver($0) }
    }

    // MARK: - Page commands

    @objc func setSource(_ call: CAPPluginCall) {
        guard let source = call.getString("url"), !source.isEmpty, URL(string: source) != nil else {
            call.reject("A url is required")
            return
        }
        let title = call.getString("title") ?? ""
        let artist = call.getString("artist") ?? ""
        let artworkPath = call.getString("artwork") ?? ""
        let rate = call.getDouble("rate") ?? 1
        DispatchQueue.main.async {
            self.title = title
            self.artist = artist
            self.artwork = Self.loadArtwork(artworkPath)
            if rate > 0 {
                self.rate = Float(rate)
            }
            // This track is already loaded and healthy: the page is retrying while the player
            // reconnects by itself. Reloading would drop the connection and the buffer.
            if source == self.source, self.item != nil, self.error == nil {
                self.updateNowPlaying()
                call.resolve(self.status("command"))
                return
            }
            let same = source == self.source
            if !same {
                self.playWhenReady = false
                self.player.pause()
                self.failingSince = nil
            }
            self.source = source
            // A retry of the same track reconnects from where it was.
            self.loadItem(at: same ? self.currentPosition() : 0)
            self.enableRemoteCommands(true)
            self.updateNowPlaying()
            call.resolve(self.status("command"))
        }
    }

    @objc func play(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            guard self.source != nil, let item = self.item else {
                call.reject("No audio source")
                return
            }
            self.playWhenReady = true
            if self.error != nil || self.reconnectOnPlay || item.status == .failed {
                // After an error, try the connection again.
                self.failingSince = nil
                self.reconnectAttempts = 0
                self.loadItem(at: self.currentPosition())
            } else if item.status == .readyToPlay {
                self.startPlayback()
            } else {
                // Starts once the item is ready (itemStatusChanged).
                self.activateSession()
            }
            self.scheduleTimer()
            self.updateNowPlaying()
            call.resolve(self.status("command"))
        }
    }

    @objc func pause(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            self.pausePlayback()
            call.resolve(self.status("command"))
        }
    }

    @objc func seekTo(_ call: CAPPluginCall) {
        guard let position = call.getDouble("position"), position.isFinite, position >= 0 else {
            call.reject("A position is required")
            return
        }
        DispatchQueue.main.async {
            self.seek(to: position)
            call.resolve(self.status("command"))
        }
    }

    @objc func setRate(_ call: CAPPluginCall) {
        guard let rate = call.getDouble("rate"), rate.isFinite, rate > 0 else {
            call.reject("A rate is required")
            return
        }
        DispatchQueue.main.async {
            self.rate = Float(rate)
            if #available(iOS 16.0, *) {
                self.player.defaultRate = self.rate
            }
            if self.player.rate > 0 {
                self.player.rate = self.rate
            }
            self.emit("change")
            self.updateNowPlaying()
            call.resolve(self.status("command"))
        }
    }

    @objc func stop(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            self.playWhenReady = false
            self.player.pause()
            self.cancelReconnect()
            self.endBackgroundTask()
            self.itemObservation = nil
            self.player.replaceCurrentItem(with: nil)
            self.item = nil
            self.source = nil
            self.error = nil
            self.ended = false
            self.pendingSeek = nil
            self.lastPosition = 0
            self.failingSince = nil
            self.enableRemoteCommands(false)
            MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
            // Let the listener's own music or podcast carry on.
            try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
            self.scheduleTimer()
            call.resolve(self.status("command"))
        }
    }

    @objc func getStatus(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            call.resolve(self.status("command"))
        }
    }

    // MARK: - Playback

    private func loadItem(at position: Double) {
        guard let source, let url = URL(string: source) else { return }
        cancelReconnect()
        error = nil
        ended = false
        reconnectOnPlay = false
        waitingSince = nil
        var options: [String: Any] = [:]
        if #available(iOS 16.0, *) {
            options[AVURLAssetHTTPUserAgentKey] = Self.userAgent
        }
        let item = AVPlayerItem(asset: AVURLAsset(url: url, options: options))
        // Suits speech at other speeds.
        item.audioTimePitchAlgorithm = .timeDomain
        item.preferredForwardBufferDuration = playWhenReady ? Self.playingBuffer : Self.pausedBuffer
        itemObservation = item.observe(\.status) { [weak self, weak item] _, _ in
            DispatchQueue.main.async {
                guard let self, let item, item === self.item else { return }
                self.itemStatusChanged(item)
            }
        }
        self.item = item
        pendingSeek = position > 0 ? position : nil
        lastPosition = position
        player.replaceCurrentItem(with: item)
        emit("change")
    }

    private func itemStatusChanged(_ item: AVPlayerItem) {
        switch item.status {
        case .readyToPlay:
            if let target = pendingSeek {
                seek(to: target)
            }
            if playWhenReady {
                startPlayback()
            }
        case .failed:
            connectionFailed(item.error)
        default:
            break
        }
        emit("change")
        updateNowPlaying()
    }

    private func startPlayback() {
        activateSession()
        item?.preferredForwardBufferDuration = Self.playingBuffer
        if #available(iOS 16.0, *) {
            player.defaultRate = rate
        }
        player.rate = rate
    }

    private func pausePlayback() {
        lastPosition = currentPosition()
        playWhenReady = false
        player.pause()
        if reconnectWork != nil {
            cancelReconnect()
            reconnectOnPlay = true
        }
        failingSince = nil
        waitingSince = nil
        endBackgroundTask()
        scheduleTimer()
        emit("change")
        updateNowPlaying()
    }

    private func seek(to target: Double) {
        let duration = currentDuration()
        let clamped = duration > 0 ? min(max(0, target), duration) : max(0, target)
        ended = false
        pendingSeek = clamped
        lastPosition = clamped
        guard let item, item.status == .readyToPlay else {
            // Applied when the item is ready (itemStatusChanged).
            emit("change")
            return
        }
        let time = CMTime(seconds: clamped, preferredTimescale: 1000)
        let tolerance = CMTime(seconds: 0.1, preferredTimescale: 1000)
        item.seek(to: time, toleranceBefore: tolerance, toleranceAfter: tolerance) { [weak self, weak item] finished in
            DispatchQueue.main.async {
                guard let self, let item, item === self.item else { return }
                // A newer seek replaces this one, and reports when it lands.
                if finished, self.pendingSeek == clamped {
                    self.pendingSeek = nil
                }
                self.emit("seeked")
                self.updateNowPlaying()
            }
        }
        emit("change")
    }

    private func activateSession() {
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.playback, mode: .spokenAudio)
            try session.setActive(true)
        } catch {
            CAPLog.print("NativeAudio: could not activate the audio session: \(error)")
        }
    }

    private func timeControlChanged() {
        if player.timeControlStatus == .playing {
            // Playing again: any outage is over.
            failingSince = nil
            reconnectAttempts = 0
            waitingSince = nil
            endBackgroundTask()
        }
        emit("change")
        updateNowPlaying()
        scheduleTimer()
    }

    private func itemEnded(_ note: Notification) {
        guard note.object as? AVPlayerItem === item else { return }
        ended = true
        playWhenReady = false
        lastPosition = currentDuration()
        endBackgroundTask()
        scheduleTimer()
        emit("change")
        updateNowPlaying()
    }

    // MARK: - Reconnecting

    // The download failed, or waited too long for data. Try again from the same place, at most
    // 5 seconds apart (at once when the network returns), until playing resumes or giveUpAfter.
    private func connectionFailed(_ failure: Error?) {
        guard item != nil, error == nil else { return }
        lastPosition = pendingSeek ?? lastPosition
        if Self.isPermanent(failure) {
            giveUp("ERROR_CODE_IO_BAD_HTTP_STATUS")
            return
        }
        guard playWhenReady else {
            // Paused: reconnect when the listener presses play.
            reconnectOnPlay = true
            emit("change")
            return
        }
        let now = Date()
        let since = failingSince ?? now
        failingSince = since
        if now.timeIntervalSince(since) >= Self.giveUpAfter {
            giveUp("ERROR_CODE_IO_NETWORK_CONNECTION_FAILED")
            return
        }
        // A suspended app can't reconnect; ask for time to finish.
        beginBackgroundTask()
        reconnectAttempts += 1
        let delay = networkAvailable ? min(Double(reconnectAttempts), 5) : 5
        let work = DispatchWorkItem { [weak self] in self?.reconnect() }
        reconnectWork?.cancel()
        reconnectWork = work
        DispatchQueue.main.asyncAfter(deadline: .now() + delay, execute: work)
        scheduleTimer()
        emit("change")
        updateNowPlaying()
    }

    private func reconnect() {
        reconnectWork = nil
        guard source != nil, playWhenReady else { return }
        loadItem(at: lastPosition)
    }

    private func cancelReconnect() {
        reconnectWork?.cancel()
        reconnectWork = nil
    }

    private func networkChanged(available: Bool) {
        let returned = available && !networkAvailable
        networkAvailable = available
        if returned, reconnectWork != nil {
            cancelReconnect()
            reconnect()
        }
    }

    // The player stops and reports an error, keeping its place; the page offers Retry.
    private func giveUp(_ code: String) {
        cancelReconnect()
        error = code
        player.pause()
        failingSince = nil
        waitingSince = nil
        endBackgroundTask()
        scheduleTimer()
        emit("change")
        updateNowPlaying()
    }

    // AVPlayer can wait for data indefinitely on a connection that went quiet without failing.
    private func checkForSilentStall() {
        guard playWhenReady, error == nil, reconnectWork == nil, let item, item.status == .readyToPlay,
              player.timeControlStatus == .waitingToPlayAtSpecifiedRate
        else {
            waitingSince = nil
            return
        }
        let buffered = bufferedEnd()
        let now = Date()
        guard let since = waitingSince, buffered <= waitingBufferedEnd + 0.5 else {
            // Waiting began, or data is still arriving.
            if waitingSince == nil, !inForeground {
                beginBackgroundTask()
            }
            waitingSince = now
            waitingBufferedEnd = buffered
            return
        }
        if now.timeIntervalSince(since) >= Self.silentStallLimit {
            waitingSince = nil
            connectionFailed(nil)
        }
    }

    private static func isPermanent(_ failure: Error?) -> Bool {
        var next = failure as NSError?
        while let error = next {
            switch (error.domain, error.code) {
            // CoreMedia's HTTP 404 and 403.
            case ("CoreMediaErrorDomain", -12938), ("CoreMediaErrorDomain", -12660):
                return true
            case (NSURLErrorDomain, NSURLErrorFileDoesNotExist),
                 (NSURLErrorDomain, NSURLErrorBadURL),
                 (NSURLErrorDomain, NSURLErrorUnsupportedURL):
                return true
            case (AVFoundationErrorDomain, AVError.Code.fileFormatNotRecognized.rawValue),
                 (AVFoundationErrorDomain, AVError.Code.decodeFailed.rawValue):
                return true
            default:
                next = error.userInfo[NSUnderlyingErrorKey] as? NSError
            }
        }
        return false
    }

    private func beginBackgroundTask() {
        guard backgroundTask == .invalid else { return }
        backgroundTask = UIApplication.shared.beginBackgroundTask(withName: "Reconnect office audio") { [weak self] in
            self?.endBackgroundTask()
        }
    }

    private func endBackgroundTask() {
        guard backgroundTask != .invalid else { return }
        UIApplication.shared.endBackgroundTask(backgroundTask)
        backgroundTask = .invalid
    }

    // MARK: - System events

    private func handleInterruption(_ note: Notification) {
        guard let info = note.userInfo,
              let rawType = info[AVAudioSessionInterruptionTypeKey] as? UInt,
              let type = AVAudioSession.InterruptionType(rawValue: rawType)
        else { return }
        switch type {
        case .began:
            if #available(iOS 14.5, *),
               let rawReason = info[AVAudioSessionInterruptionReasonKey] as? UInt,
               AVAudioSession.InterruptionReason(rawValue: rawReason) == .appWasSuspended {
                return
            }
            // A call, an alarm, Siri: the system has paused the player.
            resumeAfterInterruption = playWhenReady
            if playWhenReady {
                pausePlayback()
            }
        case .ended:
            let rawOptions = info[AVAudioSessionInterruptionOptionKey] as? UInt ?? 0
            if resumeAfterInterruption, AVAudioSession.InterruptionOptions(rawValue: rawOptions).contains(.shouldResume) {
                resumePlayback()
            }
            resumeAfterInterruption = false
        @unknown default:
            break
        }
    }

    // Headphones unplugged or Bluetooth gone: pause, rather than carry on out loud.
    private func handleRouteChange(_ note: Notification) {
        guard let rawReason = note.userInfo?[AVAudioSessionRouteChangeReasonKey] as? UInt,
              AVAudioSession.RouteChangeReason(rawValue: rawReason) == .oldDeviceUnavailable,
              playWhenReady
        else { return }
        pausePlayback()
    }

    private func resumePlayback() {
        guard source != nil, let item else { return }
        playWhenReady = true
        if error != nil || reconnectOnPlay || item.status == .failed {
            failingSince = nil
            loadItem(at: currentPosition())
        } else if item.status == .readyToPlay {
            if ended {
                seek(to: 0)
            }
            startPlayback()
        }
        scheduleTimer()
        emit("change")
        updateNowPlaying()
    }

    private func skip(by offset: Double) {
        seek(to: currentPosition() + offset)
        updateNowPlaying()
    }

    // MARK: - Lock screen, Control Center, headset

    private func setUpRemoteCommands() {
        let commands = MPRemoteCommandCenter.shared()
        commands.playCommand.addTarget { [weak self] _ in
            guard let self, self.source != nil else { return .noActionableNowPlayingItem }
            self.resumePlayback()
            return .success
        }
        commands.pauseCommand.addTarget { [weak self] _ in
            guard let self, self.source != nil else { return .noActionableNowPlayingItem }
            self.pausePlayback()
            return .success
        }
        commands.togglePlayPauseCommand.addTarget { [weak self] _ in
            guard let self, self.source != nil else { return .noActionableNowPlayingItem }
            if self.playWhenReady {
                self.pausePlayback()
            } else {
                self.resumePlayback()
            }
            return .success
        }
        commands.skipForwardCommand.preferredIntervals = [NSNumber(value: Self.skipInterval)]
        commands.skipForwardCommand.addTarget { [weak self] event in
            guard let self, self.source != nil else { return .noActionableNowPlayingItem }
            self.skip(by: (event as? MPSkipIntervalCommandEvent)?.interval ?? Self.skipInterval)
            return .success
        }
        commands.skipBackwardCommand.preferredIntervals = [NSNumber(value: Self.skipInterval)]
        commands.skipBackwardCommand.addTarget { [weak self] event in
            guard let self, self.source != nil else { return .noActionableNowPlayingItem }
            self.skip(by: -((event as? MPSkipIntervalCommandEvent)?.interval ?? Self.skipInterval))
            return .success
        }
        commands.changePlaybackPositionCommand.addTarget { [weak self] event in
            guard let self, self.source != nil,
                  let event = event as? MPChangePlaybackPositionCommandEvent
            else { return .commandFailed }
            self.seek(to: event.positionTime)
            self.updateNowPlaying()
            return .success
        }
        enableRemoteCommands(false)
    }

    private func enableRemoteCommands(_ enabled: Bool) {
        let commands = MPRemoteCommandCenter.shared()
        for command in [
            commands.playCommand,
            commands.pauseCommand,
            commands.togglePlayPauseCommand,
            commands.skipForwardCommand,
            commands.skipBackwardCommand,
            commands.changePlaybackPositionCommand,
        ] {
            command.isEnabled = enabled
        }
    }

    // Now Playing extrapolates the time itself from the rate; update it on each change.
    private func updateNowPlaying() {
        guard source != nil else {
            MPNowPlayingInfoCenter.default().nowPlayingInfo = nil
            return
        }
        var info: [String: Any] = [
            MPMediaItemPropertyTitle: title,
            MPMediaItemPropertyArtist: artist,
            MPNowPlayingInfoPropertyElapsedPlaybackTime: currentPosition(),
            MPNowPlayingInfoPropertyPlaybackRate: player.timeControlStatus == .playing ? Double(rate) : 0.0,
            MPNowPlayingInfoPropertyDefaultPlaybackRate: Double(rate),
            MPNowPlayingInfoPropertyMediaType: MPNowPlayingInfoMediaType.audio.rawValue,
        ]
        let duration = currentDuration()
        if duration > 0 {
            info[MPMediaItemPropertyPlaybackDuration] = duration
        }
        if let artwork {
            info[MPMediaItemPropertyArtwork] = artwork
        }
        MPNowPlayingInfoCenter.default().nowPlayingInfo = info
    }

    // An image from the app's bundled web assets (app/public).
    private static func loadArtwork(_ path: String) -> MPMediaItemArtwork? {
        let relative = path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        guard !relative.isEmpty, !relative.contains(".."),
              let file = Bundle.main.resourceURL?.appendingPathComponent("public").appendingPathComponent(relative),
              let image = UIImage(contentsOfFile: file.path)
        else { return nil }
        return MPMediaItemArtwork(boundsSize: image.size) { _ in image }
    }

    private static let userAgent: String = {
        let version = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "0"
        return "DailyOffice2019/\(version) (iOS \(UIDevice.current.systemVersion))"
    }()

    // MARK: - Status

    private func scheduleTimer() {
        let active = source != nil && (playWhenReady || reconnectWork != nil)
        guard active else {
            timer?.invalidate()
            timer = nil
            return
        }
        let interval: TimeInterval = inForeground ? 0.25 : 1
        if let timer, timer.timeInterval == interval {
            return
        }
        timer?.invalidate()
        timer = Timer.scheduledTimer(withTimeInterval: interval, repeats: true) { [weak self] _ in
            self?.tick()
        }
    }

    private func tick() {
        lastPosition = currentPosition()
        checkForSilentStall()
        if inForeground {
            emit("tick")
        }
    }

    private func currentPosition() -> Double {
        if let pendingSeek {
            return pendingSeek
        }
        if let item, item.status == .readyToPlay, error == nil, reconnectWork == nil {
            let seconds = item.currentTime().seconds
            if seconds.isFinite {
                return max(0, seconds)
            }
        }
        return lastPosition
    }

    private func currentDuration() -> Double {
        guard let seconds = item?.duration.seconds, seconds.isFinite, seconds > 0 else { return 0 }
        return seconds
    }

    private func bufferedEnd() -> Double {
        guard let item else { return 0 }
        let position = currentPosition()
        var end = 0.0
        for value in item.loadedTimeRanges {
            let range = value.timeRangeValue
            let start = range.start.seconds
            let rangeEnd = range.end.seconds
            guard start.isFinite, rangeEnd.isFinite else { continue }
            if start <= position + 0.5, rangeEnd > end {
                end = rangeEnd
            }
        }
        return end
    }

    private func stateName() -> String {
        guard source != nil, let item, error == nil else { return "idle" }
        if ended {
            return "ended"
        }
        if reconnectWork != nil || item.status != .readyToPlay {
            return "buffering"
        }
        if playWhenReady, player.timeControlStatus == .waitingToPlayAtSpecifiedRate {
            return "buffering"
        }
        return "ready"
    }

    private func status(_ event: String) -> [String: Any] {
        var status: [String: Any] = ["event": event, "state": stateName()]
        guard let source else { return status }
        status["url"] = source
        status["playWhenReady"] = playWhenReady
        status["isPlaying"] = playWhenReady && player.timeControlStatus == .playing
        status["position"] = currentPosition()
        status["duration"] = currentDuration()
        status["buffered"] = bufferedEnd()
        status["rate"] = Double(rate)
        if let error {
            status["error"] = error
        }
        return status
    }

    private func emit(_ event: String) {
        guard source != nil else { return }
        notifyListeners("status", data: status(event))
    }
}
