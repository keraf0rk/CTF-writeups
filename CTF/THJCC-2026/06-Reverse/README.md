<a id="en"></a>
# 06 — 404
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔧 Reverse |
| **Challenge file** | [`404`](404) (ELF 64-bit, static, stripped) |
| **Solve script** | [`solve.py`](solve.py) |
| **Status** | ✅ Solved |
| **Flag** | `THJCC{vm_bytecode_is_a_contract}` |

## 1. Description

One binary named `404`, no description. It wants a 16-byte argument.

```
usage: 404 <16-byte input>
```

## 2. Initial analysis

```bash
file 404          # ELF 64-bit LSB executable, x86-64, statically linked, stripped
ls -l 404         # 2104 bytes
readelf -SW 404
strings -n 5 404  # "vm rejected input"
```

- 2 KB total, `.text` is `0x3E3` and `.rodata` is `0x1AF` — almost half the image
  is data. In a binary this small that ratio only makes sense if the data *is*
  the program.
- The string `vm rejected input` names the design outright: a bytecode
  interpreter, same family as [`03-Reverse`](../03-Reverse/).

## 3. Investigation path

**What I confirmed**

- `0x20130D`–`0x2013ED` is an uninterrupted run of `movaps xmm0, [rip + X]` /
  `movaps [rsp + D], xmm0` pairs closed by `mov byte [rsp + 0xB0], 7`. It
  assembles `0x121` bytes of bytecode on the stack from `.rodata` chunks **in
  scrambled order**.
- `0x201427` is `jmp qword [r9*8 + 0x200240]` — an 8-entry handler table. Every
  VM instruction is 3 bytes:

| Opcode | Handler | Meaning |
|---|---|---|
| 1 | `0x20142F` | `reg[b] = input[c]` (b < 8, c < 16) |
| 2 | `0x2014EE` | `reg[b] ^= imm` |
| 3 | `0x201494` | `reg[b] += imm` |
| 4 | `0x2014B7` | `reg[b] = rol8(reg[b], imm & 7)` |
| 5 | `0x201465` | `flag = (reg[b] == imm)` |
| 6 | `0x201523` | `if not flag: reject` |
| 7 | `0x201615` | **print the flag** |
| 8 | `0x20150A` | relative jump |

- The program is 16 identical 18-byte blocks plus a trailing `07`:

```
01 00 00   LOAD  r0 = input[0]
02 00 20   XOR   r0 ^= 0x20
03 00 07   ADD   r0 += 0x07
04 00 00   ROL   r0 <<< 0
05 00 5d   CMP   r0 == 0x5D
06 00 00   CHECK
```

- Each block reads exactly one input byte, so the accepted argument inverts
  directly: `in[i] = (ror8(target, rot) - add) ^ xor` → `vm_is_not_magic!`
  (verified by replaying the forward transformation).
- Opcode 7 decodes a `.rodata` blob at VA `0x200280` with a rolling XOR (seed
  `0x35`, step `0x1A`, even byte of each pair against `key - 0x0D`), 32 bytes —
  the same construction as [`05-Reverse`](../05-Reverse/) and
  [`07-Reverse`](../07-Reverse/).

**The insight that solved it**

- The win condition is an *opcode*. Once I enumerated the handler table before
  touching the bytecode, "reverse the program" became "find which opcode prints
  the flag" — and that one needs no valid input at all. (One thing I had to get
  right: dumping `.rodata` linearly as bytecode gives garbage, because the loader
  writes 16-byte chunks to the stack out of order, so I replayed the loader
  rather than reading the data straight.)

## 4. Tools & commands

```bash
pip install capstone loguru

# Full .text disassembly
python3 - <<'PY'
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
blob = open("404", "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_64)
for insn in md.disasm(blob[0x2d0:0x2d0 + 0x3e3], 0x2012d0):
    print(f"{insn.address:#x}\t{insn.mnemonic}\t{insn.op_str}")
PY

python3 solve.py                 # flag only — no capstone needed
python3 solve.py --recover-input # also rebuild the accepted argv[1]
```

See [`solve.py`](solve.py).

## 5. Step-by-step

1. `file` / `readelf` showed a 2 KB static stripped ELF, `.rodata` nearly half
   the image.
2. I disassembled `.text` and found the `movaps` loader and the `jmp [table]`
   dispatch.
3. I replayed the loader to rebuild `0x121` bytes of bytecode (order matters).
4. I recovered the 8-opcode table from the jump table at `0x200240`.
5. I parsed the bytecode → 16 × `LOAD/XOR/ADD/ROL/CMP/CHECK` + opcode `07`.
6. I inverted each block → `vm_is_not_magic!` and replayed it forward to confirm.
7. I decoded the `.rodata` blob at VA `0x200280` → the flag.

## 6. Solution

```
$ python3 solve.py --recover-input
INFO    loaded 404 (2104 bytes)
INFO    rebuilt 289 bytes of vm bytecode
SUCCESS accepted argv[1] = vm_is_not_magic!
INFO    flag blob: VA 0x200280 -> file offset 0x280, 32 bytes
SUCCESS flag = THJCC{vm_bytecode_is_a_contract}
SUCCESS matches the known-good flag
```

Both halves are confirmed: the recovered input passes the VM's own forward
transformation, and the flag is the constant opcode 7 prints.

## 7. Flag

```
THJCC{vm_bytecode_is_a_contract}
```

## 8. Key takeaways

- **The signal:** `.rodata` comparable in size to `.text`, plus a string like
  `vm rejected input`. Find the dispatch — `jmp qword [reg*8 + addr]` is the
  giveaway — and the opcode table falls out in minutes.
- **Why it worked:** per-byte independence again (as in
  [`03-Reverse`](../03-Reverse/)), so inversion is arithmetic rather than search;
  and the flag turned out to be a constant reachable without any valid input.
- **What I'll remember:** read the opcode table before the bytecode. If a
  handler writes to stdout, that is the whole challenge.

---

<a id="ru"></a>
# 06 — 404
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔧 Reverse |
| **Файл задания** | [`404`](404) (ELF 64-bit, статика, stripped) |
| **Solve-скрипт** | [`solve.py`](solve.py) |
| **Статус** | ✅ Решено |
| **Флаг** | `THJCC{vm_bytecode_is_a_contract}` |

## 1. Условие

Один бинарь с именем `404`, описания нет. Ждёт 16-байтный аргумент.

```
usage: 404 <16-byte input>
```

## 2. Первичный анализ

```bash
file 404          # ELF 64-bit LSB executable, x86-64, statically linked, stripped
ls -l 404         # 2104 байта
readelf -SW 404
strings -n 5 404  # "vm rejected input"
```

- 2 КБ целиком, `.text` — `0x3E3`, `.rodata` — `0x1AF`, то есть почти половина
  образа это данные. В бинаре такого размера такое соотношение имеет смысл
  только если данные *и есть* программа.
- Строка `vm rejected input` называет архитектуру прямым текстом: интерпретатор
  байткода, то же семейство, что и [`03-Reverse`](../03-Reverse/).

## 3. Путь исследования

**Что я подтвердил**

- Диапазон `0x20130D`–`0x2013ED` — непрерывная серия пар
  `movaps xmm0, [rip + X]` / `movaps [rsp + D], xmm0`, закрытая
  `mov byte [rsp + 0xB0], 7`. Она собирает на стеке `0x121` байт байткода из
  кусков `.rodata` **в перемешанном порядке**.
- По адресу `0x201427` стоит `jmp qword [r9*8 + 0x200240]` — таблица из 8
  обработчиков. Каждая инструкция VM занимает 3 байта:

| Опкод | Обработчик | Смысл |
|---|---|---|
| 1 | `0x20142F` | `reg[b] = input[c]` (b < 8, c < 16) |
| 2 | `0x2014EE` | `reg[b] ^= imm` |
| 3 | `0x201494` | `reg[b] += imm` |
| 4 | `0x2014B7` | `reg[b] = rol8(reg[b], imm & 7)` |
| 5 | `0x201465` | `flag = (reg[b] == imm)` |
| 6 | `0x201523` | `if not flag: reject` |
| 7 | `0x201615` | **печать флага** |
| 8 | `0x20150A` | относительный переход |

- Программа — 16 одинаковых блоков по 18 байт и завершающий `07`:

```
01 00 00   LOAD  r0 = input[0]
02 00 20   XOR   r0 ^= 0x20
03 00 07   ADD   r0 += 0x07
04 00 00   ROL   r0 <<< 0
05 00 5d   CMP   r0 == 0x5D
06 00 00   CHECK
```

- Каждый блок читает ровно один байт ввода, поэтому принимаемый аргумент
  обращается напрямую: `in[i] = (ror8(target, rot) - add) ^ xor` →
  `vm_is_not_magic!` (проверено прогоном прямого преобразования).
- Опкод 7 декодирует блоб `.rodata` по VA `0x200280` бегущим XOR-ом (старт
  `0x35`, шаг `0x1A`, чётный байт пары против `key - 0x0D`), 32 байта — та же
  конструкция, что в [`05-Reverse`](../05-Reverse/) и
  [`07-Reverse`](../07-Reverse/).

**Идея, которая решила задачу**

- Условие победы — это *опкод*. Как только я перечислил таблицу обработчиков до
  разбора байткода, «отреверсить программу» превратилось в «найти опкод, который
  печатает флаг», а ему валидный ввод вообще не нужен. (Одно пришлось учесть:
  линейный дамп `.rodata` как байткода даёт мусор, потому что загрузчик пишет
  16-байтные куски на стек не по порядку, — поэтому я воспроизвёл загрузчик, а не
  читал данные напрямую.)

## 4. Инструменты и команды

```bash
pip install capstone loguru

# Полный дизассемблер .text
python3 - <<'PY'
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
blob = open("404", "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_64)
for insn in md.disasm(blob[0x2d0:0x2d0 + 0x3e3], 0x2012d0):
    print(f"{insn.address:#x}\t{insn.mnemonic}\t{insn.op_str}")
PY

python3 solve.py                 # только флаг — capstone не нужен
python3 solve.py --recover-input # ещё и восстановить argv[1]
```

См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. `file` / `readelf` показали 2 КБ, статический stripped ELF, `.rodata` почти
   половина образа.
2. Дизассемблировал `.text` и нашёл `movaps`-загрузчик и диспетчер `jmp [table]`.
3. Воспроизвёл загрузчик и собрал `0x121` байт байткода (порядок важен).
4. Восстановил таблицу из 8 опкодов по таблице переходов `0x200240`.
5. Разобрал байткод → 16 × `LOAD/XOR/ADD/ROL/CMP/CHECK` + опкод `07`.
6. Обратил каждый блок → `vm_is_not_magic!` и прогнал вперёд для проверки.
7. Декодировал блоб `.rodata` по VA `0x200280` → флаг.

## 6. Итоговое решение

```
$ python3 solve.py --recover-input
INFO    loaded 404 (2104 bytes)
INFO    rebuilt 289 bytes of vm bytecode
SUCCESS accepted argv[1] = vm_is_not_magic!
INFO    flag blob: VA 0x200280 -> file offset 0x280, 32 bytes
SUCCESS flag = THJCC{vm_bytecode_is_a_contract}
SUCCESS matches the known-good flag
```

Подтверждены обе половины: восстановленный ввод проходит прямое преобразование
самой VM, а флаг — константа, которую печатает опкод 7.

## 7. Флаг

```
THJCC{vm_bytecode_is_a_contract}
```

## 8. Ключевые выводы

- **Что было сигналом:** `.rodata`, сопоставимая по размеру с `.text`, плюс
  строка вроде `vm rejected input`. Найдите диспетчер — его выдаёт
  `jmp qword [reg*8 + addr]` — и таблица опкодов восстанавливается за минуты.
- **Почему сработало:** снова независимость по байтам (как в
  [`03-Reverse`](../03-Reverse/)), поэтому обращение — арифметика, а не перебор;
  а флаг оказался константой, доступной вообще без валидного ввода.
- **Что запомню:** читать таблицу опкодов раньше байткода. Если какой-то
  обработчик пишет в stdout — это и есть всё задание.
