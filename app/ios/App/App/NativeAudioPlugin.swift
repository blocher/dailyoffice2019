import Capacitor
import Foundation

/// The page's handle on the app's one audio player (OfficePlayer.swift).
///
/// It speaks the same protocol as android/.../audio/NativeAudioPlugin.java, which
/// app/src/helpers/nativeAudio.js wraps for the page: every method resolves with the player's
/// status, and a "status" event reports each change.
///
/// CarPlay plays through the same player, so the page's commands name their track: `play` with a
/// track other than the one loaded loads the page's track again, and `pause`, `seekTo`, `setRate`
/// and `stop` for another track leave the car's audio alone.
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

    private var player: OfficePlayer { OfficePlayer.shared }

    override public func load() {
        DispatchQueue.main.async {
            OfficePlayer.shared.onStatus = { [weak self] status in
                self?.notifyListeners("status", data: status)
            }
        }
    }

    /// Whether a command is for a track other than the one loaded.
    private func isForAnotherTrack(_ call: CAPPluginCall) -> Bool {
        guard let url = call.getString("url"), !url.isEmpty else { return false }
        return url != player.currentSource
    }

    private func load(_ call: CAPPluginCall, source: String) {
        player.setSource(
            source,
            title: call.getString("title") ?? "",
            artist: call.getString("artist") ?? "",
            artworkPath: call.getString("artwork") ?? "",
            rate: call.getDouble("rate")
        )
    }

    @objc func setSource(_ call: CAPPluginCall) {
        guard let source = call.getString("url"), !source.isEmpty, URL(string: source) != nil else {
            call.reject("A url is required")
            return
        }
        DispatchQueue.main.async {
            self.load(call, source: source)
            call.resolve(self.player.status("command"))
        }
    }

    @objc func play(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            // The car may have started another track since the page loaded its own.
            if self.isForAnotherTrack(call), let source = call.getString("url") {
                self.load(call, source: source)
            }
            do {
                try self.player.play()
                call.resolve(self.player.status("command"))
            } catch {
                call.reject(error.localizedDescription)
            }
        }
    }

    @objc func pause(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            if !self.isForAnotherTrack(call) {
                self.player.pause()
            }
            call.resolve(self.player.status("command"))
        }
    }

    @objc func seekTo(_ call: CAPPluginCall) {
        guard let position = call.getDouble("position"), position.isFinite, position >= 0 else {
            call.reject("A position is required")
            return
        }
        DispatchQueue.main.async {
            if !self.isForAnotherTrack(call) {
                self.player.seekTo(position)
            }
            call.resolve(self.player.status("command"))
        }
    }

    @objc func setRate(_ call: CAPPluginCall) {
        guard let rate = call.getDouble("rate"), rate.isFinite, rate > 0 else {
            call.reject("A rate is required")
            return
        }
        DispatchQueue.main.async {
            if !self.isForAnotherTrack(call) {
                self.player.setRate(rate)
            }
            call.resolve(self.player.status("command"))
        }
    }

    @objc func stop(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            if !self.isForAnotherTrack(call) {
                self.player.stop()
            }
            call.resolve(self.player.status("command"))
        }
    }

    @objc func getStatus(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            call.resolve(self.player.status("command"))
        }
    }
}
