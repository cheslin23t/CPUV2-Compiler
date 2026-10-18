"""Command-line interface. Machine-readable formats go to stdout."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from .assembly import emit_assembly, parse_assembly
from .encoding import decode_word
from .frontend import compile_source
from .interpreter import interpret
from .ir import parse_ir_json
from .layout import emit_binary, emit_flat_binary, layout_rom


def _listing(rom):
    lines = ["address hex  binary            assembly  source-line"]
    for addr, word in enumerate(rom.words):
        try: asm = emit_assembly([decode_word(word)])
        except ValueError: asm = "<invalid>"
        source = "-" if rom.source_lines[addr] is None else str(rom.source_lines[addr])
        lines.append(f"{addr:02d}      {word:04X} {word:016b}  {asm}  {source}")
    return "\n".join(lines)


def _format(fmt, instructions, rom):
    if fmt == "json": return json.dumps([i.to_dict() for i in instructions], indent=2)
    if fmt == "asm": return emit_assembly(instructions)
    if fmt == "binary": return emit_binary(rom)
    if fmt == "flat": return emit_flat_binary(rom)
    if fmt == "words": return json.dumps(list(rom.words))
    if fmt == "listing": return _listing(rom)
    raise ValueError(f"unknown format {fmt}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="redcpu")
    sub = parser.add_subparsers(dest="command", required=True)
    cp = sub.add_parser("compile", help="compile restricted Python source")
    cp.add_argument("source", type=Path)
    cp.add_argument("--format", choices=("json", "asm", "binary", "flat", "words", "listing"), default="asm")
    cp.add_argument("--metadata", type=Path)
    ap = sub.add_parser("assemble", help="assemble JSON IR or assembly")
    ap.add_argument("source", type=Path)
    ap.add_argument("--input-format", choices=("asm", "json"), default="asm")
    ap.add_argument("--format", choices=("json", "asm", "binary", "flat", "words", "listing"), default="binary")
    args = parser.parse_args(argv)
    try:
        text = args.source.read_text(encoding="utf-8")
        if args.command == "compile":
            result = compile_source(text)
            instructions, rom = result.instructions, result.rom
            if args.metadata:
                args.metadata.write_text(json.dumps({"output_registers": result.output_registers,
                    "source_lines": result.source_lines, "instruction_count": result.instruction_count,
                    "remaining_capacity": result.remaining_capacity,
                    "final_useful_address": rom.final_useful_address,
                    "following_padding_address": rom.following_padding_address}, indent=2) + "\n", encoding="utf-8")
            print(f"outputs: {result.output_registers}; {result.instruction_count}/27 logical instructions; final useful address {rom.final_useful_address}, padding {rom.following_padding_address}", file=sys.stderr)
        elif args.input_format == "json":
            instructions = parse_ir_json(text); rom = layout_rom(instructions)
        else:
            instructions = parse_assembly(text); rom = layout_rom(instructions)
        result = _format(args.format, instructions, rom)
        sys.stdout.write(result)
        if args.format != "flat" or args.command == "compile": sys.stdout.write("\n")
        return 0
    except (OSError, ValueError) as exc:
        print(f"redcpu: error: {exc}", file=sys.stderr)
        return 2
