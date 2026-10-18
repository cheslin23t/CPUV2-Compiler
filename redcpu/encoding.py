"""Exact bit-level instruction encoding for the tested CPU subset."""
from __future__ import annotations
from .ir import Instruction, BINARY, reg_name

OPCODE = {"nop": 0x0, "add": 0x1, "sub": 0x2, "and": 0x3, "nand": 0x4,
          "or": 0x5, "xor": 0x6, "nor": 0x7, "xnor": 0x8, "inc": 0x9, "ldi": 0xB}
BY_OPCODE = {v: k for k, v in OPCODE.items()}


def reverse4(n: int) -> int:
    return ((n & 1) << 3) | ((n & 2) << 1) | ((n & 4) >> 1) | ((n & 8) >> 3)


def encode_instruction(item: Instruction) -> int:
    op = item.instruction
    if op == "nop": return 0
    d = reverse4(int(item.dest[1:]))
    if op == "ldi": return (item.value << 8) | (d << 4) | 0xB
    if op == "inc": return (reverse4(int(item.src[1:])) << 8) | (d << 4) | 0x9
    lhs, rhs = int(item.lhs[1:]), int(item.rhs[1:])
    return (reverse4(lhs) << 12) | (reverse4(rhs) << 8) | (d << 4) | OPCODE[op]


def decode_word(word: int) -> Instruction:
    if isinstance(word, bool) or not isinstance(word, int) or not 0 <= word <= 0xFFFF:
        raise ValueError("machine word must be an integer from 0 through 65535")
    opcode = word & 0xF
    if opcode == 0:
        if word != 0: raise ValueError("noncanonical NOP: only 0x0000 is valid")
        return Instruction("nop")
    op = BY_OPCODE.get(opcode)
    if op is None:
        if opcode == 0xA: raise ValueError("DEC opcode 0xA is faulty and unsupported")
        if opcode == 0xC: raise ValueError("branch semantics are unverified")
        raise ValueError(f"unsupported opcode 0x{opcode:X}")
    dest = reverse4((word >> 4) & 0xF)
    if op == "ldi":
        return Instruction("ldi", dest=reg_name(dest), value=(word >> 8) & 0xFF)
    if op == "inc":
        if word & 0xF000: raise ValueError("noncanonical INC: physical A bits must be zero")
        src = reverse4((word >> 8) & 0xF)
        return Instruction("inc", dest=reg_name(dest), src=reg_name(src))
    lhs, rhs = reverse4((word >> 12) & 0xF), reverse4((word >> 8) & 0xF)
    return Instruction(op, dest=reg_name(dest), lhs=reg_name(lhs), rhs=reg_name(rhs))
