<a id="en"></a>
<h1 align="center">🛡️ FortID CTF 2026 — CTF Writeups</h1>

<p align="center"><b>🇬🇧 English</b> · <a href="#ru">🇷🇺 Русский</a></p>

<p align="center">
  My writeups for the <b>FortID CTF 2026</b> challenges I solved.<br>
  For each one I describe what I found, what I did and why it worked — with the commands and scripts I used.
</p>

---

## 🏆 Challenges

| #  | Challenge | Category | Points | Status |
|----|-----------|----------|:------:|:------:|
| 01 | [Hic Sunt Dracones](01-Crypto/) | 🔐 Crypto | 106 | ✅ |
| 02 | [Human RNG](02-Crypto/) | 🔐 Crypto | 121 | ✅ |
| 03 | [Baby Web](03-Web/) | 🌐 Web (intro) | 103 | ✅ |
| 04 | [Baby Rev](04-Reverse/) | 🔧 Reverse (intro) | 104 | ✅ |
| 05 | [Meteor Shower](05-Reverse/) | 🔧 Reverse | 107 | ✅ |
| 06 | [Paint me a Flag](06-Reverse/) | 🔧 Reverse | 115 | ✅ |
| 07 | [Breaking News](07-OSINT/) | 🔎 OSINT | 166 | ✅ |

> ✅ = solved · points are the final dynamic scores
> Each challenge folder contains its **writeup** (`README.md`), its **solve script** and the small challenge files.

## 📊 Categories

- 🔐 **Crypto** — Koblitz encoding leak, statistical oracle against a human-typed keystream
- 🌐 **Web** — client-side "protection"
- 🔧 **Reverse** — CPython 3.10 bytecode, NES 6502 ROM, a deliberately slow x86-64 renderer
- 🔎 **OSINT** — Bluesky, Pastebin, Google Drive, GitHub, Wayback Machine

## 🧠 Approach

Every writeup follows the same structure:

1. Challenge description
2. Initial analysis / reconnaissance
3. Vulnerability or investigation path
4. Tools and commands used
5. Step-by-step exploitation / investigation
6. Solution
7. Flag
8. Key takeaways

I wanted to record not just the flag, but **how** I got to it and **why** the solution works.

## 🛠️ Tools

`Linux` · `Python` · `Bash` · `C` · `numpy` · `Pillow` · `qrcode` · Reed–Solomon block mapping · Markov models · `xdis` / `pydisasm` · `py65` (6502) · iNES · `objdump` · splitmix64 · union-find · `cryptography` (Scrypt, AES-GCM) · `git` · Bluesky AT Protocol API · Wayback Machine · C2PA

## 🎯 Flag format

```
FortID{...}
```

## 📚 Disclaimer

These writeups are published for **educational purposes** and document solutions to CTF challenges.
All my testing was done against the CTF infrastructure or the provided challenge files.

---

<a id="ru"></a>
<h1 align="center">🛡️ FortID CTF 2026 — Райтапы CTF</h1>

<p align="center"><a href="#en">🇬🇧 English</a> · <b>🇷🇺 Русский</b></p>

<p align="center">
  Мои разборы заданий <b>FortID CTF 2026</b>, которые я решил.<br>
  В каждом рассказываю, что я нашёл, что сделал и почему это сработало, — с командами и скриптами.
</p>

---

## 🏆 Задания

| #  | Задание | Категория | Очки | Статус |
|----|---------|-----------|:----:|:------:|
| 01 | [Hic Sunt Dracones](01-Crypto/) | 🔐 Crypto | 106 | ✅ |
| 02 | [Human RNG](02-Crypto/) | 🔐 Crypto | 121 | ✅ |
| 03 | [Baby Web](03-Web/) | 🌐 Web (intro) | 103 | ✅ |
| 04 | [Baby Rev](04-Reverse/) | 🔧 Reverse (intro) | 104 | ✅ |
| 05 | [Meteor Shower](05-Reverse/) | 🔧 Reverse | 107 | ✅ |
| 06 | [Paint me a Flag](06-Reverse/) | 🔧 Reverse | 115 | ✅ |
| 07 | [Breaking News](07-OSINT/) | 🔎 OSINT | 166 | ✅ |

> ✅ = решено · очки — итоговые динамические
> В папке каждого задания лежат **разбор** (`README.md`), **solve-скрипт** и небольшие файлы задания.

## 📊 Категории

- 🔐 **Crypto** — утечка кодирования Коблица, статистический оракул против набранного человеком потока
- 🌐 **Web** — «защита» на стороне клиента
- 🔧 **Reverse** — байткод CPython 3.10, ROM NES на 6502, намеренно медленный рендерер x86-64
- 🔎 **OSINT** — Bluesky, Pastebin, Google Drive, GitHub, Wayback Machine

## 🧠 Подход

Все разборы построены одинаково:

1. Условие задания
2. Первичный анализ / разведка
3. Путь исследования / вектор
4. Инструменты и команды
5. Пошаговое решение
6. Итоговое решение
7. Флаг
8. Ключевые выводы

Я хотел зафиксировать не только флаг, но и то, **как** я к нему пришёл и **почему** решение работает.

## 🛠️ Инструменты

`Linux` · `Python` · `Bash` · `C` · `numpy` · `Pillow` · `qrcode` · Reed–Solomon block mapping · Markov models · `xdis` / `pydisasm` · `py65` (6502) · iNES · `objdump` · splitmix64 · union-find · `cryptography` (Scrypt, AES-GCM) · `git` · Bluesky AT Protocol API · Wayback Machine · C2PA

## 🎯 Формат флага

```
FortID{...}
```

## 📚 Дисклеймер

Разборы опубликованы в **образовательных целях** и документируют решения CTF-заданий.
Всё тестирование я проводил на инфраструктуре CTF или на выданных файлах заданий.

<p align="center">
  <sub>CTF Writeups • Cybersecurity • Learning by Breaking Things</sub>
</p>
