######################
# author:  ad-s2dios #
# version: 1.1       #
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

MEM_SIZE_LUT = {'b': 1, 'h': 2, 'w': 4, 'd': 8}

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
        print("Warning:", len(b) - N, "bits chopped off from MSB")
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
        print("imm_gen: imm format not recognized. use one of:")
        print("         bin '0b101', hex '0xabc', int '-1'")
        raise ValueError  # neither binary nor hex nor decimal

    # length checks

    if len(x) > bin_len:
        return None  # invalid input
    
    if len(x) < bin_len:
        return int(x, 2)

    # sign extension
    return bin_to_sint(x)

# takes a little endian bit string and makes it right
def reverse_bytes(bits):
    if len(bits) == 8:
        return bits

    if len(bits) % 8 != 0:
        print("reverse_bytes: bits are not padded to byte size")
        raise ValueError

    out = ''
    for i in range(0, len(bits), 8):
        out = bits[i:i+8] + out

    return out


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
#   MEM class definition                                           #
#   Mem.data is a dict of address : one byte of data               #
#   if data is binary, it's stored as 'b0110' etc                  #
#   if its an inst str, it's stored as 'iaddi t0, t1, 5' in the    #
#       1st byte, then 'i1', 'i2', 'i3'                            #
#   data is stored little endian as in RISCV                       #
#                                                                  #
####################################################################

class Mem:

    def __init__(self, data={}):
        self.data = data

        # validate that data is formatted correctly
        for k, i in data.items():
            # if len(i) != 32:
            if i[0] == 'b' and len(i) != 9:
                print("mem: initialization data provided is invalid")
                print("     empty mem initialized")
                self.data = {}
                return

    # interact with memory
        # sw 0, 0xbadcab1e
        # data  1e  ab  dc  ba
        # addr  3   2   1   0
    ################################################################

    # reads memory at address addr
    # form can be b (byte), h (half) or w (word)
    # returns data of length specified by form
    def read(self, addr, form):

        if form not in MEM_SIZE_LUT:
            print("read_mem: invalid arguments")
            raise ValueError

        # trying to read an inst str
        if form == 'w' and addr in self.data and self.data[addr][0] == 'i':
            check = [addr + i in self.data and self.data[addr + i] == 'i' + str(i) for i in range(1,4)]
            if sum(check) == 3:
                return self.data[addr]
            else:
                print("read_mem: invalid instruction string format")
                raise ValueError

        out = ''
        # read the value byte by byte
        for i in range(MEM_SIZE_LUT[form]):

            if (addr + i) not in self.data:
                print("read_mem: trying to read uninitialized mem")
                raise ValueError

            if self.data[addr + i][0] == 'i':
                print("read_mem: trying to read part of an instruction")
                raise ValueError

            out += self.data[addr + i][1:]

        return out

        # flip = 3 - (addr % 4)
        # key = addr // 4
        # out = ''

        # if form == 'b':
        #     if key in self.data:
        #         out = self.data[key][flip * 8:(flip + 1) * 8]

        # elif form == 'h':
        #     # ie we cross the boundary
        #     if flip == 0:
        #         if key in self.data and (key + 1) in self.data:
        #             out = self.data[key][:8] + self.data[key + 1][24:]

        #     elif key in self.data:
        #         out = reverse_bytes(self.data[key][(flip - 1) * 8:(flip + 1) * 8])

        # elif form == 'w':
        #     # ie we do not cross the boundary
        #     if flip == 3:
        #         if key in self.data:
        #             out = reverse_bytes(self.data[key])

        #     elif key in self.data and (key + 1) in self.data:
        #         first = self.data[key][:(flip + 1) * 8]
        #         second = self.data[key + 1][(flip + 1) * 8:]
        #         out = reverse_bytes(second + first)

        # if len(out) == 0:
        #     print("read_mem: addr", addr, "not initialized for", form, "length")
        #     raise ValueError

        # if 'x' in out:
        #     print("read_mem: parts of memory requested not initialized")
        #     raise ValueError

        # return out



    # writes memory at address addr
    # if !is_inst, val should be length 8 (byte), 16 (half) or 32 (word)
    def write(self, addr, val, is_inst=False):

        if is_inst:
            iters = 4
            to_write = ['i' + val] + ['i' + str(i) for i in range(1,4)]
        else:
            if len(val) not in [8, 16, 32]:
                print("write_mem: data should have length 8 (byte), 16 (half) or 32 (word)")
                raise ValueError

            iters = len(val) // 8
            to_write = ['b' + val[i * 8:(i + 1) * 8] for i in range(iters)]

        for i in range(iters):

            if (addr + i) in self.data:
                if self.data[addr + i][0] == 'i':
                    print("Warning: overwriting instruction at addr", addr + i)
                else:
                    print("Warning: overwriting mem at addr", addr + i)

            self.data[addr + i] = to_write[i]



####################################################################
#                                                                  #
#   CPU class definition                                           #
#                                                                  #
####################################################################

class CPU:

    def __init__(self, data={}):
        print("initializing cpu...")
        self.reset_reg()
        self.reset_PC()
        self.mem = Mem(data)

    # Reset Functions
    ################################################################

    def reset_reg(self):
        self.registers = ['0' * 32] * 32
        print("all registers set to 0")

    def reset_mem(self):
        self.mem = Mem()
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

        if code == "nop":
            print("ie addi x0, x0, 0")
            self.PC += 4
            return

        # find the first space
        space = code.find(' ')

        if space == -1:
            print("do: invalid inst without spaces")
            raise ValueError

        # extract instruction and operands
        inst = code[:space]
        opstr = [i.strip() for i in code[space:].split(',')]

        # syntax for a load / store ()
        if '(' in opstr[-1]:
            opstr[-1], temp = opstr[-1].split('(')
            close = temp.find(')')
            if close == -1:
                print("LD/ST: missing ')'")
                raise ValueError
            opstr.append(temp[:close])


        # Execute / Writeback
        #################################

        if inst in R_TYPES:
            # we should have 3 legit registers as operands
            if sum([legit_reg_str(o) for o in opstr]) != 3 or len(opstr) != 3:
                print("R_TYPE: inst should have 3 reg operands")
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
                    print("I_TYPE: inst should have 2 reg operands")
                    raise ValueError

                # and a third imm
                if len(opstr) != 3:
                    print("I_TYPE: inst should have a third immediate operand")
                    raise ValueError

                # get register number and immediate
                ops = [str_to_reg(opstr[0]), str_to_reg(opstr[1])]
                imm = imm_gen(opstr[2], 12)

                if imm == None:
                    print("I_TYPE: immediate should have len <= 12 bits")
                    print("        but", opstr[2], "exceeds this")
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

            # loads
            elif inst[0] == 'l':
                if len(opstr) != 3 or (not legit_reg_str(opstr[0])) or (not legit_reg_str(opstr[2])):
                    print("LOAD: inst should have 2 reg operands and an imm")
            
                # get registers and immediate
                rd = str_to_reg(opstr[0])
                imm = imm_gen(opstr[1], 12)

                if imm == None:
                    print("S_TYPE: immediate should have len <= 12 bits")
                    print("        but", opstr[1], "exceeds this")
                    raise ValueError

                addr = imm + self.read_reg(str_to_reg(opstr[2]), 'u')

                # b, h or w
                val = self.mem.read(addr, inst[1])
                # sign extension if not u
                val = pad_binN(val, 32, inst[-1] != 'u')

                print(bin_to_hex(val), "read to register", rd)

                self.write_reg(rd, val, 'b')
                self.PC += 4

        # stores
        elif inst in S_TYPES:

            if len(opstr) != 3 or (not legit_reg_str(opstr[0])) or (not legit_reg_str(opstr[2])):
                print("S_TYPE: inst should have 2 reg operands and an imm")
            
            # get register number and immediate
            imm = imm_gen(opstr[1], 12)

            if imm == None:
                print("S_TYPE: immediate should have len <= 12 bits")
                print("        but", opstr[1], "exceeds this")
                raise ValueError

            addr = imm + self.read_reg(str_to_reg(opstr[2]), 'u')
            val = self.read_reg(str_to_reg(opstr[0]), 'b')
            val = val[-8 * MEM_SIZE_LUT[inst[-1]]]

            print(bin_to_hex(val), "written to addr", addr)

            self.mem.write(addr, val)
            self.PC += 4

        elif inst in U_TYPES:
            print('U')

        elif inst in B_TYPES:
            print('B')

        elif inst in PSEUDO:

            if inst == "li":

                if len(opstr) != 2 or (not legit_reg_str(opstr[0])):
                    print("PSEUDO: li operands should be 1 reg and 1 immediate")
                    raise ValueError

                imm = imm_gen(opstr[1], 12)

                if imm == None:
                    print("PSEUDO: immediate should have len <= 12 bits")
                    print("        but", opstr[1], "exceeds this")
                    raise ValueError

                self.write_reg(str_to_reg(opstr[0]), imm, 'i')
                self.PC += 4

                print("ie addi", opstr[0], ", x0,", opstr[1])
                print(opstr[0], " =", imm)

            elif inst == "mv":

                if sum([legit_reg_str(o) for o in opstr]) != 2 or len(opstr) != 2:
                    print("PSEUDO: mv should have 2 reg operands")
                    raise ValueError

                val = self.read_reg(str_to_reg(opstr[1]), 'b')
                self.write_reg(str_to_reg(opstr[0]), val, 'b')
                self.PC += 4

                print("ie add", opstr[0], ", x0,", opstr[1])
                print(opstr[0], " =", opstr[1])
                print("    =", bin_to_sint(val))

            else:
                print('P')

        else:
            print("do: instruction not recognized")
            raise ValueError

    