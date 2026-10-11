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

Keep `@capacitor/assets` as development tooling. Native builds use the generated
assets already committed to `ios/` and `android/`; regenerate only when source
artwork in `assets/` changes, rather than during normal builds or deployments.

Generate in a disposable copy of the app with dependencies installed. Select
one platform explicitly so native artwork changes do not also rewrite PWA assets:
```bash
npm exec -- capacitor-assets generate --android
npm exec -- capacitor-assets generate --ios
```
Inspect the output before copying it back: check every expected image exists,
its dimensions, alpha/transparency, cropping, and appearance, along with asset
catalog JSON and Android adaptive-icon XML. Review the diff and preview the
affected platform before committing. The tool can log errors and still exit
successfully, so its exit status alone is not sufficient validation.

**Existing iOS regeneration limitation:** the current AppIcon catalog references
some filenames more than once; version 3.0.5 attempts to delete those files twice
and aborts. It also expects `Splash.imageset`, while this app uses
`LaunchImage.imageset`. Do not regenerate directly over the committed iOS assets.
An iOS catalog migration must preserve storyboard references and be checked in
Xcode before replacing the existing catalogs. Normal native builds continue to
use the committed assets without invoking this generator.

The package-scoped override pins only `@capacitor/assets`'s Sharp dependency to
`0.35.5`, addressing its reported image-library vulnerabilities. On October 11,
2026, isolated generation with this app's source artwork and compatible iOS test
catalogs produced 41 images pixel-identical to Sharp 0.32.6, with matching dimensions,
alpha channels, filenames, and Android XML. Both versions reproduced the same
failure on the unmodified iOS catalog. Simulator/device appearance was not tested;
no committed artwork or native catalogs were regenerated during this validation.
Recheck the override when upstream publishes a dependency update.

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
