<a id="en"></a>
# 03 — Baby Web
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🌐 Web |
| **Challenge file** | `index.html` |
| **Status** | ✅ Solved |
| **Flag** | `FortID{w3b_15_n07_7h47_h4rd_45_y0u_7h1nk_17_15}` |

## 1. Description

A single page, *Catch me if you can!*, with a **"Show me the flag"** button.
Every time I moved the cursor towards it, the button jumped to a random spot on
the screen — "the flag is one click away, you only have to catch the button".

## 2. Initial analysis

I didn't try to chase the button. The page is fully static — it makes no
request to a server — so the flag had to be shipped to the browser already.
I opened the source (`view-source:`, or just the file) and the whole logic was
right there:

```js
button.addEventListener("mouseenter", runAway);          // dodge the cursor

button.addEventListener("click", () => {
  const scrambled = [
    "=0XNx81Nx81auFDa38Vdwk3",
    "X1QzXkJHNo91N0g2NfdDMu9V",
    "Nx8lYzc3eElEdy9mR"
  ].join("");
  output.textContent = atob([...scrambled].reverse().join(""));
});
```

## 3. Investigation path

**What I confirmed**

- The "protection" is pure **client-side UX**: the `mouseenter` handler only
  moves the button. The click handler keeps the flag inside the page itself.
- The obfuscation is two reversible steps: **join the fragments → reverse the
  string → Base64-decode** (`atob`).

**What I did with it**

- Since the check lives only in the browser, I had three equivalent ways out:
  1. reproduce the transform offline — that's what [`solve.py`](solve.py) does;
  2. run `document.querySelector('#runaway').click()` in the DevTools console —
     `click()` fires the handler without any mouse movement;
  3. remove the dodge (`removeEventListener` / `pointer-events`) and click
     normally.

## 4. Tools & commands

```bash
python3 solve.py index.html
```

or, in the browser console:

```js
document.querySelector("#runaway").click()
```

See [`solve.py`](solve.py).

## 5. Step-by-step

1. I opened the page source and found the `click` handler.
2. I concatenated the three fragments of `scrambled`.
3. I reversed the string (`[...s].reverse().join("")`).
4. I Base64-decoded it (`atob`) and got the flag.

## 6. Solution

```
$ python3 solve.py index.html
SUCCESS  FLAG: FortID{w3b_15_n07_7h47_h4rd_45_y0u_7h1nk_17_15}
```

## 7. Flag

```
FortID{w3b_15_n07_7h47_h4rd_45_y0u_7h1nk_17_15}
```

## 8. Key takeaways

- **What tipped me off:** a static page that "hides" a secret behind an
  interaction — the secret was already in the source.
- **Why it worked:** client-side checks and light obfuscation (reverse +
  Base64) give no security at all; the browser runs whatever the page ships.
- **What I'll remember:** read the JavaScript before fighting the UI;
  `element.click()` from the console triggers handlers the interface tries to
  keep out of reach.

---

<a id="ru"></a>
# 03 — Baby Web
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🌐 Web |
| **Файл задания** | `index.html` |
| **Статус** | ✅ Solved |
| **Флаг** | `FortID{w3b_15_n07_7h47_h4rd_45_y0u_7h1nk_17_15}` |

## 1. Условие

Страница *Catch me if you can!* с кнопкой **«Show me the flag»**. Стоило мне
подвести курсор, кнопка прыгала в случайное место экрана: «флаг в одном клике,
нужно лишь поймать кнопку».

## 2. Первичный анализ

Гоняться за кнопкой я не стал. Страница полностью статична — запросов к серверу
нет, значит флаг уже лежит в браузере. Открыл исходник (`view-source:` или сам
файл), и вся логика оказалась на виду:

```js
button.addEventListener("mouseenter", runAway);          // уворот от курсора

button.addEventListener("click", () => {
  const scrambled = [
    "=0XNx81Nx81auFDa38Vdwk3",
    "X1QzXkJHNo91N0g2NfdDMu9V",
    "Nx8lYzc3eElEdy9mR"
  ].join("");
  output.textContent = atob([...scrambled].reverse().join(""));
});
```

## 3. Путь исследования

**Что я подтвердил**

- «Защита» — это чистый **клиентский UX**: обработчик `mouseenter` лишь двигает
  кнопку, а обработчик клика держит флаг прямо в странице.
- Обфускация — два обратимых шага: **склеить фрагменты → развернуть строку →
  декодировать Base64** (`atob`).

**Что я с этим сделал**

- Раз проверка живёт только в браузере, у меня было три равноценных пути:
  1. воспроизвести преобразование офлайн — это и делает [`solve.py`](solve.py);
  2. выполнить в консоли DevTools `document.querySelector('#runaway').click()` —
     `click()` вызывает обработчик без движения мыши;
  3. убрать уворот (`removeEventListener` / `pointer-events`) и кликнуть
     обычным образом.

## 4. Инструменты и команды

```bash
python3 solve.py index.html
```

или в консоли браузера:

```js
document.querySelector("#runaway").click()
```

См. [`solve.py`](solve.py).

## 5. Пошаговое решение

1. Открыл исходник страницы и нашёл обработчик `click`.
2. Склеил три фрагмента `scrambled`.
3. Развернул строку (`[...s].reverse().join("")`).
4. Декодировал Base64 (`atob`) и получил флаг.

## 6. Итоговое решение

```
$ python3 solve.py index.html
SUCCESS  FLAG: FortID{w3b_15_n07_7h47_h4rd_45_y0u_7h1nk_17_15}
```

## 7. Флаг

```
FortID{w3b_15_n07_7h47_h4rd_45_y0u_7h1nk_17_15}
```

## 8. Ключевые выводы

- **Что меня навело:** статичная страница, «прячущая» секрет за
  взаимодействием, — секрет уже был в исходнике.
- **Почему сработало:** клиентские проверки и лёгкая обфускация (разворот +
  Base64) не дают никакой защиты: браузер исполняет всё, что прислала страница.
- **Что запомню:** сначала читаю JavaScript, а потом уже трогаю интерфейс;
  `element.click()` из консоли вызывает обработчики, до которых UI не даёт
  дотянуться.
