# 10.0.0

## Breaking changes

- Remove aliases support (like `latest`): please use
  [`node-version-alias`](https://github.com/ehmicky/node-version-alias) or
  [`preferred-node-version`](https://github.com/ehmicky/preferred-node-version)
  instead.
- Remove `cwd` option

# 9.0.1

## Dependencies

- Upgrade `all-node-versions`

# 9.0.0

## Breaking changes

- Rename `*` alias to [`latest` or `l`](/README.md#supported-aliases)
- Rename `.` alias to [`current` or `c`](/README.md#supported-aliases)
- Remove `_` alias

# 8.0.1

## Dependencies

- Fix removing `core-js`

# 8.0.0

## Breaking changes

- Replace the `cache` option with the more advanced
  [`fetch` option](/README.md#fetch)

## Dependencies

- Remove `core-js`

# 7.1.0

## Features

- Can use the `_` alias to refer to the
  [current process's Node.js version](/README.md#supported-aliases)
- Can use the `.` alias to refer to the
  [current project's Node.js version](/README.md#supported-aliases) using its
  `.nvmrc`, `.node-version` or `.naverc`. The current directory can be changed
  using the [`cwd` option](/README.md#cwd).

# 7.0.1

## Bug fixes

- Fix terminal color changing on Windows

# 7.0.0

## Breaking changes

- Minimal supported Node.js version is now `10.17.0`

# 6.1.2

## Bug fixes

- Fix crash when Node.js binary URL is invalid

# 6.1.1

## Dependencies

- Upgrade `all-node-versions` to `4.1.1`

# 6.1.0

## Features

- Use cache when offline (no network connection)

# 6.0.0

## Breaking changes

- Set the
  [`cache` option](https://github.com/ehmicky/normalize-node-version/blob/master/README.md#cache)
  default value to `true`.

# 5.1.1

## Dependencies

- Reduce the number of dependencies

# 5.1.0

## Dependencies

- Upgrade `all-node-versions` to `4.1.0`

# 5.0.0

## Breaking changes

- Add the
  [`cache` option](https://github.com/ehmicky/normalize-node-version/blob/master/README.md#cache)
  to cache the HTTP request made to retrieve the list of available Node.js
  versions. This defaults to `false`.

# 4.1.4

## Bug fixes

- Fix progress bar jitter.

# 4.1.3

## Internal

- Improve the appearance of the progress bar (which is not used at the moment)

# 4.1.2

## Bug fixes

- Fix a bug on non-interactive terminals

# 4.1.1

## Internal

- Internal changes

# 4.1.0

## Features

- Improve speed.

# 4.0.0

## Breaking changes

- Remove the `progress` option and CLI flags.

# 3.0.0

## Features

- Add the
  [`progress` option](https://github.com/ehmicky/normalize-node-version/blob/master/README.md#progress).
  That option displays a loading spinner.

# 2.2.3

## Internal

- Internal changes

# 2.2.2

## Bugs

- Fix `CTRL-C` not working

# 2.2.1

## Dependencies

- Upgrade `all-node-versions`

# 2.2.0

## Features

- Add
  [`mirror` option](https://github.com/ehmicky/normalize-node-version#mirror)

# 2.1.0

## Features

- Improve progress messages on console
- Add alternative names for `NODE_MIRROR`: `NVM_NODEJS_ORG_MIRROR`,
  `N_NODE_MIRROR` and `NODIST_NODE_MIRROR`

# 2.0.1

## Bugs

- Fix cache invalidation bug

# 2.0.0

## Features

- Retry downloading the Node.js index file on network errors

# 1.0.1

## Internal

- Internal changes
