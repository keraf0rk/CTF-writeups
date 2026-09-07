#!/usr/bin/env python3
"""Quest 4 (Stego + OSINT) — восстановление «зашифрованного» PNG.

«Шифр» = построчное стирание: изображение из 376 строк, где каждые 2 из 4 строк
обнулены (шаблон CC BB), поэтому картинка выглядит тёмной с горизонтальными полосами.

Восстановление: интерполируем «чёрные» строки по соседним + растяжка контраста.
Результат — фото авиалайнера **Airbus A321 «Уральских авиалиний» (борт VQ-BOZ)**
на перроне с пожарной машиной.

OSINT: борт VQ-BOZ = самолёт **рейса 178 «Уральских авиалиний»**, аварийная
посадка в кукурузном поле у деревни Рыбаки под Жуковским (15.08.2019, столкновение
с птицами). «Текущее местоположение» борта = место посадки.

Координаты места посадки (Яндекс POI / RU-Wikipedia): 55.5104, 38.2533.
Формат флага: ozonctf{xx.xxx_yy.yyy}

Запуск:  python3 solve_reconstruct.py plain.png  -> recon.png
"""
from __future__ import annotations

import sys

import numpy as np
from PIL import Image


def reconstruct(src: str, dst: str = "recon.png") -> None:
    arr = np.array(Image.open(src).convert("RGB")).astype(np.float64)
    gray = arr.mean(axis=2)
    row_mean = gray.mean(axis=1)
    black = row_mean < 2.0                       # обнулённые (стёртые) строки
    good = np.where(~black)[0]

    out = arr.copy()
    for r in np.where(black)[0]:                 # линейная интерполяция по соседям
        lo = good[good < r]
        hi = good[good > r]
        if len(lo) and len(hi):
            a, b = lo[-1], hi[0]
            w = (r - a) / (b - a)
            out[r] = arr[a] * (1 - w) + arr[b] * w
        elif len(lo):
            out[r] = arr[lo[-1]]
        elif len(hi):
            out[r] = arr[hi[0]]

    for c in range(3):                           # поканальная растяжка контраста
        ch = out[:, :, c]
        lo, hi = np.percentile(ch, 1), np.percentile(ch, 99.5)
        out[:, :, c] = np.clip((ch - lo) / (hi - lo) * 255, 0, 255)

    Image.fromarray(out.astype("uint8")).save(dst)
    print(f"[*] Восстановленное изображение: {dst}")
    print("[*] Опознание: Airbus A321 «Уральские авиалинии», борт VQ-BOZ (рейс 178).")
    print("[*] Место посадки у д. Рыбаки (Жуковский): 55.5104, 38.2533")
    print("[*] Флаг (формат xx.xxx_yy.yyy): ozonctf{55.510_38.253}")


if __name__ == "__main__":
    reconstruct(sys.argv[1] if len(sys.argv) > 1 else "plain.png")
