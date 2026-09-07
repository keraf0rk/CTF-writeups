<a id="en"></a>
# 03 — Space Noise

**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🖼️ Steganography (audio) |
| **Challenge file** | `task.wav` (55 s, stereo, 44.1 kHz) |
| **Status** | ✅ Solved |
| **Flag** | `ozonctf{S3CR3TD3L1V3RYM3SS4G3}` |

## 1. Description

> During a routine cargo flight the operator recorded an acoustic anomaly — a short but
> strangely structured fragment, like **breathing through an aqualung**. What is hidden in the noise?

Metadata: `artist=OzonCTF`, `title=Space Noise`, `genre=Space Voices`.

## 2. Initial analysis

Full and per-channel spectrograms show only a broadband noise **cover** (the "breathing"). No visible text.

```bash
sox task.wav -n spectrogram -o spec.png     # noise only
```

## 3. Investigation path

The file is **stereo**. Take the channel difference **L − R** — the common (mono-like) cover
cancels and a clean hidden signal remains. Discrete tonal bursts in 0–4 kHz (≈ 6–37.5 s) → **Morse**.

## 4. Tools & commands

`Python` (NumPy) · `SoX`. Envelope analysis gives two durations: **dot ≈ 124 ms**,
**dash ≈ 363 ms** (exactly ×3). 80 symbols, decoded with zero errors.

## 5. Step-by-step

```bash
python3 ./flag_s.py task.wav
# Морзе-сообщение: S3CR3TD3L1V3RYM3SS4G3
# Флаг: ozonctf{S3CR3TD3L1V3RYM3SS4G3}
```

## 6. Solution

Message: `S3CR3TD3L1V3RYM3SS4G3` → **"SECRET DELIVERY MESSAGE"** (leet).

## 7. Flag

```
ozonctf{S3CR3TD3L1V3RYM3SS4G3}
```

## 8. Key takeaways

- Stereo challenge? Always check **L − R** (and L + R): a mono cover cancels and exposes the payload.
- Two clean pulse lengths in a 1:3 ratio ⇒ Morse. Estimate the dot as the median short-burst length.

---

<a id="ru"></a>
# 03 — Космический шум

[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🖼️ Стеганография (аудио) |
| **Файл задания** | `task.wav` (55 c, stereo, 44.1 кГц) |
| **Статус** | ✅ Решено |
| **Флаг** | `ozonctf{S3CR3TD3L1V3RYM3SS4G3}` |

## 1. Условие

> Во время грузового рейса оператор зафиксировал акустическую аномалию — короткий, но странно
> структурированный фрагмент, похожий на **дыхание через акваланг**. Что закодировано в шуме?

Метаданные: `artist=OzonCTF`, `title=Space Noise`, `genre=Space Voices`.

## 2. Первичный анализ

Полная и поканальная спектрограммы — только шумовой **cover** («дыхание»). Текста нет.

```bash
sox task.wav -n spectrogram -o spec.png     # только шум
```

## 3. Путь исследования

Файл **стерео**. Берём разность каналов **L − R** — общий (моно-подобный) cover вычитается,
остаётся чистый сигнал: дискретные тональные всплески 0–4 кГц (≈ 6–37.5 c) → **Морзе**.

## 4. Инструменты и команды

`Python` (NumPy) · `SoX`. Анализ огибающей даёт две длительности: **точка ≈ 124 мс**,
**тире ≈ 363 мс** (ровно ×3). 80 символов, декод без ошибок.

## 5. Пошаговое решение

```bash
python3 ./flag_s.py task.wav
# Морзе-сообщение: S3CR3TD3L1V3RYM3SS4G3
# Флаг: ozonctf{S3CR3TD3L1V3RYM3SS4G3}
```

## 6. Итоговое решение

Сообщение: `S3CR3TD3L1V3RYM3SS4G3` → **«SECRET DELIVERY MESSAGE»** (лит).

## 7. Флаг

```
ozonctf{S3CR3TD3L1V3RYM3SS4G3}
```

## 8. Ключевые выводы

- Стерео-таск? Всегда проверяй **L − R** (и L + R): моно-cover вычитается и обнажает payload.
- Две чистые длительности импульсов в отношении 1:3 ⇒ Морзе. Точку оцениваем как медиану коротких всплесков.
