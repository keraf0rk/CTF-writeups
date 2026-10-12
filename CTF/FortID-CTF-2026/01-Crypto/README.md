<a id="en"></a>
# 01 — Hic Sunt Dracones
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔐 Crypto |
| **Challenge files** | `chall.py`, `patch.py`, `Dockerfile`, `output.txt` |
| **Status** | ✅ Solved |
| **Flag** | `FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}` |

## 1. Description

The challenge gave me a script that encodes the flag onto an elliptic curve
with **Koblitz encoding** and then "encrypts" every point with the third-party
library [Dragon-Crypto](https://github.com/awnonbhowmik/Dragon-Crypto)
(commit `046ad8d`): each point is pushed through a turtle that walks a
**dragon curve**. The private key is `(size, iterations, start_angle, a, b)`
with `size ∈ [2^127, 2^128)`, `iterations ∈ [10, 15)`,
`start_angle ∈ {0, 180}`. `output.txt` held the encrypted points.

## 2. Initial analysis

I started by reading everything that was shipped:

```bash
cat Dockerfile     # clones Dragon-Crypto @046ad8d, applies patch.py
cat patch.py       # only makes koblitz_encoder work with a 256-bit prime
cat chall.py       # headless turtle, random curve, encrypt every character
```

Then I pulled `koblitz.py` and `dragon.py` from that exact commit. Two things
stood out right away:

- `koblitz_encoder` maps a character to a point with
  **`x = ord(ch) · 20 + j`, `j ∈ [1, 19]`**. So the plaintext is sitting **in
  the clear** inside `x`: `ch = (x − 1) // 20`.
- `dragon_render` is not real cryptography at all: the turtle only turns by
  **±90°** and steps forward by `size`, so the whole walk just **translates**
  the point by `size · u`, where `u` is a small integer vector that depends
  only on `iterations`.

From that moment I stopped caring about the curve parameters `a, b, p` — they
never influence the result.

## 3. Investigation path

**What I confirmed**

- `chall.py` reuses **one turtle** for every point and never resets its
  heading. I simulated the walk with `size = 1` and saw that for an even number
  of iterations the net displacement lies on a single axis, and because the
  heading keeps accumulating, that axis alternates from point to point:
  - **even** points move along **Y**, so their `x` is the untouched Koblitz
    `x` — these are the small numbers in `output.txt`;
  - **odd** points move along **X** by **`±C`**, `C = size · |u|` — the huge
    numbers. My simulation gave `|u| = 32 / 64 / 128` for
    `iterations = 10 / 12 / 14`; the `C` I recovered, together with
    `size ∈ [2^127, 2^128)`, matches `|u| = 128`.
- That meant the whole key boiled down to **one integer `C`**.

**The idea that solved it — known plaintext**

- I know the flag starts with `FortID{`. Positions 1, 3 and 5 are odd and hold
  `o`, `t`, `D`. For a known character the original `x0` must lie in
  `[20·ord(ch)+1, 20·ord(ch)+19]`, so every known odd character squeezes `C`
  into a window of 19 values. I intersected those windows, added
  `C % 128 == 0`, and was left with **exactly one** `C`.

## 4. Tools & commands

```bash
python3 solve.py handout/output.txt
```

Plain Python — I didn't need any curve arithmetic. See [`solve.py`](solve.py).

## 5. Step-by-step

1. I parsed `output.txt` (`X<x0>X<x1>…XY<y0>Y…`) and kept only the `x` values.
2. For even indices I took `x0 = x` as is (they were shifted only along Y).
3. For odd indices `x = x0 ± C`. Using `o`, `t`, `D` at indices 1, 3, 5 I
   computed `C ∈ [|x| − (20·ord+19), |x| − (20·ord+1)]` and intersected the
   ranges.
4. I kept the `C` divisible by 128 and checked that
   `size = C / 128 ∈ [2^127, 2^128)` ✔.
5. I removed the shift from every odd point and decoded
   `ch = (x0 − 1) // 20`.

## 6. Solution

```
$ python3 solve.py handout/output.txt
INFO     points: 78, shift C = 35585610297891858588915664867994857253760 (size = C / 128 = 278012580452280145225903631781209822295)
SUCCESS  FLAG: FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}
```

## 7. Flag

```
FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}
```

## 8. Key takeaways

- **What tipped me off:** a home-made "cipher" stacked on top of a standard
  encoding. Checking whether the encoding itself leaks the plaintext paid off
  immediately — Koblitz keeps it in `x`.
- **Why it worked:** 90° turns plus forward steps form an affine map — here a
  plain translation — so the "key" collapsed into a single number, and one
  known character was enough to pin it.
- **Where I lost time:** I first tried to recover `size` directly with
  `round(X / u)`; it gave garbage because `x0` is not negligible. Bounding `C`
  with intervals was the right move. The elliptic curve itself was a decoy.
- **What I'll remember:** state that survives between encryption calls (here
  the turtle heading) creates alternating patterns — splitting the ciphertext
  by index parity is worth trying early.

---

<a id="ru"></a>
# 01 — Hic Sunt Dracones
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔐 Crypto |
| **Файлы задания** | `chall.py`, `patch.py`, `Dockerfile`, `output.txt` |
| **Статус** | ✅ Solved |
| **Флаг** | `FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}` |

## 1. Условие

В задании был скрипт, который кодирует флаг на эллиптическую кривую
**кодированием Коблица**, а затем «шифрует» каждую точку сторонней библиотекой
[Dragon-Crypto](https://github.com/awnonbhowmik/Dragon-Crypto) (коммит `046ad8d`):
точка прогоняется через черепаху, рисующую **кривую дракона**. Приватный ключ —
`(size, iterations, start_angle, a, b)`, где `size ∈ [2^127, 2^128)`,
`iterations ∈ [10, 15)`, `start_angle ∈ {0, 180}`. В `output.txt` лежали
зашифрованные точки.

## 2. Первичный анализ

Начал с того, что прочитал всё, что выдали:

```bash
cat Dockerfile     # клонирует Dragon-Crypto @046ad8d, применяет patch.py
cat patch.py       # лишь адаптирует koblitz_encoder под 256-битное простое
cat chall.py       # «безголовая» черепаха, случайная кривая, шифрование символов
```

Потом скачал `koblitz.py` и `dragon.py` именно из этого коммита. Сразу бросились
в глаза две вещи:

- `koblitz_encoder` переводит символ в точку по формуле
  **`x = ord(ch) · 20 + j`, `j ∈ [1, 19]`**. То есть открытый текст лежит
  **в открытом виде** прямо в `x`: `ch = (x − 1) // 20`.
- `dragon_render` вообще не криптография: черепаха поворачивается только на
  **±90°** и шагает на `size`, поэтому весь проход просто **сдвигает** точку на
  `size · u`, где `u` — небольшой целочисленный вектор, зависящий только от
  `iterations`.

С этого момента я перестал обращать внимание на параметры кривой `a, b, p` —
на результат они не влияют.

## 3. Путь исследования

**Что я подтвердил**

- `chall.py` использует **одну черепаху** для всех точек и не сбрасывает её
  курс. Я просимулировал проход с `size = 1` и увидел, что при чётном числе
  итераций итоговое смещение лежит на одной оси, а из-за накопления курса эта
  ось чередуется от точки к точке:
  - **чётные** точки сдвигаются по **Y**, поэтому их `x` — нетронутый `x`
    Коблица (маленькие числа в `output.txt`);
  - **нечётные** сдвигаются по **X** на **`±C`**, `C = size · |u|` (огромные
    числа). Симуляция дала `|u| = 32 / 64 / 128` для `iterations = 10 / 12 / 14`;
    найденное `C` вместе с `size ∈ [2^127, 2^128)` соответствует `|u| = 128`.
- Получилось, что весь ключ сводится к **одному целому числу `C`**.

**Идея, которая решила задачу — известный открытый текст**

- Я знаю, что флаг начинается с `FortID{`. Позиции 1, 3 и 5 нечётные, в них
  `o`, `t`, `D`. Для известного символа исходный `x0` обязан лежать в
  `[20·ord(ch)+1, 20·ord(ch)+19]`, значит каждый такой символ зажимает `C` в
  окно из 19 значений. Я пересёк эти окна, добавил условие `C % 128 == 0` — и
  осталось **ровно одно** `C`.

## 4. Инструменты и команды

```bash
python3 solve.py handout/output.txt
```

Обычный Python — арифметика на кривой мне не понадобилась. См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. Распарсил `output.txt` (`X<x0>X<x1>…XY<y0>Y…`) и оставил только значения `x`.
2. Для чётных индексов взял `x0 = x` как есть (их сдвигало только по Y).
3. Для нечётных `x = x0 ± C`. По символам `o`, `t`, `D` на позициях 1, 3, 5
   посчитал `C ∈ [|x| − (20·ord+19), |x| − (20·ord+1)]` и пересёк диапазоны.
4. Оставил `C`, кратное 128, и проверил, что `size = C / 128 ∈ [2^127, 2^128)` ✔.
5. Снял сдвиг со всех нечётных точек и декодировал `ch = (x0 − 1) // 20`.

## 6. Итоговое решение

```
$ python3 solve.py handout/output.txt
INFO     points: 78, shift C = 35585610297891858588915664867994857253760 (size = C / 128 = 278012580452280145225903631781209822295)
SUCCESS  FLAG: FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}
```

## 7. Флаг

```
FortID{1f_D0n_Knu7h_H4s_1t_0n_th3_W4ll_Th3n_17_Mu57_B3_G00d_F0r_Crypt0_r1ght?}
```

## 8. Ключевые выводы

- **Что меня навело:** самописный «шифр» поверх стандартного кодирования.
  Проверка, не утекает ли открытый текст через само кодирование, окупилась
  сразу — у Коблица он остаётся в `x`.
- **Почему сработало:** повороты на 90° плюс шаги вперёд — аффинное
  преобразование, здесь обычный сдвиг, поэтому «ключ» схлопнулся в одно число, и
  одного известного символа хватило, чтобы его зафиксировать.
- **Где я потерял время:** сначала пытался найти `size` напрямую через
  `round(X / u)` — получался мусор, потому что `x0` не пренебрежимо мал. Правильным
  ходом было ограничивать `C` интервалами. Сама эллиптическая кривая — приманка.
- **Что запомню:** состояние, которое переживает вызовы шифрования (курс
  черепахи), даёт чередующиеся паттерны — разделить шифртекст по чётности индекса
  стоит попробовать сразу.
