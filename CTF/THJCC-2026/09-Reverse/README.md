<a id="en"></a>
# 09 — BlackFrost
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔧 Reverse |
| **Challenge files** | [`BlackFrost.exe`](BlackFrost.exe) (ELF 64-bit, static, stripped), [`traffic.pcap`](traffic.pcap) |
| **Solve script** | [`solve.py`](solve.py) |
| **Status** | ✅ Solved |
| **Flag** | `THJCC{blackfrost_config_recovered}` |

## 1. Description

A malware-flavoured task: an implant plus a capture of its C2 session.

> Please test in the Windows sandbox.

## 2. Initial analysis

```bash
file BlackFrost.exe traffic.pcap
ls -l BlackFrost.exe traffic.pcap    # 7168 and 304 bytes
xxd traffic.pcap | tail -8
strings -n 5 BlackFrost.exe
```

- The `.exe` extension is a lie: it is a 7 KB static, stripped **ELF**, the same
  hand-written syscall style as [`05-Reverse`](../05-Reverse/) and
  [`06-Reverse`](../06-Reverse/) by the same author. The "Windows sandbox" note
  is misdirection — nothing needs to be run.
- The capture is two loopback packets:

```
->  BFHELLO b700b632
<-  BF2:0bbc114acd70a708ed0748e357ca0ebc179ed807ae3feb38afdb77f739c53bec
    2e0cab21e810922353d14df411dc0ba1d441c96988449fd84cec0f
```

- Error strings map the whole control flow: `handshake rejected`,
  `configuration rejected`, `stage unpack failed`, `analysis mode disabled`,
  `sandbox timeout`, `C2 unavailable; start the local replay server`.

## 3. Investigation path

**Confirmed**

- `0x1400012B6` hashes `argv[1]` with FNV-1a 32 and compares against
  `0xB700B632` — exactly the value the client sends in `BFHELLO b700b632`. The
  hash *is* the key material, and the capture hands it over, so the token string
  never has to be found.
- Anti-analysis, none of it touching the key schedule:

| Address | Check | Message |
|---|---|---|
| `0x1400011A1` | `IsDebuggerPresent` | `analysis mode disabled`, exit 3 |
| `0x1400015C7` | `GetTickCount` delta ≥ `0xBB9` (3001 ms) | `sandbox timeout` |
| `0x140001A4A` | `connect` to `127.0.0.1:31337` (`0x7A69`) | `C2 unavailable; …` |

- The C2 payload parser at `0x1400019C9` reads the hex after `BF2:` and decrypts
  with a stream keyed by the hash, with a position-dependent addend (`edx` starts
  at `0x5A`, `+0x11` per byte; `r8d` `+8`, so the shift is `(n & 3) * 8`):

```
plain[n] = cipher[n] ^ (hash >> (8 * (n & 3))) ^ ((90 + 17 * n) & 0xFF)
```

  → `campaign=BLACKFROST-26;nonce=4c2f17;directive=collect-only;`
- Once the configuration parses, `0x140001777` decodes a 34-byte `.rodata` blob
  at VA `0x140003080` with the author's rolling XOR (seed `0x26`, step `0x1A`,
  even byte of each pair against `key - 0x0D`) and writes it with `WriteFile`.

**Key insight**

- A constant in the binary that also appears verbatim on the wire means the
  capture already contains the key material. Diff pcap strings against the
  immediates in the disassembly before planning any dynamic work.

**False lead**

- `0x140001394`–`0x140001501` is a dense SSE loop that decrypts a 56-byte
  `.rdata` blob with the same hash, appends three bytes derived from `ebp` and
  checks `strlen < 0x17`. It is positioned and sized to look like the payload and
  is reached *before* the real routine — but it belongs to the
  `stage unpack failed` path and decrypts to noise. (The SSE block at
  `0x140001A7E` is likewise not crypto: it is a hex encoder building
  `BFHELLO <hash>\n`.)

**Left to check**

- No `--token` value producing FNV-1a `0xB700B632` was searched for. It is
  unnecessary, and a 32-bit FNV preimage is trivially collidable, so any
  discovered token would likely not be the author's.

## 4. Tools & commands

```bash
pip install capstone loguru

# Full .text disassembly
python3 - <<'PY'
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
blob = open("BlackFrost.exe", "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_64)
for insn in md.disasm(blob[0x400:0x400 + 0x10ad], 0x140001000):
    print(f"{insn.address:#x}\t{insn.mnemonic}\t{insn.op_str}")
PY

python3 solve.py
python3 solve.py --token 'some-candidate'   # hash a candidate token
```

The solver walks the pcap itself (Ethernet/IPv4/TCP, pure `struct` — no
scapy/tshark). See [`solve.py`](solve.py).

## 5. Step-by-step

1. `file` → the `.exe` is actually a static stripped ELF; `xxd` the 304-byte pcap.
2. Read the two TCP payloads → `BFHELLO b700b632` and `BF2:<hex>`.
3. Disassemble `.text`; find the FNV-1a comparison against `0xB700B632`.
4. Match that constant to the handshake → the hash is available without the token.
5. Catalogue and dismiss the anti-analysis checks and the SSE decoy blob.
6. Decrypt the C2 payload: `cipher[n] ^ (hash >> 8*(n&3)) ^ (90 + 17n)`.
7. Decode the flag blob at VA `0x140003080`, 34 bytes, seed `0x26`.

## 6. Solution

```
$ python3 solve.py
INFO    pcap: 2 tcp payloads
INFO    handshake hash = 0xb700b632
INFO    c2 payload: 59 bytes
SUCCESS config = campaign=BLACKFROST-26;nonce=4c2f17;directive=collect-only;
INFO    image base 0x140000000, sections: .text, .rdata
SUCCESS flag = THJCC{blackfrost_config_recovered}
SUCCESS matches the known-good config and flag
```

Nothing was executed: no Windows sandbox, no replay server on port 31337.

## 7. Flag

```
THJCC{blackfrost_config_recovered}
```

## 8. Key takeaways

- **The signal:** the handshake echoes a constant that also sits in the binary.
  When an implant keys its cipher with `FNV-1a(token)` rather than the token, the
  capture leaks the key and the secret becomes irrelevant.
- **Why it worked:** the stream cipher is a per-byte XOR of three known terms —
  ciphertext, a rotation of the hash, and a position-dependent addend. Entirely
  offline.
- **False leads:** the "test in the Windows sandbox" instruction on a file that
  is not a PE, and the SSE-decrypted 56-byte decoy blob belonging to
  `stage unpack failed`. When decryption yields noise, check whether that branch
  owns an error string — decoys usually do.
- **Recognize it next time:** implant + pcap → recover the key schedule from the
  handshake, then look for a `.rodata` blob of flag length. Running the sample is
  the last resort, not the first step.

---

<a id="ru"></a>
# 09 — BlackFrost
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔧 Reverse |
| **Файлы задания** | [`BlackFrost.exe`](BlackFrost.exe) (ELF 64-bit, статика, stripped), [`traffic.pcap`](traffic.pcap) |
| **Solve-скрипт** | [`solve.py`](solve.py) |
| **Статус** | ✅ Решено |
| **Флаг** | `THJCC{blackfrost_config_recovered}` |

## 1. Условие

Задание в антураже вредоноса: имплант плюс запись его сессии с C2.

> Please test in the Windows sandbox.

## 2. Первичный анализ

```bash
file BlackFrost.exe traffic.pcap
ls -l BlackFrost.exe traffic.pcap    # 7168 и 304 байта
xxd traffic.pcap | tail -8
strings -n 5 BlackFrost.exe
```

- Расширение `.exe` врёт: это 7 КБ статического stripped **ELF** в том же
  рукописном syscall-стиле, что [`05-Reverse`](../05-Reverse/) и
  [`06-Reverse`](../06-Reverse/) того же автора. Примечание про «Windows sandbox»
  — отвлекающий манёвр, запускать не нужно ничего.
- В записи два пакета по петле:

```
->  BFHELLO b700b632
<-  BF2:0bbc114acd70a708ed0748e357ca0ebc179ed807ae3feb38afdb77f739c53bec
    2e0cab21e810922353d14df411dc0ba1d441c96988449fd84cec0f
```

- Строки ошибок размечают весь поток управления: `handshake rejected`,
  `configuration rejected`, `stage unpack failed`, `analysis mode disabled`,
  `sandbox timeout`, `C2 unavailable; start the local replay server`.

## 3. Путь исследования

**Подтверждено**

- По адресу `0x1400012B6` `argv[1]` хешируется через FNV-1a 32 и сравнивается с
  `0xB700B632` — ровно то значение, которое клиент отправляет в
  `BFHELLO b700b632`. Ключевым материалом является *хеш*, и запись его уже
  содержит, поэтому строку токена искать не нужно.
- Антианализ, не влияющий на расписание ключей:

| Адрес | Проверка | Сообщение |
|---|---|---|
| `0x1400011A1` | `IsDebuggerPresent` | `analysis mode disabled`, выход 3 |
| `0x1400015C7` | дельта `GetTickCount` ≥ `0xBB9` (3001 мс) | `sandbox timeout` |
| `0x140001A4A` | `connect` к `127.0.0.1:31337` (`0x7A69`) | `C2 unavailable; …` |

- Парсер payload-а по адресу `0x1400019C9` читает hex после `BF2:` и
  расшифровывает потоком на ключе-хеше с позиционно-зависимым слагаемым (`edx`
  стартует с `0x5A`, `+0x11` на байт; `r8d` `+8`, поэтому сдвиг `(n & 3) * 8`):

```
plain[n] = cipher[n] ^ (hash >> (8 * (n & 3))) ^ ((90 + 17 * n) & 0xFF)
```

  → `campaign=BLACKFROST-26;nonce=4c2f17;directive=collect-only;`
- После успешного разбора конфигурации `0x140001777` декодирует 34-байтный блоб
  `.rodata` по VA `0x140003080` авторским бегущим XOR-ом (старт `0x26`, шаг
  `0x1A`, чётный байт пары против `key - 0x0D`) и печатает его через `WriteFile`.

**Ключевая идея**

- Константа в бинаре, дословно встречающаяся в трафике, означает, что ключевой
  материал уже есть в записи. Сверяйте строки из pcap с непосредственными
  значениями из дизассемблера раньше, чем планировать динамику.

**Ложный след**

- Диапазон `0x140001394`–`0x140001501` — плотный SSE-цикл, расшифровывающий
  56-байтный блоб `.rdata` тем же хешем, дописывающий три байта из `ebp` и
  проверяющий `strlen < 0x17`. Он расположен и размерен так, чтобы выглядеть
  полезной нагрузкой, и встречается *раньше* настоящей процедуры — но принадлежит
  ветке `stage unpack failed` и расшифровывается в шум. (SSE-блок по
  `0x140001A7E` — тоже не криптография, а hex-кодировщик, собирающий
  `BFHELLO <hash>\n`.)

**Осталось проверить**

- Значение `--token`, дающее FNV-1a `0xB700B632`, не искалось. Оно не требуется,
  а 32-битный FNV тривиально коллизионен, так что найденный токен всё равно вряд
  ли совпал бы с авторским.

## 4. Инструменты и команды

```bash
pip install capstone loguru

# Полный дизассемблер .text
python3 - <<'PY'
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
blob = open("BlackFrost.exe", "rb").read()
md = Cs(CS_ARCH_X86, CS_MODE_64)
for insn in md.disasm(blob[0x400:0x400 + 0x10ad], 0x140001000):
    print(f"{insn.address:#x}\t{insn.mnemonic}\t{insn.op_str}")
PY

python3 solve.py
python3 solve.py --token 'some-candidate'   # посчитать хеш кандидата
```

Солвер сам обходит pcap (Ethernet/IPv4/TCP, чистый `struct` — без scapy/tshark).
См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. `file` → «`.exe`» на деле статический stripped ELF; смотрим pcap на 304 байта через `xxd`.
2. Читаем два TCP-пейлоада → `BFHELLO b700b632` и `BF2:<hex>`.
3. Дизассемблируем `.text`; находим сравнение FNV-1a с `0xB700B632`.
4. Сопоставляем константу с рукопожатием → хеш доступен без токена.
5. Каталогизируем и отбрасываем антианализ и SSE-блоб-приманку.
6. Расшифровываем payload: `cipher[n] ^ (hash >> 8*(n&3)) ^ (90 + 17n)`.
7. Декодируем блоб флага по VA `0x140003080`, 34 байта, старт `0x26`.

## 6. Итоговое решение

```
$ python3 solve.py
INFO    pcap: 2 tcp payloads
INFO    handshake hash = 0xb700b632
INFO    c2 payload: 59 bytes
SUCCESS config = campaign=BLACKFROST-26;nonce=4c2f17;directive=collect-only;
INFO    image base 0x140000000, sections: .text, .rdata
SUCCESS flag = THJCC{blackfrost_config_recovered}
SUCCESS matches the known-good config and flag
```

Ничего не запускалось: ни Windows-песочницы, ни replay-сервера на порту 31337.

## 7. Флаг

```
THJCC{blackfrost_config_recovered}
```

## 8. Ключевые выводы

- **Что было сигналом:** рукопожатие повторяет константу, которая лежит и в
  бинаре. Если имплант ключует шифр значением `FNV-1a(token)`, а не токеном,
  запись трафика утекает ключ, и секрет перестаёт иметь значение.
- **Почему сработало:** поточный шифр — побайтовый XOR трёх известных слагаемых:
  шифртекста, поворота хеша и позиционно-зависимой добавки. Полностью офлайн.
- **Ложные следы:** указание «тестировать в Windows-песочнице» на файле, который
  не является PE, и 56-байтный SSE-блоб-приманка из ветки `stage unpack failed`.
  Если расшифровка даёт шум, проверьте, нет ли у этой ветки собственной строки
  ошибки: у приманок она обычно есть.
- **Как узнать в следующий раз:** имплант + pcap → восстановить расписание ключей
  из рукопожатия, затем искать блоб `.rodata` длиной с флаг. Запуск образца —
  последнее средство, а не первый шаг.
