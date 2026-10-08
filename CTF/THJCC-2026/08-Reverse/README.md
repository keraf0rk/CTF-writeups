<a id="en"></a>
# 08 — TeaGod.exe
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔧 Reverse |
| **Challenge file** | [`TeaGod.exe`](TeaGod.exe) (PE32+ GUI, x86-64, MinGW) |
| **Solve script** | [`solve.py`](solve.py) |
| **Status** | ✅ Solved |
| **Flag** | `THJCC{h77p5://p4s73b1n.com/R58uv133}` |

## 1. Description

The challenge page shows a chat-bot style embed for a `/worship` command — a
devotee offering worship to the "Tea God", counter reading 666 times / 666 days —
and ships one artefact, `TeaGod.exe`.

> /worship — ✨ 虔誠的膜拜 ✨ … 累計膜拜次數 / 當前連續天數 666 次 / 666 天

## 2. Initial analysis

```bash
file TeaGod.exe           # PE32+ executable (GUI) x86-64, for MS Windows
ls -l TeaGod.exe          # 370688 bytes
strings -el -n 3 TeaGod.exe
```

- MinGW-built GUI program (`BeginPaint`, `CreateWindowExW`, `DefWindowProcW` in
  the imports — no .NET, no packer). The UTF-16 strings spell out the flow:
  `WORSHIP TEA GOD`, `Worship count:`, `REWARD UNLOCKED`, `Your reward:`.
- The 370 KB size is misleading. Parsing the section table shows `.text` is only
  `0x3A36` bytes; `.rsrc` holds `0x53398` bytes of artwork:

```
.text     va=0x140001000 vsize=0x3a36 raw=0x400
.rdata    va=0x140005000 vsize=0x2ad8 raw=0x4000
.data     va=0x140008000 vsize=0x190  raw=0x6c00
.rsrc     va=0x14000b000 vsize=0x53398 raw=0x7200
```

## 3. Investigation path

**Confirmed**

- The window procedure handles `WM_COMMAND` (`0x111`) with control id `0x1001`
  at `0x140001DCC`: it increments a counter in `.data` at `0x1400080C8`, then
  `0x140001E0A` tests `cmp dword [0x1400080C8], 0`. The gate is "non-zero" — one
  click unlocks the reward, the 666 in the description is flavour text.
- Layer 1 (`0x140001E90`): three 12-byte blobs reached through a pointer table at
  VA `0x140005210`, one key byte each at `0x140005228` (`A7 3C D1`). The additive
  constant decreases by 7 per position (`0xE7, 0xE0, 0xD9, …, 0x9A`):

```
tmp[i] = ((cipher[i] + (0xE7 - 7 * i)) & 0xFF) ^ key[chunk]
```

- Layer 2 (`0x140001FD0`): an 8-byte key loaded as an immediate,
  `movabs rax, 0x616E7368655F6368` → `b"hc_ehsna"`, indexed by `(1 + 3 * i) & 7`:

```
flag[i] = tmp[i] ^ b"hc_ehsna"[(1 + 3 * i) & 7]
```

**Key insight**

- In the same layer-2 loop every byte is XOR-ed **twice** with the value returned
  by the anti-analysis routine at `0x140002E10`:

```asm
xor byte ptr [r8 + rdx], r9b      ; ^ runtime byte   (0x140002033 path)
...
xor byte ptr [r8 + rdx], r9b      ; ^ the same byte again (0x140001FD0)
```

  Two XORs with the same value cancel, so whatever that routine computes is
  irrelevant to a static solve. Spotting the cancellation is what turns this into
  a five-minute job instead of an emulation exercise.

**Checked and dismissed**

- The pastebin URL inside the flag (`pastebin.com/R58uv133`) — fetching the raw
  paste returns an empty body, so it is part of the flag string, not a stage two.

**Left to check**

- What the routine at `0x140002E10` actually computes. It is provably irrelevant
  to the output, so it was never analysed.

## 4. Tools & commands

```bash
pip install capstone loguru

# Section table (shows .rsrc, not .text, is the bulk of the file)
python3 - <<'PY'
import struct
blob = open("TeaGod.exe", "rb").read()
pe = struct.unpack_from("<I", blob, 0x3c)[0]
nsec = struct.unpack_from("<H", blob, pe + 6)[0]
opt = struct.unpack_from("<H", blob, pe + 20)[0]
base = struct.unpack_from("<Q", blob, pe + 24 + 24)[0]
table = pe + 24 + opt
for i in range(nsec):
    e = table + i * 40
    name = blob[e:e + 8].rstrip(b"\0").decode()
    vs, va, rs, ro = struct.unpack_from("<IIII", blob, e + 8)
    print(f"{name:9} va={base + va:#x} vsize={vs:#x} raw={ro:#x}")
PY

python3 solve.py
```

See [`solve.py`](solve.py).

## 5. Step-by-step

1. `file` → PE32+ GUI; `strings -el` → `WORSHIP TEA GOD`, `REWARD UNLOCKED`.
2. Parse the section table → `.text` is only `0x3A36` bytes, `.rsrc` is artwork.
3. Disassemble `.text`, resolve RIP-relative references into `.rdata`.
4. Find the `WM_COMMAND` handler → the gate is `counter != 0`, one click.
5. Layer 1: pointer table `0x140005210`, 3 × 12 bytes, keys at `0x140005228`.
6. Layer 2: 8-byte key `b"hc_ehsna"` with stride 3; note the self-cancelling XOR.
7. Chain both layers → the flag.

## 6. Solution

```
$ python3 solve.py
INFO    loaded TeaGod.exe (370688 bytes)
INFO    image base 0x140000000, sections: .text, .rdata, .data, .pdata, .tls, .rsrc, .reloc
INFO    layer-1 chunk keys: a73cd1
INFO    chunk 0 at VA 0x1400051e6: a9a7b3e9ccf0ed4844175228
INFO    chunk 1 at VA 0x1400051f2: 799b5094619fb14bcf92d697
INFO    chunk 2 at VA 0x1400051fe: f6f4c60accbd0413d4e2e259
INFO    layer-2 key: b'hc_ehsna'
SUCCESS flag = THJCC{h77p5://p4s73b1n.com/R58uv133}
SUCCESS matches the known-good flag
```

## 7. Flag

```
THJCC{h77p5://p4s73b1n.com/R58uv133}
```

## 8. Key takeaways

- **The signal:** plaintext that is *almost* right after one decryption pass means
  a second pass, not a wrong key. Garbage of the correct length is a different
  failure from garbage of the wrong length.
- **Why it worked:** the same byte XOR-ed in twice is an algebraic no-op dressed
  up as anti-analysis. Before emulating any runtime-derived value, count how many
  times it is applied — an even count means it can be deleted from the model.
- **False leads:** the "666 worships" narrative (the code compares against zero),
  and the 370 KB file size (90% of it is a `.rsrc` image).
- **Recognize it next time:** a leetspeak URL inside a flag is usually
  decoration. Fetch it once to be sure, then stop — an empty or 404 response
  means the flag is already complete.

---

<a id="ru"></a>
# 08 — TeaGod.exe
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔧 Reverse |
| **Файл задания** | [`TeaGod.exe`](TeaGod.exe) (PE32+ GUI, x86-64, MinGW) |
| **Solve-скрипт** | [`solve.py`](solve.py) |
| **Статус** | ✅ Решено |
| **Флаг** | `THJCC{h77p5://p4s73b1n.com/R58uv133}` |

## 1. Условие

На странице задания — эмбед в стиле чат-бота для команды `/worship`: адепт
совершает поклонение «Чайной богине», счётчик показывает 666 раз / 666 дней. К
заданию приложен один файл — `TeaGod.exe`.

> /worship — ✨ 虔誠的膜拜 ✨ … 累計膜拜次數 / 當前連續天數 666 次 / 666 天

## 2. Первичный анализ

```bash
file TeaGod.exe           # PE32+ executable (GUI) x86-64, for MS Windows
ls -l TeaGod.exe          # 370688 байт
strings -el -n 3 TeaGod.exe
```

- GUI-программа, собранная MinGW (в импортах `BeginPaint`, `CreateWindowExW`,
  `DefWindowProcW` — ни .NET, ни упаковщика). UTF-16-строки описывают сценарий:
  `WORSHIP TEA GOD`, `Worship count:`, `REWARD UNLOCKED`, `Your reward:`.
- Размер в 370 КБ обманчив. Разбор таблицы секций показывает, что `.text` — всего
  `0x3A36` байт, а `.rsrc` занимает `0x53398` байт картинки:

```
.text     va=0x140001000 vsize=0x3a36 raw=0x400
.rdata    va=0x140005000 vsize=0x2ad8 raw=0x4000
.data     va=0x140008000 vsize=0x190  raw=0x6c00
.rsrc     va=0x14000b000 vsize=0x53398 raw=0x7200
```

## 3. Путь исследования

**Подтверждено**

- Оконная процедура обрабатывает `WM_COMMAND` (`0x111`) с id контрола `0x1001` по
  адресу `0x140001DCC`: инкрементирует счётчик в `.data` по `0x1400080C8`, затем
  `0x140001E0A` проверяет `cmp dword [0x1400080C8], 0`. Условие — «не ноль»: один
  клик открывает награду, а 666 в описании — художественный элемент.
- Слой 1 (`0x140001E90`): три 12-байтных блоба через таблицу указателей по VA
  `0x140005210`, по байту ключа на блоб в `0x140005228` (`A7 3C D1`). Аддитивная
  константа убывает на 7 на позицию (`0xE7, 0xE0, 0xD9, …, 0x9A`):

```
tmp[i] = ((cipher[i] + (0xE7 - 7 * i)) & 0xFF) ^ key[chunk]
```

- Слой 2 (`0x140001FD0`): 8-байтный ключ, загруженный непосредственным значением
  `movabs rax, 0x616E7368655F6368` → `b"hc_ehsna"`, по индексу `(1 + 3 * i) & 7`:

```
flag[i] = tmp[i] ^ b"hc_ehsna"[(1 + 3 * i) & 7]
```

**Ключевая идея**

- В том же цикле второго слоя каждый байт **дважды** XOR-ится со значением,
  которое возвращает антианализная подпрограмма по адресу `0x140002E10`:

```asm
xor byte ptr [r8 + rdx], r9b      ; ^ рантайм-байт   (путь 0x140002033)
...
xor byte ptr [r8 + rdx], r9b      ; ^ тот же байт ещё раз (0x140001FD0)
```

  Два XOR-а с одним значением взаимно уничтожаются, поэтому что бы эта
  подпрограмма ни вычисляла, к статическому решению это отношения не имеет.
  Замеченное сокращение превращает задание в пятиминутное вместо эмуляции.

**Проверено и отброшено**

- Pastebin-ссылка внутри флага (`pastebin.com/R58uv133`) — запрос raw-пасты
  возвращает пустое тело, то есть это часть строки флага, а не второй этап.

**Осталось проверить**

- Что именно вычисляет подпрограмма `0x140002E10`. На вывод она доказуемо не
  влияет, поэтому не анализировалась.

## 4. Инструменты и команды

```bash
pip install capstone loguru

# Таблица секций (видно, что основную массу файла занимает .rsrc, а не .text)
python3 - <<'PY'
import struct
blob = open("TeaGod.exe", "rb").read()
pe = struct.unpack_from("<I", blob, 0x3c)[0]
nsec = struct.unpack_from("<H", blob, pe + 6)[0]
opt = struct.unpack_from("<H", blob, pe + 20)[0]
base = struct.unpack_from("<Q", blob, pe + 24 + 24)[0]
table = pe + 24 + opt
for i in range(nsec):
    e = table + i * 40
    name = blob[e:e + 8].rstrip(b"\0").decode()
    vs, va, rs, ro = struct.unpack_from("<IIII", blob, e + 8)
    print(f"{name:9} va={base + va:#x} vsize={vs:#x} raw={ro:#x}")
PY

python3 solve.py
```

См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. `file` → PE32+ GUI; `strings -el` → `WORSHIP TEA GOD`, `REWARD UNLOCKED`.
2. Разбираем таблицу секций → `.text` всего `0x3A36` байт, `.rsrc` — картинка.
3. Дизассемблируем `.text`, разрешаем RIP-относительные ссылки в `.rdata`.
4. Находим обработчик `WM_COMMAND` → условие `counter != 0`, достаточно клика.
5. Слой 1: таблица указателей `0x140005210`, 3 × 12 байт, ключи по `0x140005228`.
6. Слой 2: 8-байтный ключ `b"hc_ehsna"` с шагом 3; замечаем самосокращающийся XOR.
7. Склеиваем оба слоя → флаг.

## 6. Итоговое решение

```
$ python3 solve.py
INFO    loaded TeaGod.exe (370688 bytes)
INFO    image base 0x140000000, sections: .text, .rdata, .data, .pdata, .tls, .rsrc, .reloc
INFO    layer-1 chunk keys: a73cd1
INFO    chunk 0 at VA 0x1400051e6: a9a7b3e9ccf0ed4844175228
INFO    chunk 1 at VA 0x1400051f2: 799b5094619fb14bcf92d697
INFO    chunk 2 at VA 0x1400051fe: f6f4c60accbd0413d4e2e259
INFO    layer-2 key: b'hc_ehsna'
SUCCESS flag = THJCC{h77p5://p4s73b1n.com/R58uv133}
SUCCESS matches the known-good flag
```

## 7. Флаг

```
THJCC{h77p5://p4s73b1n.com/R58uv133}
```

## 8. Ключевые выводы

- **Что было сигналом:** если после одного прохода расшифровки текст *почти*
  правильный, значит нужен второй проход, а не другой ключ. Мусор правильной
  длины — это не та же ошибка, что мусор неправильной длины.
- **Почему сработало:** один и тот же байт, применённый XOR-ом дважды, —
  алгебраический no-op под видом антианализа. Прежде чем эмулировать
  рантайм-значение, посчитайте, сколько раз оно применяется: чётное число
  означает, что его можно выкинуть из модели.
- **Ложные следы:** легенда про «666 поклонений» (код сравнивает с нулём) и
  размер файла в 370 КБ (90% — картинка в `.rsrc`).
- **Как узнать в следующий раз:** leet-URL внутри флага обычно декорация.
  Запросите его один раз для уверенности и остановитесь: пустой ответ или 404
  означают, что флаг уже полный.
