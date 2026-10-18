"""Independent host-side interpreter for the supported logical instruction set."""
from __future__ import annotations
from .ir import Instruction


def interpret(instructions: list[Instruction], initial: dict[str, int] | None = None) -> dict[str, int]:
    regs = [0] * 16
    if initial:
        for name, value in initial.items():
            n = int(name.lower().removeprefix("r"))
            if n == 0 or not 1 <= n <= 14: raise ValueError("initial register must be R1 through R14")
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255: raise ValueError("register values must be bytes")
            regs[n] = value
    for item in instructions:
        op = item.instruction
        if op == "nop": continue
        d = int(item.dest[1:])
        if op == "ldi": result = item.value
        elif op == "inc": result = (regs[int(item.src[1:])] + 1) & 255
        else:
            a, b = regs[int(item.lhs[1:])], regs[int(item.rhs[1:])]
            result = {"add": lambda: a + b, "sub": lambda: a - b, "and": lambda: a & b,
                      "nand": lambda: ~(a & b), "or": lambda: a | b, "xor": lambda: a ^ b,
                      "nor": lambda: ~(a | b), "xnor": lambda: ~(a ^ b)}[op]() & 255
        regs[d] = result
    return {f"r{i}": regs[i] for i in range(16)}
