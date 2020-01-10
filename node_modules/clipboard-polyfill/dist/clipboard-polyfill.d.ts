import { DT } from "./DT";
export { DT };
export declare function setDebugLog(f: (s: string) => void): void;
export declare function suppressWarnings(): void;
export declare function write(data: DT): Promise<void>;
export declare function writeText(s: string): Promise<void>;
export declare function read(): Promise<DT>;
export declare function readText(): Promise<string>;
declare const ClipboardPolyfillDefault: {
    DT: typeof DT;
    setDebugLog(f: (s: string) => void): void;
    suppressWarnings(): void;
    write(data: DT): Promise<void>;
    writeText(s: string): Promise<void>;
    read(): Promise<DT>;
    readText(): Promise<string>;
};
export default ClipboardPolyfillDefault;
