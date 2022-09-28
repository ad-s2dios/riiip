######################
# author:  ad-s2dios #
# version: 1.0       #
######################

####################################################################
#                                                                  #
#   Constants                                                      #
#                                                                  #
####################################################################

REG_LUT = {"zero": 0, "ra": 1, "sp": 2, "gp": 3, "tp": 4,
            "t0": 5, "t1": 6, "t2": 7,
            "s0": 8, "fp": 8, "s1": 9,
            "a0": 10, "a1": 11, "a2": 12, "a3": 13,
            "a4": 14, "a5": 15, "a6": 16, "a7": 17,
            "s2": 18, "s3": 19, "s4": 20, "s5": 21, "s6": 22,
            "s7": 23, "s8": 24, "s9": 25, "s10": 26, "s11": 27,
            "t3": 28, "t4": 29, "t5": 30, "t6": 31}

ABC = "abcdef" # used for hex conversions

R_TYPES = {"add", "and", "or", "sll", "slt", "sltu", 
            "sra", "srl", "sub", "xor"}

I_TYPES = {"addi", "andi", "jalr", "lb", "lbu", "lh", "lhu", "lw", 
            "ori", "slli", "slti", "sltiu", "srai", "srli", "xori"}

S_TYPES = {"sb", "sh", "sw"}

U_TYPES = {"auipc", "jal", "lui"}

B_TYPES = {"beq", "bge", "bgeu", "blt", "bltu", "bne"}

PSEUDO = {"beqz", "bnez", "j", "jr", "la", "li", "mv", "neg", "nop", 
            "not", "ret", "seqz", "snez"}


####################################################################
#                                                                  #
#   Helper functions                                               #
#                                                                  #
####################################################################

# pads binary str to N exactly
def pad_binN(b, N, sign_ext):
    # nothing to do
    if len(b) == N:
        return b

    # chop off extra MSB
    if len(b) > N:
        return b[len(b) - N:]

    if sign_ext:
        ext = b[0]
    else:
        ext = '0'

    return ext * (N - len(b)) + b


# converts binary to (signed) int
def bin_to_sint(b):
    if b[0] == '0':
        return int(b, 2)
    else:
        return int(b, 2) - (1 << len(b))


# converts int to binary with bin_len (without prefixes)
def int_to_bin(i, bin_len):
    # positive: convert and pad
    if i >= 0:
        b = bin(i)[2:]
        if len(b) > bin_len:
            return None
        else:
            b = pad_binN(b, bin_len, False)
            if b[0] == '1':
                print("Warning: Converted", i, "to a", bin_len, "-bit negative signed number")
            return b

    # negaitve: check if number is in range (3 is from -0b)
    if len(bin(i)) >= (bin_len + 3) and i != -(1 << (bin_len - 1)):
        return None

    return bin(i + (1 << bin_len))[2:]


# converts binary str to hex (without prefixes)
def bin_to_hex(b):
    h = ''

    # pads binary str to multiple of 4
    if len(b) % 4 != 0:
        b = '0' * (4 - len(b) % 4) + b

    for _ in range(len(b)//4):
        temp = int(b[:4], 2)

        if temp < 10:
            h += str(temp)
        else:
            h += ABC[temp - 10]

        b = b[4:]

    return h

# converts hex str to binary (without prefixes)
def hex_to_bin(h):
    b = ''

    for char in h:
        if char.isdigit():
            b += int_to_bin(int(char), 4)
        else:
            b += bin(10 + ABC.find(char))[2:]

    return b



# checks if register str is legit
def legit_reg_str(reg):
    if reg[0] == 'x' and reg[1:].isdigit():
        reg = int(reg[1:])
        return reg >= 0 and reg < 32

    else:
        return reg in REG_LUT

# get register number from string
def str_to_reg(reg):
    if reg[0] == 'x':
        return int(reg[1:])
    else:
        return REG_LUT[reg]

# generate immediate
# return None if it's beyond desired length (in # bits)
def imm_gen(x, bin_len):
    imm = None

    # lets handle decimals first

    if type(x) == int:
        imm = x

    elif x.isdigit():
        imm = int(x)

    elif x[0] == '-' and x[1:].isdigit():
        imm = -int(x[1:])

    # we have a decimal
    if imm != None:
        # check if int is within bin_len
        b = int_to_bin(imm, bin_len)
        if b != None:
            return bin_to_sint(b)
        else:
            return None

    # convert to nice binary format

    if x[:2] == "0x":
        x = hex_to_bin(x[2:])
    elif x[:2] == "0b":
        x = x[2:]   # strip the '0b'
    else:
        return None # neither binary nor hex

    # length checks

    if len(x) > bin_len:
        return None  # invalid input
    
    if len(x) < bin_len:
        return int(x, 2)

    # sign extension
    return bin_to_sint(x)



####################################################################
#                                                                  #
#   R type functions                                               #
#                                                                  #
####################################################################

def add_fn(op1, op2):
    print(op1, "+", op2)
    return op1 + op2

def and_fn(op1, op2):
    print(op1, "and", op2)
    return op1 & op2

def or_fn(op1, op2):
    print(op1, "or", op2)
    return op1 | op2

def slt_fn(op1, op2):
    print(op1, "<", op2)
    return op1 < op2

def sub_fn(op1, op2):
    print(op1, "-", op2)
    return op1 - op2

def xor_fn(op1, op2):
    print(op1, "xor", op2)
    return op1 ^ op2

R_FUNCS = {"add": add_fn, "and": and_fn, "or": or_fn, "slt": slt_fn, 
            "sub": sub_fn, "xor": xor_fn}



####################################################################
#                                                                  #
#   CPU class definition                                           #
#                                                                  #
####################################################################

class CPU:

    def __init__(self, mem={}):
        print("initializing cpu...")
        self.reset_reg()
        self.reset_PC()
        self.mem = mem

    # Reset Functions
    ################################################################

    def reset_reg(self):
        self.registers = ['0' * 32] * 32
        print("all registers set to 0")

    def reset_mem(self):
        self.mem = {}
        print("memory cleared")

    def reset_PC(self):
        self.PC = 0
        print("PC set to 0")

    # Interacting with Registers
    # registers array stores 32-bit long bin strings (no 0b prefix)
    ################################################################

    # reads register x(reg)
    # form can be s (signed), u (unsigned), h (hex) or b (binary)
    def read_reg(self, reg, form):
        if reg < 0 or reg > 31:
            print("read_reg: invalid register value")
            raise ValueError

        if form == 'b':
            return self.registers[reg]

        elif form == 'h':
            return bin_to_hex(self.registers[reg])

        elif form == 'u':
            return int(self.registers[reg], 2)

        elif form == 's':
            return bin_to_sint(self.registers[reg])

        else:
            print("read_reg: invalid arguments")
            raise ValueError

    # writes to register x(reg)
    # form can be i (int), h (hex) or b (binary)
    # sign extension can be set accordingly but is default to false
    def write_reg(self, reg, val, form, sign_ext=False):
        if reg < 0 or reg > 31:
            print("write_reg: invalid register value")
            raise ValueError

        if reg == 0:
            return

        if form == 'b':
            b = val

        elif form == 'h':
            b = hex_to_bin(val)

        elif form == 'i':
            b = int_to_bin(val, 32)

        else:
            print("write_reg: invalid arguments")
            raise ValueError

        self.registers[reg] = pad_binN(b, 32, sign_ext)


    # Actually execute code
    ################################################################

    def do(self, code):

        # Decode
        #################################
        code = code.lower().strip()

        # Ignore comments
        comments = code.find('#')
        if (comments == 0):
            return
        elif (comments != -1):
            code = code[:comments]

        # find the first space
        space = code.find(' ')

        if space == -1:
            print("do: invalid inst without spaces")
            raise ValueError

        # extract instruction and operands
        inst = code[:space]
        opstr = [i.strip() for i in code[space:].split(',')]


        # Execute / Writeback
        #################################

        if inst in R_TYPES:
            # we should have 3 legit registers as operands
            if sum([legit_reg_str(o) for o in opstr]) != 3 or len(opstr) != 3:
                print("do: R_TYPE inst should have 3 register operands")
                raise ValueError

            # get register number from names
            ops = [str_to_reg(o) for o in opstr]

            print(opstr[0], " = ", end='')

            # most instructions
            if inst in R_FUNCS:
                rd = R_FUNCS[inst](self.read_reg(ops[1], 's'), self.read_reg(ops[2], 's'))
                self.write_reg(ops[0], rd, 'i')

            elif inst == "sltu":
                rd = slt_fn(self.read_reg(ops[1], 'u'), self.read_reg(ops[2], 'u'))
                self.write_reg(ops[0], rd, 'i')

            # handle shifts
            else:
                rd = self.read_reg(ops[1], 'b')
                shift_amt = self.read_reg(ops[2], 'u')

                if inst == "sll":
                    print(rd, "<<", shift_amt)
                    rd = rd + '0' * shift_amt

                elif inst == "sra":
                    print(rd, ">>", shift_amt)
                    rd = rd[0] * shift_amt + rd
                    rd = rd[:32]

                else:
                    print(rd, ">>>", shift_amt)
                    rd = '0' * shift_amt + rd
                    rd = rd[:32]

                self.write_reg(ops[0], rd, 'b')

            print("    =", rd)
            self.PC += 4

        elif inst in I_TYPES:

            # arithmetic instructions
            if inst[-1] == 'i' or inst[-2:] == 'iu':

                # we should have 2 legit registers as operands
                if (not legit_reg_str(opstr[0])) or (not legit_reg_str(opstr[1])):
                    print("do: I_TYPE inst should have 2 register operands")
                    raise ValueError

                # and a third imm
                if len(opstr) != 3:
                    print("do: I_TYPE inst should have a third immediate operand")
                    raise ValueError

                # get register number and immediate
                ops = [str_to_reg(opstr[0]), str_to_reg(opstr[1])]
                imm = imm_gen(opstr[2], 12)

                if (imm == None):
                    print("do: immediate should have len <= 12 bits")
                    print("    but", opstr[2], "exceeds this")
                    raise ValueError

                print(opstr[0], " = ", end='')

                if inst[:-1] in R_FUNCS:
                    rd = R_FUNCS[inst[:-1]](self.read_reg(ops[1], 's'), imm)
                    self.write_reg(ops[0], rd, 'i')

                elif inst == "sltiu":
                    rd = slt_fn(self.read_reg(ops[1], 'u'), imm)
                    self.write_reg(ops[0], rd, 'i')

                # handle shifts
                else:
                    rd = self.read_reg(ops[1], 'b')

                    if inst == "sll":
                        print(rd, "<<", imm)
                        rd = rd + '0' * imm

                    elif inst == "sra":
                        print(rd, ">>", imm)
                        rd = rd[0] * imm + rd
                        rd = rd[:32]

                    else:
                        print(rd, ">>>", imm)
                        rd = '0' * imm + rd
                        rd = rd[:32]

                    self.write_reg(ops[0], rd, 'b')

                print("    =", rd)
                self.PC += 4                


        elif inst in S_TYPES:
            print('S')

        elif inst in U_TYPES:
            print('U')

        elif inst in B_TYPES:
            print('B')

        elif inst in PSEUDO:
            print('P')

        else:
            print("do: instruction not recognized")
            raise ValueError

    