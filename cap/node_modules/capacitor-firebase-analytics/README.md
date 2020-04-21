# capacitor-firebase-analytics

don't use this yet.

# Quickstart

## Step 1: Install
`npm install capacitor-firebase-analytics`
`npx cap sync`

## Step 2: Firebase Settings File
Navigate to the project settings page for your application on Firebase.

**Android:** Download the `google-services.json` file and copy it to the `android/app/` directory of your capacitor project. You will also need to add the Firebase SDK to your gradle files. More info can be found here: https://firebase.google.com/docs/android/setup#manually_add_firebase

**iOS:** Download the `GoogleService-Info.plist` file. In Xcode right-click on the yellow folder named, "App" and select the 'Add files to "App"'. *tip: if you drag and drop your file to this location, Xcode may not be able to find it.*

## Methods

### logEvent(_options_: { _name_: _string_, _parameters_?: _object_ })
Logs an app event.
```js
FirebaseAnalytics.logEvent({ name: 'event_name',  parameters: { param1: 'value1', param2: 'value2' });
```

### setUserId(_options_: { _userId_: _string_ })
Sets the user ID property.
```js
FirebaseAnalytics.setUserId({ userId: '11223344' });
```

### setUserProperty(_options_: { _name_: _string_, _value_: _string })
Sets a user property to a given value.
```js
FirebaseAnalytics.setUserProperty({ name: 'name1', value: 'value1' });
```

### setScreenName(options: { screenName: string, screenClassOverride?: string)
Sets the current screen name, which specifies the current visual context in your app. This helps identify the areas in your app where users spend their time and how they interact with your app.
```js
FirebaseAnalytics.setScreenName({ screenName: 'screen1', screenClassOverride: 'ScreenClassName'});
```

### appInstanceId(): Promise<string>
The unique ID for this instance of the application.
```js
FirebaseAnalytics.appInstanceId();
```

### resetAnalyticsData()
Clears all analytics data for this instance from the device and resets the app instance ID.
```js
FirebaseAnalytics.resetAnalyticsData();
```


***
# Detailed Install on New Project [Android]
## Step 1: Firebase App Setup
1. On the Firebase console (https://console.firebase.google.com/), click "Add project."
2. Click "Create Project" after naming the project and accepting the terms.
3. Click the continue button after the project is ready.
4. Click on the Android logo to add an app. If you are unable to find it, follow these steps:
    * In the top left, there is a cog next to "Project Overview." Click it and go to the project settings.
    * At the bottom of the general settings, click on the Android logo in the "Your apps" section to add an app.
5. Enter a package name. Keep your browser open. You will finish this later.

## Step 2: Create new project
1. `ionic start <name> <template> [options]` See: https://ionicframework.com/docs/cli/commands/start/
2. `cd [project-directory]`
3. `npm install`
4. `ionic build`
5. `npm install --save @capacitor/core @capacitor/cli` See: https://capacitor.ionicframework.com/docs/getting-started/
6. `npx cap init`
7. When you are prompted for the "App Package ID", enter in the package that was entered on Step 5 of Step 1.
8. `npx cap add android`

## Step 3: Install Plugin
1. `npm install capacitor-firebase-analytics`
2. `npx cap sync`
3. Open project in Android Studio.
4. In the 'MainAcivity.java' file, add `add(CapacitorFirebaseAnalytics.class);` in the `this.init` method call.
 
## Step 4: Add dependencies
1. Return to the Firebase app registration from the end of Step 1.
2. Click "Register app"
3. Follow the instructions for downloading the 'google-services.json' and adding the Firebase SDK.
4. Run the app. If everything worked correctly, you should see a response on the Firebase console.
5. More info can be found here: https://firebase.google.com/docs/android/setup
