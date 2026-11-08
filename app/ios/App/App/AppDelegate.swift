import UIKit
import AVFoundation
import Capacitor
import Firebase
import Intents
import WidgetKit

@UIApplicationMain
class AppDelegate: UIResponder, UIApplicationDelegate {

    func application(_ application: UIApplication, didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        // Configure Firebase
        FirebaseApp.configure()

        // Audio here is spoken word: keep it going with the screen locked or the app in the
        // background (with UIBackgroundModes "audio" in Info.plist), and play it even when the
        // ring/silent switch is set to silent. Office audio plays through NativeAudioPlugin,
        // which sets the same category when it starts.
        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio)
        } catch {
            print("Could not set the audio session category: \(error)")
        }

        // Offline downloads keep fresh in the background (OfflineSyncPlugin.swift). iOS requires
        // the handler to be registered before launching finishes.
        OfflineSyncPlugin.registerBackgroundTask()
        // Audio downloads that finish while the app is open are only filed once their session
        // exists again; open it now rather than waiting for the next background run.
        OfflineAudioDownloads.shared.reconnect()

        // Offices and psalms go in Spotlight's semantic index, which Siri searches
        // (Voice/VoiceIntents.swift).
        if #available(iOS 18.0, *) {
            VoiceSpotlight.indexIfNeeded()
        }

        // Play pressed with nothing to resume (a headset, the car, Siri's "play") plays the office
        // for now; Siri learns the offices' names as media titles (Voice/VoicePlayback.swift).
        OfficePlayer.shared.onPlayWithNothingQueued = {
            Task { @MainActor in OfficePlayback.playNow() }
        }
        VoiceVocabulary.register()

        // The calendar widget (DailyOfficeWidget) reads the day again whenever the app opens.
        WidgetCenter.shared.reloadAllTimelines()

        // Override point for customization after application launch.
        return true
    }

    func applicationWillResignActive(_ application: UIApplication) {
        // Sent when the application is about to move from active to inactive state. This can occur for certain types of temporary interruptions (such as an incoming phone call or SMS message) or when the user quits the application and it begins the transition to the background state.
        // Use this method to pause ongoing tasks, disable timers, and invalidate graphics rendering callbacks. Games should use this method to pause the game.
    }

    func applicationDidEnterBackground(_ application: UIApplication) {
        // Use this method to release shared resources, save user data, invalidate timers, and store enough application state information to restore your application to its current state in case it is terminated later.
        // If your application supports background execution, this method is called instead of applicationWillTerminate: when the user quits.
    }

    func applicationWillEnterForeground(_ application: UIApplication) {
        // Called as part of the transition from the background to the active state; here you can undo many of the changes made on entering the background.
    }

    func applicationDidBecomeActive(_ application: UIApplication) {
        // Restart any tasks that were paused (or not yet started) while the application was inactive. If the application was previously in the background, optionally refresh the user interface.
    }

    func applicationWillTerminate(_ application: UIApplication) {
        // Called when the application is about to terminate. Save data if appropriate. See also applicationDidEnterBackground:.
    }

    // Offline audio finished downloading while the app was suspended or not running
    // (OfflineAudioDownloads in OfflineSyncPlugin.swift).
    func application(_ application: UIApplication, handleEventsForBackgroundURLSession identifier: String, completionHandler: @escaping () -> Void) {
        guard identifier == OfflineAudioDownloads.identifier else {
            completionHandler()
            return
        }
        OfflineAudioDownloads.shared.handleEvents(completion: completionHandler)
    }

    // Siri's "Play Compline on The Daily Office" (and the same in CarPlay) is an INPlayMediaIntent,
    // handled here in the app rather than in an extension, so it plays through the app's own
    // player (Voice/VoicePlayback.swift).
    func application(_ application: UIApplication, handlerFor intent: INIntent) -> Any? {
        VoiceLog.note("Handler asked for \(String(describing: type(of: intent)))")
        return intent is INPlayMediaIntent ? PlayMediaIntentHandler() : nil
    }

    // The handler plays straight away; this only catches a .handleInApp delivery, should iOS
    // send one.
    func application(_ application: UIApplication, handle intent: INIntent, completionHandler: @escaping (INIntentResponse) -> Void) {
        VoiceLog.note("Handle in app: \(String(describing: type(of: intent)))")
        guard let intent = intent as? INPlayMediaIntent else {
            completionHandler(INPlayMediaIntentResponse(code: .failure, userActivity: nil))
            return
        }
        Task { @MainActor in
            PlayMediaIntentHandler.play(intent, completion: completionHandler)
        }
    }

    // The window, and links that open the app, belong to the scene now (SceneDelegate.swift).

}
