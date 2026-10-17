import Capacitor
import UIKit

/// The app's Capacitor screen, with the plugins that live in this app rather than in npm packages.
class MainViewController: CAPBridgeViewController {
    override open func capacitorDidLoad() {
        // Office audio (NativeAudioPlugin.swift).
        bridge?.registerPluginInstance(NativeAudioPlugin())
    }
}
