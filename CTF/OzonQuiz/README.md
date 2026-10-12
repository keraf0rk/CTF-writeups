<a id="en"></a>
<h1 align="center">🦆 OzonQuiz — CTF Writeups</h1>

<p align="center"><b>🇬🇧 English</b> · <a href="#ru">🇷🇺 Русский</a></p>

<p align="center">
  My writeups for <b>OzonQuiz</b> cybersecurity challenges.<br>
  For each one I describe what I found, what I did and why it worked — with the commands and scripts I used.
</p>

---

## 🏆 Challenges

| #  | Challenge | Category | Status |
|----|-----------|----------|:------:|
| 01 | [Gosha's Calendar](01-Osint/)         | 🔎 OSINT         | ✅ |
| 02 | [The Courier's Browser](02-Forensic/) | 🧬 Forensics     | ✅ |
| 03 | [Space Noise](03-Stego/)              | 🖼️ Steganography | ✅ |
| 04 | [Millennium Goose](04-Osint/)         | 🔎 OSINT         | ✅ |
| 05 | [The Coffee-Machine Call](05-Stego/)  | 🖼️ Steganography | ✅ |

> 🚧 = work in progress/stop · ✅ = solved
> Each challenge folder contains its **writeup** (`README.md`) and its **solve script**.

## 📊 Categories

- 🔎 **OSINT** — Open Source Intelligence
- 🧬 **Forensics** — Digital Forensics
- 🖼️ **Steganography** — Hidden Data & Information
- 🌐 **Web** — Web Security
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

`Linux` · `Python` · `Bash` · `SoX` · `ffmpeg` · `NumPy/SciPy/Pillow` · `unrar` · `strings` · `file` · `grep` · `exiftool` · `CyberChef` · reverse-image search (Yandex / Google Lens)

## 🎯 Flag format

```
ozonctf{...}
```

## 📚 Disclaimer

These writeups are published for **educational purposes** and document solutions to CTF challenges.
All my testing was done against the CTF infrastructure or the provided challenge files.

---

<a id="ru"></a>
<h1 align="center">🦆 OzonQuiz — Райтапы CTF</h1>

<p align="center"><a href="#en">🇬🇧 English</a> · <b>🇷🇺 Русский</b></p>

<p align="center">
  Мои разборы заданий <b>OzonQuiz</b> по кибербезопасности, которые я решил.<br>
  В каждом рассказываю, что я нашёл, что сделал и почему это сработало, — с командами и скриптами.
</p>

---

## 🏆 Задания

| #  | Задание | Категория | Статус |
|----|---------|-----------|:------:|
| 01 | [Календарь Гоши](01-Osint/)          | 🔎 OSINT         | ✅ |
| 02 | [Браузер курьера](02-Forensic/)      | 🧬 Форензика     | ✅ |
| 03 | [Космический шум](03-Stego/)         | 🖼️ Стеганография | ✅ |
| 04 | [Миллениум Гусь](04-Osint/)          | 🔎 OSINT         | ✅ |
| 05 | [Звонок про кофемашины](05-Stego/)   | 🖼️ Стеганография | ✅ |

> 🚧 = в работе/стоп · ✅ = решено
> В папке каждого задания лежат **разбор** (`README.md`) и **solve-скрипт**.

## 📊 Категории

- 🔎 **OSINT** — разведка по открытым источникам
- 🧬 **Forensics** — цифровая форензика
- 🖼️ **Steganography** — скрытые данные
- 🌐 **Web** — веб-безопасность
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

`Linux` · `Python` · `Bash` · `SoX` · `ffmpeg` · `NumPy/SciPy/Pillow` · `unrar` · `strings` · `file` · `grep` · `exiftool` · `CyberChef` · реверс-поиск изображений (Yandex / Google Lens)

## 🎯 Формат флага

```
ozonctf{...}
```

## 📚 Дисклеймер

Разборы опубликованы в **образовательных целях** и документируют решения CTF-заданий.
Всё тестирование я проводил на инфраструктуре CTF или на выданных файлах заданий.

<p align="center">
  <sub>CTF Writeups • Cybersecurity • Learning by Breaking Things</sub>
</p>
