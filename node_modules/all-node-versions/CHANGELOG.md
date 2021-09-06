# 8.0.0

## Breaking changes

- The [return value](/README.md#return-value) is now an object instead of an
  array

## Features

- Add information about [major releases](/README.md#majors) including latest
  version and LTS name

# 7.0.1

## Dependencies

- Fix removing `core-js`

# 7.0.0

## Features

- Cache the list of available Node.js versions for one hour
- Add [`fetch` option](README.md#fetch) to configure this caching
- Works offline, providing it has been previously cached

## Dependencies

- Remove `core-js`

# 6.0.1

## Bug fixes

- Fix terminal color changing on Windows

# 6.0.0

## Breaking changes

- Minimal supported Node.js version is now `10.17.0`

# 5.0.2

## Bug fixes

- Fix crash when Node.js binary URL is invalid

# 5.0.1

## Dependencies

- Upgrade `fetch-node-website` to `4.1.0`

# 5.0.0

## Breaking changes

- Remove CLI.

# 4.1.0

## Dependencies

- Upgrade `fetch-node-website` to `4.0.0`

# 4.0.4

## Bug fixes

- Fix progress bar jitter.

# 4.0.3

## Internal

- Improve the appearance of the progress bar (which is not used at the moment)

# 4.0.2

## Bug fixes

- Fix a bug on non-interactive terminals

# 4.0.1

## Internal

- Internal changes

# 4.0.0

## Breaking changes

- Remove the `progress` option and CLI flag.

# 3.0.0

## Breaking changes

- Change the
  [`progress` option](https://github.com/ehmicky/all-node-versions/blob/master/README.md#progress)
  default value from `true` to `false`. That option displays a loading spinner.

## Features

- Add
  [`--no-progress` CLI flag](https://github.com/ehmicky/all-node-versions/blob/master/README.md#usage-cli)
  to hide the loading spinner.

# 2.3.3

## Internal

- Internal changes

# 2.3.2

## Bugs

- Fix `CTRL-C` not working

# 2.3.1

## Dependencies

- Upgrade `fetch-node-website`

# 2.3.0

## Features

- Add [`mirror` option](https://github.com/ehmicky/all-node-versions#mirror)
- Add `--help` and `--version` CLI flags

# 2.2.0

## Features

- Improve progress messages on console
- Add alternative names for `NODE_MIRROR`: `NVM_NODEJS_ORG_MIRROR`,
  `N_NODE_MIRROR` and `NODIST_NODE_MIRROR`

# 2.1.0

## Features

- Add CLI

# 2.0.0

## Features

- Retry downloading the Node.js index file on network errors.

# 1.0.1

## Internal

- Internal changes
