const constants = require('./constants');
const os = require('os');

/**
 * ELFHeader is the main program header containing the ELF signature and
 * general machine, program and section information.
 */
class ELFHeader {
  constructor(header) {
    Object.assign(
      this,
      {
        elfsig: constants.ELF_SIGNATURE_BYTES,
        class: '64',
        endian: 'lsb',
        osabi: 'unix-sysv',
        abiversion: 'none',
        type: 'exec',
        machine: 'amd64',
        version: 1,
        entry: null,
        phoff: null,
        shoff: null,
        flags: 0,
        ehsize: null,
        phentsize: null,
        phnum: null,
        shentsize: null,
        shnum: null,
        shstrndx: null,
      },
      get_current_arch_elf_header_values(),
      // override the default values with any custom values
      header
    );
  }

  static parse(stream) {
    return new ELFHeader({
      elfsig: stream.readBuf(4),
      class: constants.class[stream.readWord(1)],
      endian: constants.endian[stream.readWord(1)],
      osabi: constants.osabi[stream.readWord(1)],
      abiversion: constants.abiversion[stream.readWord(1)],
      padding: stream.readBuf(8),
      type: constants.type[stream.readWord(2)],
      machine: constants.machine[stream.readWord(2)],
      version: stream.readWord(4),
      entry: stream.readWord(),
      phoff: stream.readWord(),
      shoff: stream.readWord(),
      flags: stream.readWord(4),
      ehsize: stream.readWord(2),
      phentsize: stream.readWord(2),
      phnum: stream.readWord(2),
      shentsize: stream.readWord(2),
      shnum: stream.readWord(2),
      shstrndx: stream.readWord(2),
    });
  }

  calculate_size(elf_offset, elf) {
    this.elf_offset = elf_offset; // should always be 0
    this.elf_size = this.ehsize = elf.word_size * 3 + 40;
    return this.elf_size;
  }

  finalise(entrypoint, program_headers, section_headers, string_table_idx) {
    this.entry = entrypoint;
    this.phoff = program_headers[0].elf_offset;
    this.phentsize = program_headers[0].elf_size;
    this.phnum = program_headers.length;
    this.shoff = section_headers[0].elf_offset;
    this.shentsize = section_headers[0].elf_size;
    this.shnum = section_headers.length;
    this.shstrndx = string_table_idx;
  }

  write(stream) {
    stream.writeBuf(this.elfsig);
    stream.writeWord(constants.class[this.class], 1);
    stream.writeWord(constants.endian[this.endian], 1);
    stream.writeWord(constants.osabi[this.osabi], 1);
    stream.writeWord(constants.abiversion[this.abiversion], 1);
    stream.skip(8);
    stream.writeWord(constants.type[this.type], 2);
    stream.writeWord(constants.machine[this.machine], 2);
    stream.writeWord(this.version, 4);
    stream.writeWord(this.entry);
    stream.writeWord(this.phoff);
    stream.writeWord(this.shoff);
    stream.writeWord(this.flags, 4);
    stream.writeWord(this.ehsize, 2);
    stream.writeWord(this.phentsize, 2);
    stream.writeWord(this.phnum, 2);
    stream.writeWord(this.shentsize, 2);
    stream.writeWord(this.shnum, 2);
    stream.writeWord(this.shstrndx, 2);
  }
}

function get_current_arch_elf_header_values() {
    const res = {
        endian: /^m/i.test(os.endianness()) ? 'msb' : 'lsb',
    }
    switch(process.arch) {
        case 'arm': res.class = '32'; res.machine = 'arm'; break;
        case 'arm64': res.class = '64'; res.machine = 'arm'; break;
        case 'x32': res.class = '32'; res.machine = 'x86'; break;
        case 'x64':
        default: res.class = '64'; res.machine = 'amd64'; break;
    }
    return res;
}

module.exports = ELFHeader;
