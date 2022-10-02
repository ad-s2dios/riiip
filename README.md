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
👻 Welcome to riiip 1.1! 👻

initializing cpu...
all registers set to 0
PC set to 0
mem: empty mem initialized

 👻 li t0, 42
ie addi t0 , x0, 42
t0  = 42
 👻 sub t1, x0, t0
t1  = 0 - 42
    = -42
 👻 sw t1, 0(a0)
ffffffd6 written to addr 0
 👻 lhu t2, 0(a0)
0000ffff read to t2
 👻 addi t2, t2, 0x1234
I_TYPE: immediate should have len <= 12 bits
        but 0x1234 exceeds this
=== invalid inst ===
 👻 help
<register>  get register value (eg 't0' or 'x5')
pc          get current PC
mem         get memory dictionary
exit        exit riiip
reset < >
      all   reset cpu and memory entirely
      reg   reset all registers to 0
      mem   reset all memory to 0
      pc    reset PC to 0
```

## Version 1.1

This version supports:

**32-bit RISCV**

**R-TYPE arithmetic instructions and their I-TYPE equivalents.** "add", "and", "or", "sll", "slt", "sltu", "sra", "srl", "sub", "xor", "addi", "andi", "ori", "slli", "slti", "sltiu", "srai", "srli", "xori".

👻 **Some Pseudo instructions!** "li", "mv", "nop"

👻 **Memory instructions!** "lb", "lbu", "lh", "lhu", "lw", "sb", "sh", "sw".

To update:

```bash
cd riiip
git pull origin main
```

## References

[The RISCV Greencard](https://inst.eecs.berkeley.edu/~cs61c/fa17/img/riscvcard.pdf)