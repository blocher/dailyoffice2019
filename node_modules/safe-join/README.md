# Safe Join

a tiny zero dependency library to join strings with slashes in them that isn't too smart about it!

## Install

```
yarn add safe-join # or npm i safe-join
```

## Usage

```ts
import { safeJoin } from 'safe-join'
safeJoin('foo', 'bar') // 'foo/bar'
safeJoin('foo/', 'bar') // 'foo/bar'
safeJoin('foo/', '/bar') // 'foo/bar'
safeJoin('foo', '/bar') // 'foo/bar'
safeJoin('http://foo/', '/bar') // 'http://foo/bar'

// works on multiple args too
safeJoin('foo', '/bar/', '/baz') // 'foo/bar/baz'
// etc
```

You might normally use path.join for this in Node but this works in the browser, also it doesnt swallow `/`'s when you need `//`.

Uses typescript because why not.

It does NOT handle query strings for you e.g. `safeJoin("https://foo", "bar", "&search=baz")` so be sure to handle those on your own. or use https://github.com/jfromaniello/url-join

## entire source code

so you know exactly what this

```ts
export function safeJoin(...args: string[]) {
  return args.reduce(_safeJoin)
}
// thanks to https://twitter.com/swyx/status/1106839872096985088
function _safeJoin(a: string, b: string) {
  return a.replace(/\/$/, '') + '/' + b.replace(/^\//, '')
}
```

## alternatives

https://github.com/jfromaniello/url-join

## TSDX Bootstrap

This project was bootstrapped with [TSDX](https://github.com/jaredpalmer/tsdx).
