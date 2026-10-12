<a id="en"></a>
# 02 — Human RNG
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔐 Crypto |
| **Challenge files** | `encrypt.py`, `bitstream.txt`, `ciphertext.png` |
| **Status** | ✅ Solved |
| **Flag** | `FortID{humans_are_not_good_random_number_generators}` |

## 1. Description

The flag is rendered as a **QR code** (version 6, error correction H, mask 0,
41 × 41 = 1681 modules) and XOR-ed with a keystream. The keystream is the last
1681 bits of `bitstream.txt` — a bit string **typed by a human**. Those bits
are redacted (`<1681-bits-redacted>`), but the first 1999 typed bits are
public.

## 2. Initial analysis

I read the encryptor first and looked at the raw bitstream:

```bash
cat encrypt.py      # QR v6-H, mask 0  ->  XOR with bits[-1681:]  ->  ciphertext.png
head -c 200 bitstream.txt
```

- `encrypt.py` told me the exact format: `FortID{` + body + `}`, the body is
  **exactly 44 characters** of lowercase English words joined by `_`
  (`[a-z]+(?:_[a-z]+)+`).
- `ciphertext.png` is the 41 × 41 XOR result scaled ×10.
- The public prefix immediately looked wrong for a random source: the bit
  **flips 70 % of the time** instead of 50 %, and runs longer than 3 almost
  never appear. That is the classic way people "type randomly" — they avoid
  repeating themselves. The title said the same thing.

## 3. Investigation path

**What I confirmed**

- I trained an **order-4 Markov model** on the 1999-bit prefix. It captures
  the bias nicely: the prefix itself scores ≈ **−0.59** log-likelihood per
  bit, while random noise scores ≈ **−0.84**.
- For any candidate flag `F` I can compute `key = ciphertext ⊕ QR(F)`. If `F`
  is right, that key is the human-typed suffix and scores like the prefix; if
  a character is wrong, the QR modules it controls become noise and the score
  drops. So the model works as a **likelihood oracle** for the plaintext.

**The idea that made it practical — the oracle is local**

- QR v6-H stores the data in **4 Reed–Solomon blocks** (15 data bytes each),
  interleaved across the symbol. I mapped every module to its block, so the
  oracle can score each block **separately** and tell me not only *whether* a
  candidate is wrong, but *which part* of the text is wrong.
- The title states the thesis — *humans make bad random number generators*.
  Fitting it into exactly 44 characters gives
  `humans_are_not_good_random_number_generators`, and the oracle confirmed it:
  all four blocks scored like the human-typed prefix.

## 4. Tools & commands

```bash
pip install qrcode pillow numpy loguru
python3 solve.py handout/                       # verify the flag
python3 solve.py handout/ "FortID{...other...}" # score any hypothesis
```

See [`solve.py`](solve.py).

## 5. Step-by-step

1. I read `ciphertext.png` by sampling the centre of each 10 × 10 cell → 1681
   bits.
2. I trained the order-4 model on the public prefix (Laplace-smoothed
   `P(bit | 4 previous bits)`).
3. I built the module → RS-block map by replaying the module placement walk
   of the `qrcode` library for version 6-H.
4. For the hypothesis I computed `key = ct ⊕ QR(flag)` and its mean
   log-likelihood overall and per RS block, and compared them with the two
   references (human prefix ≈ −0.59, noise ≈ −0.84).
5. All four blocks came out human-like, which confirmed the flag.

## 6. Solution

```
$ python3 solve.py handout/
INFO     prefix: 1999 bits, flip rate 0.702
INFO     reference LL/bit: human prefix -0.592 | random noise -0.841
INFO     candidate FortID{humans_are_not_good_random_number_generators}
INFO       whole key LL/bit -0.579
INFO       RS block 0: LL/bit -0.606  human-like
INFO       RS block 1: LL/bit -0.565  human-like
INFO       RS block 2: LL/bit -0.597  human-like
INFO       RS block 3: LL/bit -0.570  human-like
SUCCESS  FLAG: FortID{humans_are_not_good_random_number_generators}
```

The oracle is sharp: if only `not_good` is swapped for a different 8-letter
word, blocks 0, 2, 3 stay human-like and **only block 1** falls to ≈ −0.76 —
exactly the block that stores those characters.

## 7. Flag

```
FortID{humans_are_not_good_random_number_generators}
```

## 8. Key takeaways

- **What tipped me off:** a XOR keystream that is *not* uniformly random
  (typed by a person, biased, low entropy) plus a public sample of it. That is
  enough to build a statistical model and use it as an oracle.
- **Why it worked:** the plaintext is structured (a QR with RS blocks), so the
  unknown splits into independent pieces that can each be verified on their
  own.
- **What I'll remember:** with any "random" data produced by a human, I check
  the flip rate and run lengths first — anything far from 0.5 is exploitable.
- **What I want to practise:** QR internals (RS blocks, interleaving, module
  placement) and n-gram / Markov predictors (Aaronson's oracle).

---

<a id="ru"></a>
# 02 — Human RNG
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔐 Crypto |
| **Файлы задания** | `encrypt.py`, `bitstream.txt`, `ciphertext.png` |
| **Статус** | ✅ Solved |
| **Флаг** | `FortID{humans_are_not_good_random_number_generators}` |

## 1. Условие

Флаг рисуется как **QR-код** (версия 6, коррекция H, маска 0, 41 × 41 = 1681
модуль) и XOR-ится с ключевым потоком. Поток — последние 1681 бит
`bitstream.txt`, строки битов, **набранной человеком**. Эти биты вырезаны
(`<1681-bits-redacted>`), а первые 1999 набранных бит открыты.

## 2. Первичный анализ

Сначала прочитал шифратор и посмотрел на сам поток:

```bash
cat encrypt.py      # QR v6-H, маска 0  ->  XOR с bits[-1681:]  ->  ciphertext.png
head -c 200 bitstream.txt
```

- `encrypt.py` сразу дал точный формат: `FortID{` + тело + `}`, тело — **ровно
  44 символа**, английские слова в нижнем регистре через `_`
  (`[a-z]+(?:_[a-z]+)+`).
- `ciphertext.png` — результат XOR 41 × 41, увеличенный ×10.
- Открытый префикс сразу показался мне подозрительным для случайного источника:
  бит **меняется в 70 % случаев** вместо 50 %, а серий длиннее 3 почти нет. Так
  люди и «набирают случайно» — избегают повторов. Название задачи говорило о том
  же.

## 3. Путь исследования

**Что я подтвердил**

- Обучил на префиксе из 1999 бит **марковскую модель 4-го порядка**. Она хорошо
  ловит этот перекос: сам префикс даёт ≈ **−0,59** log-likelihood на бит, а
  случайный шум — ≈ **−0,84**.
- Для любого кандидата `F` я могу посчитать `key = ciphertext ⊕ QR(F)`. Если `F`
  верен, ключ — это набранный человеком суффикс и оценивается как префикс; если
  символ неверен, модули QR, которые он задаёт, превращаются в шум, и оценка
  падает. То есть модель работает как **оракул правдоподобия** для открытого
  текста.

**Идея, которая сделала это практичным — оракул локален**

- QR v6-H хранит данные в **4 блоках Рида–Соломона** (по 15 байт данных),
  перемешанных по символу. Я сопоставил каждый модуль его блоку, и оракул стал
  оценивать каждый блок **отдельно** — он говорит не только *неверен ли*
  кандидат, но и *какая часть* текста неверна.
- Название формулирует тезис — *люди — плохие генераторы случайных чисел*.
  Уложив его ровно в 44 символа, я получил
  `humans_are_not_good_random_number_generators`, и оракул это подтвердил: все
  четыре блока оценились как человеческий префикс.

## 4. Инструменты и команды

```bash
pip install qrcode pillow numpy loguru
python3 solve.py handout/                       # проверить флаг
python3 solve.py handout/ "FortID{...other...}" # оценить любую гипотезу
```

См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. Прочитал `ciphertext.png`, взяв центр каждой клетки 10 × 10 → 1681 бит.
2. Обучил модель 4-го порядка на открытом префиксе (сглаженная по Лапласу
   `P(бит | 4 предыдущих бита)`).
3. Построил карту «модуль → RS-блок», повторив обход размещения модулей
   библиотеки `qrcode` для версии 6-H.
4. Для гипотезы посчитал `key = ct ⊕ QR(flag)` и его средний log-likelihood
   целиком и по каждому RS-блоку и сравнил с эталонами (человеческий префикс
   ≈ −0,59, шум ≈ −0,84).
5. Все четыре блока получились «человеческими» — флаг подтверждён.

## 6. Итоговое решение

```
$ python3 solve.py handout/
INFO     prefix: 1999 bits, flip rate 0.702
INFO     reference LL/bit: human prefix -0.592 | random noise -0.841
INFO     candidate FortID{humans_are_not_good_random_number_generators}
INFO       whole key LL/bit -0.579
INFO       RS block 0: LL/bit -0.606  human-like
INFO       RS block 1: LL/bit -0.565  human-like
INFO       RS block 2: LL/bit -0.597  human-like
INFO       RS block 3: LL/bit -0.570  human-like
SUCCESS  FLAG: FortID{humans_are_not_good_random_number_generators}
```

Оракул точен: если заменить только `not_good` другим словом из 8 букв, блоки 0,
2, 3 остаются «человеческими», а **только блок 1** падает до ≈ −0,76 — ровно тот
блок, в котором лежат эти символы.

## 7. Флаг

```
FortID{humans_are_not_good_random_number_generators}
```

## 8. Ключевые выводы

- **Что меня навело:** поток для XOR, который *не* равномерно случаен (набран
  человеком, смещён, с низкой энтропией), плюс открытый образец этого потока.
  Этого достаточно, чтобы построить статистическую модель и использовать её как
  оракул.
- **Почему сработало:** открытый текст структурирован (QR с RS-блоками), поэтому
  неизвестное распадается на независимые куски, каждый из которых проверяется
  отдельно.
- **Что запомню:** у любых «случайных» данных, созданных человеком, первым делом
  смотрю частоту смены бита и длины серий — всё, что далеко от 0,5,
  эксплуатируемо.
- **Что хочу потренировать:** внутреннее устройство QR (RS-блоки, перемежение,
  размещение модулей) и n-граммные / марковские предикторы (оракул Ааронсона).
