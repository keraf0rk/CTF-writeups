<a id="en"></a>
# 02 — Afterimage2
**🇬🇧 English** · [🇷🇺 Русский](#ru)

| | |
|---|---|
| **Category** | 🧬 Forensics |
| **Challenge file** | [`usb_capture.pcap`](usb_capture.pcap) |
| **Status** | ✅ Solved |
| **Flag** | `THJCC{hid_k3y5tr0k3_l34k}` |

## 1. Description

> The cybersecurity team discovered an "unidentified cable" connected to a
> workstation suspected of a data breach. We captured the raw traffic from that
> line, and the data revealed frequent activity over a period of time.

One attachment: `usb_capture.pcap`.

## 2. Initial analysis

The "cable" is the hint — this is a USB bus dump, not network traffic:

```bash
file usb_capture.pcap          # pcap capture file, microsecond ts (little-endian)
# link type in the 24-byte global header: 220 = LINKTYPE_USB_LINUX_MMAPPED
```

- **Confirmed:** link type **220** → a Linux `usbmon` capture.
- **Confirmed:** every record is **72 bytes** = a **64-byte usbmon header** + an
  **8-byte USB HID keyboard report**.
- **Confirmed:** **50 packets** — press/release pairs, so ~25 real keystrokes.

So this is a keystroke-recovery task: decode the HID reports back into text.

## 3. Investigation path

USB HID boot-keyboard report (8 bytes):

| offset | meaning |
|---|---|
| 0 | modifier bitmap (`0x02` LeftShift, `0x20` RightShift) |
| 1 | reserved |
| 2..7 | up to 6 pressed key usage-ids (`0x00` = none) |

**Confirmed** rules used while walking the reports:

- `key == 0` → key-release / empty report → skip (why 50 packets → ~25 chars).
- `key == 0x28` → Enter, `key == 0x2A` → Backspace.
- otherwise map the usage-id to a character, taking the **shifted** variant when
  `modifier & 0x22` — this is what produces `{`, `}`, `_` (Shift+`[`, Shift+`]`,
  Shift+`-`). The body is lowercase leet, so no shift is held there.

Mapping the sequence in order yields the flag directly.

## 4. Tools & commands

```bash
# confirm it's a USB (usbmon) capture, not Ethernet
file usb_capture.pcap

# optional: dump HID payloads with tshark, if installed
tshark -r usb_capture.pcap -T fields -e usbhid.data | head

# self-contained solver (pure struct + loguru, no scapy/tshark needed)
pip install loguru
python3 solve.py                 # defaults to ./usb_capture.pcap
python3 solve.py usb_capture.pcap
```

## 5. Step-by-step

1. Read the 24-byte pcap global header, detect endianness from the magic, note
   link type 220.
2. Iterate 16-byte record headers + payloads to get all 50 packets.
3. For each packet, slice the HID report at `payload[64:72]`.
4. Read `modifier = report[0]`, `key = report[2]`.
5. Skip `key == 0`; handle Enter/Backspace; otherwise map `key` via the HID
   table, applying shift when `modifier & 0x22`.
6. Concatenate the characters → flag.

## 6. Solution

```console
$ python3 solve.py
INFO    pcap magic=d4c3b2a1 endian=< link_type=220
INFO    parsed 50 packets
SUCCESS recovered flag: THJCC{hid_k3y5tr0k3_l34k}
THJCC{hid_k3y5tr0k3_l34k}
```

The 25 keystrokes decode straight to the flag — the "frequent activity over a
period of time" is simply someone typing it on the planted keyboard.

## 7. Flag

```
THJCC{hid_k3y5tr0k3_l34k}
```

## 8. Key takeaways

- **The signal:** a `.pcap` whose link type is **220** (`USB_LINUX_MMAPPED`) or
  **189** (`USB_LINUX`), plus a prompt mentioning a "cable"/"device", means USB
  HID keystroke recovery — not TCP/HTTP. Tiny, uniform packets (here 72 bytes)
  confirm it.
- **HID quick reference:** report offset 2 is the key code; `modifier & 0x22`
  means a shift is held; `a`..`z` = `0x04`..`0x1D`; `1`..`0` = `0x1E`..`0x27`;
  Enter `0x28`, Backspace `0x2A`, Space `0x2C`.
- **False lead:** treating the capture as network traffic (hunting for IP/HTTP
  layers) wastes time — usbmon frames have no IP layer at all.
- **Recognize it next time:** usbmon pcap → slice `payload[64:72]` per packet,
  drop empty reports, map usage-ids with shift. For non-mmapped
  `LINKTYPE_USB_LINUX` the header is 27 bytes instead of 64 — change that one
  offset and the same decoder works.

---

<a id="ru"></a>
# 02 — Afterimage2
[🇬🇧 English](#en) · **🇷🇺 Русский**

| | |
|---|---|
| **Категория** | 🧬 Forensics |
| **Файл задания** | [`usb_capture.pcap`](usb_capture.pcap) |
| **Статус** | ✅ Solved |
| **Флаг** | `THJCC{hid_k3y5tr0k3_l34k}` |

## 1. Условие

> Команда по кибербезопасности обнаружила «неопознанный кабель», подключённый к
> рабочей станции, подозреваемой в утечке данных. Мы захватили сырой трафик с
> этой линии, и данные показали частую активность в течение некоторого времени.

Одно вложение: `usb_capture.pcap`.

## 2. Первичный анализ

«Кабель» — подсказка: это дамп шины USB, а не сетевой трафик:

```bash
file usb_capture.pcap          # pcap capture file, microsecond ts (little-endian)
# тип канала в 24-байтовом глоб. заголовке: 220 = LINKTYPE_USB_LINUX_MMAPPED
```

- **Подтверждено:** тип канала **220** → захват Linux `usbmon`.
- **Подтверждено:** каждая запись — **72 байта** = **64-байтовый заголовок
  usbmon** + **8-байтовый USB HID-репорт клавиатуры**.
- **Подтверждено:** **50 пакетов** — пары нажатие/отпускание, то есть ~25
  реальных нажатий.

Значит задача на восстановление нажатий: раскодировать HID-репорты обратно в
текст.

## 3. Путь исследования

HID boot-репорт клавиатуры (8 байт):

| смещение | значение |
|---|---|
| 0 | маска модификаторов (`0x02` LeftShift, `0x20` RightShift) |
| 1 | зарезервировано |
| 2..7 | до 6 нажатых key usage-id (`0x00` = нет) |

**Подтверждённые** правила при обходе репортов:

- `key == 0` → отпускание / пустой репорт → пропуск (поэтому 50 пакетов → ~25
  символов).
- `key == 0x28` → Enter, `key == 0x2A` → Backspace.
- иначе мапим usage-id в символ, беря **shift-вариант** при `modifier & 0x22` —
  именно так получаются `{`, `}`, `_` (Shift+`[`, Shift+`]`, Shift+`-`). Тело —
  lowercase-leet, там shift не зажат.

Последовательность по порядку сразу складывается во флаг.

## 4. Инструменты и команды

```bash
# убедиться, что это USB (usbmon), а не Ethernet
file usb_capture.pcap

# по желанию: выгрузить HID-пейлоады через tshark, если установлен
tshark -r usb_capture.pcap -T fields -e usbhid.data | head

# самодостаточный солвер (чистый struct + loguru, scapy/tshark не нужны)
pip install loguru
python3 solve.py                 # по умолчанию ./usb_capture.pcap
python3 solve.py usb_capture.pcap
```

## 5. Пошаговое решение

1. Читаем 24-байтовый глобальный заголовок pcap, определяем порядок байт по
   magic, фиксируем тип канала 220.
2. Идём по 16-байтовым заголовкам записей и данным — получаем все 50 пакетов.
3. Для каждого пакета берём HID-репорт как `payload[64:72]`.
4. Читаем `modifier = report[0]`, `key = report[2]`.
5. Пропускаем `key == 0`; обрабатываем Enter/Backspace; иначе мапим `key` по
   HID-таблице с учётом shift при `modifier & 0x22`.
6. Склеиваем символы → флаг.

## 6. Итоговое решение

```console
$ python3 solve.py
INFO    pcap magic=d4c3b2a1 endian=< link_type=220
INFO    parsed 50 packets
SUCCESS recovered flag: THJCC{hid_k3y5tr0k3_l34k}
THJCC{hid_k3y5tr0k3_l34k}
```

25 нажатий раскодируются прямо во флаг — «частая активность в течение
некоторого времени» это просто набор флага на подброшенной клавиатуре.

## 7. Флаг

```
THJCC{hid_k3y5tr0k3_l34k}
```

## 8. Ключевые выводы

- **Сигнал:** `.pcap` с типом канала **220** (`USB_LINUX_MMAPPED`) или **189**
  (`USB_LINUX`) плюс упоминание «кабеля»/«устройства» — это восстановление
  нажатий USB HID, а не TCP/HTTP. Мелкие однородные пакеты (здесь 72 байта)
  подтверждают гипотезу.
- **Шпаргалка по HID:** смещение 2 — код клавиши; `modifier & 0x22` — зажат
  shift; `a`..`z` = `0x04`..`0x1D`; `1`..`0` = `0x1E`..`0x27`; Enter `0x28`,
  Backspace `0x2A`, Space `0x2C`.
- **Ложный след:** трактовать захват как сетевой трафик (искать слои IP/HTTP) —
  пустая трата времени: у usbmon-кадров IP-слоя нет вовсе.
- **Как узнать в следующий раз:** usbmon pcap → срез `payload[64:72]` по пакету,
  выкинуть пустые репорты, мапить usage-id с учётом shift. Для не-mmapped
  `LINKTYPE_USB_LINUX` заголовок 27 байт вместо 64 — поменять одно это смещение,
  и тот же декодер работает.
