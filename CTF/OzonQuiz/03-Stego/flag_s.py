#для проверки скрипта создавайте виртуалку
#if you want check this script, please create a virtual environment.

"""Quest 3 (Stego) — азбука Морзе, спрятанная в разности стереоканалов (L-R).

Аудио: 55 c, stereo 44.1 kHz. Обычная/поканальная спектрограмма — только шум
(«дыхание через акваланг» = маскирующий cover). Разность каналов L-R убирает
общий cover и обнажает чистый сигнал: короткие/длинные тональные всплески = Морзе.

Точка ≈ 124 мс, тире ≈ 363 мс (×3). Декодируется без ошибок в:
    S3CR3TD3L1V3RYM3SS4G3   (SECRET DELIVERY MESSAGE, leet)

Флаг: ozonctf{S3CR3TD3L1V3RYM3SS4G3}
Запуск:  python3 flag_s.py task.wav
"""

from __future__ import annotations

import sys
import wave

import numpy as np

MORSE = {
    ".-": "A", "-...": "B", "-.-.": "C", "-..": "D", ".": "E", "..-.": "F",
    "--.": "G", "....": "H", "..": "I", ".---": "J", "-.-": "K", ".-..": "L",
    "--": "M", "-.": "N", "---": "O", ".--.": "P", "--.-": "Q", ".-.": "R",
    "...": "S", "-": "T", "..-": "U", "...-": "V", ".--": "W", "-..-": "X",
    "-.--": "Y", "--..": "Z",
    "-----": "0", ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8", "----.": "9",
}


def read_stereo(path: str) -> tuple[np.ndarray, np.ndarray, int]:
    with wave.open(path) as w:
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    data = data.astype(np.float64).reshape(-1, 2)
    return data[:, 0], data[:, 1], sr


def decode_morse(path: str) -> str:
    left, right, sr = read_stereo(path)
    diff = left - right  # изолируем скрытый сигнал из-под общего cover

    # огибающая по амплитуде + сглаживание
    win = int(sr * 0.005)
    env = np.convolve(np.abs(diff), np.ones(win) / win, mode="same")
    on = env > env.max() * 0.15  # порог «тон включён»

    # сегменты «тона включены»
    edges = np.where(np.diff(on.astype(int)) != 0)[0]
    segments: list[tuple[float, float]] = []
    if on[0]:
        edges = np.insert(edges, 0, 0)
    for i in range(0, len(edges) - 1, 2):
        segments.append((edges[i] / sr, edges[i + 1] / sr))

    durations = [b - a for a, b in segments]
    unit = float(np.median([d for d in durations if d < 0.2]))  # длина точки

    out, symbol = "", ""
    for i, (start, end) in enumerate(segments):
        symbol += "." if (end - start) < unit * 2 else "-"
        gap = (segments[i + 1][0] - end) if i < len(segments) - 1 else 1e9
        if gap > unit * 5:      # пробел между словами
            out += MORSE.get(symbol, "#") + " "
            symbol = ""
        elif gap > unit * 2:    # пробел между буквами
            out += MORSE.get(symbol, "#")
            symbol = ""
    if symbol:
        out += MORSE.get(symbol, "#")
    return out


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "task.wav"
    inner = decode_morse(path).strip()
    print("Морзе-сообщение:", inner)
    print("Флаг:", "ozonctf{%s}" % inner.replace(" ", ""))


if __name__ == "__main__":
    main()