# Marker decode plan — AccuMark native marker export

> ## STATUS 2026-09-10 (later) — `@454` closed on independent data; section 14 narrowed further
>
> **`@454` — now confirmed, not just "understood in the simple case."** The
> gap left by the previous pass was that both controlled tests happened to
> place the *same* piece repeatedly, so `Σ(quantity × perimeter)` couldn't be
> told apart from `n_placements × (one piece's perimeter)`. Found two
> pre-existing markers already sitting in `DATA90` (`AD1234 TEST 134`,
> `LADIES-BLOUSE TEST-2`) and exported both. `AD1234 TEST 134` is a genuine
> third, independent data point - not something built for this investigation -
> with 13 placements of `ID1005 - RUFFLE` (a 142-point gathered/curved
> piece, nothing like the rectangles used before): predicted `13 ×
> perimeter(RUFFLE) = 764.06`, actual `@454 = 764.32` - 0.03% off, on the
> same order as the curve-tessellation residuals already accepted elsewhere
> in this project. `LADIES-BLOUSE TEST-2` hit the known "Include Components
> silently drops pieces" limitation (0 of 5 needed pieces came through) and
> also exposed a real bug fixed along the way: `accumark_marker.parse_marker`
> raised `KeyError: 'size'` when a slot's best-area-match record's own text
> didn't match any declared piece name (that record never got a `'size'` key
> set at all) - now defaulted to `None` up front so binding never crashes on
> an unmatched record. `selftest.py` still passes after the fix.
>
> **Section 14's per-point stream — two more hypotheses tested, one ruled
> out, one narrowed:**
> - **Not a literal copy of the piece's own raw bytes.** Searched the piece's
>   full raw `.tmp` data for the stream's own bytes at 200/100/50/20/10-byte
>   granularity: zero matches at every size, on `2303-B1-OUMO-5-SP24`'s
>   2634-byte stream. Whatever derives this stream from the piece, it isn't
>   a direct embed.
> - **Total length tracks piece complexity, clustered by piece *family*, not
>   a single global ratio.** `stream_len / raw_piece_size` clusters tightly
>   within a style: OUCF fold pieces (4 samples) land at 0.0414-0.0436;
>   OUMO/INMO cup pieces (6 of 8 samples) land at 0.0853-0.0892 - a
>   different, family-specific proportionality, not one constant across the
>   whole format. (Two OUMO outliers, `-2`/`-4`, sit at ~0.10 - unexplained.)
> - **The stream opens with a short run of small values, then goes opaque.**
>   The first 22 bytes of `OUMO-5`'s stream are 11 `u16` pairs, every value
>   ≤ 73 (well inside its 117-point perimeter's index range - plausibly
>   point ordinals or a small record count) before the remaining ~2600 bytes
>   stop looking like anything structured at the `u16` level. Byte-level
>   layout past that header is still open.
>
> `python selftest.py` → **SELFTEST PASS** (one real fix landed this pass -
> the `KeyError` above - plus two new marker fixtures added to `markers/
> misc-test-markers/` as read-only reference data, not yet wired into
> `selftest.py`'s fixture list since `LADIES-BLOUSE TEST-2` can't fully
> decode without its missing piece components).
>
> ## STATUS 2026-09-10 — a pass at §5's "still open" list: two solved, one reframed, one narrowed
>
> Worked the long-tail unexplained-byte list (piece-side §10.3/§12 and
> marker-side §5) end to end — pure re-analysis of existing captures first,
> then two small new AccuMark objects (`CLAUDE-QTY-TEST` order+marker) built
> specifically to isolate one field each. Full detail is in `FORMAT_SPEC.md`
> §10.1/§12 for the piece-side items; summary for the marker side:
>
> - **Order quantity field — found.** Each per-model-size row in an Order
>   object is `[model name]\0 [u16 flag] [u16 QUANTITY] [~26-30 zero bytes]
>   [ASCII size name] …`; confirmed by building `CLAUDE-QTY-TEST` (quantity 3
>   for size "8" of `CLAUDE-GRADE-MODEL`, every other size left at 0) via
>   Easy Order and finding `u16 = 3` at exactly that position, against `u16 =
>   1` at the analogous position in every one of `2303 MOCUP`'s real
>   quantity-1 rows.
> - **Section 13 — already solved, this doc was stale.** `accumark_marker.
>   parse_marker()` already computes it as `record_index`: cumulative byte
>   offsets into section 14's per-piece records (66 values for 66 records on
>   `PLACED`, monotonically increasing, diffs are the records' own byte
>   lengths). The "36 u16 pairs" description in the old version of this list
>   was never updated after the code caught up.
> - **`@454` — proven not constant.** It read 19.5158 on every sample so far
>   because every sample so far was an export of the *same* two marker
>   sessions (`2303-BD 137` unlaid/laid; the four July corner probes share
>   one session too). Across five genuinely different markers it ranges
>   19.5–134.5. It matches `Σ(quantity × that placement's own perimeter
>   length, inches)` exactly on both `CLAUDE-GRADE-MARKER` (2 placements,
>   89.6476 = 2 × 44.8238) and `CLAUDE-QTY-TEST` (3 placements of the same
>   piece, 134.4714 = 3 × 44.8238 — the piece's real perimeter, computed
>   independently from its own geometry). Does not resolve against `PLACED`
>   with only that fabric group's pieces on hand (its models list other
>   sizes whose piece objects aren't in this particular export) — the
>   formula is confirmed on controlled data, not yet on a fully-self-
>   contained production marker.
> - **Section 14's per-point stream — hypothesis from this list ruled out.**
>   It is not the piece line table's TLV grammar (searched a 65-byte and a
>   2634-byte sample for the `0a 00` record header used everywhere in that
>   grammar: zero hits in either). Confirmed piece-level rather than
>   per-placement: two records of the same piece at very different sizes are
>   byte-identical apart from one heap-pointer-shaped value and a trailing
>   1-byte counter. Its own internal structure past that is still open.
>
> `python selftest.py` → **SELFTEST PASS** throughout (no decoder code
> changed this pass — this was documentation/analysis plus two new,
> clearly-named test objects in `DATA90`, not a fix to `accumark_marker.py`
> or `accumark_pds.py`).
>
> ## STATUS 2026-09-09 (later night) — M3 (graded placements) closed with a controlled test
>
> The one real gap left after §4's captures: style 2303 has no genuine
> grading, so `graded_outline()` had never been proven against a placement
> that actually moves. Rather than wait for a genuinely-graded production
> style, built the minimal controlled test directly in AccuMark: a fresh
> rectangle (`CLAUDE-GRADE-TEST`, `C:\DATA90`), assigned the existing
> `CAP-RULES-A` rule table (real, non-uniform per-size-break deltas, already
> validated on the piece side by `CAP-C20-RULE-DISTINCT`), rule 1 applied to
> only 2 of its 4 corners (Grade tab → Rule Number — the Track/Stop toggle
> from `AGENT_KNOWLEDGE_BASE.md` §10c is exactly right: canvas clicks only
> move the selection in Track mode, typing into D1 only registers in Stop
> mode) so the other 2 corners exercise `graded_outline()`'s chain-
> interpolation branch, not just the explicitly-ruled points. Bundled it into
> a model (`CLAUDE-GRADE-MODEL`, since the Marker Wizard requires a model, not
> a bare piece) and placed it twice in its own marker — size 2 and size 18,
> the two ends of the table, both far from base size 8 — via manual
> drag-to-canvas placement in Easy Marking (AutoMark reported "Success" but
> silently placed 0 of 2 pieces; not investigated further since manual
> placement is trivial for 2 pieces).
>
> Result, against AccuMark's own drawn DXF of that marker
> (`markers/CLAUDE-GRADE-MARKER/`): **both placements' graded outlines
> match to dxf_outline_max = 0.001 in**, centres to 0.0007 in, `bbox_ok 2/2`.
> This proves `graded_outline()` correctly reconstructs a genuinely different
> per-size shape — including the two interpolated corners — not just the
> two explicitly-ruled ones. Now a permanent `selftest.py` fixture.
>
> One decoder-adjacent snag worth recording: `accumark_marker.place_marker()`
> only looks for a piece object inside the *same* zip as the marker. PDS's
> own marker export (with "Include Components" checked) hit "Error: not all
> components exist" and silently dropped the piece from the zip — fixed for
> this fixture by exporting the piece separately and merging its `.tmp`
> member into the marker zip (`list_zip` classifies by content, not member
> name, so this is a legitimate zip, not a hack around the format).
>
> ## STATUS 2026-09-09 (night) — §4's three inputs captured and validated, live on the AccuMark machine
>
> Captured directly from AccuMark (Easy Marking → Marker Plot for the drawn
> DXF; PDS File → Export for the two piece DXF+ZIP pairs) rather than waiting
> on the user — style 2303's `Test` storage area on `C:` already had
> everything named in §4.
>
> | file | result |
> |---|---|
> | drawn-marker DXF of `2303-BD 137 PLACED` (`markers/2303-BD137-PLACED/2303-BD 137 PLACED.DXF`) | **97/97 placements matched**, centres worst 0.0012 in, outline Hausdorff worst 0.0205 in — closes §4a, the acceptance test for the whole placement/transform pipeline across every rotation, mirror, flip-H and fold piece in the marker (previously only exercised by the July set's 4 markers × 1 placement each) |
> | ASTM DXF of `2303-B1-38B-IN WG-SP24` (wing piece, 15-byte curve records, `captures/2303-B1-38B-IN WG-SP24/`) | **dxf max\|delta\| = 0.000000 in** — closes §4b for Fix 2: the variable-width point record is exactly right on real production curve data, not just `CAP-*` synthetic pieces |
> | ASTM DXF of `2303-B1-A1- OUCF-SP24` (fold piece, `captures/2303-B1-A1- OUCF-SP24/`) | **dxf max\|delta\| = 0.0001 in** (print rounding) — closes §4b for Fix 5: fold unfolding is exact on a real production fold piece |
>
> **New finding along the way, now fixed:** the drawn-marker DXF's raw
> polyline vertices are in whatever unit the AccuMark session was set to —
> `$INSUNITS 1` (inches) on the July markers, `$INSUNITS 5` (centimeters) on
> this one (`2303-BD-137-PLACED.DXF`'s own bbox was exactly 377.68 × 137.0,
> the marker's `length_cm`/`width_cm` to the decimal — the tell). `verify_
> marker.dxf_marker()` was comparing raw cm values against inch-based
> placements with no conversion, off by ~2.54× (worst case ~111 in before the
> fix, 0.0012 in after). Fixed by reading `$INSUNITS` and scaling to inches;
> also fixed a latent bug the same investigation exposed — `dxf_facts`'s
> glob for `*.dxf`/`*.DXF` double-counts a single file on a case-insensitive
> filesystem, defeating its "only one DXF in this folder" shortcut. Neither
> fix changes the July markers' own numbers (still ≤0.0008 in / ≤0.078 in;
> `selftest.py`'s per-marker tolerance for `dxf_centre_worst` is now 0.0015
> in generally, not 0.001, to allow for the cm→inch round-trip's slightly
> coarser precision on this vintage — still an order of magnitude tighter
> than the outline-tessellation budget).
>
> `python selftest.py` → **SELFTEST PASS**, now on 7 marker fixtures (the
> `2303-BD137-PLACED` entry gained its `--dxf` check).
>
> **What's left of §4, and the one real gap:** §4c (tilted piece, group/block
> placement, alpha-size style) is untouched. More importantly, **M3 (graded
> placements) is still unproven** — style 2303 has no real grading (every
> rule reference is the placeholder `10001`, confirmed again on both new
> piece captures), so `graded_outline()` has never moved a point on real
> data. That is the next input worth asking for, not another §4-style capture
> this machine can already supply.
>
> ## STATUS 2026-09-09 (evening) — decoder work of §3 done through M4
>
> `python selftest.py` → **SELFTEST PASS** on the 21 piece captures **and**
> the six markers now in `markers/` (2303-BD 137 unlaid, laid, and the four
> July corner probes with their drawn DXFs).
>
> | item | state | evidence |
> |---|---|---|
> | Fix 1 point-table locator | **done** | 162/162 production pieces; C61's "missing 4th corner" was this bug (spec §4 corrected, selftest expectation updated) |
> | Fix 2 variable-width records | **done** — the real cause was narrower than dxfparser's grammar: the `rule_ref` group follows whenever `f1`'s low byte is 0 (a corner carrying a notch, `f1 = 0x0N00`) | the 8 failing wing pieces now read `n_perimeter − 1` points with sane bboxes |
> | Fix 3 header residue | **done** — field-block search from 0x80, type from 0x7a | 122 July-vintage pieces decode |
> | Fix 4 refuse non-piece objects | **done** — `decode()` raises on type ≠ 20; `accumark_marker.read_object` reads every type | |
> | Fix 5 fold halves | **done** — `accumark_pds.mirror_lines()` / `unfold()`; `accumark_marker.piece_outline()` unfolds about the two perimeter points the `M` block names | the four OUCF pieces reach declared area to ≤0.7 % and pass the home×2 bbox test |
> | Fix 6 `summarize()` speed | **done** — 58 s → 0.01 s (pre-filter + `n_sizes` cap in the offset scan) | |
> | M1 `accumark_marker.py` | **done** | 97/97 slots bound; Σ areas = W·L·U exact; piece list with fabric codes, models, size rows, record index all parse on both vintages |
> | M2 `verify_marker.py` | **done** — report, `--expect`, `--dxf` (placement centres + outline Hausdorff), `--baseline` section-aware diff | July markers: centres ≤0.0008 in, outlines ≤0.078 in |
> | M3 graded placements | **engine written, only trivially exercised** — every rule reference in style 2303 is the all-zero placeholder 10001 and sister sizes share one geometry, so `graded_outline()` moves nothing here. Needs a genuinely graded style + drawn DXF | bbox test 97/97 at 0.02 in |
> | M4 fixtures in `selftest.py` | **done** | |
>
> **What the laid-vs-unlaid diff says (section diff in `verify_marker.py
> --baseline`):** laying changes only section 1 (header scalars), section 2
> (+7 bytes: the name), the slot table (section 21) and the embedded type-10
> object (168 → 175 KB); every list section is byte-identical, just shifted.
>
> **Still open (unchanged from §5):** @454, the type-10 object, section 12's
> `f0` field, the Order's quantity fields, the small parameter tables, and a
> *real* grading test. The three exports in §4 remain the next inputs.

Rewritten 2026-09-09 after analysing four files: `2303-BD 137 marker.zip`
(unlaid), `2303-BD 137 PLACED.zip` (the same marker laid, 97 placements),
`2303 PATTERN-MODELS.zip` (the whole style, 179 objects, July vintage) and
the July `2303-CP 150 CPL …` set (4 laid corner-probe markers **with their
drawn-marker DXFs**), plus the user's earlier repo
`github.com/gellerbatra-max/dxfparser` (`docs/accumark-decoded-so-far.md`
§6 is the marker ledger; `tools/accumark_marker.py`, `v2/accumark/binding.py`
are the reference implementation). Conventions as in `FORMAT_SPEC.md`:
**[V]** demonstrated by a file, **[?]** consistent but unproven.

## 0. Where we are, in five lines

1. **The marker placement format is solved and verified** — by dxfparser on
   2,830 production placements, and here on `PLACED` (97/97 slots bound,
   Σ areas = W·L·U to the last digit) and on the four July markers
   (placement centres match the drawn DXFs to ≤0.0008 in).
2. **`accumark_pds` is the better piece decoder** — its outline for the
   placed piece lands within 0.05–0.08 in of the drawn DXF (dxfparser's own
   is 3.8 in off) and matches every checkable declared area to ≤0.06 %.
3. **But `accumark_pds` needs three fixes for production pieces** (§3): a
   one-line point-table locator fix (validated, `selftest.py` still passes),
   the variable-width point record, and header-residue tolerance for the
   July vintage. After fix 1 alone: 154/162 production pieces decode.
4. **Nothing in the marker needs a GUI capture campaign any more.** The
   remaining marker unknowns (§5) are cosmetic; what is needed is one drawn
   DXF of `PLACED` and two piece DXFs (§4).
5. The rest of this plan is decoder work with the acceptance test for each
   item, in order.

---

## 1. Format facts established (all [V] unless marked)

### 1.1 Object envelope — every `.tmp`, every vintage

| offset | field |
|---|---|
| 0x00 | `XGGT IXPORT DB5.1\0` |
| 0x15 | object name, NUL-terminated (fixed slot) |
| 0x60 / 0x68 | object type u32 — **at 0x60 in the 2026-09 V17 export, at 0x68 in the 2026-07 export** |
| **0x7a** | object type u16 — **same offset in both vintages: read the type here** |
| 0x7e | payload length u32; payload starts at 0x80; `file = payload + 396` except markers |
| last 396 | trailer: u32 created, u32 modified (Unix), u32 5, two user-name slots |

Types: **20** piece · **12** model · **13** order · **9** marker · **10**
marker geometry cache (embedded) · **2** annotation / marker settings (`A`,
`M-MARKER`) · **3** block buffer (`3MM`) · **6** lay limits (`L`,
`COSTINGS`) · **17** notch table (`P-NOTCH`, `V-NOTCH-ALL CUSTOMERS`). The
Order names its annotation, lay-limit, buffer and notch tables in adjacent
fixed slots right after its own name — that is how the types were labelled.

Bytes 0x12–0x7d are heap/pointer residue that differs per machine and
vintage; **the July vintage's residue trips `accumark_pds._find_field_block`**
(it scans from 0x60). Neutralising 0x60–0x7f makes every July piece decode
(§3, fix 3).

### 1.2 Marker object (type 9)

- **Section directory at 0x8a: 42 × u32 absolute file offsets**, `0xffffffff`
  = absent. Used slots on both vintages: 1 header scalars · 2/3 options +
  name (grows with the marker name) · 4/5 per-piece label config
  (`-PDSTEXT-`) · 10 placed-piece list with fabric codes · 11 model list ·
  12 size/bundle list · 13 index [?] · 14 (piece,size) records · 15 copy of
  the order's model/size list · **21 placement slot table** · **30 embedded
  type-10 object**. The marker's payload-length field points at slot 30.
- **Header scalars (double, inches):** width @396, length @412,
  **total placed area @422** (= W·L·U/100, exact), utilisation % @446;
  @454 = 19.5158 on both 2303-BD exports, unnamed [?]. On an **unlaid**
  marker length/util are 0 and @422 holds a stale value.
- **Slot table = directory[21] … directory[30], 96-byte slots** (97 here, 72
  on the July markers; empty slots have placed = (0,0) on this vintage,
  (−1000,−1000) on older ones). Layout (dxfparser, confirmed): placed centre
  f64 @+0/+8 · home (bbox) centre f64 @+16/+24 · orientation u16 @+32 —
  bitmask `0x2000` rotate 180, `0x0080` mirror, both = flip H, other bits
  vintage base data · declared area f64 @+42 · bundle u32 @+64 (low word).
  The directory replaces dxfparser's fingerprint/sentinel locators, which
  fail on this vintage (fingerprint byte `01 01` vs its `11 01`).
- **Slot → piece binding:** the slot's area equals (≤0.1 %) the area in one
  of the section-14 records `[f64 area][f64 perimeter][u16][u16][u16 len]
  [8×0] <piece name><cut description><size>G\0`; 66 records here, e.g.
  `2303-B1-OUMO-2-SP24C-234AG` = piece, cut `C-2`, size `34A`. The same
  piece's records differ only in the size label and a trailing counter —
  the ~30 B/point stream after the label is a per-piece attribute table,
  not geometry.
- **Placed outline** = piece outline mirrored/rotated about its own bbox
  centre, translated to the placed centre. Verified on the four July
  markers: centres ≤0.0008 in; outline Hausdorff 0.046/0.078 in against the
  drawn DXF, whose curves are re-tessellated (95 vs our 85 points) — the
  same class of residual `TASK6-CURVE` showed against a *piece* DXF was
  0.0001 in, so treat this as plot smoothing, to be confirmed by a piece
  DXF (§4 b). The 1.5 mm block buffer (`3MM`) is a gap from the marker
  edge, not an enlargement of the piece.
- **The embedded type-10 object is not needed.** It is a complete object of
  its own (magic + name at +0x1a), 168–175 KB, contains no placed-outline
  coordinates in any encoding tried (int32/int16/float32/float64, 8
  orientations, absolute or delta), and changes wholesale when the marker
  is laid. Hypothesis: the unplaced/graded piece cache [?]. Park it.

### 1.3 Order (type 13) and Model (type 12) — readable, numeric flags [?]

Order: name, four table-name slots, then one block per model with the
requested sizes and quantity fields (`03 00 01 00` on ordinary rows). **Cut
quantity lives here**, per model per size — TASK1's null result explained.
Model: `3d 2b 00 00`, u16 len, piece name, flags incl. `0x41`/`0x44` per
piece [?], `Fabric Table.csv`, model name.

### 1.4 What the style bundle says about this product

Bra style 2303: 22 moulded-cup pieces (`INMO/OUMO 1–11`, graded 1–6 sizes
each), 72 wing pieces stored **one object per size** (`32A-OUWG` … , not
graded), 24 small cup-fabric pieces (`OUCF/INCF`) that are **cut on the
fold** — their decoded area is exactly 0.500 of the declared area — and
models per size range. A marker is per fabric group: `2303-BD 137` places
12 of the 18 pieces exported with it (`SA60151TH`, `SI01040A17`, `OUCF`
fabric codes in section 10).

---

## 2. Verification results (2026-09-09)

| check | result |
|---|---|
| `PLACED` slot parse | 97/97 bound, 61 bundles, x 6.1–144.1 in, y within 53.94 in |
| Σ slot areas vs @422 vs W·L·U | 5735.2104 = 5735.2104 = 5735.2104 |
| dxfparser vs directory locator, `PLACED` | identical placements |
| July markers, 4 × 1 placement, vs drawn DXF | centre ≤0.0008 in; outline 0.046/0.078 in (curve tessellation) |
| `accumark_pds` vs declared areas, 14 cup pieces | ratio 0.999–1.000 |
| `accumark_pds` vs declared areas, 4 OUCF pieces | 0.500 (fold halves — correct) |
| `selftest.py` with fix 1 applied | PASS, coverage unchanged |
| production pieces after fix 1 | 154/162 sane; all cup pieces `n = n_perimeter − 1` (closing point counted, harmless) |

---

## 3. Decoder work, in order — each with its acceptance test

**Fix 1 — point-table locator (validated, ready to apply).** Production
perimeters start at any creation-order id (13, 2, 7…), not 1/−1, and the
table begins exactly at the end of the object records; the window scan
therefore skipped real points (42A-OUWG read 24 of 27 silently) or landed
mid-record (17 pieces garbage). Patch in `accumark_pds.find_point_table`:
```python
    pid = i16(d, after)
    if (pid == -1 or 1 <= pid <= 4096) and COORD_LO < i32(d,after+2) < COORD_HI \
       and COORD_LO < i32(d,after+6) < COORD_HI and u16(d,after+10) in (0,1,2,0x101):
        return after
    # ...then the existing window scan
```
Acceptance: `selftest.py` PASS (done); wing pieces decode with sane bboxes
(done, 154/162).

**Fix 2 — variable-width point records.** The 8 remaining wing pieces carry
a 15-byte curve record `ff ff <x> <y> 01 00 01 00 0a` (14-byte form + a
terminator byte), which dxfparser documents as one of six widths (14, 15,
18, 19, 20, 21; terminator ∈ {09, 03, 0a}; `f1` low word `0x0C00` announces
an extra 8-byte payload). Port that grammar into `parse_point` (see
`dxfparser/v2/accumark/records.py`). Acceptance: 162/162 production pieces
with `n == n_perimeter − 1` and bbox < 20 in; `selftest.py` PASS.

**Fix 3 — header residue.** Start `_find_field_block` at 0x80 (payload
start) instead of 0x60, and read the object type at 0x7a. Acceptance: the
122 July pieces decode without neutralising the header; `selftest.py` PASS.

**Fix 4 — `decode()` must refuse non-piece objects** (type ≠ 20) instead of
`IndexError`; expose `read_object()` (type, name, payload, trailer) for all
types.

**Fix 5 — fold pieces.** `CAP-C61-MIRROR` gave the mirror-line grammar;
expose the axis and an `unfolded` outline. Acceptance: OUCF pieces reach
area ratio 1.00 ± 2 % against the declared area.

**Fix 6 — `summarize()` speed** (4–24 s per production piece; `decode()` is
instant). Profile the tail/coverage search; a 97-placement marker calls it
97 times.

**M1 — `accumark_marker.py`** (new): directory, header scalars, sections
10/11/12/14, slot table, binding (port `binding.py`: area match with
relative tolerance and rival band; size resolution across a piece's record
set — the *cut count is constant within a marker* rule), Order/Model
readers, `summarize_marker()` with the identities (Σ areas = @422 = W·L·U;
bundles; placed-piece list = section 10). Acceptance: reproduces §2 on
`marker.zip`, `PLACED.zip` and the four July markers, and reports
laid/unlaid correctly.

**M2 — `verify_marker.py`**: `report`, `--baseline` structural diff (reuse
`verify_capture.py`'s run classifier), `--dxf <drawn marker>` placement +
outline Hausdorff (port `_dxf_marker_polylines`/`_stitch_pieces`), and
`--expect` keys `placements, bundles, pieces_placed, width_cm, length_cm,
util_pct, area_identity=yes, laid=yes|no, geometry_match=yes`.

**M3 — graded placements.** Most placements are non-sample sizes (OUMO-3 is
placed at 36B, sample 32D). `accumark_pds` already decodes the rule table
and per-point rule references; add `graded_outline(piece, size)` (per-step
increments, smallest size first — see FORMAT_SPEC §3 and dxfparser ledger
§5: unruled points interpolate proportionally, a user-settled rule).
Acceptance: `PLACED` vs its drawn DXF (§4 a), all 97 placements within the
curve-tessellation band; then tighten with §4 b.

**M4 — `selftest.py` fixtures**: add `markers/` with the six markers and
the four July DXFs as regressions (counts, identities, Hausdorff budgets).

---

## 4. Files to ask the user for (small, all exports — no GUI experiments)

a. **Drawn-marker DXF of `2303-BD 137 PLACED`** — 97 placements covering
   rot 180, mirror, flip H, graded sizes and fold pieces in one file; the
   acceptance test for M1–M3.
b. **ASTM piece DXF (+ .RUL) of `2303-B1-38B-IN WG-SP24`** (15-byte curve
   records) **and of `2303-B1-A1- OUCF-SP24`** (fold) — settles whether the
   0.05–0.08 in residual is plot smoothing (expected) and validates Fix 2
   and Fix 5 point-exactly.
c. Later, one marker each with: a tilted piece (non-90° rotation — is it
   even stored in the orientation word?), a group/block placement
   (dxfparser's open gap), and a second style with alpha sizes.

## 5. Still open, none blocking

**Solved since this list was last written (2026-09-10, see STATUS blocks):**
section 13 (`record_index`, already implemented in `accumark_marker.py`,
just never promoted out of this list); Order quantity fields (the u16
immediately before each per-model-size row's zero-padding+size-string);
**`@454`** — confirmed `Σ(placement's own perimeter, inches)` on a third,
independent, pre-existing marker (`AD1234 TEST 134`, 13 placements of a
142-point piece, 0.03% off) in addition to the two controlled tests, so this
is no longer "the simple case only." Only loose end: it still doesn't
resolve against the production `PLACED` marker, whose export doesn't bundle
every piece its order references — a bundling gap, not a formula doubt.

**Investigated further, one hypothesis ruled out, narrowed but not cracked:**
the per-point attribute stream in section 14 — confirmed *not* the piece
line table's TLV vocabulary (zero `0a 00` record headers anywhere in it)
and confirmed piece-level, not per-placement (identical across sizes of the
same piece apart from a heap pointer and a 1-byte counter). Also now
confirmed *not* a literal copy of any part of the piece's own raw bytes
(zero substring matches from 10 to 200 bytes). Total length tracks piece
complexity in a family-specific way (`stream_len / raw_piece_size` clusters
tightly per style — OUCF fold pieces ≈0.042, OUMO/INMO cup pieces
≈0.085-0.089 — not one constant ratio), and the stream opens with ~11 `u16`
pairs of small values (all within the piece's own perimeter-index range)
before turning opaque. Internal layout past that short header is still
open.

**Untouched:** the type-10 object; `M-MARKER`/`3MM`/lay-limit/notch table
payloads; the model's `0x41/0x44` byte; the panel's length allowance
(dxfparser saw +4.00/+5.96 cm on other styles — check the Marker Properties
panel of `PLACED` against 377.68 cm once).

## 6. Superseded

The Phase M1/M2 GUI capture campaign of the first version of this plan
(MK-00 … MK-20) — the transform, the noise floor and the oracle were all
answered by dxfparser's work plus the four files above. Keep only the idea
of `MK-14-TILT` and `MK-16-QTY2`-style checks as §4 c.
