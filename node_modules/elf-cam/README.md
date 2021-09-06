## Introduction

elf-cam is a WebAssembly(WASM) module to extract very specific information from binary files built for Linux, also known as ELF files.

It's used by other Netlify projects to detect Go and Rust binaries built for Netlify Functions.

## Usage

```js
import { readFile } = require("fs");
import * as elf from "elf-cam";

const buffer = await readFile(path);
try {
  const runtime = elf.detect(buffer);
  switch (runtime) {
    case elf.Runtime.Go: console.log("Go binary file"); break;
    case elf.Runtime.Rust: console.log("Rust binary file"); break;
    default: console.log("Unknown binary file");
  }
} catch (error) {
  console.log(error);
}
```

## Development

### 🛠️ Build with `wasm-pack build`

```
wasm-pack build --target nodejs --release
```

### 🎁 Publish to NPM with `wasm-pack publish`

```
wasm-pack publish
```
