<a id="en"></a>
# 02 — The Courier's Browser

**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🧬 Forensics |
| **Challenge file** | `task_2.rar` (~38 MB) |
| **Status** | ✅ Solved |
| **Flag** | `ozonctf{34s4_br0w33r_h1st0ry_l00kup_ab3faccd1}` |

## 1. Description

> Space station *Express-66* detected anomalous activity in the delivery system. A courier
> intends to disrupt deliveries. We identified him and dumped **one directory of his browser**.
> Find proof of his intentions — that is the flag.

## 2. Initial analysis

`task_2.rar` turned out to be a dump of a **Yandex Browser** profile (`Default/…`: `History`,
`Login Data`, `Ya Passman Data`, `Cache`, `Local Storage`, `Sessions`, …).

```bash
file task_2.rar          # RAR archive data, v5
```

It is RAR5, and `7z` failed on many files with `Unsupported Method`, so I used the real `unrar`.

## 3. Investigation path

With a browser dump, I reckoned the courier's **intentions** would be in his **browsing history**
and the associated key-value stores, so I grepped everything for the flag format.

## 4. Tools & commands

```bash
sudo apt-get install -y unrar
unrar x -o+ task_2.rar ./extracted/

cd extracted
grep -rialE "ozonctf|flag\{" .
# hits: Default/History, Local Storage, Session Storage, Sessions/Tabs_*
```

## 5. Step-by-step

I pulled the flag string out of `History`:

```bash
strings -n 5 "Default/History" | grep -iaE "ozonctf"
```

The courier had searched for the flag (URL-encoded) — both on ozon.ru and through a URL-decode tool:

```
https://www.ozon.ru/search/?text=ozonctf%257B34s4_br0w33r_h1st0ry_l00kup_ab3faccd1%257D
input=ozonctf%7B34s4_br0w33r_h1st0ry_l00kup_ab3faccd1%7D
```

`%7B` → `{`, `%7D` → `}`.

## 6. Solution

Automated: [`./find_flag.sh`](./find_flag.sh)

```bash
./find_flag.sh task_2.rar
```

## 7. Flag

```
ozonctf{34s4_br0w33r_h1st0ry_l00kup_ab3faccd1}
```

## 8. Key takeaways

- RAR5 dumps: I reach for `unrar` over `7z` (which chokes on `Unsupported Method`).
- Browser artifacts (`History`, `Local Storage`, `Session Storage`, `Sessions`) are gold for
  forensics — one recursive `grep` for the flag format saved me a lot of time.
- I watched for decoys: a bare `ozonctf` search without braces was present, but the real flag was
  the neighbouring URL-encoded entry with `{}`.

---

<a id="ru"></a>
# 02 — Браузер курьера

[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🧬 Форензика |
| **Файл задания** | `task_2.rar` (~38 МБ) |
| **Статус** | ✅ Решено |
| **Флаг** | `ozonctf{34s4_br0w33r_h1st0ry_l00kup_ab3faccd1}` |

## 1. Условие

> Космическая станция *Экспресс-66*: в системе доставки аномальная активность. Курьер намерен
> сорвать доставки. Личность установили и выгрузили **один из каталогов его браузера**.
> Найди доказательство намерений — это и есть флаг.

## 2. Первичный анализ

`task_2.rar` оказался выгрузкой профиля **Yandex Browser** (`Default/…`: `History`, `Login Data`,
`Ya Passman Data`, `Cache`, `Local Storage`, `Sessions`, …).

```bash
file task_2.rar          # RAR archive data, v5
```

Это **RAR5**, и `7z` споткнулся на части файлов (`Unsupported Method`), поэтому я взял `unrar`.

## 3. Путь исследования

С дампом браузера я решил, что намерения курьера будут в **истории** и связанных key-value
хранилищах, поэтому прогрепал всё по формату флага.

## 4. Инструменты и команды

```bash
sudo apt-get install -y unrar
unrar x -o+ task_2.rar ./extracted/

cd extracted
grep -rialE "ozonctf|flag\{" .
# попадания: Default/History, Local Storage, Session Storage, Sessions/Tabs_*
```

## 5. Пошаговое решение

Достал строку флага из `History`:

```bash
strings -n 5 "Default/History" | grep -iaE "ozonctf"
```

Курьер сам искал флаг (URL-encoded) — и на ozon.ru, и через URL-декодер:

```
https://www.ozon.ru/search/?text=ozonctf%257B34s4_br0w33r_h1st0ry_l00kup_ab3faccd1%257D
input=ozonctf%7B34s4_br0w33r_h1st0ry_l00kup_ab3faccd1%7D
```

`%7B` → `{`, `%7D` → `}`.

## 6. Итоговое решение

Автоматизация: [`./find_flag.sh`](./find_flag.sh)

```bash
./find_flag.sh task_2.rar
```

## 7. Флаг

```
ozonctf{34s4_br0w33r_h1st0ry_l00kup_ab3faccd1}
```

## 8. Ключевые выводы

- RAR5-дампы: я беру `unrar` вместо `7z` (тот падает на `Unsupported Method`).
- Артефакты браузера (`History`, `Local Storage`, `Session Storage`, `Sessions`) — золото для
  форензики; один рекурсивный `grep` по формату флага сэкономил мне время.
- Я следил за приманками: голый запрос `ozonctf` без скобок был, но реальный флаг — соседняя
  URL-encoded запись с `{}`.
