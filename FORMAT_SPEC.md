# AccuMark native piece file — byte-level format spec

Reverse-engineered from the eight-piece controlled export set in `PDS.zip`
(AccuMark V17.1.0, Windows). Every statement marked **[V]** is validated
against the paired ASTM/D6673 DXF export of the same piece; statements marked
**[?]** are consistent with all eight samples but not yet pinned down.

## 0. Container

A PDS "ZIP files (*.zip)" export is an ordinary ZIP holding two members:

| member | content |
|---|---|
| `a<4 hex>.tmp` | the piece record stream (this document) |
| `ver.5` | zero-length; storage-area version marker |

All multi-byte integers are **little-endian**. Coordinates are **signed
int32 in units of 1e-4 inch** (10 000 units/inch) **[V]** — confirmed to the
last digit on all eight pieces against DXF `Units: ENGLISH` coordinates
(max residual 1e-4 in = 0.0025 mm, i.e. DXF print rounding).

## 1. File header (0x00–0x87)

| offset | size | field |
|---|---|---|
| 0x00 | 18 | ASCII magic `XGGT IXPORT DB5.1\0` **[V]** |
| 0x12 | 3 | uninitialised **[?]** |
| 0x15 | var | exported **piece name**, NUL-terminated **[V]** — written into a fixed-width slot: the 21-character `CAP-C02-SAVEAS-NOEDIT` produced a file of exactly the same length as the 12-character `CAP-C00-BASE`, overwriting residue bytes instead of shifting anything (the trailer copy of the name behaves the same way) **[V]** |
| … | … | uninitialised heap/stack residue: 64-bit pointer-shaped values (`…7f 00 00`) that differ between two otherwise byte-identical exports **[V]** |

**Export-to-export noise floor [V]** (round 2, `CAP-C00-BASE` vs `CAP-C01-REEXPORT`):
two exports of the same unmodified, un-re-saved piece, two minutes apart, differ
in exactly **one 3-byte run at 0x48–0x4A** (`50 f8 5c` → `10 2c 5d`, the low
bytes of a pointer-shaped value). Nothing else — no timestamp change, no
coordinate change. Any other differing byte between a baseline and its variant
is therefore attributable to the edit (or to a re-save, see §7).

The header carries the *export* piece name. The name inside the piece record
(§2) is the piece's **category / original name**, which differs whenever the
piece was produced by Copy-Piece → Paste-Piece: all six rectangles carry
`TASK1-CUTQTY3` there, matching `CATEGORY:` in the DXF **[V]**.

## 2. Piece record

A file contains **one or more** piece records (§8). Each begins with a
22-byte field block whose string lengths are given in a different order from
the strings themselves:

| offset | type | field |
|---|---|---|
| +0x00 | u16 | `len(name)` |
| +0x02 | u16 | `len(annotation)` |
| +0x04 | u16 | 0 in every non-mirror sample; **2** on `CAP-C61-MIRROR` (round 2) — the only capture made with the "Fold Keep" tool (internal fold line + Mirror Piece checkbox). Previously mis-modeled as the high 16 bits of a u32 `len(annotation)` (harmless while always 0). Likely a mirror/flip flag or a count of mirror-related sub-records; meaning **[?]** unconfirmed pending a second Fold Keep sample |
| +0x06 | u32 | `len(size)` |
| +0x0A | u32 | `len(rule_table)` |
| +0x0E | u32 | `n_perimeter` — perimeter point records **including** the closing record **[V]** |
| +0x12 | u16 | 1 in all samples **[?]** |
| +0x14 | u16 | `len(sample_size)` |

then the concatenated, unterminated strings in this order **[V]**:
`name`, `annotation`, `rule_table`, `size`, `sample_size`
(e.g. `TASK6-CURVE` `CIRCLE` `TASK6-RULES` `8` `8`).

### 2.1 Size list

| offset | type | field |
|---|---|---|
| +0 | u32 | 0 (reserved) |
| +4 | u16 | `n_sizes` **[V]** |
| +6 | u16 | `n_break_rows - 1` — the number of size-break rows in the rule table minus one (A1-LADIES 7 sizes/6 rows → 5; TASK5/TASK6 9 sizes/5 rows → 4; CAP-RULES-A 9 sizes/8 rows → 7). Sets the object-record stride in §3 **[V]** (`CAP-C20-RULE-DISTINCT`) |
| +8 | u16 | `base_size_index` (0-based into the size list) **[V]** |
| +10 | u16 | `0x0200` in all samples **[?]** |
| +12 | u16 | `n_object_records` (§3) **[V]** |

followed by `n_sizes` entries of `u16 len, u16 flag, char name[len]`. The
flag is 1 for a contiguous interior run of sizes and 0 elsewhere; it is not
explained by base size, first/last position, or the rule-table size breaks
**[?]**.

## 3. Object records — grade rules, `n_object_records` × (8 + 8·n_rows) bytes **[V]**

Resolved by `CAP-C20-RULE-DISTINCT` (round 2), whose rule 1 has a different
X and Y in every one of its eight size-break rows:

```
i32 id            rule number for an embedded rule (1 in TASK5 and C20);
                  10001, 10002, … for the placeholder records (see below)
i32 0             reserved
n_rows × { i32 dx, i32 dy }   per-size-break increment of the rule, in
                  1e-4 inch, truncated toward zero, smallest break first
```

`n_rows` is the rule table's number of size-break rows, stored as
`n_rows - 1` in the size-list u16 at +6 (§2.1). Round 1's tables all had
five rows (breaks 10…18), so every record was 8 + 40 = 48 bytes and looked
like "11 payload slots"; C20's eight-row table gives 72-byte records.

C20's record 1 reads `0 | 393,-196 | 787,-393 | 1181,-590 | 1574,-787 |
1968,-984 | 2362,-1181 | 2755,-1377 | 3149,-1574` — exactly the entered
0.10/-0.05 … 0.80/-0.40 cm rows (0.10 cm = 393.7 → 393; -0.05 cm =
-196.85 → -196). TASK5's `[0, 3937 ×10]` is the same layout with 1.00 cm in
both X and Y of all five rows. The `.RUL` companion lists the *cumulative*
per-size deltas in inches; the binary stores the *per-row increments*.

Every rule that a point references is embedded under its own rule number
with its values **[V]**: `CAP-C21-RULE-TWO` (rule 1 on point 4, rule 2 on
point 1) carries `id=1` with the distinct rows, `id=2` with `(3937, 0)` in all
eight rows (X = 1.00 cm, Y = 0), then the all-zero `10001` record that every
file has. Records appear in rule-number order and `n_object_records` (§2.1)
counts them (2 → 3 from C20 to C21). `TASK6-CURVE` is the odd one out: its
points reference `10002…10011` and all ten of those records are zero — the
round-1 session may have typed rule numbers that did not resolve; treat that
file as anomalous rather than as the model.

Each graded point also adds a ~50-byte structure to the tail section (§10),
`00 | 05 00 | 04 0a | <u32 rule> | <u32 rule> | 00 00 | 0f 0a ff ff 00 00 ff ff …`
— C20 gained one such block (rule 1) at 0x436/0x46e, C21 a second (rule 2)
**[?]** (purpose unresolved; the two copies per point are in record 0 and the
pre-edit record 1).

On the six pieces whose rule table has 7 sizes, the object array is followed
by 8 zero bytes before the point table; on the two 9-size pieces it is not
**[?]**. The decoder locates the point table by scan, not by arithmetic.

## 4. Perimeter point table — `n_perimeter` records

Variable length; two optional fields:

```
i16 id            sequential 1..n for turn/curve points; 0xFFFF (-1) for
                  unnumbered points (notches, interior points, closing)
i32 x, i32 y      1e-4 inch
u16 f1            0x0000 -> explicit grade-rule reference follows
                  0x0001 -> ordinary point with NO grade rule [V]
                            (CAP-C22-RULE-NONE: table assigned, nothing
                            applied -> all four points f1 = 1, no refs, no
                            embedded rule record; TASK5's "# 1" DXF texts on
                            its f1 = 1 points were DXF noise)
                  0x0002 -> closing record (repeats point 1)
                  (id==-1, low byte 1, high byte N) -> notch of PDS
                            "Notch Type" N (1..30); high byte is the type
                            number, NOT a bit flag (see below)
u16 f2            trailer BYTE COUNT, not a 0/1 flag [V] (round 2,
                            CAP-C62-DART) - every sample before the dart
                            capture only ever had f2 in {0,1}, making it
                            indistinguishable from a boolean until a dart
                            leg point turned up with f2 == 2 (two trailer
                            bytes). Reading it as a count is backward
                            compatible: f2 == 1 still reads exactly one byte.
i32 rule_ref      iff f1 == 0   -> object-record id (§3)
u16 rule_pad      iff f1 == 0   -> 0 in all samples
u8[f2] attr_bytes iff f2 >= 1   -> first byte: 0x09 turn point, 0x0A curve
                            point, 0x12 dart apex point [V] (CAP-C62-DART);
                            second byte (f2 == 2 only): differs between a
                            dart's two leg points (`09 10` / `09 11` seen on
                            one dart) - [?] pairing/index, unconfirmed
```

Record length is therefore 14, 15, 20 or 21 bytes. All 82 point records
across the eight files parse to exactly `n_perimeter` records terminating on
a valid `f1 == 2` closing record **[V]**.

**Exception — `CAP-C61-MIRROR` (round 2):** metadata's `n_perimeter` reads 4
for what the DXF confirms is a true 4-corner rectangle, but only **3**
explicit point records exist before the file transitions straight into the
internal-line list (§5) — no `f1 == 2` closing record, no 4th corner point of
any kind. The decoder now stops the point run defensively the moment it sees
an internal-line header where a point was expected, rather than trusting
`n_perimeter` blindly (this is safe: a genuine point can never produce a
false-positive match against an internal-line header, since notches — the
only other `id ∈ {0, -1}` point kind — use `f1` values that can't collide
with the grain/drill/cutout tag bytes). With that fix the remaining 3 points
match the DXF to 0.0 in. Leading theory **[?]**: the 4th corner of a mirrored
piece is implied by reflection across the internal fold line rather than stored
explicitly, and `n_perimeter` counts the *logical* corner count rather than
the *stored* record count — unconfirmed pending a second Fold Keep sample.

**Darts are cut directly into the perimeter, not stored as an internal line
[V]** (round 2, `CAP-C62-DART`): Advanced tab → Darts → Add on a plain
rectangle (opening point on the bottom edge, apex point above it, 2 cm
width) added **3** new perimeter points between the two bottom corners - a
dart-leg point (`id -1`, `f1 1`, `f2 2`), the apex (`id -1`, `f1 1`, `f2 1`,
`attr 0x12`), and a second dart-leg point (`f2 2` again) - taking a plain
4-corner rectangle to 7 perimeter points. This is also what first exposed
`f2` as a byte count rather than a flag (above): the two dart-leg points'
`f2 == 2` was silently misread as `f2 == 1` (one trailer byte instead of
two), which desynced every point read afterward into garbage coordinates -
`accumark_pds.py`'s `summarize()` additionally hung for minutes on a
false-positive metadata match this misalignment produced deeper in the file
(a brute-force offset scan with no bound on the resulting `n_object_records`/
`n_perimeter`, now guarded in `parse_object_records` and
`decode_piece_block`'s internal-line reader).

**Notches** are extra perimeter vertices with `id = -1` and `f1` low byte
`0x01`, inserted in sequence between the two numbered points of the side
they sit on **[V]** — `TASK3-NOTCHED` decodes two notches at +2.1067 in and
+6.0113 in along the left edge, matching DXF layer 4 to 1e-4 in.

**Notch Type is the high byte of `f1`, not a bit flag [V]** (round 2,
`CAP-C40-NOTCH-TYPES`): four notches placed via PDS's "Add Standard Notch"
panel with **Notch: Type:** set to 1, 2, 4 and 8 in the UI decoded to
`f1 = 0x0101, 0x0201, 0x0401, 0x0501` — i.e. `f1 = (type << 8) | 0x01`. All
of round 1's captures only ever used the default Type 1 (`f1 = 0x0101`),
which is why the high byte's role as a bit-8 flag looked plausible from that
data alone: type 1's high byte (`0b00000001`) has bit 0 set, so a "bit 8 of
f1" check happens to fire for every *odd* type number but silently misses
even ones (2, 4, 6, …) — the decoder used exactly that wrong check until
this capture exposed it. The corrected rule: a perimeter point is a notch
iff `id == -1`, `f1 & 0xFF == 1`, and `f1 >> 8 != 0` (the last clause
excludes plain unnumbered points such as grain-line/drill endpoints, whose
`f1 = 0x0001` with a zero high byte). No width, depth, or angle value is
visible elsewhere in the record — whether those are stored at all, and
where, is `CAP-C41-NOTCH-WIDTH`'s question.

**Notch Depth is not stored anywhere in the piece file [V]** (round 2,
`CAP-C41-NOTCH-WIDTH`): the "Add Standard Notch" panel's **Depth:** field is
not a user-editable control — the UI accessibility tree exposes a `Combo Box`
for **Type:** but no `Edit` control for **Depth:**; typing into its screen
coordinates has no effect and the displayed value only ever changes as a
side effect of picking a different Type. Depth is therefore fixed per Type,
looked up from a system-wide notch-shape table, not settable per placement.
Two notches were placed on the same rectangle with the same Type (1, default
Depth 0.40) at different positions to test whether the record differs beyond
(x, y); the decoded records are

```
id=-1 x=134833 y=110570 f1=257 f2=0   (14 bytes)
id=-1 x=107086 y=110570 f1=257 f2=0   (14 bytes)
```

byte-identical apart from `x`. Since a notch record is exactly 14 bytes with
no spare field, and Type (which fully determines Depth in the UI) is already
known to live in `f1`'s high byte, Depth is not persisted per-instance at
all — like round 1's cut quantity, it is a UI/reference value resolved from
Type at render or cut time, not part of the geometry record.

**Notch-to-edge (L-line) assignment confirmed on all four edges [V]** (round
2, `CAP-C42-NOTCH-ALLEDGES`): one Type-1 notch placed per edge of a fresh
rectangle decodes to `perimeter_points=8` (4 numbered corners + 4 unnumbered
notches), `segment_points=3;3;3;3` — each edge's L-line attribute record
(§5.2/L-labels) counts exactly 3 points (its 2 corners plus the one notch
inserted between them), matching the DXF's own `L1 polyline points=[3, 3, 3,
3]` independently. This fixed a real bug in `verify_capture.py`'s `facts()`:
it sliced `s['segments']` (one L-line record **per edge, concatenated across
every piece block in the file** — current block first, any stale pre-edit
block(s) after) by `len(b0['perimeter'])`, i.e. by perimeter *point* count.
That happened to work when every point was numbered (no notches, so
points == edges) but silently pulled in the *next* piece block's stale
L-line records once notches made points > edges (this piece's stale block 1
predates the notches and has `n_points=2` on every edge, which is exactly
what leaked into the tail of the reported list). Fixed to slice by the count
of *numbered* perimeter points (`id != -1`), which equals the true edge
count regardless of how many notches are on the piece.

**The `attr` byte marks a segment start point** — for `TASK6-CURVE` the four
`attr = 0x0A` points fall at perimeter indices 0, 9, 18, 25, exactly the
cumulative boundaries implied by the segment point counts 10/10/8/10 **[V]**.

## 5. Internal-line lists

After the closing record: `u16 0x0000`, `u16 0x0047`, `u16 count`,
`u32 0x0001`, then `count` point records in the §4 layout. Every piece has
one such list of two points: the **grain line**. It is horizontal at
mid-height of the bounding box and spans the middle half of the bounding-box
width — inset `width/4` from each vertical edge, i.e. 2.9510 in on the
11.8039 in rectangles and 3.8454 in on the 15.3818 in circle. Verified on all
eight pieces as fractions of the bounding box (length/width = 0.5000,
height fraction = 0.5000) rather than as a fixed inset **[V]**.

### 5.1 Interior / drill points **[V]** (round 2, `CAP-C50-DRILL1`)

A drill point is a second internal list, directly after the grain-line list,
with header `u16 0xFFFF, u16 0x0044, u16 count, u32 0x0001` (grain line:
`0x0000, 0x0047, …`), followed by `count` 14-byte point records in the §4
layout (`id = -1, f1 = 1, f2 = 0`) and a `u32 0x00000003` terminator plus
zero padding. The point's (x, y) is in the same piece-local frame as the
perimeter: `CAP-C50-DRILL1` stores (82826, 16566) = (8.2826, 1.6566) in,
matching the DXF layer-13 `POINT` to 1e-4 in relative to the outline. In the
ASTM DXF a drill point is a `POINT` + `TEXT` pair on layer 13.

With name-termination (§6) the grain line is `L04` and the drill-point list is
`L08` on a 4-point piece; the segment records that follow are `L00…L03`. The
two counters at +0x260 (6→7) and +0x31e (5→6) in the tail section each
increased by one when the drill list was added **[?]** — candidate "number of
line records" fields.

### 5.2 Internal cut-out **[V]** (round 2, `CAP-C60-CUTOUT`)

A circle drawn with Create→Circles→Center **and "Create New Piece"
unchecked** (checked by default — leaving it checked spawns an independent
second piece instead of an internal feature of the current one, which is
presumably what a genuine two-piece-per-file export like `CAP-C63-MODEL`
relies on) becomes a third kind of internal list, using header
`u16 0xFFFF, u16 0x0049, u16 count, u32 0x0001` — same shape as grain
(`0x0000/0x0047`) and drill (`0xFFFF/0x0044`), new tag `0x0049`. `count` is
the number of points PDS tessellated the circle into (25 for the ~1.7 in
circle in this capture — not a fixed value; presumably scales with radius or
a global curve-fitting tolerance, unconfirmed). Each point is a plain
14-byte record (`id = -1, f1 = 1, f2 = 0`), and the list is **explicitly
closed**: the last point's (x, y) is byte-identical to the first, unlike the
open grain/drill lists. The list's terminator is `u32 0x00000006`, not the
`0x00000003` grain and drill use **[?]** — one sample only, but consistent
with 3 meaning "open list" and 6 "closed loop"; `_internal_list_label` in
`accumark_pds.py` now accepts either value when hunting for the trailing
`Lnn` label. The main perimeter is completely unaffected (still the plain
4-point rectangle) — a cut-out is purely additive internal geometry, not a
perimeter modification, so it does not show up as a notch, drill point, or
seam change.

The ASTM DXF represents the same circle **twice**, at two different
tessellation resolutions: layer 8 has 25 points (matching the binary list's
`count` exactly) and layer 85 has 49 points (roughly double, presumably a
finer display/smoothing curve) — both polylines share their first vertex and
trace the same circle. `verify_capture.py`'s `dxf_check()` only reads
layers `1`/`14` (the cut/sew perimeter), so it never touches either cut-out
layer; the binary-vs-DXF residual check for this capture is validating the
rectangle only, not the circle. `facts()`'s new `cutout_points` field (count
per internal cut-out list, semicolon-joined if more than one) reads straight
off `summarize()`'s `cutouts_in`.

## 6. Line records — name-*terminated*

The 3-byte ASCII label `L%02d` follows the field group it names, so the label
preceding a group belongs to the *previous* record. Attribute-record fields:

```
u16 0x0004, u16 0x000E, u16 n_lines   (first record of the group only)
u16 n_points_on_line
u16 seam_flag            1 -> seam-allowance pair follows
u16 c (=1), u16 d (=0)
i32 seam_begin, i32 seam_end          iff seam_flag == 1   (1e-4 inch)
6 zero bytes                          iff seam_flag == 1
u32 0x00000003                        terminator, then zero padding
```

With name-termination, the four perimeter segments decode as `L00…L03` with
point counts that match the DXF layer-1 polylines **on every piece** —
`2;2;2;2` for the plain rectangles, `4;2;2;2` for the notched one (the
notched edge), `10;10;8;10` for the circle **[V]**.

### 6.1 Seam allowance

Seam allowance is **not** stored as an offset outline on the perimeter. It is
a per-segment `(begin, end)` int32 pair inside the segment attribute record.
`TASK2-SEAM1CM` yields `(3937, 3937)` on all four segments = 0.3937 in =
**1.00 cm**; every other piece has `seam_flag = 0` **[V]**.

**`begin` / `end` semantics [V]** (round 2, `CAP-C30-SEAM-UNEVEN`, Manual –
Uneven with corner values 1.0 / 0.5 / 0.25 cm and one corner left at 0):
`seam_begin` is the allowance at the segment's first perimeter point and
`seam_end` the allowance at its last point, with a **linear taper** between
them. The three seamed segments read `(0, 3937)`, `(0, 1969)`, `(0, 984)` and
the derived cut line for the first runs from (3938, 1) to (4, 78749) — 0 at
the bottom corner, 1 cm at the top corner. A segment whose two ends are both
0 has `seam_flag = 0` and **no** cut-line record (only 3 `line_geometry`
records on that piece), i.e. zero allowance clears the flag rather than
writing an explicit 0. Values are 1e-4 in (0.25 cm = 984, 0.5 cm = 1969).
In the PDS tool a value entered at a corner sets the `end` of the segment
that *ends* there and leaves the next segment's `begin` at 0.

Two side effects of a seam on the rest of the file **[V]** (`CAP-C31-SEAM-TAPER`
vs `CAP-C00-BASE`, same piece, same position): record 0 is re-normalised so
that the **cut** outline's minimum is at the origin — the sew-line perimeter of
C31 starts at x = 1969 (its top-left corner carries 0.5 cm) — and the ASTM DXF
writes layer-14 (sew-line) polylines **only for the seamed edges**; unseamed
edges appear on layer 1 alone. The cut-line records that follow the grain line
are labelled `L08`, `L09`, `L10`, `L11` in order (`L04` names the grain line;
`L05`–`L07` have never been seen and appear to be reserved slots).

**Label numbering is per-segment-creation-order, not final perimeter order [V]**
(round 2, `CAP-C10-PENT`): a 5-sided piece made by splitting one edge of a
rectangle and dragging the new vertex out labels its perimeter segments
`L00, L01, L06, L02, L03` — a jump to `L06` between the 2nd and 3rd segment.
The piece's stale pre-edit duplicate (record 1, still the original rectangle)
labels its four segments plainly `L00…L03`. So the label a segment gets
depends on *when* PDS created that line record internally (the split
operation evidently allocated slot 6 for one of the two new half-segments),
not its position walking the perimeter — the same kind of jump the capture
plan flagged from round 1 (`L04, L08…L11`).

The derived **cut line** *is* stored, as four separate line records carrying
two explicit point records each, prefixed
`<label> FE FF 53 00 02 00 01 00 <u16> <u16>`. Decoded, they reproduce DXF
layer 1 of the seamed piece exactly (0.0000 in residual; 12.5913 × 8.6688 in
= sew 11.8039 × 7.8814 + 2 × 0.3937) **[V]**. In an ASTM DXF of a seamed
piece, layer 1 = cut line and layer 14 = sew line **[V]**.

## 7. Trailer

Piece name repeated, then a **`u32` Unix-epoch timestamp written twice**
(`TASK1` = 1788729478 = 2026-09-06 21:17:58 UTC). The eight values are
strictly monotonic in export order and sit a roughly constant ≈5 h 33 m
before each ZIP member's mtime **[V]**; the residual drift of ±2 min between
files means this is the piece's own *last-saved* time rather than the export
time **[V]** — confirmed by `CAP-C01-REEXPORT`: re-exporting `CAP-C00-BASE`
two minutes later without a Save produced byte-identical timestamps. Files with two piece records can carry two distinct
timestamps (`TASK5-GRADED`). Then `MSI` marker strings and zero padding.

## 8. Multiple piece records per file

`TASK1-CUTQTY3` and `TASK2-NOSEAM` contain one piece record; the other six
contain two. The second record is a **stale duplicate**: byte-identical
across `TASK3-NONOTCH`, `TASK3-NOTCHED` and `TASK4-DRILLPOINT`, always at
storage position (23.3994, 13.2026) in, and never carrying the edit that
distinguishes its file (no notches, no seam, no grade refs) **[V]**. Decode
record 0 and ignore the rest.

Round 2 refines the trigger: `CAP-C00-BASE` (fresh rectangle, Save As, never
pasted) has **one** record; `CAP-C50-DRILL1` — the same piece with a drill point
added and Save-As'd under a new name, still never pasted — has **two**. The
second record is the pre-edit geometry (no drill list) at the piece's
**work-area position** (−7.26, 1.2882) in, while record 0 sits at the origin;
the ASTM DXF is written in that work-area frame. So the duplicate is produced
by editing, not by Save-As and not by Copy/Paste as such **[V]**:
`CAP-C02-SAVEAS-NOEDIT` (re-opened C00, dropped on the canvas, Save-As'd under
a new name, never edited) has **one** record and differs from C00 only in
name, heap residue and timestamps, while every piece that was modified after
its first save (`CAP-C50-DRILL1`, `CAP-C30-SEAM-UNEVEN`, `CAP-C31-SEAM-TAPER`)
has two. Record 1 holds the pre-edit geometry — the likely backing store of
PDS's *Bookmark → Restore Original*.

**A genuine two-piece "Model" export is a different, much smaller file
format entirely — not two piece blocks in one `.tmp` [V]** (round 2,
`CAP-C63-MODEL`): two independently-created rectangles were both checked
"Add Piece to Model" under the same new model name, then exported via
File → Export → **Export Models** (as opposed to the normal **Export
Pieces**) to a ZIP. That ZIP's single `.tmp` member is only **621 bytes**
(a single ordinary rectangle piece file is 1500+) and starts with the usual
`XGGT IXPORT DB5.1` magic and the *model's* name, not either piece's name —
but `decode()` finds **zero** valid piece blocks in it: none of the
per-piece metadata (annotation, rule table, size, perimeter point count)
this format's decoder is built on is present. This is a lightweight
model-level manifest/reference format, structurally unrelated to the
per-piece export format the rest of this document describes; it does not
embed full piece geometry for either piece. Each piece's own geometry stays
in its individual stored record in the storage area (`DATA90`), addressed
by name — the model file just groups the names. Exporting the same two
pieces via ordinary **Export Pieces** instead only accepts one piece
selection at a time in this dialog, so it was not tested further; the
Model-export path already answers the capture's question. **The "one file
holds two genuine pieces" scenario does not occur via either export path
tried** — multi-piece grouping is a manifest-level concept, and the
already-documented stale-duplicate-record case above remains the only way
two piece blocks appear inside one piece `.tmp`.

**Copy-Piece/Paste-Piece confirmed directly, not just inferred [V]** (round
2, `CAP-C70-PASTED`): opened `CAP-C00-BASE` fresh from storage, Create →
Piece → **Copy** with **Category: Copy Original** selected, clicked to place
the pasted copy (named `CAP-C70-PASTED` at the piece-name prompt), then
File → Save As → `CAP-C70-PASTED`, export ASTM + ZIP — no edit at any point
after the paste. Result: **`category = CAP-C00-BASE`** (the *original*
piece's name, not the pasted copy's own name — direct confirmation of the
category field's semantics from §1, this time deliberately rather than
inferred from six accidental instances) and **`piece_records = 1`**, not 2.
This sharpens rather than contradicts the trigger rule two sections above:
Copy-Piece/Paste-Piece by itself is just another way to reach the same
"opened, placed, saved under a new name, never edited" state as
`CAP-C02-SAVEAS-NOEDIT` — the stale second record still requires an edit
*after* that point, and pasting a piece is not itself an edit.

## 9. `.RUL` companion — fully readable

`.RUL` is **plain ASCII** (ASTM/D13 Proposal 1, D 6673-04): `AUTHOR`,
`PRODUCT`, `VERSION`, `CREATION DATE/TIME`, `UNITS`, `GRADE RULE TABLE`,
`NUMBER OF SIZES`, `SIZE LIST`, `SAMPLE SIZE`, then one
`RULE: DELTA <n>` block per rule listing **cumulative** (X, Y) deltas per
size in inches, then `END`. No binary decoding required.
