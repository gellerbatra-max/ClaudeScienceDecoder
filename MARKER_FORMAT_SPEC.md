# AccuMark native marker (type 9) - byte-level format spec

The CURRENT state of what is known about the marker object inside an AccuMark
"XGGT IXPORT DB5.x" export ZIP. `MARKER_DECODE_PLAN.md` is the journal (newest
STATUS block first) and `CHANGELOG.md` the per-round evidence; this file is the
reference that should read the same tomorrow as today. `FORMAT_SPEC.md` is the
sister spec for PIECES (type 20).

Tags: **[V]** demonstrated by a named file or a corpus-wide check; **[?]**
consistent with the data but unproven. Corpus = the 18 markers under `markers/`
(6 never-laid: 1825D x2, 5683D, 2591A, 418T, CLAUDE-QTY-TEST; 2303-BD 137 unlaid
with its laid twin and a drawn DXF; 4 July CP 150 markers, 1 of 72 placed; 5 small
CLAUDE-GRADE / CAP-C21 / AD1234 / LADIES-BLOUSE laid markers). All offsets are
file offsets unless stated; all integers little-endian; lengths in inches.

Reader: `accumark_marker.py` (`parse_marker`, `check_marker`, `marker_warnings`,
`marker_coverage`, `unplaced_inventory`). `python accumark_marker.py <zip>
--inventory` is the front door.

## 1. Object envelope [V]

Shared by every object type. Magic `XGGT IXPORT DB5.` at 0; the object name is a
NUL-terminated string at 0x15; the object type is a u16 at 0x7a (marker = 9,
type-10 geometry = 10, piece = 20, model = 12, order = 13, ...) with a u32 copy
at 0x60 or 0x68 by export vintage; the payload length is a u32 at 0x7e; the
payload starts at 0x80. The LAST 396 bytes are a trailer: the object's name again
at +0x8a, created / modified Unix stamps as aligned u32s at +0xf4 / +0xf8, and two
user-name strings at +0x110 / +0x162. Other envelope bytes (0x10-0x14, 0x48-0x5f,
0x64-0x77, 0x83-0x89) and most of the trailer are unexplained [?]; `marker_coverage`
counts them unknown.

## 2. Directory [V]

42 u32 ABSOLUTE offsets at 0x8a (0x8a-0x131). `0xffffffff` (or 0) = section absent.

- **Words 0-39 are section offsets.** Used on the corpus: 1, 2, 3, 4, 5, 6, 10, 11,
  12, 13, 14, 15, 21, 30. A section's span runs to the next used offset.
- **Word 40 is a STATE code, not an offset:** 0 = AS GENERATED (never stored by Easy
  Marking), 1 = stored by Easy Marking with fewer than all pieces placed - **including
  none at all** - and 2 = all placed [V: 60 markers; live: a marker opened in Easy
  Marking and stored empty reads 1]. It is not a count of placed slots. **Word 41 is 0.**
  Reading them as offsets fabricated a section 40.
- **The `-6` convention:** every list section's chain starts 6 bytes BEFORE its
  directory offset and closes 6 bytes before the next section's [V for 6, 10-13,
  15, 21]. The directory offset points 6 bytes into the first structure.

## 3. Section 1 - header scalars

Six f64 are read [V]: **@396 fabric width**, **@412 length** (0 on a never-laid
marker), **@422 total area**, **@430 placed area** (= sum of the PLACED slots'
declared areas = W x L x U / 100; 0 when nothing is placed) [V: 18/18], **@446
utilisation %**, **@454** (a perimeter sum). The section is about 370 bytes and
only these 48 are read (v4.14: plus four u16 counters at 480 / 482 / 490 / 492 = records, slots, models, size rows - section 22; v4.16: the u16 at 520 = the lay table's SPREAD - section 23). Of the 316 unread byte positions `marker_coverage`
attributes to it, 271 are byte-identical across all 18 markers and 45 vary; their
meaning is open [?].

`@422` / `@454` relate to the slots in one of three MODES (`header_sums`): the sum
over `all` slots' declared area / record perimeter; over the `last_model`'s slots
only; or `2x_all` [V]. On the six never-laid single-model markers both are `all`;
on the unlaid 2303-BD 137 both are `last_model`; on its laid twin `@422` is `all`,
`@454` `last_model`; LADIES-BLOUSE's `@454` is `2x_all`. Why the last model [?].

## 4. Sections 2, 3, 4, 5 [?]

Section 2's tail is decoded (section 15 below: the names of the four tables the marker was made with); the rest is not. 2 = options + those names (grows with them); **3 = the marker's copy of its Notch Parameter
Table and 4 = its Lay Limits rows (v4.14, section 22 - the earlier readings "repeating `00 00 b0 07` groups" and "a 12-byte label-config header" are retracted)**; 5 = the Annotation table's copy, then the `-PDSTEXT-` label
table (`-PDSTEXT-`, then a 3-byte gap and the piece's label text: what
`declared_piece_names` scans). They hold most of the marker's unexplained bytes.

## 5. Section 6 - block buffers [V framing]

Only on some markers (1825D, 418T, July CP 150, the ZZC / ZZN scratch markers).
Entries of 102 bytes from `dir[6] - 6`: `<u16 0><4 x f64 buffer, inches><68 zero
bytes>` [V framing, 13 markers]. **The table is a list of buffer DEFINITIONS, and a
piece points into it** by a 0-based `buffer_index` (section 10, flag bytes 4..5) or
at none (`0xffff`) [V]. Where every piece has its own definition the table has
`pieces + 1` entries and piece k points at k (1825D, 418T, July CP 150, ZZC-BIG);
`ZZC-M1..M3` / `ZZN-F1` have 4 entries for 5 pieces - `[0.3937 x4]`, `[0.1968 x4]`,
`[0.3937 x4]`, `[0.7874, 0.1968, 0, 0]` inches - with BK -> 0, COL -> 1, CUFF ->
none, FR -> 2, SL -> 3. (An earlier reading, "entry k is piece k's, entry 0 the
marker default", was an over-fit to the small corpus and is retracted.) **An entry is the static
amounts of the block-buffer rule the piece's Lay Limits row names [V, v4.12: 81 entries on 5 markers]**, and its four doubles are ordered **Left, Right, Top, Bottom** - the sleeve's rule 4
(Left 2.00 cm, Top 0, Right 0.50 cm, Bottom 0 in the table, section 19) is `[0.7874, 0.1968, 0, 0]`, and a live run with a rule of four different amounts (Left .11, Top .22, Right .33, Bottom .44 cm; lay limits
`ZZLL-BB9` pointing FRONT at rule 9, a copy of ZZC-M1's order with block buffer `ZZBB-X1`, Process, then the four doubles read from the marker file) gave `[0.0433, 0.1299, 0.0866, 0.1732]`.

**The home box does NOT follow this table.** The same five pieces in ZZC-M1 (buffers
0.5 cm / 1 cm / none / unequal) and ZZC-BIG (1 cm everywhere) have byte-identical
home boxes [V], so what the table is for, and why the July CP 150 x residual
(`home x 2 - bbox` = 0.1182 = 2 x 0.0591 in) matches it, are both open [?].

## 6. Section 10 - piece list [V: 18 of 18]

A 28-byte header whose last 6 bytes are the literal `MARKER`, then contiguous rows
closing at `dir[11] - 6`:

    <u16 name length> <u16 category length> <24 flag bytes> <name> <category>
    <fabric types: u16 count at flag byte 18, then that many <u16 len><text>>

Flag bytes 4..5 (u16) = 0-based index into section 6's table of buffer definitions (0xffff = none). The 'Fabric
Type' role (A/B/C/D/G/M/F ...) is the fabric-type text. v4.14: flag u16 @+2 = the piece's Lay Limits row, @+6 = its buffer rule,
@+8 = its flip code, @+10 (i32) = its tilt limit - section 22. The other flag bytes stay raw [?].

## 7. Sections 11 and 12 - models and size table [V: 18 of 18]

11: `<u16 length><name>` per model, in order. 12: rows of `<u16 name length><u16 model
index (0-based)><u16 pieces><u32 first slot><u32 flags><size name>`; `pieces` is
how many section-21 slots the row owns and `first slot` the running sum, so the
rows TILE the slot table. Each cut of a size is its own row (and bundle), so a
size appears once per cut. `flags` is 0xffff on 12 markers and 0 on the rest [?].

## 8. Sections 13 and 14 - records [V]

13 is a u32 array of the section-14 records' byte offsets, relative to `dir[14] - 6`.
A record: 48 bytes of head (8 unexplained, then a 10-byte prefix of 5 u16, then
`f64 area`, `f64 perimeter`, `u16 3`, `u16 1`, `u16 stream length`, 8 zero bytes), a
NUL-terminated label `<piece><cut description><size>G`, then the **stream** (extent = up
to the next record). One record per (piece, size, cut). u16 @+10 of the head is the
stream's per-size entry count (slot `@88 = it + C`, section 10).

**The stream IS the graded outline (v4.7 [V, most of the grammar]).** `accumark_marker.decode_record_stream`.

    00 02 00                              3-byte lead
    [<tag> 00 <n> 00]*                    header records; tags are ASCII: S 0x53, M 0x4d, F 0x46, G 0x47,
                                          I 0x49, H 0x48 ... with a point count n [?: read as contour kinds]
    point items                           one per point: prefix parts + ONE main part + u16 point id
    <attribute bytes 0x09 / 0x01 ...> <3 bytes>   trailer (first byte 0x09 or 0x01; last byte varies with size [?])

A *part* is `<tag> <data>`. Tag bit 7 = MAIN (the last part of a point), bits 6-5 = width code (0: two
i32 [8 B], 1: 12-bit [3 B: byte `x_hi<<4|y_hi`, x lo8, y lo8], 2: two i16 [4 B], 3: 20-bit [5 B: x lo16,
y lo16, byte `x_hi<<4|y_hi`]), bit 4 CLEAR = ONE LEADING EXTRA BYTE before the data (meaning open [?]).
Coordinates are 1e-4 in. **A point's step is the SUM of its parts** (a long or curved run is a chain of
prefixes and one main part: 26 parts were seen on one point). The first point of a contour is absolute; every
other point is a step from the previous. A prefix with low nibble `0xa` CLOSES the contour (its step returns to
the start) and the main part after it is the absolute start of the next contour (the internal / grain line);
tag `0x00` starts a contour with an absolute 20-bit pair. The point ids count 1, 2, 3, 4 on 'turn' points and
down from 29999 on plain ones (restarting per contour). Low nibbles (1 plain, 9 turn, 8 / c / 4 ...) carry the
point's attribute [?].

A point with MORE THAN 6 parts is a **pen move**: a long jump decomposed into 12- / 16-bit steps (7 - 52
parts seen; ordinary points have 1 - 3). The next contour starts where it ends (the far-away mirror line on a
fold piece, a seam contour).

**Fold pieces.** When the first contour does not reproduce the record's area and perimeter, it is ONE HALF of
the piece: its first and last point lie on the fold line, the record's `area` is twice the half's, and the full
outline is the half plus its mirror image about that line, in reverse (131 of 255 streams: 1825D, 5683D, the
2303 OUCF pieces, 2591A, half of the blouse). The header records `M` / `S` describe the extra contours
(a mirror line, a seam offset by about +0.28 in) that follow.

Ground truth, three independent kinds - (1) the piece object: the first contour equals the graded outline
EXACTLY - the rectangle 4 of 4 at sizes 2 / 8 / 18, RUFFLE 142 of 142 at all five sizes, its grain line
(543131, 45098)-(584289, 45098) too; (2) the record head's own `area` and `perimeter`: the shoelace of the
outline (unfolded when needed) reproduces both on **255 of 255 distinct corpus streams** (median error
0.0000%, max 0.29% area / 0.04% perimeter); (3) the slot's stored home box, which the decode never uses: its
bounding box equals the home box to 0.000 in on every slot of the MARKER-ONLY ZIPs 1825D (36), 5683D (24), 2591A
(35), 0418T (22) and of every fixture with a piece object (2303-CP 150: 0.118 - 0.183 in larger, the stored /
block-buffer effect [?]). `record_outline` reads an outline from a marker with NO piece objects, and
`unplaced_inventory` uses it (`outline_source: stream`).

**The stream is the CUT line (v4.7 blind test).** For a piece with seam allowances the stream is the stitch line
offset by each segment's allowance (BACK: 1.0 in fold edge, 0.375, 0.25), not the piece object's perimeter - verified on
`CLAUDE-D3-BF` (BACK / FRONT, never seen before): the stitch points lie exactly 0.375 / 0.25 in inside the stream outline
and the stream's bounding box equals the stored home box to 0.0001 in. Contours are split by a pen-move threshold that is
the one guess in the grammar (`_PEN_MOVE` 6; BACK / FRONT need 20: 7 parts is a normal long step there): `record_outline`
tries 6, 20, never and keeps the first that reproduces the record's area and perimeter.

**The other lines of the piece (v4.7 [V], blind test CLAUDE-D4).** After the perimeter the stream holds, back to back, the grain
line (2 points; implicit unless the header has a `G`) and then one contour per header record - `I` internal line, `H` cutout, `D` drill hole
(1 point) - each `n` points (`!`: 3 points' worth of something else, adds none). Each contour starts with an ABSOLUTE point that carries no
marker of its own; the counts add up exactly to the points left after the perimeter, so that is how they are split. A contour-start item's
absolute position is its MAIN part alone: the prefix parts in front of it (up to 6 on a 2303 piece) are not a movement. Internal lines and
drills are NOT graded (identical at every size). Verified equal to the piece objects on 77 records (grain, internal, cutout, drill).
Fold pieces (`S` / `M` / `F` records) are not split this way yet [?].

**Fold halves (v4.7 [V for the newer vintage]).** After the cut half: the grain line (2 points), the internal lines (I / H / D counts), the SEW half (the
stitch line - every point left over) and the mirror line (2 points). Accepted only when the cut and sew halves' end points lie on the mirror line. The mirror line is
the chord of the sew half and moves with the size; the grain and internal lines do not. The 1825D / 5683D / 2591A / 418T vintage differs (id 0 items `(-10000, -1)`, a
`00`-tag item at the end of a chain, more attribute bytes) - not decoded [?]; its grain is the second contour's first two points, a horizontal segment (89 of 89 records).

**Grading between two ruled points (v4.7 [V], blind test CLAUDE-D4).** Points without a rule between two ruled points move by a SIMILARITY
of the chord joining them: the chord is rotated and scaled onto the graded chord and the chain keeps its shape (matched to 1e-4 in on 20 points
at two sizes; a blend of the two moves by chain length is up to 0.295 in off). Identical to a plain translation when both ruled moves are equal.

**Point attributes (v4.7 [V]).** The low nibble of a point's main tag and its extra byte say what the point is: low
nibble `1` = a PLAIN point, or a NOTCH when the tag carries an extra byte (notch type = the extra byte's low
nibble: 5 and 1 seen; the high nibble is a flag, 0 / 1 / 2 seen [?]); any other low nibble (`9 8 c 4 0`) = a TURN
(corner) point, with a notch type in the extra byte for a corner notch. Against the piece object's own perimeter
points this classifies **7,455 of 7,455** points correctly (turn / plain / notch and notch type), so notches can be
read from a marker with no piece object (`record_outline()['notches']`, `unplaced_inventory` slot `notches`: 36 type-1
notches on 5683D). Turn points carry ids 1, 2, 3 ... (their sequence), plain / notch points count down from 29999.
The trailer's attribute bytes are the turn points' attributes (`09`, `0d` ...) over all contours, then 3 bytes.

Still open [?]: the extra byte's high nibble, the trailer's last 3 bytes (`ff ff xx` / `fe ff xx` / `00 00 xx`,
xx varies with size), the header records' exact meaning (which contour is the cut line when several are present - the first
is), the trailer's attribute bytes and its last byte (varies with size), curve segments (the stream is the
finished, sampled line; the piece object holds control points: 35 points against ~100 on LADIES-BLOUSE-BK).

## 9. Section 15 - the order copy [V: 18 of 18]

The marker's own copy of the ORDER, closing at `dir[21] - 6`. Per model:

    <48-byte header: u16 name length @+0, u16 ordinal (1-based) @+8,
     u16 size count @+12, u16 fabric-type count @+14>
    <name> <fabric types (<u16 len><text>)> <size rows>
    size row = <u16 name length><u16 QUANTITY><24 zero bytes><size name>

Model names equal section 11's, and **QUANTITY equals the number of size-table rows
for that (model, size)** - the marker states its own cut quantities.

## 10. Section 21 - slots [V]

`(dir[30] - dir[21]) / 96` slots of 96 bytes; slot `i` starts at `dir[21] + 96 i`.

    +0   f64 placed centre x     +8   f64 placed centre y      (0.0 while as generated;
                                                                 -1000 once Easy Marking has
                                                                 stored the slot unplaced [V live])
    +16  f64 home x              +24  f64 home y     (half the piece's box; the block-buffer table does not drive it [?])
    +32  u16 orientation         +34..+37  const ff ff ff ff    +38  f32 TILT in radians, ccw (v4.13, section 20)
    +42  f64 declared area       +50..+63  raw (u16 @52, @54 vary [?]); **u16 @60 = the engine word - bit 0x0200 = the piece's engine frame is a quarter turn from its stream frame (section 36)**
    +64  u32 bundle (low 16) + flags (high 16, 0)    +68..+87 const [?]
    +88  u16 AS-GENERATED SIGNATURE [V]: non-zero on every slot of a marker Easy Marking
         has never stored, 0 on every slot of every marker it has - laid, part-laid, or
         stored EMPTY. `@88 != 0  <=>  word 40 == 0` holds on all 60 markers, and on the
         live twins below. **@88 = record head u16 @+10 (per-size count) + C, C one constant
         per piece** [V: 107 (marker, piece) groups, 43 markers, 31 pieces, 0 exceptions];
         C = 4 for a piece with at most a grain line, 28-32 with grain + mirror, 216-266 with
         ten internal lines, 620+ with eighteen - what exactly C counts is open [?].
    +90..+95  the NEXT slot's head (below)

**The head.** 6 bytes BEFORE each slot body: `<u16 record index (0-based, section 14
order)> <u16 piece index (1-based, section 10)> <u16 bundle>` [V: 677 of 677 slots on
all 18 markers]. (Earlier notes read `+90/+92/+94` as a circular pointer; it is the
next slot's head.)

**Orientation.** (v4.13: this is the PRE-SET pattern of an unlaid marker; the PLACED orientation of a laid slot is its low three bits + the tilt float - section 20.) Bit 0x2000 = rotate 180, bit 0x0080 = mirror [V vs drawn DXF]; v4.17: 0x0080 = flip X, 0x0100 = flip Y, both = X,Y - the model's FLIPS (section 24). Bit
0x0040 is a COPY of the piece row's flag u16 @+14 (section 10): slot bit == (flag == 1)
[V: 9,122 of 9,122 slots, 111 markers; no marker mixes flag values, which is why it looked
marker-level]. It is not the mirrored-pair bit (2303 has pairs and no 0x0040); what order /
model option sets the flag is open [?]. **Bit 0x8000 = "stored by Easy Marking"** [V live: every slot
gains it on a plain store, `0x0000 -> 0x8000`, and `0x2000 -> 0xa004` - a rot180 preset
also gains 0x0004]. A placed slot's word also carries lay-
session bits (0x8000, 0x0200, 0x0020 ... ). On a never-laid marker only the three
known bits appear [V: 6 of 6]; on a PARTLY laid marker an unplaced slot keeps the
bits it had before it was lifted (61 of 71 on July CP 150). So on a never-laid
marker the word is a PRE-SET lay pattern, not a placement.

**Placed vs unplaced** is a sentinel test on the centre (0,0 as generated, -1000 once
stored, i.e. x < -900); the laid state cross-checks it with directory word 40 and `@430`.

**What Easy Marking's STORE does to an unplaced marker** [V live, 2026-09-21,
`markers-live/CLAUDE-UNP-E1-TWINS`]: `CLAUDE-QTY-TEST` (as generated) was opened and
Saved As E1A with nothing placed; then one piece was dragged onto the marker, returned
(Piece > Return > Unplaced) and stored as E1B. E1A vs the original: directory word 40
0 -> 1; every slot's centre 0,0 -> -1000,-1000, orientation gains 0x8000 (and 0x0004
beside rot180), `@88` 9 -> 0, home box +5e-5 in in x (rounding to the 1e-4 in unit);
the header doubles, areas and every list section are unchanged; the type-10 object
grows (1958 -> 2818 B). **E1B vs E1A differs in 12 bytes - the name, timestamps, session
residue and the last byte of one slot's area double (1 ulp).** Laying a piece and
returning it leaves no trace, so "laid once and cleared" cannot be told from "opened and
stored empty", and "never laid" cannot be told from "never stored" by anything but the
as-generated signature above.

## 11. Section 30 - the embedded type-10 object [V structure, ? content]

A full XGGT object (its own envelope + 42-slot directory) holding the layout's
scratch data. Its slot 33 exists only when laid, and its own directory word 41 is
the placed count (0 when never laid) [V: 18 of 18; 0x80002 on the July partial
markers, meaning not understood [?]]. Slot 39 (95% of the bytes) is a function of the piece TOPOLOGY only -
independent of layout, fabric cost, grading complexity. Not chased.

## 12. Binding a slot [V]

- **size, model** <- the size table tiles the slot table (row `i` owns slots
  `ordinal .. ordinal + pieces - 1`);
- **record** <- the slot head's record index;
- **piece** <- section 10 at the head's piece index - 1;
- **checked, never chosen from:** the declared area equals the record's; the slot's
  bundle equals its head's bundle equals its size-row index; the record label ends
  `<size>G`.

Proof independent of area and geometry: the drawn DXF labels every placed piece
`<piece> <size>` at its placed centre - 97/97 on 2303-BD 137 PLACED with this
binding, 20/97 with binding by declared area (which ties on sister sizes).

Pairs: slots sharing (bundle, record) form a group of 1 or 2; a group of 2 is a
`CUT X02` mirrored pair - the plain slot then the `0x0080` one [V: 116 of 116].

## 13. Byte-map status (`marker_coverage`, 18 markers)

Every byte in sections 6, 11-15, 21, 30 is classified. Unknown = 1,111-1,753 bytes
per marker (1.32% overall, the same on a 3 KB marker as a 280 KB one; v4.8: was 1.38% before section 2's table names were decoded): trailer,
section 1's unread bytes, sections 2-5, the envelope. **identified 32.5%, raw 7.1%,
zero_pad 0.8%, opaque 58.3%** (v4.7: was 4.1 / 2.4 / 0.8 / 91.3 before the section-14 stream was decoded; a
stream that verifies against its record's area + perimeter is identified up to its trailer). The opaque bytes are now almost entirely section 30, the embedded type-10 object.

## 14. Open, and what settles each

| open | evidence so far | method |
|---|---|---|
| what the buffer is for in the home box of an UNPLACED slot (the marker's entry order Left, Right, Top, Bottom is proved; for a PLACED slot the box is the placed shape + the buffer turned with it, section 20) | unplaced: home box ignores it (ZZC-M1 vs ZZC-BIG) | live: unequal buffers on a piece with real geometry, unlaid |
| the COLLAR of the LADIES-BLOUSE set lies a quarter turn from the frame its orientation codes refer to (section 20, `frame_offsets`): **WHICH pieces: CLOSED v4.33 (slot word @+60 bit 0x0200, section 36)**; the sign (+90 collar; a legacy sleeve +90 / -90 by size) and WHY are open [?] | 28 markers, one piece, +90 fits every one; the bundled pieces are stubs | a piece object with a real grain line whose stream outline is turned (a collar digitised with the grain along its length) |
| how a 45-degree (or any other non-tilt) placement is stored | AccuNest's Rotation-45 override placed nothing off the 90-degree grid; tilts are the float at +38 (section 20) | Easy Marking: `Rotate 45 CW` on an asymmetric piece, stored, read back |
| ~~the exact area a BLOCK adds to a placed slot's declared area~~ CLOSED v4.19 (section 25): record area + the growth of the outline by (left + right) x (top + bottom) in the piece frame, turned with the piece | 18 slots under an unequal block (exact to 0.004 sq in) + the 1 cm block of 12 earlier markers | percentages / the Segment amount on a placed marker |
| ~~notch numbers above 15 in a marker stream~~ CLOSED v4.15: a marker keeps only the code min(number, 5) (section 18); what a corner notch (a notch on a turn point) stores: see section 37 - the stream keeps the piece's own byte, 9 seen unclamped (v4.34); a corner notch above 15 is not tested [?] | 11 numbers (1-7, 12, 16, 25, 30) on PDS / imported pieces and their markers | live PDS: a corner notch (Seam > Define corner notches?) with a number of 12 / 16 / 25 |
| ~~what sets the piece-row flag @+14 (= the slot 0x0040 bit)~~ CLOSED v4.16: the M (major piece) option of the piece's Lay Limits row (section 23); the pre-set rot180 alternation follows the table's Bundling [V] | 0x0040 == flag @+14 on 9,122 / 9,122 slots [V]; flag == the row's M on 341 / 341 piece rows | live: flip one order / model option per run (DATASET_DESIGN F5) |
| the extra byte's high nibble; the stream trailer's last 3 bytes | kinds and notch types classify 7,455 / 7,455 piece points | correlate with the piece's f2 / rule fields and the size |
| what C counts in @88 = head count + C; slot @52/@54/@60 | @88 = p1 + C(piece) [V], C tracks internal-line points; stored-empty and laid-then-returned read 0 alike | pieces with 0 / 1 / 2 / 4 internal lines built in Pattern Design (DATASET_DESIGN F6); @52/@54/@60 vs piece/size |
| the y excess on July CP 150 unplaced slots (up to 0.0786 in, one-sided) | x fits the CP 150 table but the table does not drive home | live: known notch / curve |
| ~~placed slots 7.2% larger than their record (ZZC-M3, ZZN-F1)~~ CLOSED v4.19: the 1 cm block's growth (section 25) | 2 slots each | - |
| why `@422` / `@454` are last-model sums; LADIES-BLOUSE 2x | modes observed exactly; a FRESH two-model as-generated marker (`CLAUDE-D2-E7B`) shows `last_model` on both [V], so it is generation-time behaviour, not a laid-state artefact; the LADIES-BLOUSE `2x_all` case is still unexplained [?] | one more two-model order laid in Easy Marking |
| size-row `flags` (0xffff vs 0) | 12 vs 6 markers | live |
| section 2 (its 211 constant bytes before the name strings), section 5 (the Annotation copy's packed format), section 1's other counters (+168, +172, +180, +182, +184, +190 ... : equal no sum tried), the trailer's filler and state words | constant across 73 markers / varying with content | twin diffs; Annotation editor ground truth |
| the two tilt directions of a Lay Limits row (a marker keeps ONE value: cw or ccw?) and its unit when the table is in DEGREES | the only corpus rows with a tilt have cw == ccw == 0.1574 | a table with cw 1 / ccw 2 (or degrees), a marker made from it, read section 4 |
| Lay Limits: the low three bits of a row's byte b2 (0x07), the eight constant bytes `01 00 .. 00` before the skew array and `7f 00 ..` after it, what the Group column does; older-vintage multi-row tables and their tilt / skew bytes | b2 & 0x07 varies (06 / 05 / 01 / 00) with no visible setting behind it; every other byte is constant across 15 tables | a fresh table from File > New, one row edited at a time; a real multi-row table of the older vintage |
| `ALL GMT WAY` (2591A): the marker's own row says DEFAULT = MWS, flip 1, single ply (sections 22 / 23); its Bundling is INFERRED from the presets (all 0 over 7 sizes = All Bundle, Same Direction) - unconfirmed until the file arrives | 2591A marker, bundle presets | the table from Explorer `OldFiles` |
| does a row that allows 180 let the nest engine turn a piece against its preset? | presets follow the table's Bundling on 29 markers [V]; a `W` piece keeps its preset in a real AccuNest nest [V, `laylimits/EXPERIMENT_W_ALTERNATE.md`]; no piece in that small draft nest was turned | live: a blank-options table with alternating bundles, a marker with room to gain, read the placed orientations |

Marker-only ZIPs (no piece objects) can never yield outlines, and an unplaced marker
carries no positions - those are limits of the export, not of the decoder.

## 15. Section 2 - the table names [V: 69 of 69 markers, every vintage]

Section 2 ends with the NAMES of the tables the marker was made with. Eleven u16 lengths sit at section start -4, -2, 0, 2, 4, 6, 8, 10, 12, 14 and 18; the strings follow, back to back
and without separators, from **section start + 231**, in that order:

| at | string | seen |
|---|---|---|
| -4 | the marker's own name | equals the object name on 68 of 69 (the 69th, `ZZN-D1`, is a copy that kept its source's name) |
| -2 | customer | empty, `GERBER GARMENT TECH`, `MarkerWizard`; `[1]` appended once per regeneration |
| 0 | the order object's name | may differ from the marker's (`CLAUDE-D2-GEN` / `CLAUDE-D2-M0`) |
| 2 | reference | `4` on the ACCUPLAN markers, else empty |
| 4 | **lay limits** table | `L`, `SINGLE-PLY`, `COSTINGS`, `ZZLL-1..3`, and the user's `NEED- TWO WAY`, `ALL GMT WAY`, `G-LAYLIMITS` |
| 6 | annotation table | `A`, `SIZE-AND-BUNDLE`, `M-MARKER`, `NEED-MARKER` |
| 8 | block buffer table | empty, `3MM`, `ZZBB-1` |
| 10, 14 | (always empty) | |
| 12 | notch table | `P-NOTCH`, `AP-NOTC`, `V-NOTCH-ALL CUSTOMERS`, `NEED-P-NOTCH` |
| 18 | extra | `A4-LADIES-BLOUSE`, `-REGEN-` |

`lay_limits`, `annotation`, `block_buffer` and `notch_table` equal the names of the type 6 / 2 / 3 / 17 objects bundled next to the marker (58 markers find their lay-limits object). The **order** stores
the same ten slots (below), and an order and its marker agree on the four table names in 58 of 58 pairs (41 orders) (`customer` and `extra` change when a marker is regenerated). `accumark_marker.parse_marker_tables`.

## 16. Lay Limits tables (object type 6) [V]

`accumark_laylimits.py`. In an export ZIP the table starts at object offset 0x8a (10 bytes into the payload region, after `00 00 90 00 00 00 00 00 00 00`) and is `payload_len` long; a `.GT_lay`
file in a storage area holds the same bytes from 0x90. Two vintages, told apart by structure (the file's type byte at 0x76 is 5 / 4):

**V17 vintage** (every table the current editor saves) - verified against the editor's grid on six tables (`ZZLL-1`, `-X1`, `-X2`, `-X3`, and the older-vintage `L` and `SINGLE-PLY`) and against the recorded settings of nine single-row tables
(`laylimits/GROUND_TRUTH.json`); `ZZLL-X1..X3` were built one setting at a time from `ZZLL-1`, each saved under a new name and diffed:

```
u16 line1_len, u16 line2_len      the comment, wrapped at 20 characters (20 + 13 for "ZZ scratch enforcement test table")
u8 spread                         0 single ply, 1 face to face, 2 book fold, 3 tubular
u8 bundling                       0 all bundles same direction, 1 alternate bundles alternate direction, 2 same size same direction
u16 n_rows
u8 per_model, 7 x 00              Per Model checkbox
comment text
n_rows x ( u16 name_len, u8 b2, u8 b3, u8 flip_code (1-12), u8 units_flag, u16 buffer_rule, i32 tilt_cw, i32 tilt_ccw, name )
u32 1, u32 0
u32 4*n, n x i32                  weft skew x 10000, degrees
u32 0x7f, u32 0
u32 len, u32 n_props, props       each: u32 len, u32 1, u32 0, u32 nlen, name, u32 4+vlen, u32 vlen, text   ("Category group" = "0,0,3,0,0,0,0", only when a group is non-zero)
```

Piece options are bits: b3 `M 0x80, W 0x40, S 0x20, 9 0x10, 4 0x08, F 0x04, O 0x02, N 0x01`; b2 `U 0x80, X 0x40, Z 0x10, P 0x08`. `b2 & 0x20` + `units_flag = 1` = the tilt unit is degrees; b2 & 0x07 carries nothing
visible (06 / 05 / 01 / 00 seen; a row's b2 is rewritten when its options are edited). The tilt limit is stored x 10000 in **inches** for a length (0.40 cm -> 1574, 1.5 cm -> 5905, 2.5 cm -> 9842) and
raw degrees when the unit is degrees (0.40 -> 4000). The rule number is a u16 (17 read back). Flip codes as the editor labels them: 1 Original Digitized Position, 2 Rotate 180, 3 Flip about Y-axis,
4 Flip about X-axis, 5 Rotate 90 CCW + Flip X-axis, 6 Rotate 90 CCW, 7 Rotate 90 CW, 8 Rotate 90 CW + Flip X-axis, 9 Rotate 45 CCW + Flip X-axis, 10 Rotate 45 CCW, 11 Rotate 45 CW, 12 Rotate 45 CW + Flip X-axis
(Gerber's help text lists 5 and 6 identically; the editor and `marker-making.md` agree on the table above).

**AccuMark 9 saves** (`NEED- TWO WAY`, 39 bytes; `ONE GMT ONW WAY`, 55): the V17 header and row layout, then either nothing or only `u32 1, u32 0, u32 4n, n x i32` (the weft-skew array) - no `0x7f`, no property block.
The editor shows them exactly as read (Single Ply, Alternate Bundle, `MWS`, rule 1).

**Older vintage** (the user's real `L`, `SINGLE-PLY`, `G-LAYLIMITS`; 84 / 76 bytes): 40 comment characters, u8 spread, u8 bundling, u16 n_rows, then the row: name padded to 20, `00`, options byte (same bits), flip code,
one byte, u16 buffer rule, zeros. Read for single-row tables only, verified in the editor on `L` (Single Ply, Same Size Same Direction, blank options, flip 1, rule 0) and `SINGLE-PLY` (Single Ply,
Alternate Bundle, `MS`, flip 1, rule 1); `COSTINGS` (2303 CP 150) reads `MWS`, rule 1, alternate - by the same layout, not seen in the editor. The corpus `L` (in every user ZIP) is the blank-options table.

**Independent confirmation.** The table's Bundling predicts the 180-degree pattern the marker stores on its bundles: on 29 markers with a bundled table every neighbouring bundle pair follows it - alternate
bundles differ (`COSTINGS`, `SINGLE-PLY`, `ZZLL-1..3`), same size same direction is equal within a size and alternates between sizes (`L`, 16 markers where two bundles share a size), all same direction is equal -
and the wrong Bundling on `CLAUDE-D2-E7B` is contradicted (`selftest`). The stored presets carry no trace of a flip code.

## 17. The order's table names [V: 41 of 41 orders, 58 order-marker pairs]

The order object stores the same ten name slots. **V17 vintage:** u16 lengths at payload +10, +12, +14, +74, +76, +78, +80, +82, +84, +88 (name = the marker name the order generates, customer, reference,
lay limits, annotation, block buffer, -, notch table, -, extra) and the strings back to back from +176. **Older vintage** (`COSTORDER`, `LADIES-BLOUSE`): ten 20-character slots, space- or NUL-padded, at +10, +31,
+52, +132, +153, +174, +195, +216, +237, +259. `accumark_marker.parse_order_tables` (also in `parse_order(...)['tables']`).

## 18. Notch Parameter Tables (object type 17) [V]

`accumark_notch.py`. In an export ZIP the table starts at object offset 0x8a and is `payload_len` long; a `.GT_notpt` file has the same bytes from 0x90. Verified in the Notch editor (`Notch.exe`) on a table
with one row of every type and distinct numbers (`notch/ZZNT-X1`, `-X2`, saved under new names) and on the real `NEED-P-NOTCH`, `V-NOTCH-ALL CUSTOMERS` and default `P-NOTCH`:

```
5 x ( i32 perimeter, i32 inside, i32 depth )                 the first five notches again in the older three-value layout (always equal to records 1-5)
u32 N                                                        the number of records = the highest notch number kept (a table ends at its last defined notch)
N x ( u32 type, i32 perimeter, i32 inside, i32 depth )       record k = notch number k
[ u32 0 ]                                                    optional trailer (present on tables saved by the V17 editor and on 2303's)
```

Lengths x 10000 in inches (0.30 cm = 1181, -0.20 cm = -787); `type` 0 None (an undefined number), 1 Slit, 2 T, 3 V, 4 Castle, 5 Left Check, 6 Right Check, 7 U, 8 No Lift Slit (the editor's list order). Up to 99
numbers. The editor greys out the widths a type does not use (Slit / T / No Lift Slit have no perimeter width, V / Slit / Left / Right Check no inside width) and stores 0 there. Depth > 0 cuts into the
piece, depth < 0 sticks out (Castle, the external V of the 2303 and 1825D tables). A piece's `Notch Type N` (FORMAT_SPEC.md: "Notch Depth is not stored in the piece file: looked up from a system-wide table") and the
notch code in a marker's section-14 stream are this notch number **for numbers 1-4 only - corrected in v4.15, see below**. Confirmed geometrically: the 30 notch spikes of a real AccuNest plot are all 0.40 cm =
notch 1 of the default `P-NOTCH`. A table whose length is not 64 + 16 N (+ 4 zero bytes), whose triplets differ from records 1-5 or with a type above 8 is refused.

**Number and code (v4.15) [V].** A notch keeps its NUMBER (1-99, the row of this table) on the PIECE only: it is the last byte of the 45-byte tag-0x07 child of the notch's point in the piece's line table (Region D;
`accumark_pds.notch_numbers`). The perimeter point (its `f1` high byte) and the marker's stream (the low nibble of the extra byte) store the notch CODE **`min(number, 5)`**: numbers 1-4 as they are, every number from
5 up reads 5 - the five older-layout triplets at the head of the table are why. Proved on a piece made in PDS with the Type list set to 3, 6 (the two imported notches), 7, 12, 16, 25, 30 and 30 and the marker Order Editor made
from it (`notchnum/`: piece codes 3 + 8 x 5, the marker's stream the same at S / M / L, all nine notches), and on the corpus: the 134 notches of the bundled pieces that carry the number (numbers 5 and 6) and the real styles of the scratch area (numbers 1, 2 and 4) - none against the rule.
So a marker cannot say which notch a code 5 is: notch 5 (a slit in `NEED-P-NOTCH`), 6-7 (V) or 8-15 (slit) all read 5. The nest spec gives each shape notch the CANDIDATE numbers (`notches[].numbers`, `number` when there is one)
and warns when the candidates differ in shape; the piece objects, when bundled, hold the number. The old "numbers above 15 (a nibble)" worry is moot: no number above 5 is stored in a marker at all.

## 19. Block / Buffer tables (object type 3) [V]

`accumark_blockbuffer.py`. In an export ZIP the table starts at object offset 0x8a and is `payload_len` long; a `.GT_block` file has the same bytes from 0x90. Verified in the Block Buffer editor (`BlockBuff.exe`)
on `ZZBB-USER` (8 rules, unequal sides, a Block rule, static and dynamic amounts) and on `ZZBB-X1` / `-X2` (a rule with nine distinct amounts, percentages, a two-line comment; saved under new names and diffed),
and on the real `3MM` / `3MM-N`:

```
V17 layout:    u16 line1_len, u16 line2_len, u16 n_rules, comment text, n_rules x entry, [ u32 0 ]
older layout:  40 comment characters, u16 n_rules, n_rules x entry                          (AccuMark 9 `3MM`; stray bytes in the units' high bytes)
entry (70 bytes):  u16 rule number, u16 type (0 buffer, 1 block), 11 x slot
slot (6 bytes):    i32 amount x 10000, u16 unit          static Left, Top, Right, Bottom, Segment, dynamic Left, Top, Right, Bottom, Segment, and one slot that is always 0
```

An amount is a length in inches (0.30 cm = 1181) or a percentage of the plaid / stripe repeat (unit 2: 50% = 500000, 12.5% = 125000); typing a unit suffix (`1.5in`) is ignored by the editor (read as 1.5 cm in a
metric table). The editor requires a rule number for every used rule and greys out the Segment cells, so segment amounts read 0. The header count is the highest rule kept. A Lay Limits row names a rule by number
(`buffer_rule`, 0 = none); the real `3MM` rule 1 is a Buffer of 0.15 cm on every side (0.0591 in): two pieces end 3 mm apart. Blocking is a visible zone added to the piece (die-cut / matched pieces); buffering
is invisible space that keeps the cutter blade off the neighbour; static amounts apply when the order is processed, dynamic ones during marker making. A table whose length does not add up, with an unknown
type or a repeated rule number is refused.

## 20. Placed orientation - what a LAID marker says about how each piece lies [V, v4.13]

Three things, none of them the `0x2000` / `0x0080` bits of section 10 (those are the PRE-SET lay pattern of the unlaid marker and stay in the word when a nester lays the piece another way):

1. **The low three bits of the slot's orientation word** (`orient_L`) = the placed orientation: a turn (degrees counter-clockwise) and whether the piece is mirrored top-to-bottom BEFORE the turn.

| `L` | turn | mirror | | `L` | turn | mirror |
|---|---|---|---|---|---|---|
| 0 | 0 | no | | 2 | 90 | no |
| 4 | 180 | no | | 6 | 270 | no |
| 3 | 180 | yes | | 1 | 90 | yes |
| 7 | 0 | yes | | 5 | 270 | yes |

   (0 / 4 / 3 / 7 are the old rot0 / rot180 / flip-about-the-vertical-axis / flip-about-the-horizontal-axis; 1, 2, 5, 6 are the quarter turns the earlier reading called "unknown low bits".)
2. **A signed float32 at slot byte +38** = a further tilt in RADIANS, counter-clockwise, applied after the mirror and the turn (0 or -0.0 = none; -0.0 is what a nester writes, +0.0 is the default). AccuNest's
   CW / CCW Tilt Limit overrides (10 degrees) gave 10.000 degrees on the two collars that used them; the corpus marker `ZZN-B4` has +-3.0 and +1.5. Bytes +34..+37 stay `ff ff ff ff`.
3. **A quarter turn between a piece's stream outline and the frame the code refers to** (`frame`, per piece; `frame_offsets`). Only the COLLAR of the LADIES-BLOUSE set needs it (+90 counter-clockwise): its stream
   outline is 3.48 x 16.47 in and every placed collar, at every code and in every one of 28 markers (23 of the corpus, 5 fixtures), is 16.47 x 3.48; the other four pieces of the set and every other corpus piece need 0. The reader decides it from the
   marker's own home boxes (the quarter turn that predicts them better, by 0.25 in per slot at least). Why the collar differs is not known: the piece objects bundled with these markers are stubs, so its grain line
   cannot be compared (the stream's inferred grain is a 1.74 in horizontal segment for it); +90 and +270 cannot be told apart on a piece that is nearly symmetric under 180 degrees.

**The home box** (`home_x`, `home_y` = half of it) is the bounding box of the PLACED shape (turned, mirrored, tilted) plus the piece's block buffer turned with the shape [V]: the sleeve's Left 2.0 + Right 0.5 cm add 0.984 in
along x at 0 / 180 degrees and along y at 90 / 270; a collar tilted 10 degrees adds 2 x 0.1968 x (cos 10 + sin 10) = 0.456 in; every laid marker of the corpus passes the runtime check
(`orientation_check`, appended to `place_marker`'s `checks`: 40 laid markers, worst 0.018 in). `x`, `y` is the centre of that box. `transform(outline, slot, frame)` gives the placed shape.

**Proof.** Four AccuNest runs of a copy of `ZZC-M1` (Nest Markers overrides: Rotation 90 / 45 / 45 + tilt limits, Flip enabled; and the W-row run of `laylimits/EXPERIMENT_W_ALTERNATE.md`), each plotted to DXF:
72 placed slots, every decoded outline lies on its plotted loop (Hausdorff 0.16 in = the curve sag of the plot; the cuff rectangles 0.002), all eight `L` codes measured alone on 32 slots (`rotation/GROUND_TRUTH.json`).
Changing the rule breaks it: +180 on 56 slots, the mirror inverted on 48, the pre-4.13 rule on 47, no collar frame on 16, the tilt sign on both tilted collars. Over the 31 laid markers of the corpus the pre-4.13 reading has 1,707
overlapping pairs of placed pieces, this one 15 (three copies of one experiment with a hand-placed piece lying across others, and slots that touch within the buffer).

**Not seen, so not claimed.** A piece placed at 45 or another angle by a NESTER other than through the tilt limits: the Rotation-45 override made AccuNest place nothing off the 90-degree grid (18 slots), so there
is no marker in the corpus whose slot says 45. Easy Marking's rotate tools (its toolbox `Rotate` list: 45 CW / CCW, 90 CW / CCW, 180, Tilt CW / CCW, Variable, Reset Tilt, Power Rotate; applied by selecting the piece
with a left click and a right click, `Override` needed where the turned piece would touch a neighbour) were not driven to a stored marker. If a 45-degree turn is stored it can only be as a tilt of +-45 degrees on
top of `L`, since `L` has room for the eight orientations above and nothing else; that is an inference, not a reading.

## 21. Marker files in an AccuMark storage area [V, v4.13]

`<area>\mark\<Made | UnMade | Partial | NeedsApproval>\NAME.GT_mark` is 0x90 bytes of its own header (created / modified stamps at 0x6a / 0x6e, user names at 0x86) followed by the payload an export object
carries from 0x8a: slots, records, tables, stream outlines read identically (`ZZC-M1`: 18 slots, all records and tables equal to its export). `read_storage_marker(path)` rebuilds the export envelope around it and
`place_marker(path)` takes such a file. The state folder is the marker's own: a nest that ends "needs approval" (e.g. an angled marker border) leaves a partial marker there (`rotation/ZZROT-B.GT_mark`: 17 placed, 1 not).

## 22. The marker carries its own tables: sections 3 and 4, and the words of a piece row [V, v4.14]

A marker is made from an order, a Lay Limits table, a Notch Parameter Table, a Block Buffer table and an Annotation table, and it keeps COPIES of them as they were that day. Two of the copies are decoded:

**Section 3 = the Notch Parameter Table** (`accumark_notch.parse_notch_snapshot`). The bytes of the table object's payload, one for one (section 3's length is the table's: 144 for a table with one notch, 160, 304 for the real
`NEED-P-NOTCH`, 464 for the 25-notch `V-NOTCH-ALL CUSTOMERS`); 40 markers equal their bundled table byte for byte (the optional trailing zero dword is left out on 6 more). 16 markers of the scratch set (`ZZ-AM-*`,
`ZZN-*` ... - written by another path; why is not known) hold only its first 60 bytes: the five older-layout triplets (perimeter, inside, depth, x 10000 in) of notches 1-5, no type codes, no count - `notch 1` there is a slit of depth 0.1496 in (0.38 cm) where the
table now says 0.1574 (0.40 cm): the copy is the table AS IT WAS. The real markers' copies equal the real tables: 1825D, 5683D and 2591A hold `NEED-P-NOTCH` (15 numbers), 418T a 6-notch `P-NOTCH`, 2303 a 2-notch one
(sites keep different tables under the same name).

**Section 4 = the Lay Limits ROWS** (`accumark_laylimits.parse_snapshot_rows`), 12 bytes per row, in the table's order (row 0 = DEFAULT):

    +0  u16 flip code      +2  f64 tilt limit (the table's own unit; the two directions are one value here)      +10  u8 b2      +11  u8 b3     (the option bytes exactly as in the table, section 16)

No names, no buffer rule, no spread, no bundling: those stay in the table (and on the piece rows). 76 of 76 rows on the 56 markers that bundle their table have the same flip code, options and tilt.

**The piece row's words** (section 10, `<24 flag bytes>` = 12 u16 words w0..w11): **w1 = the piece's row of the Lay Limits table** (0 = DEFAULT: the row its category names, else DEFAULT), **w2 = the block-buffer entry**
(0-based, 0xffff none; as before), **w3 = the buffer rule number** of that row, **w4 = its flip code**, **w5, w6 = its tilt limit as an i32 x 10000** (the CUFF's 0.1574 in = 1574), w7 = the 0x0040 flag (section 10), w9 = the
fabric-type count; w0, w8, w10, w11 are 0. 287 of 287 piece rows on the 56 markers with a bundled table agree with the table (row index by category name, buffer rule, flip code). So **the marker states, per piece, the rotation
rule it was made with** - row options (section 4) at index w1 - without the table. What it does not carry: the row's NAME (a nester matches a piece to its row by the piece's row index, not by category) and the table's Bundling; the table's SPREAD is section 1's word at 520 (v4.16, section 23).

**Consequences.** (1) `nest_spec` of a marker-only ZIP reads its own rotation rules and notch sizes (`lay_limits.source` / `notch_table.source` = `marker snapshot`): the four real production markers no longer say `assumed` -
1825D / 5683D / 418T / 2591A are locked one-way (W + S), every piece fixed in its preset direction; the notch numbers of 2591A (1 and 5) are read from its own copy. With a bundled or supplied table as well, the two are
compared and a difference is reported (the table was edited after the marker was made): the real `NEED- TWO WAY` reads `MWS` today, and the 1825D / 5683D markers hold `WS` - consistent with a table edited after they were made (the `M` = major piece added).
(2) `ALL GMT WAY`, the table of 2591A that is not in any file: its DEFAULT row is `MWS`, flip code 1, no tilt - read from the marker; its Bundling still rests on the presets (all 0 = All Bundle, Same Direction). (3) Sections 3 and 4
and the piece words leave no unknown byte (`marker_coverage`); together with section 1's four counters (below) the unknown bytes per marker fall from 1,111-1,753 to 1,031-1,280 (1.06% of a marker).

**Section 1's counters** (file offsets 480 / 482 / 490 / 492, u16): the number of records (section 14), slots, models and size-table rows [V: 73 of 73 markers; `check_marker` row]. The other 40-odd varying section-1 bytes (a few
more counters, two constants of 3750 / 1476, a value 257 / 0, a 33280-33304 word) equal none of the quantities tried (sums over records, slots, streams, areas) and stay raw.

**Not decoded.** Section 5's first part is the Annotation table's copy in a packed form (row names without padding, then the field codes) - the format of the table itself is open, it does not affect a nest; section 2's 211 constant
bytes before the name strings and the trailer's filler (`00 01 01 02 00` repeated 27 times) are identical on every marker.

## 23. The spread and the major piece [V, v4.16]

**Spread.** Section 1's u16 at file offset 520 (section 1 + 216) is the SPREAD of the Lay Limits table the marker was made with: **0 single ply, 1 face to face, 2 book fold, 3 tubular** (the table's own byte, section 16).
Proved on four markers made from ONE order (`CLAUDE-D4`: model `CLAUDE-CURVE`, three sizes, one piece that is a `CUT X02` pair) with only the table changed (`spread/`: `L`, `ZZLL-F2F-R5`, `ZZLL-BOOKFOLD`, `ZZLL-X2` = words
0, 1, 2, 3) and on the 56 corpus markers that bundle their table (54 single ply, 2 face to face; 56 of 56 equal the table's spread). What a spread does to the marker: a **single-ply** marker lays the pair as TWO slots (the plain piece
and its mirror, slot bit `0x0080`; 6 slots for 3 sizes), each **two-ply spread lays it as ONE slot** (3 slots): the second ply is the mirror under it. The header's slot counters (+178, +180), the size-table rows and the
order copy (quantity 1 per size) do not change - only the slot table halves. So a nester of a two-ply marker lays each listed shape once and cuts it twice (`fabric.plies` = 2 in the nest spec).

**The major piece.** The piece-row flag @+14 (section 10; the slot bit `0x0040` is a copy of it) is the **M option** of the piece's Lay Limits row ("major piece": AccuNest places these first): 341 of 341 piece rows on the 78
markers whose row could be read (`M` in the row's options <=> flag 1). This closes the old question what sets it - no order or model option, and not the engine that wrote the marker (the earlier readings "0 in one marker, 1 in
another for the same pieces" were two different tables).

**Bundling.** Still not stored, but the presets it produces are: `nest_spec` lists the modes the stored bundle directions do not contradict (`lay_limits.bundling_candidates`) and, when one is left, states it as INFERRED
(`bundling_basis`): the real 2591A (all 7 sizes preset 0) -> All Bundle, Same Direction - the still-missing `ALL GMT WAY`; the fixtures `ZZLL-F2F-R5` and `ZZLL-BOOKFOLD` (all bundles preset alike) infer their own table's
mode correctly, and `ZZLL-X2` (tubular, same size same direction) leaves {alternate, same size} of which its own is one.

## 24. Flips and two-ply slots [V, v4.17]

**The flip bits.** A slot word's bits 0x0080 and 0x0100 are the piece's FLIP from the Model Editor's FLIPS columns (`--` as is, `X`, `Y`, `X,Y` = how many of the piece are cut as is / flipped about X / flipped about Y / flipped
about both): `0x0000` = `--`, `0x0080` = X, `0x0100` = Y, `0x0180` = X,Y. Until v4.17 only 0x0080 was known ("mirror"); 0x0100 had never occurred in the corpus (the decoder warned about it). Proved on one model (a copy of LADIES-BLOUSE
with the FLIPS of its five pieces edited three times, `twoply/`, 9 unmade markers + 4 placed ones): in every single-ply marker the slots of a piece in a bundle carry exactly the flips the model states (90 of 90 (bundle, piece) multisets),
including counts above one (3 as is, 2 + 2, 1 + 2). Geometry: **X and Y are mirror images, X,Y is the piece turned 180 degrees** (AccuMark's own flip vocabulary; on the sleeve, placed under a `MS` row, both engines kept it: AutoMark
14 of 14 slots, AccuNest 6 of 6). What a flip means to a nester is its RETRIEVAL DIRECTION as well: a Y or X,Y instance is retrieved turned 180 degrees (Y = X mirrored, then turned), and the direction composes with the bundle's 0x2000 bit
(`turn = 180 x (0x2000 XOR flip in {Y, X,Y})`, `slot['preset_turn_deg']`). On a row that may not rotate (`W`) AccuNest keeps it: **the rotation part of the placed orientation equals `preset_turn_deg` on 32 of 32 slots** (ZZLL-1WAY, every
row `MW`) **and on 8 of 8 front-piece slots** of an alternating table (ZZLL-1, FRONT = `MW`, the X,Y instance of bundle 1 comes out at 0). What neither engine keeps everywhere is the per-slot chirality: where the row is `MW` they lay as-is and
mirrored instances of one piece interchangeably (front piece: AutoMark 3 of 8 slots kept, AccuNest 9 of 16; sleeve on the all-`MW` table 2 of 6) - so the flips are a PRESET, not a constraint; whether the `S` option is what protects the sleeve
(its row is `MS`, and carries a 90-degree flip code) is not established. `slot['flip']`, `slot['preset_mirrored']`, `slot['preset_turn_deg']`;
`unplaced_inventory` `preset` = `{rot180, mirror (0x0080 only, as before), flip, mirrored, turn_deg, pair_bit, other}`; the nest spec's `demand[]` counts `mirrored` = X or Y (it was: bit 0x0080, so X,Y is no longer called
mirrored), and lists `flip_by_slot` and `preset_turn_deg_by_slot` (`allowed_deg_by_slot` turns from there).

**Two-ply spreads.** Section 23 said a two-ply marker lays a `CUT X02` pair as ONE slot. In terms of the flips (`twoply/`, face to face; book fold and tubular gave the same slots on the first configuration): **each as-is instance
of a piece in a bundle absorbs ONE flipped instance - the partner is the second ply - taking Y first, then X,Y, then X**: slots = pieces - min(`--`, X + Y + X,Y), and the surviving slots keep their own words (the absorbing `--` slot is
still `--`). Fifteen configurations (a, x, y, b) agree: (3,0,0,0) -> 3; (2,2,0,0) -> 2; (0,1,0,0) -> 1 (X); (2,0,0,0) -> 2; (1,1,1,1) -> `--`, X, X,Y (Y absorbed); (0,0,1,0) -> Y; (0,0,0,1) -> X,Y; (1,0,1,0) -> `--`; (0,1,1,0) -> X, Y
(nothing to absorb them); (1,0,0,1) -> `--`; (1,1,0,1) -> `--`, X; (1,1,1,0) -> `--`, X; (1,0,1,1) -> `--`, X,Y; (2,1,0,1) -> `--`, `--`; (1,2,0,0) -> `--`, X. So **a piece cut once (`CUT1`, a back, a single collar) keeps
one slot per garment in a two-ply marker** - nothing to absorb - and only a mirrored pair halves; there is no field for "pieces per garment" (the same section-10 word signature occurs for one-copy and two-copy pieces: e.g. 130 groups of each share the flags `0 / none / 0 0 0 0 / 1 / 0 0` on the single-ply markers of the corpus;
the record's cut text is the piece's annotation, e.g. `1 SELF` on a piece that lays as a pair), the slots ARE the demand. The header counters, size rows and order copy do not change. A nester of a two-ply marker lays each listed slot once; `fabric.plies` = 2 and `fabric.plies_note` say what a slot stands for.
**v4.18: larger counts agree** (`flipcount/`, 30 of 30 (bundle, piece) cases on the single-ply baseline, face to face and book fold, counts up to 4): (0,3,0,0) -> X, X, X; (2,3,0,0) -> `--`, `--`, X; (1,0,3,0) -> `--`, Y, Y;
(2,2,2,2) -> `--`, `--`, X, X, X,Y, X,Y (both Y absorbed first); (4,1,1,1) -> four `--` (all three flipped absorbed). [?] the number of plies a ply height multiplies a slot by is not stored in the marker.

**The composition with the bundle direction is proved (v4.18).** A rotating row hides the retrieval direction (the nester may turn the piece), so the test is a no-rotation row inside an alternating table: ZZLL-1's FRONT is `MW`, the model gave
the front piece (2,2,2,2) and AccuNest placed all 16 instances (`flipcount/`) at the rotation `turn = 180 x (0x2000 XOR flip in {Y, X,Y})` - every (bundle, flip) combination twice: `--` 0 / 180, X 0 / 180, Y 180 / **0**, X,Y 180 / **0** (bundle 0 / bundle 1). On this piece the
per-instance chirality was kept on 10 of 16 slots (the Y and X,Y instances of the alternating bundle came out swapped, as-is instances of a direction interchanged with mirrored ones).

**What is still open here.** Whether AccuNest's chirality swaps are its S-row / pair balancing or a choice of the Draft engine (the `S` option's role); the tubular spread differs from face to face only in its slot words (no 0x0040 bit here: the table's row has no `M`).

## 25. The area a Block adds [V, v4.19]

A block / buffer rule is a BUFFER (empty space, area unchanged) or a BLOCK (a visible area added to the piece); the marker keeps only the four amounts of each rule it uses (section 6) and never says which kind it is - **the slot's area does**. A PLACED slot of a piece
whose rule is a block stores (slot +42) its record's area plus the growth of the piece outline by a rectangle: **area(outline + R) - area(outline), R = (left + right) x (top + bottom) of the rule, in the piece's own frame, turned with the piece**. Only the two TOTALS matter (the
rectangle's position does not change an area). The marker's section 6 entry is `[left, right, top, bottom]` (the x pair, then the y pair) [V: rule 9 of `ZZBB-X1` = left 0.0433 / top 0.0866 / right 0.1299 / bottom 0.1732 reads back as 0.0433, 0.1299, 0.0866, 0.1732; the side-order question of section 22 / v4.12 is closed].

Proved on `blockarea/`: a copy of the ZZLL-1 table whose five rows all use that unequal block, the order of LADIES-BLOUSE, AutoMark - 18 placed slots of 5 pieces (back, collar, cuff, front, sleeve; 12.532 / 4.021 / 2.738 / 10.626 / 9.338 sq in added, the decoder's growth agrees to
0.004 sq in, the record and the stream outline themselves differ by 0.03), placed at 0 / 90 / 180 / 270 degrees and mirrored - and on the 1 cm equal block of the BACK piece in every earlier marker (ZZC-M3, ZZN-F1, the ZZROT set, ZZLL-EXP1: +44.095 stored, 44.09 computed). What does NOT
explain it: a uniform offset of the outline (652.9 against 657.64, the number the v4.12 note quoted), the totals swapped (11.47 against 12.53 on the back piece), a square of either total, the convex hull grown, or the bounding box grown. **The home box follows the same totals:** the
placed outline's bounding box plus (left + right) along the piece's x and (top + bottom) along its y, turned with the piece - x pad 0.1732 at 0 / 180 degrees, 0.2598 at 90 / 270 (the collar's stream frame is a quarter turn from its orientation frame, section 20, so its pads swap: 0.2598 x 0.1732 at 0).
The slots' declared areas include the block, hence the header's placed-area sum (@430) and the utilisation do too (their check rows pass on the blocked markers).

`_explain_block_areas` (called by `parse_marker`) tries this for every slot whose area exceeds its record's and whose piece has a rule with non-zero totals: when the growth explains it, `binding['area_ok']` is true and `binding['block_added']` holds the growth
(also `unplaced_inventory` `slots[].block_added`) - so the two old failed check rows / warnings of ZZC-M3 and ZZN-F1 are gone; a slot whose area is neither the record's nor the block's still fails. `rect_growth(points, wx, wy)` is the pure-Python scanline routine (error under 0.005 sq in).
[?] percentage amounts (a share of the plaid / stripe repeat) and the Segment amount were not placed on a marker; a block on an unplaced slot (its area stays the record's until it is laid).

## 26. More of section 1 [V / ?, v4.20]

Section 1 is 372 bytes (file offsets 304-675). Twelve of its words vary from marker to marker beyond the width, length and area scalars; before v4.20 four counters and the spread were known (sections 22 and 23). Found by correlating every word with the counts the decoder can compute over the 98 markers of the corpus and the fixture folders
(offline; no live round):

| word (file offset) | meaning | status |
|---|---|---|
| @486 | the number of pieces (section 10) **+ 1** | [V] 97 of 97 markers with a section 1 of this size |
| @496 | the rows of the marker's own Lay Limits table (section 4; 0 when the marker has none) | [V] 97 of 97 |
| @498 | the entries of the block-buffer table (section 6) | [V] 97 of 97 |
| @568 | 128 on every marker **AccuNest** nested (8 of 8 fixtures, and the corpus's AccuNest markers), 0 on an unmade or AutoMark-made marker (8 of 8); 64 on the July CP 150 marker | [V] correlation, `mk['nested_by']` |
| @674 | 3 after AccuNest (8 of 8), 19 on an unmade or AutoMark-made marker (8 of 8); 6 / 9 / 12 on the corpus markers nested more than once (`ZZN-1`, `ZZN-B1`, `ZZN-C1`) - a count of engine passes? | [V] for 3 / 19, [?] for the rest |
| @472 | the **attribute points** of the laid slots' streams: notch points (type 1-5) plus the turn points that carry a number 1, summed over the slots. Per slot on the LADIES-BLOUSE set: back 5, collar 1, cuff 0, front 1, sleeve 4; on the CLAUDE-CURVE piece the number of its notches (2, or 9 on the notch fixture) | [V] 29 of 29 fixture markers and about 45 of the 51 distinct real ones; exceptions: the 2303 markers (0 / 6 against 186 / 216 notch points: older vintage), `LADIES-BLOUSE TEST-2` / `ZZN-*` (204 against 90), `CLAUDE-D2-E7B` (27 against 61) and the tubular `ZZQ-T` (38 against 62: the sleeve, 24 points, is not in the count - the one marker whose Process ended "with warnings") |
| @476 | another per-slot count, exact per piece on the 19 LADIES-BLOUSE fixtures (back 10, collar 8, cuff 4, front 8, sleeve 4; the CLAUDE-CURVE piece 10; the same tubular shortfall of 24); the sharp corners of the outline give 8 / 4 / 4 / 8 / 4, the stream's turn points do not | [?] rule unknown |
| @484 | = slots - c: it falls with a two-ply merge exactly as the slot count does (54 -> 38 slots: 40 -> 24) but c (5 on ZZC-M1, 14 on ZZR-S / ZZR-B, 0 on the single-piece markers) is not explained | [?] |
| @488 | 103 on an as-generated marker and 112 once it has been laid (the same order, ZZR-K -> ZZR-KA), other values on other markers | [?] |
| @530 | grows with the notches (20 -> 41 per slot for +7 notches on the curve piece: 3 per notch) and the points; no fit | [?] |
| @168.. / @202 / @264 / @672 | see MARKER_FORMAT_SPEC.md section 13 (byte map); not reduced | [?] |

`mk['header_counts2']` (pieces + 1, lay rows, block entries), `mk['engine_words']` and `mk['nested_by']` (`accunest` / `automark or none` / `other (n)`), a check row (the three counters equal what the sections hold), and the byte map marks the five words as identified.

## 27. The tilt limit and the Piece Options [V, v4.21]

**The marker keeps ONE tilt: the smaller of the table's two limits.** A Lay Limits row has a clockwise and a counter-clockwise tilt limit (`tilt/`: a copy of ZZLL-1 with unequal limits, made into markers with the Order Editor): the marker's section-4 row holds one f64, and the piece row's tilt words (w5-6, i32 x 1e4) the same number.
Rows and what was stored (cw / ccw in the table -> the marker): back 0.5 / 0.2 cm -> 0.0787 in; collar 5 / 10 degrees -> 5.0 (b2 bit 0x20 set: the unit is degrees); cuff 0.3 / 0.5 cm -> 0.1181 in; front 20 / 15 cm -> 5.9055 in; and with a ZERO side (cuff 0 / 0.4, sleeve 0.3 / 0) -> 0.
So `min(cw, ccw)`, in inches for a length and in degrees for the degree unit. A nester reading a marker-only ZIP sees both directions equal to the smaller limit: **that is stricter than the table** when the two differ, and the real table (bundled or supplied) is the source when the two directions matter.
The nest spec adds a `note` to `tilt_limit` from a marker's own copy, and `_snapshot_diff` compares the marker's tilt with `min(cw, ccw)` (before: with either).

**The twelve Piece Options** (read from the checklist of the Lay Limits Editor, 2026-09-25): M Major Piece; W One Way Piece, Flip in X-axis, No Rotation; S Allow 180 degree rotation, No Flip; 9 Allow 90 degree rotation; 4 Allow 45 degree rotation; F Allow folds for mirrored pieces; O Optional piece (placing will not be required);
N Do not plot this piece; X Do not cut this piece; P Pair orientation maintained; U Will not include this area in marker; Z Piece can be completely inside a splice mark. The decoder's `orientation_rules` (`flip_x_axis_allowed = 'S' not in options`, W removes the rotation, S the flip) was already this; the checklist is the ground truth.

**What S does to a marker** (closes the open question of sections 23 / 24 - why AccuNest and AutoMark laid as-is instances mirrored and mirrored ones as is): **a row WITHOUT `S` allows the flip, and the engines then treat the mirrored / as-is instances of a piece as interchangeable - even their
number is not kept (48 of 102 (piece, size) groups differ); a row WITH `S` (no flip) keeps every slot's chirality.** Over 42 placed markers (the corpus and the fixtures), 1,240 slots of pieces that are not their own mirror image: rows with S kept the chirality on 905 of 922 slots (the 17 exceptions are the `ZZROT-*` AccuNest runs, which ticked the
"Flip: Enable" override that lifts the row's S; without them 100%), rows without S on 188 of 314 (60%; with W 46%). In the fixtures used by `selftest` (no override): 38 of 38 against 24 of 50. So the mirrored flags of the model are a PRESET on a flip-allowed row and a constraint on an S row: the nest spec's `demand[].mirror_binding` says
`kept` (the row has S) or `free`.

## 28. A 45-degree placement, and two more words of section 1 [V, v4.22]

**A 45-degree placement is a tilt of exactly +-45.0 degrees on top of the orientation code.** Made with my own processes (`deg45/`): a copy of ZZLL-1 whose rows all say `MW` (one way: no rotation, so the nester keeps the piece in its initial orientation) with the 45-degree flip codes - the Lay Limits
Editor's own list is `1` Original Digitized Position, `2` Rotate 180, `3` Flip about Y-axis, `4` Flip about X-axis, `5` Rotate 90 CCW + Flip X, `6` Rotate 90 CCW, `7` Rotate 90 CW, `8` Rotate 90 CW + Flip X, `9` Rotate 45 CCW + Flip X, `10` Rotate 45 CCW, `11` Rotate 45 CW, `12` Rotate 45 CW + Flip X - on FRONT (11), BACK (9),
COLLAR (10), CUFF (12), SLEEVE (7). The unmade marker keeps the codes in its PIECE rows only (no trace in the slots, as with every flip code). AccuNest (Draft, no overrides) laid every piece in its initial orientation: **the slot's float at +38 is +45.0 (one front slot -45.0) on the back, collar, cuff and front
slots, 0 on the 90-degree sleeve, and the low three bits keep the mirror and quarter turn** - the rule of section 20 (mirror, turn, then tilt, counter-clockwise) unchanged. The decoded outlines lie on the MarkPlot plot to 0.16 in (curve sag; the cuff 0.001) on all 18 slots, with the tilt ignored or inverted missing by 3 to 11 in.
So no separate encoding exists for 45 degrees: the Rotation 45 override of AccuNest simply places nothing off the 90-degree grid, but a `W` row with a 45-degree code does. `tilt_deg` 45.0 is what a nester or reader sees; nothing in the marker says whether it came from a code or a tilt limit.
**What the stored boxes cannot say:** a thin piece tilted by 45 degrees has the same bounding box from a 0- or a 90-degree stream frame, so `frame_offsets` (home-box based) cannot decide it: the LADIES-BLOUSE collar (+90, section 20) came out at frame 0 here and missed its plotted loop by 7.1 in (0.16 in with its frame). `frame_ambiguous` names the pieces whose
frame the boxes cannot decide (back, collar and cuff here; none on any earlier marker), `mk['frames_ambiguous']` and a warning in `place_marker`'s inventory carry it. The collar's record has no grain line (its stream carries an extra tag 0x46 and its grain is 'inferred'), which may be why its frame differs; no field of the record states it [?].

**Two more words of section 1** (section 26): **@472 = the sum, over the slots, of the record's `prefix[3]`, and @476 = the sum of `prefix[4]`** (76 of 100 markers exactly; 33 of 33 fixture markers but the tubular `ZZQ-T`). `prefix[3]` is the number of attribute points of the record's stream (notch points + numbered turn points: 1,241 of 1,319 records, 94%): back 5, collar 1,
cuff 0, front 1, sleeve 4; `prefix[4]` is another point count (back 10, collar 8, cuff 4, front 8, sleeve 4; the curve piece 10 - not the stream's turn points). The exceptions: the 2303 markers (older vintage), some 54-slot markers where the words are twice the sum (`LADIES-BLOUSE TEST-2`, `ZZ-AM-1`), `CLAUDE-D2-E7B`, and the
tubular `ZZQ-T` (short by the sleeve). The prefix words 0-2 are still unexplained (words 0 / 1 differ by 2 x (words 2) + 2 on the LADIES-BLOUSE set?).

## 29. Every marker on this machine, plaid / stripe data, and the engine's own input file [V / ?, v4.23]

**The scan.** Every `.GT_mark` of every storage area of this machine (219 files, 211 unique: `ZZ-CLAUDE-SCRATCH` 108, `OLDFiles` 80, `DATA90` 8, `Dataset` 8, `CLD` 3, `Test` 3, `3D-DemoFiles` 1; read-only, straight from the storage files) went through `parse_marker`, `check_marker`,
`marker_warnings` and `coverage_warnings`: **no exception on any**, 176 fully clean, laid 136 / unlaid 65 / partial 10. What the scan found, and what was done:
* **`OLDFiles` (80 real older production markers, `4787S-209-... CM 16500 OGOW 14P` and the like):** the order copy of that vintage lists every size of the model, the unused ones with quantity 0 (`XS 0`, `XXXL 0`), and the check "order copy tiles section 15; quantity == size-row count" wrongly failed on 64 of them: a size ordered 0 times has no size-table row. Fixed (v4.23);
  the nest spec's `order_lines` no longer lists sizes ordered 0 times. The slot `@88` rule of v4.7 (record head count + one constant per piece) holds only to within 2 on a real production piece (`4787S SIDE`: 94 on XS, 96 on the others - `@88` follows the graded size, `prefix[1]` does not do so exactly): a spread of up to 2 is accepted, a wider one still fails.
* **Plaid / stripe:** the order's plaid and stripe values are **twelve f64 (inches) of section 1, just before the width: stripe offsets @300 / 308 / 316, stripe repeats @324 / 332 / 340, plaid offsets @348 / 356 / 364, plaid repeats @372 / 380 / 388** (`mk['plaid_stripe']`, `mk['has_plaid_stripe']`; the nest spec's `fabric.plaid_stripe` in the spec's units).
  [V: the ZZP* set of 2026-09-22, made with stripe repeat 10 cm / offset 1 cm and plaid repeat 12 cm / offset 2 cm: 3.937 / 0.3937 / 4.7244 / 0.7874 in; the two stripe-less runs ZZPU / ZZPV read 0]. The first double overlaps the two directory "state words" (40 / 41), which is why 27 markers of that set showed
  `directory word 41 is 0x32617c1b` - not a state. `has_plaid_stripe` is true on exactly those 27 of 211 markers.
* **Plaid / stripe MATCHING** (a Matching table on the order: piece-to-piece and fabric rules; decoded in v4.25, section 31): three more directory slots are used - **9 (168 bytes), 23 (14 bytes) and 24 (504 bytes = 42 records of 12: u16 a, i32 -1, u16 1, u16 b, u16 c)** on the 25 markers made with a table - and the rules themselves are NOT decoded [?]. They are named
  (`MATCHING_SECTIONS`; a warning "the marker carries plaid / stripe MATCHING data ... not decoded and not in the nest spec"), bounded as `opaque` in the byte map, and the nest spec keeps its `warnings`. The ground truth for a later decode is on this machine: the table objects (`match/ZZ-PLAID*.GT_match`, 250-401 bytes), the orders, and the
  **engine input file `frommed.mra`** (below). `plaid/` holds ZZP1-M, ZZPH-M, the table ZZ-PLAID and job 117's file.
* One old sample marker (`DATA90` LADIES-BLOUSE) still warns by name (sections 9 and 16 in use, the record index not validating, slots bound by area): an older vintage; the real user markers (`CLD`, `Dataset`) are clean except `4155B LACE 30`, a partly laid marker with a stale header (the known kind).

**The engine's own input file** (a resource, not yet a test): for every AccuNest job `C:\Users\Public\Gerber Technology\Queue\ultramrk_umq\<job>\frommed.mra` is plain text written by the front end from the marker + order + tables: `MARKER_NAME`, `MARKER_WIDTH`, `GLOBAL_GAP`, `TUBE_FLAG`, `SPREAD`, `MATCHING_TYPE`, the STRIPE / PLAID
(offset, repeat) lists in 1e-4 inch (`(7874,47244)` = offset 2 cm, repeat 12 cm), per style-piece `NAP_GROUP`, `FLIP_GROUP`, `CW_TILT_LIMIT`, `CCW_TILT_LIMIT`, `ROTATE_INCR`, `FOLDABLE_FLAG`, `BUNDLE_GROUP`, per size `REPEAT_COUNT`, per piece instance `BUNDLE_ID`, `ANGLE`, `FLIP_FLAG`, `AM_AREA`, `LOCATION`, the outline points, and per piece the
matching rules (`MATCHING_RULE_TYPE` 1 fabric / 0 piece, `MATCH_FIRST`, `MATCHING_POINT`, `MATCHING_TYPE_X / _Y` 0 Relative / 1 None / 2 Same, `MATCHING_OFFSET`). It is an independent rendering of everything a nest spec must say - 100+ jobs of my earlier sessions are still there. Used as a check since v4.24: section 30.

## 30. The engine's own input file (`frommed.mra`) as a check of the job spec [V, v4.24]

`accumark_engine.py` reads it (`read_engine_file(path)` -> `header`, `style_pieces`, `sizes`, `size_pieces`, `pieces`; `engine_flags(options)`). The four jobs of `engine/` were made from `twoply/ZZQ-W`, `twoply/ZZQ-A`, `flipcount/ZZR-S` and `deg45/ZZR-45` (jobs 266, 269, 272, 275); 73 more jobs on this machine were used for the counts below.

**Layout and units.** Plain text `KEY value`. Header (`MARKER_NAME`, `MARKER_WIDTH`, `GLOBAL_GAP`, `SPREAD`, `PIECE_COUNT`, `BUNDLE_COUNT`, `TILT_INCR`, `ROTATE_INCR` ...), one `BEGIN_ST_PC` per CATEGORY (`PIECE_NAME` = the category, e.g. `BACK`), one `BEGIN_SIZE`, one `BEGIN_ST_PC_SZ`, then one `BEGIN_PIECE` per marker slot, **in slot order**
(`PIECE_COUNT` = slots; `SPREAD` = the section-1 word @520; `MARKER_WIDTH` = the marker width). Lengths and outline points: 1e-4 inch; `AM_AREA`: 1e-3 square inch; `ANGLE`: 1e-2 degree (counter-clockwise, mirror first); tilt limits: 1e-1 degree; an unplaced piece has `LOCATION` about (-1000, -1000) inch.

**1. Retrieval orientation = `ANGLE` / `FLIP_FLAG` [V].** `accumark_laylimits.retrieval_orientation(flip, alt, code)` = the row's flip code (`code_transform`: mirror first, then turn ccw; a code that rotates and flips - 5, 8, 9, 12 - rotates first) composed onto the model flip (`--`, X, Y, X,Y: X and Y mirror, Y and X,Y add a half turn) and the bundle direction (0x2000 = another half turn):
`mirrored = (flip in X,Y) != (code mirrors)`; `angle = (turn(code) + (-p if code mirrors else p)) mod 360` with `p = 180` when `(0x2000 set) != (flip in Y, X,Y)`. **136 of 136 instances of the four fixture jobs agree, and 3,460 of 3,508 over 73 jobs (codes 1, 7, 9, 10, 11, 12, every flip and bundle combination).** The 48 exceptions are all in job 71 (`ZZN-B4`), a LAID marker: there `ANGLE` is the
placed angle (the slot's tilt float included: 44 of its 54 agree with retrieval + tilt), not the retrieval angle. `nest_spec` now reports exactly this: `demand[].mirrored` = `FLIP_FLAG`, `retrieval_deg_by_slot` = `ANGLE`, `allowed_deg_by_slot` turn from there (a `W` row with code 7 is fixed at 270, not 0). This corrects v4.17-v4.23, where `mirrored` was only the model flip and the row's code was ignored.

**2. Per-category flags follow the Piece Options [V: 20 of 20 style pieces of the four jobs; 19 (options, code, unit, spread) combinations over all jobs].** `NAP_GROUP` 2 when the row has `W`, else 0; `FLIP_GROUP` 2 when it has `S`, else 0; `ROTATE_INCR` 0 for `W`, 45 for `4`, 90 for `9`, else 180 (`MS` keeps 180: S allows the half turn); `FOLDABLE_FLAG` always 0, `BUNDLE_GROUP` always empty (the Bundling option does not reach the categories: it is in the slots' 0x2000 bits).
Exception: a row with `S` shows `FLIP_GROUP` 0 in 7 of the 37 jobs that have one - 4 are the `Flip: Enable` override of the job, 3 unexplained (section 34). Tilt limits: `CW_TILT_LIMIT` = -`CCW_TILT_LIMIT`, 0 when the table's tilt is 0; a table tilt of 0.1574 in became +-2 (0.2 degree) in a 55 in marker [?: one data point, the conversion from a length to an angle is not decoded], a Nest Markers Tilt Limit override of 10 / 3 degrees became +-100 / +-30.
`GLOBAL_GAP` is the piece gap in inches (0.01181 = 0.03 cm), set by the job's `Piece Gap` override (section 34).

**3. Areas and outlines [V].** `AM_AREA` equals the slot's area on 353 of 360 piece kinds over all jobs (17 of 20 in the four; the other three are the BACK piece of `ZZQ-A` / `ZZR-S` / `ZZR-45`, where it equals the BUFFERED outline area: 657.638 = 613.543 + 44.09). The engine's outline points (`points_in`, in the piece's home frame) are **the piece plus its block buffer**: their area minus the decoded outline's area
equals `rect_growth(outline, L + R, T + B)` (the v4.19 rectangle dilation) within 1.5% on all 20 kinds (worst 0.4%: curve sampling), including the unequal `[0.7874, 0.1968, 0, 0]` sleeve and the piece with no rule (growth 0). This confirms the block model independently: the front end applies EVERY block-buffer entry to the piece as a rectangle dilation, whatever the marker's word says about Block or Buffer, and passes the piece gap separately (`GLOBAL_GAP`). Section 32 extends this to 223 pieces of 73 jobs and nine amounts, and to the frame.

**Not used yet [?]:** the matching rules of each piece (`MATCHING_RULE_TYPE`, `MATCH_FIRST`, `MATCHING_POINT`, `MATCHING_TYPE_X / _Y`, `MATCHING_OFFSET`) - the ground truth for sections 9 / 23 / 24 (plan item 11); the per-piece `FOLD_LINE`, `RIGHT_FLAG`, `BUNDLE_ID` (97 in every fixture: a per-size constant?).

## 31. Plaid / stripe matching rules: sections 9, 23, 24 [V, v4.25]

Present on every marker made with a Matching table (25 of the 219 marker files on this machine, all mine: `ZZP*`, `ZZC20-*`). `parse_matching(d, mk)` -> `mk['matching']` = `rules`, `blocks`, `bundles`, `categories`, `ok`, `problems`; `matching_for_category(matching, category, bundle)` lists the rules a piece takes part in, in the engine's order.
**Verified against the engine's own input file** (`frommed.mra`, section 30) for 22 AccuNest jobs: every rule (kind, role, X / Y type, offset) of 816 piece instances and every one of 1,264 rule points equal the engine's (worst 0.0001 in); the five markers in `plaid/` are the selftest fixtures (204 instances, 310 points). All three sections use the "-6" frame: the first record's first 6 bytes sit BEFORE the section.

* **Section 9 = the RULES**, one 42-byte record each, cut 6 bytes early: `[u16 first point][u16 second point][u16 rule index (0xffff on a fabric rule)]`, then `[u16 second block][u16 first category][u16 second category][u16 X type][u16 Y type][f64 offset x][f64 offset y]`, 2 zero bytes, `[u16 1 on a fabric rule, else 0]`, 6 zero bytes; the last row's
  final 6 bytes are an end triple `(0, 6, 1)` [?]. **Category 0 = the MARKER** (a fabric rule: a point of a piece matched to the plaid of the fabric; the marker is its first side), 1.. = the categories in the order of the piece list. Types: **0 relative, 1 none, 2 same** (the engine's `MATCHING_TYPE_X / _Y`); offsets in inches (a 3 cm relative offset = 1.1811). The rule points are point NUMBERS of the pieces (`PFRONT 3 - PBACK 3`).
* **Section 24 = the BLOCKS**: for every point a rule uses (category, point number), one 10-byte item per bundle: `[i32 -1][u16 category][u16 bundle][u16 point number][u16 vertex]`, the first item's leading bytes being the 6 before the section and the vertex of each item sitting in the FIRST two bytes of the next 12-byte record; an item `(0, 0, 0)` ends the list.
  Records = blocks x bundles (bundle = the size-table row; ten in `ZZC20-STD`). **The vertex is the point's 0-based index in the piece's outline (the section-14 stream order): the engine's `MATCHING_POINT` = that vertex less the middle of the piece's (unbuffered) box, in the piece's own frame and NOT mirrored** (a flipped instance carries the same point and `FLIP_FLAG`) - so point number != vertex
  (`PPOCKET 1` = vertex 0, `PFRONT 2..5` = vertices 2..5) and the marker gives both. A rule's second piece is `blocks[second block]`; the first piece's block is the one for (first category, first point).
* **Section 23 = the block start offsets** (in items: 0, B, 2B ...): the first three in the 6 bytes before the section, the rest in it, then the first item `(1, 0, point)` again [V: 25 of 25 markers].
* **What the engine does with them** (per piece instance, in rule order): `MATCHING_RULE_TYPE` 1 fabric / 0 piece, `MATCH_FIRST` 1 when the piece is the rule's first piece else 2, the two types, the offset, the point. **A stale block** is possible: `ZZP2-M` / `ZZP3-M` list `PBACK 5` as a block that no rule uses; the engine ignores it.
* **Not decoded / not verified [?]:** the end triple, the unknown bytes that a fabric rule's flag word stands for; **the offset Y is verified since v4.32** (live: a table with Relative stripe offsets of 2 and 1.5 cm read back as `f64` +18 = 0.7874 / 0.5906 in and as the engine's `MATCHING_OFFSET` y = 7874 / 5906, `MATCHING_TYPE_Y` relative; `plaid/ZZPQ-M`); the marker point of a fabric rule (`Marker pt 2`) has no coordinates anywhere (it is a point of the plaid, not a piece); what AccuNest HONOURS is a separate question (plaid-matching.md of the skill: the fabric anchor
  rule, 2-D pocket rule and relative offsets were not honoured in one run, some combinations end in `ERROR 1006 Bad nest file`).

## 32. The engine's outline: the buffer rectangle and the frame [V, v4.26]

What AccuNest is handed for a piece (`frommed.mra`, section 30) set against the marker's own stream outline (section 14, unfolded for a fold piece), on 27 pieces of the six jobs in `engine/`, `plaid/` and the fixture folders, and on 223 pieces of 73 jobs on this machine.
* **The buffer is a rectangle grown about the middle of the box.** The engine's outline is the stream outline grown by the marker's section-6 entry as a RECTANGLE `(L + R) x (T + B)` (the v4.19 rectangle dilation), **symmetrically**: half of `L + R` on each side in x, half of `T + B` in y (the sleeve's unequal `(0.7874, 0.1968, 0, 0)` grows +-0.4921 in x, 0 in y). Its box is the stream box grown by exactly that (to 0.0001 in) and its area growth equals `rect_growth`
  within 2% (curve sampling). **Whatever the rule's kind:** the nine amounts seen (none; 0.0059, 0.0118, 0.0393, 0.059 and 0.3937 in on every side; `(0.7874, 0.1968, 0, 0)`; the real `3MM` Buffer of 0.15 cm = 0.059 in among them) all behave the same, so the front end turns every entry, Buffer or Block, into piece growth. The **piece gap** (`GLOBAL_GAP`, 0 / 0.01181 / 0.3937 in in the jobs seen) is a separate job
  setting: it does not change the polygon and is not in the marker. A consumer that wants what the engine nests grows each shape's `outline` by the rectangle (the convex hull of every edge swept by the rectangle - not a rounded offset).
* **The frame.** The engine's outline is in the piece's own frame (the frame the orientation code refers to), origin at the middle of the (unbuffered) box. **One piece is turned in it against the stream: the LADIES-BLOUSE COLLAR (a fold piece, 3.48 x 16.47 in in the stream), by +90 degrees counter-clockwise** - its engine outline is 0.28 in (the corner of the buffer) from the stream outline turned +90 and 0.98 in from the one turned 270,
  so the sign v4.13 could not tell from the home boxes is settled (the ambiguity of `frame_offsets` for a piece symmetric under 180 degrees does not arise for this collar). Every other piece is in the stream frame (BACK, FRONT, SLEEVE, CUFF and the four `ZZPLD` pieces: 27 of 27 with the collar). **What FLAGS the turn is known since v4.33 - bit 0x0200 of the slot word @+60, section 36; WHY the engine turns the piece is still open [?]** (best hypothesis, live 2026-09-25: the engine frame is the grain-aligned one and the stream frame is the piece's stored one - the Model Editor's thumbnail of the LADIES-BLOUSE collar is tall with a vertical line, of every V17-made piece wide with a horizontal one; a vertical-grain piece cannot be made with V17 tools: DCU import turns the grain to x, and a PDS Rotate 90 / 180 of the collar, saved, came back with UNROTATED geometry and engine frame 0 - the rotation is not stored in the piece, scratch pieces `ZZC-VCCW` / `ZZC-VCW`; so only legacy AccuMark 9 pieces show it) - what the turn does NOT follow: not the aspect (the `ZZPLD` POCKET, 3.07 x 3.94 in, is taller than wide and is
  not turned), not the grain line (the collar's is a short horizontal segment in the stream), not the fold line (the BACK is a fold piece too). The engine's `FOLD_LINE` (BACK `(-16.583, 0)`, COLLAR `(-0.0001, -0.9245)` in inches) = **the first point of the piece's fold (mirror) line, measured from the middle of the unbuffered box in the engine's frame** [V: the two pieces whose stream carries the mirror line, ACCUPLAN-M-04 BACK `(-16.4851, 0)` and MARKERB BACK `(1.9765, -0.0026)`, equal `mirror[0]` less the box centre; the engine file has it for every fold piece of 73 jobs]. In the stream frame the collar's fold starts at about `(-0.92, 0)`, i.e. the fold is horizontal there like the BACK's, so the turn is not made to put the fold in a fixed direction either.

## 33. The engine's fabric weight and cost; what is still unidentified [V / ?, v4.27]

* **Two float32 in section 1: the fabric WEIGHT at file offset 596 (section 1 + 292) and the COST at 600 (+ 296)** [V: equal to the `FABRIC_WEIGHT` / `FABRIC_COST` of the engine's own output header (`intomed.mra`) on 49 of 49 jobs whose marker is the one the job wrote; `engine/INTOMED_HEADERS.json` keeps five]. An unmade marker holds 0 / 0 (the front end passes them on to the engine as `FABRIC_COST 0`); AccuNest
  writes back its own 0.029493 / 0.914402 unless the job gives others (`ZZN-B5`, job 74: 11.43 / 5.8987, the user's values from the Nest Markers dialog [?]). Units (v4.30, section 34): the dialog's cost per metre x 0.9144 = per yard, weight in gsm x 0.029493 = oz per sq yd. `mk['fabric_weight_cost']`.
* **The byte map now separates the bytes that are ZERO** (`zero`: unidentified, zero, outside the parsed sections - they carry no information in that marker) **from the unidentified non-zero ones** (`unknown`): 105-371 unidentified non-zero bytes per fixture marker (0.21%; 933-1,182 before, when the zero bytes counted). Inside the parsed sections nothing changes: an unidentified byte stays `unknown` whatever its value. Also identified now: @472 / @476.
* **What is left (non-zero, not identified), by frequency over 114 markers:** the envelope byte 16 (`0x31` on all); section 1 @404 / @438 (identified in v4.31: the order's Target Length and Target Utilization, section 35), @484 / @488 / @494 (bytes, 7-27 values), @504 (5 on all), @522 / @530
  (words, 2-34 values), @588 (`01 01 01 01` and a word `0x8018` / `0x8218`: an engine state word), @604 (1 on 73); section 2 two constants (`0x01` before, `0x31` at +230); section 10's two lead constants (`06`, `01`); **section 5** (the Annotation table copy: `DEFAULT`, `MARKER`, `LABEL` style records with font / size bytes; 10 KB over the corpus, 14 layouts) - its structure is open.
  None of them changes what a nester needs; each is bounded.

## 34. The job's own settings and the flags the engine gets [V, v4.30]

Everything in the marker and the tables is not all the engine hears: the Queue job also carries what the **Nest Markers dialog** said, in the `Job Settings` block of the job's `nestserv.log` (`accumark_engine.parse_job_settings`). It settles the open points of section 30 (checked on the 73 jobs of this machine; 40 style pieces of the eight jobs in `engine/` are tests):
* **Overrides** (block `8. Overrides`): `Rotation N` gives EVERY category a rotation step of N degrees and drops its one-way flag (`NAP_GROUP` 0, `ROTATE_INCR` N - a `MW` row under `Rotation 45` becomes a free 45-degree piece); `Flip: Enable` clears the no-flip group of every category (`FLIP_GROUP` 0 although the row has `S`); a tilt override of n degrees gives every category
  `CW_TILT_LIMIT` -10 n and `CCW_TILT_LIMIT` +10 n (0.1 degree: 10 degrees = 100, 3 degrees = 30, whatever the table says); `Piece Gap` c cm is the job's `GLOBAL_GAP` = c / 2.54 in (0.03 cm = 0.01181, 1 cm = 0.3937; jobs 174 and 29); `Marker Border Angle` changes no flag. `accumark_engine.engine_flags(options, overrides)` computes all of it.
  That explains 4 of the 7 jobs with an `S` row and `FLIP_GROUP` 0 (jobs 35, 254, 257, 260: `Flip: Enable`); the other 3 (216, 218, 221: `MWS` rows, no override) are probably a Lay Limits table edited after the marker was made (the engine reads the table when the job is submitted) [?]. Without an override the engine converts the table's tilt itself: -round(10 cw) / +round(10 ccw), inches or degrees as they stand (section 35).
* **Fabric options** (block `9. Fabric Options`, the dialog's `Fabric Cost` per metre and `Fabric Weight` in gsm; defaults 1.0 / 1.0): the engine stores them per yard and in ounces per square yard - **cost x 0.9144, weight x 0.029493** [V: 5 jobs: 12.5 -> 11.43, 200.003 -> 5.8987, 1 -> 0.914402 / 0.029493] - and AccuNest writes those into the marker (section 33, @596 / @600). So the units of section 33 are per yard and oz / sq yd.
* `ZZROT-B`'s engine file (the `Marker Border Angle` 30 run, a partial marker) lists a sixth style piece with a blank name that the marker does not have [?].

## 35. The tilt limits the engine takes, and the order's Target Length / Target Utilization [V, v4.31, live]

Two AccuNest jobs of my own (jobs 278 and 281, 2026-09-25): a copy of an order with 7 sizes x 2 of `LADIES-BLOUSE`, the table `tilt/ZZLL-TLT` (unequal clockwise / counter-clockwise tilts in cm and in degrees), at fabric widths 140 and 100 cm, Draft, no overrides; the engine's `frommed.mra` style pieces are in `engine/TILT_JOBS.json`.
* **Tilt.** The engine does not read the marker's single tilt (section 4 / the piece row keep the smaller of the two sides, 0 when either is 0: section 27): it reads the **Lay Limits table itself**, each side on its own, and writes `CW_TILT_LIMIT = -round(10 x cw)`, `CCW_TILT_LIMIT = +round(10 x ccw)` (0.1 degree) with cw / ccw the table's numbers **in inches (a length tilt) or degrees, used as they are**: FRONT 20 / 15 cm
  (7.874 / 5.9055 in) -> -79 / +59; BACK 0.5 / 0.2 cm -> -2 / +1; COLLAR 5 / 10 degrees -> -50 / +100; CUFF 0 / 0.4 cm -> 0 / +2; SLEEVE 0.3 / 0 cm -> -1 / 0 (10 of 10 categories of both jobs; and the older 0.1574 in -> -2 / +2). **The fabric width does not matter** (55.1 and 39.4 in give the same limits), so a length tilt is not an angle over the width: the engine simply reads the inch number as degrees.
  (A nester that wants AccuNest's numbers takes them from the table, not from the marker.) `accumark_engine.engine_tilt_from_table`. The three-fold flag mapping of section 34 (the flags from the Piece Options) is unchanged: 10 of 10.
* **Order targets.** Section 1 holds two doubles that copy the order: **@404 = the order's Target Length in inches** (order object u32 at +150, 1e-4 in; Order Editor field `Target Length [m cm]`, 630 cm -> 248.0314) and **@438 = the Target Utilization in percent x 10** (order u16 at +158; Settings > `Target Utilization` replaces the Target Length field by `Target Utilization [%]`: 91.5 -> 915;
  850 = 85.0 % on the older orders); the order also holds the fabric width (u32 at +154). [V: 79 of 79 order / marker pairs; live: 630 cm and 91.5 %.] **The engine's `TARGET_LENGTH` = total piece area / (width x utilization) when the order has a utilization, else its target length, else 0** [V: 80 jobs: 29 with a utilization, 1 with a target length, 50 with neither]
  (the Nest Markers dialog's `Use Order Utilization / Length` and `Target Utilization [%]` are the job-side counterparts). `mk['order_targets']`; the nest spec's `fabric` has `target_length`, `target_utilization_pct` and `target_length_at_utilization`; `accumark_engine.engine_target_length`. This settles two of the residue words of section 33.

## 36. Which pieces the engine turns: bit 0x0200 of the slot word @+60 [V, v4.33, live]

Section 32 found that the engine holds the LADIES-BLOUSE collar a quarter turn away from the marker's stream and could not say what decides it. The slot says: **bit 0x0200 of the u16 at slot +60 is set on every slot of a piece the engine turns and on no other.** No placement is needed - it is there on an UNPLACED marker too.

* **Evidence** (`engine/FRAME_TURNS.json`, live 2026-09-25): the engine's own outline (`frommed.mra` points) of every piece x size of five AccuNest jobs against the marker's stream outline turned 0 / 90 / 180 / 270 about the middle of its box (largest distance either way, inches). 133 pieces x sizes: **14 turned pieces, all 14 set the bit; 119 unturned, all 119 clear it.** The 14 = the LADIES-BLOUSE collar (five sizes, +90) and the sleeve of a legacy AccuMark 9 sample jacket set (nine sizes, three fabric rows; the sample style is in the machine's sample area and was copied into scratch, only the fitted numbers are here).
  Every turned piece fits its quarter turn to 0.02 - 0.11 in (the sleeve 0.06 - 0.11 in, the collar of the twoply job 0.56 in = the block buffer its engine outline carries and the stream does not) and the next-best turn is at least 0.6 in worse. The other slot words that were tried (@32 orientation, @34..@42, the bundle, the record head) carry no trace of it.
* **On the corpus:** all 46 marker files of the fixture folders (162 marker files with the ZIPs): the bit is all-or-nothing per piece, only the LADIES-BLOUSE collar (32 collars) sets it, it agrees with the home-box method (`frame_offsets`, section 20) on every collar that method can decide, and it decides the one it cannot: **the collar of the 45-degree job** (`deg45/ZZR-45-MADE`: thin, tilted 45 degrees, so both frames predict the same boxes - `frame_offsets` says 0, the plot needs +90) - `frames_ambiguous` is now empty there.
* **What the decoder does:** `slot['frame_turned']` / `slot['engine_word']`; `piece_frames(slots, items)` (the bit wins, the boxes fill a piece whose slots disagree) -> `mk['frames']` (0 / 90), `mk['frames_ambiguous']` (only for a piece the bit does not decide), `mk['frames_box_disagree']`; the inventory's slot has `frame_turn_deg`, **the nest spec's shape has `engine_frame_turn_deg`** (90 for the collar, also on an unplaced marker). A nester that reads `retrieval_deg_by_slot` / `allowed_deg_by_slot` (both in the ENGINE frame) turns the outline by it first.
* **Only the size of the turn is stored, not the sign.** The collar is +90 (counter-clockwise) at every size and on every job; the sleeve of the jacket set fits **+90 on sizes 2 - 8 and -90 (270) on sizes 10 - 18** with a margin of 2 - 3.5 in (a mirrored turn fits 0.24 in worse: it is a rotation). Nothing in the slot, the record head or the engine's piece record changes between size 8 and size 10 besides the counters, the box and the area, and the sleeve's shape does not cross any threshold there
  (10.2 - 11.2 x 11.8 - 16.6 in in the stream: a tall piece at every size). The sign therefore is either the engine's own choice from the geometry or an undecoded field [?]; it only matters to a piece pinned to one direction (the allowed sets 0/180 and 90/270 are closed under 180).
* **A float at slot +72 accompanies the turn** on some markers: 0 on every unturned slot (8,162 of 8,162), +-1.5708 on 696 of 1,258 turned slots (the collar of the placed block-buffer jobs `+pi/2`; on the jacket set `+-(pi/2 - e)` with e = 0.0006 rad per size number away from size 8, its sign NOT following the sign of the turn: the sleeve of size 2 reads -1.5672 and fits +90). Read as raw; not used [?].
* **What the turn does NOT follow (v4.37, offline over the machine's 86 pieces that have both a piece file and a marker; the sleeve is the only turned one):** not the aspect (tall pieces that are not turned: a 4155B front 4.9 x 14.6 in, a jacket pocket flap 1.5 x 4.0, a real style's side piece 11.5 x 18.0, a facing 3.2 x 4.8); not the grain line (the turned sleeve's grain is horizontal in its piece object like every other piece's); not an internal line (a side piece with three internal lines is not turned); not any word of the piece object's meta block (`mirror_flag`, `unk_u16_a/b/c`, `n_break_rows` are identical or differ per piece topology only, not with the turn); not the piece's fold (the jacket collars have a horizontal mirror line and are not turned). The sign flips with the size on the sleeve, so the engine decides it - and probably the turn itself - from geometry it recomputes per size, or from state the piece object hides. Ground truth to settle it would be the same piece at a second frame, which V17 cannot make.
* **Why the engine turns it** stays open (section 32: not the aspect, not the grain line the stream stores, not the fold line). The grain-aligned-frame hypothesis fits the collar and the sleeve (both are pieces a designer draws with the grain along y in AccuMark 9), but no V17 tool makes a piece with a vertical grain - DCU import turns it to x and a PDS rotation is not stored - so it cannot be tested with a piece of my own.

## 37. Notches on a turn point (corner notches) [V, v4.34]

A stream point whose main tag has a low nibble other than 1 (a TURN point, section 14) and that carries an extra byte is a **corner notch**: the low nibble of the extra byte is its type (the same byte as for a notch on a plain point). `record_outline()['notches']` listed only the notches on plain points, so **the corner ones were dropped and the nest spec had no notch on any corner**. Since v4.34:
`record_outline()['corner_notches']` = `(point index, type, x, y)` (inches, the outline's own frame; a fold piece's mirrored half included), the inventory's slot `corner_notches`, the nest spec's shape `corner_notches` (and `corner_notches_mirrored`, the DXF / SVG output, `notch_table.numbers_used`). `notches` is unchanged.

* **Evidence.** The piece object flags the same points (`is_corner_notch`, the type in the high byte of the point's `f1`, FORMAT_SPEC 4.x): **piece == stream on 201 of 201 records** of the repo's live blouse markers (back, collar and sleeve each hold one type-1 corner notch) and on 86 more records of markers of this machine (production styles, types 1, 2 and 5). The exceptions are the piece decoder's, not the stream's: 14 records of one pouch (a notch the piece decoder reads as an edge notch of byte 13 stands as corner types 1, 1, 5 in the stream) and 4 of the sample jacket set (the piece flags fewer corners than the stream).
* **Corner types 9 / 10 are not evidence:** of the 480 records of this machine with a turn point carrying a type, 390 verify (types 1, 2, 5) and the 90 that do not carry the types 9 / 10 - a stream that does not verify may have its point kinds off, so those two types are a hint only.
* **Numbers above 5.** An EDGE notch: the piece keeps the number, the stream min(number, 5) (v4.15; a real piece of the OLDFiles area shows it on its own: piece byte 13, stream 5). **A CORNER notch looks unclamped** [? a hint, not a proof]: on six records of one real production style the pieces store corner type 9 (one piece also 10, another also 1) and the streams show corner type 9 - never 5 - but those six streams do not verify against the record's area (an older layout), so the kinds may be off, and their counts differ from the pieces'. So a corner notch above 5 probably keeps the byte the piece stores, up to the nibble's 15 [numbers above 15 cannot fit the nibble and were not tested - PDS would have to make a corner notch with a number of 16 / 25, `Seam > Define` corner notches or a Notch on a turn point, not run]. The nest spec passes a corner type above 5 through as `number` / `numbers` and lists it in `undefined_numbers` (and a warning) when the notch table has no such row.
* **Live (v4.35, 2026-09-25): a corner notch made by the DCU is clamped like an edge notch.** A DXF of a 30 x 20 cm rectangle with notch points on two vertices and one on an edge (`notchnum/ZZCN_spec.json`; all three become number 6 under the scratch table) was imported, an Easy Order of the model processed to an unmade marker (`notchnum/ZZCN.GT_mark`, piece `ZZCN-RECT.GT_piece`): the piece stores **code 5** on both corner notches (`is_corner_notch`, f1 = 0x0500) and on the edge notch (f1 = 0x0501, number 6 in its child), and the stream has `turn 5`, `notch 5`, `turn 5`. So the raw 9 of the real production style comes from another way of making corner notches (a seam corner notch?) - **how a corner notch gets its byte decides whether it is clamped [?]**.
  `@472` (section 1) = the attribute points: 18 = 6 slots x 3 on this marker, so corner notches count as attribute points (the byte-map test now covers it).
* **A record that does not verify - the control (v4.36):** `notchnum/ZZCN2` holds the same rectangle three times, without a notch, with one edge notch and with two corner notches: the first two verify exactly (area 93.000 / 93.001, home box = outline box), **only the corner-notch piece does not**: head area 101.364 / perimeter 39.677 against the polygon's 93.000 / 39.370, and its stored home box is **8.966 in high against the outline's 7.874 (+1.092), 11.811 wide as the outline** - so AccuMark's declared area, perimeter and box include something the corner notches add beyond the stream's outline (a spike of the notch, in y only on this rectangle) that the stream's polygon does not carry. **AccuNest job 302 on that marker shows what it is (v4.39, `engine/ZZCN2.frommed.mra`):** the engine's own polygon of the corner-notch piece has **12 points: an ARCHED top edge**, 1.092 in above the chord between its two top corners (the peak nearer the notched corner), the sides and the bottom straight; its `AM_AREA` is 101,364 = the record head's number. The pieces without a notch and with an edge notch are the plain rectangle (5 / 6 points, 93,000 / 93,001). The arch is in neither the marker's stream (4 points) nor the piece object (the same 5 perimeter points as the plain piece; the two corner notches add two 47-byte children, 94 bytes, no curve data), so **AccuMark itself builds a curved edge from a code-5 corner notch here (its row is undefined in this scratch notch table)** - what the front end does with a corner notch of an undefined row is open [?]; a real style's verified corner-5 records show no such arch in their area.
* **The same record, as first seen [open]:** on `ZZCN` the record head says area 101.364 sq in / perimeter 39.677 in, the stream's polygon (the 30 x 20 cm rectangle, 93.000 / 39.370) is what the piece is; `record_outline` cannot verify it, the nest spec says `no outline` (loud, `complete: false`). No perimeter-and-area pair of a rectangle fits the head's numbers (the isoperimetric bound), so the head describes another shape (notch geometry? the DCU's duplicate vertices?) - the control above says the corner notches are what differs. Since v4.35 the guess `record_outline` returns for an unverified record is the split with the longest first contour (here the whole 5-point outline with its notches).
* **Not decided:** whether the cutter draws a corner notch differently from an edge notch of the same number (needs a marker plot with one of each).

## 38. The residue of section 1, tried again [?, v4.38]

Across the 222 distinct markers of this machine the unidentified non-zero bytes of section 1 sit at the file offsets 484 (u16, 38 values), 488 (u16, 42 values: 94 on 50 markers, 7 on 24), 494 (u16, 3 - 8), 504 (`5` on all 222), 506 (`0` on 142, 20 - 40 on the rest), 522 (`3750` on 204, `1476` on 18), 530 (u16, 59 values), 588 (`0x01010101` on 204, `0` on the 18 oldest), 592 (`0x8018` / `0x8218` ..., 9 values) and 604 (0 or 1). A brute-force correlation of each word with sums over the records / slots of every prefix word, the stream lengths, the text lengths, the record / slot / piece / size counts and the name lengths (221 markers) finds **no rule**: the best is `@484 = the number of records` on 38 of 221 and `@506 = sum of prefix word 3` on 53 of 221. None of these words is needed by a nester (they do not feed the engine's job file); they stay identified as `unknown`. Section 5 (the Annotation table copy, up to 9.6 KB) was not attempted: its content is font and text-style records of the annotation table object, not job data.
