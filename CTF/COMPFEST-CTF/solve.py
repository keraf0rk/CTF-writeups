#!/usr/bin/env python3
"""
BurhanGuild Loader Incident  -  full solver
Compfest CTF  /  Forensics  /  100 pts

Chain:
  1. pick the ONE internally-consistent volatile capture (the real event)
  2. match it to its deleted-storage page (same host + evidence_ref)
  3. carve the loader region (BGMR record type 9) out of that capture
  4. re-derive the loader key schedule from artifacts in the SAME capture and
     decrypt the embedded CFG3 blob (custom KDF + XTEA-32 in CTR mode)
  5. rebuild the incident proof token per the config's closure_contract.

Usage:  python3 solve.py [path-to-extracted-attachment]
Only the public attachment is needed. No network.
"""
import argparse, hashlib, json, re, struct, sys, importlib.util
from pathlib import Path

M = 0xffffffff
def rol(x, r):
    r &= 31
    return ((x << r) | (x >> (32 - r))) & M

def kdf(parts):
    """Loader's custom key schedule (pi-digit IV + 0x9e3779b9), from the .so."""
    st = [0x243f6a88, 0x85a308d3, 0x13198a2e, 0x03707344]
    data = b"".join(parts); c1 = 0
    for i, b in enumerate(data):
        s1 = st[(i + 1) & 3]
        t = (((s1 << 6) & M) + (s1 >> 2) + 0x9e3779b9) & M
        t = (t + b) & M
        t ^= st[i & 3]
        t = rol(t, (i % 13) + 5)
        st[i & 3] = t
        st[(i + 2) & 3] = (st[(i + 2) & 3] + (t ^ c1)) & M
        c1 = (c1 + 0x045d9f3b) & M
    return b"".join(struct.pack(">I", x) for x in st)

def xtea(block8, key16):
    v0, v1 = struct.unpack(">II", block8)
    k = struct.unpack(">IIII", key16); s = 0; d = 0x9e3779b9
    for _ in range(32):
        v0 = (v0 + ((((v1 << 4) ^ (v1 >> 5)) & M) + v1 ^ (s + k[s & 3]))) & M
        s = (s + d) & M
        v1 = (v1 + ((((v0 << 4) ^ (v0 >> 5)) & M) + v0 ^ (s + k[(s >> 11) & 3]))) & M
    return struct.pack(">II", v0, v1)

def decrypt_cfg(ct, mutex, heap8, build10):
    key = kdf([mutex, heap8, build10, b"eir-v3"]); nonce = heap8[:4]; out = bytearray()
    for i in range((len(ct) + 7) // 8):
        ks = xtea(nonce + b"\x00\x00\x00" + bytes([i]), key)
        out += bytes(a ^ b for a, b in zip(ct[i*8:i*8+8], ks))
    return bytes(out)

sha256 = lambda b: hashlib.sha256(b).hexdigest()

def load_helper(pkg):
    spec = importlib.util.spec_from_file_location("bg", str(pkg / "plugins" / "bgloader_hunt.py"))
    bg = importlib.util.module_from_spec(spec); spec.loader.exec_module(bg); return bg

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pkg", nargs="?", default="challenge/BurhanGuild-Loader-Incident")
    pkg = Path(ap.parse_args().pkg); bg = load_helper(pkg)

    caps  = sorted((pkg / "artifacts" / "captures").glob("*.raw"))
    pages = sorted((pkg / "artifacts" / "deleted_pages").glob("*.bin"))

    # 1) isolate the genuine capture -----------------------------------------
    real = recs = loader_pid = None
    for cap in caps:
        r = {k: b for k, o, b in bg.records(str(cap))}
        if 5 not in r or 6 not in r or 7 not in r:
            continue
        maps_has_loader = b"libpam_bg.so" in r[5]
        file_has_cache  = b".bg-cache" in r[7]
        c2_external     = b"invalid" in r[6]
        if maps_has_loader and file_has_cache and c2_external:
            real, recs = cap, r
            loader_pid = struct.unpack(">I", r[5][:4])[0]   # maps record starts with pid
            break
    if not real:
        sys.exit("could not isolate the genuine capture")
    print(f"[+] genuine capture : {real.name}")
    print(f"[+] loader pid      : {loader_pid}")

    # build_id (maps, type 5): pid(4) vma(8) perms(4) name(str8) build(10)
    c = bg.Cursor(recs[5]); c.unpack(">IQ"); c.take(4); c.text8(); build10 = c.take(10)

    # 8-byte heap fragment (type 4) -> KDF material + CTR nonce
    c = bg.Cursor(recs[4]); pid, cnt = c.unpack(">IH"); heap8 = None
    for _ in range(cnt):
        addr, size = c.unpack(">QI"); frag = c.take(size)
        if size == 8: heap8 = frag

    # BG_MUTEX (environment, type 3)
    c = bg.Cursor(recs[3]); (cnt,) = c.unpack(">H"); mutex = None
    for _ in range(cnt):
        c.unpack(">I"); k = c.text8(); v = c.text16()
        if k == "BG_MUTEX": mutex = v.encode()

    # JNDI payload from the java heap (type 4, the printable fragment)
    c = bg.Cursor(recs[4]); pid, cnt = c.unpack(">IH"); jndi = None
    for _ in range(cnt):
        addr, size = c.unpack(">QI"); frag = c.take(size)
        if b"ldap://" in frag:
            # de-obfuscate the log4shell payload: ${lower:x} -> x
            jndi = re.sub(r"\$\{lower:(.)\}", r"\1", frag.decode())

    print(f"[+] BG_MUTEX        : {mutex.decode()}")
    print(f"[+] heap nonce/key  : {heap8.hex()}")
    print(f"[+] build id        : {build10.hex()}")
    print(f"[+] jndi payload    : {jndi}")

    # 2) match the deleted page via evidence_ref -----------------------------
    c = bg.Cursor(recs[7]); (cnt,) = c.unpack(">H"); evref = None
    for _ in range(cnt):
        c.unpack(">IHB"); pth = c.text16(); c.unpack(">QI"); ref = c.text8()
        if ".bg-cache" in pth: evref = ref
    import zipfile, io
    archive = None
    for page in pages:
        raw = page.read_bytes()
        st = raw.find(b"PK\x03\x04"); en = raw.find(b"PK\x05\x06", st)
        if st < 0 or en < 0:
            continue
        blob = raw[st:en + 22]
        try:
            z = zipfile.ZipFile(io.BytesIO(blob))
            inside = b"".join(z.read(n) for n in z.namelist())
        except Exception:
            continue
        if evref.encode() in inside:                 # same evidence_ref = same event
            archive = blob
            print(f"[+] matched page    : {page.name}  ({evref})")
            break
    archive_sha = sha256(archive)
    print(f"[+] archive sha256  : {archive_sha}")

    # 3) carve loader region (type 9) ----------------------------------------
    region = recs[9]
    print(f"[+] carved .so      : {len(region)} bytes  sha256={sha256(region)}")

    # 4) decrypt CFG3 --------------------------------------------------------
    i = region.find(b"CFG3"); (clen,) = struct.unpack(">I", region[i+4:i+8])
    cfg = decrypt_cfg(region[i+8:i+8+clen], mutex, heap8, build10)
    conf = json.loads(cfg)
    assert format(__import__("zlib").crc32(cfg.replace(b',"crc32":"%s"' % conf["crc32"].encode(), b"")) & M, "08x") == conf["crc32"], "crc mismatch"
    print("[+] CFG3 decrypted & crc32 verified:")
    print("    " + json.dumps(conf, indent=2).replace("\n", "\n    "))
    config_sha = sha256(cfg)

    # 5) rebuild the proof token ---------------------------------------------
    cc = conf["closure_contract"]
    fields = {
        "jndi_normalized": jndi,
        "build_id": build10.hex(),
        "implant_id": conf["implant_id"],
        "c2_domain": conf["c2_domain"],
        "archive_sha256": archive_sha,
    }
    digest = hashlib.sha256(cc["digest_separator"].join(fields[f] for f in cc["digest_fields"]).encode()).hexdigest()
    token = cc["token_schema"]
    for k, v in {
        "capture_id": real.stem.split("_")[1], "loader_pid": loader_pid,
        "implant_id": conf["implant_id"], "build_id": build10.hex(),
        "config_sha256": config_sha, "archive_sha256": archive_sha, "digest": digest,
    }.items():
        token = token.replace("{" + k + "}", str(v))
    print("\n[FLAG] " + token)

if __name__ == "__main__":
    main()
