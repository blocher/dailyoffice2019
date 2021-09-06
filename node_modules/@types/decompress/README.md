# Installation
> `npm install --save @types/decompress`

# Summary
This package contains type definitions for decompress (https://github.com/kevva/decompress#readme).

# Details
Files were exported from https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/decompress.
## [index.d.ts](https://github.com/DefinitelyTyped/DefinitelyTyped/tree/master/types/decompress/index.d.ts)
````ts
// Type definitions for decompress 4.2
// Project: https://github.com/kevva/decompress#readme
// Definitions by: York Yao <https://github.com/plantain-00>
//                 Jesse Bethke <https://github.com/jbethke>
// Definitions: https://github.com/DefinitelyTyped/DefinitelyTyped

/// <reference types="node" />

export = decompress;

declare function decompress(input: string | Buffer, output?: string | decompress.DecompressOptions, opts?: decompress.DecompressOptions): Promise<decompress.File[]>;

declare namespace decompress {
    interface File {
        data: Buffer;
        mode: number;
        mtime: string;
        path: string;
        type: string;
    }

    interface DecompressOptions {
        /**
         * Filter out files before extracting
         */
        filter?(file: File): boolean;
        /**
         * Map files before extracting
         */
        map?(file: File): File;
        /**
         * Array of plugins to use.
         * Default: [decompressTar(), decompressTarbz2(), decompressTargz(), decompressUnzip()]
         */
        plugins?: any[] | undefined;
        /**
         * Remove leading directory components from extracted files.
         * Default: 0
         */
        strip?: number | undefined;
    }
}

````

### Additional Details
 * Last updated: Tue, 06 Jul 2021 20:32:42 GMT
 * Dependencies: [@types/node](https://npmjs.com/package/@types/node)
 * Global values: none

# Credits
These definitions were written by [York Yao](https://github.com/plantain-00), and [Jesse Bethke](https://github.com/jbethke).
