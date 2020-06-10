const DataBlock = require('./data_block');
const ELFHeader = require('./elf_header');
const SectionHeader = require('./section_header');
const StringTable = require('./string_table');
const TextBlock = require('./text_block');
const Readable = require('stream').Readable;

/**
 * Minimal ELF layout (32/64 bit):
 *
 * - ELF header (52/64)
 * - Program headers
 *     0 load (56/32)
 * - .text section (variable, padded) - r/e - contains code and ro data
 * - .data section (variable, padded) - r/w - contains rw data and bss length
 * - .shstrtab section ()
 * - Section headers (40/72):
 *     0 null
 *     1 .text
 *     2 .data
 *     3 .shstrtab
 *
 * The program-headers load everything from 0 to the end of .data section from the image into memory.
 * The .text segment contains executable code and read-only data
 * The .data segment contains writable data and zero-init bytes (bss)
 * The .data segment may be zero-length
 * The image entry point is always at the start of the .text section
 * The .shstrtab section contains the names of the section headers and any symbols.
 *
 */

 const zero_len_data = Buffer.alloc(0);

 // the default address the image is loaded at
 const default_image_base_address = 0x400000;
 
 /**
 * ELF image builder
 */
class ELFWriter {

  constructor(base_address, code, rodata = zero_len_data, rwdata = zero_len_data, bss_length = 0, entry_offset = 0, elf_header = null) {
    check_elfwriter_args(base_address, code, rodata, rwdata, bss_length, entry_offset, elf_header);

    this.base_address = base_address;
    this.entry_offset = entry_offset;
    this.elf_header = new ELFHeader(elf_header);

    this.writeIntFn = get_writeIntFn(this.elf_header.endian);
    this.word_size = this.elf_header.class / 8;

    this.text_block = new TextBlock(this, code, rodata);
    this.data_block = new DataBlock(this, rwdata, bss_length);
    this.string_table = new StringTable(SectionHeader.SHSTRTAB_NAME);

    this.program_headers = [
      this.text_block.program_header,
      this.data_block.program_header,
    ];

    this.section_headers = [
      SectionHeader.null(),
      this.text_block.section_header,
      this.data_block.section_header,
      this.string_table.section_header,
    ];
  }

  /**
   * @param {Writable} [stream] (optional) stream to write to
   * @returns {Buffer|Number}
   */
  build(stream) {
    // create an rough map of all the parts that go into the ELF image
    const elf_parts = [
      this.elf_header,
      ...this.program_headers,
      this.text_block,
      this.data_block,
      this.string_table,
      align_to(this.word_size),
      ...this.section_headers,
    ];

    // add all the section header names to the string table
    // - the string table must be up-to-date before the size is calculated
    this.section_headers.forEach(s => {
        this.string_table.add_string(s.name);
    });

    // work out the size and offset for each part
    let elf_image_size = 0;
    elf_parts.forEach(elf_part => {
      const elf_part_size = elf_part.calculate_size(elf_image_size, this);
      elf_image_size += elf_part_size;
    });

    // find the section-header string table index
    const shstrtabidx = this.section_headers.findIndex(sh => sh.name === SectionHeader.SHSTRTAB_NAME);

    // we only set the default entrypoint value if it hasn't already been customised in the elf_header
    let entrypoint = this.elf_header.entry;
    if (entrypoint === null) {
        // the default program entrypoint is the offset from the start of the text (code) block
        entrypoint = this.base_address + this.text_block.elf_offset + this.entry_offset;
    }

    // finalise the details in the header
    this.elf_header.finalise(
      entrypoint,
      this.program_headers,
      this.section_headers,
      shstrtabidx
    );

    let elf_image;
    if (stream) {
        // create a wrapper around the stream with the same methods as the buffer
        elf_image = this.create_stream_wrapper(stream);
    } else {
        elf_image = this.create_buffer_wrapper(elf_image_size);
    }

    // write all the parts to the ELF image buffer
    elf_parts.forEach(elf_part => {
        elf_part.write(elf_image, this);
    })

    if (stream) {
        stream.push(null); // end of stream
        return elf_image.idx;
    }

    return elf_image.buffer;
  }

  create_buffer_wrapper(size) {
    return {
        buffer: Buffer.alloc(size),
        endian: this.elf_header.endian,
        idx: 0,
        word_size: this.word_size,
        writeIntFn: this.writeIntFn,

        skip(sz) {
          this.idx += sz;
        },

        writeBuf(buf) {
            buf.copy(this.buffer, this.idx);
            this.idx += buf.byteLength;
        },

        writeWord(value, sz) {
          if (!Number.isSafeInteger(value)) {
              throw new Error(`Cannot write non-integer value: ${value}`);
            }
            sz = sz || this.word_size;
            // From v10, Buffer no longer allows writeUInt.. with bytelengths > 6
            // so for 64-bit integers, write via a temporary buffer
            if (sz > 6) {
                const buf = Buffer.alloc(sz);
                const idx = this.endian === 'lsb' ? 0 : (sz-6);
                buf[this.writeIntFn](value, idx, 6);
                this.writeBuf(buf);
                return;
            }
            this.buffer[this.writeIntFn](value, this.idx, sz);
            this.idx += sz;
        },
    }
}

  create_stream_wrapper(stream) {
      return {
          stream,
          idx: 0,
          word_size: this.word_size,
          writeIntFn: this.writeIntFn,

          skip(sz) {
              this.stream.push(Buffer.alloc(sz));
            // this.stream.write(Buffer.alloc(sz));
              this.idx += sz;
          },

          writeBuf(buf) {
            this.stream.push(buf);
            //this.stream.write(buf);
            this.idx += buf.byteLength;
          },

          writeWord(value, sz) {
            if (!Number.isSafeInteger(value)) {
                throw new Error(`Cannot write non-integer value: ${value}`);
              }
              sz = sz || this.word_size;
              const wordbuf = Buffer.alloc(sz);
              // From v10, Buffer no longer allows writeUInt.. with bytelengths > 6
              let idx = 0;
              if (sz > 6) {
                  idx = this.endian === 'lsb' ? 0 : (sz - 6);
                  sz = 6;
              }
              wordbuf[this.writeIntFn](value, idx, sz);
              //this.stream.write(wordbuf);
              this.stream.push(wordbuf);
              this.idx += sz;
          },
      }
  }
}


function check_elfwriter_args(base_address, code, rodata, rwdata, bss_length, entry_offset, elf_header) {
    if (typeof base_address !== 'number' || (base_address < 0) || ((base_address|0) !== base_address)) {
        throw new Error('base_address must be a non-negative integer')
    }
    if (!Buffer.isBuffer(code) || (code.byteLength <= 0)) {
        throw new Error('code must be a Buffer with at least 1 byte');
    }
    if (rodata && !Buffer.isBuffer(rodata)) {
        throw new Error('rodata must be a Buffer');
    }
    if (rwdata && !Buffer.isBuffer(rwdata)) {
        throw new Error('rwdata must be a Buffer');
    }
    if (typeof bss_length !== 'number' || (bss_length < 0) || ((bss_length|0) !== bss_length)) {
        throw new Error('bss_length must be a non-negative integer')
    }
    if (typeof entry_offset !== 'number' || (entry_offset < 0) || !Number.isSafeInteger(entry_offset)) {
        throw new Error('entry_offset must be a non-negative integer')
    }
    if (typeof elf_header !== 'object') {
        throw new Error('elf_header must be an object')
    }
    // we don't perform any validation of the elf_header values
}


  /**
 * Returns the integer-writing method that should be used
 * @param {'lsb'|'msb'} endian 
 */
function get_writeIntFn(endian) {
  switch (endian) {
    case 'lsb':
      return 'writeUIntLE';
    case 'msb':
      return 'writeUIntBE';
    default:
      new Error('Invalid endian: ' + endian);
  }
}

/**
 * Helper function to pad content to a specified alignment
 * @param {number} boundary
 * @returns {Buffer}
 */
function align_to(boundary) {
  return {
    boundary,
    elf_size: null,
    elf_offset: null,
    calculate_size(elf_offset) {
        this.elf_offset = elf_offset;
        let mod = elf_offset % this.boundary;
        if (mod === 0) {
            mod = this.boundary;
        }
        return (this.elf_size = boundary - mod);
    },
    write(stream) {
        stream.skip(this.elf_size);
    },
  };
}


/**
 * Build an ELF image. The resulting image contains the concatenation (with no padding) of:
 *   - code
 *   - rodata
 *   - rwdata
 *   - zeros (bss_length)
 *
 * @param {Buffer|Object} opts
 * @param {Buffer} opts.code code bytes
 * @param {Buffer} [opts.rodata] (optional) read-only data bytes
 * @param {Buffer} [opts.rwdata] (optional) read-write data bytes
 * @param {Number} [opts.bss_length] size of pre-zeroed read-write data
 * @param {Number} [opts.base_address] memory address for loading the elf image (default: 0x400000)
 * @param {Number} [opts.entry_offset] offset into the code buffer for the first instruction executed (default: 0)
 * @param {Object} [opts.elf_header] custom ELF header values
 * @returns {Buffer}
 */
function build(opts) {
    let { code, rodata, rwdata, bss_length, base_address, entry_offset, elf_header } = Buffer.isBuffer(opts) ? {code: opts} : opts;

    const has_base_address = typeof(base_address) !== 'undefined'
    const has_entry_offset = typeof(entry_offset) !== 'undefined'

    // if the entrypoint is set in the custom elf_header, we don't allow base_address or entry_offset to be set
    if (elf_header && Object.prototype.hasOwnProperty.call(elf_header, 'entry')) {
        if (has_base_address || has_entry_offset) {
            throw new Error('base_address and entry_offset cannot be defined with elf_header.entry');
        }
    }
    if (!has_base_address) {
        base_address = default_image_base_address;
    }
    if (!has_entry_offset) {
        entry_offset = 0;
    }
    const elf = new ELFWriter(base_address, code, rodata, rwdata, bss_length, entry_offset, elf_header);
    return elf.build();
}


/**
 * Build an ELF image and output it to a Readable stream
 * The resulting image contains the concatenation (with no padding) of:
 *   - code
 *   - rodata
 *   - rwdata
 *   - zeros (bss_length)
 *
 * @param {Buffer|Object} opts
 * @param {Buffer} opts.code code bytes
 * @param {Buffer} [opts.rodata] (optional) read-only data bytes
 * @param {Buffer} [opts.rwdata] (optional) read-write data bytes
 * @param {Number} [opts.bss_length] size of pre-zeroed read-write data
 * @param {Number} [opts.base_address] memory address for loading the elf image (default: 0x400000)
 * @param {Number} [opts.entry_offset] offset into the code buffer for the first instruction executed (default: 0)
 * @param {Object} [opts.elf_header] custom ELF header values
 * @returns {Readable} stream containing ELF image
 */
function createBuildStream(opts) {
    const stream = new Readable();
    let { code, rodata, rwdata, bss_length, base_address, entry_offset, elf_header } = Buffer.isBuffer(opts) ? {code: opts} : opts;

    const has_base_address = typeof(base_address) !== 'undefined'
    const has_entry_offset = typeof(entry_offset) !== 'undefined'

    // if the entrypoint is set in the custom elf_header, we don't allow base_address or entry_offset to be set
    if (elf_header && Object.prototype.hasOwnProperty.call(elf_header, 'entry')) {
        if (has_base_address || has_entry_offset) {
            throw new Error('base_address and entry_offset cannot be defined with elf_header.entry');
        }
    }
    if (!has_base_address) {
        base_address = default_image_base_address;
    }
    if (!has_entry_offset) {
        entry_offset = 0;
    }

    const elf = new ELFWriter(base_address, code, rodata, rwdata, bss_length, entry_offset, elf_header);
    process.nextTick(() => {
        elf.build(stream);
    });
    return stream;
}
  
module.exports = {
  build,
  createBuildStream,
  default_image_base_address,
};
