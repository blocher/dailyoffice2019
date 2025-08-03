# app

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
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

## Firebase Analytics for Capacitor

Native iOS and Android builds use [`@capacitor-firebase/analytics`](https://www.npmjs.com/package/@capacitor-firebase/analytics) to send Firebase Analytics events. Web builds continue to use `vue-gtag`.

### Setup

1. Install the plugin and its peer dependency:
   ```bash
   npm install @capacitor-firebase/analytics firebase@11.10.0
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
See [Configuration Reference](https://cli.vuejs.org/config/).
