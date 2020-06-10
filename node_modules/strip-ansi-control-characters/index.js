const stream = require('stream');

const REGEXP_NEWLINE = /(\r\n|\r|\n)/;
const REGEXP_ANSI_CC = /\u001Bc*\[*[0-9]*[HABCDEFGJKsu];*[0-9]*/gi;

class AnsiTransformStream extends stream.Transform {
  constructor(bufferEncoding) {
    super();
    this.bufferEncoding = bufferEncoding;
    this.line = '';
  }

  flushLine(contents) {
    this.push(contents.replace(REGEXP_ANSI_CC, ''));
  }

  _flush(callback) {
    // Emit that last bit of data
    if (this.line.length) {
      this.flushLine(this.line);
      this.line = '';
    }
    callback();
  }

  _transform(chunk, encoding, callback) {
    let contents = encoding === 'buffer' ? chunk.toString(this.bufferEncoding) : chunk;

    if (typeof contents !== 'string') {
      contents = contents.toString();
    }
    const lineContents = this.line + contents;

    if (lineContents.indexOf('\r') !== -1 || lineContents.indexOf('\n') !== -1) {
      // We found a line
      const lines = lineContents.split(REGEXP_NEWLINE);

      if (lines.length === 1) {
        // Fail-safe
        this.line = lines[0];
      } else {
        // Ignoring last chunk intentionally, as it may be incomplete
        for (let i = 0, length = lines.length - 1; i < length; i += 1) {
          const currentLine = lines[i];
          if (currentLine === '\r' || currentLine === '\n' || currentLine === '\r\n') {
            // .split() with regexp returns the separators, we let these pass through
            // untouched
            this.push(currentLine);
          } else {
            this.flushLine(lines[i]);
          }
        }

        // Store the last chunk to process at a later time
        this.line = lines[lines.length - 1];
      }
    } else {
      this.line = lineContents;
    }

    callback();
  }
}

function stripFromString(input) {
  if (typeof input !== 'string') {
    throw new Error(`Expected first parameter to be string, got: ${typeof input}`);
  }
  return input.replace(REGEXP_ANSI_CC, '');
}

function stripFromStream(givenEncoding) {
  const encoding = typeof givenEncoding === 'string' ? givenEncoding : 'utf8';

  if (typeof encoding !== 'string') {
    throw new Error(`Expected first parameter to be string, got: ${typeof encoding}`);
  }

  return new AnsiTransformStream(encoding);
}

module.exports = {
  string: stripFromString,
  stream: stripFromStream,
};
