import type { Plugin } from './definitions';
import { WebPlugin } from './web-plugin';
/******** WEB VIEW PLUGIN ********/
export interface WebViewPlugin extends Plugin {
    setServerAssetPath(options: WebViewPath): Promise<void>;
    setServerBasePath(options: WebViewPath): Promise<void>;
    getServerBasePath(): Promise<WebViewPath>;
    persistServerBasePath(): Promise<void>;
}
export interface WebViewPath {
    path: string;
}
export declare const WebView: WebViewPlugin;
export interface CapacitorCookiesPlugin {
    getCookies(options?: GetCookieOptions): Promise<HttpCookieMap>;
    /**
     * Write a cookie to the device.
     */
    setCookie(options: SetCookieOptions): Promise<void>;
    /**
     * Delete a cookie from the device.
     */
    deleteCookie(options: DeleteCookieOptions): Promise<void>;
    /**
     * Clear cookies from the device at a given URL.
     */
    clearCookies(options: ClearCookieOptions): Promise<void>;
    /**
     * Clear all cookies on the device.
     */
    clearAllCookies(): Promise<void>;
}
interface HttpCookie {
    /**
     * The URL of the cookie.
     */
    url?: string;
    /**
     * The key of the cookie.
     */
    key: string;
    /**
     * The value of the cookie.
     */
    value: string;
}
interface HttpCookieMap {
    [key: string]: string;
}
interface HttpCookieExtras {
    /**
     * The path to write the cookie to.
     */
    path?: string;
    /**
     * The date to expire the cookie.
     */
    expires?: string;
}
export type GetCookieOptions = Omit<HttpCookie, 'key' | 'value'>;
export type SetCookieOptions = HttpCookie & HttpCookieExtras;
export type DeleteCookieOptions = Omit<HttpCookie, 'value'>;
export type ClearCookieOptions = Omit<HttpCookie, 'key' | 'value'>;
export declare class CapacitorCookiesPluginWeb extends WebPlugin implements CapacitorCookiesPlugin {
    getCookies(): Promise<HttpCookieMap>;
    setCookie(options: SetCookieOptions): Promise<void>;
    deleteCookie(options: DeleteCookieOptions): Promise<void>;
    clearCookies(): Promise<void>;
    clearAllCookies(): Promise<void>;
}
export declare const CapacitorCookies: CapacitorCookiesPlugin;
/******** END COOKIES PLUGIN ********/
/******** HTTP PLUGIN ********/
export interface CapacitorHttpPlugin {
    /**
     * Make a Http Request to a server using native libraries.
     */
    request(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Make a Http GET Request to a server using native libraries.
     */
    get(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Make a Http POST Request to a server using native libraries.
     */
    post(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Make a Http PUT Request to a server using native libraries.
     */
    put(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Make a Http PATCH Request to a server using native libraries.
     */
    patch(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Make a Http DELETE Request to a server using native libraries.
     */
    delete(options: HttpOptions): Promise<HttpResponse>;
}
/**
 * How to parse the Http response before returning it to the client.
 */
export type HttpResponseType = 'arraybuffer' | 'blob' | 'json' | 'text' | 'document';
export interface HttpOptions {
    /**
     * The URL to send the request to.
     */
    url: string;
    /**
     * The Http Request method to run. (Default is GET)
     */
    method?: string;
    /**
     * URL parameters to append to the request.
     */
    params?: HttpParams;
    /**
     * Note: On Android and iOS, data can only be a string or a JSON.
     * FormData, Blob, ArrayBuffer, and other complex types are only directly supported on web
     * or through enabling `CapacitorHttp` in the config and using the patched `window.fetch` or `XMLHttpRequest`.
     *
     * If you need to send a complex type, you should serialize the data to base64
     * and set the `headers["Content-Type"]` and `dataType` attributes accordingly.
     */
    data?: any;
    /**
     * Http Request headers to send with the request.
     */
    headers?: HttpHeaders;
    /**
     * How long to wait to read additional data in milliseconds.
     * Resets each time new data is received.
     */
    readTimeout?: number;
    /**
     * How long to wait for the initial connection in milliseconds.
     */
    connectTimeout?: number;
    /**
     * Sets whether automatic HTTP redirects should be disabled
     */
    disableRedirects?: boolean;
    /**
     * Extra arguments for fetch when running on the web
     */
    webFetchExtra?: RequestInit;
    /**
     * This is used to parse the response appropriately before returning it to
     * the requestee. If the response content-type is "json", this value is ignored.
     */
    responseType?: HttpResponseType;
    /**
     * Use this option if you need to keep the URL unencoded in certain cases
     * (already encoded, azure/firebase testing, etc.). The default is _true_.
     */
    shouldEncodeUrlParams?: boolean;
    /**
     * This is used if we've had to convert the data from a JS type that needs
     * special handling in the native layer
     */
    dataType?: 'file' | 'formData';
}
export interface HttpParams {
    /**
     * A key/value dictionary of URL parameters to set.
     */
    [key: string]: string | string[];
}
export interface HttpHeaders {
    /**
     * A key/value dictionary of Http headers.
     */
    [key: string]: string;
}
export interface HttpResponse {
    /**
     * Additional data received with the Http response.
     */
    data: any;
    /**
     * The status code received from the Http response.
     */
    status: number;
    /**
     * The headers received from the Http response.
     */
    headers: HttpHeaders;
    /**
     * The response URL received from the Http response.
     */
    url: string;
}
/**
 * Read in a Blob value and return it as a base64 string
 * @param blob The blob value to convert to a base64 string
 */
export declare const readBlobAsBase64: (blob: Blob) => Promise<string>;
/**
 * Build the RequestInit object based on the options passed into the initial request
 * @param options The Http plugin options
 * @param extra Any extra RequestInit values
 */
export declare const buildRequestInit: (options: HttpOptions, extra?: RequestInit) => RequestInit;
export declare class CapacitorHttpPluginWeb extends WebPlugin implements CapacitorHttpPlugin {
    /**
     * Perform an Http request given a set of options
     * @param options Options to build the HTTP request
     */
    request(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Perform an Http GET request given a set of options
     * @param options Options to build the HTTP request
     */
    get(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Perform an Http POST request given a set of options
     * @param options Options to build the HTTP request
     */
    post(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Perform an Http PUT request given a set of options
     * @param options Options to build the HTTP request
     */
    put(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Perform an Http PATCH request given a set of options
     * @param options Options to build the HTTP request
     */
    patch(options: HttpOptions): Promise<HttpResponse>;
    /**
     * Perform an Http DELETE request given a set of options
     * @param options Options to build the HTTP request
     */
    delete(options: HttpOptions): Promise<HttpResponse>;
}
export declare const CapacitorHttp: CapacitorHttpPlugin;
/******** END HTTP PLUGIN ********/
/******** SYSTEM BARS PLUGIN ********/
/**
 * Available status bar styles.
 */
export declare enum SystemBarsStyle {
    /**
     * Light system bar content on a dark background.
     *
     * @since 8.0.0
     */
    Dark = "DARK",
    /**
     * For dark system bar content on a light background.
     *
     * @since 8.0.0
     */
    Light = "LIGHT",
    /**
     * The style is based on the device appearance or the underlying content.
     * If the device is using Dark mode, the system bars content will be light.
     * If the device is using Light mode, the system bars content will be dark.
     *
     * @since 8.0.0
     */
    Default = "DEFAULT"
}
/**
 * Available status bar animations.  iOS only.
 */
export type SystemBarsAnimation = 'FADE' | 'NONE';
/**
 * Available system bar types.
 */
export declare enum SystemBarType {
    /**
     * The top status bar on both Android and iOS.
     *
     * @since 8.0.0
     */
    StatusBar = "StatusBar",
    /**
     * The navigation bar (or gesture bar on iOS) on both Android and iOS.
     *
     * @since 8.0.0
     */
    NavigationBar = "NavigationBar"
}
export interface SystemBarsStyleOptions {
    /**
     * Style of the text and icons of the system bars.
     *
     * @since 8.0.0
     * @default 'DEFAULT'
     * @example "DARK"
     */
    style: SystemBarsStyle;
    /**
     * The system bar to which to apply the style.
     *
     *
     * @since 8.0.0
     * @default null
     * @example SystemBarType.StatusBar
     */
    bar?: SystemBarType;
}
export interface SystemBarsVisibilityOptions {
    /**
     * The system bar to hide or show.
     *
     * @since 8.0.0
     * @default null
     * @example SystemBarType.StatusBar
     */
    bar?: SystemBarType;
    /**
     * The type of status bar animation used when showing or hiding.
     *
     * This option is only supported on iOS.
     *
     * @default 'FADE'
     *
     * @since 8.0.0
     */
    animation?: SystemBarsAnimation;
}
export interface SystemBarsAnimationOptions {
    /**
     * The type of status bar animation used when showing or hiding.
     *
     * This option is only supported on iOS.
     *
     * @default 'FADE'
     *
     * @since 8.0.0
     */
    animation: SystemBarsAnimation;
}
export interface SystemBarsPlugin {
    /**
     * Set the current style of the system bars.
     *
     * @since 8.0.0
     */
    setStyle(options: SystemBarsStyleOptions): Promise<void>;
    /**
     * Show the system bars.
     *
     * @since 8.0.0
     */
    show(options?: SystemBarsVisibilityOptions): Promise<void>;
    /**
     * Hide the system bars.
     *
     * @since 8.0.0
     */
    hide(options?: SystemBarsVisibilityOptions): Promise<void>;
    /**
     * Set the animation to use when showing / hiding the status bar.
     *
     * Only available on iOS.
     *
     * @since 8.0.0
     */
    setAnimation(options: SystemBarsAnimationOptions): Promise<void>;
}
export declare class SystemBarsPluginWeb extends WebPlugin implements SystemBarsPlugin {
    setStyle(): Promise<void>;
    setAnimation(): Promise<void>;
    show(): Promise<void>;
    hide(): Promise<void>;
}
export declare const SystemBars: SystemBarsPlugin;
export {};
/******** END SYSTEM BARS PLUGIN ********/
