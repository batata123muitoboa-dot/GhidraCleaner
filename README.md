<div align="center">

# GhidraCleaner

**Clean and rebuild C source code decompiled with Ghidra.**

[![Version](https://img.shields.io/badge/version-1.0-orange)]()
[![Status](https://img.shields.io/badge/status-experimental-yellow)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Windows-lightgrey)]()

</div>

---

## About

GhidraCleaner is a Python tool designed to make working with C source code exported from [Ghidra](https://github.com/NationalSecurityAgency/ghidra) easier.

It applies basic cleanup and compatibility adjustments to decompiled C files, generates cleaned copies, and can automatically compile the resulting source code using GCC.

The project aims to reduce repetitive manual work when turning decompiled code into something that can be compiled and tested.

**GhidraCleaner is experimental.** It does not guarantee that every decompiled project can be cleaned, compiled, or reconstructed correctly.

## Features

- Cleans common patterns found in Ghidra decompiled output.
- Applies basic type and compatibility adjustments.
- Processes individual C files.
- Supports multiple C source files.
- Can process entire source directories.
- Generates cleaned copies without modifying original files.
- Generates a compatibility header.
- Automatically compiles processed sources.
- Supports additional include directories, macros, libraries, and compiler flags.
- Installs a global terminal command.
- Supports command installation and updates through `-u`.
- Works on Linux and Windows.

## Requirements

- Python 3.10 or newer.
- GCC or another compatible GCC-based compiler.
- Linux or Windows.

### Linux

On Arch Linux:

```bash
sudo pacman -S python gcc
```

On Debian or Ubuntu:

```bash
sudo apt install python3 gcc
```

### Windows

Install:

- [Python](https://www.python.org/downloads/)
- [MSYS2](https://www.msys2.org/)

Install GCC through the MSYS2 MinGW-w64 environment.

Make sure the compiler is available through your terminal's `PATH`.

## Installation

Clone the repository:

```bash
git clone https://github.com/batata123muitoboa-dot/GhidraCleaner.git
cd GhidraCleaner
```

Run the script:

```bash
python cleaner.py
```

GhidraCleaner can offer to install its global terminal command automatically.

### Linux command

The launcher is installed at:

```text
~/.local/bin/ghidracleaner
```

Make sure `~/.local/bin` is included in your `PATH`.

### Windows command

The launcher is installed at:

```text
%LOCALAPPDATA%\GhidraCleaner\ghidracleaner.cmd
```

The installer attempts to add its directory to the current user's `PATH`.

Restart your terminal after installation.

## Usage

### Process a single file

```bash
ghidracleaner program.c
```

### Process multiple files

```bash
ghidracleaner main.c utils.c functions.c
```

### Process an entire directory

```bash
ghidracleaner ./src
```

### Specify an output path

```bash
ghidracleaner program.c -o cleaned.c
```

### Specify the executable path

```bash
ghidracleaner program.c -b my_program
```

On Windows, GhidraCleaner automatically adds the `.exe` extension when necessary.

### Skip compilation

```bash
ghidracleaner program.c --no-compile
```

### Specify a compiler

```bash
ghidracleaner program.c --compiler gcc
```

### Add include directories

```bash
ghidracleaner program.c -I ./include
```

Multiple directories can be specified:

```bash
ghidracleaner program.c -I ./include -I ./headers
```

### Define preprocessor macros

```bash
ghidracleaner program.c -DDEBUG
```

### Link additional libraries

```bash
ghidracleaner program.c -lm
```

### Additional compiler flags

```bash
ghidracleaner program.c --cflag=-O2
```

### Additional linker flags

```bash
ghidracleaner program.c --ldflag=-static
```

### Check version

```bash
ghidracleaner --version
```

### Update the global command

Run this from the directory containing `cleaner.py`:

```bash
python cleaner.py -u
```

This recreates the launcher using the current script location.

## Output

For a single input file:

```text
program.c
program_clean.c
ghidracleaner_compat.h
program_clean
```

For a project directory, GhidraCleaner creates a separate output directory containing the cleaned source files and compatibility header.

The original source files are not modified.

## Example

Original decompiled code:

```c
#include <stdio.h>
#include <stdint.h>

int somar(int param_1,int param_2)
{
    return param_2 + param_1;
}

undefined8 main(void)
{
    uint uVar1;
    uVar1 = somar(0x14,0x16);
    printf("%d\n",(ulong)uVar1);
    return 0;
}
```

After processing:

```bash
./program_clean
```

Output:

```text
42
```

## Limitations

GhidraCleaner is not a decompiler and does not recover the original source code.

Decompilation can lose information, including:

- Original variable and function names.
- Type information.
- Structure definitions.
- Original comments.
- Project dependencies.

Some projects may require manual modifications before they can compile.

Other limitations include:

- Complex pointers and data structures.
- Missing headers and external libraries.
- Platform-specific APIs.
- Incorrect or incomplete type information.
- Compiler and linker incompatibilities.

A successful compilation does not guarantee that the resulting executable behaves exactly like the original program.

## Contributing

Contributions, bug reports, and suggestions are welcome.

If you encounter an issue, include:

- Your operating system.
- Python and GCC versions.
- The command you executed.
- The relevant error output.
- A small reproducible source example, if possible.

## License

GhidraCleaner is distributed under the Apache-2.0 License.

See [LICENSE](LICENSE) for details.
