[![Codecov](https://img.shields.io/codecov/c/github/ehmicky/all-node-versions.svg?label=tested&logo=codecov)](https://codecov.io/gh/ehmicky/all-node-versions)
[![Build](https://github.com/ehmicky/all-node-versions/workflows/Build/badge.svg)](https://github.com/ehmicky/all-node-versions/actions)
[![Node](https://img.shields.io/node/v/all-node-versions.svg?logo=node.js)](https://www.npmjs.com/package/all-node-versions)
[![Gitter](https://img.shields.io/gitter/room/ehmicky/all-node-versions.svg?logo=gitter)](https://gitter.im/ehmicky/all-node-versions)
[![Twitter](https://img.shields.io/badge/%E2%80%8B-twitter-4cc61e.svg?logo=twitter)](https://twitter.com/intent/follow?screen_name=ehmicky)
[![Medium](https://img.shields.io/badge/%E2%80%8B-medium-4cc61e.svg?logo=medium)](https://medium.com/@ehmicky)

List all available Node.js versions.

Sorted from the most to the least recent. Includes major release and LTS
information.

# Install

```bash
npm install all-node-versions
```

# Usage

<!-- Remove 'eslint-skip' once estree supports top-level await -->
<!-- eslint-skip -->

```js
const allNodeVersions = require('all-node-versions')

const { versions, majors } = await allNodeVersions(options)

console.log(versions)
// ['13.13.0', '13.12.0', ..., '0.1.15', '0.1.14']

console.log(majors)
// [
//   { major: 13, latest: '13.13.0' },
//   { major: 12, latest: '12.16.2', lts: 'erbium' },
//   { major: 11, latest: '11.15.0' },
//   { major: 10, latest: '10.20.1', lts: 'dubnium' },
//   { major: 9, latest: '9.11.2' },
//   { major: 8, latest: '8.17.0', lts: 'carbon' },
//   { major: 7, latest: '7.10.1' },
//   { major: 6, latest: '6.17.1', lts: 'boron' },
//   { major: 5, latest: '5.12.0' },
//   { major: 4, latest: '4.9.1', lts: 'argon' },
//   { major: 0, latest: '0.12.18' }
// ]
```

## allNodeVersions(options?)

`options`: `object`\
_Returns_: `Promise<object>`

### Return value

The return value resolves to an object with the following properties.

#### versions

_Type_: `string[]`

List of available Node.js versions sorted from the most to the least recent.
Each version is a `major.minor.patch` string.

#### majors

_Type_: `object[]`

List of Node.js major releases sorted from the most to the least recent. Each
major release has the following properties.

##### major

_Type_: `number`

Major version number. `0` for old releases `0.*.*`.

##### latest

_Type_: `string`

Latest version for that major release, as a `major.minor.patch` string.

##### lts

_Type_: `string?`

LTS name, lowercased. `undefined` if the major release is not LTS.

### options

#### mirror

_Type_: `string`\
_Default_: `https://nodejs.org/dist`

Base URL to fetch the list of available Node.js versions. Can be customized (for
example `https://npm.taobao.org/mirrors/node`).

The following environment variables can also be used: `NODE_MIRROR`,
`NVM_NODEJS_ORG_MIRROR`, `N_NODE_MIRROR` or `NODIST_NODE_MIRROR`.

#### fetch

_Type_: `boolean`\
_Default_: `undefined`

The list of available Node.js versions is cached for one hour by default. If the
`fetch` option is:

- `true`: the cache will not be used
- `false`: the cache will be used even if it's older than one hour

# See also

- [`nve`](https://github.com/ehmicky/nve): Run a specific Node.js version (CLI)
- [`nvexeca`](https://github.com/ehmicky/nve): Run a specific Node.js version
  (programmatic)
- [`get-node`](https://github.com/ehmicky/get-node): Download Node.js
- [`normalize-node-version`](https://github.com/ehmicky/normalize-node-version):
  Normalize and validate Node.js versions
- [`fetch-node-website`](https://github.com/ehmicky/fetch-node-website): Fetch
  releases on nodejs.org

# Support

If you found a bug or would like a new feature, _don't hesitate_ to
[submit an issue on GitHub](../../issues).

For other questions, feel free to
[chat with us on Gitter](https://gitter.im/ehmicky/all-node-versions).

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
<table><tr><td align="center"><a href="https://twitter.com/ehmicky"><img src="https://avatars2.githubusercontent.com/u/8136211?v=4" width="100px;" alt="ehmicky"/><br /><sub><b>ehmicky</b></sub></a><br /><a href="https://github.com/ehmicky/all-node-versions/commits?author=ehmicky" title="Code">💻</a> <a href="#design-ehmicky" title="Design">🎨</a> <a href="#ideas-ehmicky" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/ehmicky/all-node-versions/commits?author=ehmicky" title="Documentation">📖</a></td></tr></table>

<!-- ALL-CONTRIBUTORS-LIST:END -->
