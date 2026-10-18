# Complete Minecraft CPU schematic

[`8bCPU-repaired-v1.schem`](8bCPU-repaired-v1.schem) is the **complete physical CPU**, copied byte-for-byte from the existing repaired lab build exported on 17 October 2026. It includes the ROM, registers, ALU, control/PC circuitry, clock, supports, and block-entity data. It is not the conceptual SVG or a ROM-only reconstruction. No wiring was invented or changed for this repository addition.

- Format: Sponge schematic v3 (`.schem`), Minecraft Java **1.21.7**, DataVersion 4438.
- Exporter: WorldEdit 7.3.16 on Fabric, lab snapshot `cpu_repaired_v1`.
- Size: **91 × 45 × 65** blocks (X × Y × Z), **32,543 non-air blocks**.
- Block entities: **1,433** (874 comparators, 496 barrels, 63 signs).
- SHA-256: `7485daa252e126b7ca49d26235e1d47318c78b09fdf3d986da77560b7daac5c9`.

## Import with WorldEdit

Use Java 1.21.7 with compatible WorldEdit; the source was exported using WorldEdit 7.3.16/Fabric. Copy the `.schem` into the instance's `config/worldedit/schematics/` directory (Bukkit installations use `plugins/WorldEdit/schematics/`). In a creative test world, choose an empty area large enough for the full selection. Enable creative flight, then run these commands as an operator to reproduce the original placement. Stay at the teleported position until pasting:

```text
/tick freeze
/tp @s 340 115 39
//schem load 8bCPU-repaired-v1.schem
//paste
/forceload add 256 -4 346 60
/tick step 300
```

The selection occupies **(256,72,-4)..(346,116,60)**, inclusive. Ordinary `//paste` includes air and clears the entire selection; use an empty test area. Do not rotate or flip the clipboard when using the supplied coordinate manifest. WorldEdit's [clipboard documentation](https://worldedit.enginehub.org/en/latest/usage/clipboard/) explains schematic loading and relative placement.

The saved offset is **(-84,-43,-43)**. At a different integer paste anchor `(X,Y,Z)`, the lower corner is `(X-84,Y-43,Z-43)` and the upper corner is `(X+6,Y+1,Z+21)`. Translate every supplied world coordinate, including force-load bounds and ROM cells, by `(X-340,Y-115,Z-39)`.

## Program and controls

The export contains the **original build ROM**, not the animation's `165 + 60` demo. Its nonzero words are address 1=`0x001B`, address 2=`0x012B`, and address 4=`0x2131`. The saved CPU was at PC=0 with run/manual controls off; it is not an all-zero register reset image.

To run the demo, program all 1,024 torch/air cells from [`docs/demo_physical_rom_manifest.json`](../docs/demo_physical_rom_manifest.json) after importing the CPU, while ticks are frozen and the run lever is off. The manifest only changes ROM cells; it cannot build the CPU by itself. Preserve each torch's west-facing orientation. This repository does not automate placement.

At the original placement, the run lever is at `(307,77,19)`, the step button at `(301,78,17)`, and the PC-reset lever at `(309,82,16)`. `/tick unfreeze` resumes redstone simulation; then use the run lever, or the step button with run off. The repaired clock has a 146-game-tick period. Stop it externally: there is no verified HALT. Keeping the bounding chunks force-loaded avoids partially unloaded circuitry.

## Validation and remaining limits

The file was opened with **nbtlib 2.0.4**. Every block-palette index was decoded, all 266,175 cells counted, and all block entities checked for unique, in-bounds positions and matching block types. The 1,024 ROM cells were also decoded. The file's SHA-256 matches the existing lab export exactly. Details and source provenance are in [`8bCPU-repaired-v1.verification.json`](8bCPU-repaired-v1.verification.json).

This verifies an actual importable physical schematic, not a fully working CPU. Earlier lab runs verified the repaired LDI/ADD demo and nine arithmetic/logic operations; **DEC and R15 operand reads remain faulty**, ROM **60/61 alias 56/57**, and conditional branching/overflow remain unverified. This repository addition performs file/structure validation, not a new in-game paste or an exhaustive hardware test.
