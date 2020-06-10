const SectionHeader = require('./section_header');

/**
 * The string table is used to store section and symbol names. In the ELF image, it consists
 * of a sequence of null-terminated ASCII strings.
 */
class StringTable {
  constructor(arg) {
    if (typeof arg === 'object') {
      // from StringTable.parse()
      Object.assign(this, arg);
      return;
    }

    this.strings = '';
    this.section_header = new SectionHeader({
      name: arg,
      type: 'strtab',
      flags: '',
      addr: 0,
      offset: null,
      size: null,
      link: 0,
      info: 0,
      addralign: 1,
      entsize: 0,
    });
  }

  static parse({ header, data }) {
    return new StringTable({
      section_header: header,
      strings: data.toString(StringTable.ENCODING),
    });
  }

  add_string(str) {
    return this.getStringOffset(str, true);
  }

  /**
   * Returns the offset into the table of the specified string
   * @param {string} str string to locate
   * @param {boolean} [add] optional - automatically add the string if it's not in the table
   */
  getStringOffset(str, add = false) {
    // strings are a concatenated list of null-terminated values
    const str0 = str + '\0';
    let offset = this.strings.indexOf(str0);
    if (offset < 0) {
      if (!add) {
        throw new Error(`String '${str}' not found in string table`);
      }
      offset = this.strings.length;
      this.strings += str0;
    }
    return offset;
  }

  // retrieve the string from the table at the given offset
  getString(offset) {
    if (offset < 0 || offset >= this.strings.length)
      throw new RangeError(`Offset out of range of string table. Offset=${offset}, Table length=${this.strings.length}`);
    const s = this.strings.slice(offset, this.strings.indexOf('\0', offset));
    return s;
  }

  calculate_size(elf_offset) {
    this.elf_offset = this.section_header.offset = elf_offset;
    // ELF only allows ascii chars, so bytes = length
    this.elf_size = this.section_header.size = this.strings.length;
    return this.elf_size;
  }

  write(stream) {
    stream.writeBuf(Buffer.from(this.strings, StringTable.ENCODING));
  }
}

StringTable.ENCODING = 'ascii';

module.exports = StringTable;
