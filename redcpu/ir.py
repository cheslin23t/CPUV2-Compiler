"""Canonical instruction representation and strict JSON validation."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


OPS = {"nop", "ldi", "add", "sub", "and", "nand", "or", "xor", "nor", "xnor", "inc"}
BINARY = {"add", "sub", "and", "nand", "or", "xor", "nor", "xnor"}
_SCHEMAS = {
    "nop": {"instruction"}, "ldi": {"instruction", "dest", "value"},
    "inc": {"instruction", "dest", "src"},
    **{op: {"instruction", "dest", "lhs", "rhs"} for op in BINARY},
}


def register_number(value: Any) -> int:
    if not isinstance(value, str) or not re.fullmatch(r"[rR](?:[0-9]|1[0-5])", value):
        raise ValueError(f"invalid register {value!r}; expected R0 through R14")
    number = int(value[1:])
    if number == 15:
        raise ValueError("R15 is unsupported because its operand reads are faulty")
    return number


def reg_name(number: int) -> str:
    return f"r{number}"


@dataclass(frozen=True)
class Instruction:
    instruction: str
    dest: str | None = None
    value: int | None = None
    lhs: str | None = None
    rhs: str | None = None
    src: str | None = None

    def __post_init__(self) -> None:
        op = self.instruction.lower() if isinstance(self.instruction, str) else self.instruction
        object.__setattr__(self, "instruction", op)
        for key in ("dest", "lhs", "rhs", "src"):
            value = getattr(self, key)
            if isinstance(value, str): object.__setattr__(self, key, value.lower())
        if op not in OPS:
            if op == "dec":
                raise ValueError("DEC is unsupported because opcode 0xA is faulty")
            if op in ("br", "branch"):
                raise ValueError("branch semantics are unverified")
            raise ValueError(f"unknown or unsupported instruction {op!r}")
        data = self.to_dict()
        expected = _SCHEMAS[op]
        if set(data) != expected:
            raise ValueError(f"{op.upper()} requires exactly fields: {', '.join(sorted(expected - {'instruction'}))}")
        if op == "nop":
            return
        d = register_number(self.dest)
        if d == 0:
            raise ValueError("R0 is read-only and cannot be a destination")
        sources = []
        if op == "ldi":
            if isinstance(self.value, bool) or not isinstance(self.value, int) or not 0 <= self.value <= 255:
                raise ValueError("LDI value must be an integer from 0 through 255")
        elif op == "inc":
            sources.append(register_number(self.src))
        else:
            sources.extend((register_number(self.lhs), register_number(self.rhs)))
        if d in sources:
            raise ValueError("destination register must differ from every source register")

    def to_dict(self) -> dict[str, Any]:
        vals = {"instruction": self.instruction}
        for key in ("dest", "value", "lhs", "rhs", "src"):
            value = getattr(self, key)
            if value is not None:
                vals[key] = value
        return vals

    @classmethod
    def from_dict(cls, data: Any) -> "Instruction":
        if not isinstance(data, dict):
            raise ValueError("each instruction must be a JSON object")
        op = data.get("instruction")
        if not isinstance(op, str):
            raise ValueError("instruction field must be a string")
        op = op.lower()
        expected = _SCHEMAS.get(op)
        if expected is None:
            if op == "dec":
                raise ValueError("DEC is unsupported because opcode 0xA is faulty")
            if op in ("br", "branch"):
                raise ValueError("branch semantics are unverified")
            raise ValueError(f"unknown or unsupported instruction {op!r}")
        if set(data) != expected:
            missing, extra = expected - set(data), set(data) - expected
            details = []
            if missing: details.append("missing " + ", ".join(sorted(missing)))
            if extra: details.append("unknown " + ", ".join(sorted(extra)))
            raise ValueError(f"invalid {op.upper()} fields: {'; '.join(details)}")
        return cls(**data)


def parse_ir_json(text: str) -> list[Instruction]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON line {exc.lineno}: {exc.msg}") from exc
    if not isinstance(data, list):
        raise ValueError("IR JSON must be a list of instruction objects")
    return [Instruction.from_dict(item) for item in data]
