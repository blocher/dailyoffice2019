[![Codecov](https://img.shields.io/codecov/c/github/ehmicky/fetch-node-website.svg?label=tested&logo=codecov)](https://codecov.io/gh/ehmicky/fetch-node-website)
[![Build](https://github.com/ehmicky/fetch-node-website/workflows/Build/badge.svg)](https://github.com/ehmicky/fetch-node-website/actions)
[![Node](https://img.shields.io/node/v/fetch-node-website.svg?logo=node.js)](https://www.npmjs.com/package/fetch-node-website)
[![Gitter](https://img.shields.io/gitter/room/ehmicky/fetch-node-website.svg?logo=gitter)](https://gitter.im/ehmicky/fetch-node-website)
[![Twitter](https://img.shields.io/badge/%E2%80%8B-twitter-4cc61e.svg?logo=twitter)](https://twitter.com/intent/follow?screen_name=ehmicky)
[![Medium](https://img.shields.io/badge/%E2%80%8B-medium-4cc61e.svg?logo=medium)](https://medium.com/@ehmicky)

Fetch releases on nodejs.org

Download release files available on
[`https://nodejs.org/dist/`](https://nodejs.org/dist/).

# Example

<!-- Remove 'eslint-skip' once estree supports top-level await -->
<!-- eslint-skip -->

```js
const fetchNodeWebsite = require('fetch-node-website')

const stream = await fetchNodeWebsite('v12.8.0/node-v12.8.0-linux-x64.tar.gz')

// Example with options
const otherStream = await fetchNodeWebsite(
  'v12.8.0/node-v12.8.0-linux-x64.tar.gz',
  {
    progress: true,
    mirror: 'https://npm.taobao.org/mirrors/node',
  },
)
```

# Install

```bash
npm install fetch-node-website
```

# Usage

## fetchNodeWebsite(path, options?)

`path`: `string`\
`options`: `object`\
_Returns_: `Promise<Stream>`

### options

#### progress

_Type_: `boolean`\
_Default_: `false`

Show a progress bar.

#### mirror

_Type_: `string`\
_Default_: `https://nodejs.org/dist`

Base URL. Can be customized (for example `https://npm.taobao.org/mirrors/node`).

The following environment variables can also be used: `NODE_MIRROR`,
`NVM_NODEJS_ORG_MIRROR`, `N_NODE_MIRROR` or `NODIST_NODE_MIRROR`.

# See also

- [`nve`](https://github.com/ehmicky/nve): Run a specific Node.js version (CLI)
- [`nvexeca`](https://github.com/ehmicky/nve): Run a specific Node.js version
  (programmatic)
- [`get-node`](https://github.com/ehmicky/get-node): Download Node.js
- [`normalize-node-version`](https://github.com/ehmicky/normalize-node-version):
  Normalize and validate Node.js versions
- [`all-node-versions`](https://github.com/ehmicky/all-node-versions): List all
  available Node.js versions

# Support

If you found a bug or would like a new feature, _don't hesitate_ to
[submit an issue on GitHub](../../issues).

For other questions, feel free to
[chat with us on Gitter](https://gitter.im/ehmicky/fetch-node-website).

Everyone is welcome regardless of personal background. We enforce a
[Code of conduct](CODE_OF_CONDUCT.md) in order to promote a positive and
inclusive environment.

# Contributing

This project was made with ❤️. The simplest way to give back is by starring and
sharing it online.

If the documentation is unclear or has a typo, please click on the page's `Edit`
button (pencil icon) and suggest a correction.

If you would like to help us fix a bug or add a new feature, please check our
[guidelines](CONTRIBUTING.md). Pull requests are welcome!

<!-- Thanks go to our wonderful contributors: -->

<!-- ALL-CONTRIBUTORS-LIST:START -->
<!-- prettier-ignore -->
<table><tr><td align="center"><a href="https://twitter.com/ehmicky"><img src="https://avatars2.githubusercontent.com/u/8136211?v=4" width="100px;" alt="ehmicky"/><br /><sub><b>ehmicky</b></sub></a><br /><a href="https://github.com/ehmicky/fetch-node-website/commits?author=ehmicky" title="Code">💻</a> <a href="#design-ehmicky" title="Design">🎨</a> <a href="#ideas-ehmicky" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/ehmicky/fetch-node-website/commits?author=ehmicky" title="Documentation">📖</a></td></tr></table>

<!-- ALL-CONTRIBUTORS-LIST:END -->
