"""Compiler and offline tools for the tested redstone CPU subset."""

from .assembly import emit_assembly, parse_assembly
from .encoding import decode_word, encode_instruction
from .frontend import CompilationResult, compile_source
from .interpreter import interpret
from .ir import Instruction, parse_ir_json
from .layout import RomImage, emit_binary, emit_flat_binary, layout_rom, placement_manifest

__all__ = [
    "CompilationResult", "Instruction", "RomImage", "compile_source",
    "decode_word", "emit_assembly", "emit_binary", "emit_flat_binary",
    "encode_instruction", "interpret", "layout_rom", "parse_assembly",
    "parse_ir_json", "placement_manifest",
]
