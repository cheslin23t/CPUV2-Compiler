"""Safe 64-word ROM layout and optional data-only physical manifest."""
from __future__ import annotations
from dataclasses import dataclass
from .encoding import encode_instruction
from .ir import Instruction


@dataclass(frozen=True)
class RomImage:
    words: tuple[int, ...]
    logical_addresses: tuple[int, ...]
    source_lines: tuple[int | None, ...]

    @property
    def final_useful_address(self) -> int | None:
        return self.logical_addresses[-1] if self.logical_addresses else None

    @property
    def following_padding_address(self) -> int | None:
        return None if self.final_useful_address is None else self.final_useful_address + 1


def layout_rom(instructions: list[Instruction], source_lines: list[int | None] | None = None) -> RomImage:
    if len(instructions) > 27:
        raise ValueError(f"program has {len(instructions)} logical instructions; maximum is 27")
    if source_lines is None: source_lines = [None] * len(instructions)
    if len(source_lines) != len(instructions): raise ValueError("source mapping length must match instruction count")
    words = [0] * 64
    addresses = []
    lines: list[int | None] = [None] * 64
    for idx, (item, line) in enumerate(zip(instructions, source_lines)):
        addr = 1 + idx * 2
        addresses.append(addr)
        words[addr] = encode_instruction(item)
        lines[addr] = line
    return RomImage(tuple(words), tuple(addresses), tuple(lines))


def emit_binary(rom: RomImage) -> str:
    return "\n".join(format(word, "016b") for word in rom.words)


def emit_flat_binary(rom: RomImage) -> str:
    return "".join(format(word, "016b") for word in rom.words)


def placement_manifest(rom: RomImage) -> list[dict[str, object]]:
    cells = []
    for address, word in enumerate(rom.words):
        x, y = 286 - 2 * (address % 16), 86 - 4 * (address // 16)
        for bit in range(16):
            cells.append({"address": address, "bit": bit, "x": x, "y": y,
                          "z": 30 + 2 * bit,
                          "block": "minecraft:redstone_wall_torch[facing=west]" if (word >> bit) & 1 else "minecraft:air"})
    return cells
