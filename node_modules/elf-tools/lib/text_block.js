const ProgramHeader = require('./program_header');
const SectionHeader = require('./section_header');

/**
 * TextBlock defines the code and read-only data bytes of the program.
 * It creates both a program header and section header describing the raw buffer.
 * 
 * If ro_data exists, the code buffer should be pre-padded to a reasonable alignment since the
 * buffers are concatenated when writing to the ELF image.
 */
class TextBlock {
    constructor(elf, code, ro_data) {
      this.elf = elf;
      this.code = code;
      this.ro_data = ro_data;
      this.elf_offset = null;
      this.elf_size = code.byteLength + ro_data.byteLength,
  
      // the .text program header loads everything in the ELF image from start (offset:0)
      // to the end of ro_data chunk at the base address.
      // This means the loaded image includes the ELF signature, program headers, code and ro_data.
      this.program_header = new ProgramHeader({
        type: 'load',
        offset: 0,
        vaddr: elf.base_address,
        paddr: elf.base_address,
        filesz: null,
        memsz: null,
        flags: 'read|execute',
        align: 0x100000,
      });
  
      this.section_header = new SectionHeader({
        name: '.text',
        type: 'progbits',
        flags: 'alloc|execute',
        addr: null,
        offset: null,
        size: this.elf_size,
        link: 0,
        info: 0,
        addralign: 1,
        entsize: 0,
      });
    }
  
    calculate_size(elf_offset, elf) {
      this.elf_offset = elf_offset;
      this.program_header.filesz = elf_offset + this.elf_size;
      this.program_header.memsz = elf_offset + this.elf_size;
      this.section_header.addr = elf.base_address + elf_offset;
      this.section_header.offset = elf_offset;
      return this.elf_size;
    }
  
    write(stream) {
      stream.writeBuf(this.code);
      stream.writeBuf(this.ro_data);
    }
  }
  
module.exports = TextBlock;
  