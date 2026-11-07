import Capacitor
import UIKit

/// The app's Capacitor screen, with the plugins that live in this app rather than in npm packages.
class MainViewController: CAPBridgeViewController {
    /// Where a foldable iPhone's screen divides (FoldPlugin.swift).
    private let foldPlugin = FoldPlugin()

    override open func capacitorDidLoad() {
        // Office audio (NativeAudioPlugin.swift).
        bridge?.registerPluginInstance(NativeAudioPlugin())
        // Background downloads for offline use (OfflineSyncPlugin.swift).
        bridge?.registerPluginInstance(OfflineSyncPlugin())
        bridge?.registerPluginInstance(foldPlugin)
        // Siri and Shortcuts open pages through this (Voice/VoiceLaunchPlugin.swift).
        bridge?.registerPluginInstance(VoiceLaunchPlugin())
    }

    // Folding, unfolding, and turning iPhone Duo lay the screen out again.
    override open func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        foldPlugin.refresh()
    }
}
