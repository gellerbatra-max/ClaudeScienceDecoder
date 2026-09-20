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
- **Word 40 is a STATE code, not an offset:** 0 = nothing placed, 1 = some, 2 = all
  [V: 18 of 18]. **Word 41 is 0.** Reading them as offsets fabricated a section 40.
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

Only on some markers (1825D, 418T, July CP 150). `(pieces + 1)` entries of 102
bytes from `dir[6] - 6`: `<u16 0><4 x f64 buffer, inches><68 zero bytes>`. Every
value observed is 0.0591 in (1.5 mm). A piece row's `buffer_index` equals its
1-based position in the piece list, so entry 0 is the marker-wide default and
entry k is piece k's [V]. It is what makes `home x 2` exceed a piece's own bounding
box (July markers: residual 0.1182 in = 2 x 0.0591 without it, 0.0000 with it) [V].
Which side each double is [?] - all are equal.

## 6. Section 10 - piece list [V: 18 of 18]

A 28-byte header whose last 6 bytes are the literal `MARKER`, then contiguous rows
closing at `dir[11] - 6`:

    <u16 name length> <u16 category length> <24 flag bytes> <name> <category>
    <fabric types: u16 count at flag byte 18, then that many <u16 len><text>>

Flag bytes 4..5 (u16) = 1-based index into section 6 (0xffff = none). The 'Fabric
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

    +0   f64 placed centre x     +8   f64 placed centre y      (0.0 when unplaced;
                                                                 -1000 on older exports)
    +16  f64 home x              +24  f64 home y     (half the piece's box + buffer)
    +32  u16 orientation         +34..+41  const  ff ff ff ff 00 00 00 00 [?]
    +42  f64 declared area       +50..+63  raw (u16 @52, @54, @60 vary) [?]
    +64  u32 bundle (low 16) + flags (high 16, 0)    +68..+87 const [?]
    +88  u16 (non-zero, constant per record, on never-laid markers; 0 on laid ones) [?]
    +90..+95  the NEXT slot's head (below)

**The head.** 6 bytes BEFORE each slot body: `<u16 record index (0-based, section 14
order)> <u16 piece index (1-based, section 10)> <u16 bundle>` [V: 677 of 677 slots on
all 18 markers]. (Earlier notes read `+90/+92/+94` as a circular pointer; it is the
next slot's head.)

**Orientation.** Bit 0x2000 = rotate 180, bit 0x0080 = mirror [V vs drawn DXF]; 0x0040
tracks the pair bit of a `CUT X02` piece [?]. A placed slot's word also carries lay-
session bits (0x8000, 0x0200, 0x0020 ... ). On a never-laid marker only the three
known bits appear [V: 6 of 6]; on a PARTLY laid marker an unplaced slot keeps the
bits it had before it was lifted (61 of 71 on July CP 150). So on a never-laid
marker the word is a PRE-SET lay pattern, not a placement.

**Placed vs unplaced** is a sentinel test on the centre (0,0, or x < -900); the
laid state cross-checks it with directory word 40 and `@430`.

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
| side order of the four block-buffer doubles | all equal in the corpus | live: unequal buffers |
| what sets the 0x0040 pair bit; the pre-set rot180 alternation | tracks `CUT X02`; alternates per bundle | live: qty / flip options |
| slot u16 @88, @52/@54/@60 | @88 non-zero only when never laid | never-laid vs cleared twin |
| the y excess on July CP 150 unplaced slots (up to 0.0786 in, one-sided) | x exact with the buffer | live: known notch / curve |
| why `@422` / `@454` are last-model sums; LADIES-BLOUSE 2x | modes observed exactly | two-model live order |
| size-row `flags` (0xffff vs 0) | 12 vs 6 markers | live |
| sections 2, 3, 4, 5; section 1's 45 varying bytes; the trailer | mostly constant | twin diffs |

Marker-only ZIPs (no piece objects) can never yield outlines, and an unplaced marker
carries no positions - those are limits of the export, not of the decoder.
