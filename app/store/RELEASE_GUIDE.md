# Releasing The Daily Office 4.0.0

A step-by-step guide to shipping the native apps to the App Store and Google
Play. Everything you paste or upload is in this `store/` folder; paths below
are relative to `app/`.

| | iOS | Android |
|---|---|---|
| Bundle / package | `com.dailyoffice.dailyoffice2019` | `com.dailyoffice2019.app` |
| Version | 4.0.0 (build 4.0.0) | 4.0.0 (version code 6) |
| Live today | 3.1.3 (March 9, 2026) | 3.1.3 (version code 4) |
| Toolchain | Xcode 27.1, iOS 15+ deployment, SPM | AGP 8.13.2, Gradle 8.14.6, compile/target SDK 36, min SDK 24 |
| Capacitor | 8.5.3 (latest stable; 9 is still alpha) | same |

## 0. Before you start (10 minutes)

1. **Review the `apps` branch** (`git log master..apps`). Merge it into
   `master` when you're happy; the web build is unaffected except for the
   splash-screen hide call, which does nothing on the web.
2. **Decide the version number.** I used **4.0.0** because this is the
   largest update since launch (new design, audio, Book view, podcasts). If you
   would rather ship 3.2.0, change `MARKETING_VERSION`/`CURRENT_PROJECT_VERSION`
   in `ios/App/App.xcodeproj/project.pbxproj`, `versionName` in
   `android/app/build.gradle`, and `version` in `package.json`; Android's
   `versionCode` must stay above anything already uploaded (6 is safe even if a
   3.2.0 build with code 5 reached a test track).
3. **Security: the Android keystore is committed to a public repository**
   (`keystore/dailyoffice2019.jks`, since the "privacy-policy" commit). It is
   password-protected, but treat it as exposed. If Play App Signing is on (check
   Play Console → *Test and release → App integrity*), this file is only your
   *upload* key: request an upload-key reset there, then delete the file from
   the repository (and ideally its history). Keep keys in a password manager.
4. Have ready: your Apple Developer account (team `2TG4YK78KZ`) signed in to
   Xcode, the Play Console, the keystore passwords, and a YouTube account for
   the promo video.

## 1. Build and upload the iOS app

```bash
cd app
npm ci
npm run capacitor:build -- ios   # builds, uploads source maps to Bugsnag, syncs, archives
```

If `cap build` asks for signing options, use Xcode instead (simplest):

```bash
npm run build && node scripts/upload-sourcemaps.mjs --base-url capacitor://localhost --base-url https://localhost && npx cap sync
npx cap open ios
```

1. In Xcode choose **Any iOS Device (arm64)** as the destination.
2. **Product → Archive.** Signing is automatic for team 2TG4YK78KZ.
3. In the Organizer: **Distribute App → App Store Connect → Upload.** The
   privacy manifest and `ITSAppUsesNonExemptEncryption = NO` are already set, so
   there is no export-compliance question.
4. Wait for the build to finish processing (email from App Store Connect),
   then install it from **TestFlight** on a phone and an iPad. Check: launch
   (cover-art splash, no white flash), Morning Prayer, audio with the screen
   locked and lock-screen controls, Book view, dark mode, the new icon on the
   home screen (also try *Customize → Dark / Tinted* icons).

## 2. App Store Connect listing

Open **App Store Connect → The Daily Office → + Version → 4.0.0**.

### Text (copy from `store/metadata/ios/en-US/`)

| Field | File | Notes |
|---|---|---|
| Promotional text | `promotional_text.txt` | 161/170; can change any time without review |
| Description | `description.txt` | 2,679/4,000 |
| Keywords | `keywords.txt` | 95/100 bytes; don't repeat words from the name or subtitle |
| What's New | `release_notes.txt` | |
| Support URL | `support_url.txt` | https://www.dailyoffice2019.com/about |
| Marketing URL | `marketing_url.txt` | |
| Copyright | `copyright.txt` | |

**App information** (applies to every version): the subtitle in
`subtitle.txt` is **"Anglican Book of Common Prayer"** (30/30), replacing
"Morning and Evening Prayer". It puts the most-searched words in an indexed
field. Keep the name **The Daily Office**. Privacy policy URL:
https://www.dailyoffice2019.com/privacy-policy.

### Screenshots (from `store/screenshots/ios/`, 10 per size, already in order)

- **iPhone 6.9" display** → `iphone-6.9/` (1320×2868). Apple's newest
  requirement is the **6.3" Dynamic Island** slot; upload `iphone-6.3/`
  (1206×2622) there if App Store Connect shows it. Upload any other slot it
  asks for from `iphone-6.5/`, `iphone-6.1/`, `iphone-5.5/`.
- **iPad 13" display** → `ipad-13/` (2064×2752); `ipad-12.9/` and `ipad-11/` if
  asked.
- Drag them in by file name (`01-office` … `10-podcasts`); order matters, and the
  first three show in search results.
- The un-captioned originals are in `store/screenshots/raw/` if you prefer
  plain screenshots for any slot.

### App previews (videos; optional, recommended)

Videos aren't in git (they're large). Rebuild them with
`node store/scripts/build-videos.mjs`, or use the copies I left in
`store/video/` on this Mac:

- iPhone: `app-preview-iphone-886x1920.mp4` (23 s, 30 fps, H.264 10 Mbps,
  silent stereo AAC) for the 6.9"/6.5" slots.
- iPad: `app-preview-ipad-1200x1600.mp4` for the 13" slot.
- Choose a poster frame from the first seconds (Morning Prayer).

### App Review, privacy, and rating

- **Sign-in required:** No. **Notes:** "No account needed. Audio is available
  for three days ago through nine days ahead; tap Audio on, then play."
- **App Privacy** (update to match the new privacy manifest):
  - *Product Interaction* (Firebase Analytics): **not linked** to identity, not tracking, Analytics.
  - *Crash Data* (Bugsnag): **not linked**, not tracking, App Functionality.
  - *Email Address* (optional email-updates sign-up): **linked**, not tracking,
    Developer's Advertising or Marketing. This is new; the email sign-up form in
    the app collects it.
- **Age rating:** answer **None/No** throughout the updated questionnaire. No
  user-generated content, messaging, ads, or web browsing beyond links that open
  in the system browser. Expected rating: **4+**.
- **Content rights:** Yes, the app shows third-party content (Scripture
  translations, the 2019 BCP) and you have the rights (licensed/permissioned).
- **Release:** choose **Manually release** or a **7-day phased release**, then
  **Add for Review → Submit**. Reviews usually take a day or two.

## 3. Build the Android app bundle

```bash
cd app
cp android/keystore.properties.example android/keystore.properties
# fill in storePassword, keyAlias, keyPassword (keystore.properties is git-ignored)
npm run build && node scripts/upload-sourcemaps.mjs --base-url https://localhost && npx cap sync android
cd android && ./gradlew bundleRelease
```

The signed bundle is `android/app/build/outputs/bundle/release/app-release.aab`
(about 23 MB). It has no native libraries, so Google Play's 16 KB page-size rule
doesn't apply. The `capacitor:build` route also works:
`npm run capacitor:build -- android --androidreleasetype AAB --keystorepath ../keystore/dailyoffice2019.jks --keystorealias … `.

Optional local check on a device or emulator: `./gradlew :app:connectedDebugAndroidTest`
(5 tests, passing on Android 17).

## 4. Google Play Console

### Release

1. **Test and release → Production → Create new release** (or start with
   *Internal testing* if you want a phone test first).
2. Upload `app-release.aab`. Release name: `4.0.0 (6)`.
3. Release notes: paste `store/metadata/android/en-US/changelogs/6.txt`
   (465/500 characters).
4. **Staged rollout:** start at 20%, raise to 100% after a day or two with no
   new Bugsnag errors.

### Store listing (Grow users → Store presence → Main store listing)

| Field | Source |
|---|---|
| App name | `store/metadata/android/en-US/title.txt` → **The Daily Office: BCP 2019** (26/30) |
| Short description | `short_description.txt` (72/80) |
| Full description | `full_description.txt` |
| App icon | `images/icon.png` (512×512) |
| Feature graphic | `images/featureGraphic.png` (1024×500) |
| Phone screenshots | `images/phoneScreenshots/` (8 × 1080×1920) |
| 7-inch tablet | `images/sevenInchScreenshots/` (8 × 1080×1920) |
| 10-inch tablet | `images/tenInchScreenshots/` (8 × 1440×2560) |
| Video | YouTube URL (below) |

All screenshots are 9:16 at 1080 px or more, which qualifies the listing for
Play's larger promotional formats. Chromebook screenshots are optional; skip
them.

**Promo video:** upload `store/video/promo-1920x1080.mp4` (27 s) to YouTube as
**Unlisted**, with ads off and not age-restricted, and paste the plain
`https://www.youtube.com/watch?v=…` URL (no playlist or timestamp). Put the same
URL in `store/metadata/android/en-US/video.txt` if you later use fastlane.

### App content (Policy → App content); update if prompted

- **Data safety:** collected: *App activity → App interactions* (analytics),
  *App info and performance → Crash logs* (Bugsnag), and *Personal info → Email
  address* (optional, for email updates). None is shared or sold; all of it is
  encrypted in transit. Users can request deletion at feedback@dailyoffice2019.com.
- **Ads:** No. **Target audience:** 13+ (general audience). **Content rating:**
  redo the IARC questionnaire if asked; answer No throughout (expected
  *Everyone*).
- **Target API:** 36 (Android 16) meets the August 31, 2026 requirement.

Submit for review ("Send changes for review" on the Publishing overview).

## 5. After release

- Watch **Bugsnag** for release 4.0.0 (native builds report as `4.0.0`; source
  maps were uploaded by the commands above) and **Firebase Analytics** for
  `screen_view`s from the new version.
- Answer reviews that mention the redesign; it changes a lot for long-time users.
- When both stores are live, merge `apps` into `master` if you haven't already.

## Optional

- **fastlane:** `store/metadata/ios/en-US` and `store/metadata/android/en-US`
  use fastlane's file names. With fastlane installed:
  `fastlane deliver --metadata_path store/metadata/ios --skip_screenshots` and
  `fastlane supply --metadata_path store/metadata/android`.
- **Liquid Glass icon:** iOS 26/27 apply the system glass treatment to the
  current asset-catalog icon automatically. For a hand-tuned version, import
  `store/icons/icon-composer/background.png` and `cross.svg` into Icon Composer
  (Xcode → Open Developer Tool), save as `AppIcon.icon` in `ios/App/App/`, and
  add it to the target.
- **Social and press images:** `store/graphics/` (1200×630, 1600×900,
  1500×500 banner, 1080 square) and `store/icons/sizes/`.

## Rebuilding the assets

All art comes from scripts, so it can be regenerated after design changes:

```bash
node store/scripts/build-icons.mjs        # icons, splashes, store icons
node store/scripts/build-screenshots.mjs  # framed screenshots + feature graphic
node store/scripts/build-videos.mjs       # app previews + promo (needs store/video/raw/)
```

The raw captures in `store/screenshots/raw/` were taken from the app itself on
an iPhone 18 Pro Max (iOS 27), an iPad Pro 13" (M5), and Android 17 phone and
tablet emulators, with clean 9:41 status bars. To retake them, run
`node store/scripts/remote/remote.mjs`, add `store/scripts/remote/driver.js` to
a local build's `public/index.html` (never a release build; `npx cap sync`
removes it), and send navigation commands to
`curl localhost:9999/run --data-binary '…'`; capture with
`xcrun simctl io booted screenshot` or `adb exec-out screencap -p`. The
captured office is Friday, October 23, 2026 (St. James of Jerusalem), chosen
for its red liturgical color, which matches the icon.
