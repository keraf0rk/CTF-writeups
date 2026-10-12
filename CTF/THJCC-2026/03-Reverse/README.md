<a id="en"></a>
# 03 — Because There is no one Make Reverse So I Create This Chal
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔧 Reverse |
| **Challenge file** | `chal` (Mach-O 64-bit arm64, PIE) |
| **Status** | ✅ Solved |
| **Flag** | `THJCC{1_w0nd3r_h0w_l0n6_41_50lv35_17_>w<}` |

## 1. Description

A single stripped arm64 Mach-O binary. Run it, feed a string, and it tells you
whether the input is the flag. No source, no symbols — pure reverse engineering.

## 2. Initial analysis

```bash
file chal          # Mach-O 64-bit arm64 executable, PIE
```

- I saw that the check logic is **not** in plain arm64. The binary carries a
  blob in `__TEXT,__const` that gets decrypted at runtime and then interpreted —
  i.e. it runs a tiny custom **bytecode VM**, and the real comparison logic
  lives in that bytecode, not in native instructions.
- I also found that before running the program the binary verifies the
  decrypted blob against a hard-coded **FNV-1a 32-bit** checksum
  (`0x4B9FB9F7`). I took that constant as my anchor: once my decryption
  reproduces it, I know the payload is correct.

## 3. Investigation path

**Confirmed**

- `__TEXT,__const` holds a `0x2C4` (708) byte ciphertext followed by two 16-byte
  key halves. The effective XTEA key is `key_a XOR key_b` (the two halves
  `XOR`-ed word by word).
- The payload is a **keystream cipher**: for each 8-byte block index `i` the
  binary computes `XTEA_encipher(i + 0xAFD9E340, 0x1E403058, key)` and XORs the
  result over the ciphertext (standard XTEA, 32 rounds, delta `0x9E3779B9`).
- Decrypted payload passes FNV-1a == `0x4B9FB9F7` → decryption is correct.
- The payload is a flat opcode stream. Each flag position gets its own
  **transformation chain** (`+`, `-`, `^`, `rol`) terminated by a `==`
  comparison against a constant. `OP_CHECK_LEN` (`0xCD`) encodes the flag length.

**The insight that made it easy**

- I noticed every byte is checked **independently** (one chain per position, no
  cross-byte mixing). So each position is a 1-byte equation: I run all 256
  candidates through the chain and keep the one whose output hits the target
  constant. No real "cracking" needed.

## 4. Tools & commands

```bash
# Static look (optional)
file chal

# Decrypt payload, verify checksum, brute-force the flag
python3 solve.py            # uses ./chal by default
python3 solve.py ./chal     # explicit path
```

Pure-Python solver — no external RE tooling required. See [`solve.py`](solve.py).

## 5. Step-by-step

1. I parsed the Mach-O load commands, located `__TEXT,__const` and read its
   bytes.
2. I split it: `ciphertext = body[:0x2C4]`, then the two 4-word key halves right
   after it; `key = key_a ^ key_b`.
3. I rebuilt the keystream block by block with
   `XTEA(block + 0xAFD9E340, 0x1E403058, key)` and XORed it over the ciphertext.
4. I confirmed `fnv1a_32(payload) == 0x4B9FB9F7`.
5. I walked the bytecode: `SET_PTR` selects the current flag index,
   `ADD/SUB/XOR/ROL` append to that index's chain, `CHECK` records the target
   constant, `CHECK_LEN` gives the length.
6. For each position I ran `candidate in range(256)` through the chain (minus
   the final `==`) and kept the one matching the target.
7. I joined the recovered bytes → the flag.

## 6. Solution

When I ran the solver against the provided binary:

```
$ python3 solve.py
INFO     XTEA key: 0x2580f501 0xd194e025 0x9f48ceeb 0x05488ea6
INFO     FNV-1a of payload: 0x4b9fb9f7 (expected 0x4b9fb9f7)
INFO     VM expects 41 input bytes
SUCCESS  FLAG: THJCC{1_w0nd3r_h0w_l0n6_41_50lv35_17_>w<}
```

## 7. Flag

```
THJCC{1_w0nd3r_h0w_l0n6_41_50lv35_17_>w<}
```

## 8. Key takeaways

- **The signal:** a decrypted-at-runtime blob plus a self-checksum (FNV-1a here)
  screams "bytecode VM / packed check". Treat the checksum constant as a free
  oracle — reproduce it and you've validated your decryption before touching the
  logic.
- **Why it worked:** the VM checks each byte through an isolated chain, so the
  keyspace collapses from `256^41` to `41 × 256`. Independent per-byte checks are
  the classic weakness of hand-rolled "VM" validators.
- **False leads:** trying to brute the input against the whole program, or
  chasing native arm64 disassembly — the native code is just the VM loop; the
  logic is in the decrypted bytecode.
- **Recognize it next time:** `__TEXT,__const` / `.rodata` blob + XTEA/TEA
  constant `0x9E3779B9` + a rolling keystream = decrypt-then-interpret. Rebuild
  the keystream, verify with the embedded hash, then model the opcode handlers.

---

<a id="ru"></a>
# 03 — Because There is no one Make Reverse So I Create This Chal
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔧 Reverse |
| **Файл задания** | `chal` (Mach-O 64-bit arm64, PIE) |
| **Статус** | ✅ Solved |
| **Флаг** | `THJCC{1_w0nd3r_h0w_l0n6_41_50lv35_17_>w<}` |

## 1. Условие

Один stripped-бинарник arm64 Mach-O. Запускаешь, вводишь строку — он говорит,
флаг это или нет. Ни исходников, ни символов — чистый реверс.

## 2. Первичный анализ

```bash
file chal          # Mach-O 64-bit arm64 executable, PIE
```

- Я увидел, что логика проверки **не** в обычном arm64. В `__TEXT,__const`
  лежит блоб, который в рантайме расшифровывается и затем интерпретируется — то
  есть бинарник гоняет крошечную собственную **байткод-ВМ**, и настоящая
  проверка живёт в этом байткоде, а не в нативных инструкциях.
- Ещё я нашёл, что перед запуском бинарник сверяет расшифрованный блоб с зашитой
  контрольной суммой **FNV-1a 32-bit** (`0x4B9FB9F7`). Эту константу я взял за
  якорь: как только моя расшифровка её воспроизводит, payload точно верный.

## 3. Путь исследования

**Подтверждено**

- В `__TEXT,__const` лежит шифртекст `0x2C4` (708) байт, за ним две 16-байтовые
  половины ключа. Эффективный XTEA-ключ — `key_a XOR key_b` (половины XOR-ятся
  пословно).
- Payload — **потоковый шифр**: для каждого 8-байтового блока с индексом `i`
  бинарник считает `XTEA_encipher(i + 0xAFD9E340, 0x1E403058, key)` и XOR-ит
  результат по шифртексту (обычный XTEA, 32 раунда, delta `0x9E3779B9`).
- Расшифрованный payload даёт FNV-1a == `0x4B9FB9F7` → расшифровка верна.
- Payload — плоский поток опкодов. Каждая позиция флага получает свою
  **цепочку преобразований** (`+`, `-`, `^`, `rol`), завершённую сравнением `==`
  с константой. `OP_CHECK_LEN` (`0xCD`) кодирует длину флага.

**Идея, которая всё упростила**

- Я заметил, что каждый байт проверяется **независимо** (по одной цепочке на
  позицию, без перемешивания между байтами). То есть каждая позиция — уравнение
  на 1 байт: я прогоняю все 256 кандидатов через цепочку и оставляю тот, чей
  результат совпал с целевой константой. Никакого реального «крэка» не нужно.

## 4. Инструменты и команды

```bash
# Статический взгляд (опционально)
file chal

# Расшифровать payload, проверить сумму, перебрать флаг
python3 solve.py            # по умолчанию берёт ./chal
python3 solve.py ./chal     # явный путь
```

Чистый Python, без внешних RE-инструментов. См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. Распарсил load-команды Mach-O, нашёл `__TEXT,__const`, прочитал байты.
2. Разбил: `ciphertext = body[:0x2C4]`, сразу за ним две 4-словные половины
   ключа; `key = key_a ^ key_b`.
3. Собрал keystream поблочно через `XTEA(block + 0xAFD9E340, 0x1E403058, key)`
   и XOR-нул по шифртексту.
4. Убедился, что `fnv1a_32(payload) == 0x4B9FB9F7`.
5. Прошёл байткод: `SET_PTR` выбирает текущий индекс флага, `ADD/SUB/XOR/ROL`
   дописывают в цепочку этого индекса, `CHECK` фиксирует целевую константу,
   `CHECK_LEN` задаёт длину.
6. Для каждой позиции прогнал `candidate in range(256)` через цепочку (без
   финального `==`) и оставил совпавший с целью.
7. Склеил восстановленные байты → флаг.

## 6. Итоговое решение

Когда я запустил солвер на выданном бинарнике:

```
$ python3 solve.py
INFO     XTEA key: 0x2580f501 0xd194e025 0x9f48ceeb 0x05488ea6
INFO     FNV-1a of payload: 0x4b9fb9f7 (expected 0x4b9fb9f7)
INFO     VM expects 41 input bytes
SUCCESS  FLAG: THJCC{1_w0nd3r_h0w_l0n6_41_50lv35_17_>w<}
```

## 7. Флаг

```
THJCC{1_w0nd3r_h0w_l0n6_41_50lv35_17_>w<}
```

## 8. Ключевые выводы

- **Сигнал:** расшифрованный-в-рантайме блоб плюс самопроверка контрольной суммой
  (здесь FNV-1a) — явный признак «байткод-ВМ / упакованная проверка». Константа
  суммы — бесплатный оракул: воспроизвёл её — значит расшифровка верна ещё до
  разбора логики.
- **Почему сработало:** ВМ проверяет каждый байт отдельной цепочкой, поэтому
  пространство перебора схлопывается с `256^41` до `41 × 256`. Независимые
  побайтовые проверки — классическая слабость самописных «ВМ»-валидаторов.
- **Ложные следы:** перебирать вход против всей программы или копаться в нативном
  arm64 — нативный код это лишь цикл ВМ; логика в расшифрованном байткоде.
- **Как узнать в следующий раз:** блоб в `__TEXT,__const` / `.rodata` + константа
  XTEA/TEA `0x9E3779B9` + потоковый keystream = «расшифровать-и-интерпретировать».
  Восстанови keystream, проверь встроенным хэшем, потом моделируй обработчики
  опкодов.
