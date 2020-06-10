# Release Fetch

Thin wrapper to fetch packages from GitHub releases.

## Usage

### Typescript

```ts
import * from 'release-fetch'

fetchLatest({ repository: 'netlify/netlify-cli', package: 'cli.tar.gz', destination: 'dist' });
```

## License

[MIT](/LICENSE)
