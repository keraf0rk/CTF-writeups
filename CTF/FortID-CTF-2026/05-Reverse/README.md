<a id="en"></a>
# 05 — Meteor Shower
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔧 Reverse |
| **Challenge file** | `meteor_shower.nes` (iNES, NROM: 2 × 16 KB PRG, 1 × 8 KB CHR) |
| **Status** | ✅ Solved |
| **Flag** | `FortID{SCIENTIA_POTENTIA_EST}` |

## 1. Description

A homebrew NES game, *Meteor Shower*: dodge falling meteors with the D-pad
until the timer runs out. Nothing in normal gameplay shows a flag.

## 2. Initial analysis

I started with the iNES header:

```bash
python3 -c "d=open('meteor_shower.nes','rb').read(); print(d[:16].hex())"
# 4e45531a 02 01 00 00 ...  -> iNES, 2 PRG banks, 1 CHR bank, mapper 0 (NROM)
```

- Mapper 0 means the 32 KB of PRG are mapped flat at `$8000–$FFFF`, with
  `RESET = $8000` and `NMI = $8098`. I disassembled it with
  [`py65`](https://github.com/mnaberez/py65) (6502).
- Looking for text, I noticed the strings use a tile offset (`0x80 = 'A'`,
  `0x00 = ' '`, `0xFF` ends a string). Once I decoded them, six strings showed
  up that the game never displays in normal play (`$86AA–$8701`):
  **"EASTER EGG FOUND! GREAT JOB ON FINDING THE EASTER EGG. I HOPE YOU LIKE
  BACON & EGGS!!! FIVE STRIPS AT A TIME."** That told me there was a hidden
  code, and I went looking for what draws this screen.

## 3. Investigation path

**What I confirmed — the hidden input checker**

- **`$80EF`** — every frame, while the game isn't won, a *newly pressed* **A**
  appends bit **0** and **B** appends bit **1** to a bit buffer at `$0400`
  (MSB first). Counter `$0C` tracks how many bits were entered.
- When `$0C` reaches **`0x5F` = 95**, **`$8158`** checks the buffer:

  ```
  k = 0x0B
  for i in 0..94:
      expected = (T1[k] ^ T2[k] ^ i) & 1      ; T1 = $8718, T2 = $8798
      fail    |= buffer_bit[i] ^ expected
      k = (k + 0x25) & 0x7F
  ```

  I recognised `T1`/`T2`: they are the same tables the game uses to spawn the
  meteors (x position and speed) — the secret was hidden in plain sight.
- If all 95 bits match, the game sets state `$04 = 4` and screen `$05 = 5`, and
  routine `$8577` draws the Easter-egg screen. A wrong sequence just clears the
  buffer.

**The idea that solved it**

- The expected sequence depends only on constants in the ROM, so I could
  compute it statically — no emulator and no button mashing.
- The Easter-egg screen is the second half of the hint: **bacon & eggs, five
  strips at a time** → **Bacon's cipher**, 5 bits per letter, and 95 bits are
  exactly 19 letters.

## 4. Tools & commands

```bash
pip install py65 loguru
python3 solve.py meteor_shower.nes
```

See [`solve.py`](solve.py).

## 5. Step-by-step

1. I loaded the PRG at `$8000` and disassembled the main loop (`$8059`), the
   input handling (`$80C1`, `$80EF`) and the checker (`$8158`).
2. I decoded the screen strings and found the Easter-egg text with the Bacon
   hint.
3. I re-ran the checker's arithmetic over `T1`/`T2` and got the 95 expected
   bits (as buttons: `B A A B A A A A B …`).
4. I split them into 19 groups of 5 and decoded them with the 26-letter Bacon
   alphabet (`A = 00000 … Z = 11001`):
   `10010 00010 01000 00100 01101 …` → **`SCIENTIA POTENTIA EST`**
   ("knowledge is power").

## 6. Solution

```
$ python3 solve.py meteor_shower.nes
INFO     win screen $86AA: EASTER EGG FOUND·
INFO     win screen $86F1: BACON · EGGS···
INFO     win screen $8701: FIVE STRIPS AT A TIME·
INFO     button sequence: BAABAAAABAABAAAAABAAABBABBAABBABAAAAAAAAABBBBABBBABAABBAABAAABBABBAABBABAAAAAAAAAABAABAABABAABB
INFO     Bacon plaintext: SCIENTIAPOTENTIAEST
SUCCESS  FLAG: FortID{SCIENTIA_POTENTIA_EST}
```

The bits come straight from the checker's own formula, so this exact A/B
sequence is the only input that makes `$8158` return success (carry set).

## 7. Flag

```
FortID{SCIENTIA_POTENTIA_EST}
```

## 8. Key takeaways

- **What tipped me off:** text in the ROM that normal play never shows. I
  found the code that draws it and worked backwards to its trigger.
- **Why it worked:** the secret check compares the input with values derived
  from constant tables, so the expected input can be computed offline.
- **What I skipped:** playing the game to the end — surviving the timer only
  leads to "MISSION COMPLETE", not to the flag.
- **What I'll remember:** bit strings in groups of 5 plus a bacon hint mean
  Bacon's cipher; on retro platforms I look for the controller-read routine
  (`$4016`) and whatever consumes its result.

---

<a id="ru"></a>
# 05 — Meteor Shower
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔧 Reverse |
| **Файл задания** | `meteor_shower.nes` (iNES, NROM: 2 × 16 КБ PRG, 1 × 8 КБ CHR) |
| **Статус** | ✅ Solved |
| **Флаг** | `FortID{SCIENTIA_POTENTIA_EST}` |

## 1. Условие

Самодельная игра для NES — *Meteor Shower*: уворачиваешься крестовиной от
падающих метеоров, пока не кончится таймер. В обычной игре флаг нигде не
показывается.

## 2. Первичный анализ

Начал с заголовка iNES:

```bash
python3 -c "d=open('meteor_shower.nes','rb').read(); print(d[:16].hex())"
# 4e45531a 02 01 00 00 ...  -> iNES, 2 банка PRG, 1 банк CHR, маппер 0 (NROM)
```

- Маппер 0 — значит 32 КБ PRG отображены целиком на `$8000–$FFFF`,
  `RESET = $8000`, `NMI = $8098`. Дизассемблировал через
  [`py65`](https://github.com/mnaberez/py65) (6502).
- Когда искал текст, заметил, что строки хранятся со смещением тайлов
  (`0x80 = 'A'`, `0x00 = ' '`, `0xFF` — конец строки). После декодирования нашлись
  шесть строк, которые игра в обычном режиме никогда не показывает
  (`$86AA–$8701`): **«EASTER EGG FOUND! GREAT JOB ON FINDING THE EASTER EGG. I
  HOPE YOU LIKE BACON & EGGS!!! FIVE STRIPS AT A TIME.»** Стало ясно, что есть
  скрытый код, и я пошёл искать, что рисует этот экран.

## 3. Путь исследования

**Что я подтвердил — скрытая проверка ввода**

- **`$80EF`** — каждый кадр, пока игра не выиграна, *новое нажатие* **A**
  дописывает бит **0**, а **B** — бит **1** в битовый буфер `$0400` (старшим
  битом вперёд). Счётчик `$0C` считает введённые биты.
- Когда `$0C` доходит до **`0x5F` = 95**, **`$8158`** проверяет буфер:

  ```
  k = 0x0B
  for i in 0..94:
      expected = (T1[k] ^ T2[k] ^ i) & 1      ; T1 = $8718, T2 = $8798
      fail    |= buffer_bit[i] ^ expected
      k = (k + 0x25) & 0x7F
  ```

  Я узнал `T1`/`T2`: это те же таблицы, по которым игра порождает метеоры
  (координата x и скорость), — секрет был спрятан на виду.
- Если все 95 бит совпали, игра ставит состояние `$04 = 4` и экран `$05 = 5`, и
  подпрограмма `$8577` рисует экран-пасхалку. Неверная последовательность просто
  очищает буфер.

**Идея, которая решила задачу**

- Ожидаемая последовательность зависит только от констант ROM, поэтому я мог
  вычислить её статически — без эмулятора и без перебора кнопок.
- Экран-пасхалка — вторая половина подсказки: **bacon & eggs, five strips at a
  time** → **шифр Бэкона**, 5 бит на букву, а 95 бит — ровно 19 букв.

## 4. Инструменты и команды

```bash
pip install py65 loguru
python3 solve.py meteor_shower.nes
```

См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. Загрузил PRG по адресу `$8000` и дизассемблировал главный цикл (`$8059`),
   обработку ввода (`$80C1`, `$80EF`) и проверку (`$8158`).
2. Декодировал экранные строки и нашёл текст пасхалки с подсказкой про Бэкона.
3. Повторил арифметику проверки по `T1`/`T2` и получил 95 ожидаемых бит
   (в виде кнопок: `B A A B A A A A B …`).
4. Разбил их на 19 групп по 5 и декодировал 26-буквенным алфавитом Бэкона
   (`A = 00000 … Z = 11001`):
   `10010 00010 01000 00100 01101 …` → **`SCIENTIA POTENTIA EST`**
   («знание — сила»).

## 6. Итоговое решение

```
$ python3 solve.py meteor_shower.nes
INFO     win screen $86AA: EASTER EGG FOUND·
INFO     win screen $86F1: BACON · EGGS···
INFO     win screen $8701: FIVE STRIPS AT A TIME·
INFO     button sequence: BAABAAAABAABAAAAABAAABBABBAABBABAAAAAAAAABBBBABBBABAABBAABAAABBABBAABBABAAAAAAAAAABAABAABABAABB
INFO     Bacon plaintext: SCIENTIAPOTENTIAEST
SUCCESS  FLAG: FortID{SCIENTIA_POTENTIA_EST}
```

Биты получены по формуле самой проверки, поэтому именно эта последовательность
A/B — единственный ввод, при котором `$8158` возвращает успех (флаг переноса
установлен).

## 7. Флаг

```
FortID{SCIENTIA_POTENTIA_EST}
```

## 8. Ключевые выводы

- **Что меня навело:** текст в ROM, который обычная игра не показывает. Я нашёл
  код, который его рисует, и раскрутил назад до триггера.
- **Почему сработало:** секретная проверка сравнивает ввод со значениями из
  константных таблиц, поэтому нужный ввод можно посчитать офлайн.
- **Что я пропустил сознательно:** проходить игру до конца — выживание по таймеру
  ведёт только к «MISSION COMPLETE», а не к флагу.
- **Что запомню:** битовые строки группами по 5 плюс намёк на бекон — это шифр
  Бэкона; на ретро-платформах ищу подпрограмму чтения контроллера (`$4016`) и то,
  что использует её результат.
