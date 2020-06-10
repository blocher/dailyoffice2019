const ProgramHeader = require('./program_header');
const SectionHeader = require('./section_header');

/**
 * DataBlock defines the writable data bytes and any pre-zeroed data area in the program.
 * It creates both a program header and section header describing the raw data block.
 *
 * The program header sets a memory_size = file_size + bss_length. This makes the loader allocate
 * and zero additional bytes for the data segment.
 */

class DataBlock {
  constructor(elf, rw_data, bss_length) {
    this.elf = elf;
    this.rw_data = rw_data;
    this.bss_length = bss_length;
    this.elf_offset = null;
    this.elf_size = this.rw_data.length;

    this.program_header = new ProgramHeader({
      type: 'load',
      offset: null,
      vaddr: null,
      paddr: null,
      filesz: this.elf_size,
      memsz: this.elf_size + this.bss_length, // memsz > filesz -> fill bss data with zero
      flags: 'read|write',
      align: elf.word_size,
    });
    this.section_header = new SectionHeader({
      name: '.data',
      type: 'progbits',
      flags: 'alloc|write',
      addr: null,
      offset: null,
      size: this.elf_size,
      link: 0,
      info: 0,
      addralign: 1,
      entsize: 0,
    });
  }

  calculate_size(elf_offset) {
    this.elf_offset = elf_offset;
    this.program_header.offset = elf_offset;
    this.section_header.offset = elf_offset;
    this.program_header.vaddr = this.elf.base_address + elf_offset;
    this.program_header.paddr = this.elf.base_address + elf_offset;
    this.section_header.addr = this.elf.base_address + elf_offset;
    return this.elf_size;
  }

  write(stream) {
    stream.writeBuf(this.rw_data);
  }
}

module.exports = DataBlock;
