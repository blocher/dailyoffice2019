const constants = require('./constants');
const flags = require('./flags');

/**
 * SectionHeader defines a chunk of the ELF image.
 * Each section has a name which must be added to the StringTable.
 */
class SectionHeader {
  constructor(data) {
    Object.assign(this, data);
  }

  static null() {
    return new SectionHeader({
        name: '',
        type: 'null',
        flags: '',
        addr: 0,
        offset: 0,
        size: 0,
        link: 0,
        info: 0,
        addralign: 0,
        entsize: 0,
    });
  }

  static parse(stream) {
      return new SectionHeader({
        name: stream.readWord(4),   // name string can only be determined once all the section headers are parsed
        type: constants.sectType[stream.readWord(4)],
        flags: flags.map(stream.readWord(), constants.sectType),
        addr: stream.readWord(),
        offset: stream.readWord(),
        size: stream.readWord(),
        link: stream.readWord(4),
        info: stream.readWord(4),
        addralign: stream.readWord(),
        entsize: stream.readWord(),
      })
  }

  calculate_size(elf_offset, elf) {
    this.elf_offset = elf_offset;
    return this.elf_size = (6 * elf.word_size) + (4 * 4);
  }

  write(stream, elf) {
    stream.writeWord(elf.string_table.getStringOffset(this.name), 4);
    stream.writeWord(constants.sectType[this.type], 4);
    // flags
    let value = flags.unmap(this.flags, constants.sectFlags);
    stream.writeWord(value);
    // remaining fields are all integers
    const fields = [
      'addr', // virtual address for the section
      'offset', // ELF image offset
      'size', // ELF image size
      'link',
      'info',
      'addralign',
      'entsize',
    ];
    for (let field of fields) {
      let intsz = /link|info/.test(field) ? 4 : undefined;
      stream.writeWord(this[field], intsz);
    }
  }
}

// the name of the Section Header string table
SectionHeader.SHSTRTAB_NAME = '.shstrtab';

module.exports = SectionHeader;
