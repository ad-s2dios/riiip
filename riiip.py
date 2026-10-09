######################
# author:  ad-s2dios #
# version: 1.2       #
######################

import re

####################################################################
#                                                                  #
#   Constants                                                      #
#                                                                  #
####################################################################

XLEN = 32
MASK = (1 << XLEN) - 1

REG_LUT = {"zero": 0, "ra": 1, "sp": 2, "gp": 3, "tp": 4,
            "t0": 5, "t1": 6, "t2": 7,
            "s0": 8, "fp": 8, "s1": 9,
            "a0": 10, "a1": 11, "a2": 12, "a3": 13,
            "a4": 14, "a5": 15, "a6": 16, "a7": 17,
            "s2": 18, "s3": 19, "s4": 20, "s5": 21, "s6": 22,
            "s7": 23, "s8": 24, "s9": 25, "s10": 26, "s11": 27,
            "t3": 28, "t4": 29, "t5": 30, "t6": 31}

# ABI name of each register, indexed by register number
REG_NAMES = ["zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2",
            "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5",
            "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7",
            "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6"]

MEM_SIZE_LUT = {'b': 1, 'h': 2, 'w': 4}
MEM_SIZE_NAME = {'b': "byte", 'h': "half", 'w': "word"}

# sbrk (ecall 9) hands out memory starting here, like venus does
HEAP_BASE = 0x10008000

# how many instructions one 'run' may execute before riiip assumes
# the program is stuck in an infinite loop
MAX_STEPS = 10000

# after this many instructions in one run, riiip stops explaining
# every instruction and prints a summary at the end instead
QUIET_AFTER = 30

# RV32I register-register arithmetic, plus the M extension
R_TYPES = {"add", "and", "or", "sll", "slt", "sltu",
            "sra", "srl", "sub", "xor",
            "mul", "mulh", "mulhsu", "mulhu", "div", "divu", "rem", "remu"}

I_ARITH = {"addi", "andi", "ori", "slti", "sltiu", "xori"}

I_SHIFT = {"slli", "srai", "srli"}

LOADS = {"lb", "lbu", "lh", "lhu", "lw"}

S_TYPES = {"sb", "sh", "sw"}

U_TYPES = {"auipc", "lui"}

B_TYPES = {"beq", "bge", "bgeu", "blt", "bltu", "bne"}

J_TYPES = {"jal", "jalr"}

SYSTEM = {"ebreak", "ecall", "fence"}

# pseudo instructions that are a simple rewrite into one real one
# name: (# operands, usage, expansion)
PSEUDO_LUT = {
    "nop":  (0, "",                "addi x0, x0, 0"),
    "mv":   (2, "rd, rs",          "addi {0}, {1}, 0"),
    "not":  (2, "rd, rs",          "xori {0}, {1}, -1"),
    "neg":  (2, "rd, rs",          "sub {0}, x0, {1}"),
    "seqz": (2, "rd, rs",          "sltiu {0}, {1}, 1"),
    "snez": (2, "rd, rs",          "sltu {0}, x0, {1}"),
    "sltz": (2, "rd, rs",          "slt {0}, {1}, x0"),
    "sgtz": (2, "rd, rs",          "slt {0}, x0, {1}"),
    "beqz": (2, "rs, label",       "beq {0}, x0, {1}"),
    "bnez": (2, "rs, label",       "bne {0}, x0, {1}"),
    "blez": (2, "rs, label",       "bge x0, {0}, {1}"),
    "bgez": (2, "rs, label",       "bge {0}, x0, {1}"),
    "bltz": (2, "rs, label",       "blt {0}, x0, {1}"),
    "bgtz": (2, "rs, label",       "blt x0, {0}, {1}"),
    "bgt":  (3, "rs, rt, label",   "blt {1}, {0}, {2}"),
    "ble":  (3, "rs, rt, label",   "bge {1}, {0}, {2}"),
    "bgtu": (3, "rs, rt, label",   "bltu {1}, {0}, {2}"),
    "bleu": (3, "rs, rt, label",   "bgeu {1}, {0}, {2}"),
    "j":    (1, "label",           "jal x0, {0}"),
    "jr":   (1, "rs",              "jalr x0, 0({0})"),
    "ret":  (0, "",                "jalr x0, 0(ra)"),
    # real assemblers emit auipc + jalr and let the linker relax them
    # into a single jal when the target is close, which it always is here
    "call": (1, "label",           "jal ra, {0}"),
    "tail": (1, "label",           "jal x0, {0}"),
}

PSEUDO = set(PSEUDO_LUT) | {"la", "li"}

LABEL_RE = re.compile(r'^[a-z_][a-z0-9_.]*$')


####################################################################
#                                                                  #
#   Errors                                                         #
#                                                                  #
####################################################################

# base class: the message explains to the user what went wrong
class RiiipError(Exception):
    pass

# the line typed is not a valid instruction
class AsmError(RiiipError):
    pass

# the instruction is valid but couldn't be executed
class ExecError(RiiipError):
    pass


####################################################################
#                                                                  #
#   Helper functions                                               #
#                                                                  #
####################################################################

# interprets the lowest `bits` bits of v as a two's complement number
def to_signed(v, bits=XLEN):
    v &= (1 << bits) - 1
    if v >> (bits - 1):
        return v - (1 << bits)
    return v


# formats v as a zero padded hex string of `bits` bits
def to_hex(v, bits=XLEN):
    return "0x" + format(v & ((1 << bits) - 1), "0" + str((bits + 3) // 4) + "x")


# checks if register str is legit
def legit_reg_str(reg):
    if len(reg) > 1 and reg[0] == 'x' and reg[1:].isdigit():
        return 0 <= int(reg[1:]) < 32

    return reg in REG_LUT


# get register number from string
def str_to_reg(reg):
    if reg[0] == 'x':
        return int(reg[1:])
    else:
        return REG_LUT[reg]


# parses a decimal, hex or binary number
# returns (value, is_bit_pattern) where hex / binary count as bit patterns
def parse_number(s):
    neg = s.startswith('-')
    body = s[1:] if neg else s

    try:
        if body[:2] == "0x":
            v = int(body[2:], 16)
        elif body[:2] == "0b":
            v = int(body[2:], 2)
        elif body.isdigit():
            v = int(body)
        else:
            raise ValueError
    except ValueError:
        raise AsmError("'" + s + "' is not a number. use one of:\n"
                       "  bin '0b101', hex '0xabc', int '-1'")

    return (-v if neg else v), (body[:2] in ("0x", "0b") and not neg)


def is_number(s):
    try:
        parse_number(s)
        return True
    except AsmError:
        return False


# generate immediate that fits in `bits` bits
# signed immediates accept decimals in range, or a hex / binary bit
#   pattern of `bits` bits which is then sign extended (eg 0xfff is -1)
# raises AsmError if it doesn't fit
def imm_gen(x, bits, signed=True):
    v, is_pattern = parse_number(x)

    if not signed:
        if 0 <= v < (1 << bits):
            return v
        raise AsmError("immediate should be between 0 and " + str((1 << bits) - 1)
                       + " (" + str(bits) + " bits)\n  but " + x + " isn't")

    lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1

    if is_pattern and hi < v < (1 << bits):
        print("Note:", x, "has its top bit set, so as a", bits,
              "bit immediate it is sign extended to", v - (1 << bits))
        return v - (1 << bits)

    if lo <= v <= hi:
        return v

    raise AsmError("immediate should fit in " + str(bits) + " bits ("
                   + str(lo) + " to " + str(hi) + ")\n  but " + x + " doesn't")


# splits 'rd, rs1, rs2' or 'rd, 8(sp)' into operand strings
def split_operands(s):
    s = re.sub(r'\s*\(\s*', '(', s)
    s = re.sub(r'\s*\)', ')', s)
    return [o for o in re.split(r'[\s,]+', s.strip()) if o]


####################################################################
#                                                                  #
#   Inst class definition                                          #
#   one real RISCV instruction, already checked for valid syntax   #
#   registers are kept as the names the user typed (eg 't0')       #
#                                                                  #
####################################################################

class Inst:

    def __init__(self, op, rd=None, rs1=None, rs2=None, imm=None,
                 imm_str=None, label=None, reloc=None):
        self.op = op
        self.rd = rd
        self.rs1 = rs1
        self.rs2 = rs2
        self.imm = imm
        self.imm_str = imm_str  # how the user wrote the immediate
        self.label = label      # branch / jump target, or la's label
        self.reloc = reloc      # 'hi' or 'lo' for the halves of la
        self.src = None         # the pseudo instruction this came from

    def imm_text(self):
        if self.reloc:
            return "%pcrel_" + self.reloc + "(" + self.label + ")"
        if self.imm_str is not None:
            return self.imm_str
        return str(self.imm)

    def target_text(self):
        return self.label if self.label is not None else self.imm_text()

    def __str__(self):
        op = self.op

        if op in R_TYPES:
            return op + " " + self.rd + ", " + self.rs1 + ", " + self.rs2
        if op in I_ARITH or op in I_SHIFT:
            return op + " " + self.rd + ", " + self.rs1 + ", " + self.imm_text()
        if op in LOADS or op == "jalr":
            return op + " " + self.rd + ", " + self.imm_text() + "(" + self.rs1 + ")"
        if op in S_TYPES:
            return op + " " + self.rs2 + ", " + self.imm_text() + "(" + self.rs1 + ")"
        if op in B_TYPES:
            return op + " " + self.rs1 + ", " + self.rs2 + ", " + self.target_text()
        if op in U_TYPES:
            return op + " " + self.rd + ", " + self.imm_text()
        if op == "jal":
            return op + " " + self.rd + ", " + self.target_text()
        return op


# turns one line of assembly (no labels or comments) into a list of
# real instructions. returns (insts, is_pseudo)
def assemble(line):
    parts = line.split(None, 1)
    op = parts[0]
    ops = split_operands(parts[1]) if len(parts) > 1 else []

    def need(*counts, usage=""):
        if len(ops) not in counts:
            raise AsmError(op + ": expected '" + (op + " " + usage).strip()
                           + "' but got " + str(len(ops)) + " operand(s)")

    def reg(i):
        if not legit_reg_str(ops[i]):
            raise AsmError(op + ": '" + ops[i] + "' is not a register")
        return ops[i]

    # a branch / jump target: a label, or a numeric byte offset from pc
    def target(i, bits):
        o = ops[i]
        if legit_reg_str(o):
            raise AsmError(op + ": expected a label or an offset but '" + o
                           + "' is a register" + ("\n  to jump to an address in a register use jalr / jr"
                                                  if op == "jal" else ""))
        if is_number(o):
            imm = imm_gen(o, bits)
            if imm % 2:
                raise AsmError(op + ": offset " + o + " must be even\n"
                               "  (targets are at least 2 byte aligned, so bit 0 isn't stored)")
            return {"imm": imm, "imm_str": o}
        if not LABEL_RE.match(o):
            raise AsmError(op + ": '" + o + "' is not a valid label")
        return {"label": o}

    # 'offset(reg)' as used by loads, stores and jalr
    def mem_operand(i):
        m = re.fullmatch(r'(.*)\((.*)\)', ops[i])
        if not m:
            raise AsmError(op + ": expected offset(register), eg 8(sp), but got '" + ops[i] + "'")
        off = m.group(1) or '0'
        if not legit_reg_str(m.group(2)):
            raise AsmError(op + ": '" + m.group(2) + "' is not a register")
        return imm_gen(off, 12), off, m.group(2)

    if op in R_TYPES:
        need(3, usage="rd, rs1, rs2")
        if not legit_reg_str(ops[2]) and is_number(ops[2]):
            if op == "sub":
                raise AsmError("sub: there is no subi, use addi with a negative immediate")
            if op + 'i' in I_ARITH | I_SHIFT:
                raise AsmError(op + ": the last operand is an immediate, did you mean " + op + "i?")
        return [Inst(op, rd=reg(0), rs1=reg(1), rs2=reg(2))], False

    if op in I_ARITH:
        need(3, usage="rd, rs1, imm")
        if legit_reg_str(ops[2]):
            raise AsmError(op + ": the last operand should be an immediate, did you mean " + op[:-1] + "?")
        rd, rs1 = reg(0), reg(1)
        return [Inst(op, rd=rd, rs1=rs1, imm=imm_gen(ops[2], 12), imm_str=ops[2])], False

    if op in I_SHIFT:
        need(3, usage="rd, rs1, shamt")
        rd, rs1 = reg(0), reg(1)
        try:
            shamt = imm_gen(ops[2], 5, signed=False)
        except AsmError:
            raise AsmError(op + ": shift amount should be between 0 and 31 but got " + ops[2])
        return [Inst(op, rd=rd, rs1=rs1, imm=shamt, imm_str=ops[2])], False

    if op in LOADS:
        need(2, usage="rd, offset(rs1)")
        rd = reg(0)
        imm, off, base = mem_operand(1)
        return [Inst(op, rd=rd, rs1=base, imm=imm, imm_str=off)], False

    if op in S_TYPES:
        need(2, usage="rs2, offset(rs1)")
        rs2 = reg(0)
        imm, off, base = mem_operand(1)
        return [Inst(op, rs1=base, rs2=rs2, imm=imm, imm_str=off)], False

    if op in B_TYPES:
        need(3, usage="rs1, rs2, label")
        return [Inst(op, rs1=reg(0), rs2=reg(1), **target(2, 13))], False

    if op in U_TYPES:
        need(2, usage="rd, imm")
        rd = reg(0)
        try:
            imm = imm_gen(ops[1], 20, signed=False)
        except AsmError:
            raise AsmError(op + ": immediate should be between 0 and 0xfffff (20 bits)\n  but "
                           + ops[1] + " isn't. use li to load any 32 bit number")
        return [Inst(op, rd=rd, imm=imm, imm_str=ops[1])], False

    if op == "jal":
        need(1, 2, usage="rd, label")
        if len(ops) == 1:
            return assemble("jal ra, " + ops[0])[0], True
        return [Inst(op, rd=reg(0), **target(1, 21))], False

    if op == "jalr":
        need(1, 2, 3, usage="rd, offset(rs1)")
        if len(ops) == 1:
            return assemble("jalr ra, 0(" + ops[0] + ")")[0], True
        rd = reg(0)
        if len(ops) == 3:
            rs1 = reg(1)
            return [Inst(op, rd=rd, rs1=rs1, imm=imm_gen(ops[2], 12), imm_str=ops[2])], False
        if legit_reg_str(ops[1]):
            return [Inst(op, rd=rd, rs1=ops[1], imm=0, imm_str='0')], False
        imm, off, base = mem_operand(1)
        return [Inst(op, rd=rd, rs1=base, imm=imm, imm_str=off)], False

    if op == "fence":
        need(0, 2, usage="[pred, succ]")
        return [Inst(op)], False

    if op in SYSTEM:
        need(0)
        return [Inst(op)], False

    if op in PSEUDO_LUT:
        count, usage, expansion = PSEUDO_LUT[op]
        need(count, usage=usage)
        return assemble(expansion.format(*ops))[0], True

    if op == "li":
        need(2, usage="rd, imm")
        rd = reg(0)
        v, _ = parse_number(ops[1])

        if not -(1 << 31) <= v <= MASK:
            raise AsmError("li: " + ops[1] + " doesn't fit in 32 bits")

        sv = to_signed(v)

        # small enough for a single addi
        if -2048 <= sv <= 2047:
            imm_str = ops[1] if v == sv else str(sv)
            return [Inst("addi", rd=rd, rs1="x0", imm=sv, imm_str=imm_str)], True

        # otherwise lui the upper 20 bits, then addi the lower 12
        # addi sign extends its immediate, so if bit 11 is set the
        # lower half is negative and lui has to load one more to make up
        upper = ((v + 0x800) >> 12) & 0xfffff
        lower = to_signed(v - (upper << 12), 12)

        if lower < 0:
            print("Note: the lower 12 bits", to_hex(v, 12), "will be sign extended by addi to", lower)
            print("      so lui loads", hex(upper), "instead of", hex((v >> 12) & 0xfffff), "to make up for it")

        insts = [Inst("lui", rd=rd, imm=upper, imm_str=hex(upper))]
        if lower != 0:
            insts.append(Inst("addi", rd=rd, rs1=rd, imm=lower, imm_str=str(lower)))
        return insts, True

    if op == "la":
        need(2, usage="rd, label")
        rd = reg(0)
        if not LABEL_RE.match(ops[1]) or legit_reg_str(ops[1]):
            raise AsmError("la: '" + ops[1] + "' is not a valid label")
        return [Inst("auipc", rd=rd, label=ops[1], reloc="hi"),
                Inst("addi", rd=rd, rs1=rd, label=ops[1], reloc="lo")], True

    raise AsmError("instruction '" + op + "' not recognized")


####################################################################
#                                                                  #
#   ALU                                                            #
#   operands and results are unsigned 32-bit ints                  #
#                                                                  #
####################################################################

def div_fn(a, b):
    a, b = to_signed(a), to_signed(b)
    if b == 0:
        return -1
    if a == -(1 << 31) and b == -1:
        return a
    q = abs(a) // abs(b)
    return q if (a < 0) == (b < 0) else -q  # round towards zero

def divu_fn(a, b):
    return MASK if b == 0 else a // b

def rem_fn(a, b):
    sa, sb = to_signed(a), to_signed(b)
    if sb == 0:
        return sa
    return sa - sb * to_signed(div_fn(a, b))

def remu_fn(a, b):
    return a if b == 0 else a % b

# op: (symbol, how to show the operands, function)
# show is s (signed), u (unsigned), su (signed, unsigned), h (hex)
# or shift (hex, then the shift amount)
ALU = {
    "add":    ("+",   's',     lambda a, b: a + b),
    "sub":    ("-",   's',     lambda a, b: a - b),
    "slt":    ("<",   's',     lambda a, b: int(to_signed(a) < to_signed(b))),
    "sltu":   ("<",   'u',     lambda a, b: int(a < b)),
    "and":    ("and", 'h',     lambda a, b: a & b),
    "or":     ("or",  'h',     lambda a, b: a | b),
    "xor":    ("xor", 'h',     lambda a, b: a ^ b),
    "sll":    ("<<",  'shift', lambda a, b: a << (b & 31)),
    "srl":    (">>>", 'shift', lambda a, b: a >> (b & 31)),
    "sra":    (">>",  'shift', lambda a, b: to_signed(a) >> (b & 31)),
    "mul":    ("*",   's',     lambda a, b: to_signed(a) * to_signed(b)),
    "mulh":   ("*",   's',     lambda a, b: (to_signed(a) * to_signed(b)) >> 32),
    "mulhsu": ("*",   'su',    lambda a, b: (to_signed(a) * b) >> 32),
    "mulhu":  ("*",   'u',     lambda a, b: (a * b) >> 32),
    "div":    ("/",   's',     div_fn),
    "divu":   ("/",   'u',     divu_fn),
    "rem":    ("%",   's',     rem_fn),
    "remu":   ("%",   'u',     remu_fn),
}

# immediate versions of R type instructions
I_TO_R = {"addi": "add", "andi": "and", "ori": "or", "slti": "slt",
          "sltiu": "sltu", "xori": "xor", "slli": "sll", "srli": "srl",
          "srai": "sra"}

# branch: (symbol, compare signed?, function)
BRANCH = {
    "beq":  ("==", True,  lambda a, b: a == b),
    "bne":  ("!=", True,  lambda a, b: a != b),
    "blt":  ("<",  True,  lambda a, b: a < b),
    "bge":  (">=", True,  lambda a, b: a >= b),
    "bltu": ("<",  False, lambda a, b: a < b),
    "bgeu": (">=", False, lambda a, b: a >= b),
}


####################################################################
#                                                                  #
#   MEM class definition                                           #
#   Mem.data is a dict of address : one byte of data (an int)      #
#   data is stored little endian as in RISCV                       #
#       sw 0, 0xbadcab1e                                           #
#       data  ba  dc  ab  1e                                       #
#       addr  3   2   1   0                                        #
#                                                                  #
####################################################################

class Mem:

    def __init__(self, data=None):
        self.data = {}

        # validate that data is formatted correctly
        for addr, byte in (data or {}).items():
            if not (isinstance(addr, int) and isinstance(byte, int) and 0 <= byte <= 0xff):
                print("mem: initialization data provided is invalid")
                self.data = {}
                break
            self.data[addr & MASK] = byte

        if len(self.data) == 0:
            print("mem: empty mem initialized")

    # reads memory at address addr
    # form can be b (byte), h (half) or w (word)
    # returns the unsigned value read
    def read(self, addr, form):
        out = 0
        for i in range(MEM_SIZE_LUT[form]):
            a = (addr + i) & MASK
            if a not in self.data:
                raise ExecError("trying to read uninitialized mem at addr " + to_hex(a))
            out |= self.data[a] << (8 * i)
        return out

    # writes the lowest byte / half / word of val to address addr
    def write(self, addr, val, form):
        for i in range(MEM_SIZE_LUT[form]):
            self.data[(addr + i) & MASK] = (val >> (8 * i)) & 0xff

    # prints every word that has at least one byte written to it
    def dump(self):
        if not self.data:
            print("mem is empty")
            return

        print("addr          +3 +2 +1 +0")
        for base in sorted({a & ~3 for a in self.data}):
            cells = [self.data.get(base + i) for i in range(3, -1, -1)]
            line = to_hex(base) + "    " + " ".join("--" if c is None else format(c, "02x") for c in cells)
            if None not in cells:
                word = self.read(base, 'w')
                line += "   " + to_hex(word) + " (" + str(to_signed(word)) + ")"
            print(line)


####################################################################
#                                                                  #
#   CPU class definition                                           #
#                                                                  #
#   every instruction typed is assembled and stored in a separate  #
#   instruction memory (self.text) at self.text_end, then the cpu  #
#   runs from PC until it reaches the end of the program again.    #
#   normally that's just the new instruction, but after a backward #
#   branch it replays the stored instructions, which is how loops  #
#   work. a jump to a label that isn't defined yet sets            #
#   pending_label, and typed instructions are skipped until that   #
#   label is defined.                                              #
#                                                                  #
####################################################################

class CPU:

    def __init__(self, data=None):
        print("initializing cpu...")
        self.quiet = False
        self.reset_reg()
        self.reset_text()
        self.reset_PC()
        self.reset_mem(data)

    # Reset Functions
    ################################################################

    def reset_all(self):
        self.__init__()

    def reset_reg(self):
        self.registers = [0] * 32
        print("all registers set to 0")

    def reset_mem(self, data=None):
        self.mem = Mem(data)
        self.heap = HEAP_BASE

    def reset_text(self):
        self.text = {}      # addr: Inst
        self.labels = {}    # label: addr
        self.text_end = 0   # where the next instruction typed goes

    def reset_PC(self):
        self.PC = 0
        self.pending_label = None
        self.halted = False
        self.paused = False
        print("PC set to 0")
        if self.text:
            print("type 'run' to run your program again from the start")

    # Interacting with Registers
    # registers array stores unsigned 32-bit ints
    ################################################################

    # reads register x(reg)
    # form can be s (signed), u (unsigned), h (hex) or b (binary)
    def read_reg(self, reg, form):
        if reg < 0 or reg > 31:
            raise ExecError("read_reg: invalid register value")

        v = self.registers[reg]

        if form == 'b':
            return format(v, "032b")
        elif form == 'h':
            return format(v, "08x")
        elif form == 'u':
            return v
        elif form == 's':
            return to_signed(v)

        raise ExecError("read_reg: invalid arguments")

    # writes to register x(reg)
    # form can be i (int), h (hex) or b (binary)
    def write_reg(self, reg, val, form='i'):
        if reg < 0 or reg > 31:
            raise ExecError("write_reg: invalid register value")

        if form == 'b':
            val = int(val, 2)
        elif form == 'h':
            val = int(val, 16)
        elif form != 'i':
            raise ExecError("write_reg: invalid arguments")

        if reg != 0:
            self.registers[reg] = val & MASK

    # reads a register by name, unsigned
    def get(self, name):
        return self.registers[str_to_reg(name)]

    # writes a register by name, explaining writes to x0
    def set(self, name, val):
        if str_to_reg(name) == 0:
            self.say("Note: x0 is hardwired to 0, so this result is thrown away")
        self.write_reg(str_to_reg(name), val)

    # Output
    ################################################################

    # prints an explanation, unless we're running quietly
    def say(self, *args):
        if not self.quiet:
            print(*args)

    # prints 'rd = step1' then '   = step2' etc
    def explain(self, rd, steps):
        pad = ' ' * len(rd)
        last = None
        for i, s in enumerate(steps):
            if s != last:
                self.say((rd if i == 0 else pad) + " = " + s)
            last = s

    # label name of an address, for nicer output
    def label_at(self, addr):
        names = [l for l, a in self.labels.items() if a == addr]
        return " (" + ", ".join(names) + ")" if names else ""

    # Program state
    ################################################################

    # why the cpu can't run right now, or None if it can
    def blocked_reason(self):
        if self.halted:
            return "the program has exited. type 'reset pc' or 'reset all' to start again"
        if self.pending_label is not None:
            return "waiting for label '" + self.pending_label + "' to be defined"
        if self.PC > self.text_end:
            return "pc is " + to_hex(self.PC) + ", past the end of your program"
        return None

    def can_run(self):
        return self.blocked_reason() is None and self.PC in self.text

    # Actually execute code
    ################################################################

    # handles one line typed by the user:
    # labels, an instruction, or both (eg 'loop: addi t0, t0, 1')
    def do(self, code):

        # Decode
        #################################
        code = code.lower().strip()

        # Ignore comments
        comments = code.find('#')
        if comments != -1:
            code = code[:comments].strip()

        # strip off labels
        labels = []
        m = re.match(r'^([^\s:]+)\s*:(.*)$', code)
        while m:
            name = m.group(1)
            if not LABEL_RE.match(name) or legit_reg_str(name):
                raise AsmError("'" + name + "' is not a valid label name")
            if name in self.labels or name in labels:
                raise AsmError("label '" + name + "' is already defined at "
                               + to_hex(self.labels.get(name, self.text_end)))
            labels.append(name)
            code = m.group(2).strip()
            m = re.match(r'^([^\s:]+)\s*:(.*)$', code)

        insts, is_pseudo = assemble(code) if code else ([], False)

        # Store
        #################################

        for name in labels:
            self.labels[name] = self.text_end
            print("label", name, "=", to_hex(self.text_end))

            # a jump to this label happened earlier, so pick up from here
            if self.pending_label == name:
                self.pending_label = None
                self.PC = self.text_end
                print("that's where the earlier jump to '" + name + "' goes. resuming execution here")

        if not insts:
            return

        if is_pseudo:
            insts[0].src = code
            print("ie", insts[0])
            for inst in insts[1:]:
                print("  ", inst)

        first = self.text_end
        for inst in insts:
            self.text[self.text_end] = inst
            self.text_end += 4

        # Execute
        #################################

        if not self.can_run():
            reason = self.blocked_reason()
            if reason is None:
                reason = "pc is " + to_hex(self.PC)
            print("(not executed: " + reason + ")")
            return

        try:
            self.run(new=range(first, self.text_end, 4))
        except RiiipError:
            # if the instruction just typed failed, forget it
            # so the user can fix it and try again
            if self.PC is not None and first <= self.PC < self.text_end:
                for a in range(first, self.text_end, 4):
                    del self.text[a]
                self.text_end = first
                self.PC = first
            else:
                print("execution stopped at pc =", to_hex(self.PC), "\n")
            raise

    # executes instructions from PC until the end of the program
    # instructions in `new` were just typed, so they aren't echoed
    def run(self, new=()):
        steps = 0
        start = list(self.registers)
        self.paused = False

        try:
            while self.can_run() and not self.paused:
                if steps == MAX_STEPS:
                    print("stopped after", MAX_STEPS, "instructions, is this an infinite loop?")
                    print("pc =", to_hex(self.PC), "type 'run' to keep going or 'reset pc' to start over")
                    break

                if steps == QUIET_AFTER:
                    print("... looping, hiding output after", QUIET_AFTER, "instructions ...")
                    self.quiet = True

                if self.PC not in new:
                    self.say("[" + to_hex(self.PC) + "] " + str(self.text[self.PC]))

                self.step()
                steps += 1

        except KeyboardInterrupt:
            print("\ninterrupted at pc =", to_hex(self.PC))

        finally:
            if self.quiet:
                self.quiet = False
                self.summary(steps, start)

        if self.pending_label is not None:
            print("instructions you type will be skipped until you define '"
                  + self.pending_label + ":'")
        elif self.PC > self.text_end:
            print("instructions you type will be skipped until one lands at", to_hex(self.PC))

    # after a quiet run, show what changed
    def summary(self, steps, start):
        print("ran", steps, "instructions. pc =",
              "?" if self.PC is None else to_hex(self.PC))
        changed = [i for i in range(32) if start[i] != self.registers[i]]
        for i in changed:
            print("  " + REG_NAMES[i].ljust(4), to_signed(start[i]), "->", to_signed(self.registers[i]))

    # executes the instruction at PC and explains what it did
    def step(self):
        inst = self.text[self.PC]
        op = inst.op
        pc = self.PC
        next_pc = pc + 4

        # arithmetic
        #################################
        if op in R_TYPES or op in I_TO_R:
            a = self.get(inst.rs1)

            if op in R_TYPES:
                b, b_str = self.get(inst.rs2), inst.rs2
            else:
                imm = inst.imm
                if inst.reloc == "lo":
                    imm = self.pcrel(inst, pc - 4)[1]
                b, b_str = imm & MASK, inst.imm_text()

            self.alu(I_TO_R.get(op, op), op, inst.rd, inst.rs1, b_str, a, b)

        # loads
        #################################
        elif op in LOADS:
            form = op[1]
            size = MEM_SIZE_LUT[form]
            addr = (self.get(inst.rs1) + inst.imm) & MASK
            val = self.mem.read(addr, form)

            steps = ["mem[" + inst.rs1 + " + " + inst.imm_text() + "]  (" + MEM_SIZE_NAME[form] + ")",
                     "mem[" + to_hex(addr) + "]",
                     to_hex(val, 8 * size)]

            if size < 4:
                if op[-1] == 'u':
                    steps[-1] += " zero extended"
                else:
                    steps[-1] += " sign extended"
                    val = to_signed(val, 8 * size) & MASK

            steps.append(to_hex(val) + " (" + str(to_signed(val)) + ")")
            self.explain(inst.rd, steps)
            self.check_align(addr, size)
            self.set(inst.rd, val)

        # stores
        #################################
        elif op in S_TYPES:
            form = op[1]
            size = MEM_SIZE_LUT[form]
            addr = (self.get(inst.rs1) + inst.imm) & MASK
            val = self.get(inst.rs2)

            self.mem.write(addr, val, form)

            lhs = "mem[" + inst.rs1 + " + " + inst.imm_text() + "]"
            self.say(lhs, "=", inst.rs2, " (" + MEM_SIZE_NAME[form] + ")")
            self.say(' ' * len(lhs), "=", to_hex(val & ((1 << 8 * size) - 1), 8 * size),
                     "written to addr", to_hex(addr))
            if size < 4 and val >> (8 * size):
                self.say("Note: only the lowest", 8 * size, "bits of", inst.rs2, "are stored")
            self.check_align(addr, size)

        # branches
        #################################
        elif op in B_TYPES:
            sym, signed, fn = BRANCH[op]
            a, b = self.get(inst.rs1), self.get(inst.rs2)
            if signed:
                a, b = to_signed(a), to_signed(b)

            taken = fn(a, b)
            self.say(op + ": " + inst.rs1 + " " + sym + " " + inst.rs2 + " ?  "
                     + str(a) + " " + sym + " " + str(b) + " ?  "
                     + ("yes, branch taken" if taken else "no, branch not taken")
                     + ("" if signed else "  (compared as unsigned)"))

            if taken:
                next_pc = self.jump(inst, pc)
            else:
                self.say("pc = pc + 4 =", to_hex(next_pc))

        # jumps
        #################################
        elif op == "jal":
            target = self.target(inst, pc)
            self.check_jump(target)
            self.link(inst.rd, pc)
            next_pc = self.jump(inst, pc)

        elif op == "jalr":
            # read rs1 before writing rd, in case they're the same
            base = self.get(inst.rs1)
            target = (base + inst.imm) & MASK & ~1
            self.check_jump(target)
            self.link(inst.rd, pc)
            self.say("pc = (" + inst.rs1 + " + " + inst.imm_text() + ") & ~1")
            self.say("   =", to_hex(target) + self.label_at(target))
            next_pc = self.landing(target)

        # upper immediates
        #################################
        elif op == "lui":
            val = inst.imm << 12
            self.explain(inst.rd, [inst.imm_text() + " << 12", to_hex(val) + " (" + str(to_signed(val)) + ")"])
            self.set(inst.rd, val)

        elif op == "auipc":
            upper = inst.imm
            if inst.reloc == "hi":
                upper = self.pcrel(inst, pc)[0]
            val = (pc + (upper << 12)) & MASK
            self.explain(inst.rd, ["pc + (" + inst.imm_text() + " << 12)",
                                   to_hex(pc) + " + " + to_hex(upper << 12),
                                   to_hex(val) + " (" + str(to_signed(val)) + ")"])
            self.set(inst.rd, val)

        # system
        #################################
        elif op == "ecall":
            self.ecall()
            if self.halted:
                next_pc = pc

        elif op == "ebreak":
            self.say("ebreak: breakpoint at", to_hex(pc) + ". type 'run' or 'step' to continue")
            self.paused = True

        elif op == "fence":
            self.say("fence: orders memory accesses between harts. riiip only has one, so it does nothing")

        else:
            raise ExecError("do: instruction not recognized")

        self.PC = None if next_pc is None else next_pc & MASK

    # does the arithmetic for R and I type instructions
    # alu_op is the R type op, op is what was actually typed
    def alu(self, alu_op, op, rd, a_str, b_str, a, b):
        sym, show, fn = ALU[alu_op]
        result = fn(a, b) & MASK

        if show == 's':
            vals = str(to_signed(a)) + " " + sym + " " + str(to_signed(b))
        elif show == 'u':
            vals = str(a) + " " + sym + " " + str(b)
        elif show == 'su':
            vals = str(to_signed(a)) + " " + sym + " " + str(b)
        elif show == 'h':
            vals = to_hex(a) + " " + sym + " " + to_hex(b)
        else:
            vals = to_hex(a) + " " + sym + " " + str(b & 31)

        if alu_op in ("mulh", "mulhsu", "mulhu"):
            res = to_hex(result) + " (" + str(to_signed(result)) + ")  upper 32 bits of the 64 bit product"
        elif show in ('h', 'shift'):
            res = to_hex(result) + " (" + str(to_signed(result)) + ")"
        elif show == 'u' and alu_op != "sltu":
            res = str(result)
        else:
            res = str(to_signed(result))

        self.explain(rd, [a_str + " " + sym + " " + b_str, vals, res])

        # point out the tricky edge cases
        sa, sb = to_signed(a), to_signed(b)
        if alu_op in ("add", "sub", "mul"):
            exact = {"add": sa + sb, "sub": sa - sb, "mul": sa * sb}[alu_op]
            if exact != to_signed(result):
                self.say("Note: overflow! " + str(exact) + " doesn't fit in 32 bits so it wraps around")
        if op == "sltiu" and sb < 0:
            self.say("Note: sltiu sign extends the immediate, then compares unsigned, so",
                     sb, "is", b)
        if op in ("srl", "sll", "sra") and b > 31:
            self.say("Note: only the lowest 5 bits of", b_str, "are used, so it shifts by", b & 31)
        if alu_op in ("div", "divu", "rem", "remu"):
            if b == 0:
                self.say("Note: dividing by zero doesn't trap in RISCV,",
                         "div gives -1 and rem gives the dividend")
            elif alu_op in ("div", "rem") and sa == -(1 << 31) and sb == -1:
                self.say("Note: overflow! -2147483648 / -1 doesn't fit, so div gives",
                         "-2147483648 and rem gives 0")
            elif alu_op == "div" and sa % sb != 0 and (sa < 0) != (sb < 0):
                self.say("Note: div rounds towards zero")

        self.set(rd, result)

    # the upper / lower parts of the offset from pc to la's label
    def pcrel(self, inst, auipc_pc):
        if inst.label not in self.labels:
            raise ExecError("la: label '" + inst.label + "' isn't defined yet")
        offset = (self.labels[inst.label] - auipc_pc) & MASK
        upper = ((offset + 0x800) >> 12) & 0xfffff
        lower = to_signed(offset - (upper << 12), 12)
        return upper, lower

    # address a branch / jal goes to, or None if its label isn't defined yet
    def target(self, inst, pc):
        if inst.label is not None:
            return self.labels.get(inst.label)
        return (pc + inst.imm) & MASK

    # instructions are 4 bytes, so jumping between them is an error
    def check_jump(self, target):
        if target is not None and target % 4:
            raise ExecError("instruction address misaligned: " + to_hex(target)
                            + " is not a multiple of 4")

    def check_align(self, addr, size):
        if addr % size:
            self.say("Note:", to_hex(addr), "isn't aligned to", size, "bytes.",
                     "RISCV allows this, but it can be slow or trap on real hardware")

    # saves the return address for jal / jalr
    def link(self, rd, pc):
        if str_to_reg(rd) != 0:
            self.explain(rd, ["pc + 4", to_hex(pc + 4) + "  (return address)"])
            self.write_reg(str_to_reg(rd), pc + 4)

    # works out where a branch / jal goes
    def jump(self, inst, pc):
        target = self.target(inst, pc)

        if target is None:
            self.say("pc = " + inst.label + ", which isn't defined yet")
            self.pending_label = inst.label
            return None

        self.check_jump(target)
        if inst.label is not None:
            self.say("pc =", inst.label, "=", to_hex(target))
        else:
            self.say("pc = pc + " + inst.imm_text() + " = " + to_hex(target) + self.label_at(target))
        return self.landing(target)

    def landing(self, target):
        if target > self.text_end:
            self.say("Note: that's past the end of your program")
        return target

    # environment calls, using venus' convention:
    # a0 is the call id and a1 is the argument
    def ecall(self):
        cid = to_signed(self.get("a0"))
        arg = self.get("a1")

        if cid == 1:
            self.say("ecall: a0 = 1, print_int(a1)")
            print("output:", to_signed(arg))

        elif cid == 4:
            self.say("ecall: a0 = 4, print_string(a1)")
            chars = []
            addr = arg
            while True:
                byte = self.mem.read(addr, 'b')
                if byte == 0:
                    break
                chars.append(chr(byte))
                addr = (addr + 1) & MASK
            print("output:", "".join(chars))

        elif cid == 9:
            self.say("ecall: a0 = 9, sbrk(a1) allocates", arg, "bytes of heap")
            self.explain("a0", ["start of the new memory", to_hex(self.heap)])
            self.write_reg(10, self.heap)
            self.heap = (self.heap + arg) & MASK

        elif cid == 11:
            self.say("ecall: a0 = 11, print_char(a1)")
            print("output:", chr(arg & 0xff))

        elif cid in (10, 17):
            code = 0 if cid == 10 else to_signed(arg)
            print("ecall: a0 =", cid, "exit. program exited with code", code)
            self.halted = True

        else:
            raise ExecError("ecall: unknown call id a0 = " + str(cid) + "\n"
                            "  try 1 print_int, 4 print_string, 9 sbrk,\n"
                            "  10 exit, 11 print_char, 17 exit with code a1")
