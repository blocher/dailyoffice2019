import Capacitor
import UIKit

/// Where a foldable iPhone's screen divides (iPhone Duo), so Book view can open a two-page
/// spread across the fold like a book (app/src/helpers/fold.js).
///
/// UIKit reports the fold as a division region of the web view; the hinge says whether the
/// phone is partly folded (`active`) or flat. The fold sent is the crease itself, without the
/// margins UIKit adds around it for controls. The page calls:
///
///     getFold()  -> { hasFold, x, y, width, height, active }  (points, in the web view)
///
/// and listens for "foldChange" with the same data whenever the hinge moves or the layout
/// changes (folding, unfolding, or turning the phone).
@objc(FoldPlugin)
public class FoldPlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "FoldPlugin"
    public let jsName = "Fold"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "getFold", returnType: CAPPluginReturnPromise),
    ]

    private var hingeInteraction: UIInteraction?
    private var partlyFolded: Bool?
    private var lastFold: [String: Any] = [:]

    override public func load() {
        DispatchQueue.main.async { [weak self] in
            guard #available(iOS 27.1, *), let self, let webView = self.bridge?.webView else { return }
            let interaction = UIHingeInteraction { [weak self] _, update in
                guard let self else { return }
                if let status = update.hinge?.status, status != .unknown {
                    self.partlyFolded = status == .partiallyOpen
                }
                self.refresh()
                // The reserved region can settle a moment after the hinge reports.
                DispatchQueue.main.async { [weak self] in self?.refresh() }
            }
            webView.addInteraction(interaction)
            self.hingeInteraction = interaction
        }
    }

    @objc func getFold(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            call.resolve(self.currentFold())
        }
    }

    /// Tells the page about a change; called on the main thread.
    func refresh() {
        let fold = currentFold()
        if NSDictionary(dictionary: fold).isEqual(to: lastFold) { return }
        lastFold = fold
        notifyListeners("foldChange", data: fold)
    }

    private func currentFold() -> [String: Any] {
        guard #available(iOS 27.1, *), let webView = bridge?.webView,
              let region = webView.reservedRegions(kind: .division, options: .includeInactive).first
        else {
            return ["hasFold": false]
        }
        let frame = region.frame.inset(by: region.margins)
        return [
            "hasFold": true,
            "x": frame.minX,
            "y": frame.minY,
            "width": frame.width,
            "height": frame.height,
            "active": partlyFolded ?? region.isActive,
        ]
    }
}
