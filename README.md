# 👻 riiip: RISCV Interactive Interpreter in Python

The main goal of riiip is to make learning RISCV easy! 

riiip is inspired by the python shell, which was extremely helpful for me when I first learned to code. Simply type instructions in riiip and get instant feedback on what executed. Type a register name to get its value. Invalid instructions print helpful messages as they execute, so you know why they're wrong. Tricky edge cases with negative numbers and sign extentions are clearly indicated.

riiip is built entirely in python, making it easy to play around with and modify.

## Starting riiip

```bash
git clone https://github.com/ad-s2dios/riiip.git
python3 riiip
```

## Example

```
👻 Welcome to riiip 1.2! 👻

initializing cpu...
all registers set to 0
PC set to 0
mem: empty mem initialized

 👻 li t0, 0
ie addi t0, x0, 0
t0 = x0 + 0
   = 0 + 0
   = 0
 👻 li t1, 3
ie addi t1, x0, 3
t1 = x0 + 3
   = 0 + 3
   = 3
 👻 loop: addi t0, t0, 1
label loop = 0x00000008
t0 = t0 + 1
   = 0 + 1
   = 1
 👻 blt t0, t1, loop
blt: t0 < t1 ?  1 < 3 ?  yes, branch taken
pc = loop = 0x00000008
[0x00000008] addi t0, t0, 1
t0 = t0 + 1
   = 1 + 1
   = 2
blt: t0 < t1 ?  2 < 3 ?  yes, branch taken
pc = loop = 0x00000008
[0x00000008] addi t0, t0, 1
t0 = t0 + 1
   = 2 + 1
   = 3
blt: t0 < t1 ?  3 < 3 ?  no, branch not taken
pc = pc + 4 = 0x00000010
 👻 sub t1, x0, t0
t1 = x0 - t0
   = 0 - 3
   = -3
 👻 sw t1, 0(a0)
mem[a0 + 0] = t1  (word)
            = 0xfffffffd written to addr 0x00000000
 👻 lhu t2, 0(a0)
t2 = mem[a0 + 0]  (half)
   = mem[0x00000000]
   = 0xfffd zero extended
   = 0x0000fffd (65533)
 👻 addi t2, t2, 0x1234
immediate should fit in 12 bits (-2048 to 2047)
  but 0x1234 doesn't
=== invalid inst ===
```

## How branches and jumps work

Every instruction you type is stored in instruction memory, starting at address 0, and then executed. riiip keeps running from the PC until it reaches the end of what you've typed. This is how control flow works in a shell:

* **Backward branches and jumps (loops).** riiip replays the stored instructions from the target, showing each one with its address, until the PC is back at the end of your program. After 30 instructions it stops explaining each one and prints a summary of the registers that changed. After 10000 it stops and asks if you have an infinite loop.
* **Forward branches and jumps.** If the target label isn't defined yet, the instructions you type next are stored but *skipped*, just like the CPU would skip them, until you define the label. Then execution resumes there. For example, `jal ra, func` then `j end` then `func:` jumps to `func`. A `ret` later returns to the stored `j end`.
* Branch and jump targets can be labels (`loop`) or byte offsets from the PC (`beq t0, t1, -8`).
* Typing a label then an instruction on one line works too: `loop: addi t0, t0, 1`.
* `ebreak` pauses a running program. `run` continues it, and `step` runs one instruction at a time. `reset pc` then `run` replays your whole program from the start.
* `load file.s` (or `python3 riiip file.s`) types in every line of an assembly file for you. Assembler directives like `.text` are ignored.

Instructions live in their own memory, separate from data, so a store to address 0 can't overwrite your program. Unlike jumps, `la` needs its label to already be defined.

## Commands

```
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
      pc        reset PC to 0 (then 'run' replays your program)
```

## Version 1.2

This version supports the full **RV32IM** instruction set: the 32-bit RISCV base integer ISA plus the multiply / divide extension.

**R-TYPE arithmetic instructions and their I-TYPE equivalents.** "add", "and", "or", "sll", "slt", "sltu", "sra", "srl", "sub", "xor", "addi", "andi", "ori", "slli", "slti", "sltiu", "srai", "srli", "xori".

**Upper immediates.** "lui", "auipc".

**Memory instructions.** "lb", "lbu", "lh", "lhu", "lw", "sb", "sh", "sw".

👻 **Branches!** "beq", "bne", "blt", "bge", "bltu", "bgeu".

👻 **Jumps!** "jal", "jalr".

👻 **Multiply and divide (M extension)!** "mul", "mulh", "mulhsu", "mulhu", "div", "divu", "rem", "remu". Division by zero and overflow follow the spec: they don't trap.

👻 **System.** "ecall", "ebreak", "fence". `ecall` follows the [venus](https://venus.cs61c.org) convention. a0 picks the call and a1 is its argument: 1 print_int, 4 print_string, 9 sbrk, 10 exit, 11 print_char, 17 exit with code a1.

👻 **Pseudo instructions.** "li" (any 32-bit value, using lui + addi when needed), "la", "mv", "nop", "not", "neg", "seqz", "snez", "sltz", "sgtz", "beqz", "bnez", "blez", "bgez", "bltz", "bgtz", "bgt", "ble", "bgtu", "bleu", "j", "jal label", "jr", "jalr rs", "ret", "call", "tail". riiip shows what each one expands to.

riiip also points out tricky edge cases as they happen: overflow, sign extension of immediates and loads, `sltiu` with negative immediates, shifts that only use the lowest 5 bits, writes to x0, and misaligned addresses.

Not supported: CSR instructions (Zicsr), atomics (A), floating point (F/D), compressed instructions (C), and 64-bit RISCV.

## Tests

```bash
python3 -m unittest test_riiip
```

To update:

```bash
cd riiip
git pull origin main
```

## References

[The RISCV Greencard](https://inst.eecs.berkeley.edu/~cs61c/fa17/img/riscvcard.pdf)