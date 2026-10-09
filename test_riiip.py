# run with: python3 -m unittest test_riiip

import contextlib
import io
import unittest

from riiip import *


class RiiipTest(unittest.TestCase):

    def setUp(self):
        self.out = io.StringIO()
        with contextlib.redirect_stdout(self.out):
            self.cpu = CPU()

    # types each line into riiip
    def do(self, *lines):
        with contextlib.redirect_stdout(self.out):
            for line in lines:
                self.cpu.do(line)

    def reg(self, name, form='s'):
        return self.cpu.read_reg(str_to_reg(name), form)


class TestArithmetic(RiiipTest):

    def test_r_types(self):
        self.do("li t0, -7", "li t1, 3")
        cases = {"add": -4, "sub": -10, "and": -7 & 3, "or": -7 | 3,
                 "xor": -7 ^ 3, "slt": 1, "sltu": 0, "sll": -56,
                 "srl": (2**32 - 7) >> 3, "sra": -1}
        for op, want in cases.items():
            self.do(op + " t2, t0, t1")
            self.assertEqual(self.reg("t2"), want, op)

    def test_i_types(self):
        self.do("li t0, -7")
        cases = {"addi t2, t0, 3": -4, "andi t2, t0, 3": 1, "ori t2, t0, 3": -5,
                 "xori t2, t0, -1": 6, "slti t2, t0, 0": 1, "sltiu t2, t0, -1": 1,
                 "slli t2, t0, 1": -14, "srli t2, t0, 28": 15, "srai t2, t0, 1": -4}
        for inst, want in cases.items():
            self.do(inst)
            self.assertEqual(self.reg("t2"), want, inst)

    def test_overflow_wraps(self):
        self.do("li t0, 0x7fffffff", "addi t0, t0, 1")
        self.assertEqual(self.reg("t0"), -2**31)
        self.assertIn("overflow", self.out.getvalue())

    def test_shift_uses_low_5_bits(self):
        self.do("li t0, 1", "li t1, 33", "sll t2, t0, t1")
        self.assertEqual(self.reg("t2"), 2)

    def test_x0_stays_zero(self):
        self.do("addi x0, x0, 5")
        self.assertEqual(self.reg("x0"), 0)

    def test_hex_immediate_sign_extends(self):
        self.do("addi t0, x0, 0xfff")
        self.assertEqual(self.reg("t0"), -1)

    def test_immediate_too_big(self):
        with self.assertRaises(AsmError):
            self.do("addi t0, x0, 2048")
        with self.assertRaises(AsmError):
            self.do("slli t0, t0, 32")

    def test_lui_auipc(self):
        self.do("lui t0, 0xfffff")
        self.assertEqual(self.reg("t0", 'u'), 0xfffff000)
        self.do("auipc t1, 1")
        self.assertEqual(self.reg("t1"), 4 + 0x1000)


class TestM(RiiipTest):

    def test_mul(self):
        self.do("li t0, -3", "li t1, 0x7fffffff")
        self.do("mul t2, t0, t1")
        self.assertEqual(self.reg("t2"), to_signed(-3 * 0x7fffffff))
        self.do("mulh t2, t0, t1")
        self.assertEqual(self.reg("t2"), (-3 * 0x7fffffff) >> 32)
        self.do("mulhu t2, t0, t1")
        self.assertEqual(self.reg("t2", 'u'), ((2**32 - 3) * 0x7fffffff) >> 32)
        self.do("mulhsu t2, t0, t1")
        self.assertEqual(self.reg("t2"), (-3 * 0x7fffffff) >> 32)

    def test_div_rounds_to_zero(self):
        self.do("li t0, -7", "li t1, 2", "div t2, t0, t1", "rem t3, t0, t1")
        self.assertEqual(self.reg("t2"), -3)
        self.assertEqual(self.reg("t3"), -1)
        self.do("divu t2, t0, t1", "remu t3, t0, t1")
        self.assertEqual(self.reg("t2", 'u'), (2**32 - 7) // 2)
        self.assertEqual(self.reg("t3", 'u'), 1)

    def test_div_edge_cases(self):
        self.do("li t0, 5", "div t2, t0, x0", "rem t3, t0, x0", "divu t4, t0, x0")
        self.assertEqual(self.reg("t2"), -1)
        self.assertEqual(self.reg("t3"), 5)
        self.assertEqual(self.reg("t4", 'u'), 2**32 - 1)
        self.do("li t0, 0x80000000", "li t1, -1", "div t2, t0, t1", "rem t3, t0, t1")
        self.assertEqual(self.reg("t2"), -2**31)
        self.assertEqual(self.reg("t3"), 0)


class TestMemory(RiiipTest):

    def test_little_endian(self):
        self.do("li t0, 0xbadcab1e", "sw t0, 0(x0)", "lbu t1, 0(x0)", "lhu t2, 2(x0)")
        self.assertEqual(self.reg("t1"), 0x1e)
        self.assertEqual(self.reg("t2"), 0xbadc)

    def test_sign_extension(self):
        self.do("li t0, -42", "sb t0, 8(x0)", "lb t1, 8(x0)", "lbu t2, 8(x0)",
                "sh t0, 12(x0)", "lh t3, 12(x0)")
        self.assertEqual(self.reg("t1"), -42)
        self.assertEqual(self.reg("t2"), 0xd6)
        self.assertEqual(self.reg("t3"), -42)

    def test_uninitialized_read_is_discarded(self):
        with self.assertRaises(ExecError):
            self.do("lw t0, 100(x0)")
        self.assertEqual(self.cpu.text_end, 0)
        self.assertEqual(self.cpu.PC, 0)

    def test_reset_mem_clears(self):
        self.do("sw x0, 0(x0)")
        with contextlib.redirect_stdout(self.out):
            self.cpu.reset_mem()
            self.assertEqual(Mem().data, {})


class TestControlFlow(RiiipTest):

    def test_backward_loop(self):
        self.do("li t0, 0", "li t1, 10", "loop: addi t0, t0, 1", "blt t0, t1, loop")
        self.assertEqual(self.reg("t0"), 10)
        self.assertEqual(self.cpu.PC, self.cpu.text_end)

    def test_forward_branch_skips(self):
        self.do("li t0, 1", "bnez t0, skip", "li t1, 99", "skip:", "li t2, 5")
        self.assertEqual(self.reg("t1"), 0)
        self.assertEqual(self.reg("t2"), 5)

    def test_branch_not_taken(self):
        self.do("bne x0, t0, done", "li t1, 1", "done:")
        self.do("li t0, 1", "bne t0, x0, 8", "li t1, 2", "li t2, 3")
        self.assertEqual(self.reg("t1"), 1)
        self.assertEqual(self.reg("t2"), 3)

    def test_all_branches(self):
        self.do("li t0, -1", "li t1, 1")
        cases = {"beq": False, "bne": True, "blt": True, "bge": False,
                 "bltu": False, "bgeu": True, "bgt": False, "ble": True,
                 "bgtu": True, "bleu": False}
        for i, (op, taken) in enumerate(cases.items()):
            label = "l" + str(i)
            self.do("li a0, 0", op + " t0, t1, " + label, "li a0, 1", label + ":")
            self.assertEqual(self.reg("a0"), 0 if taken else 1, op)

    def test_function_call(self):
        self.do("li a0, 7", "jal ra, double", "j end",
                "double:", "add a0, a0, a0", "ret", "end:", "addi a1, a0, 1")
        self.assertEqual(self.reg("a0"), 14)
        self.assertEqual(self.reg("a1"), 15)
        self.assertEqual(self.reg("ra"), 8)

    def test_call_defined_function(self):
        self.do("j main", "inc:", "addi a0, a0, 1", "ret",
                "main:", "call inc", "call inc", "jal inc")
        self.assertEqual(self.reg("a0"), 3)

    def test_jalr_same_register(self):
        self.do("li t0, 12", "jalr t0, 0(t0)", "li t1, 1", "li t2, 2")
        self.assertEqual(self.reg("t0"), 8)
        self.assertEqual(self.reg("t1"), 0)
        self.assertEqual(self.reg("t2"), 2)

    def test_la(self):
        self.do("nop", "here:", "nop", "la t0, here")
        self.assertEqual(self.reg("t0"), 4)
        # la isn't a jump, so it can't wait for a label defined later
        with self.assertRaises(ExecError):
            self.do("la t1, later")

    def test_misaligned_jump(self):
        with self.assertRaises(ExecError):
            self.do("li t0, 2", "jr t0")

    def test_duplicate_label(self):
        self.do("a:")
        with self.assertRaises(AsmError):
            self.do("a:")

    def test_infinite_loop_stops(self):
        self.do("spin: j spin")
        self.assertIn("infinite loop", self.out.getvalue())

    def test_recursive_factorial(self):
        self.do("li sp, 0x1000", "li a0, 5", "jal fact", "j done",
                "fact:",
                "addi sp, sp, -8", "sw ra, 4(sp)", "sw a0, 0(sp)",
                "li t0, 2", "blt a0, t0, base",
                "addi a0, a0, -1", "jal fact",
                "lw t1, 0(sp)", "mul a0, a0, t1", "j fact_ret",
                "base:", "li a0, 1",
                "fact_ret:", "lw ra, 4(sp)", "addi sp, sp, 8", "ret",
                "done:")
        self.assertEqual(self.reg("a0"), 120)
        self.assertEqual(self.reg("sp"), 0x1000)

    def test_ebreak_pauses(self):
        self.do("li t0, 0", "loop: addi t0, t0, 1", "ebreak", "j loop")
        self.assertEqual(self.reg("t0"), 2)
        with contextlib.redirect_stdout(self.out):
            self.cpu.run()
        self.assertEqual(self.reg("t0"), 3)


class TestSystem(RiiipTest):

    def test_print_and_exit(self):
        self.do("li a0, 1", "li a1, -5", "ecall",
                "li t0, 0x6968", "sw t0, 0(x0)", "sb x0, 2(x0)",
                "li a0, 4", "li a1, 0", "ecall",
                "li a0, 10", "ecall")
        self.assertIn("output: -5", self.out.getvalue())
        self.assertIn("output: hi", self.out.getvalue())
        self.assertTrue(self.cpu.halted)

    def test_li_32_bit(self):
        for v in ["0x12345678", "0x12345fff", "-1", "0x80000000", "4294967295", "2048"]:
            self.do("li t0, " + v)
            self.assertEqual(self.reg("t0", 'u'), parse_number(v)[0] & MASK, v)


if __name__ == "__main__":
    unittest.main()
