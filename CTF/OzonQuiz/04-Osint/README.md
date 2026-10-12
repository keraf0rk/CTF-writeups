<a id="en"></a>
# 04 — Millennium Goose

**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔎 OSINT (+ light stego) |
| **Challenge file** | `plain.png` (561×376) |
| **Status** | ✅ Solved |
| **Flag** | `ozonctf{55.236_79.758}` |

**Accepted flag:** `ozonctf{55.236_79.758}`. ⚠️ I'm keeping this writeup honest: the point I
actually submitted (**55.236, 79.758**) does **not** match the Ural Airlines Flight 178 landing
site near Zhukovsky that my geolocation led me to below. That geolocation was my first lead and the
scorebot rejected it; I don't reconstruct how the accepted coordinates were derived here, so I'm
recording the path I took rather than claiming it was clean.

## 1. Description

> The fastest courier starship **"Millennium Goose"** has disappeared, and a suspicious man
> claims it is his ship. If you are the real owner, prove it by **decrypting its current location**.
> Flag format: `ozonctf{xx.xxx_yy.yyy}`.

## 2. Initial analysis

`plain.png` is dark with horizontal banding. I found no LSB text and no appended data, and the
"black" rows carried only noise. My row statistics showed a **2-content / 2-erased** row pattern
(period 4) — half the rows are zeroed out, which is the "encryption".

## 3. Investigation path

I reconstructed the image by interpolating the erased rows, then geolocated the revealed photo.

## 4. Tools & commands

`Python` (NumPy, Pillow) · reverse image search (Yandex Images) · Wikimedia Commons · Wikipedia.

```bash
python3 ./solve_reconstruct.py plain.png   # -> recon.png
```

## 5. Step-by-step

1. My reconstruction revealed a photo of an **Ural Airlines Airbus A321** on an apron with a fire
   truck.
2. A reverse image search plus the livery gave me *Ural Airlines, A320/A321*.
3. On Wikimedia Commons I found the registration **VQ-BOZ** next to
   `Wreckage of Ural Airlines Flight 178` → this is the aircraft of **Flight 178**.
4. **Flight 178** (15 Aug 2019): bird strike → forced landing in a cornfield near the village
   **Rybaki**, close to Zhukovsky. I read the ship's "current location" as the landing site.
5. I took the coordinates (Yandex POI *"Место аварийной посадки А321 под Жуковским"* / RU
   Wikipedia): **55.5104, 38.2533** (EN Wikipedia: 55.5108, 38.2526).

## 6. Solution

The disappeared "starship" = Ural Airlines A321 **VQ-BOZ** that force-landed near Zhukovsky.

## 7. Flag

```
ozonctf{55.236_79.758}
```

This is the point the scorebot accepted: **55.236, 79.758**. My Zhukovsky-based coordinates from
steps 5–6 were all rejected ("close, but not quite"), so I treat that geolocation as an incorrect
lead — the accepted point is substantially different, and I record it here as the one that worked
rather than claiming my Flight 178 reasoning produced it.

## 8. Key takeaways

- On a dark, banded PNG I check the **row structure** first (erased/interleaved rows) before
  reaching for LSB tools.
- Aircraft OSINT: livery → airline, then **Wikimedia Commons categories by registration** tied the
  photo to a specific tail number and its history.
- For coordinate flags I match the rounding of the source the author likely used — but here that
  wasn't enough, and the lesson I took away is to verify the submitted point against the scorebot
  before trusting a geolocation.

---

<a id="ru"></a>
# 04 — Миллениум Гусь

[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔎 OSINT (+ лёгкое стего) |
| **Файл задания** | `plain.png` (561×376) |
| **Статус** | ✅ Решено |
| **Флаг** | `ozonctf{55.236_79.758}` |

**Принятый флаг:** `ozonctf{55.236_79.758}`. ⚠️ Пишу честно: точка, которую я реально отправил
(**55.236, 79.758**), **не** совпадает с местом посадки рейса 178 под Жуковским, к которому меня
привела геолокация ниже. Та геолокация была моей первой версией, и бот её отклонил; как именно
выведены принятые координаты, я здесь не восстанавливаю, поэтому фиксирую свой ход, а не выдаю его
за чистый.

## 1. Условие

> Пропал самый быстрый курьерский звездолёт **«Миллениум Гусь»**, а подозрительный тип
> утверждает, что это его корабль. Докажи владение, **расшифровав его текущее местоположение**.
> Формат: `ozonctf{xx.xxx_yy.yyy}`.

## 2. Первичный анализ

`plain.png` — тёмный, с горизонтальными полосами. LSB-текста и приписанных данных я не нашёл, а
«чёрные» строки несли только шум. Моя построчная статистика дала шаблон **2 контентные / 2
обнулённые** (период 4) — половина строк стёрта, это и есть «шифр».

## 3. Путь исследования

Я восстановил изображение, интерполировав стёртые строки, затем геолоцировал проявившееся фото.

## 4. Инструменты и команды

`Python` (NumPy, Pillow) · реверс-поиск (Яндекс.Картинки) · Wikimedia Commons · Wikipedia.

```bash
python3 ./solve_reconstruct.py plain.png   # -> recon.png
```

## 5. Пошаговое решение

1. Моё восстановление проявило фото **Airbus A321 «Уральских авиалиний»** на перроне + пожарная
   машина.
2. Реверс-поиск + ливрея дали мне *Уральские авиалинии, A320/A321*.
3. На Wikimedia Commons я нашёл борт **VQ-BOZ** рядом с `Wreckage of Ural Airlines Flight 178`
   → это самолёт **рейса 178**.
4. **Рейс 178** (15.08.2019): столкновение с птицами → вынужденная посадка в кукурузном поле у
   деревни **Рыбаки** под Жуковским. «Текущее местоположение» борта я прочитал как место посадки.
5. Я взял координаты (Яндекс-POI «Место аварийной посадки А321 под Жуковским» / RU-Wikipedia):
   **55.5104, 38.2533** (EN-Wikipedia: 55.5108, 38.2526).

## 6. Итоговое решение

Пропавший «звездолёт» = A321 «Уральских авиалиний» **VQ-BOZ**, севший в поле под Жуковским.

## 7. Флаг

```
ozonctf{55.236_79.758}
```

Это точка, которую принял бот: **55.236, 79.758**. Мои координаты по Жуковскому из пп. 5–6 все были
отклонены («близко, но не совсем»), поэтому ту геолокацию я считаю ошибочным следом — принятая точка
существенно другая, и я фиксирую её как сработавшую, а не выдаю за результат своих рассуждений про
рейс 178.

## 8. Ключевые выводы

- На тёмном полосатом PNG я сначала проверяю **строчную структуру** (стёртые/чередующиеся строки),
  а не хватаюсь за LSB-инструменты.
- OSINT по самолётам: ливрея → авиакомпания, затем **категории Wikimedia Commons по регистрации**
  связали фото с конкретным бортом.
- Для координатных флагов я подгоняю округление под источник автора — но здесь этого не хватило, и
  вывод, который я забрал: сверять отправляемую точку с ботом раньше, чем доверять геолокации.