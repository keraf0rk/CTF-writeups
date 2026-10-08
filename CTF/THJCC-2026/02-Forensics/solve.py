#!/usr/bin/env python3
"""Afterimage2 — THJCC 2026 Summer.

Reconstruct keystrokes from a raw USB HID capture (Linux usbmon, DLT 220).

Each captured packet is a 64-byte usbmon header followed by an 8-byte USB HID
keyboard report:

    byte 0  -> modifier bitmap (bit 1 = LeftShift, bit 5 = RightShift)
    byte 1  -> reserved
    byte 2  -> first pressed key code (HID usage id)
    ...      (up to 6 simultaneous keys; only the first is needed here)

Decoding the key codes with shift handling spells out the flag. The parser is
dependency-free (pure ``struct``) so it runs anywhere without scapy/tshark.
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

from loguru import logger

# HID usage id -> (unshifted, shifted) character.
HID_KEYMAP: dict[int, str] = {
    4: "aA", 5: "bB", 6: "cC", 7: "dD", 8: "eE", 9: "fF", 10: "gG",
    11: "hH", 12: "iI", 13: "jJ", 14: "kK", 15: "lL", 16: "mM", 17: "nN",
    18: "oO", 19: "pP", 20: "qQ", 21: "rR", 22: "sS", 23: "tT", 24: "uU",
    25: "vV", 26: "wW", 27: "xX", 28: "yY", 29: "zZ",
    30: "1!", 31: "2@", 32: "3#", 33: "4$", 34: "5%", 35: "6^", 36: "7&",
    37: "8*", 38: "9(", 39: "0)",
    44: "  ", 45: "-_", 46: "=+", 47: "[{", 48: "]}", 49: "\\|",
    51: ";:", 52: "'\"", 53: "`~", 54: ",<", 55: ".>", 56: "/?",
}

KEY_ENTER = 40
KEY_BACKSPACE = 42
SHIFT_MASK = 0x22  # LeftShift (0x02) | RightShift (0x20)
USBMON_HEADER_LEN = 64
HID_REPORT_LEN = 8


def read_pcap_packets(path: Path) -> list[bytes]:
    """Return the raw payload of every record in a classic .pcap file."""
    data = path.read_bytes()
    if len(data) < 24:
        raise ValueError("file too small to be a pcap")

    magic = data[:4]
    if magic in (b"\xd4\xc3\xb2\xa1", b"\x4d\x3c\xb2\xa1"):
        endian = "<"
    elif magic in (b"\xa1\xb2\xc3\xd4", b"\xa1\xb2\x3c\x4d"):
        endian = ">"
    else:
        raise ValueError(f"unknown pcap magic: {magic.hex()}")

    link_type = struct.unpack(endian + "I", data[20:24])[0]
    logger.info("pcap magic={} endian={} link_type={}", magic.hex(), endian, link_type)

    packets: list[bytes] = []
    offset = 24
    while offset + 16 <= len(data):
        _ts_s, _ts_us, incl_len, _orig_len = struct.unpack(
            endian + "IIII", data[offset : offset + 16]
        )
        offset += 16
        packets.append(data[offset : offset + incl_len])
        offset += incl_len
    logger.info("parsed {} packets", len(packets))
    return packets


def decode_keystrokes(packets: list[bytes]) -> str:
    """Turn USB HID keyboard reports into the typed text."""
    typed: list[str] = []
    for pkt in packets:
        report = pkt[USBMON_HEADER_LEN : USBMON_HEADER_LEN + HID_REPORT_LEN]
        if len(report) < HID_REPORT_LEN:
            continue

        modifier, key = report[0], report[2]
        if key == 0:  # key-release / empty report
            continue

        shifted = bool(modifier & SHIFT_MASK)
        if key == KEY_ENTER:
            typed.append("\n")
        elif key == KEY_BACKSPACE:
            if typed:
                typed.pop()
        elif key in HID_KEYMAP:
            typed.append(HID_KEYMAP[key][1 if shifted else 0])
        else:
            logger.debug("unmapped key code {}", key)
            typed.append(f"<{key}>")
    return "".join(typed)


def main() -> int:
    parser = argparse.ArgumentParser(description="Decode USB HID keystrokes from a pcap")
    parser.add_argument(
        "pcap",
        nargs="?",
        default="usb_capture.pcap",
        type=Path,
        help="path to the USB capture (default: usb_capture.pcap)",
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level: <7}</level> {message}")

    packets = read_pcap_packets(args.pcap)
    flag = decode_keystrokes(packets)
    logger.success("recovered flag: {}", flag)
    print(flag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
