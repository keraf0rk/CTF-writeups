<a id="en"></a>
# 04 — Welcome
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🧬 Forensics |
| **Challenge file** | [`welcome.gif`](welcome.gif) |
| **Solve script** | [`solve.py`](solve.py) |
| **Status** | ✅ Solved |
| **Flag** | `THJCC{w3lc0me_t0_tHjCc_CTF_sUmM3r_ed1ti0n}` |

## 1. Description

> Welcome to THJCC Summer Edition~
> Please follow the rules and do not violate them!

The page carries the competition rules, the flag format `THJCC{...}` and one
attachment: `welcome.gif`. 100 points, author `xzhiyouu`. No hint text.

## 2. Initial analysis

The attachment previewed for me as a static black square with a white letter
`h` — but that is only the first frame. The container told me otherwise:

```bash
file welcome.gif               # GIF image data, version 89a, 800 x 600
identify welcome.gif | wc -l   # 57
```

- **Confirmed:** **57 frames**, 800x600, one large white glyph per frame → the
  GIF animates a string character by character.
- **Confirmed:** no plaintext in the file — `strings` returns only LZW noise and
  the palette ramp.
- **Confirmed:** walking the extension blocks finds **no comment block** and
  **no data after the `0x3B` trailer**; the only non-GCE block is the standard
  `NETSCAPE2.0` loop extension.

No metadata shortcut, so I had to get the payload out of the frames themselves.

## 3. Investigation path

**Step 1 — I read the frames.** A contact sheet made the whole string legible:

```bash
convert welcome.gif -coalesce -resize 100x75 miff:- \
  | montage - -tile 8x -geometry +2+2 -background gray50 -label '%p' sheet.png
```

The 57 glyphs, in order:

```
htps:/welcome.xzhiyou.idv.tw;Pas_code:NT9C-S8DP-D85B-Z8H6
```

**Step 2 — I noticed it was broken.** `htps:/` is not a scheme, `Pas_code` is
not a word. Both defects had the same shape: a character that should appear
**twice** appears once. My hypothesis was that the encoder wrote one frame per
*visible state*, so a run of two identical characters never produced a second
frame.

**Step 3 — the trap I hit.** Restoring the doubles by intuition was ambiguous,
and character arithmetic did **not** disambiguate it for me — both candidates
balance:

| Candidate | Full length | Collapsed runs | Frames implied |
|---|---|---|---|
| `https://welcome.xzhiyou.idv.tw;Pass_code:…` | 60 | `tt`, `//`, `ss` | 57 ✓ |
| `https://welcome.xzhiyouu.idv.tw;Pass_code:…` | 61 | `tt`, `//`, `uu`, `ss` | 57 ✓ |

I bet on the first one and got a host that answered with an **empty body** —
which reads like "the site is down", not "wrong hostname". It was a convincing
false lead that cost me time.

**Step 4 — I found the real channel.** Two measurements settled it for me.

First, I checked that no two consecutive coalesced frames are pixel-identical,
so the "dropped duplicate" idea needed evidence rather than intuition.

Then I found the per-frame delays are not uniform:

```bash
python3 -c "
from PIL import Image
im = Image.open('welcome.gif')
for i in range(im.n_frames):
    im.seek(i)
    print(i, im.info['duration'])
"
```

53 frames run at **50 ms**; exactly **4** run at **100 ms** — frames 1, 5, 20 and
31, carrying `t`, `/`, `u` and `s`. Those are precisely the four doubled
characters: a frame held twice as long stands in for two characters.

`u` was in that set, so the host is `xzhiyouu` — which also matches the
challenge author's handle, `xzhiyouu`.

## 4. Tools & commands

| Tool | Use |
|---|---|
| `file`, `identify` (ImageMagick) | container type, frame count |
| `convert` + `montage` (ImageMagick) | coalesce frames into a contact sheet |
| `strings` | rule out plaintext in the file |
| Pillow | frame seek, `info["duration"]`, duplicate detection |
| `loguru` | logging in `solve.py` |

```bash
file welcome.gif
identify welcome.gif | wc -l
strings welcome.gif | grep -aiE 'thjcc|flag|\{'

convert welcome.gif -coalesce -resize 100x75 miff:- \
  | montage - -tile 8x -geometry +2+2 -background gray50 -label '%p' sheet.png

pip install pillow loguru
python3 solve.py                      # defaults to ./welcome.gif
python3 solve.py --dump-frames out/   # also writes every frame + contact sheet
```

## 5. Step-by-step

1. `identify welcome.gif` showed 57 frames — not a still image.
2. `strings` and an extension-block walk gave me no plaintext flag and no
   comment block.
3. `convert -coalesce` + `montage` gave me a contact sheet; I read the 57 glyphs
   by eye.
4. I saw the transcription was malformed (`htps:/`, `Pas_code`).
5. I read `info["duration"]` per frame → two delay classes, 50 ms and 100 ms.
6. I doubled every 100 ms glyph → the full string.
7. I split on `;` → URL and pass code.
8. I opened the URL and submitted the 16-character code (dashes and case
   ignored).
9. The check-in page returned a pastebin link; the paste was the flag.

## 6. Solution

```console
$ python3 solve.py
INFO    read 57 frame durations from welcome.gif
INFO    delays: 50 ms x53 (single), 100 ms x4 (doubled)
INFO    frames as read : htps:/welcome.xzhiyou.idv.tw;Pas_code:NT9C-S8DP-D85B-Z8H6
INFO    reconstructed  : https://welcome.xzhiyouu.idv.tw;Pass_code:NT9C-S8DP-D85B-Z8H6
SUCCESS url       = https://welcome.xzhiyouu.idv.tw
SUCCESS pass code = NT9C-S8DP-D85B-Z8H6
SUCCESS matches the known-good plaintext
```

`https://welcome.xzhiyouu.idv.tw` served me an **"Entry desk · THJCC Summer"**
page with a single field:

> Type the 16-character code from your pass. Case and dashes don't matter.

`NT9C-S8DP-D85B-Z8H6` is 16 characters once the dashes are stripped
(`NT9CS8DPD85BZ8H6`). Submitting it flipped the page to `CHECKED IN` and printed
`https://pastebin.com/DUxM02Gp`, whose body was the flag.

> **Note on the script.** `solve.py` does **not** OCR the frames. Tesseract at
> `--psm 10` misreads these isolated glyphs badly (it returns
> `nCpSa/We;COmMeaXZnyOUa…`), so the glyph sequence is a transcribed constant
> (`GLYPHS`) and the *reconstruction* — the part that actually matters — is
> derived entirely from the file's frame delays.

## 7. Flag

```
THJCC{w3lc0me_t0_tHjCc_CTF_sUmM3r_ed1ti0n}
```

## 8. Key takeaways

- **The signal.** A malformed transcription with a *consistent* defect
  (`htps:/`, `Pas_code` — always a missing **repeat**) means the loss is
  systematic, not random. Systematic loss implies the encoder had a rule, and a
  rule almost always leaves a trace elsewhere in the container.
- **The real trick.** GIF frame delay is a side channel that survives every
  visual inspection: playing the animation, scrubbing it, or dumping frames all
  discard it. Whenever an animated GIF encodes text, dump `info["duration"]`
  before anything else. A delay histogram with exactly two buckets is loud.
- **False lead worth remembering.** Character arithmetic *looked* like proof
  (60 chars − 3 collapsed runs = 57 frames), but the same arithmetic fits
  `xzhiyouu` too (61 − 4 = 57). An identity satisfied by more than one
  hypothesis proves nothing. And an empty HTTP response is not evidence that a
  hostname is right.
- **Corroboration is cheap.** The author's handle on the scoreboard is
  `xzhiyouu`. Cross-checking the recovered hostname against it would have caught
  the wrong reading immediately.
- **Pattern for next time.** Animated GIF + one glyph per frame → build a contact
  sheet, then immediately check (a) duplicate consecutive frames, (b) a
  non-uniform delay histogram, (c) comment/application extension blocks, (d) data
  after the `0x3B` trailer.

---

<a id="ru"></a>
# 04 — Welcome
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🧬 Forensics |
| **Файл задания** | [`welcome.gif`](welcome.gif) |
| **Solve-скрипт** | [`solve.py`](solve.py) |
| **Статус** | ✅ Решено |
| **Флаг** | `THJCC{w3lc0me_t0_tHjCc_CTF_sUmM3r_ed1ti0n}` |

## 1. Условие

> Welcome to THJCC Summer Edition~
> Please follow the rules and do not violate them!

На странице — правила соревнования, формат флага `THJCC{...}` и одно вложение:
`welcome.gif`. 100 баллов, автор `xzhiyouu`. Никаких подсказок.

## 2. Первичный анализ

В превью файл показался мне статичным чёрным квадратом с белой буквой `h` — но
это только первый кадр. Контейнер сказал другое:

```bash
file welcome.gif               # GIF image data, version 89a, 800 x 600
identify welcome.gif | wc -l   # 57
```

- **Подтверждено:** **57 кадров** 800x600, в каждом один крупный белый глиф →
  GIF посимвольно анимирует строку.
- **Подтверждено:** открытого текста в файле нет — `strings` отдаёт только шум
  LZW и градиент палитры.
- **Подтверждено:** обход блоков расширений не находит **ни блока комментария**,
  **ни данных после трейлера `0x3B`**; единственный не-GCE блок — стандартное
  зацикливание `NETSCAPE2.0`.

Через метаданные срезать не вышло, значит, полезную нагрузку нужно доставать из
самих кадров.

## 3. Путь исследования

**Шаг 1 — я прочитал кадры.** Контактный лист сделал строку читаемой целиком:

```bash
convert welcome.gif -coalesce -resize 100x75 miff:- \
  | montage - -tile 8x -geometry +2+2 -background gray50 -label '%p' sheet.png
```

57 глифов по порядку:

```
htps:/welcome.xzhiyou.idv.tw;Pas_code:NT9C-S8DP-D85B-Z8H6
```

**Шаг 2 — я заметил, что строка битая.** `htps:/` — не схема, `Pas_code` — не
слово. У обоих дефектов одна форма: символ, который должен идти **дважды**, идёт
один раз. Моя гипотеза: кодировщик писал по кадру на *видимое состояние*,
поэтому пара одинаковых символов подряд второго кадра не породила.

**Шаг 3 — ловушка, в которую я попал.** Восстановить удвоения «на глаз»
оказалось неоднозначно, и подсчёт символов **не** различил для меня варианты —
сходятся оба:

| Вариант | Полная длина | Схлопнутые пары | Нужно кадров |
|---|---|---|---|
| `https://welcome.xzhiyou.idv.tw;Pass_code:…` | 60 | `tt`, `//`, `ss` | 57 ✓ |
| `https://welcome.xzhiyouu.idv.tw;Pass_code:…` | 61 | `tt`, `//`, `uu`, `ss` | 57 ✓ |

Я поставил на первый вариант и получил хост, вернувший **пустое тело** — это
читается как «сайт лежит», а не «хост неверный». Убедительный ложный след,
который стоил мне времени.

**Шаг 4 — я нашёл настоящий канал.** Решили два измерения.

Сначала я проверил, что среди coalesce-кадров нет ни одной пиксельно одинаковой
пары подряд — значит, идее «кодировщик выкинул дубликаты» нужны доказательства,
а не интуиция.

Потом я обнаружил, что задержки кадров неоднородны:

```bash
python3 -c "
from PIL import Image
im = Image.open('welcome.gif')
for i in range(im.n_frames):
    im.seek(i)
    print(i, im.info['duration'])
"
```

53 кадра идут по **50 мс**, ровно **4** — по **100 мс**: кадры 1, 5, 20 и 31, а на
них `t`, `/`, `u` и `s`. Это в точности четыре удвоенных символа: кадр, висящий
вдвое дольше, отвечает за два символа.

`u` попал в этот набор, значит, хост — `xzhiyouu`, что совпало с ником автора
задания: `xzhiyouu`.

## 4. Инструменты и команды

| Инструмент | Зачем |
|---|---|
| `file`, `identify` (ImageMagick) | тип контейнера, число кадров |
| `convert` + `montage` (ImageMagick) | склейка кадров в контактный лист |
| `strings` | исключить открытый текст в файле |
| Pillow | перебор кадров, `info["duration"]`, поиск дубликатов |
| `loguru` | логирование в `solve.py` |

```bash
file welcome.gif
identify welcome.gif | wc -l
strings welcome.gif | grep -aiE 'thjcc|flag|\{'

convert welcome.gif -coalesce -resize 100x75 miff:- \
  | montage - -tile 8x -geometry +2+2 -background gray50 -label '%p' sheet.png

pip install pillow loguru
python3 solve.py                      # по умолчанию ./welcome.gif
python3 solve.py --dump-frames out/   # плюс выгрузка кадров и контактного листа
```

## 5. Пошаговое решение

1. `identify welcome.gif` показал 57 кадров, а не статичную картинку.
2. `strings` и обход блоков расширений не дали ни открытого флага, ни
   комментариев.
3. `convert -coalesce` + `montage` дали контактный лист; я прочитал 57 глифов
   глазами.
4. Я увидел, что транскрипция битая (`htps:/`, `Pas_code`).
5. Прочитал `info["duration"]` по кадрам → два класса задержек, 50 и 100 мс.
6. Удвоил каждый глиф со 100 мс → полная строка.
7. Разделил по `;` → URL и пасскод.
8. Открыл URL и ввёл 16-символьный код (дефисы и регистр игнорируются).
9. Страница check-in отдала ссылку на pastebin, в пасте был флаг.

## 6. Итоговое решение

```console
$ python3 solve.py
INFO    read 57 frame durations from welcome.gif
INFO    delays: 50 ms x53 (single), 100 ms x4 (doubled)
INFO    frames as read : htps:/welcome.xzhiyou.idv.tw;Pas_code:NT9C-S8DP-D85B-Z8H6
INFO    reconstructed  : https://welcome.xzhiyouu.idv.tw;Pass_code:NT9C-S8DP-D85B-Z8H6
SUCCESS url       = https://welcome.xzhiyouu.idv.tw
SUCCESS pass code = NT9C-S8DP-D85B-Z8H6
SUCCESS matches the known-good plaintext
```

По адресу `https://welcome.xzhiyouu.idv.tw` мне отдалась страница **«Entry desk ·
THJCC Summer»** с одним полем:

> Type the 16-character code from your pass. Case and dashes don't matter.

`NT9C-S8DP-D85B-Z8H6` без дефисов — ровно 16 символов (`NT9CS8DPD85BZ8H6`). После
отправки страница переключилась в `CHECKED IN` и напечатала
`https://pastebin.com/DUxM02Gp`; тело пасты и было флагом.

> **Оговорка про скрипт.** `solve.py` **не** распознаёт кадры OCR. Tesseract с
> `--psm 10` читает эти изолированные глифы плохо (выдаёт
> `nCpSa/We;COmMeaXZnyOUa…`), поэтому последовательность глифов задана
> константой `GLYPHS` как ручная транскрипция, а *реконструкция* — то, что
> действительно важно, — целиком выводится из задержек кадров.

## 7. Флаг

```
THJCC{w3lc0me_t0_tHjCc_CTF_sUmM3r_ed1ti0n}
```

## 8. Ключевые выводы

- **Что было сигналом.** Битая транскрипция с *однотипным* дефектом (`htps:/`,
  `Pas_code` — всегда пропущен **повтор**) означает, что потеря систематическая,
  а не случайная. Систематическая потеря = у кодировщика было правило, а правило
  почти всегда оставляет след где-то ещё в контейнере.
- **Настоящий трюк.** Задержка кадра в GIF — побочный канал, переживающий любой
  визуальный осмотр: ни проигрывание анимации, ни перемотка, ни выгрузка кадров
  его не сохраняют. Если анимированный GIF кодирует текст, дампьте
  `info["duration"]` раньше всего остального. Гистограмма задержек ровно с двумя
  корзинами — громкий сигнал.
- **Ложный след, который стоит запомнить.** Арифметика по количеству символов
  *выглядела* как доказательство (60 символов − 3 схлопнутые пары = 57 кадров),
  но та же арифметика сходится и для `xzhiyouu` (61 − 4 = 57). Тождество,
  которому удовлетворяет больше одной гипотезы, не доказывает ничего. И пустой
  HTTP-ответ — не подтверждение того, что хост угадан верно.
- **Перекрёстная проверка почти бесплатна.** Ник автора на скорборде —
  `xzhiyouu`. Сверка восстановленного хоста с ним сразу поймала бы ошибку.
- **Паттерн на будущее.** Анимированный GIF + один глиф на кадр → собрать
  контактный лист, затем сразу проверить: (а) одинаковые соседние кадры,
  (б) неоднородную гистограмму задержек, (в) блоки comment/application
  extension, (г) данные после трейлера `0x3B`.
