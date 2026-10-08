#!/usr/bin/env python3
"""THJCC 2026 Summer - "BlackFrost" solver.

Two artefacts: a 7 KB static, stripped ELF (x86-64, raw syscalls, ws2_32-style C2 client)
and a 304-byte pcap of its loopback session.

The capture holds the whole handshake::

    ->  BFHELLO b700b632
    <-  BF2:0bbc114acd70...84cec0f

``b700b632`` is the FNV-1a 32 hash of the ``--token`` argument, which the binary compares
against the hard-coded ``0xB700B632``. The token itself is never needed: the hash is the
key material, and the capture hands it over.

C2 payload decryption (loop at 0x1400019C9)::

    plain[n] = cipher[n] ^ (hash >> (8 * (n & 3))) ^ ((90 + 17 * n) & 0xFF)

That yields the campaign configuration. The flag is a separate ``.rodata`` blob at VA
0x140003080, encoded with the author's usual rolling-XOR stream (key starts at 0x26, grows
by 0x1A per pair, the even byte of a pair uses ``key - 0x0D``), printed with WriteFile once
the configuration parses.

Anti-analysis in the binary, neither of which matters statically: ``IsDebuggerPresent`` ->
"analysis mode disabled", and a ``GetTickCount`` delta of >= 3001 ms -> "sandbox timeout".

Usage:
    python3 solve.py --binary BlackFrost.exe --pcap traffic.pcap
"""

from __future__ import annotations

import argparse
import re
import struct
import sys
from pathlib import Path
from typing import NamedTuple

from loguru import logger

FLAG_VA: int = 0x140003080
FLAG_LEN: int = 34
FLAG_KEY_START: int = 0x26
FLAG_KEY_STEP: int = 0x1A
FLAG_EVEN_BIAS: int = 0x0D

PAYLOAD_BIAS: int = 90
PAYLOAD_STEP: int = 17

HELLO_RE: re.Pattern[bytes] = re.compile(rb"BFHELLO ([0-9a-fA-F]{8})")
PAYLOAD_RE: re.Pattern[bytes] = re.compile(rb"BF2:([0-9a-fA-F]+)")

PCAP_MAGIC_LE: bytes = b"\xd4\xc3\xb2\xa1"
PCAP_MAGIC_BE: bytes = b"\xa1\xb2\xc3\xd4"

EXPECTED_CONFIG: str = "campaign=BLACKFROST-26;nonce=4c2f17;directive=collect-only;"
EXPECTED_FLAG: str = "THJCC{blackfrost_config_recovered}"


class PeSection(NamedTuple):
    """Minimal PE section descriptor."""

    name: str
    va: int
    raw_offset: int
    raw_size: int


def read_sections(blob: bytes) -> tuple[int, list[PeSection]]:
    """Return the image base and the section table of a PE32+ image."""
    pe_offset = struct.unpack_from("<I", blob, 0x3C)[0]
    if blob[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise ValueError("not a PE image")
    section_count = struct.unpack_from("<H", blob, pe_offset + 6)[0]
    opt_size = struct.unpack_from("<H", blob, pe_offset + 20)[0]
    opt_offset = pe_offset + 24
    image_base = struct.unpack_from("<Q", blob, opt_offset + 24)[0]

    sections: list[PeSection] = []
    table = opt_offset + opt_size
    for index in range(section_count):
        entry = table + index * 40
        name = blob[entry : entry + 8].rstrip(b"\0").decode()
        _, virtual_address, raw_size, raw_offset = struct.unpack_from("<IIII", blob, entry + 8)
        sections.append(PeSection(name, image_base + virtual_address, raw_offset, raw_size))
    return image_base, sections


def va_to_offset(sections: list[PeSection], va: int) -> int:
    """Translate a virtual address into a file offset."""
    for section in sections:
        if section.va <= va < section.va + section.raw_size:
            return section.raw_offset + (va - section.va)
    raise LookupError(f"virtual address {va:#x} is not mapped by any section")


def iter_tcp_payloads(pcap: bytes) -> list[bytes]:
    """Yield the TCP payload of every Ethernet/IPv4/TCP record in a classic pcap."""
    magic = pcap[:4]
    if magic == PCAP_MAGIC_LE:
        endian = "<"
    elif magic == PCAP_MAGIC_BE:
        endian = ">"
    else:
        raise ValueError("not a classic pcap file")

    payloads: list[bytes] = []
    cursor = 24
    while cursor + 16 <= len(pcap):
        _, _, captured, _ = struct.unpack_from(f"{endian}IIII", pcap, cursor)
        frame = pcap[cursor + 16 : cursor + 16 + captured]
        cursor += 16 + captured
        if len(frame) < 14 or frame[12:14] != b"\x08\x00":
            continue
        ip = frame[14:]
        ip_header_len = (ip[0] & 0x0F) * 4
        if ip[9] != 6:
            continue
        tcp = ip[ip_header_len:]
        tcp_header_len = (tcp[12] >> 4) * 4
        payload = tcp[tcp_header_len:]
        if payload:
            payloads.append(payload)
    return payloads


def decrypt_payload(cipher: bytes, token_hash: int) -> bytes:
    """Undo the C2 stream cipher keyed by the FNV-1a hash of the token."""
    return bytes(
        byte ^ ((token_hash >> (8 * (index & 3))) & 0xFF) ^ ((PAYLOAD_BIAS + PAYLOAD_STEP * index) & 0xFF)
        for index, byte in enumerate(cipher)
    )


def decode_rolling_xor(data: bytes, key_start: int, key_step: int, even_bias: int) -> bytes:
    """Undo the author's rolling-XOR stream (same shape as License / 404 / xorlocks)."""
    out = bytearray()
    key = key_start
    for pair_index in range(0, len(data), 2):
        out.append(data[pair_index] ^ ((key - even_bias) & 0xFF))
        if pair_index + 1 < len(data):
            out.append(data[pair_index + 1] ^ key)
        key = (key + key_step) & 0xFF
    return bytes(out)


def fnv1a_32(data: bytes) -> int:
    """FNV-1a 32-bit hash - the token check the binary performs at 0x1400012B6."""
    digest = 0x811C9DC5
    for byte in data:
        digest = ((digest ^ byte) * 0x01000193) & 0xFFFFFFFF
    return digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--binary",
        type=Path,
        default=Path(__file__).with_name("BlackFrost.exe"),
        help="path to the challenge binary",
    )
    parser.add_argument(
        "--pcap",
        type=Path,
        default=Path(__file__).with_name("traffic.pcap"),
        help="path to the captured C2 session",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="optional token to hash and compare against the value seen in the capture",
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(sys.stderr, level="INFO", format="<level>{level: <7}</level> {message}")

    for path in (args.binary, args.pcap):
        if not path.is_file():
            logger.error("no such file: {}", path)
            return 1

    payloads = iter_tcp_payloads(args.pcap.read_bytes())
    logger.info("pcap: {} tcp payloads", len(payloads))

    joined = b"".join(payloads)
    hello = HELLO_RE.search(joined)
    cipher_match = PAYLOAD_RE.search(joined)
    if hello is None or cipher_match is None:
        logger.error("capture does not contain a BFHELLO / BF2 pair")
        return 1

    token_hash = int(hello.group(1), 16)
    logger.info("handshake hash = {:#010x}", token_hash)
    if args.token is not None:
        logger.info("fnv-1a({!r}) = {:#010x}", args.token, fnv1a_32(args.token.encode()))

    cipher = bytes.fromhex(cipher_match.group(1).decode())
    logger.info("c2 payload: {} bytes", len(cipher))

    config = decrypt_payload(cipher, token_hash).decode()
    logger.success("config = {}", config)

    blob = args.binary.read_bytes()
    image_base, sections = read_sections(blob)
    logger.info("image base {:#x}, sections: {}", image_base, ", ".join(s.name for s in sections))

    offset = va_to_offset(sections, FLAG_VA)
    flag = decode_rolling_xor(
        blob[offset : offset + FLAG_LEN],
        FLAG_KEY_START,
        FLAG_KEY_STEP,
        FLAG_EVEN_BIAS,
    ).rstrip(b"\x00").decode()
    logger.success("flag = {}", flag)

    if config != EXPECTED_CONFIG or flag != EXPECTED_FLAG:
        logger.error("does not match the known-good config/flag")
        return 1
    logger.success("matches the known-good config and flag")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
