/*
 * Paint me a Flag — fast, bit-exact re-implementation of `paint_me_a_flag`.
 *
 * The original binary replays NP (= W*H) encrypted flood-fill operations and,
 * after each one, `diff` (= 64) decoy fills whose only purpose is to stir the
 * state hash. It recolours with a naive BFS, so one 1600x600 part takes hours.
 *
 * Here regions live in a union-find structure: an op touches only region
 * roots, region size and XOR-hash are maintained incrementally, and the decoy
 * rounds are evaluated arithmetically (they recolour a region and restore it,
 * so the canvas never changes). The state machine matches the binary exactly,
 * which is why every op decrypts and passes its 16-bit integrity tag.
 *
 * build:  cc -O2 -o render render.c
 * usage:  render <part.pmaf> <in.rgb32> <out.rgb32>
 *         rgb32 = raw little-endian uint32 0x00RRGGBB, W*H pixels, row-major.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef uint64_t u64;
typedef uint32_t u32;

static const u64 C1 = 0xbf58476d1ce4e5b9ULL, C2 = 0x94d049bb133111ebULL;
static const u64 M3 = 0xd6e8feb86659fd93ULL, GAMMA = 0x9e3779b97f4a7c15ULL;
static const u64 PIXEL_KEY = 0x243f6a8885a308d3ULL;    /* per-pixel hash salt   */
static const u64 S0_SALT = 0x6f3d9b21a4c875e1ULL;      /* initial-state salt    */
static const u64 DECOY_R14 = 15485907386658061715ULL;  /* decoy counter base    */

/* splitmix64 finaliser */
static inline u64 mix(u64 z) {
    z = (z ^ (z >> 30)) * C1;
    z = (z ^ (z >> 27)) * C2;
    return z ^ (z >> 31);
}

static int W, H;
static long N;
static int *parent;                 /* union-find parent                    */
static long *rsize;                 /* region size in pixels                */
static u64 *rhash;                  /* XOR of mix(pixel_index ^ PIXEL_KEY)  */
static u32 *rcolor;                 /* region colour (valid at the root)    */
static int **adj, *adj_n, *adj_cap; /* neighbour lists of region roots      */
static int *seen, epoch = 1;

static int find(int x) {
    while (parent[x] != x) { parent[x] = parent[parent[x]]; x = parent[x]; }
    return x;
}

static void adj_push(int r, int v) {
    if (adj_n[r] >= adj_cap[r]) {
        adj_cap[r] = adj_cap[r] ? adj_cap[r] * 2 : 4;
        adj[r] = realloc(adj[r], (size_t)adj_cap[r] * sizeof(int));
    }
    adj[r][adj_n[r]++] = v;
}

static int unite(int a, int b) {
    a = find(a); b = find(b);
    if (a == b) return a;
    if (rsize[a] < rsize[b]) { int t = a; a = b; b = t; }
    parent[b] = a;
    rsize[a] += rsize[b];
    rhash[a] ^= rhash[b];
    for (int i = 0; i < adj_n[b]; i++) adj_push(a, adj[b][i]);
    free(adj[b]); adj[b] = NULL; adj_n[b] = adj_cap[b] = 0;
    return a;
}

/* State update after the real fill (f1 = filled size, f2 = filled hash,
 * f3 = previous colour). Transcribed 1:1 from the binary. */
static u64 update_main(u64 state, u64 ctr, u64 Y, u64 f1, u64 f2, u64 f3) {
    u64 A = f2, rsi = Y, rdx = (f3 << 24);
    u64 rcx = (A >> 30) ^ A; rsi |= rdx;
    rcx = rcx * C1; rcx ^= rcx >> 27; u64 rax = (rdx >> 30) ^ rsi; rcx = rcx * C2;
    rax = rax * C1; rax ^= rax >> 27; u64 rdxx = f1 * M3; rax = rax * C2;
    rdxx ^= rcx; rdxx ^= rcx >> 31; rdxx ^= state; rdxx ^= ctr; rdxx ^= rax;
    rax = rax >> 31; rax ^= rdxx;
    return mix(rax);
}

/* One decoy round: the merged region (size f1r, hash f2r) is painted with a
 * pseudo-random decoy colour and then back with Y. Canvas is unchanged, only
 * the state moves. Transcribed 1:1 from the binary (note the 32-bit decoy). */
static u64 decoy_round(u64 state, u64 ctr, u64 Y, u64 f1r, u64 f2r, u64 r14) {
    u64 rdx = ctr ^ state ^ r14;
    u64 rcx = ((rdx ^ (rdx >> 30)) * C1); u64 rax = rcx >> 27; rax ^= rcx; rax *= C2;
    u64 r12v = rax ^ (rax >> 31); u32 r12d = (u32)r12v; r12d = (r12d & 0xfffffe) | 1;
    while (r12d == 0xf2eadf) {      /* the reserved colour is never used as decoy */
        rdx += GAMMA;
        u64 a = ((rdx ^ (rdx >> 30)) * C1); a = ((a ^ (a >> 27)) * C2); rdx = a ^ (a >> 31);
        rcx = ((rdx ^ (rdx >> 30)) * C1); rax = rcx >> 27; rax ^= rcx; rax *= C2;
        r12v = rax ^ (rax >> 31); r12d = (u32)r12v; r12d = (r12d & 0xfffffe) | 1;
    }
    u64 r12 = r12d; rax = (Y << 24); r12 = (r12 | rax);
    rcx = (f2r >> 30) ^ f2r; u64 rax2 = (rax >> 30) ^ r12;
    rcx *= C1; rax2 *= C1; rcx ^= rcx >> 27; rax2 ^= rax2 >> 27;
    rcx *= C2; u64 rdxx = f1r * M3; rax2 *= C2;
    rdxx = rdxx ^ rcx ^ (rcx >> 31) ^ ctr ^ state ^ rax2; rax2 = (rax2 >> 31) ^ rdxx;
    u64 r12b = rax2; r12b = (r12b ^ (r12b >> 30)) * C1; r12b = (r12b ^ (r12b >> 27)) * C2;
    u64 r15 = r12b >> 31;
    rax = ((u64)r12d << 24); u64 rsi = (Y | rax);
    rcx = (f2r >> 30) ^ f2r; u64 rax3 = (rax >> 30) ^ rsi;
    rcx *= C1; rax3 *= C1; rcx ^= rcx >> 27; rax3 ^= rax3 >> 27;
    rcx *= C2; rdxx = f1r * M3; rax3 *= C2;
    rdxx = rdxx ^ rcx ^ (rcx >> 31) ^ ctr ^ rax3; rax3 = (rax3 >> 31) ^ rdxx;
    rax3 = rax3 ^ r12b ^ r15;
    return mix(rax3);
}

static unsigned char *read_file(const char *path, long *len) {
    FILE *f = fopen(path, "rb");
    if (!f) { perror(path); exit(1); }
    fseek(f, 0, SEEK_END); *len = ftell(f); fseek(f, 0, SEEK_SET);
    unsigned char *buf = malloc(*len);
    if (fread(buf, 1, *len, f) != (size_t)*len) { perror(path); exit(1); }
    fclose(f);
    return buf;
}

int main(int argc, char **argv) {
    if (argc != 4) { fprintf(stderr, "usage: %s part.pmaf in.rgb32 out.rgb32\n", argv[0]); return 2; }

    /* ---- header: "PMAF\3\r\n\x1a" | W u32 | H u32 | NP u64 | seed u64 | diff u32 | 0 u32 */
    long flen; unsigned char *d = read_file(argv[1], &flen);
    if (memcmp(d, "PMAF\x03\r\n\x1a", 8) != 0) { fprintf(stderr, "bad magic\n"); return 1; }
    W = *(u32 *)(d + 8); H = *(u32 *)(d + 12);
    u64 NP = *(u64 *)(d + 16), seed = *(u64 *)(d + 24);
    u64 diff = *(u32 *)(d + 32);
    N = (long)W * H;
    const unsigned char *ops = d + 40;

    /* initial state, exactly as computed in main() before the op loop */
    u64 state = mix(mix(NP) ^ seed ^ (u64)H ^ ((u64)W << 32) ^ (diff * M3) ^ S0_SALT);

    long clen; u32 *canvas = (u32 *)read_file(argv[2], &clen);
    if (clen != N * 4) { fprintf(stderr, "canvas size mismatch\n"); return 1; }

    parent = malloc(N * sizeof(int)); rsize = malloc(N * sizeof(long));
    rhash = malloc(N * sizeof(u64)); rcolor = malloc(N * sizeof(u32));
    adj = calloc(N, sizeof(int *)); adj_n = calloc(N, sizeof(int));
    adj_cap = calloc(N, sizeof(int)); seen = calloc(N, sizeof(int));

    /* build initial regions (4-connectivity, equal colour) */
    for (long i = 0; i < N; i++) {
        parent[i] = (int)i; rsize[i] = 1; rhash[i] = mix((u64)i ^ PIXEL_KEY); rcolor[i] = canvas[i];
    }
    for (long i = 0; i < N; i++) {
        int c = (int)(i % W); long r = i / W;
        if (c < W - 1 && canvas[i] == canvas[i + 1]) unite((int)i, (int)i + 1);
        if (r < H - 1 && canvas[i] == canvas[i + W]) unite((int)i, (int)(i + W));
    }
    for (long i = 0; i < N; i++) {
        int c = (int)(i % W); long r = i / W;
        if (c < W - 1 && canvas[i] != canvas[i + 1]) {
            int a = find((int)i), b = find((int)i + 1); adj_push(a, b); adj_push(b, a);
        }
        if (r < H - 1 && canvas[i] != canvas[i + W]) {
            int a = find((int)i), b = find((int)(i + W)); adj_push(a, b); adj_push(b, a);
        }
    }

    long bad_tags = 0;
    for (u64 n = 0; n < NP; n++) {
        u64 ctr = n * GAMMA, op;
        memcpy(&op, ops + n * 8, 8);
        u64 V = mix(ctr ^ state) ^ op;               /* decrypt the op            */
        int X = (int)(V & 0xffffff);                 /* target pixel              */
        u64 Y = (V >> 24) & 0xffffff;                /* new colour                */
        u64 tag = V >> 48;                           /* 16-bit integrity tag      */
        if ((mix(((Y << 24) | (u64)X) ^ ctr ^ state) >> 48) != tag || X >= N) bad_tags++;

        int r = find(X);
        u32 old = rcolor[r];
        u64 f1 = 0, f2 = 0;
        if (old != (u32)Y) { f1 = (u64)rsize[r]; f2 = rhash[r]; rcolor[r] = (u32)Y; }

        /* the recoloured region merges with every neighbour already painted Y */
        int changed = 1;
        while (changed) {
            changed = 0; r = find(r);
            int w = 0, cnt = adj_n[r], *al = adj[r];
            for (int i = 0; i < cnt; i++) {
                int nb = find(al[i]);
                if (nb == r || seen[nb] == epoch) continue;
                seen[nb] = epoch;
                if (rcolor[nb] == (u32)Y) { r = unite(r, nb); changed = 1; epoch++; goto next_pass; }
                al[w++] = nb;
            }
            adj_n[r] = w; epoch++;
        next_pass:;
        }

        state = update_main(state, ctr, Y, f1, f2, old);
        u64 r14 = DECOY_R14;
        for (u64 i = 0; i < diff; i++) {
            state = decoy_round(state, ctr, Y, (u64)rsize[r], rhash[r], r14);
            r14 += M3;
        }
    }

    for (long i = 0; i < N; i++) canvas[i] = rcolor[find((int)i)];
    FILE *o = fopen(argv[3], "wb");
    fwrite(canvas, 4, N, o); fclose(o);
    fprintf(stderr, "ops=%llu bad_tags=%ld\n", (unsigned long long)NP, bad_tags);
    return bad_tags ? 1 : 0;
}
