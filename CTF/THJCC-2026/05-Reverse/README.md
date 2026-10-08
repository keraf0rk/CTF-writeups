<a id="en"></a>
# 05 — License
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔧 Reverse |
| **Challenge file** | [`license_v2`](license_v2) (ELF 64-bit, static, stripped) |
| **Solve script** | [`solve.py`](solve.py) |
| **Status** | ✅ Solved |
| **Flag** | `THJCC{license_pipeline_rebuilt}` |

## 1. Description

A single binary that validates a license key and prints a reward on success. No
source, no symbols, no libc — everything is raw syscalls.

```
usage: license_v2 <license>
```

## 2. Initial analysis

```bash
file license_v2      # ELF 64-bit LSB executable, x86-64, statically linked, stripped
ls -l license_v2     # 3608 bytes
readelf -SW license_v2
strings -n 5 license_v2
```

- 3.6 KB total, two allocated sections only: `.rodata` (`0x10F`) and `.text`
  (`0xA63`). No import table, no dynamic linker — a hand-written, syscall-only
  binary, small enough to read end to end.
- Visible strings: `invalid license`, `usage: %s <license>`, and a suspicious
  `1111111111111111` — nothing resembling a flag, so the flag is encoded.

## 3. Investigation path

**Confirmed**

- The argument loop at `0x201264` keeps two counters in lockstep (`rcx = rdi + 1`)
  and tests `5 * floor(rcx / 5) - 1 == rdi`, which selects indexes 4, 9, 14, 19,
  24 for `'-'`. Everything else must be a hex digit. With `strlen == 29` the
  format is exactly `XXXX-XXXX-XXXX-XXXX-XXXX-XXXX` → 24 nibbles.
- The real validation is three stages: a `.rodata`-driven byte permutation with
  per-byte `xor`/`rol`/`add` (SSE block at `0x201410`), four diffusion rounds of
  the shape `new[i] = rol(((i + c) ^ K) ^ S[i] ^ S[(i + 7) % 24], shift)` with
  `K` ∈ {`0x13579BDF`, `0x2468ACE0`, `0x0BADF00D`, `0x55AA55AA`}, and a byte-wise
  comparison against 24 constants starting at `0x201A34`.
- The success branch at `0x201BC3` derives **nothing** from the key: it decodes a
  fixed `.rodata` blob at VA `0x200210` and writes it out.
- That decoder is a rolling XOR: key starts at `0x7E`, grows by `0x1A` per byte
  pair, the even byte of a pair is XOR-ed with `key - 0x0D`, the odd one with
  `key`; the loop stops at index `0x1F` → 31 bytes.

**Key insight**

- Reading the *win branch* before the validator collapses the whole challenge.
  The flag is a constant, so the three-stage pipeline never has to be inverted.

**False lead**

- At `0x201398` a hash is seeded with `0x31415926` and folded over the input with
  `xor`/`ror 29`. It looks like the check — but `0x2013F7` loads the result into
  `eax` and `0x201404` immediately does `xor eax, eax`. Dead code.

**Left to check**

- A *valid license key* was never produced. Inverting the four rounds is feasible
  (`gcd(7, 24) = 1` makes `S[i] ^ S[(i + 7) % 24]` a single 24-cycle, so each
  round inverts up to one global XOR byte, and the hex-only alphabet should pin
  the survivor), but it is not needed for the flag and was not carried out.

## 4. Tools & commands

```bash
pip install capstone loguru

# Full .text disassembly (0xA63 bytes — just dump all of it)
python3 - <<'PY'
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
blob = open("license_v2", "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_64)
for insn in md.disasm(blob[0x230:0x230 + 0xa63], 0x201230):
    print(f"{insn.address:#x}\t{insn.mnemonic}\t{insn.op_str}")
PY

# Lift the flag
python3 solve.py
python3 solve.py --check-key 'AAAA-BBBB-CCCC-DDDD-EEEE-FFFF'   # format check only
```

Pure-Python solver, no RE tooling needed at solve time. See [`solve.py`](solve.py).

## 5. Step-by-step

1. `file` / `readelf` → 3.6 KB static stripped ELF, `.rodata` + `.text` only.
2. Disassemble all of `.text`.
3. Read the argument loop → 29 chars, dashes at 4/9/14/19/24, hex elsewhere.
4. Spot the `0x31415926` hash and confirm its result is discarded.
5. Map the real pipeline: permutation → 4 diffusion rounds → 24 constants.
6. Notice the success branch decodes a fixed blob instead of using the key.
7. Parse the ELF section table, translate VA `0x200210` → file offset.
8. Undo the rolling XOR over 31 bytes → the flag.

## 6. Solution

```
$ python3 solve.py
INFO    loaded license_v2 (3608 bytes)
INFO    sections: .rodata, .text, .comment, .shstrtab
INFO    flag blob: VA 0x200210 -> file offset 0x210, 31 bytes
INFO    key format: 29 chars, '-' at 4, 9, 14, 19, 24, rest hex
INFO    note: the 0x31415926 hash at 0x201398 is computed but never used
SUCCESS flag = THJCC{license_pipeline_rebuilt}
SUCCESS matches the known-good flag
```

## 7. Flag

```
THJCC{license_pipeline_rebuilt}
```

## 8. Key takeaways

- **The signal:** when the success path builds its output from `.rodata` instead
  of from the validated input, the flag is a constant and the validator is
  decoration. Read the win branch first — it decides how much work the challenge
  actually requires.
- **Why it worked:** the flag decoder is a rolling XOR over a fixed blob, fully
  reproducible from the file. No key, no execution, no emulation.
- **False leads:** the `0x31415926` hash (result discarded two instructions
  later) and the intimidating SSE diffusion rounds, which never touch the flag.
- **Recognize it next time:** static, stripped, syscall-only ELF of a few KB with
  a `.rodata` blob roughly the length of a flag → look for a rolling-XOR decoder
  near the success branch before reversing any validation. The same author reuses
  this exact construction in [`06-Reverse`](../06-Reverse/),
  [`07-Reverse`](../07-Reverse/) and [`09-Reverse`](../09-Reverse/); only the
  seed changes.

---

<a id="ru"></a>
# 05 — License
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔧 Reverse |
| **Файл задания** | [`license_v2`](license_v2) (ELF 64-bit, статика, stripped) |
| **Solve-скрипт** | [`solve.py`](solve.py) |
| **Статус** | ✅ Решено |
| **Флаг** | `THJCC{license_pipeline_rebuilt}` |

## 1. Условие

Один бинарь, который проверяет лицензионный ключ и при успехе печатает награду.
Ни исходников, ни символов, ни libc — только голые syscall-ы.

```
usage: license_v2 <license>
```

## 2. Первичный анализ

```bash
file license_v2      # ELF 64-bit LSB executable, x86-64, statically linked, stripped
ls -l license_v2     # 3608 байт
readelf -SW license_v2
strings -n 5 license_v2
```

- 3.6 КБ целиком, только две загружаемые секции: `.rodata` (`0x10F`) и `.text`
  (`0xA63`). Ни таблицы импортов, ни динамического линкера — рукописный бинарь на
  syscall-ах, достаточно маленький, чтобы прочитать целиком.
- Видимые строки: `invalid license`, `usage: %s <license>` и подозрительная
  `1111111111111111` — ничего похожего на флаг, значит флаг закодирован.

## 3. Путь исследования

**Подтверждено**

- Цикл по аргументу `0x201264` ведёт два синхронных счётчика (`rcx = rdi + 1`) и
  проверяет `5 * floor(rcx / 5) - 1 == rdi`, что отбирает индексы 4, 9, 14, 19,
  24 под `'-'`. Всё остальное обязано быть hex-цифрой. Вместе с `strlen == 29`
  формат ровно `XXXX-XXXX-XXXX-XXXX-XXXX-XXXX` → 24 ниббла.
- Настоящая валидация трёхстадийная: перестановка байт по таблице из `.rodata` с
  побайтовыми `xor`/`rol`/`add` (SSE-блок `0x201410`), четыре раунда диффузии вида
  `new[i] = rol(((i + c) ^ K) ^ S[i] ^ S[(i + 7) % 24], shift)` с
  `K` ∈ {`0x13579BDF`, `0x2468ACE0`, `0x0BADF00D`, `0x55AA55AA`} и побайтовое
  сравнение с 24 константами, начиная с `0x201A34`.
- Ветка успеха `0x201BC3` **ничего** не выводит из ключа: она декодирует
  фиксированный блоб `.rodata` по VA `0x200210` и печатает его.
- Этот декодер — бегущий XOR: ключ стартует с `0x7E`, растёт на `0x1A` на пару
  байт, чётный байт пары XOR-ится с `key - 0x0D`, нечётный — с `key`; цикл
  останавливается на индексе `0x1F` → 31 байт.

**Ключевая идея**

- Чтение *ветки победы* раньше валидатора схлопывает всё задание: флаг — это
  константа, и трёхстадийный конвейер обращать не нужно вовсе.

**Ложный след**

- По адресу `0x201398` хеш инициализируется значением `0x31415926` и
  сворачивается по вводу через `xor`/`ror 29`. Выглядит как проверка — но
  `0x2013F7` кладёт результат в `eax`, а `0x201404` тут же делает `xor eax, eax`.
  Мёртвый код.

**Осталось проверить**

- Валидный лицензионный ключ так и не был получен. Обратить четыре раунда
  реально (`gcd(7, 24) = 1` делает `S[i] ^ S[(i + 7) % 24]` одним циклом длины
  24, поэтому каждый раунд обращается с точностью до одного глобального
  XOR-байта, а hex-алфавит должен отсеять лишних), но для флага это не нужно и
  сделано не было.

## 4. Инструменты и команды

```bash
pip install capstone loguru

# Полный дизассемблер .text (0xA63 байта — проще вывалить целиком)
python3 - <<'PY'
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
blob = open("license_v2", "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_64)
for insn in md.disasm(blob[0x230:0x230 + 0xa63], 0x201230):
    print(f"{insn.address:#x}\t{insn.mnemonic}\t{insn.op_str}")
PY

# Достать флаг
python3 solve.py
python3 solve.py --check-key 'AAAA-BBBB-CCCC-DDDD-EEEE-FFFF'   # только формат
```

Солвер на чистом Python, RE-инструменты на этапе решения не нужны.
См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. `file` / `readelf` → 3.6 КБ, статический stripped ELF, только `.rodata` и `.text`.
2. Дизассемблируем весь `.text`.
3. Читаем цикл по аргументу → 29 символов, дефисы на 4/9/14/19/24, остальное hex.
4. Замечаем хеш `0x31415926` и убеждаемся, что результат выбрасывается.
5. Размечаем настоящий конвейер: перестановка → 4 раунда диффузии → 24 константы.
6. Замечаем, что ветка успеха декодирует фиксированный блоб, а не использует ключ.
7. Разбираем таблицу секций ELF, переводим VA `0x200210` в смещение в файле.
8. Снимаем бегущий XOR с 31 байта → флаг.

## 6. Итоговое решение

```
$ python3 solve.py
INFO    loaded license_v2 (3608 bytes)
INFO    sections: .rodata, .text, .comment, .shstrtab
INFO    flag blob: VA 0x200210 -> file offset 0x210, 31 bytes
INFO    key format: 29 chars, '-' at 4, 9, 14, 19, 24, rest hex
INFO    note: the 0x31415926 hash at 0x201398 is computed but never used
SUCCESS flag = THJCC{license_pipeline_rebuilt}
SUCCESS matches the known-good flag
```

## 7. Флаг

```
THJCC{license_pipeline_rebuilt}
```

## 8. Ключевые выводы

- **Что было сигналом:** если ветка успеха собирает вывод из `.rodata`, а не из
  проверенного ввода, значит флаг — константа, а валидатор — декорация. Читайте
  ветку победы первой: именно она определяет, сколько работы реально нужно.
- **Почему сработало:** декодер флага — бегущий XOR по фиксированному блобу,
  полностью воспроизводимый из файла. Ни ключа, ни запуска, ни эмуляции.
- **Ложные следы:** хеш `0x31415926` (результат выбрасывается через две
  инструкции) и пугающие SSE-раунды диффузии, которые к флагу не прикасаются.
- **Как узнать в следующий раз:** статический stripped ELF на несколько КБ,
  только syscall-ы и блоб в `.rodata` длиной примерно с флаг → сначала ищите
  rolling-XOR-декодер рядом с веткой успеха и только потом реверсьте валидацию.
  Тот же автор переиспользует ровно эту конструкцию в
  [`06-Reverse`](../06-Reverse/), [`07-Reverse`](../07-Reverse/) и
  [`09-Reverse`](../09-Reverse/); меняется только стартовый байт.
