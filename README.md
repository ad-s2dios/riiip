# riiip: RISCV Interactive Interpreter in Python

The main goal of riiip is to make learning RISCV easy! It does so with a shell-like interactive interpreter inspired by Python. Instructions print helpful messages as they execute. For now, riiip is built entirely in python and interprets 32-bit RISCV.

## Using riiip

```bash
git clone https://github.com/ad-s2dios/riiip.git
python3 riiip
```

## Example

```
Welcome to riiip 1.1!

initializing cpu...
all registers set to 0
PC set to 0

riiip$ t0
t0 : 0x 00000000    0
riiip$ addi t0, x0, 42
t0  = 0 + 42
    = 42
riiip$ sub t1, x0, t0
t1  = 0 - 42
    = -42
riiip$ t0
t0 : 0x 0000002a    42
riiip$ t1
t1 : 0x ffffffd6    -42
riiip$ addi a0, x0, 9000
do: immediate should have len <= 12 bits
    but 9000 exceeds this
===== ERROR =====
riiip$ 
```

## Version 1.1

This version supports:

R-TYPE arithmetic instructions and their I-TYPE equivalents. ie "add", "and", "or", "sll", "slt", "sltu", "sra", "srl", "sub", "xor", "addi", "andi", "ori", "slli", "slti", "sltiu", "srai", "srli", "xori".

Memory instructions. ie "lb", "lbu", "lh", "lhu", "lw", "sb", "sh", "sw".

## References

[The RISCV Greencard](https://inst.eecs.berkeley.edu/~cs61c/fa17/img/riscvcard.pdf)