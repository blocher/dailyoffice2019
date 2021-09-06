<img src="https://raw.githubusercontent.com/ehmicky/design/master/keep-func-props/keep-func-props.svg?sanitize=true" width="700"/>

[![Codecov](https://img.shields.io/codecov/c/github/ehmicky/keep-func-props.svg?label=tested&logo=codecov)](https://codecov.io/gh/ehmicky/keep-func-props)
[![Build](https://github.com/ehmicky/keep-func-props/workflows/Build/badge.svg)](https://github.com/ehmicky/keep-func-props/actions)
[![Node](https://img.shields.io/node/v/keep-func-props.svg?logo=node.js)](https://www.npmjs.com/package/keep-func-props)
[![Gitter](https://img.shields.io/gitter/room/ehmicky/keep-func-props.svg?logo=gitter)](https://gitter.im/ehmicky/keep-func-props)
[![Twitter](https://img.shields.io/badge/%E2%80%8B-twitter-4cc61e.svg?logo=twitter)](https://twitter.com/intent/follow?screen_name=ehmicky)
[![Medium](https://img.shields.io/badge/%E2%80%8B-medium-4cc61e.svg?logo=medium)](https://medium.com/@ehmicky)

Wrap a function without changing its name and other properties.

Function wrappers return a new function which means the original function's
`name` and other properties are usually lost. This module enhances them to keep
those properties instead.

The new function will also print the original function's body when stringified.

Function wrappers are commonly used in functional programming. They take a
function as input and return it wrapped. Examples include
[memoizing](https://github.com/planttheidea/moize) or ensuring a function is
only called once.

# Example

```js
const keepFuncProps = require('keep-func-props')
// Any function wrapper works
const memoize = require('lodash/memoize')

const betterMemoize = keepFuncProps(memoize)

const anyFunction = () => true

// Function `name` and other properties are kept
console.log(anyFunction) // `[Function: anyFunction]`
console.log(memoize(anyFunction)) // `[Function: memoized]`
console.log(betterMemoize(anyFunction)) // `[Function: anyFunction]`

// Function body is kept when stringified
console.log(String(anyFunction))
// () => true
console.log(String(memoize(anyFunction)))
// function() {
//   var args = arguments,
//   key = resolver ? resolver.apply(this, args) : args[0],
//   cache = memoized.cache;
//   ...
// }
console.log(String(betterMemoize(anyFunction)))
// /* Wrapped with memoized() */
// () => true
```

# Demo

You can try this library:

- either directly [in your browser](https://repl.it/@ehmicky/keep-func-props).
- or by executing the [`examples` files](examples/README.md) in a terminal.

# Install

```bash
npm install keep-func-props
```

# Usage

```js
const keepFuncProps = require('keep-func-props')

// Any function wrapper works
const wrapper = function (anyFunction) {
  return (...args) => anyFunction(...args)
}

// `betterWrapper` is like `wrapper` but it keeps the function properties
const betterWrapper = keepFuncProps(wrapper)
```

## keepFuncProps(wrapper)

`wrapper`: `(anyFunction, [...args]) => newFunction`\
_Returns_: new `wrapper`

A function `wrapper` is passed as argument. A copy of it is returned.

# See also

- [`mimic-fn`](https://github.com/sindresorhus/mimic-fn): same but for functions
  that do not wrap other functions.

# Support

If you found a bug or would like a new feature, _don't hesitate_ to
[submit an issue on GitHub](../../issues).

For other questions, feel free to
[chat with us on Gitter](https://gitter.im/ehmicky/keep-func-props).

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
<table><tr><td align="center"><a href="https://twitter.com/ehmicky"><img src="https://avatars2.githubusercontent.com/u/8136211?v=4" width="100px;" alt="ehmicky"/><br /><sub><b>ehmicky</b></sub></a><br /><a href="https://github.com/ehmicky/keep-func-props/commits?author=ehmicky" title="Code">💻</a> <a href="#design-ehmicky" title="Design">🎨</a> <a href="#ideas-ehmicky" title="Ideas, Planning, & Feedback">🤔</a> <a href="https://github.com/ehmicky/keep-func-props/commits?author=ehmicky" title="Documentation">📖</a></td></tr></table>

<!-- ALL-CONTRIBUTORS-LIST:END -->
