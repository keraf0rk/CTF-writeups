<a id="en"></a>
# 07 — xorlocks
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔧 Reverse |
| **Challenge file** | [`xorlock`](xorlock) (ELF 64-bit, static, stripped) |
| **Solve script** | [`solve.py`](solve.py) |
| **Status** | ✅ Solved |
| **Flag** | `THJCC{xor_basics_are_not_magic}` |

## 1. Description

One binary, `xorlock`, that takes a password and prints `access denied` on
failure.

```
usage: xorlock <password>
```

## 2. Initial analysis

```bash
file xorlock          # ELF 64-bit LSB executable, x86-64, statically linked, stripped
ls -l xorlock         # 1256 bytes
readelf -SW xorlock
strings -n 5 xorlock  # "access denied"
```

- 1256 bytes, `.text` is only `0x1D3`. This is the smallest member of the
  author's trio — see [`05-Reverse`](../05-Reverse/) and
  [`06-Reverse`](../06-Reverse/) — and the entire check fits on one screen.

## 3. Investigation path

**Confirmed**

- `0x2011BA` requires `strlen == 20`.
- The comparison loop at `0x2011D0` is four instructions long:

```asm
movzx esi, byte ptr [rax + rdx]       ; password[i]
xor   sil, 0x5a                       ; ^ 0x5A
add   sil, cl                         ; + 3*i   (cl starts at 0, += 3 per byte)
movzx edi, byte ptr [rdx + 0x200150]  ; table[i]
cmp   sil, dil
```

  i.e. `((password[i] ^ 0x5A) + 3 * i) & 0xFF == table[i]`, which inverts to
  `password[i] = ((table[i] - 3 * i) & 0xFF) ^ 0x5A` → `xor_me_if_you_can_26`
  (confirmed by replaying the forward check).
- The success branch at `0x2011FD` decodes a fixed `.rodata` blob at VA
  `0x200170` — rolling XOR, seed `0x40`, step `0x1A`, even byte of each pair
  against `key - 0x0D`, 31 bytes — exactly as in the sibling challenges.

**Key insight**

- A position-dependent XOR is still a closed-form bijection. The `+ 3*i` term
  only *looks* like it adds strength; subtracting it back costs one line.

## 4. Tools & commands

```bash
pip install capstone loguru

# Full .text disassembly (0x1D3 bytes)
python3 - <<'PY'
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
blob = open("xorlock", "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_64)
for insn in md.disasm(blob[0x190:0x190 + 0x1d3], 0x201190):
    print(f"{insn.address:#x}\t{insn.mnemonic}\t{insn.op_str}")
PY

python3 solve.py
./xorlock xor_me_if_you_can_26        # on an x86-64 Linux host
```

See [`solve.py`](solve.py).

## 5. Step-by-step

1. `file` / `readelf` → 1256-byte static stripped ELF, `.rodata` + `.text`.
2. Disassemble all `0x1D3` bytes of `.text`.
3. Read `0x2011BA` → the password is exactly 20 characters.
4. Read the loop at `0x2011D0` → `((p[i] ^ 0x5A) + 3*i) & 0xFF == table[i]`.
5. Invert against the table at VA `0x200150` → `xor_me_if_you_can_26`.
6. Replay the forward check to confirm the inversion.
7. Decode the `.rodata` blob at VA `0x200170` (seed `0x40`) → the flag.

## 6. Solution

```
$ python3 solve.py
INFO    loaded xorlock (1256 bytes)
INFO    check table at VA 0x200150: 22382e0e434e174854204156532c636864389ea5
SUCCESS password = xor_me_if_you_can_26
SUCCESS flag = THJCC{xor_basics_are_not_magic}
SUCCESS matches the known-good password and flag
```

## 7. Flag

```
THJCC{xor_basics_are_not_magic}
```

## 8. Key takeaways

- **The signal:** a four-instruction comparison loop with one register
  incremented by a constant per iteration is a position-dependent XOR — always
  invertible in closed form. No search, no solver.
- **Why it worked:** inverting is two lines, and replaying the original direction
  on the recovered password removes any doubt about sign/mask/order mistakes.
- **False leads:** none worth the name here — but note the password is *not* the
  goal. As in [`05-Reverse`](../05-Reverse/) the flag is a constant blob; the
  password only gates the print.
- **Recognize it next time:** tiny static ELF + `access denied` + a `.rodata`
  table the same length as the expected input → invert the loop directly, then
  look for a second blob of flag length nearby. Across this author the flag
  decoder is always the same rolling XOR with step `0x1A`; only the seed changes
  (`0x7E` → `0x35` → `0x40` → `0x26`).

---

<a id="ru"></a>
# 07 — xorlocks
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔧 Reverse |
| **Файл задания** | [`xorlock`](xorlock) (ELF 64-bit, статика, stripped) |
| **Solve-скрипт** | [`solve.py`](solve.py) |
| **Статус** | ✅ Решено |
| **Флаг** | `THJCC{xor_basics_are_not_magic}` |

## 1. Условие

Один бинарь `xorlock`, принимающий пароль и печатающий `access denied` при
неудаче.

```
usage: xorlock <password>
```

## 2. Первичный анализ

```bash
file xorlock          # ELF 64-bit LSB executable, x86-64, statically linked, stripped
ls -l xorlock         # 1256 байт
readelf -SW xorlock
strings -n 5 xorlock  # "access denied"
```

- 1256 байт, `.text` всего `0x1D3`. Это самый маленький представитель авторской
  тройки — см. [`05-Reverse`](../05-Reverse/) и [`06-Reverse`](../06-Reverse/) —
  и вся проверка помещается на один экран.

## 3. Путь исследования

**Подтверждено**

- По адресу `0x2011BA` требуется `strlen == 20`.
- Цикл сравнения `0x2011D0` состоит из четырёх инструкций:

```asm
movzx esi, byte ptr [rax + rdx]       ; password[i]
xor   sil, 0x5a                       ; ^ 0x5A
add   sil, cl                         ; + 3*i   (cl стартует с 0, += 3 на байт)
movzx edi, byte ptr [rdx + 0x200150]  ; table[i]
cmp   sil, dil
```

  то есть `((password[i] ^ 0x5A) + 3 * i) & 0xFF == table[i]`, что обращается в
  `password[i] = ((table[i] - 3 * i) & 0xFF) ^ 0x5A` → `xor_me_if_you_can_26`
  (подтверждено прогоном прямой проверки).
- Ветка успеха `0x2011FD` декодирует фиксированный блоб `.rodata` по VA
  `0x200170` — бегущий XOR, старт `0x40`, шаг `0x1A`, чётный байт пары против
  `key - 0x0D`, 31 байт — ровно как в соседних заданиях.

**Ключевая идея**

- Позиционно-зависимый XOR всё равно остаётся биекцией в замкнутой форме.
  Слагаемое `+ 3*i` лишь *выглядит* как усиление; вычесть его обратно — одна
  строка.

## 4. Инструменты и команды

```bash
pip install capstone loguru

# Полный дизассемблер .text (0x1D3 байта)
python3 - <<'PY'
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
blob = open("xorlock", "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_64)
for insn in md.disasm(blob[0x190:0x190 + 0x1d3], 0x201190):
    print(f"{insn.address:#x}\t{insn.mnemonic}\t{insn.op_str}")
PY

python3 solve.py
./xorlock xor_me_if_you_can_26        # на хосте x86-64 Linux
```

См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. `file` / `readelf` → статический stripped ELF на 1256 байт, `.rodata` + `.text`.
2. Дизассемблируем все `0x1D3` байта `.text`.
3. Читаем `0x2011BA` → пароль ровно 20 символов.
4. Читаем цикл `0x2011D0` → `((p[i] ^ 0x5A) + 3*i) & 0xFF == table[i]`.
5. Обращаем относительно таблицы по VA `0x200150` → `xor_me_if_you_can_26`.
6. Прогоняем прямую проверку, чтобы подтвердить обращение.
7. Декодируем блоб `.rodata` по VA `0x200170` (старт `0x40`) → флаг.

## 6. Итоговое решение

```
$ python3 solve.py
INFO    loaded xorlock (1256 bytes)
INFO    check table at VA 0x200150: 22382e0e434e174854204156532c636864389ea5
SUCCESS password = xor_me_if_you_can_26
SUCCESS flag = THJCC{xor_basics_are_not_magic}
SUCCESS matches the known-good password and flag
```

## 7. Флаг

```
THJCC{xor_basics_are_not_magic}
```

## 8. Ключевые выводы

- **Что было сигналом:** цикл сравнения из четырёх инструкций, где один регистр
  увеличивается на константу каждую итерацию, — это позиционно-зависимый XOR,
  всегда обратимый в замкнутой форме. Ни перебора, ни солвера.
- **Почему сработало:** обращение занимает две строки, а прогон исходного
  направления на восстановленном пароле снимает сомнения насчёт ошибок в знаке,
  маске и порядке.
- **Ложные следы:** здесь настоящих не было — но стоит отметить, что пароль *не*
  является целью. Как и в [`05-Reverse`](../05-Reverse/), флаг — константный
  блоб, а пароль лишь открывает печать.
- **Как узнать в следующий раз:** крошечный статический ELF + `access denied` +
  таблица в `.rodata` длиной с ожидаемый ввод → обращайте цикл напрямую, затем
  ищите рядом второй блоб длиной с флаг. У этого автора декодер флага всегда один
  и тот же бегущий XOR с шагом `0x1A`; меняется только стартовый байт
  (`0x7E` → `0x35` → `0x40` → `0x26`).
