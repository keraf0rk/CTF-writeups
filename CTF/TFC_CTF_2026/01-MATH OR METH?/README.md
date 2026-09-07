<a id="en"></a>
# 01 — MATH OR METH?
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔐 Crypto |
| **Challenge file** | [`chall.py`](chall.py), [`output.py`](output.py) |
| **Status** | ✅ Solved |
| **Flag** | `TFCCTF{this_is_a_very_very_long_flag_for_a_short_ctf_chall_ggs}` |

## 1. Description

We are given the source `chall.py` and its printed `output.py`. The flag is
encoded as digits, hidden as **one row** of a small random matrix, and only a
secret mod-`p` linear combination of the rows is published.

```python
# chall.py (essential part)
msg = b"?"                       # the flag content placed inside TFCCTF{}
n = 57
B = 32
base = B + 1                     # = 33
p = getPrime(1084)

x = bytes_to_long(msg)
row = []                         # base-33 digits of x, little-endian
while x:
    row.append(x % base)
    x //= base

m = len(row)                     # = 88
assert n < m
a = [secrets.randbelow(p) for _ in range(n)]                 # secret coeffs
A = [[secrets.randbelow(base) for _ in range(m)] for _ in range(n)]
planted_idx = secrets.randbelow(n)
A[planted_idx] = row[:]          # one row IS the flag digits

h = [sum(a[i] * A[i][j] for i in range(n)) % p for j in range(m)]  # published
```

So `h` is a secret linear combination (mod `p`) of `n = 57` rows, each row a
vector of `m = 88` small digits in `[0, 33)`. One of those rows is the flag.

## 2. Initial analysis

Confirmed facts from `output.py`:

- `n = 57`, `m = 88`, `B = 32` (`base = 33`), `p` is a 1084-bit prime.
- `h` is a length-88 vector over `Z_p`.

`h` lies in the **integer row span (mod p) of a matrix with tiny entries**.
This is the textbook setup for an **orthogonal lattice attack** (Nguyen–Stern
hidden subset-sum family): vectors orthogonal to all the small rows over `Z`
are automatically orthogonal to `h` mod `p`, and they are short, so lattice
reduction isolates them.

## 3. Investigation path

1. Build the lattice `Λ = { u ∈ Z^m : ⟨u, h⟩ ≡ 0 (mod p) }`, reduce it (LLL).
   The reduced basis splits cleanly: exactly `m − n = 31` genuinely short
   vectors (they span `L_A^⊥`, orthogonal to every matrix row) and the rest
   are `~p`-scale. The sharp norm gap confirms the structure.
2. Take the orthogonal complement of those 31 vectors → recover `L_A`, the
   rank-`n = 57` integer lattice spanned by the matrix rows.
3. **Key subtlety:** the rows (norm ≈ 175, all entries in `[0, 33)`) are **not**
   the shortest vectors of `L_A` — their pairwise differences are shorter
   (≈ 102), so plain LLL/BKZ returns mixed-sign junk, not the rows. But every
   row lives inside the box `[0, 33)^m` and sits ~90 from the box centre
   `(16, …, 16)`. So enumerate lattice points near the centre (Fincke–Pohst
   CVP enumeration) — that returns exactly the 57 rows.
4. Decode each row as base-33 little-endian → `bytes_to_long` inverse. Only the
   planted row decodes to readable ASCII.

## 4. Tools & commands

- Python 3, [`fpylll`](https://github.com/fplll/fpylll) (LLL/BKZ), `numpy`,
  `pycryptodome`, `loguru`.

```bash
pip install fpylll pycryptodome loguru numpy --break-system-packages
python3 solve.py
```

Solve script: [`flag_detected.py`](flag_detected.py).

## 5. Step-by-step

1. Parse `n, m, B, p, h` from `output.py`.
2. `orthogonal_lattice(h, p)` → basis of `Λ`; `LLL.reduction` → sort by norm →
   take the `m − n = 31` shortest = `L_A^⊥`.
3. `recover_row_lattice` → embed `[ I_m | 2^60·W^T ]`, LLL, keep rows with a
   zeroed tail = `L_A` (rank 57).
4. `box_lattice_points` → LLL+BKZ `L_A`, then Fincke–Pohst enumeration of all
   lattice points within radius 140 of `(16, …, 16)`, filtered to `[0, 33)^m`.
5. `decode_row` each candidate; the one that is printable ASCII is the message.
   `chall.py` says to place it in `TFCCTF{}`.

## 6. Solution

Running the script recovers the planted row, which decodes to
`this_is_a_very_very_long_flag_for_a_short_ctf_chall_ggs`, and `chall.py`
instructs to wrap the message in `TFCCTF{}`.

```
$ python3 solve.py
... recovered L_A^perp: 31 short vectors
... recovered L_A: rank 57
... recovered message row -> TFCCTF{this_is_a_very_very_long_flag_for_a_short_ctf_chall_ggs}
```

## 7. Flag

```
TFCCTF{this_is_a_very_very_long_flag_for_a_short_ctf_chall_ggs}
```

Status: ✅ **confirmed**.

## 8. Key takeaways

- **Signal to the right hypothesis:** `output = secret linear combination of
  small (0..B) vectors mod a large prime`, with a meaningful vector hidden
  among random ones → orthogonal lattice attack. The clean norm gap at index
  `m − n` after the first LLL is the confirmation you are on track.
- **False trail / time sink:** reducing `L_A` directly and expecting the rows to
  pop out. With `B > 1` the lattice minima are row *differences* (mixed signs),
  not the rows. Don't chase shortest vectors — the rows are box-constrained
  non-negative points, so switch to CVP enumeration around the box centre.
- **If `B = 1`** (0/1 vectors) the rows themselves are the shortest vectors and
  plain Nguyen–Stern finishes; the extra CVP step is only needed for `B > 1`.
- **Recognising this class in future:** any "hidden subset sum" / small-matrix
  mod-`p` combination. Recipe: `Λ` orthogonal-mod-`p` → LLL → gap at `m − n` →
  orthogonal complement → recover the small vectors (shortest for 0/1, box CVP
  otherwise).

---
<a id="ru"></a>
# 01 — MATH OR METH?
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔐 Crypto |
| **Файл задания** | [`chall.py`](chall.py), [`output.py`](output.py) |
| **Статус** | ✅ Решено |
| **Флаг** | `TFCCTF{this_is_a_very_very_long_flag_for_a_short_ctf_chall_ggs}` |

## 1. Условие

Даны исходник `chall.py` и его вывод `output.py`. Флаг кодируется в цифры,
прячется как **одна строка** небольшой случайной матрицы, а публикуется лишь
секретная линейная комбинация строк по модулю `p`.

```python
# chall.py (суть)
msg = b"?"                       # содержимое флага, что кладут внутрь TFCCTF{}
n = 57
B = 32
base = B + 1                     # = 33
p = getPrime(1084)

x = bytes_to_long(msg)
row = []                         # цифры x в base-33, little-endian
while x:
    row.append(x % base)
    x //= base

m = len(row)                     # = 88
assert n < m
a = [secrets.randbelow(p) for _ in range(n)]                 # секретные коэф.
A = [[secrets.randbelow(base) for _ in range(m)] for _ in range(n)]
planted_idx = secrets.randbelow(n)
A[planted_idx] = row[:]          # одна строка — это цифры флага

h = [sum(a[i] * A[i][j] for i in range(n)) % p for j in range(m)]  # публикуется
```

То есть `h` — секретная (mod `p`) линейная комбинация `n = 57` строк, каждая из
которых — вектор из `m = 88` малых цифр в `[0, 33)`. Одна из строк и есть флаг.

## 2. Первичный анализ

Подтверждено из `output.py`:

- `n = 57`, `m = 88`, `B = 32` (`base = 33`), `p` — простое на 1084 бита.
- `h` — вектор длины 88 над `Z_p`.

`h` лежит в **целочисленной оболочке строк (mod p) матрицы с крошечными
элементами**. Это классическая постановка для **orthogonal lattice attack**
(семейство Nguyen–Stern / hidden subset-sum): векторы, ортогональные всем малым
строкам над `Z`, автоматически ортогональны `h` по модулю `p` и при этом
короткие — редукция решётки их выделяет.

## 3. Путь исследования

1. Строим решётку `Λ = { u ∈ Z^m : ⟨u, h⟩ ≡ 0 (mod p) }`, редуцируем (LLL).
   Базис делится чётко: ровно `m − n = 31` действительно коротких вектора (они
   натягивают `L_A^⊥`, ортогональный каждой строке матрицы), остальные —
   масштаба `~p`. Резкий разрыв норм подтверждает структуру.
2. Берём ортогональное дополнение к этим 31 векторам → восстанавливаем `L_A` —
   решётку ранга `n = 57`, натянутую на строки матрицы.
3. **Ключевой нюанс:** строки (норма ≈ 175, все элементы в `[0, 33)`) — **не**
   кратчайшие векторы `L_A`: их попарные разности короче (≈ 102), поэтому
   обычный LLL/BKZ выдаёт мусор со смешанными знаками, а не строки. Но каждая
   строка лежит в кубе `[0, 33)^m` и отстоит на ~90 от центра куба
   `(16, …, 16)`. Значит, перечисляем точки решётки рядом с центром
   (Fincke–Pohst CVP enumeration) — получаем ровно 57 строк.
4. Декодируем каждую строку как base-33 little-endian → обратно в байты. Только
   подсаженная строка декодируется в читаемый ASCII.

## 4. Инструменты и команды

- Python 3, [`fpylll`](https://github.com/fplll/fpylll) (LLL/BKZ), `numpy`,
  `pycryptodome`, `loguru`.

```bash
pip install fpylll pycryptodome loguru numpy --break-system-packages
python3 solve.py
```

Solve-скрипт: [`flag_detected.py`](flag_detected.py).

## 5. Пошаговое решение

1. Парсим `n, m, B, p, h` из `output.py`.
2. `orthogonal_lattice(h, p)` → базис `Λ`; `LLL.reduction` → сортируем по норме →
   берём `m − n = 31` кратчайших = `L_A^⊥`.
3. `recover_row_lattice` → embedding `[ I_m | 2^60·W^T ]`, LLL, оставляем строки
   с занулённым хвостом = `L_A` (ранг 57).
4. `box_lattice_points` → LLL+BKZ по `L_A`, затем перечисление Fincke–Pohst всех
   точек решётки в радиусе 140 от `(16, …, 16)`, отфильтрованных по `[0, 33)^m`.
5. `decode_row` каждого кандидата; читаемый ASCII — это сообщение. `chall.py`
   велит поместить его в `TFCCTF{}`.

## 6. Итоговое решение

Скрипт восстанавливает подсаженную строку, которая декодируется в
`this_is_a_very_very_long_flag_for_a_short_ctf_chall_ggs`, а `chall.py`
предписывает обернуть сообщение в `TFCCTF{}`.

```
$ python3 solve.py
... recovered L_A^perp: 31 short vectors
... recovered L_A: rank 57
... recovered message row -> TFCCTF{this_is_a_very_very_long_flag_for_a_short_ctf_chall_ggs}
```

## 7. Флаг

```
TFCCTF{this_is_a_very_very_long_flag_for_a_short_ctf_chall_ggs}
```

Статус: ✅ **подтверждён**.

## 8. Ключевые выводы

- **Сигнал к правильной гипотезе:** `вывод = секретная линейная комбинация малых
  (0..B) векторов по модулю большого простого`, с осмысленным вектором среди
  случайных → orthogonal lattice attack. Чёткий разрыв норм на индексе `m − n`
  после первого LLL — подтверждение, что путь верный.
- **Ложный след / потеря времени:** редуцировать `L_A` напрямую и ждать, что
  строки «всплывут». При `B > 1` минимумы решётки — это *разности* строк
  (смешанные знаки), а не сами строки. Не гоняйся за кратчайшими векторами —
  строки это неотрицательные точки в кубе, поэтому переходим к CVP-перечислению
  вокруг центра куба.
- **Если `B = 1`** (0/1 векторы), строки сами — кратчайшие векторы, и хватает
  чистого Nguyen–Stern; дополнительный CVP-шаг нужен только при `B > 1`.
- **Как распознать в будущем:** любая «hidden subset sum» / комбинация малой
  матрицы по модулю `p`. Рецепт: `Λ` ортогонально-mod-`p` → LLL → разрыв на
  `m − n` → ортогональное дополнение → восстановить малые векторы (кратчайшие
  для 0/1, box-CVP иначе).
