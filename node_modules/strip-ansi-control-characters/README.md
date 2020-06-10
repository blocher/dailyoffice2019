# strip-ansi-control-characters
Strips ANSI Control Characters from string or stream.

## Use cases
If you spawn a child process in NodeJS with `inherit` or
`pipe` -> `process.std{out,err}` as `stdio`, the child process can clear
terminal screen or mangle information printed by your application.
This package allows you to show output from child process with all colors
and formatting but without those pesky clear screen or clear line
control characters.

## API

```js
function stripFromString(input: string): string
function stripFromStream(bufferEncoding: string = 'utf8'): stream.Duplex
```

## Usage
```js
const stripAnsiCc = require('strip-ansi-control-characters');
const child_process = require('child_process');

const ps = child_process.spawn('vuepress', ['dev'], {
  env: process.env,
  stdio: 'pipe',
});

ps.stdout.pipe(stripAnsiCc.stream()).pipe(process.stdout);
ps.stderr.pipe(stripAnsiCc.stream()).pipe(process.stderr);
```

## License
MIT license - file included in repo
