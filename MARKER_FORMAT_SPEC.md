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
only these 48 are read. Of the 316 unread byte positions `marker_coverage`
attributes to it, 271 are byte-identical across all 18 markers and 45 vary; their
meaning is open [?].

`@422` / `@454` relate to the slots in one of three MODES (`header_sums`): the sum
over `all` slots' declared area / record perimeter; over the `last_model`'s slots
only; or `2x_all` [V]. On the six never-laid single-model markers both are `all`;
on the unlaid 2303-BD 137 both are `last_model`; on its laid twin `@422` is `all`,
`@454` `last_model`; LADIES-BLOUSE's `@454` is `2x_all`. Why the last model [?].

## 4. Sections 2, 3, 4, 5 [?]

Not decoded. 2 = options + the marker's name (grows with the name); 3 = repeating
`00 00 b0 07` groups; 4 = a 12-byte label-config header; 5 = the `-PDSTEXT-` label
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
marker default", was an over-fit to the small corpus and is retracted.) Side order
of the four doubles is [?].

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
Type' role (A/B/C/D/G/M/F ...) is the fabric-type text. The other flag bytes stay
raw [?].

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
NUL-terminated label `<piece><cut description><size>G`, then a per-point attribute
stream (extent = up to the next record; content bounded, not decoded - it is a
per-piece attribute table, not geometry). One record per (piece, size, cut).

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
    +32  u16 orientation         +34..+41  const  ff ff ff ff 00 00 00 00 [?]
    +42  f64 declared area       +50..+63  raw (u16 @52, @54, @60 vary) [?]
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

**Orientation.** Bit 0x2000 = rotate 180, bit 0x0080 = mirror [V vs drawn DXF]. Bit
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

Every byte in sections 6, 11-15, 21, 30 is classified. Unknown = 1,187-1,829 bytes
per marker (1.38% overall, the same on a 3 KB marker as a 280 KB one): trailer,
section 1's unread bytes, sections 2-5, the envelope. identified 4.1%, raw 2.4%,
zero_pad 0.8%, opaque 91.3% (section 14's streams + section 30).

## 14. Open, and what settles each

| open | evidence so far | method |
|---|---|---|
| side order of the four block-buffer doubles; what the table is for | home box ignores it (ZZC-M1 vs ZZC-BIG) | live: unequal buffers on a piece with real geometry |
| what order / model option sets the piece-row flag @+14 (= the slot 0x0040 bit); the pre-set rot180 alternation | 0x0040 == flag @+14 on 9,122 / 9,122 slots [V]; alternates per bundle | live: flip one order / model option per run (DATASET_DESIGN F5) |
| what C counts in @88 = head count + C; slot @52/@54/@60 | @88 = p1 + C(piece) [V], C tracks internal-line points; stored-empty and laid-then-returned read 0 alike | pieces with 0 / 1 / 2 / 4 internal lines built in Pattern Design (DATASET_DESIGN F6); @52/@54/@60 vs piece/size |
| the y excess on July CP 150 unplaced slots (up to 0.0786 in, one-sided) | x fits the CP 150 table but the table does not drive home | live: known notch / curve |
| placed slots 7.2% larger than their record (ZZC-M3, ZZN-F1) | 2 slots each | live: repeat with a plain piece |
| why `@422` / `@454` are last-model sums; LADIES-BLOUSE 2x | modes observed exactly; a FRESH two-model as-generated marker (`CLAUDE-D2-E7B`) shows `last_model` on both [V], so it is generation-time behaviour, not a laid-state artefact; the LADIES-BLOUSE `2x_all` case is still unexplained [?] | one more two-model order laid in Easy Marking |
| size-row `flags` (0xffff vs 0) | 12 vs 6 markers | live |
| sections 2, 3, 4, 5; section 1's 45 varying bytes; the trailer | mostly constant | twin diffs |

Marker-only ZIPs (no piece objects) can never yield outlines, and an unplaced marker
carries no positions - those are limits of the export, not of the decoder.
