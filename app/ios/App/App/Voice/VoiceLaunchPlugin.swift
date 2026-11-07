import Capacitor
import CoreSpotlight
import Intents
import UIKit
import UniformTypeIdentifiers

/// Opens app pages for Siri, and tells the system what the listener opens and plays.
///
/// App Intents (VoiceIntents.swift) and Siri Suggestions call `VoiceLaunch.open(path:)`; the page
/// gets an "open" event and goes there (app/src/helpers/voice.js). A request made while the app is
/// still starting waits until the page is listening.
///
/// The page calls `donate` when someone opens or plays an office, the readings, or a psalm. That
/// becomes the screen's NSUserActivity (Siri Suggestions and Spotlight on iOS 15 and later, and
/// what's on screen for Siri on iOS 18.2 and later) and, on iOS 17 and later, a donated App Intent,
/// so Siri learns when someone usually prays Compline.
@objc(VoiceLaunchPlugin)
public class VoiceLaunchPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "VoiceLaunchPlugin"
    public let jsName = "VoiceLaunch"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "donate", returnType: CAPPluginReturnPromise),
    ]

    override public func load() {
        VoiceLaunch.attach(self)
    }

    func emitOpen(_ path: String) {
        // Kept until the page's listener takes it, if it isn't listening yet.
        notifyListeners("open", data: ["path": path], retainUntilConsumed: true)
    }

    @objc func donate(_ call: CAPPluginCall) {
        guard let activity = VoiceActivity(call.options) else {
            call.reject("Not something to remember")
            return
        }
        DispatchQueue.main.async { [weak self] in
            VoiceDonations.donate(activity, on: self?.bridge?.viewController)
            call.resolve()
        }
    }
}

/// Where Siri's requests to open a page go.
enum VoiceLaunch {
    private static weak var plugin: VoiceLaunchPlugin?
    private static var pending: String?

    static func attach(_ plugin: VoiceLaunchPlugin) {
        DispatchQueue.main.async {
            self.plugin = plugin
            if let path = pending {
                pending = nil
                plugin.emitOpen(path)
            }
        }
    }

    /// Opens the app at a page: "/office/compline?autoplay=1".
    static func open(path: String) {
        DispatchQueue.main.async {
            if let plugin {
                plugin.emitOpen(path)
            } else {
                pending = path
            }
        }
    }

    static func open(url: URL) -> Bool {
        guard let path = VoiceLinks.path(from: url) else { return false }
        open(path: path)
        return true
    }
}

/// Something the listener opened or played, as the page reports it.
struct VoiceActivity {
    enum Kind: String {
        case office
        case readings
        case psalm
    }

    let kind: Kind
    let title: String
    let path: String
    let played: Bool
    let office: Office?
    let readings: ReadingsService?
    let psalm: Int?

    init?(_ options: [AnyHashable: Any]) {
        guard let kindName = options["kind"] as? String, let kind = Kind(rawValue: kindName) else { return nil }
        self.kind = kind
        played = options["played"] as? Bool ?? false
        switch kind {
        case .office:
            guard let found = Office.find(
                serviceType: options["serviceType"] as? String ?? "office",
                slug: options["office"] as? String ?? ""
            ) else { return nil }
            office = found
            readings = nil
            psalm = nil
            title = found.title
            path = found.path
        case .readings:
            let service = ReadingsService.allCases.first { $0.slug == options["service"] as? String } ?? .morningPrayer
            office = nil
            readings = service
            psalm = nil
            title = "Readings for \(service.title)"
            path = service.path
        case .psalm:
            guard let number = (options["number"] as? NSNumber)?.intValue ?? Int(options["number"] as? String ?? "") else { return nil }
            office = nil
            readings = nil
            psalm = number
            title = "Psalm \(number)"
            path = "/psalm/\(number)/"
        }
    }

    /// What Siri Suggestions offer to say for it.
    var invocationPhrase: String {
        switch kind {
        case .office: return played ? "Play \(title)" : "Pray \(title)"
        case .readings: return played ? "Play today’s readings" : "Today’s readings"
        case .psalm: return "Open \(title)"
        }
    }
}

enum VoiceDonations {
    /// Activities Siri can bring back (NSUserActivityTypes in Info.plist).
    static let activityType = "com.dailyoffice.dailyoffice2019.open"

    static func donate(_ activity: VoiceActivity, on viewController: UIViewController?) {
        let userActivity = NSUserActivity(activityType: activityType)
        userActivity.title = activity.title
        let target = VoiceLinks.adding(autoplay: activity.played, to: activity.path)
        userActivity.userInfo = ["path": target]
        userActivity.requiredUserInfoKeys = ["path"]
        userActivity.persistentIdentifier = target
        userActivity.isEligibleForSearch = true
        userActivity.isEligibleForPrediction = true
        userActivity.isEligibleForHandoff = true
        userActivity.webpageURL = VoiceLinks.webURL(path: activity.path)
        userActivity.suggestedInvocationPhrase = activity.invocationPhrase
        let attributes = CSSearchableItemAttributeSet(contentType: UTType.text)
        attributes.contentDescription = activity.kind == .office ? "Pray \(activity.title) in The Daily Office" : activity.title
        userActivity.contentAttributeSet = attributes
        if #available(iOS 18.2, *) {
            VoiceEntityAnnotations.annotate(userActivity, for: activity)
        }
        viewController?.userActivity = userActivity
        userActivity.becomeCurrent()

        if #available(iOS 17.0, *) {
            VoiceIntentDonations.donate(activity)
        }
    }

    /// The page a Siri Suggestion or Handoff names.
    static func path(for userActivity: NSUserActivity) -> String? {
        if userActivity.activityType == activityType {
            return userActivity.userInfo?["path"] as? String
        }
        return nil
    }
}
