import { WebPlugin } from '@capacitor/core';
import type { BrowserPlugin, OpenOptions } from './definitions';
export declare class BrowserWeb extends WebPlugin implements BrowserPlugin {
    _lastWindow: Window | null;
    constructor();
    open(options: OpenOptions): Promise<void>;
    close(): Promise<void>;
}
declare const Browser: BrowserWeb;
export { Browser };
