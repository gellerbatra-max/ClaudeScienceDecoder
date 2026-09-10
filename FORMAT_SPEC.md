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
| 0x15 | var | exported **piece name**, NUL-terminated **[V]** — written into a fixed-width slot: the 21-character `CAP-C02-SAVEAS-NOEDIT` produced a file of exactly the same length as the 12-character `CAP-C00-BASE`, overwriting residue bytes instead of shifting anything (the trailer copy of the name behaves the same way) **[V]**. Confirmed at 30 characters too (round 2, `CAP-C13-LONGNAME-1234567890ABC`): `_find_field_block`'s metadata offset (0x8a) is byte-identical to `CAP-C00-BASE`'s, so the header slot absorbed 18 more name characters with zero shift downstream. The *only* size growth between the two files (1560 vs 1542 bytes, +18) is the piece record's own `len(name)`-prefixed name string (§2) growing by the same 18 bytes - confirming, with a single clean sample rather than by inference, that the header name is fixed-width/slot-based while the piece-record name is genuinely length-prefixed and variable **[V]** |
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

**`annotation` is a literal, tool-derived piece-type string, not a
freeform description [V]** (round 2, `CAP-C14-ANNOT`): every capture so far
used Create→Rectangle and read `RECTANGLE`; a piece made with
Create→Piece→**Collar** instead reads **`collar`** — lowercase, unlike
`RECTANGLE`'s uppercase, confirming these are literal per-tool strings
(not a normalized/cased category enum) and that the field is genuinely
length-prefixed text rather than a fixed set of flag values. No dedicated
UI field edits this string directly; it's set by which Piece-group tool
(Rectangle, Collar, Facing, Sleeve, Skirt, Fusible, Binding, …) created the
piece.

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

**Correction (2026-09-09, production pieces):** two rules above were
artefacts of the eight captures, not the format. (a) The perimeter's first
record can carry **any** creation-order id (13, 2, 7 … on the 2303 wing
pieces; **5** on `CAP-C61-MIRROR`) — `find_point_table` used to scan for
id 1/−1 and so skipped real leading points. (b) The `rule_ref/rule_pad`
group follows whenever `f1`'s **low byte** is 0, not only when `f1 == 0`:
a numbered corner that also carries a notch has `f1 = 0x0N00` (type N in
the high byte, as for unnumbered notches) plus its rule reference. With
both fixes all 162 production pieces of style 2303 (cups, per-size wings,
fold halves; two export vintages) read `n_perimeter − 1` explicit records
plus the closing record, and every piece with a declared area in a marker
matches it to ≤0.06 % (fold halves: exactly 0.500). **The C61 exception
below is therefore withdrawn**: its 4th corner (id 5) was the *first*
record of the table, skipped by the old locator; all four now match the DXF
to 0.000000 in, and the "virtual 4th corner" of §10.2/§11 is simply that
stored point.

**Exception — `CAP-C61-MIRROR` (round 2, superseded above):** metadata's `n_perimeter` reads 4
for what the DXF confirms is a true 4-corner rectangle, but only **3**
explicit point records exist before the file transitions straight into the
internal-line list (§5) — no `f1 == 2` closing record, no 4th corner point of
any kind. The decoder now stops the point run defensively the moment it sees
an internal-line header where a point was expected, rather than trusting
`n_perimeter` blindly (this is safe: a genuine point can never produce a
false-positive match against an internal-line header, since notches — the
only other `id ∈ {0, -1}` point kind — use `f1` values that can't collide
with the grain/drill/cutout tag bytes). With that fix the remaining 3 points
match the DXF to 0.0 in. `n_perimeter` counts the *logical* corner count
(4) rather than the *stored* record count (3) — confirmed, not just
theorised, in round-2 tail-section analysis (§10.2, §11): the missing 4th
corner's exact coordinates turned up as a "virtual" table point in the
line table (§10), computable trivially from the 3 stored corners (this
piece is a right triangle whose two short legs are axis-aligned — see §11
for the numbers). Whether that reflects genuine mirror-fold geometry or
just bounding-box corner completion can't be told apart on an axis-aligned
right triangle; a non-45°, non-axis-aligned Fold Keep sample would settle
it (`CAP-C80-BOOKMARK`-style Phase C capture, not yet done) **[?]**.

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

**Tag `0x0049` is "generic drawn internal line," not "closed cut-out"
specifically [V]** (round 2, `CAP-C12-TWOINTLINES`): a plain open 2-point
internal line (Create→Line→2-Point, drawn free-floating inside the piece,
touching no perimeter point) gets the *same* `0xFFFF/0x0049` header as the
circle above — not a fourth tag. Its terminator is `0x00000003` (open),
confirming with a second, independent sample that **the terminator, not the
tag byte, is what distinguishes an open line from a closed loop** (the "one
sample only" hedge above is resolved). Labels were sequential in this
capture (grain `L04`, the new line `L05`) with no jump — the `L04, L08…L11`
jump documented elsewhere for `CAP-C10-PENT` correlates with editing
*perimeter* points after the piece's first save, not merely with having more
than one internal line; a second internal line added before any perimeter
edit doesn't reproduce it.

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

## 10. Line table (TLV)

The block's final section (previously "the large 847/1852/1312-byte
tag/length/value tail" in earlier notes, and the source of the "~50-byte
per-graded-point block" open item) is a self-describing **tag/length/value
line table**: one record per perimeter edge and per internal line (grain,
drill, cut-out), in Region A's line-creation order, immediately after §11's
two perimeter snapshots. `accumark_pds.parse_line_table()` **[V]** — walked
byte-for-byte across every capture in the corpus with zero manual offset
correction (each record's own fields land exactly on the next record's `0a
00` header) and cross-checked point-by-point against the independently
decoded perimeter/internal-line/closing points (`accumark_pds.
check_line_table()`, wired into `verify_capture.py` as
`line_table_consistent`).

Record header:

```
0a 00  i32 idx  u16 kind  u16 n_points  u16 const(=3)
```

`idx` is 1-based and increases by one per record; `kind` is `1` for a
perimeter edge, `2` for an internal line (grain/drill/cut-out, and see the
cut-line case below). `n_points` is the point count that follows, and the
trailing `const` is `3` in every sample seen so far **[?]**.

Record-level tags, in order, before the points:

```
0b 04  u32                  = idx again (line_idx)
0c 04  u32                  = n_points + 1
0d <len=4*n_points>  u32 × n_points     point ordinals, endpoints first then
                                        interior (e.g. [1,3,2] for a 3-point
                                        edge whose notch sits at ordinal 3)
```

Then `n_points` **table points**. Every field elsewhere in the record is a
conventional `(tag: u8, len: u8, payload[len])` TLV, but the point tag is a
special case: its length byte is always `0x00`, yet it actually carries a
fixed 16-byte struct, itself followed by that point's own child TLVs:

```
10 00  i32 x  i32 y  u16 a  u16 b  u16 c  u16 e
```

`a` is the point's id, using the **same unsigned encoding as `parse_point`'s
signed `id`** — an unnumbered point (notch, grain/drill/cut-out point, or a
plain corner that never got a sequential id, see below) reads `a = 0xFFFF`
here, the same bit pattern as `id == -1` there. `e` is the number of child
TLVs immediately following this point (0 for a plain point). `b`/`c` are
unidentified so far **[?]** (constant across every sample seen).

Per-point child tags, any combination of:

```
06 02  09 <'0'|'1'>          point-name marker; present only on a line's
                             first ('0') or last ('1') point [?] exact role
07 2d  <45 bytes>            notch attribute block - see §10.3
04 0a  u32 rule_id  u32 rule_id  u16 0     graded-point rule reference: the
                             object-record id (§3) repeated twice, i.e. the
                             ~50-byte "per-graded-point tail block" from §3
                             is this tag plus the two 0f-tags below, resolving
                             that open item
0f 0a  <10 bytes>            appears exactly 3× on a graded point,
                             immediately after its 04 0a tag; every sample so
                             far is the placeholder
                             `ff ff 00 00 ff ff 00 00 00 00` - no capture yet
                             has a non-placeholder value here to decode
                             against **[?]**
```

**`04 0a`'s rule-id pairing confirmed exactly [V]** (`CAP-C21-RULE-TWO`,
rule 2 on point 1 / rule 1 on point 4): the line table reads
`rule_ids=(2,2)` on the table-point entries for point 1 and `(1,1)` on
point 4, each appearing twice (once in each of the two edge records that
share that corner) — matching `verify_capture.py`'s independently-decoded
`grade_refs` exactly, with no ambiguity about pairing or order.

**Corners that never got a sequential id [V]** (round 2, `CAP-C10-PENT`,
`CAP-C11-HEX`): a pentagon made by splitting one edge of `CAP-C00-BASE`'s
rectangle decodes perimeter ids `[1, 2, -1, 3, 4]` — the inserted 5th corner
is a plain `attr = 0x09` turn point, not a notch, yet carries `id = -1` the
same way a notch does. A hexagon made the same way (two corners inserted)
decodes `[1, 2, -1, 3, 4, -1]` — always exactly the *original* rectangle's
four corners keep ids 1–4; every corner added afterward stays unnumbered.
This means a kind-1 record's point count is not reliably "2, plus one per
notch on that edge" — it can also include an unnumbered *real* corner, which
is why `check_line_table()` does not require a kind-1 record to have two
numbered endpoints, only that every point coincide with real geometry.

**Curved segments number interior points, not just endpoints [V]**
(`TASK6-CURVE`): the four curve segments (10/10/8/10 points, §4/§6) produce
only **4** kind-1 records — one per Lnn segment, each carrying all of that
segment's points, not one record per numbered point. `TASK6-CURVE` has 10
*numbered* perimeter points (matching `graded_points = 10`), because a grade
rule reference needs a point id to attach to — numbering here tracks which
points carry a rule, not corner/edge count. Point count is one kind-1 record
per Lnn segment (§6), each holding every point — numbered or not — that
segment contains, in perimeter order.

### 10.1 Cut-line records (seam allowance)

A seam-allowanced edge (§6.1) adds one **kind-2** record after the ordinary
perimeter/internal-line records, `n_points = 4`, whose points are not raw
stored geometry: `[mitered corner at this edge's start, plain offset at
start, plain offset at end, mitered corner at end]` **[V]** (`TASK2-SEAM1CM`,
uniform 1 cm seam on all 4 edges → 4 such records; `CAP-C30-SEAM-UNEVEN`,
3 of 4 edges seamed → 3 records). On a **uniform** seam every one of these
points is a real perimeter corner offset by the seam allowance along x, y,
or diagonally (a "plain offset" moves on one axis, a "mitered corner" moves
on both, by the same magnitude) — confirmed to the exact allowance value
(3937 = 1.00 cm) on `TASK2-SEAM1CM`. This duplicates, more completely, the
simpler 2-point-per-edge cut line `parse_line_geometry()` already extracts
from Region A (§6.1's `Lnn FE FF 53 00 …` records) — the line table's
version additionally carries the mitered corner needed to join adjacent
offset segments cleanly.

On an **uneven/tapered** seam (`CAP-C30-SEAM-UNEVEN`, `CAP-C31-SEAM-TAPER`)
most corners turn out to be plain single-edge offsets once matched to the
*correct* adjacent edge, not genuine two-edge miters **[V]** (2026-09-09
re-analysis, no new capture): the PDS rule that "a value entered at a corner
sets the `end` of the segment ending there and leaves the next segment's
`begin` at 0" (§6.1) means a shared corner almost always has exactly one
nonzero contributing edge. `CAP-C30-SEAM-UNEVEN`'s corner at real point 4
(`121977,1`) is a clean example: its incoming edge's `seam_end = 984`
(0.25 cm) reproduces the recorded cut-line point `(122961,1)` exactly
(`+984,+0`), zero residual. The corner at point 3 matches its incoming
edge's `seam_end = 1969` to within 25/1 units (rounding, not a modelling
gap). **One corner remains genuinely unexplained**: the corner at real
point 2 (`3938,78815`), whose incoming edge (`L00`, vertical, `seam_end =
3937`) predicts a plain offset to `(1,78815)`, but the recorded cut-line
point is `(4,78749)` — residual `(dx, dy) = (-3934, -66)` relative to a
*plain-offset* prediction that already accounts for `seam_end`, not merely
relative to the unmoved corner. This is the same numeric example this
document already flagged; re-deriving it did not explain it, only pin down
that it resists both the "plain single-edge offset" model (which works
everywhere else) and a naive two-line intersection (which would give
`(0,78685)`, also not a match). `check_line_table()` recognises only the
uniform case (an offset that is 0 on one axis, or equal in magnitude on
both, within `SEAM_OFFSET_MAX`) and still returns `line_table_consistent =
no` on this file rather than force-fit **[?]**.

### 10.2 The mirror piece's virtual 4th corner — located, not fully explained

`CAP-C61-MIRROR`'s line table references a table point (`a = 5`, at
(461361, 237653)) that matches **none** of the block's 3 real perimeter
points ((429009,237653) id 1, (429009,270071) id 2, (461361,270071) id 6),
its closing point, or its grain line. **[V]**: this point is exactly the
4th corner of the axis-aligned rectangle the other 3 corners already
define — `x` taken from id 6 (the corner with a different x than id 1),
`y` taken from id 1 (the corner with a different y than id 6). Both §4's
metadata `n_perimeter` and §11's pretable `n_perimeter_a/b` count this
piece as having 4 corners, one more than are actually stored, so this
"virtual" table point is where that logical 4th corner's coordinates
finally surface in the file. Left **[?]**: this stored triangle happens to
be a right triangle with axis-aligned legs, so "reflect across the fold
line" and "complete the bounding rectangle" produce the identical answer —
they can't be told apart on this sample, only on a non-axis-aligned Fold
Keep capture (Phase C, not yet done).

### 10.3 Still open

- **The `07 2d` notch-attribute payload, byte-diffed across `CAP-C40-NOTCH-
  TYPES`'s four notches (Types 2, 4, 5, 1 in perimeter order — see §4;
  intended input was 1/2/3/8, so the log already flags that the UI's own
  dropdown mis-selected on at least one of these):
  ```
  byte  0        varies: 02, 04, 05, 01 (one per notch)
  bytes 1-5      00 00 00 00 00           (const)
  byte  6        01                       (const)
  bytes 7-11     00 00 00 00 00           (const)
  byte  12       01                       (const)
  bytes 13-33    00 × 21                  (const)
  bytes 34-35    ff ff                    (const)
  bytes 36-43    00 × 8                   (const)
  byte  44       varies: 02, 04, 08, 01 (one per notch)
  ```
  Only bytes 0 and 44 vary across the four notches; every other byte is
  identical. **Byte 0 exactly matches `f1`'s already-decoded Notch Type
  (§4)** on all four (2, 4, 5, 1). **Byte 44 matches on three of four but
  reads `8` where byte 0/`f1` read `5`.** Since the capture log for this exact
  piece independently records uncertainty about whether the UI's Type
  dropdown (which re-scrolls its list on reopen) actually applied the
  intended selection every time, byte 44 disagreeing with `f1` on exactly
  the one notch is a plausible sign that byte 44 is a *second, independent*
  copy of the Notch Type — possibly the more reliable one — rather than
  noise; not confirmed without a controlled re-capture **[?]**. The `b`/`c`
  fields of the table-point struct remain confirmed presence-only, no
  decoded semantics **[?]**.
- **`0f 0a` triples**: every occurrence in the entire corpus (all graded
  points, all blocks) is the same `ff ff 00 00 ff ff 00 00 00 00`
  placeholder, including `TASK6-CURVE`'s anomalous `10002…10011` rule
  references — ruling that file out as a source of a non-placeholder
  sample. No capture yet has one to decode against **[?]**.

## 11. Pre-table header and geometry snapshots

Between the last `Lnn` line record's own label (Region A, §6) and the line
table (§10) sit two further regions, found positionally (right after the
label) rather than by content search, since the line table's own header
pattern can false-match inside an object-record size list (`TASK6-CURVE`).
`accumark_pds._locate_tail()` re-finds this boundary independently of
`decode_piece_block()`'s own `block_end`, which stops one step short (at the
label's own terminator) for backward compatibility with existing callers.

**Region B — pre-table header, 52 fixed bytes** (`parse_pretable_header()`):

```
u16 0x0032 (const)   u32 1 (const)        u32 n            u32 0x10 (const)
u16 e1 (const=0)     u32 0x10 (const)     u16 e2 (const=0) u32 0x14 (const)
u32 0x1a (const)     u16 n (repeated)     u32 0x1c (const) 12 zero bytes
u32 (n_line_table_records + 1)
```

**`n` is NOT `len(perimeter)` [V]** (round 2, whole-corpus fit): it is the
count of perimeter points that carry an attr byte at all (`f2 >= 1` — §4;
this alone excludes every notch, which always has `f2 == 0`) **and** whose
attr is not `POINT_DART_APEX` (0x12). Verified exactly against every block
in the corpus but one: this single formula resolves three previously
separate open items at once —

- `CAP-C14-ANNOT` (Collar, 5 real perimeter points): one plain corner has
  `f2 == 0` (no attr byte at all, unlike an ordinary corner's `f2 == 1`), so
  `n = 4` — the field was never wrong, the collar tool just leaves one
  corner without an attr byte.
- `CAP-C62-DART` (7 real perimeter points, 4 corners + 2 dart legs + 1
  apex): every point except the apex has an attr byte, and the apex is
  specifically excluded by the `!= POINT_DART_APEX` clause, so `n = 6`.
- `CAP-C40/41/42-NOTCH-*`: notches are excluded by the `f2 >= 1` test
  alone (`n` = numbered-corner count on all three, since none of their
  notches carry an attr byte).
- `CAP-C10-PENT`/`CAP-C11-HEX` (corners added by edge-splitting, §10):
  these *do* carry an ordinary attr byte like any other corner, so they
  count normally — `n = 5`/`6`, matching `len(perimeter)` exactly, which is
  why these two looked like "the field just means total count" before the
  dart/notch/collar samples were fit against the same formula.

**`CAP-C61-MIRROR` is the one exception** (formula predicts 3, file reads
4) — consistent with, not contradicting, the rule: see the missing-4th-
corner discussion above and in §10.2. Both `n_perimeter` fields (here and
in metadata, §2) count the mirror piece's implied corner as if it had an
attr byte like any other, even though no such record exists.

**`e1`/`e2` (u16 at +14/+20) are seam-edge counts, not always-zero
constants [V]**: every non-seam sample reads 0/0 as previously logged, but
on a seam-allowanced piece `e1` is the number of `Lnn` segments with
`seam_flag == 1` (exactly `cutline_records`, §6.1/§10.1) and `e2` is how
many of those are *uneven* (`seam_begin != seam_end`) — `TASK2-SEAM1CM`'s
uniform 1 cm seam on all 4 edges reads `(4, 0)`; `CAP-C30-SEAM-UNEVEN`'s 3
tapered edges read `(3, 3)`; `CAP-C31-SEAM-TAPER`'s 2 tapered edges read
`(2, 2)` — exact matches in every case, not an approximation.

Every other field (`magic`, `one`, and the four `0x10`/`0x14`/`0x1a`/`0x1c`
constants) is a raw invariant in every one of the corpus's ~50 blocks —
confirmed constant, but its *role* (as opposed to its value) is still
unknown **[?]**.

**Region C — two full perimeter re-listings**, each **the same `n` as
Region B above** (i.e. `n_perimeter_a` — corners minus notches/dart-apex,
*not* `len(perimeter)`) consecutive `parse_point`-format "turn" records
(`f1 = 1, f2 = 1, attr = 9` regardless of a point's real kind — notches and
curve points are flattened to plain turn points here, so Region C is a
geometry-only copy, not authoritative for point kind). **[V, corrected
2026-09-11]** these records are **variable width**, not a fixed 15 bytes —
whenever a point's own re-encoded size differs from the common
14-base+1-trailer-byte case, a fixed stride silently misaligns the rest of
the snapshot (`CAP-C62-DART`); read each point's own computed size and
advance by that, the same technique `parse_point_run` already uses for the
primary point table. Using `len(perimeter)` for `n` instead of
`n_perimeter_a` has the same failure mode on any notched/darted/annotated/
curved piece: the reader runs past the snapshot's real end and starts
reading the next region's own bytes as a bogus extra point.

The first copy starts at the point *after* point 1 (rotated by one); the
second starts at point 1, in the same cyclic order. The two copies are
separated by: zero-padded u32s, a nonzero **marker value 10000**, more zero
padding, a second marker (also 10000) — the padding can precede the *first*
marker too, not only sit between the two (`CAP-C00-BASE`: `marker1 = 0` at
the position right after snapshot1, with the real 10000 further on) — **and
then a third, narrower tag** (`marker3`: a single **u16**, not a u32 like
the other two; value **1** on every sample checked so far) immediately
before snapshot2's first point **[V, corrected 2026-09-11]**. This third
tag was the actual root cause of the original snapshot2-is-garbage finding:
it is only 2 bytes, so a reader that (like this module, before the fix)
treats the gap after `marker2` as one more 4-byte value consumes half of
snapshot2's own first point's id/x field along with it, misaligning every
point in the snapshot by those same few bytes. `accumark_pds.
check_region_c()` cross-validates both snapshots against the real perimeter
(the `region_c_consistent` fact in `verify_capture.py`) and passes on every
corpus fixture except the same three seam-allowanced pieces §11's own
`check_line_table` discussion below already flags as a known gap. Two
snapshots of the same geometry bracketed by a repeated 100.00%-shaped
constant is consistent with these being PDS's *Bookmark → Restore Original
/ Restore Defined* geometry cache, but that is unconfirmed pending
`CAP-C80-BOOKMARK` (Phase C of the decode plan); `marker3`'s role is
similarly unconfirmed **[?]**.

Immediately after snapshot2, on a piece with more than one piece record
(`piece_records > 1`, i.e. it has been edited at least once, §8) an
**undelimited second copy of the piece's own category name string** sits
right at the line table's doorstep — found by searching for the
already-known name rather than assuming a fixed gap size. A never-edited
piece (`piece_records == 1`) has no such echo. The zero-padded bytes between
snapshot2's end and the name echo (or the line table, if there is no echo)
are captured as `unclassified_gap` and are not yet understood **[?]**.

## 12. Coverage and remaining gaps

`accumark_pds.coverage()` classifies every byte of a file as `identified`
(assigned a meaning by this document), `zero_pad`, `residue` (§1's 3-byte
export-noise floor), or `unknown`, and is the acceptance metric for "is this
format fully decoded" (`CAPTURE_PLAN.md`'s Phase 1). Across the full
corpus (every `CAP-*`/`TASK*` capture except `CAP-C63-MODEL`, a distinct
manifest format with no piece blocks at all, §8): **93–99.5% identified**,
zero decoder exceptions on any block of any file. The trailer (§7), whose
size was previously only estimated at "~160 bytes", measures out as a
consistent **306 bytes** for a 1-block file and **334 bytes** for almost
every 2-block file; `CAP-C62-DART`'s **440-byte** trailer is the one
outlier, now explained rather than anomalous **[V]** (2026-09-09): the extra
106 bytes sit as a single block inserted at the very start of the trailer,
*before* the ordinary per-block `0d 00 00 00 10 00 00 00 …` markers (§11) —
those markers, and everything after them (name/timestamp/`MSI` fields), are
byte-for-byte the normal 334-byte layout just shifted later by exactly 106.
Inside that inserted block sit **three** consecutive 8-byte pointer-shaped
values (`50 2c 54 82 4c 02 00 00`, `00 2c 54 82 4c 02 00 00`,
`60 2c 54 82 4c 02 00 00` — differing only in their low 16 bits, the
established heap/pointer-residue shape from §1) that appear nowhere in any
non-dart capture's trailer — matching, one-for-one, the piece's three
points that don't exist on any other capture (two dart-leg points and the
apex). The values themselves are unrecovered heap residue like their
counterparts elsewhere in the file; what's now pinned down is that the
extra trailer size scales with "how many perimeter points aren't part of
the base corner set," not that it's specific to darts.

Remaining `unknown` bytes, roughly in order of how much of the file they
account for:

- A handful of small (1–8 byte) scalar fields scattered around fixed
  positions — right after the file header and before the metadata field
  block (e.g. `CAP-C00-BASE` +0x60, +0x70–0x83), at the internal-line list's
  own terminator boundary, and a handful of small ints at the very start of
  the trailer (`06 00 00 01 00 00 00 …` immediately after the line table) —
  none yet tied to a control or value in the UI **[?]**.
- §10.3's notch-attribute payload, table-point `b`/`c` fields, and `0f 0a`
  triples.
- §10.1's uneven/tapered cut-line miter point at `CAP-C30-SEAM-UNEVEN`
  corner 2 (two of the seam's three corners are now explained as plain
  single-edge offsets; this one resists both that model and a naive
  two-line intersection).
- §11's `unclassified_gap` bytes (Region C's `n_perimeter` mismatches on
  `CAP-C14-ANNOT`/`CAP-C62-DART`/notch pieces, and `CAP-C61-MIRROR`'s
  virtual 4th corner, are now explained — §10.2, §11).

None of these affect geometry, seam, notch, grade-rule, or grain/drill/
cut-out decoding, all of which are validated to 0.000000 in DXF residual
across the corpus; they are catalogued here as the specific, named targets
for Phase B (arithmetic/byte-diff analysis against the existing corpus) and
Phase C (the one or two targeted captures — `CAP-C80-BOOKMARK` for §11's
snapshot hypothesis, `CAP-C81-MEASURE` if anything remains after that) in
the decode plan.
