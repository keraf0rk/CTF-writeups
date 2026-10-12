<a id="en"></a>
<h1 align="center">🇹🇼 THJCC-2026 — CTF Writeups</h1>

<p align="center"><b>🇬🇧 English</b> · <a href="#ru">🇷🇺 Русский</a></p>

<p align="center">
  My writeups for the <b>THJCC CTF 2026</b> challenges I solved.<br>
  For each one I describe what I found, what I did and why it worked — with the commands and scripts I used.
</p>

---

## 🏆 Challenges

| #  | Challenge | Category | Status |
|----|-----------|----------|:------:|
| 01 | [Contoso Asset Portal](01-Web/) | 🌐 Web | ✅ |
| 02 | [Afterimage2](02-Forensics/) | 🧬 Forensics | ✅ |
| 03 | [Because There is no one Make Reverse…](03-Reverse/) | 🔧 Reverse | ✅ |
| 04 | [Welcome](04-Forensics/) | 🧬 Forensics | ✅ |
| 05 | [License](05-Reverse/) | 🔧 Reverse | ✅ |
| 06 | [404](06-Reverse/) | 🔧 Reverse | ✅ |
| 07 | [xorlocks](07-Reverse/) | 🔧 Reverse | ✅ |
| 08 | [TeaGod.exe](08-Reverse/) | 🔧 Reverse | ✅ |
| 09 | [BlackFrost](09-Reverse/) | 🔧 Reverse | ✅ |

> 🚧 = work in progress/stop · ✅ = solved
> Each challenge folder contains its **writeup** (`README.md`) and its **solve script**.

## 📊 Categories

- 🌐 **Web** — Web Security
- 🧬 **Forensics** — Digital Forensics
- 🔧 **Reverse** — Reverse Engineering
- 🔐 **Crypto** — Cryptography
- ⚙️ **Misc** — Miscellaneous

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

`Linux` · `Python` · `Bash` · `curl` · `base64` · `hmac` (HMAC-SHA1) · ASP.NET ViewState · `USB HID` · `pcap` · `usbmon` · `capstone` · `readelf` · `strings` · XTEA · FNV-1a · Mach-O/ELF/PE parsing · `ImageMagick` · `Pillow` · `GIF frame timing`

## 🎯 Flag format

```
THJCC{...}
```

## 📚 Disclaimer

These writeups are published for **educational purposes** and document solutions to CTF challenges.
All my testing was done against the CTF infrastructure or the provided challenge files.

---

<a id="ru"></a>
<h1 align="center">🇹🇼 THJCC-2026 — Райтапы CTF</h1>

<p align="center"><a href="#en">🇬🇧 English</a> · <b>🇷🇺 Русский</b></p>

<p align="center">
  Мои разборы заданий <b>THJCC CTF 2026</b>, которые я решил.<br>
  В каждом рассказываю, что я нашёл, что сделал и почему это сработало, — с командами и скриптами.
</p>

---

## 🏆 Задания

| #  | Задание | Категория | Статус |
|----|---------|-----------|:------:|
| 01 | [Contoso Asset Portal](01-Web/) | 🌐 Web | ✅ |
| 02 | [Afterimage2](02-Forensics/) | 🧬 Forensics | ✅ |
| 03 | [Because There is no one Make Reverse…](03-Reverse/) | 🔧 Reverse | ✅ |
| 04 | [Welcome](04-Forensics/) | 🧬 Forensics | ✅ |
| 05 | [License](05-Reverse/) | 🔧 Reverse | ✅ |
| 06 | [404](06-Reverse/) | 🔧 Reverse | ✅ |
| 07 | [xorlocks](07-Reverse/) | 🔧 Reverse | ✅ |
| 08 | [TeaGod.exe](08-Reverse/) | 🔧 Reverse | ✅ |
| 09 | [BlackFrost](09-Reverse/) | 🔧 Reverse | ✅ |

> 🚧 = в работе/стоп · ✅ = решено
> В папке каждого задания лежат **разбор** (`README.md`) и **solve-скрипт**.

## 📊 Категории

- 🌐 **Web** — веб-безопасность
- 🧬 **Forensics** — форензика
- 🔧 **Reverse** — реверс-инжиниринг
- 🔐 **Crypto** — криптография
- ⚙️ **Misc** — разное

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

`Linux` · `Python` · `Bash` · `curl` · `base64` · `hmac` (HMAC-SHA1) · ASP.NET ViewState · `USB HID` · `pcap` · `usbmon` · `capstone` · `readelf` · `strings` · XTEA · FNV-1a · Mach-O/ELF/PE parsing · `ImageMagick` · `Pillow` · `GIF frame timing`

## 🎯 Формат флага

```
THJCC{...}
```

## 📚 Дисклеймер

Разборы опубликованы в **образовательных целях** и документируют решения CTF-заданий.
Всё тестирование я проводил на инфраструктуре CTF или на выданных файлах заданий.

<p align="center">
  <sub>CTF Writeups • Cybersecurity • Learning by Breaking Things</sub>
</p>
