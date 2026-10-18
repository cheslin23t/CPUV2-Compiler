"""Strict parser and canonical formatter for the supported assembly."""
from __future__ import annotations

import re
from .ir import Instruction, BINARY


def _imm(token: str) -> int:
    try:
        if token.lower().startswith("0x"): value = int(token, 16)
        elif token.lower().startswith("0b"): value = int(token, 2)
        else: value = int(token, 10)
    except ValueError as exc:
        raise ValueError(f"invalid immediate {token!r}") from exc
    if not 0 <= value <= 255: raise ValueError("immediate must be from 0 through 255")
    return value


def parse_assembly(text: str) -> list[Instruction]:
    out = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line: continue
        match = re.fullmatch(r"([A-Za-z]+)(?:\s+(.*))?", line)
        if not match: raise ValueError(f"line {line_no}: invalid assembly syntax")
        op, argtext = match.group(1).lower(), match.group(2)
        args = [x.strip() for x in argtext.split(",")] if argtext is not None else []
        try:
            if op == "nop" and not args:
                item = Instruction("nop")
            elif op == "ldi" and len(args) == 2:
                item = Instruction("ldi", dest=args[0].lower(), value=_imm(args[1]))
            elif op == "inc" and len(args) == 2:
                item = Instruction("inc", dest=args[0].lower(), src=args[1].lower())
            elif op in BINARY and len(args) == 3:
                item = Instruction(op, dest=args[0].lower(), lhs=args[1].lower(), rhs=args[2].lower())
            elif op in ("dec", "br", "branch"):
                Instruction(op)  # produce the target-specific diagnostic
            else:
                raise ValueError(f"invalid operands for {op.upper()}")
        except ValueError as exc:
            raise ValueError(f"line {line_no}: {exc}") from exc
        out.append(item)
    return out


def emit_assembly(instructions: list[Instruction]) -> str:
    lines = []
    for item in instructions:
        op = item.instruction.upper()
        if op == "NOP": lines.append("NOP")
        elif op == "LDI": lines.append(f"LDI {item.dest.upper()}, {item.value}")
        elif op == "INC": lines.append(f"INC {item.dest.upper()}, {item.src.upper()}")
        else: lines.append(f"{op} {item.dest.upper()}, {item.lhs.upper()}, {item.rhs.upper()}")
    return "\n".join(lines)
