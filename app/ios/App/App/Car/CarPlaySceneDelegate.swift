import CarPlay
import UIKit

/// The Daily Office in CarPlay: a Pray tab with the office for now and all eight offices, and a
/// Readings tab with the day's readings. Choosing one finds its audio (OfficeAudioResolver) and
/// plays it through the app's one player (OfficePlayback, Voice/VoicePlayback.swift, as Siri
/// does), then shows Now Playing, whose controls
/// the player already answers (play, pause, 15-second skips, scrubbing).
///
/// CarPlay can start the app with no screen of its own on the phone, so none of this needs the
/// page. The list header names the day in the church calendar (LiturgicalCalendar.swift).
final class CarPlaySceneDelegate: UIResponder, CPTemplateApplicationSceneDelegate {
    private var interfaceController: CPInterfaceController?
    private var prayTemplate: CPListTemplate?
    private var readingsTemplate: CPListTemplate?
    private var items: [OfficeAudioResolver.Request: [CPListItem]] = [:]
    private var dayHeadline: String?
    private var statusObserver: NSObjectProtocol?

    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didConnect interfaceController: CPInterfaceController
    ) {
        self.interfaceController = interfaceController
        let pray = CPListTemplate(title: "Pray", sections: praySections())
        pray.tabTitle = "Pray"
        pray.tabImage = UIImage(systemName: "book")
        let readings = CPListTemplate(title: "Readings", sections: readingsSections())
        readings.tabTitle = "Readings"
        readings.tabImage = UIImage(systemName: "text.book.closed")
        prayTemplate = pray
        readingsTemplate = readings
        interfaceController.setRootTemplate(CPTabBarTemplate(templates: [pray, readings]), animated: false, completion: nil)

        CPNowPlayingTemplate.shared.isUpNextButtonEnabled = false
        CPNowPlayingTemplate.shared.isAlbumArtistButtonEnabled = false

        statusObserver = NotificationCenter.default.addObserver(
            forName: OfficePlayer.statusChanged, object: nil, queue: .main
        ) { [weak self] _ in
            self?.showPlaying()
        }
        loadDay()
    }

    func templateApplicationScene(
        _ templateApplicationScene: CPTemplateApplicationScene,
        didDisconnectInterfaceController interfaceController: CPInterfaceController
    ) {
        if let statusObserver { NotificationCenter.default.removeObserver(statusObserver) }
        statusObserver = nil
        self.interfaceController = nil
        items = [:]
    }

    // MARK: - Lists

    private func praySections() -> [CPListSection] {
        let family = AppPreferences.prefersFamilyPrayer
        let now = Office.current(family: family)
        let other = Office.current(family: !family)
        return [
            CPListSection(
                items: [item(.office(now), detail: "For this time of day"), item(.office(other), detail: nil)],
                header: dayHeadline ?? "Now",
                sectionIndexTitle: nil
            ),
            CPListSection(
                items: [Office.morningPrayer, .middayPrayer, .eveningPrayer, .compline].map { item(.office($0), detail: nil) },
                header: "The Daily Office",
                sectionIndexTitle: nil
            ),
            CPListSection(
                items: [Office.familyMorning, .familyMidday, .familyEarlyEvening, .familyCloseOfDay].map {
                    item(.office($0), detail: nil)
                },
                header: "Family Prayer",
                sectionIndexTitle: nil
            ),
        ]
    }

    private func readingsSections() -> [CPListSection] {
        [
            CPListSection(
                items: ReadingsService.allCases.map { item(.readings($0), detail: "Psalms and lessons, read aloud") },
                header: dayHeadline ?? "Today",
                sectionIndexTitle: nil
            ),
        ]
    }

    private func item(_ request: OfficeAudioResolver.Request, detail: String?) -> CPListItem {
        let title: String
        switch request {
        case .office(let office): title = office.title
        case .readings(let service): title = service.title
        }
        let item = CPListItem(text: title, detailText: detail, image: UIImage(systemName: icon(for: request)))
        item.handler = { [weak self] _, completion in
            self?.play(request, completion: completion)
        }
        item.isPlaying = OfficePlayer.shared.currentSource == OfficePlayback.currentSource
            && request == OfficePlayback.current && OfficePlayer.shared.isPlaying
        items[request, default: []].append(item)
        return item
    }

    private func icon(for request: OfficeAudioResolver.Request) -> String {
        switch request {
        case .office(.morningPrayer), .office(.familyMorning): return "sunrise"
        case .office(.middayPrayer), .office(.familyMidday): return "sun.max"
        case .office(.eveningPrayer), .office(.familyEarlyEvening): return "sunset"
        case .office: return "moon.stars"
        case .readings: return "text.book.closed"
        }
    }

    /// The day's name above the lists: "Saturday · Willibrord".
    private func loadDay() {
        Task { [weak self] in
            guard let day = try? await CalendarAPI.day(Date()) else { return }
            let name = day.headline.components(separatedBy: ",").first ?? day.headline
            await MainActor.run {
                guard let self else { return }
                self.dayHeadline = name.count > 48 ? String(name.prefix(47)) + "…" : name
                self.items = [:]
                self.prayTemplate?.updateSections(self.praySections())
                self.readingsTemplate?.updateSections(self.readingsSections())
            }
        }
    }

    // MARK: - Playing

    private func play(_ request: OfficeAudioResolver.Request, completion: @escaping () -> Void) {
        Task { @MainActor [weak self] in
            do {
                try await OfficePlayback.play(request)
                self?.showPlaying()
                completion()
                self?.showNowPlaying()
            } catch {
                completion()
                self?.showAlert(error.localizedDescription)
            }
        }
    }

    private func showNowPlaying() {
        guard let interfaceController else { return }
        if interfaceController.topTemplate === CPNowPlayingTemplate.shared { return }
        interfaceController.pushTemplate(CPNowPlayingTemplate.shared, animated: true, completion: nil)
    }

    /// Marks what is playing in the lists, whether CarPlay, Siri or the headset started it
    /// (nothing, once the page has loaded a track of its own).
    private func showPlaying() {
        let player = OfficePlayer.shared
        let playing = player.currentSource != nil && player.currentSource == OfficePlayback.currentSource
            ? OfficePlayback.current : nil
        for (request, listItems) in items {
            for item in listItems {
                item.isPlaying = request == playing && player.isPlaying
            }
        }
    }

    private func showAlert(_ message: String) {
        guard let interfaceController else { return }
        let alert = CPAlertTemplate(
            titleVariants: [message],
            actions: [CPAlertAction(title: "OK", style: .cancel) { [weak interfaceController] _ in
                interfaceController?.dismissTemplate(animated: true, completion: nil)
            }]
        )
        interfaceController.presentTemplate(alert, animated: true, completion: nil)
    }
}
