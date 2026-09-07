#!/usr/bin/env python3

import secrets
from Crypto.Util.number import getPrime, bytes_to_long

# place the flag obtained in TFCCTF{}
msg = b"?"
n = 57
B = 32
base = B + 1
p = getPrime(1084)

x = bytes_to_long(msg)
row = []
while x:
    row.append(x % base)
    x //= base
if not row:
    row = [0]

m = len(row)
#print(m)
assert n < m
a = [secrets.randbelow(p) for _ in range(n)]
A = [[secrets.randbelow(base) for _ in range(m)] for _ in range(n)]
planted_idx = secrets.randbelow(n)
A[planted_idx] = row[:]

h = [
    sum(a[i] * A[i][j] for i in range(n)) % p
    for j in range(m)
]

print(f"n = {n}")
print(f"m = {m}")
print(f"B = {B}")
print(f"p = {p}")
print(f"h = {h}")