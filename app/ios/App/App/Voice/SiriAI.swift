// Siri AI Developer Preview (iOS 27.3 and later).
//
// Offers each of the app's actions (VoiceIntents.swift) to Siri AI as a tool, so it can be asked
// in any words ("put on night prayers for the kids", "is this Friday a fast?") and combine them
// with the app skills in Skills.skillsbundle.
//
// Only built with the iOS 27.3 SDK or later: SiriAI.xcconfig sets SIRI_AI_PREVIEW and adds the
// skills bundle for those SDKs alone, so the app still builds with the current Xcode for the App
// Store. Apple doesn't offer Siri AI to App Store or external TestFlight builds during the preview;
// internal TestFlight builds and development builds on a device with Apple Intelligence get it.
//
// The intents keep their titles, descriptions and parameter descriptions written for someone who
// doesn't know the app, which is what Siri reads to choose a tool.
#if SIRI_AI_PREVIEW
import AppIntents

@available(iOS 27.3, *) extension PlayOfficeIntent: ToolIntent {}
@available(iOS 27.3, *) extension OpenOfficeIntent: ToolIntent {}
@available(iOS 27.3, *) extension PlayReadingsIntent: ToolIntent {}
@available(iOS 27.3, *) extension OpenReadingsIntent: ToolIntent {}
@available(iOS 27.3, *) extension OpenPsalmIntent: ToolIntent {}
@available(iOS 27.3, *) extension ReadPsalmIntent: ToolIntent {}
@available(iOS 27.3, *) extension OpenPageIntent: ToolIntent {}
@available(iOS 27.3, *) extension OpenDayIntent: ToolIntent {}
@available(iOS 27.3, *) extension GetLiturgicalDayIntent: ToolIntent {}
@available(iOS 27.3, *) extension GetLiturgicalColorIntent: ToolIntent {}
@available(iOS 27.3, *) extension GetSeasonIntent: ToolIntent {}
@available(iOS 27.3, *) extension GetFastDayIntent: ToolIntent {}
@available(iOS 27.3, *) extension GetSaintsIntent: ToolIntent {}
@available(iOS 27.3, *) extension AboutSaintIntent: ToolIntent {}
@available(iOS 27.3, *) extension GetCollectIntent: ToolIntent {}
@available(iOS 27.3, *) extension GetReadingsIntent: ToolIntent {}
@available(iOS 27.3, *) extension GetGospelIntent: ToolIntent {}
@available(iOS 27.3, *) extension FindFeastIntent: ToolIntent {}
@available(iOS 27.3, *) extension NextHolyDayIntent: ToolIntent {}
#endif
