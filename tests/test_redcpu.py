import json
import unittest

from redcpu import (Instruction, compile_source, decode_word, emit_assembly,
                    emit_binary, emit_flat_binary, encode_instruction,
                    interpret, layout_rom, parse_assembly, parse_ir_json,
                    placement_manifest)


class EncodingTests(unittest.TestCase):
    def test_golden_vectors(self):
        vectors = [
            (Instruction("nop"), 0x0000, "0000000000000000"),
            (Instruction("ldi", "r1", 165), 0xA58B, "1010010110001011"),
            (Instruction("ldi", "r2", 60), 0x3C4B, "0011110001001011"),
            (Instruction("add", "r3", lhs="r2", rhs="r1"), 0x48C1, "0100100011000001"),
            (Instruction("add", "r3", lhs="r1", rhs="r2"), 0x84C1, "1000010011000001"),
            (Instruction("sub", "r3", lhs="r2", rhs="r1"), 0x48C2, "0100100011000010"),
            (Instruction("inc", "r3", src="r1"), 0x08C9, "0000100011001001"),
        ]
        for instruction, word, bits in vectors:
            with self.subTest(instruction=instruction):
                self.assertEqual(encode_instruction(instruction), word)
                self.assertEqual(format(word, "016b"), bits)

    def test_sub_operand_order_is_not_commuted(self):
        result = interpret([Instruction("ldi", "r2", 60), Instruction("ldi", "r1", 165),
                            Instruction("sub", "r3", lhs="r2", rhs="r1")])
        self.assertEqual(result["r3"], 151)

    def test_all_immediates_and_destination_registers(self):
        for dest in range(1, 15):
            for value in range(256):
                ins = Instruction("ldi", f"r{dest}", value)
                self.assertEqual(decode_word(encode_instruction(ins)), ins)

    def test_round_trip_all_supported_ops(self):
        items = [Instruction("nop"), Instruction("ldi", "r1", 0), Instruction("inc", "r2", src="r0")]
        items += [Instruction(op, "r3", lhs="r1", rhs="r2") for op in
                  ("add", "sub", "and", "nand", "or", "xor", "nor", "xnor")]
        for item in items: self.assertEqual(decode_word(encode_instruction(item)), item)

    def test_decode_noncanonical_and_unsupported(self):
        for word in (1, 0x000A, 0x000C, 0x000D, 0x1009):
            with self.subTest(word=word), self.assertRaises(ValueError): decode_word(word)

    def test_validation(self):
        for data in (
            {"instruction": "ldi", "dest": "r15", "value": 1},
            {"instruction": "ldi", "dest": "r1", "value": True},
            {"instruction": "ldi", "dest": "r1", "value": 256},
            {"instruction": "add", "dest": "r1", "lhs": "r1", "rhs": "r2"},
            {"instruction": "add", "dest": "r1", "lhs": "r2", "rhs": "r3", "extra": 0},
            {"instruction": "dec", "dest": "r1", "src": "r2"},
            {"instruction": "branch"},
        ):
            with self.subTest(data=data), self.assertRaises(ValueError): Instruction.from_dict(data)


class FormatsAndLayoutTests(unittest.TestCase):
    def test_json_assembly_json_round_trip(self):
        original = [Instruction("ldi", "r1", 165), Instruction("add", "r3", lhs="r2", rhs="r1")]
        text = emit_assembly(original)
        parsed = parse_assembly("# comment\n" + text.lower() + " # trailing\n")
        self.assertEqual([x.to_dict() for x in parsed], [x.to_dict() for x in original])
        self.assertEqual([x.to_dict() for x in parse_ir_json(json.dumps([x.to_dict() for x in parsed]))],
                         [x.to_dict() for x in original])

    def test_default_rom_and_tail(self):
        ins = [Instruction("ldi", "r1", 165), Instruction("ldi", "r2", 60),
               Instruction("add", "r3", lhs="r2", rhs="r1")]
        rom = layout_rom(ins)
        self.assertEqual(rom.words[:7], (0, 0xA58B, 0, 0x3C4B, 0, 0x48C1, 0))
        self.assertEqual(rom.words[56:], (0,) * 8)
        lines = emit_binary(rom).splitlines()
        self.assertEqual(len(lines), 64)
        self.assertTrue(all(len(x) == 16 and set(x) <= {"0", "1"} for x in lines))
        self.assertEqual(len(emit_flat_binary(rom)), 1024)
        self.assertTrue(set(emit_flat_binary(rom)) <= {"0", "1"})

    def test_physical_reference_program_values(self):
        ins = [Instruction("ldi", "r1", 165), Instruction("ldi", "r2", 60),
               Instruction("add", "r3", lhs="r2", rhs="r1")]
        state = interpret(ins)
        self.assertEqual((state["r1"], state["r2"], state["r3"]), (165, 60, 225))

    def test_capacity(self):
        self.assertEqual(len(layout_rom([Instruction("nop")] * 27).words), 64)
        with self.assertRaisesRegex(ValueError, "maximum is 27"):
            layout_rom([Instruction("nop")] * 28)

    def test_physical_mapping_ends_and_lsb(self):
        rom = layout_rom([Instruction("ldi", "r1", 1)])
        cells = placement_manifest(rom)
        self.assertEqual(len(cells), 64 * 16)
        first = cells[0]
        self.assertEqual((first["address"], first["bit"], first["x"], first["y"], first["z"]), (0, 0, 286, 86, 30))
        self.assertEqual(first["block"], "minecraft:air")
        address1_bit0 = cells[16]
        self.assertEqual(address1_bit0["block"], "minecraft:redstone_wall_torch[facing=west]")
        last = cells[-1]
        self.assertEqual((last["address"], last["bit"], last["x"], last["y"], last["z"]), (63, 15, 256, 74, 60))


class FrontendTests(unittest.TestCase):
    def test_example_outputs_and_distinct_reassignment(self):
        result = compile_source("""a = 10
x = a
x = x + 1
output(x)
""")
        self.assertEqual(interpret(result.instructions)[result.output_registers["x"]], 11)
        arithmetic = next(i for i in result.instructions if i.instruction == "add" and i.lhs != "r0")
        self.assertNotEqual(arithmetic.dest, arithmetic.lhs)

    def test_requested_example_and_wraparound(self):
        result = compile_source("""a = 165
b = 60
total = a + b
masked = total & 15
output(total)
output(masked)
""")
        regs = interpret(result.instructions)
        self.assertEqual(regs[result.output_registers["total"]], 225)
        self.assertEqual(regs[result.output_registers["masked"]], 1)
        wrap = compile_source("x = 255 + 1\ny = 0 - 1\nz = ~0\noutput(x)\noutput(y)\noutput(z)")
        got = interpret(wrap.instructions)
        self.assertEqual([got[wrap.output_registers[k]] for k in ("x", "y", "z")], [0, 255, 255])

    def test_lowered_and_decoded_rom_equivalent(self):
        result = compile_source("a = 7\nb = a ^ 3\nc = ~b\noutput(c)")
        logical = [decode_word(result.rom.words[a]) for a in result.rom.logical_addresses]
        self.assertEqual(interpret(logical), interpret(result.instructions))

    def test_invalid_syntax_and_literals(self):
        bad = ["x = 1\noutput(x)\nx = 2", "x = 256\noutput(x)", "x = -129\noutput(x)",
               "x = 1\nif x: y = 2\noutput(x)", "x = unknown\noutput(x)",
               "x = f(2)\noutput(x)", "x = [1]\noutput(x)", "x = 1 * 2\noutput(x)",
               "x = 1"]
        for source in bad:
            with self.subTest(source=source), self.assertRaises(ValueError): compile_source(source)
        with self.assertRaisesRegex(ValueError, "line 2"):
            compile_source("x = (1 +\n     2 * 3)\noutput(x)")

    def test_output_retained_during_temporary_reuse(self):
        result = compile_source("a = 99\nt = 1 + 2\nu = 3 + 4\noutput(a)")
        self.assertEqual(interpret(result.instructions)[result.output_registers["a"]], 99)

    def test_register_exhaustion_is_reported(self):
        expression = " + ".join(f"v{i}" for i in range(14))
        source = "\n".join(f"v{i} = {i}" for i in range(14)) + f"\nt = {expression}\noutput(t)"
        with self.assertRaisesRegex(ValueError, "register exhaustion"):
            compile_source(source)


if __name__ == "__main__": unittest.main()
