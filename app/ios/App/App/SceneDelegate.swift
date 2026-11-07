import Capacitor
import UIKit

/// The app's one window. iOS 27 only launches apps built with its SDK that use scenes; the window
/// and its MainViewController come from Main.storyboard (UISceneStoryboardFile in Info.plist).
/// Links that open the app arrive here now instead of in AppDelegate, and Capacitor passes them
/// on to the App plugin's appUrlOpen as before.
class SceneDelegate: UIResponder, UIWindowSceneDelegate {
    var window: UIWindow?

    func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options connectionOptions: UIScene.ConnectionOptions) {
        // Also delivers a link the app was launched with, once the page has loaded.
        SceneDelegateProxy.shared.scene(scene, willConnectTo: session, options: connectionOptions)
        // A Siri Suggestion or Handoff the app was launched from (Voice/VoiceLaunchPlugin.swift).
        for activity in connectionOptions.userActivities {
            if let path = VoiceDonations.path(for: activity) { VoiceLaunch.open(path: path) }
        }
    }

    func scene(_ scene: UIScene, openURLContexts URLContexts: Set<UIOpenURLContext>) {
        SceneDelegateProxy.shared.scene(scene, openURLContexts: URLContexts)
    }

    func scene(_ scene: UIScene, continue userActivity: NSUserActivity) {
        if let path = VoiceDonations.path(for: userActivity) {
            VoiceLaunch.open(path: path)
            return
        }
        SceneDelegateProxy.shared.scene(scene, continue: userActivity)
    }
}
