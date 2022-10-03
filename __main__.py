######################
# author:  ad-s2dios #
# version: 1.2       #
######################

from riiip import *

# Main function
if __name__ == "__main__":
    print("👻 Welcome to riiip 1.1! 👻\n")
    cpu = CPU()
    print()

    # mem = Mem({0:'b00000001', 1:'b00100011', 2:'b01000101', 3:'b01100111', 4:'b10001001',5:'b10101011',6:'b11001101',7:'b11101111', 8:'ili t0, 0xabc', 9:'i1', 10:'i2', 11:'iL'})

    while True:
        code = input(' 👻 ')

        code = code.lower().strip()

        if legit_reg_str(code):
            # print the register in hex and signed int
            print(code, ": 0x", cpu.read_reg(str_to_reg(code), 'h'), end='\t')
            print(cpu.read_reg(str_to_reg(code), 's'))

        elif code == "pc":
            print("pc :", cpu.PC)

        elif code == "mem":
            print("mem :", cpu.mem.data)

        elif code == 'exit':
            exit()

        elif 'reset' in code:
            code = code.split(' ')

            if code[-1] == 'all':
                cpu = CPU()

            elif code[-1] == 'reg':
                cpu.reset_reg()

            elif code[-1] == 'mem':
                cpu.reset_mem()

            elif code[-1] == 'pc':
                cpu.reset_PC()

            else:
                print("=== invalid command ===")
                print("Enter 'help' for available commands")

        elif code == 'help':
            print("<register>  get register value (eg 't0' or 'x5')")
            print("pc          get current PC")
            print("mem         get memory dictionary")
            print("exit        exit riiip")
            print("reset < >")
            print("      all   reset cpu and memory entirely")
            print("      reg   reset all registers to 0")
            print("      mem   reset all memory to 0")
            print("      pc    reset PC to 0")

        else:
            try:
                # try to execute the instruction given
                cpu.do(code)
            except Exception as e:
                if len(str(e)) > 0:
                    print("=== ERROR:", e)
                else:
                    print("=== invalid inst ===")