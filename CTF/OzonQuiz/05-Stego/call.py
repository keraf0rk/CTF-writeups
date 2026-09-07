#используйте виртуальные окружение 
#plese create virtual environment


"""Quest 5 (Stego) — DTMF в режиме multi-tap поверх офисного шума.

Аудио: 93 c, stereo, стоковый клип «звуки офиса» как cover. «Обычный разговор» и
«звуки набора цифр» — маскировка. Реальные данные набраны **DTMF-тонами** в режиме
**multi-tap** (набор букв на кнопочном телефоне: 2=ABC, 6=MNO, 7=PQRS, 9=WXYZ ...),
где N нажатий одной цифры = N-я буква.

Детектор: Goertzel по 8 DTMF-частотам (порог по «чистоте тона», чтобы отсечь речь) +
точный подсчёт тапов по пикам огибающей каждой пары тонов.

Раскодированная последовательность (клавиша 1 — структурная: скобки/разделитель):
    OZONCTF { S3CR3T _ CH4NN3(1) }
т.е. S3CR3T = SECRET, CH4NN3L = CHANNEL (A->4, E->3, L->1).

Флаг: ozonctf{S3CR3T_CH4NN31}   (вариант с L как буква: ozonctf{S3CR3T_CH4NN3L})

Запуск:  python3 solve_dtmf.py Task_5.wav
Зависимости: numpy, scipy
"""
from __future__ import annotations

import sys
import wave

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

LOW = [697, 770, 852, 941]
HIGH = [1209, 1336, 1477, 1633]
KEYPAD = {
    (0, 0): "1", (0, 1): "2", (0, 2): "3",
    (1, 0): "4", (1, 1): "5", (1, 2): "6",
    (2, 0): "7", (2, 1): "8", (2, 2): "9",
    (3, 1): "0",
}
# частоты для конкретной клавиши (для подсчёта тапов по огибающей)
TONES = {
    "1": (697, 1209), "2": (697, 1336), "3": (697, 1477),
    "4": (770, 1209), "5": (770, 1336), "6": (770, 1477),
    "7": (852, 1209), "8": (852, 1336), "9": (852, 1477),
    "0": (941, 1336),
}
MULTITAP = {
    "2": "ABC2", "3": "DEF3", "4": "GHI4", "5": "JKL5",
    "6": "MNO6", "7": "PQRS7", "8": "TUV8", "9": "WXYZ9", "1": "1", "0": " 0",
}


def read_mono(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path) as w:
        sr = w.getframerate()
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
    data = data.astype(np.float64)
    if w.getnchannels() == 2:
        data = data.reshape(-1, 2).mean(axis=1)
    return data, sr


def goertzel(segment: np.ndarray, freq: float, sr: int) -> float:
    n = len(segment)
    k = int(round(n * freq / sr))
    coeff = 2 * np.cos(2 * np.pi * k / n)
    s1 = s2 = 0.0
    for value in segment:
        s0 = value + coeff * s1 - s2
        s2, s1 = s1, s0
    return s1 * s1 + s2 * s2 - coeff * s1 * s2


def detect_letters(signal: np.ndarray, sr: int) -> list[dict]:
    """Найти окна букв (одна цифра, разделённые паузами) по чистому двухтональному DTMF."""
    win = int(sr * 0.035)
    hop = int(sr * 0.01)
    labels: list[tuple[float, str | None]] = []
    for i in range(0, len(signal) - win, hop):
        seg = signal[i:i + win] * np.hanning(win)
        lo = [goertzel(seg, f, sr) for f in LOW]
        hi = [goertzel(seg, f, sr) for f in HIGH]
        li, hii = int(np.argmax(lo)), int(np.argmax(hi))
        lo2 = sorted(lo)[-2] + 1
        hi2 = sorted(hi)[-2] + 1
        purity = (lo[li] + hi[hii]) / (sum(lo) + sum(hi) + 1)
        ok = (lo[li] / lo2 > 6 and hi[hii] / hi2 > 6 and purity > 0.8
              and min(lo[li], hi[hii]) > 4e6 and hii < 3)
        labels.append((i / sr, KEYPAD.get((li, hii)) if ok else None))

    letters: list[dict] = []
    cur: dict | None = None
    for t, dig in labels:
        if dig is None:
            continue
        if cur and cur["dig"] == dig and (t - cur["end"]) < 0.8:
            cur["end"] = t
        else:
            if cur:
                letters.append(cur)
            cur = {"dig": dig, "start": t, "end": t}
    if cur:
        letters.append(cur)
    return letters


def _bandpass(x: np.ndarray, freq: float, sr: int, bw: int = 20) -> np.ndarray:
    b, a = butter(4, [(freq - bw) / (sr / 2), (freq + bw) / (sr / 2)], btype="band")
    return filtfilt(b, a, x)


def count_taps(signal: np.ndarray, sr: int, start: float, end: float,
               dig: str) -> tuple[int, float]:
    """Число тапов в окне буквы (по пикам огибающей двух тонов) и пиковая энергия."""
    fl, fh = TONES[dig]
    s = max(0, int((start - 0.08) * sr))
    e = int((end + 0.1) * sr)
    seg = signal[s:e]
    env = np.abs(_bandpass(seg, fl, sr)) + np.abs(_bandpass(seg, fh, sr))
    k = int(sr * 0.008)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    peaks, _ = find_peaks(env, height=env.max() * 0.42, distance=int(sr * 0.14))
    return max(1, len(peaks)), float(env.max())


# Полезное сообщение набирается в интервале ~21..76 c; вне него — только офисный
# cover (речь/клавиатура), который изредка проходит фильтр как ложные буквы.
MSG_START, MSG_END = 20.0, 78.0


def solve(path: str, t0: float = MSG_START, t1: float = MSG_END) -> str:
    """Печатает сильные (реальные DTMF) буквы в окне сообщения и возвращает их строку.

    Порог по пиковой энергии отсекает речевой cover; остаётся multi-tap-сообщение.
    Клавиша 1 — структурная (скобки/разделитель).
    """
    signal, sr = read_mono(path)
    letters = []
    for letter in detect_letters(signal, sr):
        if not (t0 <= letter["start"] <= t1):
            continue
        taps, energy = count_taps(signal, sr, letter["start"], letter["end"], letter["dig"])
        letters.append({**letter, "taps": taps, "energy": energy})

    if not letters:
        return ""
    threshold = 0.35 * max(l["energy"] for l in letters)  # сильные тона = реальный DTMF

    out = ""
    for l in letters:
        if l["energy"] < threshold:
            continue
        ch = MULTITAP[l["dig"]][(l["taps"] - 1) % len(MULTITAP[l["dig"]])]
        out += ch
        print(f"  {l['dig']} x{l['taps']} = {ch}  @{l['start']:.1f}s")
    return out


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else "Task_5.wav"
    decoded = solve(path)
    print("\nСильные DTMF-буквы (multi-tap):", decoded)
    print("Чтение (клавиша 1 = { / _ / }):  OZONCTF { S3CR3T _ CH4NN3(1) }")
    print("Содержание: S3CR3T = SECRET, CH4NN3L = CHANNEL  ->  «secret channel»")
    print("Флаг: ozonctf{S3CR3T_CH4NN31}   (либо ozonctf{S3CR3T_CH4NN3L})")


if __name__ == "__main__":
    main()
