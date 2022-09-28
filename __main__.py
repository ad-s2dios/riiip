######################
# author:  ad-s2dios #
# version: 1.1       #
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

        elif code == 'help':
            print("Enter registers to get their value (eg 't0' or 'x5')")
            print("'exit' to exit")

        elif code == 'exit':
            exit()

        else:
            try:
                # try to execute the instruction given
                cpu.do(code)
            except Exception as e:
                if len(str(e)) > 0:
                    print("=== ERROR:", e)
                else:
                    print("=== invalid inst ===")