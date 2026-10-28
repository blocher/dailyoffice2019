# Releasing the native apps

A step-by-step guide to shipping the native apps to the App Store and Google
Play, written from the 4.0.0 release. Everything you paste or upload is in this
`store/` folder; paths below are relative to `app/`.

| | iOS | Android |
|---|---|---|
| Bundle / package | `com.dailyoffice.dailyoffice2019` | `com.dailyoffice2019.app` |
| Latest release | 4.0.0 (build 4.0.0), submitted October 27, 2026 | 4.0.0 (version code 6), submitted October 28, 2026 |
| Previous release | 3.1.3 (March 9, 2026) | 3.1.3 (version code 4) |
| Toolchain | Xcode 27.1, iOS 15+ deployment, SPM | AGP 8.13.2, Gradle 8.14.6, compile/target SDK 36, min SDK 24 |
| Capacitor | 8.5.3 | same |

## Accounts

- **App Store Connect:** app ID `1513851259`, team `2TG4YK78KZ`
  (https://appstoreconnect.apple.com/apps).
- **Google Play Console:** sign in as **dailyoffice.bcp2019@gmail.com**.
  Developer account `9181541960142784840`, app `4973236224968670884`. In a
  browser signed in to several Google accounts, the Console URL's `/u/N/` picks
  the account; check the avatar before changing anything. The old
  "The Daily Office, LLC" developer account (`9034754646816353208`) was closed
  in April 2024 and can't publish.

## 0. Before you start

1. **Merge to `master` first.** Release builds come from `master`.
2. **Bump the versions.** Both stores reject a version they've already seen.
   - iOS: `MARKETING_VERSION` and `CURRENT_PROJECT_VERSION` in
     `ios/App/App.xcodeproj/project.pbxproj` (both Debug and Release).
   - Android: `versionName` and `versionCode` in `android/app/build.gradle`.
     `versionCode` must be higher than any code ever uploaded; **the next one
     is 7**.
   - `version` in `package.json`, then `npm install` to update the lockfile.
3. **Write the release notes:** iOS `store/metadata/ios/en-US/release_notes.txt`,
   and Android `store/metadata/android/en-US/changelogs/<versionCode>.txt`
   (500 characters at most).
4. **Security: the Android keystore is committed to a public repository**
   (`keystore/dailyoffice2019.jks`). It is password-protected, and Play App
   Signing is on, so it's only the *upload* key (Play accepted the 4.0.0 bundle
   signed with it). Treat it as exposed anyway: request an upload-key reset in
   Play Console → *Test and release → App integrity*, then delete the file from
   the repository (and ideally its history). Keep keys in a password manager.
5. Have ready: Xcode signed in to the Apple Developer account, the keystore
   passwords, and Chrome signed in to both consoles.

## 1. Build and upload the iOS app

The command line is the most reliable route. **Run `xcodebuild` with Apple's
`PATH`:** Homebrew's rsync shadows Apple's, and `-exportArchive` then fails with
"Copy failed" (`rsync: --extended-attributes: unknown option`).

```bash
cd app
npm ci
npm run build
node scripts/upload-sourcemaps.mjs --base-url capacitor://localhost --base-url https://localhost
npx cap sync

cat > /tmp/ExportOptions.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>method</key><string>app-store-connect</string>
<key>destination</key><string>upload</string>
<key>teamID</key><string>2TG4YK78KZ</string>
<key>signingStyle</key><string>automatic</string>
<key>uploadSymbols</key><true/>
<key>manageAppVersionAndBuildNumber</key><false/>
</dict></plist>
EOF

export PATH=/usr/bin:/bin:/usr/sbin:/sbin
xcodebuild -project ios/App/App.xcodeproj -scheme App -configuration Release \
  -destination 'generic/platform=iOS' -archivePath /tmp/App.xcarchive \
  -allowProvisioningUpdates archive
xcodebuild -exportArchive -archivePath /tmp/App.xcarchive \
  -exportOptionsPlist /tmp/ExportOptions.plist -exportPath /tmp/export \
  -allowProvisioningUpdates
```

`destination: upload` sends the build straight to App Store Connect. To use
Xcode instead: `npx cap open ios`, choose **Any iOS Device (arm64)**,
**Product → Archive**, then **Distribute App → App Store Connect → Upload** in
the Organizer.

The privacy manifest and `ITSAppUsesNonExemptEncryption = NO` are already set,
so there is no export-compliance question. Wait for the build to finish
processing (about 15 minutes; App Store Connect emails you). Optionally install
it from **TestFlight** on a phone and an iPad and check launch, an office, audio
with the screen locked, Book view, and dark mode.

## 2. App Store Connect listing

Open **App Store Connect → The Daily Office → + Version**, enter the version,
and select the uploaded build.

### Text (copy from `store/metadata/ios/en-US/`)

| Field | File | Notes |
|---|---|---|
| Promotional text | `promotional_text.txt` | 170 characters at most; can change any time without review |
| Description | `description.txt` | 4,000 characters at most |
| Keywords | `keywords.txt` | 100 bytes at most; don't repeat words from the name or subtitle |
| What's New | `release_notes.txt` | |
| Support URL | `support_url.txt` | https://www.dailyoffice2019.com/about |
| Marketing URL | `marketing_url.txt` | |
| Copyright | `copyright.txt` | |

**App information** (applies to every version): the name is **The Daily
Office** and the subtitle is `subtitle.txt`, **"Anglican Book of Common
Prayer"** (30/30). Privacy policy URL:
https://www.dailyoffice2019.com/privacy-policy.

### Screenshots (from `store/screenshots/ios/`, 10 per size, already in order)

- **iPhone 6.9" display** → `iphone-6.9/` (1320×2868). Apple's newest
  requirement is the **6.3" Dynamic Island** slot; upload `iphone-6.3/`
  (1206×2622) there if App Store Connect shows it. Upload any other slot it
  asks for from `iphone-6.5/`, `iphone-6.1/`, `iphone-5.5/`.
- **iPad 13" display** → `ipad-13/` (2064×2752); `ipad-12.9/` and `ipad-11/` if
  asked.
- Order matters (`01-office` … `10-podcasts`), and the first three show in
  search results.
- The un-captioned originals are in `store/screenshots/raw/`.

### App previews (videos; optional)

Videos aren't in git (they're large). Rebuild them with
`node store/scripts/build-videos.mjs`, or use the copies in `store/video/` on
the release Mac:

- iPhone: `app-preview-iphone-886x1920.mp4` (23 s) for the 6.9"/6.5" slots.
- iPad: `app-preview-ipad-1200x1600.mp4` for the 13" slot.

### App Review, privacy, and rating

- **Sign-in required:** No. **Notes:** "No account needed. Audio is available
  for three days ago through nine days ahead; tap Audio on, then play." (Remove
  any older note that calls the app fully offline.)
- **App Privacy** should match the privacy manifest:
  - *Product Interaction* (Firebase Analytics): **not linked** to identity, not tracking, Analytics.
  - *Crash Data* (Bugsnag): **not linked**, not tracking, App Functionality.
  - *Email Address* (optional email-updates sign-up): **linked**, not tracking,
    Developer's Advertising or Marketing. **Not added yet as of 4.0.0.**
- **Age rating:** Apple's updated questionnaire must be answered before you can
  submit. Answer **None/No** throughout, including "Social Media Disabled for
  Users Under 13" = **No**. The result is **4+**.
- **Content rights:** Yes, the app shows third-party content (Scripture
  translations, the 2019 BCP) and you have the rights.
- **Version release:** 4.0.0 used **Automatically release this version**.
  Choose manual or a 7-day phased release if you want more control.
- **Reset iOS summary rating:** choose **Keep existing rating**. Never reset it.
- **Add for Review → Submit.** Reviews usually take a day or two.
- **Business → Agreements:** the Paid Applications Schedule shows as pending.
  It didn't block 4.0.0, but only the Account Holder can accept it.

## 3. Build the Android app bundle

Signing reads `android/keystore.properties`, which is git-ignored. Create it
once on each Mac:

```bash
cd app/android
cp keystore.properties.example keystore.properties
keytool -list -keystore ../../keystore/dailyoffice2019.jks   # shows the key alias (asks for the keystore password)
open -e keystore.properties                                   # fill in storePassword, keyAlias, keyPassword
```

Leave `storeFile=` as it is; no quotes or spaces after the `=` signs. Then build:

```bash
cd app
npm run build
node scripts/upload-sourcemaps.mjs --base-url https://localhost
npx cap sync android
cd android && ./gradlew bundleRelease
```

The signed bundle is `android/app/build/outputs/bundle/release/app-release.aab`
(about 23 MB). It has no native libraries, so Google Play's 16 KB page-size rule
doesn't apply.

Optional local check on a device or emulator: `./gradlew :app:connectedDebugAndroidTest`.

## 4. Google Play Console

**Managed publishing is off**, so approved changes go live as soon as Google
approves them. Turn it on under *Publishing overview* if you want to choose the
moment yourself.

### Release

1. **Test and release → Production → Create new release.**
2. Upload `app-release.aab` by hand. Browser automation can't attach files over
   10 MB.
3. Release name: `<versionName> (<versionCode>)`, such as `4.0.0 (6)`.
4. Release notes: paste `store/metadata/android/en-US/changelogs/<versionCode>.txt`.
5. **Rollout:** 4.0.0 went to 100%. A staged rollout (for example 20%, then 100%
   after a day with no new Bugsnag errors) is safer for risky releases.

### Store listing (Grow users → Store presence → Main store listing)

| Field | Source |
|---|---|
| App name | `store/metadata/android/en-US/title.txt` → **The Daily Office: BCP 2019** (26/30) |
| Short description | `short_description.txt` (80 characters at most) |
| Full description | `full_description.txt` |
| App icon | `images/icon.png` (512×512) |
| Feature graphic | `images/featureGraphic.png` (1024×500) |
| Phone screenshots | `images/phoneScreenshots/` (8 × 1080×1920) |
| 7-inch tablet | `images/sevenInchScreenshots/` (8 × 1080×1920) |
| 10-inch tablet | `images/tenInchScreenshots/` (8 × 1440×2560) |
| Video | YouTube URL (optional, below) |

- **Screenshot order:** a multi-file upload lands in random order. Upload one
  file at a time, or add them from the asset library one by one (select, then
  **Add**), in file-name order.
- **Save properly:** listing edits reach the Publishing overview only after
  **Next → Save** in the listing editor; **Save as draft** alone doesn't queue
  them.
- Chromebook screenshots are optional; skip them.
- **Promo video** (not used for 4.0.0): upload `store/video/promo-1920x1080.mp4`
  to YouTube as **Unlisted**, with ads off, and paste the plain
  `https://www.youtube.com/watch?v=…` URL.

### App content (Policy → App content); update if prompted

- **Foreground service permissions:** the app declares a `mediaPlayback`
  foreground service for audio, and Play requires a declaration with a video
  link before it accepts updates. 4.0.0's declaration uses
  `store/video/daily-office-background-audio-demo.mp4` (a 32-second emulator
  recording of audio continuing with the app in the background, with the media
  notification controls), shared from Google Drive as "anyone with the link can
  view". Keep that file shared; re-record and re-file only if Google asks.
- **Data safety:** collected: *App activity → App interactions* (analytics),
  *App info and performance → Crash logs* and *Diagnostics* (Bugsnag), and
  *Personal info → Email address* (optional, for email updates). None is shared
  or sold; all of it is encrypted in transit. Users can request deletion at
  feedback@dailyoffice2019.com. This was already correct for 4.0.0.
- **Ads:** No. **Target audience:** 13+ (general audience). **Content rating:**
  redo the IARC questionnaire if asked; answer No throughout (expected
  *Everyone*).
- **Target API:** 36 (Android 16) meets the August 31, 2026 requirement.

### Submit

On the **Publishing overview**, click **Send changes for review** and confirm.
Play first runs automated checks (up to about 14 minutes), then sends the
changes to review, which can take up to 7 days. If it asks whether any assets
are AI-generated, the 4.0.0 assets are not.

## 5. After release

- Watch **Bugsnag** for the new release (native builds report their version;
  source maps were uploaded by the commands above) and **Firebase Analytics**
  for `screen_view`s from the new version.
- Answer reviews, especially any about changes long-time users will notice.

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

On the Android emulator, launch with `setopt NO_BG_NICE` and `-no-window`
(for example `emulator -avd DO_Phone -no-window -no-snapshot-save`); a
backgrounded, niced emulator runs too slowly to record.
