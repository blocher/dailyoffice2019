const constants = require('./constants');
const flags = require('./flags');

/**
 * ProgramHeader contains information about how and where to load a segment of
 * the ELF image into memory for execution.
 */
class ProgramHeader {
  constructor(data) {
    Object.assign(this, data);
  }

  static parse(stream, elf_header) {
      const data = {
        type: constants.entryType[stream.readWord(4)],
        flags64: (elf_header.class === '64') ? flags.map(stream.readWord(4), constants.entryFlags) : '',
        offset: stream.readWord(),
        vaddr: stream.readWord(),
        paddr: stream.readWord(),
        filesz: stream.readWord(),
        memsz: stream.readWord(),
        flags32: (elf_header.class === '32') ? flags.map(stream.readWord(4), constants.entryFlags) : '',
        align: stream.readWord(),
      }
      data.flags = data.flags32 || data.flags64;
      delete data.flags32;
      delete data.flags64;

    return new ProgramHeader(data);
  }

  calculate_size(elf_offset, elf) {
    this.elf_offset = elf_offset;
    // type and flags are 32-bit, everything else is word_size
    return (this.elf_size = 6 * elf.word_size + 8);
  }

  finalise(filesz) {
    this.filesz = this.memsz = filesz;
  }

  write(stream, elf) {
    stream.writeWord(constants.entryType[this.type], 4);
    if (elf.elf_header.class === '64') {
      stream.writeWord(flags.unmap(this.flags, constants.entryFlags), 4);
    }
    stream.writeWord(this.offset); // offset into ELF image
    stream.writeWord(this.vaddr); // virtual address to load at
    stream.writeWord(this.paddr);
    stream.writeWord(this.filesz); // amount of data to copy from ELF image
    stream.writeWord(this.memsz); // amount of memory to allocate - any > filesz is zeroed (the .data program header uses this to allocate BSS data)
    if (elf.elf_header.class === '32') {
      stream.writeWord(flags.unmap(this.flags, constants.entryFlags), 4);
    }
    stream.writeWord(this.align);
  }
}

module.exports = ProgramHeader;
