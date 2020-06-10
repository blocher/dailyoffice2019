## elf-tools

A NodeJS library for building and parsing ELF (Executable and Linker Format) binaries.

### Building an ELF image

There are two ways to output an ELF image:

#### build(opts)
Use `elf_tools.build(opts)` to create a buffer containing ELF bytes
```javascript
const fs = require('fs');
const elf_tools = require('elf-tools');

// create some raw "Hello world!" code for the ELF executable
// note that these instruction bytes are for the Linux OS on Intel/AMD x64 platform
const code = Buffer.from(
 '488d3523000000'    // lea    rsi,[rip+0x23]
+'48c7c20d000000'    // mov    rdx,0xd
+'48c7c701000000'    // mov    rdi,0x1
+'48c7c001000000'    // mov    rax,0x1
+'0f05'              // syscall
+'4831ff'            // xor    rdi,rdi
+'48c7c03c000000'    // mov    rax,0x3c
+'0f05'              // syscall
+'48656c6c6f20776f726c64210a'	// "Hello world!\n"
, 'hex');

// build the ELF executable with the code
const image = elf_tools.build({
    code,
});

// save the ELF image as a binary executable file
fs.writeFileSync('./a.out', image, { mode: 0o755 });

```

#### createBuildStream(opts)
Use `elf_tools.createBuildStream(opts)` and pipe the result to another [Writable](https://nodejs.org/api/stream.html#stream_writable_streams) stream
```javascript
const fs = require('fs');
const elf_tools = require('elf-tools');

// create some raw "Hello world!" code for the ELF executable
// note that these instruction bytes are for the Linux OS on Intel/AMD x64 platform
const code = Buffer.from(
 '488d3523000000'    // lea    rsi,[rip+0x23]
+'48c7c20d000000'    // mov    rdx,0xd
+'48c7c701000000'    // mov    rdi,0x1
+'48c7c001000000'    // mov    rax,0x1
+'0f05'              // syscall
+'4831ff'            // xor    rdi,rdi
+'48c7c03c000000'    // mov    rax,0x3c
+'0f05'              // syscall
+'48656c6c6f20776f726c64210a'	// "Hello world!\n"
, 'hex');

// create a ELF stream to output the ELF image bytes
const elf_stream = elf_tools.createBuildStream({
    code,
});

// create a writable file stream
const file_stream = fs.createWriteStream('./a.out', { mode: 0o755 });

// pipe the ELF bytes to the file
elf_stream.pipe(file_stream);

```
Once the file is saved, run it from a terminal:
```
$ ./a.out
Hello world!
```

### Parsing ELF files

To parse an ELF file:
```javascript
const fs = require('fs');
const elf_tools = require('elf-tools');

// read the file into a buffer
const elf_bytes = fs.readFileSync('./a.out');

// parse the data
const elf = elf_tools.parse(elf_bytes);

// elf is an object containing the parsed ELF-header, program headers (if any) and sections

```

### Documentation

### `build(opts)`

Build an ELF image
- **opts**: Object containing code and data to place inside the ELF image
  - **code**: *Buffer*. Raw executable code bytes. The ELF builder places this data in a *.text* section. All calls to `build()` must include a code buffer. The caller must ensure the code bytes represent valid instructions for the target machine. **Important**: the code must be position-independant with no relocations.
  - **rodata**: *Buffer* (optional). Raw read-only data bytes. The ELF builder places any read-only data in the *.text* section immediately following the code buffer. If this data needs aligning to a particular byte boundary, the code buffer should be padded accordingly.
  - **rwdata**: *Buffer* (optional). Raw read/write data bytes. The ELF builder places any writable data in a *.data* section following the code and read-only data
  - **bss_length**: *integer* (optional). Length of uninitialised (writable) data bytes. The ELF builder locates this data after the rwdata buffer. Although the data is "uninitialized" (because it takes up no space in the ELF image), when the image is run, this section is always zero-filled.
  - **base_address**: *integer* (optional). Memory address for loading the elf image (default: 0x400000)
  - **entry_offset**: *integer* (optional). Byte offset into the code buffer for the first instruction (default: 0)
  - **elf_header**: *Object* (optional). Custom ELF header values. See the notes below for the list of fields supported in this object.
  
- returns **Buffer** containing the complete ELF image

#### Customising the ELF header

By default, the constructed ELF header contains values based upon your current executing platform. You can override some of these values by passing an **elf_header** object to `build()`. The customisable values include:

- **elfsig**: *string* ELF signature
- **class**: *string* `'32'` or `'64'` (note that this value is passed as a string, not an integer)
- **endian**: *string* `'lsb'` or `'msb'`
- **osabi**: *string* Any of the allowed values in `lib/constants.js`
- **abiversion**: *string* Any of the allowed values in `lib/constants.js`
- **type**: *string* Any of the allowed values in `lib/constants.js`
- **machine**: *string* Any of the allowed values in `lib/constants.js`
- **version**: *integer* Any of the allowed values in `lib/constants.js`
- **entry**: *integer* ELF entrypoint. *Note*: this value cannot be set if either `base_address` or `entry_offset` are set.
- **flags**: *integer*

The default values for these fields can be found in `lib/elf_header.js`. Any customised values passed to `build()` are **not validated** - make sure you set correct values or the resulting ELF image is likely to be invalid.

#### Example

This example uses all 4 fields (code, r/o data, r/w data, bss data) to build an executable which:
- writes out a prompt (r/o data)
- then reads user-inputted text into a buffer (r/w data)
- then reverses the text using scratch space (bss data)
- finally writes out the reversed text and exits the program

```javascript
const fs = require('fs');
const elf_tools = require('elf-tools');

const opts = {
    // note that these instruction bytes are for the Linux OS on Intel/AMD x64 platform
    // you can find the source to this program at https://github.com/adelphes/elf-tools/blob/master/test/programs/reverse/reverse.s
    code: Buffer.from(`
488d3579 00000048 c7c21c00 0000e85c 00000048 8d358600 000048c7 c2000100
00e83e00 000048ff c84889c2 488d3d6d 01000048 01c78a0e 880f48ff cf48ffc6
4883e801 75f04889 fe48ffc6 c604160a 48ffc2e8 17000000 4831ff48 c7c03c00
00000f05 bf010000 004831c0 0f05c348 c7c70100 000048c7 c0010000 000f05c3
    `.replace(/\s+/g,''), 'hex'),
    
    // add the prompt as read-only bytes - the extra null bytes pad the section to an 8-byte alignment.
    rodata: Buffer.from('Enter some text to reverse: \0\0\0\0', 'ascii'),

    // pre-allocate 256 zero bytes in the program to store the user-input
    rwdata: Buffer.alloc(256),

    // reserve another 256 bytes of memory for us to reverse the text
    bss_length: 256,
}

// create a ELF stream to output the ELF image bytes
const elf_stream = elf_tools.createStream(opts);

// create a writable file stream
const file_stream = fs.createWriteStream('./reverse', { mode: 0o755 });

// pipe the ELF bytes to the file
elf_stream.pipe(file_stream);

```
Once the file is saved, run it
```
$ ./reverse
Enter some text to reverse: abcdef
fedcba
```
