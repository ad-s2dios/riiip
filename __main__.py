######################
# author:  ad-s2dios #
# version: 1.2       #
######################

import sys

from riiip import *

PROMPT = ' 👻 '

HELP = """\
<instruction>   execute an instruction (eg 'addi t0, t0, 1')
<label>:        define a label for branches and jumps (eg 'loop:')
<register>      get register value (eg 't0' or 'x5')
regs            get all register values
pc              get current PC
mem             get memory contents
prog            list the program typed so far
labels          list labels
run             continue running the program from PC
step            execute one instruction at PC
load <file>     type in every line of an assembly file
exit            exit riiip
reset < >
      all       reset cpu, program and memory entirely
      reg       reset all registers to 0
      mem       reset all memory
      pc        reset PC to 0 (then 'run' replays your program)"""


def show_reg(cpu, name):
    reg = str_to_reg(name)
    out = name + " = 0x" + cpu.read_reg(reg, 'h') + " = " + str(cpu.read_reg(reg, 's'))
    if cpu.read_reg(reg, 's') < 0:
        out += " (unsigned " + str(cpu.read_reg(reg, 'u')) + ")"
    print(out)


def show_regs(cpu):
    for row in range(8):
        cells = []
        for reg in range(row, 32, 8):
            label = ("x" + str(reg) + " " + REG_NAMES[reg]).ljust(9)
            cells.append(label + str(cpu.read_reg(reg, 's')).rjust(11))
        print("   ".join(cells))


def show_prog(cpu):
    if not cpu.text and not cpu.labels:
        print("no program yet")
        return

    for addr in range(0, cpu.text_end + 4, 4):
        for label, a in cpu.labels.items():
            if a == addr:
                print(" " * 13 + label + ":")

        if addr not in cpu.text:
            continue

        inst = cpu.text[addr]
        line = (">" if addr == cpu.PC else " ") + " " + to_hex(addr) + "    " + str(inst)
        if inst.src:
            line = line.ljust(45) + "# " + inst.src
        print(line)

    reason = cpu.blocked_reason()
    if reason:
        print("(" + reason + ")")


def show_pc(cpu):
    if cpu.pending_label is not None:
        print("pc : unknown, waiting for label '" + cpu.pending_label + "' to be defined")
    else:
        print("pc :", to_hex(cpu.PC), "=", cpu.PC)


# feeds each line of a file to riiip as if it were typed
def load(cpu, path):
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError as e:
        print("load: couldn't open", path, "-", e.strerror)
        return

    for num, line in enumerate(lines, 1):
        code = line.split('#')[0].strip()
        if not code:
            continue

        print(PROMPT + code)

        if code.startswith('.'):
            print("(assembler directive ignored)")
            continue

        if not handle(cpu, code):
            print("load: stopped at line", num, "of", path)
            return


# handles one line of input. returns False if it failed
def handle(cpu, line):
    raw = line.strip()
    code = raw.lower()
    words = code.split()

    if not code:
        pass

    elif legit_reg_str(code):
        show_reg(cpu, code)

    elif code == "regs":
        show_regs(cpu)

    elif code == "pc":
        show_pc(cpu)

    elif code == "mem":
        cpu.mem.dump()

    elif code in ("prog", "program"):
        show_prog(cpu)

    elif code == "labels":
        if not cpu.labels:
            print("no labels yet")
        for label, addr in cpu.labels.items():
            print(label.ljust(12), to_hex(addr))

    elif code in ("run", "step"):
        reason = cpu.blocked_reason()
        if reason:
            print(reason)
        elif not cpu.can_run():
            print("nothing to " + code + ", pc is at the end of your program")
        else:
            try:
                if code == "run":
                    cpu.run()
                else:
                    print("[" + to_hex(cpu.PC) + "] " + str(cpu.text[cpu.PC]))
                    cpu.step()
            except RiiipError as e:
                print(e)
                print("=== runtime error ===")
                return False

    elif code in ("exit", "quit"):
        sys.exit()

    elif words[0] == "reset":
        if words[-1] == "all":
            cpu.reset_all()
        elif words[-1] == "reg":
            cpu.reset_reg()
        elif words[-1] == "mem":
            cpu.reset_mem()
            print("memory cleared")
        elif words[-1] == "pc":
            cpu.reset_PC()
        else:
            print("=== invalid command ===")
            print("Enter 'help' for available commands")
            return False

    elif words[0] == "load" and len(words) > 1:
        load(cpu, raw.split(None, 1)[1])

    elif code == "help":
        print(HELP)

    else:
        try:
            # try to execute the instruction given
            cpu.do(code)
        except AsmError as e:
            print(e)
            print("=== invalid inst ===")
            return False
        except ExecError as e:
            print(e)
            print("=== runtime error ===")
            return False

    return True


# Main function
if __name__ == "__main__":
    print("👻 Welcome to riiip 1.2! 👻\n")
    cpu = CPU()
    print()

    # any files given on the command line are loaded first
    for path in sys.argv[1:]:
        load(cpu, path)

    while True:
        try:
            line = input(PROMPT)
        except (EOFError, KeyboardInterrupt):
            print()
            break

        try:
            handle(cpu, line)
        except RiiipError as e:
            print("=== ERROR:", e)
        except Exception as e:
            # a bug in riiip itself, keep the session alive
            print("=== ERROR:", repr(e))
