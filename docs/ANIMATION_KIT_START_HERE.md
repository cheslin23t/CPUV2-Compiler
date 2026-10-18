# CPU animation kit — start here

This kit is for a separate Codex chat/environment. Attach or open the kit and ask it to read `docs/CPU_ANIMATION_HANDOFF.md` and `docs/cpu_animation_data.json` first. Those contain the verified CPU facts, exact example, ROM timing/layout, and animation constraints.

## Files

- `docs/CPU_ANIMATION_HANDOFF.md`: copy-ready prompt and complete explanatory brief.
- `docs/cpu_animation_data.json`: machine-readable facts and demo checkpoints.
- `docs/redcpu_behavioral_schematic.svg`: downloadable conceptual schematic; it is not a physical wiring plan.
- `docs/demo_logical_ir.json`, `docs/demo_logic.asm`, `docs/demo_rom_binary.txt`, `docs/demo_rom_words.json`: the physically tested three-instruction demo and its padded 64-word ROM.
- `schematics/8bCPU-repaired-v1.schem`: complete physical Minecraft CPU from the existing repaired lab build; not ROM-only.
- `schematics/README.md`, `schematics/8bCPU-repaired-v1.verification.json`: placement/import instructions, provenance, parser checks, and remaining hardware faults. The schematic ships the original ROM, not the demo program.
- `redcpu/`, `tests/`, `examples/`, `README.md`: compiler source, tests, and a separate frontend example.

## In another environment

Extract this kit, open its root, then run:

```sh
python3 -m unittest discover -s tests -v
python3 -m redcpu assemble docs/demo_logic.asm --format listing
```

Python's standard library is sufficient. The files are offline artifacts; no Minecraft server, web access, RCON, or block placement is needed.
