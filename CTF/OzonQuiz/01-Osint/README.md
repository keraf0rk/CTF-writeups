<a id="en"></a>
# 01 — Gosha's Calendar

**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🔎 OSINT |
| **Challenge file** | — (pure OSINT, text only) |
| **Status** | ✅ Solved |
| **Flag** | `ozonctf{E-CODE}` |

## 1. Description

> Goose **Gosha** loves *far, far away galaxies*, chatting and programming. Recently he circled
> **September 12 and 13** on his calendar — looks like he planned something special.
> What event is in Gosha's calendar? (wrap the answer in `ozonctf{}`)

## 2. Initial analysis

- **Gosha** = the official mascot goose of **Ozon Tech** (name = **Go + C#**).
- "far, far away galaxy" = Star Wars flavour matching the CTF storyline.
- The three hobbies map to platforms: *programming* → GitHub, *chatting* → Telegram, *galaxies* → the theme.

## 3. Investigation path

Gosha "chats" on the Ozon Tech Telegram (`@ozon_tech`). Ozon's flagship event on those exact dates
is the annual conference **E-CODE**.

## 4. Findings

- **E-CODE 2026** — Ozon Tech's IT conference — runs on **12–13 September 2026** (Moscow, LOFT #8),
  which matches the circled dates exactly.
- The tracks even mirror Gosha's hobbies: *"Life & Science / space & supercomputers"* → far galaxies;
  networking → chatting; backend **Go / C#** → programming.

## 5. Solution

The event in Gosha's calendar is Ozon Tech's IT conference **E-CODE**. The accepted flag is the
plain conference name (no year, no separators):

```
ozonctf{E-CODE}
```

> Note: dated/verbose variants (`E-CODE_2026`, `E-CODE 2026`, `E-CODE'26`) were "close but not
> exact" — the scorebot wants just the bare event name.

## 6. Key takeaways

- Recognise the persona first: *Gosha = Ozon Tech mascot (Go + C#)*.
- Map flavour words to platforms, then pivot to the org's real events (E-CODE).
- For "name the event" flags, try the **shortest canonical form** first — the bare name beat every
  dated/formatted variant here.

---

<a id="ru"></a>
# 01 — Календарь Гоши

[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🔎 OSINT |
| **Файл задания** | — (чистый OSINT, только текст) |
| **Статус** | ✅ Решено |
| **Флаг** | `ozonctf{E-CODE}` |

## 1. Условие

> Гусь **Гоша** любит *далёкие-далёкие галактики*, общаться и программировать. Недавно он обвёл
> **12 и 13 сентября** кружком — похоже, запланировал что-то особенное. Какое событие в календаре
> Гоши? (обернуть ответ в `ozonctf{}`)

## 2. Первичный анализ

- **Гоша** = официальный маскот-гусь **Ozon Tech** (имя = **Go + C#**).
- «далёкая-далёкая галактика» = Star Wars-отсылка под сюжет CTF.
- Три хобби = три площадки: *программировать* → GitHub, *общаться* → Telegram, *галактики* → тема.

## 3. Путь исследования

Гоша «общается» в Telegram Ozon Tech (`@ozon_tech`). Флагманское событие Ozon ровно на эти даты —
ежегодная конференция **E-CODE**.

## 4. Находки

- **E-CODE 2026** — IT-конференция Ozon Tech — проходит **12–13 сентября 2026** (Москва, LOFT #8),
  что точно совпадает с обведёнными датами.
- Треки повторяют хобби Гоши: *«Жизнь и наука / космос и суперкомпьютеры»* → далёкие галактики;
  нетворкинг → общаться; бэкенд **Go / C#** → программировать.

## 5. Итоговое решение

Событие в календаре Гоши — IT-конференция Ozon Tech **E-CODE**. Принятый флаг — чистое название
конференции (без года и разделителей):

```
ozonctf{E-CODE}
```

> Замечание: датированные/развёрнутые варианты (`E-CODE_2026`, `E-CODE 2026`, `E-CODE'26`) были
> «близко, но не то» — боту нужно именно голое название события.

## 6. Ключевые выводы

- Сначала опознать персону: *Гоша = маскот Ozon Tech (Go + C#)*.
- Сопоставить слова-подсказки с площадками, выйти на реальные события (E-CODE).
- Для флагов вида «назови событие» пробуй **самую короткую каноничную форму** — здесь голое
  название побило все датированные/форматированные варианты.
