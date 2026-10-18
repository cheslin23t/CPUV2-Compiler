"""Restricted Python-AST frontend with conservative register allocation."""
from __future__ import annotations

import ast
from dataclasses import dataclass
from .ir import Instruction, reg_name
from .layout import RomImage, layout_rom


@dataclass
class CompilationResult:
    instructions: list[Instruction]
    output_registers: dict[str, str]
    source_lines: list[int]
    rom: RomImage

    @property
    def instruction_count(self) -> int: return len(self.instructions)
    @property
    def logical_instructions(self) -> list[Instruction]: return self.instructions
    @property
    def remaining_capacity(self) -> int: return 27 - self.instruction_count


class _Allocator:
    def __init__(self): self.used: set[int] = set()
    def alloc(self, line: int, exclude: set[int] | None = None) -> int:
        exclude = exclude or set()
        for n in range(1, 15):
            if n not in self.used and n not in exclude:
                self.used.add(n); return n
        raise ValueError(f"line {line}: register exhaustion (R1-R14 only; spilling is unsupported)")
    def free(self, n: int) -> None: self.used.discard(n)


def compile_source(source: str) -> CompilationResult:
    try: tree = ast.parse(source)
    except SyntaxError as exc: raise ValueError(f"line {exc.lineno}: {exc.msg}") from exc
    assigns: list[tuple[int, str, ast.expr]] = []
    outputs: list[tuple[int, str]] = []
    output_started = False
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign):
            if output_started: raise ValueError(f"line {stmt.lineno}: assignments must precede output declarations")
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                raise ValueError(f"line {stmt.lineno}: only simple variable assignments are supported")
            assigns.append((stmt.lineno, stmt.targets[0].id, stmt.value))
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call) and isinstance(stmt.value.func, ast.Name) and stmt.value.func.id == "output":
            output_started = True
            call = stmt.value
            if len(call.args) != 1 or call.keywords or not isinstance(call.args[0], ast.Name):
                raise ValueError(f"line {stmt.lineno}: output() requires exactly one variable name")
            outputs.append((stmt.lineno, call.args[0].id))
        else:
            raise ValueError(f"line {getattr(stmt, 'lineno', 1)}: unsupported statement {type(stmt).__name__}")
    if not outputs: raise ValueError("source must declare at least one output(variable)")
    names = {name for _, name, _ in assigns}
    seen_outputs = set()
    for line, name in outputs:
        if name not in names: raise ValueError(f"line {line}: output variable {name!r} is undefined")
        if name in seen_outputs: raise ValueError(f"line {line}: duplicate output({name}) declaration")
        seen_outputs.add(name)
    last_use: dict[str, int] = {}
    for idx, (_, _, expr) in enumerate(assigns):
        for node in ast.walk(expr):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load): last_use[node.id] = idx
    emitted: list[Instruction] = []
    source_lines: list[int] = []
    allocator = _Allocator()
    bindings: dict[str, int] = {}

    def emit(item: Instruction, line: int) -> None:
        emitted.append(item); source_lines.append(line)

    def expression(node: ast.expr, line: int) -> tuple[int, bool]:
        line = getattr(node, "lineno", line)
        if isinstance(node, ast.Constant) and type(node.value) is int:
            value = node.value
            if not (0 <= value <= 255 or -128 <= value <= -1):
                raise ValueError(f"line {line}: integer literal must be 0..255 or -128..-1")
            n = allocator.alloc(line)
            emit(Instruction("ldi", dest=reg_name(n), value=value & 255), line)
            return n, True
        if isinstance(node, ast.Name):
            if node.id not in bindings: raise ValueError(f"line {line}: variable {node.id!r} is undefined")
            src = bindings[node.id]
            n = allocator.alloc(line, {src})
            emit(Instruction("add", dest=reg_name(n), lhs=reg_name(src), rhs="r0"), line)
            return n, True
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Invert):
                src, owned = expression(node.operand, line)
                n = allocator.alloc(line, {src})
                emit(Instruction("nor", dest=reg_name(n), lhs=reg_name(src), rhs="r0"), line)
                if owned: allocator.free(src)
                return n, True
            if isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant) and type(node.operand.value) is int:
                value = -node.operand.value
                if not -128 <= value <= -1: raise ValueError(f"line {line}: integer literal must be 0..255 or -128..-1")
                n = allocator.alloc(line); emit(Instruction("ldi", dest=reg_name(n), value=value & 255), line)
                return n, True
            raise ValueError(f"line {line}: unsupported unary operator {type(node.op).__name__}")
        if isinstance(node, ast.BinOp):
            opcode = {ast.Add: "add", ast.Sub: "sub", ast.BitAnd: "and", ast.BitOr: "or", ast.BitXor: "xor"}.get(type(node.op))
            if opcode is None: raise ValueError(f"line {line}: unsupported binary operator {type(node.op).__name__}")
            left, left_owned = expression(node.left, line)
            right, right_owned = expression(node.right, line)
            dest = allocator.alloc(line, {left, right})
            emit(Instruction(opcode, dest=reg_name(dest), lhs=reg_name(left), rhs=reg_name(right)), line)
            if left_owned: allocator.free(left)
            if right_owned: allocator.free(right)
            return dest, True
        raise ValueError(f"line {line}: unsupported expression {type(node).__name__}")

    for idx, (line, target, expr) in enumerate(assigns):
        new_reg, _ = expression(expr, line)
        old = bindings.get(target)
        bindings[target] = new_reg
        if old is not None: allocator.free(old)
        for name, register in list(bindings.items()):
            if name not in seen_outputs and last_use.get(name, -1) <= idx:
                allocator.free(register); del bindings[name]
    missing = [name for _, name in outputs if name not in bindings]
    if missing: raise ValueError(f"output values are not live at end: {', '.join(missing)}")
    output_regs = {name: reg_name(bindings[name]) for _, name in outputs}
    rom = layout_rom(emitted, source_lines)
    return CompilationResult(emitted, output_regs, source_lines, rom)
