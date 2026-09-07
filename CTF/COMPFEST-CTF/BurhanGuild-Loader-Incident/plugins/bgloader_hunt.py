#!/usr/bin/env python3
import argparse
import hashlib
import ipaddress
import struct
from datetime import datetime, timezone
from pathlib import Path


MAGIC = b"BGMR"
HEADER = struct.Struct(">4sBBI")


class ParseError(ValueError):
    pass


class Cursor:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def take(self, size):
        if size < 0 or self.pos + size > len(self.data):
            raise ParseError("truncated record")
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def unpack(self, fmt):
        spec = struct.Struct(fmt)
        return spec.unpack(self.take(spec.size))

    def text8(self):
        size, = self.unpack(">B")
        return self.take(size).decode("utf-8")

    def text16(self):
        size, = self.unpack(">H")
        return self.take(size).decode("utf-8")


def records(path):
    data = Path(path).read_bytes()
    pos = 0
    result = []
    while True:
        offset = data.find(MAGIC, pos)
        if offset < 0:
            break
        if offset + HEADER.size > len(data):
            raise ParseError(f"truncated header at {offset:#x}")
        magic, version, kind, size = HEADER.unpack_from(data, offset)
        if magic != MAGIC or version != 3:
            pos = offset + 1
            continue
        start = offset + HEADER.size
        end = start + size
        if size > 16 * 1024 * 1024 or end > len(data):
            raise ParseError(f"invalid record length at {offset:#x}")
        result.append((kind, offset, data[start:end]))
        pos = end
    return result


def body_for(path, expected_kind):
    matches = [(offset, body) for kind, offset, body in records(path)
               if kind == expected_kind]
    if len(matches) != 1:
        raise ParseError(
            f"expected one record of type {expected_kind}, found {len(matches)}"
        )
    return matches[0]


def table(rows, columns):
    widths = {
        key: max(len(label), *(len(str(row.get(key, ""))) for row in rows))
        for key, label in columns
    }
    print(" | ".join(label.ljust(widths[key]) for key, label in columns))
    print("-+-".join("-" * widths[key] for key, _ in columns))
    for row in rows:
        print(" | ".join(str(row.get(key, "")).ljust(widths[key])
                         for key, _ in columns))


def iso_time(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def metadata(path, _args):
    offset, body = body_for(path, 1)
    capture_time, process_count, boot_id, kernel_size = struct.unpack_from(
        ">QH20sB", body
    )
    kernel = body[31:31 + kernel_size].decode()
    table([{
        "offset": hex(offset),
        "kernel": kernel,
        "capture_time": iso_time(capture_time),
        "processes": process_count,
        "boot_id": boot_id.hex(),
    }], [
        ("offset", "OFFSET"), ("kernel", "KERNEL"),
        ("capture_time", "CAPTURE TIME"), ("processes", "PROCESSES"),
        ("boot_id", "BOOT ID"),
    ])


def read_process(cursor):
    pid, ppid, started = cursor.unpack(">IIQ")
    return {
        "pid": pid,
        "ppid": ppid,
        "started": iso_time(started),
        "comm": cursor.text8(),
    }


def processes(path, _args):
    _offset, body = body_for(path, 2)
    cursor = Cursor(body)
    list_count, scan_count = cursor.unpack(">HH")
    rows = []
    for source, count in (("list", list_count), ("scan", scan_count)):
        for _ in range(count):
            row = read_process(cursor)
            row["source"] = source
            rows.append(row)
    table(rows, [
        ("source", "SOURCE"), ("pid", "PID"), ("ppid", "PPID"),
        ("comm", "COMMAND"), ("started", "STARTED"),
    ])


def environment(path, _args):
    _offset, body = body_for(path, 3)
    cursor = Cursor(body)
    count, = cursor.unpack(">H")
    rows = []
    for _ in range(count):
        pid, = cursor.unpack(">I")
        rows.append({"pid": pid, "key": cursor.text8(), "value": cursor.text16()})
    table(rows, [("pid", "PID"), ("key", "KEY"), ("value", "VALUE")])


def heap(path, _args):
    _offset, body = body_for(path, 4)
    cursor = Cursor(body)
    pid, count = cursor.unpack(">IH")
    rows = []
    for _ in range(count):
        address, size = cursor.unpack(">QI")
        fragment = cursor.take(size)
        printable = all(32 <= byte < 127 for byte in fragment)
        rows.append({
            "pid": pid,
            "address": hex(address),
            "length": size,
            "sha256": hashlib.sha256(fragment).hexdigest(),
            "preview": fragment.decode() if printable else fragment.hex(),
        })
    table(rows, [
        ("pid", "PID"), ("address", "ADDRESS"), ("length", "LENGTH"),
        ("sha256", "SHA256"), ("preview", "DATA/PREVIEW"),
    ])


def maps(path, _args):
    _offset, body = body_for(path, 5)
    cursor = Cursor(body)
    pid, address = cursor.unpack(">IQ")
    perms = cursor.take(4).decode()
    name = cursor.text8()
    build_id = cursor.take(10).hex()
    region_hash = cursor.take(32).hex()
    table([{
        "pid": pid, "address": hex(address), "perms": perms,
        "name": name, "build_id": build_id, "sha256": region_hash,
    }], [
        ("pid", "PID"), ("address", "VMA"), ("perms", "PERMS"),
        ("name", "NAME"), ("build_id", "BUILD ID"),
        ("sha256", "REGION SHA256"),
    ])


def network(path, _args):
    _offset, body = body_for(path, 6)
    cursor = Cursor(body)
    count, = cursor.unpack(">H")
    states = {1: "ESTABLISHED", 2: "CLOSED", 3: "LISTEN"}
    rows = []
    for _ in range(count):
        pid, = cursor.unpack(">I")
        local_ip = str(ipaddress.ip_address(cursor.take(4)))
        local_port, = cursor.unpack(">H")
        remote = cursor.text8()
        remote_port, state = cursor.unpack(">HB")
        rows.append({
            "pid": pid,
            "local": f"{local_ip}:{local_port}",
            "remote": f"{remote}:{remote_port}",
            "state": states.get(state, f"UNKNOWN({state})"),
        })
    table(rows, [
        ("pid", "PID"), ("local", "LOCAL"),
        ("remote", "REMOTE"), ("state", "STATE"),
    ])


def files(path, _args):
    _offset, body = body_for(path, 7)
    cursor = Cursor(body)
    count, = cursor.unpack(">H")
    rows = []
    modes = {1: "deleted", 2: "read", 3: "write"}
    for _ in range(count):
        pid, fd, mode = cursor.unpack(">IHB")
        path_name = cursor.text16()
        inode, size = cursor.unpack(">QI")
        rows.append({
            "pid": pid, "fd": fd, "mode": modes.get(mode, mode),
            "path": path_name, "inode": inode, "size": size,
            "evidence_ref": cursor.text8(),
        })
    table(rows, [
        ("pid", "PID"), ("fd", "FD"), ("mode", "MODE"),
        ("inode", "INODE"), ("size", "SIZE"),
        ("evidence_ref", "EVIDENCE REF"), ("path", "PATH"),
    ])


def supply(path, _args):
    _offset, body = body_for(path, 10)
    cursor = Cursor(body)
    row = {
        "package": cursor.text8(),
        "advisory": cursor.text8(),
        "version": cursor.text8(),
        "assessment": cursor.text16(),
    }
    table([row], [
        ("package", "PACKAGE"), ("advisory", "ADVISORY"),
        ("version", "VERSION"), ("assessment", "ASSESSMENT"),
    ])


def carve_region(path, args):
    _offset, body = body_for(path, 9)
    output = Path(args.output)
    output.write_bytes(body)
    print(
        f"wrote {output} size={len(body)} "
        f"sha256={hashlib.sha256(body).hexdigest()}"
    )


COMMANDS = {
    "metadata": metadata,
    "processes": processes,
    "environment": environment,
    "heap": heap,
    "maps": maps,
    "network": network,
    "files": files,
    "supply": supply,
    "carve-region": carve_region,
}


def main():
    parser = argparse.ArgumentParser(description="Inspect BGMR v3 capture records")
    parser.add_argument("-f", "--file", required=True)
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("-o", "--output", default="region_dump.so")
    args = parser.parse_args()
    try:
        COMMANDS[args.command](Path(args.file), args)
    except (OSError, ParseError, UnicodeError, struct.error) as exc:
        raise SystemExit(f"error: {exc}") from exc


if __name__ == "__main__":
    main()
