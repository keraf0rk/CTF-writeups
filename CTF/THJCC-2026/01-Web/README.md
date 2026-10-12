<a id="en"></a>
# 01 — Contoso Asset Portal
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🌐 Web |
| **Challenge file** | — (remote only: `chal.thjcc.org:31255`) |
| **Status** | ✅ Solved |
| **Flag** | `THJCC{f0rg3d_v13wst4t3_w1th_l34k3d_m4ch1n3k3y}` |

## 1. Description

A "legacy internal asset-lookup tool": a classic ASP.NET Web Forms page that
lets you search a hardware asset by tag. The page keeps session-ish state
(`role`, current `asset`) inside the `__VIEWSTATE` field. Restricted assets are
only shown to an `admin` role, which a `guest` session does not have.

## 2. Initial analysis

```bash
curl -s http://chal.thjcc.org:31255/           # ASP.NET Web Forms, POST to /Default.aspx
curl -s http://chal.thjcc.org:31255/robots.txt # Disallow: /backup/
```

- The page is ASP.NET and posts back with `__VIEWSTATE` (+ `__VIEWSTATEGENERATOR`).
- `robots.txt` points at a `/backup/` directory.
- A forged/garbage `__VIEWSTATE` is rejected — so **ViewState MAC is enabled**
  (`EnableViewStateMac`). That told me the server signs the ViewState, so to
  tamper with it I first needed the signing key.

## 3. Investigation path

**Confirmed**

- `/backup/` has directory listing enabled and exposes `web.config~` and
  `assets.csv.bak`.
- `web.config~` leaks the active `<machineKey>` — specifically the
  `validationKey` used to sign the ViewState.
- `assets.csv.bak` lists assets and marks `AST-4F2A9C0` as **restricted**.
- Base64-decoding the live `__VIEWSTATE` shows **plaintext**: two serialized
  strings `guest` and `AST-0000000`, followed by a **20-byte** trailer.
  20 bytes == SHA-1 digest length → the trailer is an HMAC-SHA1 MAC, and the
  state itself is **not encrypted**.

**What I confirmed next**

- The MAC is `HMAC-SHA1(validationKey, serialized_payload)`. I confirmed it by
  recomputing the MAC over the original payload with the leaked key and matching
  it byte for byte against the trailer (see `solve.py`, `forge()` assertion).

## 4. Tools & commands

```bash
# Recon
curl -s http://chal.thjcc.org:31255/robots.txt
curl -s http://chal.thjcc.org:31255/backup/
curl -s http://chal.thjcc.org:31255/backup/web.config~      # -> validationKey
curl -s http://chal.thjcc.org:31255/backup/assets.csv.bak   # -> AST-4F2A9C0 restricted

# Inspect / forge / submit
python3 solve.py            # verify key, print forged ViewState (offline)
python3 solve.py --submit   # forge + POST to the live target, extract flag
```

## 5. Step-by-step

1. I pulled `/backup/web.config~` and extracted the hex `validationKey`.
2. I grabbed a fresh `__VIEWSTATE` from `GET /Default.aspx`.
3. I base64-decoded it and split it into `payload = raw[:-20]` and
   `sig = raw[-20:]`.
4. I checked `HMAC_SHA1(key, payload) == sig`, which proved the algorithm and
   the key.
5. I rewrote the plaintext inside `payload`: `guest` → `admin` and
   `AST-0000000` → `AST-4F2A9C0`. Both edits are **length-preserving**, so the
   serialized length prefixes stayed valid and nothing else shifted.
6. I recomputed the MAC over the new payload and re-base64'd `payload + new_mac`.
7. I POSTed the forged `__VIEWSTATE` back to `/Default.aspx` with
   `--data-urlencode` (so the `+` / `=` in the base64 survive).

## 6. Solution

The forged ViewState I produced with `solve.py`:

```
/wEMAQVhZG1pbgELQVNULTRGMkE5QzBF1lsA6BNCBNhd4CVDh7zJlLbvRg==
```

Submitting it:

```bash
curl -s http://chal.thjcc.org:31255/Default.aspx \
  --data-urlencode '__VIEWSTATE=/wEMAQVhZG1pbgELQVNULTRGMkE5QzBF1lsA6BNCBNhd4CVDh7zJlLbvRg==' \
  --data-urlencode '__VIEWSTATEGENERATOR=' \
  --data-urlencode 'ctl00$asset=AST-4F2A9C0' \
  --data-urlencode 'ctl00$lookup=Lookup'
```

Response: `Access granted — role=admin.` followed by the restricted asset
`AST-4F2A9C0` and the flag.

## 7. Flag

```
THJCC{f0rg3d_v13wst4t3_w1th_l34k3d_m4ch1n3k3y}
```

## 8. Key takeaways

- **The signal:** a forged ViewState being *rejected* (not ignored) means MAC
  validation is on — so the whole challenge becomes "find the key". `robots.txt`
  → `/backup/` → `web.config~` is the canonical key-leak chain.
- **Why it worked:** ViewState MAC only guarantees *integrity*, not
  *confidentiality*. With `EnableViewStateMac` but **no encryption**, whoever
  owns the `validationKey` can forge arbitrary state. Default ASP.NET MAC here is
  plain `HMAC-SHA1(validationKey, payload)`.
- **Length-preserving edits:** `guest`→`admin` and the two asset ids are the same
  length, so I could byte-patch without touching the serialization format. If
  the lengths had differed I would have had to fix the ViewState length prefixes
  too.
- **False leads:** trying to brute the MAC or attack the serialization — pointless
  once the key is in `web.config~`. Don't over-engineer; check backups first.
- **Recognize it next time:** ASP.NET + `__VIEWSTATE` + an exposed backup dir is
  almost always a ViewState-forgery task. `ysoserial.net` is the heavier cousin
  when the goal is RCE; here a plain role flip was enough.

---

<a id="ru"></a>
# 01 — Contoso Asset Portal
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🌐 Web |
| **Файл задания** | — (только удалённо: `chal.thjcc.org:31255`) |
| **Статус** | ✅ Solved |
| **Флаг** | `THJCC{f0rg3d_v13wst4t3_w1th_l34k3d_m4ch1n3k3y}` |

## 1. Условие

«Легаси-инструмент для внутреннего поиска активов»: классическая страница
ASP.NET Web Forms, которая ищет железо по инвентарному тегу. Страница хранит
состояние (`role`, текущий `asset`) прямо в поле `__VIEWSTATE`. Ограниченные
активы видны только роли `admin`, которой у `guest`-сессии нет.

## 2. Первичный анализ

```bash
curl -s http://chal.thjcc.org:31255/           # ASP.NET Web Forms, POST на /Default.aspx
curl -s http://chal.thjcc.org:31255/robots.txt # Disallow: /backup/
```

- Это ASP.NET, postback идёт с `__VIEWSTATE` (+ `__VIEWSTATEGENERATOR`).
- `robots.txt` указывает на каталог `/backup/`.
- Подделанный/мусорный `__VIEWSTATE` отвергается → **включена MAC-проверка
  ViewState** (`EnableViewStateMac`). Значит, сервер подписывает ViewState, и
  для подмены мне сначала нужен был ключ подписи.

## 3. Путь исследования

**Подтверждено**

- В `/backup/` открыт листинг каталога, доступны `web.config~` и
  `assets.csv.bak`.
- `web.config~` сливает активный `<machineKey>` — а именно `validationKey`,
  которым подписывается ViewState.
- `assets.csv.bak` перечисляет активы и помечает `AST-4F2A9C0` как
  **restricted**.
- Base64-декод текущего `__VIEWSTATE` показывает **открытый текст**: две
  сериализованные строки `guest` и `AST-0000000`, за ними **20-байтовый** хвост.
  20 байт == длина SHA-1 → хвост это HMAC-SHA1, а само состояние **не
  зашифровано**.

**Что я подтвердил дальше**

- MAC — это `HMAC-SHA1(validationKey, serialized_payload)`. Я подтвердил это:
  пересчитал MAC по исходному payload с утёкшим ключом и побайтово сравнил с
  хвостом (см. `solve.py`, проверка в `forge()`).

## 4. Инструменты и команды

```bash
# Разведка
curl -s http://chal.thjcc.org:31255/robots.txt
curl -s http://chal.thjcc.org:31255/backup/
curl -s http://chal.thjcc.org:31255/backup/web.config~      # -> validationKey
curl -s http://chal.thjcc.org:31255/backup/assets.csv.bak   # -> AST-4F2A9C0 restricted

# Разбор / подделка / отправка
python3 solve.py            # проверка ключа + печать подделанного ViewState (офлайн)
python3 solve.py --submit   # подделка + POST на боевой таргет, вытащить флаг
```

## 5. Пошаговое решение

1. Забрал `/backup/web.config~` и вытащил hex `validationKey`.
2. Взял свежий `__VIEWSTATE` из `GET /Default.aspx`.
3. Сделал base64-декод и разбил на `payload = raw[:-20]` и `sig = raw[-20:]`.
4. Проверил `HMAC_SHA1(key, payload) == sig` — это подтвердило алгоритм и ключ.
5. Переписал открытый текст в `payload`: `guest` → `admin` и
   `AST-0000000` → `AST-4F2A9C0`. Обе правки **сохраняют длину**, поэтому
   префиксы длины в сериализации остались валидными и ничего не «съехало».
6. Пересчитал MAC по новому payload и заново взял base64 от `payload + new_mac`.
7. Отправил подделанный `__VIEWSTATE` на `/Default.aspx` через
   `--data-urlencode` (чтобы `+` / `=` в base64 не поломались).

## 6. Итоговое решение

Подделанный ViewState, который я получил через `solve.py`:

```
/wEMAQVhZG1pbgELQVNULTRGMkE5QzBF1lsA6BNCBNhd4CVDh7zJlLbvRg==
```

Отправка:

```bash
curl -s http://chal.thjcc.org:31255/Default.aspx \
  --data-urlencode '__VIEWSTATE=/wEMAQVhZG1pbgELQVNULTRGMkE5QzBF1lsA6BNCBNhd4CVDh7zJlLbvRg==' \
  --data-urlencode '__VIEWSTATEGENERATOR=' \
  --data-urlencode 'ctl00$asset=AST-4F2A9C0' \
  --data-urlencode 'ctl00$lookup=Lookup'
```

Ответ: `Access granted — role=admin.`, далее ограниченный актив `AST-4F2A9C0`
и флаг.

## 7. Флаг

```
THJCC{f0rg3d_v13wst4t3_w1th_l34k3d_m4ch1n3k3y}
```

## 8. Ключевые выводы

- **Сигнал:** если подделанный ViewState именно *отвергается* (а не молча
  игнорируется) — включена MAC-проверка, и вся задача сводится к «найти ключ».
  Цепочка `robots.txt` → `/backup/` → `web.config~` — канонический слив ключа.
- **Почему сработало:** MAC ViewState гарантирует только *целостность*, не
  *конфиденциальность*. При включённом `EnableViewStateMac`, но **без
  шифрования**, владелец `validationKey` подделывает любое состояние. Дефолтный
  MAC здесь — простой `HMAC-SHA1(validationKey, payload)`.
- **Правки с сохранением длины:** `guest`→`admin` и оба id актива одной длины,
  поэтому байт-патч не тронул формат сериализации. Будь длины разными, мне
  пришлось бы чинить ещё и префиксы длины в ViewState.
- **Ложные следы:** брутить MAC или атаковать сериализацию — бессмысленно, как
  только ключ лежит в `web.config~`. Не усложняй: сначала смотри бэкапы.
- **Как узнать в следующий раз:** ASP.NET + `__VIEWSTATE` + открытый каталог
  бэкапов — почти всегда задача на forgery ViewState. `ysoserial.net` — тяжёлый
  родственник, когда цель RCE; здесь хватило простой смены роли.
