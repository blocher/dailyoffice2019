# app

## Project setup
```
npm ci
```

### Compiles and hot-reloads for development
```
npm run dev
```

### Compiles and minifies for production
```
npm run build
```

### Run your unit tests
```
npm run test:unit
```

### Run your end-to-end tests
```
npm run test:e2e
```

### Lints and fixes files
```
npm run lint
```

## Native builds with Capacitor

Native commands use Vite and the official Capacitor CLI; Vue CLI is no longer required.
Run these commands from `app/` after installing dependencies and the native platform toolchains.

Build the web app, sync the native projects, and create a signed native build:
```bash
npm run capacitor:build -- ios
npm run capacitor:build -- android
```
Signing options can be appended after the platform, as described in the
[Capacitor build documentation](https://capacitorjs.com/docs/cli/commands/build).

Build the web app, sync, and run on a device or simulator:
```bash
npm run capacitor:serve -- ios
npm run capacitor:serve -- android
```
`npm run ios` is a shortcut for the iOS run command. These commands run the bundled
web app by default. For live reload, start `npm run dev -- --host 0.0.0.0` in a
separate terminal, then run `npm run capacitor:serve -- ios --live-reload --host
<your-local-network-address> --port 5176` (or use `android`). See the
[Capacitor run documentation](https://capacitorjs.com/docs/cli/commands/run).

## Icons and splash screens

The app icon is the gold Jerusalem cross of the 2019 prayer book's cover on
oxblood leather, drawn as a vector in `store/scripts/build-icons.mjs`. That
script writes every icon and splash screen from it:

```bash
node store/scripts/build-icons.mjs
```

- iOS: a single-size `AppIcon` (1024px) with dark and tinted appearances, and
  the `Splash` launch image the launch storyboard and SplashScreen plugin use.
- Android: adaptive icons (leather background, cross foreground, and a vector
  monochrome layer for themed icons), legacy and round icons, the Android 12+
  splash icon (`splash_icon`, on `@color/splash_background`), and full-screen
  WebP splashes for older versions.
- `assets/`: matching sources for `@capacitor/assets`, plus store icons and
  Icon Composer layers in `store/icons/`.

Review the diff and preview both platforms after changing the art. Keep
`@capacitor/assets` as development tooling only; the build-icons script
replaces its iOS output, which used to fail on this project's catalogs.

The package-scoped override pins `@capacitor/assets`'s Sharp dependency to
`0.35.5`, addressing its reported image-library vulnerabilities; the icon and
store scripts use the same Sharp. Recheck the override when upstream publishes
a dependency update.

The native apps keep the splash up until the first page renders (`main.js`
hides it; `capacitor.config.ts` hides it after four seconds regardless).

## Store listings and release

`store/` holds everything for the App Store and Google Play: listing text
(`store/metadata/`, laid out for fastlane `deliver` and `supply`), framed
screenshots for every required size, icons, the Play feature graphic, and the
scripts that build them from real simulator captures. `store/RELEASE_GUIDE.md`
walks through a release step by step.

## Email updates

`EmailSignup.vue` posts the address to Django's `/api/v1/email_signup` endpoint.
The backend subscribes the address using the Python Mailchimp Marketing client
and server-side configuration. No browser Mailchimp subscription package is required.

## Firebase Analytics for Capacitor

Native iOS and Android builds use [`@capacitor-firebase/analytics`](https://www.npmjs.com/package/@capacitor-firebase/analytics) to send Firebase Analytics events. Web builds continue to use `vue-gtag`.

### Setup

1. Install the plugin and its peer dependency:
   ```bash
   npm install @capacitor-firebase/analytics firebase@13.0.0
   ```
2. Add your Firebase configuration files:
   - `android/app/google-services.json`
   - `ios/App/App/GoogleService-Info.plist`

   > The provided `GoogleService-Info.plist` sets `IS_ANALYTICS_ENABLED` to `false`. This is the value supplied by Firebase and does not prevent Analytics from working.

3. For iOS projects using CocoaPods, ensure the following line is present in `ios/App/Podfile`:
   ```ruby
   pod 'CapacitorFirebaseAnalytics/Analytics', :path => '../../node_modules/@capacitor-firebase/analytics'
   ```
4. After installation, run Capacitor sync to copy native assets:
   ```bash
   npx cap sync
   ```

All route changes in the native apps automatically log detailed `screen_view` events and print success or error messages to the console for debugging.

### Customize configuration
See [Vite configuration](https://vite.dev/config/).
