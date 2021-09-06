# 5.0.3

## Dependencies

- Fix removing `core-js`

# 5.0.2

## Dependencies

- Remove `core-js`

# 5.0.1

## Bug fixes

- Fix terminal color changing on Windows

# 5.0.0

## Breaking changes

- Minimal supported Node.js version is now `10.17.0`

# 4.1.1

## Bug fixes

- Fix crash when Node.js binary URL is invalid

# 4.1.0

## Features

- Improve the appearance of the progress bar

# 4.0.0

## Breaking changes

- Upgrade `got` to `10.0.0-alpha.2.2`.

# 3.3.1

## Bug fixes

- Fix progress bar jitter.

# 3.3.0

## Features

- Improve the appearance of the progress bar with the
  [`progress` option](https://github.com/ehmicky/fetch-node-website/blob/master/README.md#progress).

# 3.2.1

## Bug fixes

- The
  [`progress` option](https://github.com/ehmicky/fetch-node-website/blob/master/README.md#progress)
  was not working in non-interactive terminals.

# 3.2.0

## Features

- The
  [`progress` option](https://github.com/ehmicky/fetch-node-website/blob/master/README.md#progress)
  now displays a progress bar instead of a spinner.

# 3.1.0

## Features

- Show percentage instead of number of megabytes in spinner

# 3.0.0

## Breaking changes

- Change the
  [`progress` option](https://github.com/ehmicky/fetch-node-website/blob/master/README.md#progress)
  default value from `true` to `false`. That option displays a loading spinner.

# 2.3.1

## Internal

- Internal changes

# 2.3.0

## Features

- Only show one spinner at once when called several times in parallel

# 2.2.2

## Bugs

- Fix CTRL-C not working

# 2.2.1

## Features

- Improve CLI spinner

# 2.2.0

## Features

- Allow mirrors to be specified via a `mirror` option.

# 2.1.0

## Features

- Improve progress messages on console
- Add alternative names for `NODE_MIRROR`: `NVM_NODEJS_ORG_MIRROR`,
  `N_NODE_MIRROR` and `NODIST_NODE_MIRROR`

# 2.0.0

## Features

- Retry downloading the Node.js binaries on network errors.

## Breaking changes

- The return value now resolves to a stream, not to a fetch `Response`.

# 1.1.0

## Features

- Add a loading spinner. Can be disabled with the `progress` option.
