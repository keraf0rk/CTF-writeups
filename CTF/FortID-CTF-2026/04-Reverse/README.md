<a id="en"></a>
# 04 — Baby Rev
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔧 Reverse |
| **Challenge file** | `chall.pyc` (CPython 3.10 bytecode) |
| **Status** | ✅ Solved |
| **Flag** | `FortID{nokia_3310_is_still_the_most_robust_piece_of_technology_i_have_ever_owned}` |

## 1. Description

A compiled Python flag checker. It prompts `pls text me the flag :P` and
answers either `nope! ಠ_ಠ` or `*\0/* I knew you could do it! ^5`.

## 2. Initial analysis

The first thing I checked was the `.pyc` magic:

```bash
python3 -c "print(open('chall.pyc','rb').read(4).hex())"   # 6f0d0d0a
```

- `0x0D6F` = **3439 → CPython 3.10**. My interpreter is newer, and `marshal`
  refuses bytecode from another version, so I disassembled it cross-version
  with [`xdis`](https://github.com/rocky/python-xdis):

```bash
pip install xdis
pydisasm chall.pyc
```

- The constants and names already gave away the plan: `t9text.t9.get_touchtone`,
  `sha256`, the number `81`, `'FortID{'`, `'}'`, `'_'`, `'-'`, a long digit
  string and a SHA-256 digest.

## 3. Investigation path

**What I confirmed — the checker, rebuilt from the bytecode**

```python
from hashlib import sha256
from t9text import t9

flag = input("pls text me the flag :P\n> ")
assert len(flag) == 81
assert flag.startswith("FortID{") and flag.endswith("}")
words = flag[len("FortID{"):-1]
for w in words.split("_"):
    assert all(c in ascii_lowercase for c in w) or all(c in digits for c in w)
words = "-".join(words.split("_"))
assert t9.get_touchtone(words)[::-1] == \
    "33696-7383-3824-4-9465664238-36-32347-878267-8766-348-55487-74-0133-24566"
assert sha256(flag.encode()).hexdigest() == \
    "3576c495f89236515fbbfbfb519dceb9899122e92460d418d2ce37a1ff357e0c"
```

- I opened the `t9text` package: `get_touchtone` maps letters to **phone
  keypad digits** (`abc→2 … wxyz→9`) and leaves digits and `-` untouched.
- The result is **reversed** (`[::-1]`) before the comparison. Reversing the
  whole string flips both the digits inside each word and the word order —
  that's why the target looked like nonsense at first.

**The idea that solved it**

- I reversed the target, split it on `-`, and each group turned into one word
  typed on an old phone keypad. Digit-only groups (`3310`) stay digits. The
  SHA-256 in the bytecode then confirmed the exact text, so nothing was left to
  guess.

## 4. Tools & commands

```bash
pip install xdis
pydisasm chall.pyc        # recover the logic
python3 solve.py          # decode the keypad groups and verify the hash
```

See [`solve.py`](solve.py).

## 5. Step-by-step

1. I disassembled `chall.pyc` with `pydisasm` and rewrote the checker in
   Python.
2. I reversed the target string:
   `66542-3310-47-78455-843-6678-762878-74323-63-8324665649-4-4283-3837-69633`.
3. I read every group on the keypad:

   | digits | word | digits | word |
   |---|---|---|---|
   | `66542` | nokia | `63` | of |
   | `3310` | 3310 | `8324665649` | technology |
   | `47` | is | `4` | i |
   | `78455` | still | `4283` | have |
   | `843` | the | `3837` | ever |
   | `6678` | most | `69633` | owned |
   | `762878` | robust | | |
   | `74323` | piece | | |

4. I joined the words with `_` and wrapped them in `FortID{…}`: the length is
   81 and the SHA-256 matches.

## 6. Solution

```
$ python3 solve.py
INFO     keypad groups: ['66542', '3310', '47', '78455', '843', '6678', '762878', '74323', '63', '8324665649', '4', '4283', '3837', '69633']
...
SUCCESS  FLAG: FortID{nokia_3310_is_still_the_most_robust_piece_of_technology_i_have_ever_owned}  (length 81, SHA-256 matches)
```

## 7. Flag

```
FortID{nokia_3310_is_still_the_most_robust_piece_of_technology_i_have_ever_owned}
```

## 8. Key takeaways

- **What tipped me off:** a `.pyc` whose magic doesn't match my interpreter —
  `xdis`/`pydisasm` (or `pycdc`) instead of `marshal`.
- **Why it worked:** T9 loses information (3–4 letters per key), but a real
  sentence plus the embedded SHA-256 leaves exactly one answer.
- **Where it could go wrong:** missing the `[::-1]` — without the reversal the
  groups look meaningless.
- **What I'll remember:** "text me", phone keypads and digit groups made only
  of `2–9` mean T9 / multi-tap.

---

<a id="ru"></a>
# 04 — Baby Rev
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔧 Reverse |
| **Файл задания** | `chall.pyc` (байткод CPython 3.10) |
| **Статус** | ✅ Solved |
| **Флаг** | `FortID{nokia_3310_is_still_the_most_robust_piece_of_technology_i_have_ever_owned}` |

## 1. Условие

Скомпилированная проверялка флага на Python. Спрашивает `pls text me the flag :P`
и отвечает либо `nope! ಠ_ಠ`, либо `*\0/* I knew you could do it! ^5`.

## 2. Первичный анализ

Первым делом посмотрел magic у `.pyc`:

```bash
python3 -c "print(open('chall.pyc','rb').read(4).hex())"   # 6f0d0d0a
```

- `0x0D6F` = **3439 → CPython 3.10**. Мой интерпретатор новее, а `marshal` не
  принимает байткод другой версии, поэтому я дизассемблировал его
  кросс-версионно через [`xdis`](https://github.com/rocky/python-xdis):

```bash
pip install xdis
pydisasm chall.pyc
```

- Константы и имена сразу выдали план: `t9text.t9.get_touchtone`, `sha256`,
  число `81`, `'FortID{'`, `'}'`, `'_'`, `'-'`, длинная цифровая строка и
  SHA-256-дайджест.

## 3. Путь исследования

**Что я подтвердил — проверка, восстановленная из байткода**

```python
from hashlib import sha256
from t9text import t9

flag = input("pls text me the flag :P\n> ")
assert len(flag) == 81
assert flag.startswith("FortID{") and flag.endswith("}")
words = flag[len("FortID{"):-1]
for w in words.split("_"):
    assert all(c in ascii_lowercase for c in w) or all(c in digits for c in w)
words = "-".join(words.split("_"))
assert t9.get_touchtone(words)[::-1] == \
    "33696-7383-3824-4-9465664238-36-32347-878267-8766-348-55487-74-0133-24566"
assert sha256(flag.encode()).hexdigest() == \
    "3576c495f89236515fbbfbfb519dceb9899122e92460d418d2ce37a1ff357e0c"
```

- Я заглянул в пакет `t9text`: `get_touchtone` переводит буквы в **цифры
  телефонной клавиатуры** (`abc→2 … wxyz→9`), а цифры и `-` не трогает.
- Результат **разворачивается** (`[::-1]`) перед сравнением. Разворот всей
  строки переворачивает и цифры внутри слов, и порядок слов — поэтому цель
  поначалу выглядела бессмыслицей.

**Идея, которая решила задачу**

- Я развернул целевую строку, разрезал по `-`, и каждая группа превратилась в
  одно слово, набранное на кнопочном телефоне. Чисто цифровые группы (`3310`)
  остаются цифрами. SHA-256 из байткода затем подтвердил точный текст, так что
  угадывать было нечего.

## 4. Инструменты и команды

```bash
pip install xdis
pydisasm chall.pyc        # восстановить логику
python3 solve.py          # декодировать группы и проверить хеш
```

См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. Дизассемблировал `chall.pyc` через `pydisasm` и переписал проверку на Python.
2. Развернул целевую строку:
   `66542-3310-47-78455-843-6678-762878-74323-63-8324665649-4-4283-3837-69633`.
3. Прочитал каждую группу по клавиатуре:

   | цифры | слово | цифры | слово |
   |---|---|---|---|
   | `66542` | nokia | `63` | of |
   | `3310` | 3310 | `8324665649` | technology |
   | `47` | is | `4` | i |
   | `78455` | still | `4283` | have |
   | `843` | the | `3837` | ever |
   | `6678` | most | `69633` | owned |
   | `762878` | robust | | |
   | `74323` | piece | | |

4. Склеил слова через `_` и обернул в `FortID{…}`: длина 81, SHA-256 совпадает.

## 6. Итоговое решение

```
$ python3 solve.py
INFO     keypad groups: ['66542', '3310', '47', '78455', '843', '6678', '762878', '74323', '63', '8324665649', '4', '4283', '3837', '69633']
...
SUCCESS  FLAG: FortID{nokia_3310_is_still_the_most_robust_piece_of_technology_i_have_ever_owned}  (length 81, SHA-256 matches)
```

## 7. Флаг

```
FortID{nokia_3310_is_still_the_most_robust_piece_of_technology_i_have_ever_owned}
```

## 8. Ключевые выводы

- **Что меня навело:** `.pyc`, чей magic не совпадает с моим интерпретатором, —
  значит `xdis`/`pydisasm` (или `pycdc`), а не `marshal`.
- **Почему сработало:** T9 теряет информацию (3–4 буквы на клавишу), но
  осмысленная фраза плюс встроенный SHA-256 оставляют ровно один ответ.
- **Где можно было ошибиться:** пропустить `[::-1]` — без разворота группы
  выглядят бессмысленными.
- **Что запомню:** «text me», телефонная клавиатура и группы цифр только из
  `2–9` — это T9 / multi-tap.
