#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path


VERSION = "1.0 EXPERIMENTAL"

COMMAND_NAME = "ghidracleaner"
WINDOWS = os.name == "nt"

if WINDOWS:
    COMMAND_DIR = Path(
        os.environ.get(
            "LOCALAPPDATA",
            Path.home() / "AppData" / "Local",
        )
    ) / "GhidraCleaner"
    COMMAND_PATH = COMMAND_DIR / f"{COMMAND_NAME}.cmd"
else:
    COMMAND_DIR = Path.home() / ".local" / "bin"
    COMMAND_PATH = COMMAND_DIR / COMMAND_NAME

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}

TYPE_ALIASES = {
    "undefined1": "uint8_t",
    "undefined2": "uint16_t",
    "undefined4": "uint32_t",
    "undefined8": "uint64_t",
    "byte": "uint8_t",
    "sbyte": "int8_t",
    "word": "uint16_t",
    "sword": "int16_t",
    "dword": "uint32_t",
    "sdword": "int32_t",
    "qword": "uint64_t",
    "sqword": "int64_t",
    "uint": "unsigned int",
    "ushort": "unsigned short",
    "ulong": "unsigned long",
    "longlong": "long long",
    "ulonglong": "unsigned long long",
}

STANDARD_HEADERS = {
    "stdio.h": (
        r"\b(?:printf|fprintf|sprintf|snprintf|puts|fputs|"
        r"fopen|fclose|fread|fwrite|scanf|fscanf|getchar|"
        r"putchar|perror|FILE)\b"
    ),
    "stdlib.h": (
        r"\b(?:malloc|calloc|realloc|free|exit|abort|atoi|"
        r"atol|strtol|strtoul|rand|srand|qsort|abs)\b"
    ),
    "string.h": (
        r"\b(?:memcpy|memmove|memset|memcmp|strlen|strcmp|"
        r"strncmp|strcpy|strncpy|strchr|strstr|strtok)\b"
    ),
    "math.h": (
        r"\b(?:sqrt|pow|sin|cos|tan|log|log10|exp|fabs|"
        r"floor|ceil|fmod|atan|atan2)\b"
    ),
    "time.h": (
        r"\b(?:time|clock|difftime|mktime|localtime|"
        r"gmtime|strftime)\b"
    ),
    "unistd.h": (
        r"\b(?:read|write|close|access|getpid|sleep|"
        r"usleep|fork|execve)\b"
    ),
    "errno.h": r"\berrno\b",
    "ctype.h": (
        r"\b(?:isalpha|isdigit|isalnum|isspace|isupper|"
        r"islower|toupper|tolower)\b"
    ),
    "limits.h": r"\b(?:INT_MAX|INT_MIN|CHAR_BIT|LONG_MAX)\b",
    "inttypes.h": r"\b(?:PRI[diouxX]|SCN[diouxX])\w*\b",
}


def path_is_in(entries: list[str], directory: Path) -> bool:
    target = os.path.normcase(os.path.abspath(str(directory)))

    return any(
        os.path.normcase(os.path.abspath(entry.strip('"'))) == target
        for entry in entries
        if entry.strip()
    )


def add_windows_path() -> bool:
    try:
        import winreg

        key_path = r"Environment"

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            key_path,
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        ) as key:
            try:
                user_path, value_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                user_path = ""
                value_type = winreg.REG_EXPAND_SZ

            entries = user_path.split(";") if user_path else []

            if path_is_in(entries, COMMAND_DIR):
                return True

            entries.append(str(COMMAND_DIR))

            winreg.SetValueEx(
                key,
                "Path",
                0,
                value_type,
                ";".join(entries),
            )

        return True

    except (OSError, ImportError):
        return False


def install_command() -> bool:
    script_path = Path(__file__).resolve()

    try:
        COMMAND_DIR.mkdir(parents=True, exist_ok=True)

        if WINDOWS:
            launcher = (
                "@echo off\n"
                f'"{sys.executable}" "{script_path}" %*\n'
            )
        else:
            launcher = (
                "#!/bin/sh\n"
                f"exec {shlex.quote(sys.executable)} "
                f"{shlex.quote(str(script_path))} \"$@\"\n"
            )

        COMMAND_PATH.write_text(launcher, encoding="utf-8")

        if not WINDOWS:
            COMMAND_PATH.chmod(0o755)

    except OSError as error:
        print(f"Could not install shell command: {error}")
        return False

    print(f"Shell command installed: {COMMAND_PATH}")

    if WINDOWS:
        if add_windows_path():
            print("GhidraCleaner was added to your user PATH.")
            print("Restart your terminal to use the command.")
        else:
            print("Could not update your Windows PATH automatically.")
            print(f"Add this directory to your PATH: {COMMAND_DIR}")
    else:
        print(f"Use '{COMMAND_NAME}' from your terminal.")

        if not path_is_in(
            os.environ.get("PATH", "").split(os.pathsep),
            COMMAND_DIR,
        ):
            print(f"Add {COMMAND_DIR} to your PATH if necessary.")

    return True


def ask_to_install() -> None:
    if COMMAND_PATH.exists():
        return

    print("GhidraCleaner shell command is not installed.")

    try:
        answer = input("Would you like to install it? [Y/n] ").strip().lower()
    except EOFError:
        return

    if answer in ("", "y", "yes"):
        install_command()


def clean_banners(source: str) -> str:
    source = re.sub(
        r"/\*\s*={3,}[\s\S]*?={3,}\s*\*/",
        "",
        source,
    )

    source = re.sub(
        r"/\*\s*Function:.*?\*/",
        "",
        source,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return source


def normalize_main(source: str) -> str:
    return re.sub(
        r"\b(?:undefined8|uint64_t|int64_t)\s+main\s*\(",
        "int main(",
        source,
    )


def normalize_source(source: str) -> str:
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    source = clean_banners(source)

    for old, new in TYPE_ALIASES.items():
        source = re.sub(rf"\b{old}\b", new, source)

    source = re.sub(
        r"\b(?:undefined8|uint64_t|int64_t)\s+main\s*\(",
        "int main(",
        source,
    )

    source = re.sub(
        r'printf\s*\(\s*("%(?:[^"\\]|\\.)*")\s*,\s*'
        r'\((?:uint64_t|int64_t|unsigned long|long)\)\s*'
        r"([A-Za-z_]\w*)\s*\)",
        r"printf(\1, (int)\2)",
        source,
    )

    source = re.sub(r"[ \t]+\n", "\n", source)
    source = re.sub(r"\n{3,}", "\n\n", source)

    return source.strip() + "\n"


def build_compat_header(source: str) -> str:
    lines = [
        "#ifndef GHIDRACLEANER_COMPAT_H",
        "#define GHIDRACLEANER_COMPAT_H",
        "",
        "#include <stdint.h>",
        "#include <stdbool.h>",
        "#include <stddef.h>",
    ]

    for header, pattern in STANDARD_HEADERS.items():
        if re.search(pattern, source):
            lines.append(f"#include <{header}>")

    used_aliases = [
        (name, definition)
        for name, definition in TYPE_ALIASES.items()
        if re.search(rf"\b{re.escape(name)}\b", source)
    ]

    if used_aliases:
        lines.append("")

        for name, definition in used_aliases:
            lines.append(f"typedef {definition} {name};")

    if re.search(r"\bpthread_", source):
        lines.append("")
        lines.append("#include <pthread.h>")

    lines.extend(["", "#endif", ""])

    return "\n".join(lines)


def collect_sources(inputs: list[Path], output_root: Path | None) -> tuple[list[Path], Path]:
    sources = []
    project_root = None

    for item in inputs:
        if not item.exists():
            raise FileNotFoundError(f"Input not found: {item}")

        if item.is_file():
            if item.suffix.lower() != ".c":
                raise ValueError(f"Unsupported source file: {item}")

            sources.append(item.resolve())
            continue

        if not item.is_dir():
            raise ValueError(f"Invalid input: {item}")

        directory = item.resolve()
        project_root = directory

        for source in directory.rglob("*.c"):
            relative = source.relative_to(directory)

            if any(
                part in EXCLUDED_DIRS or part.startswith(".")
                for part in relative.parts
            ):
                continue

            if source.name.endswith("_clean.c"):
                continue

            if output_root and source.resolve().is_relative_to(output_root):
                continue

            sources.append(source.resolve())

    sources = sorted(set(sources))

    if not sources:
        raise ValueError("No C source files were found.")

    if project_root is None:
        common = os.path.commonpath([str(source.parent) for source in sources])
        project_root = Path(common)

    return sources, project_root


def prepare_output_paths(
    sources: list[Path],
    project_root: Path,
    output: Path | None,
    is_single_file: bool,
) -> tuple[Path, dict[Path, Path]]:
    if is_single_file:
        source = sources[0]

        output_file = (
            output
            if output is not None
            else source.with_name(source.stem + "_clean.c")
        )

        output_root = output_file.parent

        return output_root, {source: output_file}

    output_root = (
        output
        if output is not None
        else project_root.parent / f"{project_root.name}_clean"
    )

    mapping = {}

    for source in sources:
        relative = source.relative_to(project_root)
        mapping[source] = output_root / relative

    return output_root, mapping


def write_clean_sources(
    sources: list[Path],
    mapping: dict[Path, Path],
    output_root: Path,
) -> Path:
    combined_source = "\n".join(
        source.read_text(encoding="utf-8", errors="replace")
        for source in sources
    )

    header_path = output_root / "ghidracleaner_compat.h"
    header_path.parent.mkdir(parents=True, exist_ok=True)

    header = build_compat_header(combined_source)
    header_path.write_text(header, encoding="utf-8")

    for source, destination in mapping.items():
        original = source.read_text(encoding="utf-8", errors="replace")
        cleaned = normalize_source(original)

        relative_header = os.path.relpath(
            header_path,
            destination.parent,
        ).replace(os.sep, "/")

        include_line = f'#include "{relative_header}"'

        if include_line not in cleaned:
            cleaned = include_line + "\n\n" + cleaned

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(cleaned, encoding="utf-8")

        print(f"Cleaned source: {destination}")

    return header_path


def compile_project(
    sources: list[Path],
    mapping: dict[Path, Path],
    binary: Path,
    compiler: str,
    project_root: Path,
    include_dirs: list[Path],
    defines: list[str],
    libraries: list[str],
    compiler_flags: list[str],
    linker_flags: list[str],
) -> bool:
    if WINDOWS and not binary.suffix:
        binary = binary.with_suffix(".exe")

    binary.parent.mkdir(parents=True, exist_ok=True)

    command = [
        compiler,
        "-std=gnu11",
        "-Wall",
        "-Wextra",
        "-Wno-unused-parameter",
    ]

    command.extend(compiler_flags)

    include_paths = {
        project_root,
        *include_dirs,
        *(source.parent for source in sources),
        *(path.parent for path in mapping.values()),
    }

    for directory in sorted(include_paths):
        command.extend(["-I", str(directory)])

    for define in defines:
        command.append(f"-D{define}")

    cleaned_files = [str(mapping[source]) for source in sources]
    command.extend(cleaned_files)

    command.extend(["-o", str(binary)])

    if any(
        re.search(r"\bpthread_", source.read_text(encoding="utf-8", errors="replace"))
        for source in sources
    ):
        command.append("-pthread")

    if any(
        re.search(STANDARD_HEADERS["math.h"], source.read_text(encoding="utf-8", errors="replace"))
        for source in sources
    ) and "m" not in libraries:
        libraries.append("m")

    command.extend(linker_flags)

    for library in libraries:
        command.append(f"-l{library}")

    print("Compiling project...")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError:
        print(f"Compiler not found: {compiler}")
        return False

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        print("Compilation failed.")
        return False

    print(f"Executable created: {binary}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="GhidraCleaner",
        description="Clean, analyze and compile C code exported from Ghidra.",
    )

    parser.add_argument(
        "inputs",
        nargs="*",
        type=Path,
        help="C files or a directory containing a C project",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output C file or cleaned project directory",
    )

    parser.add_argument(
        "-b",
        "--binary",
        type=Path,
        help="Output executable path",
    )

    parser.add_argument(
        "--compiler",
        default="gcc",
        help="C compiler to use",
    )

    parser.add_argument(
        "-I",
        "--include-dir",
        action="append",
        type=Path,
        default=[],
        help="Additional include directory",
    )

    parser.add_argument(
        "-D",
        "--define",
        action="append",
        default=[],
        help="Define a preprocessor macro",
    )

    parser.add_argument(
        "-l",
        "--library",
        action="append",
        default=[],
        help="Link an additional library",
    )

    parser.add_argument(
        "--cflag",
        action="append",
        default=[],
        help="Additional compiler flag",
    )

    parser.add_argument(
        "--ldflag",
        action="append",
        default=[],
        help="Additional linker flag",
    )

    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="Only generate cleaned source files",
    )

    parser.add_argument(
        "-u",
        "--update",
        action="store_true",
        help="Install or update the shell command",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"GhidraCleaner {VERSION}",
    )

    args = parser.parse_args()

    if args.update:
        return 0 if install_command() else 1

    ask_to_install()

    if not args.inputs:
        parser.error("at least one input file or directory is required")

    inputs = [item.expanduser().resolve() for item in args.inputs]
    output = args.output.expanduser().resolve() if args.output else None

    try:
        is_single_file = len(inputs) == 1 and inputs[0].is_file()

        sources, project_root = collect_sources(inputs, output)

        output_root, mapping = prepare_output_paths(
            sources,
            project_root,
            output,
            is_single_file,
        )

        if any(
            source.resolve() == destination.resolve()
            for source, destination in mapping.items()
        ):
            print("An output file would overwrite an input file.")
            return 1

        print("GhidraCleaner is still EXPERIMENTAL!!")

        write_clean_sources(sources, mapping, output_root)

        print(f"Sources processed: {len(sources)}")

        if args.no_compile:
            return 0

        if args.binary:
            binary = args.binary.expanduser().resolve()
        elif is_single_file:
            binary = next(iter(mapping.values())).with_suffix("")
        else:
            binary = output_root / project_root.name

        include_dirs = [
            directory.expanduser().resolve()
            for directory in args.include_dir
        ]

        return 0 if compile_project(
            sources,
            mapping,
            binary,
            args.compiler,
            project_root,
            include_dirs,
            args.define,
            args.library.copy(),
            args.cflag,
            args.ldflag,
        ) else 1

    except (OSError, ValueError) as error:
        print(f"GhidraCleaner: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
