const constants = require('./constants');
const ELFHeader = require('./elf_header');
const ProgramHeader = require('./program_header');
const SectionHeader = require('./section_header');
const StringTable = require('./string_table');

/**
 * Returns the integer-writing method that should be used
 * @param {'lsb'|'msb'} endian
 */
function getReadIntFn(endian) {
  switch (endian) {
    case 'lsb':
      return 'readUIntLE';
    case 'msb':
      return 'readUIntBE';
    default:
      new Error('Invalid endian: ' + endian);
  }
}

function parse(image) {
    // load the first part of the ELF-header with the signature, word-size and endian
  const hdr_bytes = image.slice(0, 8);
  const hdr = {
    signature: hdr_bytes.slice(0, 4),
    class: constants.class[hdr_bytes[4]],
    endian: constants.endian[hdr_bytes[5]],
    osabi: constants.osabi[hdr_bytes[6]],
    abiversion: constants.abiversion[hdr_bytes[7]],
  };
  if (!hdr.signature.equals(constants.ELF_SIGNATURE_BYTES)) {
    throw new Error('Invalid ELF signature bytes');
  }

  const stream = {
    endian: hdr.endian,
    image,
    idx: 0,
    word_size: hdr.class / 8,
    readIntFn: getReadIntFn(hdr.endian),
    seek(offset) {
        return this.idx = offset;
    },
    skip(sz) {
        return this.idx += sz;
    },
    readWord(sz) {
      sz = sz || this.word_size;
      // Node v10 no longer allows reads > 6 bytes
      if (sz > 6) {
        let buf = this.image.slice(this.idx, this.idx += sz);
        if (this.endian === 'lsb') buf = buf.reverse();
        const hex = buf.toString('hex').match(/[^0].*|0$/)[0];
        const n = parseInt(hex, 16);
        // sanity check
        if (n.toString(16) !== hex) {
          throw new Error(`Cannot represent 0x${buf.toString('hex')} as a JS number`);
        }
        return n;
      }
      this.idx += sz;
      return this.image[this.readIntFn](this.idx - sz, sz);
    },
    readBuf(sz) {
      return this.image.slice(this.idx, (this.idx += sz));
    },
  };

  // parse the header (fully)
  const header = ELFHeader.parse(stream);
  const programs = [];
  const sections = [];

  // parse the program headers
  stream.seek(header.phoff);
  for (let i=0; i < header.phnum; i++) {
    const ph = ProgramHeader.parse(stream, header);
    programs.push({
        header: ph,
        data: image.slice(ph.offset, ph.offset + ph.filesz),
      })
  }

  // parse the section headers
  stream.seek(header.shoff);
  for (let i=0; i < header.shnum; i++) {
    const sh = SectionHeader.parse(stream);
    sections.push({
        header: sh,
        data: image.slice(sh.offset, sh.offset + sh.size),
      })
  }

  // resolve the section header string table and convert the section header name offsets to real names
  const sh_string_table = StringTable.parse(sections[header.shstrndx]);
  sections.forEach(section => {
      section.header.name = sh_string_table.getString(section.header.name);
  });


  return {
      header,
      programs,
      sections,
      sh_string_table,
  }
}

module.exports = {
    parse,
}
