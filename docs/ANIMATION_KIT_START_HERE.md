# CPU animation kit — start here

This kit is for a separate Codex chat/environment. Attach or open the kit and ask it to read `CPU_ANIMATION_HANDOFF.md` and `cpu_animation_data.json` first. Those contain the verified CPU facts, exact example, ROM timing/layout, and animation constraints.

## Files

- `CPU_ANIMATION_HANDOFF.md`: copy-ready prompt and complete explanatory brief.
- `cpu_animation_data.json`: machine-readable facts and demo checkpoints.
- `redcpu_behavioral_schematic.svg`: downloadable conceptual schematic; it is not a physical wiring plan.
- `demo_logical_ir.json`, `demo_logic.asm`, `demo_rom.bin`, `demo_rom_words.json`: the physically tested three-instruction demo and its padded 64-word ROM.
- `redcpu/`, `tests/`, `examples/`, `README.md`: compiler source, tests, and a separate frontend example.

## In another environment

Extract this kit, open its root, then run:

```sh
python3 -m unittest discover -s tests -v
python3 -m redcpu assemble demo_logic.asm --format listing
```

Python's standard library is sufficient. The files are offline artifacts; no Minecraft server, web access, RCON, or block placement is needed.
