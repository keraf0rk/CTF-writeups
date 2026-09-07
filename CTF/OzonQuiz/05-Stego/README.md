<a id="en"></a>
# 05 — The Coffee-Machine Call

**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🖼️ Steganography (audio) |
| **Challenge file** | `Task_5.wav` (93 s, stereo, 44.1 kHz) |
| **Status** | ✅ Solved |
| **Flag** | `ozonctf{S3CR3T_CH4NN31}` * |

`*` content — "SECRET CHANNEL" — is certain; the final letter `L` was tuned
(`CH4NN31` vs `CH4NN3L`), see step 7.

## 1. Description

> Hyperdrive blueprints vanished from the SITH warehouse. A strange new employee phoned his wife
> from a work terminal, talking about **"pigeons"** and **"the weather"**, mentioning
> **"coffee machines"** (though we only have kettles!), and naming suspicious **numbers**.
> Figure out what data he was transmitting under the guise of an ordinary conversation.

Container: a stock "office sounds" clip (`Sound-Pack.net`) as cover; you can hear **keypad tones** and typing.

## 2. Initial analysis

Dead ends ruled out: **not** LSB, **not** steghide (themed-password brute), **not** a high-band
signal, **not** appended data, **not** a null-cipher on the spoken dialogue.

The tell is **"the sound of dialing digits" = DTMF**, buried under the office noise.

## 3. Investigation path

A single digit is pressed **several times in a row** → **multi-tap** (old-phone text entry):
`2=ABC`, `6=MNO`, `7=PQRS`, `9=WXYZ`… where *N* presses of a key = the *N*-th letter.
So `6×3 = O`, `9×4 = Z`, `7×4 = S`, `4×2 = H`, …

## 4. Tools & commands

`Python` (NumPy, SciPy). Goertzel over the 8 DTMF frequencies with a **tone-purity** filter to
reject speech/keyboard, plus per-letter tap counting via envelope peaks of the two tones.

```bash
python3 ./call.py Task_5.wav
```

## 5. Step-by-step

Decoded sequence (key `1` is structural: braces / separator):

```
OZONCTF { S3CR3T _ CH4NN3(1) }
```

- `S3CR3T` = **SECRET** (E→3) — confirmed: each `3` = key3 ×4.
- `CH4NN3L` = **CHANNEL** (A→4, E→3, L→1) — confirmed taps: C=2×3, H=4×2, 4=4×4, N=6×2, N=6×2, 3=3×4.
- There is **no clean key5 (L)** after `CH4NN3`; instead a **key1** press ⇒ the `L` was entered as leet `1`.

## 6. Solution

The "ordinary conversation" hid a DTMF multi-tap message: **"SECRET CHANNEL"**.

## 7. Flag

```
ozonctf{S3CR3T_CH4NN31}
```

> Alternative if the L is a literal letter: `ozonctf{S3CR3T_CH4NN3L}`.

## 8. Key takeaways

- "Sounds of dialing" over noise ⇒ **DTMF**. Repeated same-digit presses ⇒ **multi-tap** text.
- Reject speech with a **two-tone purity** test (real DTMF = exactly two pure tones); count taps
  by envelope peaks, not by naive thresholding.
- Story words ("pigeons", "weather", "coffee machines") were pure flavour/misdirection.

---

<a id="ru"></a>
# 05 — Звонок про кофемашины

[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🖼️ Стеганография (аудио) |
| **Файл задания** | `Task_5.wav` (93 c, stereo, 44.1 кГц) |
| **Статус** | ✅ Решено |
| **Флаг** | `ozonctf{S3CR3T_CH4NN31}` * |

`*` содержание — «SECRET CHANNEL» — установлено точно; финальная буква `L` подбиралась
(`CH4NN31` vs `CH4NN3L`), см. п. 7.

## 1. Условие

> На складе СТИ пропали чертежи гипердвигателя. Новый работник звонил жене со служебного терминала,
> говорил про **«голубей»** и **«погоду»**, упоминал **«кофемашины»** (хотя у нас только чайники!),
> называл подозрительные **цифры**. Разберись, какие данные он передавал под видом обычного разговора.

Контейнер — стоковый клип «звуки офиса» (`Sound-Pack.net`); слышны **тоны набора** и стук клавиатуры.

## 2. Первичный анализ

Отсекаем тупики: **не** LSB, **не** steghide (перебор тематических паролей), **не** ВЧ-сигнал,
**не** приписанные данные, **не** нуль-шифр по тексту разговора.

Ключ — **«звуки набора цифр» = DTMF**, спрятанные под офисным шумом.

## 3. Путь исследования

Одна цифра нажимается **по несколько раз подряд** → **multi-tap** (набор букв на кнопочном телефоне):
`2=ABC`, `6=MNO`, `7=PQRS`, `9=WXYZ`… где *N* нажатий = *N*-я буква.
Значит `6×3 = O`, `9×4 = Z`, `7×4 = S`, `4×2 = H`, …

## 4. Инструменты и команды

`Python` (NumPy, SciPy). Goertzel по 8 DTMF-частотам + фильтр по **чистоте тона** (отсекает
речь/клавиатуру) + точный подсчёт тапов по пикам огибающей двух тонов.

```bash
python3 ./call.py Task_5.wav
```

## 5. Пошаговое решение

Раскодированная последовательность (клавиша `1` — структурная: скобки / разделитель):

```
OZONCTF { S3CR3T _ CH4NN3(1) }
```

- `S3CR3T` = **SECRET** (E→3) — подтверждено: каждая `3` = key3 ×4.
- `CH4NN3L` = **CHANNEL** (A→4, E→3, L→1) — тапы: C=2×3, H=4×2, 4=4×4, N=6×2, N=6×2, 3=3×4.
- Чистой **key5 (L)** после `CH4NN3` нет; вместо неё нажатие **key1** ⇒ `L` набрана как лит `1`.

## 6. Итоговое решение

«Обычный разговор» прятал DTMF-multitap сообщение: **«SECRET CHANNEL»**.

## 7. Флаг

```
ozonctf{S3CR3T_CH4NN31}
```

> Вариант, если L — буква: `ozonctf{S3CR3T_CH4NN3L}`.

## 8. Ключевые выводы

- «Звуки набора» поверх шума ⇒ **DTMF**. Повторные нажатия одной цифры ⇒ **multi-tap** текст.
- Речь отсекаем тестом на **чистоту двух тонов** (реальный DTMF = ровно два чистых тона); тапы
  считаем по пикам огибающей, а не наивным порогом.
- Слова из сюжета («голуби», «погода», «кофемашины») — чистая маскировка.