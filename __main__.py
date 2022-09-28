######################
# author:  ad-s2dios #
# version: 1.0       #
######################

from riiip import *

# Main function
if __name__ == "__main__":
    print("Welcome to riiip 1.0!\n")
    cpu = CPU()
    print()

    while True:
        code = input('riiip$ ')

        code = code.lower().strip()

        if legit_reg_str(code):
            # print the register in hex and signed int
            print(code, ": 0x", cpu.read_reg(str_to_reg(code), 'h'), end='\t')
            print(cpu.read_reg(str_to_reg(code), 's'))

        elif code == 'help':
            print("Enter registers to get their value (eg 't0' or 'x5')")
            print("'exit' to exit")

        elif code == 'exit':
            exit()

        else:
            try:
                # try to execute the instruction given
                cpu.do(code)
            except:
                print("===== ERROR =====")