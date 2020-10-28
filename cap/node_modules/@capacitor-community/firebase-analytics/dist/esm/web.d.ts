import { WebPlugin } from "@capacitor/core";
import { FirebaseAnalyticsPlugin, FirebaseInitOptions } from "./definitions";
export declare class FirebaseAnalyticsWeb extends WebPlugin implements FirebaseAnalyticsPlugin {
    private not_supported_mssg;
    private options_missing_mssg;
    private duplicate_app_mssg;
    private analytics_missing_mssg;
    readonly ready: Promise<any>;
    private readyResolver;
    private analyticsRef;
    private scripts;
    constructor();
    /**
     * Configure and Initialize FirebaseApp if not present
     * @param options - web app's Firebase configuration
     * @returns firebase analytics object reference
     * Platform: Web
     */
    initializeFirebase(options: FirebaseInitOptions): Promise<any>;
    /**
     * Sets the user ID property.
     * @param options - userId: unique identifier of the user to log
     * Platform: Web/Android/iOS
     */
    setUserId(options: {
        userId: string;
    }): Promise<void>;
    /**
     * Sets a user property to a given value.
     * @param options - name: The name of the user property to set.
     *                  value: The value of the user property.
     * Platform: Web/Android/iOS
     */
    setUserProperty(options: {
        name: string;
        value: string;
    }): Promise<void>;
    /**
     * Retrieves the app instance id from the service.
     * @returns - instanceId: current instance if of the app
     * Platform: Web/Android/iOS
     */
    getAppInstanceId(): Promise<{
        instanceId: string;
    }>;
    /**
     * Sets the current screen name, which specifies the current visual context in your app.
     * @param options - screenName: the activity to which the screen name and class name apply.
     *                  nameOverride: the name of the current screen. Set to null to clear the current screen name.
     * Platform: Android/iOS
     */
    setScreenName(_options: {
        screenName: string;
        nameOverride: string;
    }): Promise<void>;
    /**
     * Clears all analytics data for this app from the device and resets the app instance id.
     * Platform: Android/iOS
     */
    reset(): Promise<void>;
    /**
     * Logs an app event.
     * @param options - name: unique name of the event
     *                  params: the map of event parameters.
     * Platform: Web/Android/iOS
     */
    logEvent(options: {
        name: string;
        params: object;
    }): Promise<void>;
    /**
     * Sets whether analytics collection is enabled for this app on this device.
     * @param options - enabled: boolean true/false to enable/disable logging
     * Platform: Web/Android/iOS
     */
    setCollectionEnabled(options: {
        enabled: boolean;
    }): Promise<void>;
    /**
     * Sets the duration of inactivity that terminates the current session.
     * @param options - duration: duration of inactivity
     * Platform: Android/iOS
     */
    setSessionTimeoutDuration(_options: {
        duration: number;
    }): Promise<void>;
    /**
     * Returns analytics reference object
     */
    get remoteConfig(): any;
    enable(): Promise<void>;
    disable(): Promise<void>;
    /**
     * Ready resolver to check and load firebase analytics
     */
    private configure;
    /**
     * Check for existing loaded script and load new scripts
     */
    private loadScripts;
    /**
     * Loaded single script with provided id and source
     * @param id - unique identifier of the script
     * @param src - source of the script
     */
    private loadScript;
    /**
     * Returns true/false if firebase object reference exists inside window
     */
    private hasFirebaseInitialized;
}
declare const FirebaseAnalytics: FirebaseAnalyticsWeb;
export { FirebaseAnalytics };
