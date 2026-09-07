<a id="en"></a>
# 04 — Millennium Goose

**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔎 OSINT (+ light stego) |
| **Challenge file** | `plain.png` (561×376) |
| **Status** | 🚧 Unsolved (flag not accepted) |
| **Flag** | _not confirmed — see step 7_ |

Technique & location are certain (Ural Airlines A321 **VQ-BOZ**, Flight 178 landing site), but
**no coordinate variant was accepted** by the scorebot — the expected value/format is still open.

## 1. Description

> The fastest courier starship **"Millennium Goose"** has disappeared, and a suspicious man
> claims it is his ship. If you are the real owner, prove it by **decrypting its current location**.
> Flag format: `ozonctf{xx.xxx_yy.yyy}`.

## 2. Initial analysis

`plain.png` is dark with horizontal banding. No LSB text, no appended data, the "black" rows carry
only noise. Row statistics show a **2-content / 2-erased** row pattern (period 4) — half the rows
are zeroed out, which is the "encryption".

## 3. Investigation path

Reconstruct the image by interpolating the erased rows, then geolocate the revealed photo.

## 4. Tools & commands

`Python` (NumPy, Pillow) · reverse image search (Yandex Images) · Wikimedia Commons · Wikipedia.

```bash
python3 ./solve_reconstruct.py plain.png   # -> recon.png
```

## 5. Step-by-step

1. Reconstruction reveals a photo of an **Ural Airlines Airbus A321** on an apron with a fire truck.
2. Reverse image search + livery → *Ural Airlines, A320/A321*.
3. On Wikimedia Commons the registration **VQ-BOZ** sits next to `Wreckage of Ural Airlines Flight 178`
   → this is the aircraft of **Flight 178**.
4. **Flight 178** (15 Aug 2019): bird strike → forced landing in a cornfield near the village
   **Rybaki**, close to Zhukovsky. The ship's "current location" = the landing site.
5. Coordinates (Yandex POI *"Место аварийной посадки А321 под Жуковским"* / RU Wikipedia):
   **55.5104, 38.2533** (EN Wikipedia: 55.5108, 38.2526).

## 6. Solution

The disappeared "starship" = Ural Airlines A321 **VQ-BOZ** that force-landed near Zhukovsky.

## 7. Flag — 🚧 not confirmed

The location is certain (Flight 178 landing site), but **none of the submitted coordinate variants
were accepted**:

| Tried | Verdict |
|---|---|
| `ozonctf{55.511_38.253}` | "close, but not quite" |
| `ozonctf{55.512_38.252}` | "close" |
| `ozonctf{55.510_38.253}` | not accepted |

Team feedback pointed to the coordinates being "just wrong". Open hypotheses for the exact answer:
the point the challenge author actually used may differ (e.g. the **field-centre pin** vs. the
Wikipedia article coordinate), a different **precision/rounding**, or **lat/lon order swapped**.
Needs the exact source POI to lock the flag.

## 8. Key takeaways

- "Dark, banded PNG" ⇒ check the **row structure** first (erased/interleaved rows) before LSB tools.
- Aircraft OSINT: livery → airline, then **Wikimedia Commons categories by registration** tie a
  photo to a specific tail number and its history.
- Coordinate flags: match the rounding of the source the author likely used (RU challenge →
  Yandex Maps POI / RU Wikipedia).

---

<a id="ru"></a>
# 04 — Миллениум Гусь

[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔎 OSINT (+ лёгкое стего) |
| **Файл задания** | `plain.png` (561×376) |
| **Статус** | 🚧 Не решено (флаг не принят) |
| **Флаг** | _не подтверждён — см. п. 7_ |

Техника и локация установлены однозначно (A321 «Уральских авиалиний» **VQ-BOZ**, место посадки
рейса 178), но **ни один вариант координат не принят** ботом — точное значение/формат пока открыты.

## 1. Условие

> Пропал самый быстрый курьерский звездолёт **«Миллениум Гусь»**, а подозрительный тип
> утверждает, что это его корабль. Докажи владение, **расшифровав его текущее местоположение**.
> Формат: `ozonctf{xx.xxx_yy.yyy}`.

## 2. Первичный анализ

`plain.png` — тёмный, с горизонтальными полосами. Нет LSB-текста, нет приписанных данных,
«чёрные» строки несут только шум. Построчная статистика: шаблон **2 контентные / 2 обнулённые**
(период 4) — половина строк стёрта, это и есть «шифр».

## 3. Путь исследования

Восстановить изображение, интерполировав стёртые строки, затем геолоцировать проявившееся фото.

## 4. Инструменты и команды

`Python` (NumPy, Pillow) · реверс-поиск (Яндекс.Картинки) · Wikimedia Commons · Wikipedia.

```bash
python3 ./solve_reconstruct.py plain.png   # -> recon.png
```

## 5. Пошаговое решение

1. Восстановление проявляет фото **Airbus A321 «Уральских авиалиний»** на перроне + пожарная машина.
2. Реверс-поиск + ливрея → *Уральские авиалинии, A320/A321*.
3. На Wikimedia Commons борт **VQ-BOZ** соседствует с `Wreckage of Ural Airlines Flight 178`
   → это самолёт **рейса 178**.
4. **Рейс 178** (15.08.2019): столкновение с птицами → вынужденная посадка в кукурузном поле у
   деревни **Рыбаки** под Жуковским. «Текущее местоположение» борта = место посадки.
5. Координаты (Яндекс-POI «Место аварийной посадки А321 под Жуковским» / RU-Wikipedia):
   **55.5104, 38.2533** (EN-Wikipedia: 55.5108, 38.2526).

## 6. Итоговое решение

Пропавший «звездолёт» = A321 «Уральских авиалиний» **VQ-BOZ**, севший в поле под Жуковским.

## 7. Флаг — 🚧 не подтверждён

Локация установлена точно (место посадки рейса 178), но **ни один вариант координат не принят**:

| Пробовали | Вердикт |
|---|---|
| `ozonctf{55.511_38.253}` | «Близко, но не совсем» |
| `ozonctf{55.512_38.252}` | «Близко» |
| `ozonctf{55.510_38.253}` | не принят |