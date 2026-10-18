# redcpu

`redcpu` is an offline Python compiler for the verified straight-line subset of a custom 8-bit Minecraft redstone CPU. It uses only Python's standard library. It emits an instruction-object JSON IR, assembly, 64-line binary ROM images, flat 1024-bit ROM data, word arrays, listings, and optional coordinate manifests. It does not connect to Minecraft or issue block-placement commands.

## Run

From this directory:

```sh
python3 -m unittest discover -s tests -v
python3 -m redcpu compile examples/example.py --format json
python3 -m redcpu compile examples/example.py --format asm
python3 -m redcpu compile examples/example.py --format binary
python3 -m redcpu compile examples/example.py --format flat
python3 -m redcpu assemble examples/example.asm --format binary
python3 -m redcpu assemble examples/example.json --input-format json --format flat
```

Machine-readable output goes to stdout. Compilation summaries and errors go to stderr. `compile --metadata FILE` writes output-register assignments, instruction capacity, and final useful/padding addresses to a separate JSON file. A failed command exits nonzero.

## Input language

The frontend parses Python syntax with `ast`; it never executes source. Supported statements are assignments to simple names and `output(name)` declarations. Expressions contain byte integer literals, names, copies, parentheses, `+`, `-`, `&`, `|`, `^`, and unary `~`. Negative literals from -128 through -1 are accepted and encoded modulo 256. All computed values wrap to 8 bits. Output declarations are required and must follow every assignment. Each output value remains in its reported register through program completion.

Control flow, functions, imports, collections, calls other than `output`, multiplication/division, comparisons, Boolean operations, attributes, and memory access are rejected. An undefined name, unsupported syntax, or literal outside the allowed range is an error with its source line.

The canonical IR is a JSON list, for example:

```json
[
  {"instruction": "ldi", "dest": "r1", "value": 165},
  {"instruction": "ldi", "dest": "r2", "value": 60},
  {"instruction": "add", "dest": "r3", "lhs": "r2", "rhs": "r1"}
]
```

Only exact instruction schemas are accepted. Registers are lowercase in IR and uppercase in assembly. R1–R14 are allocatable; R0 reads as zero and cannot be a destination. R15 is rejected because its operand reads are faulty. Destinations must differ from all nonzero sources, including in user-supplied IR and assembly. There is no spilling. Frontend lowering copies values into distinct destinations and uses liveness to reuse registers after values die.

## Assembly and operands

Assembly is case-insensitive on input; canonical output uses uppercase mnemonics/registers and decimal immediates. Decimal, `0x` hexadecimal, `0b` binary, and `#` comments are supported. Binary operations use destination-first order: `SUB R4, R2, R1` means `(R2 - R1) & 255`. The JSON `lhs` maps to physical A and `rhs` to physical B. Each register nibble is bit-reversed independently in machine encoding; the whole word and LDI immediate byte are not reversed. LDI and INC have their own hardware layouts as implemented by `encode_instruction`.

Supported opcodes are NOP, ADD, SUB, AND, NAND, OR, XOR, NOR, XNOR, INC, and LDI. DEC is rejected because opcode `0xA` is faulty; branch opcode `0xC` has unverified semantics, and `0xD`–`0xF` are unspecified. Decoder input must be canonical, including exactly `0x0000` for NOP and zero unused bits for INC.

## ROM layout and execution limits

Each logical instruction is placed at addresses 1, 3, 5, …, with NOP at address 0 and one NOP after every instruction. The rest of the 64-word ROM is NOP, including addresses 56–63. The physical aliases at addresses 60 and 61 therefore cannot execute useful code. This leaves room for at most 27 logical instructions; overflow is an error. The binary file contains 64 lines of 16 bits, printed most-significant bit first. `flat` is exactly 1024 binary digits without separators, and `words` is a JSON array of 64 integers.

The compiler does not emit HALT or claim that a program stops. The six-bit PC eventually wraps and repeats the ROM. Stop the physical clock externally. `CompilationResult.rom.final_useful_address` and `following_padding_address` report where useful execution ends and its padding begins. The reference interpreter executes the logical instruction list once as a host-side testing convention, not as a hardware feature.

The native repaired clock advances every 146 game ticks (7.3 seconds at 20 TPS). The compiler does not model that timing. Known hardware defects also include incorrect DEC results, broken R15 operand reads, and ROM address aliases 60→56 and 61→57. Conditional branch behavior, overflow flags, and several potentially overlapping sequences are not certified. Passing software tests is not physical hardware validation.

## Minecraft CPU schematic

The complete physical CPU is included as [`schematics/8bCPU-repaired-v1.schem`](schematics/8bCPU-repaired-v1.schem), a byte-for-byte copy of the existing lab build (91×45×65 blocks; 32,543 non-air blocks). See the [placement/import instructions and known limits](schematics/README.md). The schematic, instructions, and parse-verification report are also inside [`CPU_Animation_Kit.zip`](CPU_Animation_Kit.zip). The export contains the original build ROM; the animation demo must be programmed separately.

The SVG illustrates behavior, and the manifest below programs ROM cells; neither substitutes for this full Minecraft schematic.

## Physical manifest

`placement_manifest(rom)` returns data only, one record for each address/bit cell. It maps address `a` and numeric word bit `i` to `x=286-2*(a%16)`, `y=86-4*(a//16)`, `z=30+2*i`; set bits use the tested west-facing redstone torch identifier and clear bits use air. Physical bit 0 corresponds to the rightmost character in a displayed 16-bit word.
