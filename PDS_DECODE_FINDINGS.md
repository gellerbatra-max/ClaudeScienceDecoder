# PDS decoder — full analysis of the eight-piece capture set

> **Round 2 status (2026-09-07, captures `CAP-*` in the bundle root, log in
> `CAPTURE_LOG.md`, details in `FORMAT_SPEC.md`).** Resolved since this
> document was written: §5.1 grade-rule layout (object record = `id, 0,
> n_rows × (dx, dy)` per-row increments in 1e-4 in; stride set by the
> size-list u16 at +6 = rows − 1; referenced rules embedded under their own
> number) — `CAP-C20/C21`; §5.2 `f1 = 1` means *no* rule — `CAP-C22`; §5.4
> drill points (internal list tag `0x44`, label `L08`) — `CAP-C50`; uneven
> seam (`begin`/`end` = allowance at the segment's two ends, linear taper,
> zero ends clear the flag) — `CAP-C30/C31`. Also: the export-to-export noise
> floor is 3 bytes at 0x48 (`CAP-C01`); the second piece record is created by
> *editing* (any edit, including assigning a rule table), not by Save-As or
> pasting (`CAP-C02`); header and trailer piece names are fixed-width slots.
> Since then, also resolved: notch encoding — high byte of `f1` is the PDS
> Notch Type number, not a bit flag (`CAP-C40/C41/C42`); internal cut-outs,
> a third internal-list kind (`CAP-C60`); a metadata field mis-modeled as
> part of `len_annot`, and `n_perimeter` over-counting by one on Fold-Keep
> pieces (`CAP-C61`); `f2` is a trailer byte count, not a 0/1 flag, exposed
> by dart points (`CAP-C62`); a Model-level export is a distinct manifest
> format, not an embedding of multiple pieces' geometry (`CAP-C63`); and
> Copy-Piece/Paste-Piece alone does not trigger the stale-second-record
> mechanism — only a subsequent edit does (`CAP-C70`). All of Phase 6 is
> now done. Phase 1's five capture items are also now done: a 30-character
> piece name grows the file by exactly the length difference while the
> header's metadata offset stays fixed (`CAP-C13`), confirming the header
> name is a fixed-width slot vs. the piece-record's own length-prefixed
> name/annotation strings (`CAP-C14`: `annotation` is a literal
> per-creation-tool string, e.g. `"collar"` lowercase vs `RECTANGLE`
> uppercase) — plus the internal-line open/closed and point-count findings
> already logged under Phase 6. **Tail section (2026-09-08, no new
> captures — pure byte-level analysis of the existing corpus, `FORMAT_SPEC.
> md` §10/§11).** The 847/1852/1312-byte tag/length/value tail is now fully
> parsed: a 52-byte pre-table header, two full perimeter geometry
> snapshots, then a self-describing TLV line table (one record per
> perimeter edge/internal line, with notch/graded-point/seam-cutline child
> tags) — this also resolves the ~50-byte per-graded-point block (it's the
> line table's own `04 0a` rule-reference tag plus its two `0f 0a`
> children). `accumark_pds.coverage()` now classifies 93–99.5% of every
> capture's bytes as `identified`. Also resolved by fitting the pre-table
> header's scalars across the whole corpus: its `n_perimeter` field (not
> `len(perimeter)` — the count of points with an attr byte, excluding a
> dart's own apex point) and two more fields exposed on seam pieces
> specifically (count of seamed edges / count of *uneven* seamed edges,
> exact on every seam sample). This also explains `CAP-C61-MIRROR`'s
> missing-4th-corner anomaly: its exact coordinates surface as a "virtual"
> point in the line table, computable from the piece's 3 real corners.
> **Still open**, catalogued with exact values in FORMAT_SPEC.md §10.3/§12:
> the notch-attribute payload's byte layout (partially cracked — one byte
> matches the already-known Notch Type, a second mostly matches but
> disagrees on one sample), the table-point struct's `b`/`c` fields, the
> `0f 0a` triple (every sample in the corpus is a placeholder, none yet
> decodable), uneven/tapered seam cut-line miters, `CAP-C62-DART`'s
> otherwise-unexplained 440-byte trailer, and whether the mirror piece's
> virtual corner is genuine fold-line reflection or simple bounding-box
> completion (indistinguishable on an axis-aligned right triangle). None of
> these affect geometry, seam, notch, grade-rule, or grain/drill/cut-out
> decoding, which remain validated to 0.000000 in DXF residual.

Inputs: `PDS.zip` → `AGENT_KNOWLEDGE_BASE.md` + 8 task folders, each with a
native AccuMark export ZIP (containing the binary piece record), an ASTM
D6673-04 DXF, and a `.RUL` grade-rule table.

Deliverables: `accumark_pds.py` (decoder), `FORMAT_SPEC.md` (byte-level
spec), `pds_decode_validation.csv`, `pds_decoded.json` (full decode of all
eight pieces), `pds_decode_overlay.png`.

## 1. Headline result

The native piece format is decoded and validated. Coordinates are signed
int32 in **1e-4 inch**; the decoded perimeter, notches, grain line and cut
line reproduce the paired DXF on **all eight pieces** with a maximum
residual of 1e-4 in (0.0025 mm), which is DXF print rounding, not decoder
error. Independent structural checks also pass: `n_perimeter` from the
metadata block equals the number of point records parsed, and the per-segment
point counts equal the DXF layer-1 polyline vertex counts on every piece
(`2;2;2;2`, `4;2;2;2` for the notched edge, `10;10;8;10` for the circle).

## 2. What each task established

| task | what it was meant to isolate | verdict |
|---|---|---|
| TASK1-CUTQTY3 | cut quantity 3 | **not stored** — see §3 |
| TASK2-NOSEAM / SEAM1CM | seam allowance | **solved** — per-segment `(begin,end)` int32 pair, 1 cm = 3937; cut line additionally stored as 4 explicit line records |
| TASK3-NONOTCH / NOTCHED | notches | **solved** — extra perimeter vertices with `f1 = 0x0101`, inserted in sequence on their side; positions match DXF layer 4 exactly |
| TASK4-DRILLPOINT | interior drill point | **no evidence in the file** — see §3 |
| TASK5-GRADED | grade rule assignment | **partly solved** — per-point rule reference decoded; rule *values* live in the ASCII `.RUL`, and the binary rule-value layout is unresolved (§5) |
| TASK6-CURVE | curves + many distinct rules | **solved for geometry**, 10 distinct per-point rule references decoded; segment-boundary point coding confirmed |

## 3. Two null results — both worth acting on

**Cut quantity is genuinely absent.** `TASK1-CUTQTY3` and `TASK2-NOSEAM` are
both 1543 bytes. A byte diff shows only 175 differing bytes, entirely
accounted for by: the piece-name string (twice), 4 bytes of uninitialised
heap residue at 0x48, the coordinate translation between the two pieces, and
the trailer timestamps. There is no quantity field. This confirms
`AGENT_KNOWLEDGE_BASE.md` §4 from the file side, and the DXF agrees —
`Quantity: 1,0` in both. Cut quantity must be read from the Model/Order
module, not from a piece file.

**The drill point never made it into the piece.** `TASK3-NONOTCH` and
`TASK4-DRILLPOINT` are both 2690 bytes and differ in **31 bytes across 7
runs**: the name string (twice), 4 bytes of heap residue, and two 2-byte
timestamp halves. Nothing else. The DXF has no layer-13 entity and no extra
`POINT` either. So the Create → Point/Drill click in that session was not
persisted to the saved piece — this is the silent-no-op failure mode the
knowledge base warns about (§2, §12), and TASK4 needs to be re-captured
before anything can be said about drill-point encoding.

## 4. Corrections to the knowledge base

- **§5 item 8 and §11 are wrong about `.RUL`.** The 5862-byte `.RUL` is not
  an empty stub: it is plain ASCII and contains the **complete 35-rule
  `A1-LADIES` sample library**. The 476-byte and 2488-byte files are small
  because `TASK5-RULES` and `TASK6-RULES` contain 1 and 11 rules
  respectively. `.RUL` size tracks *how many rules the assigned table
  defines*, not whether rules were applied to points — so it is not a
  grading-verification signal. Use the piece binary instead: per-point rule
  references are directly readable (`accumark_pds.summarize(...)['grade_refs']`).
- **`.RUL` needs no reverse engineering at all** — it is ASCII with a
  documented ASTM header and one `RULE: DELTA n` block per rule, listing
  cumulative (X, Y) deltas per size in inches.
- **The internal piece name is the category, not the piece name.** All six
  rectangles carry `TASK1-CUTQTY3` in the metadata block because they were
  produced by Copy-Piece/Paste-Piece; the exported name lives at file offset
  0x15. Renaming via Save-As does not rewrite the category.
- **Copy-pasted pieces carry a stale second piece record.** Six of the eight
  files contain two piece records; the second is a byte-identical, unedited
  duplicate at storage position (23.3994, 13.2026) in. It has none of the
  edits that define its file. Any downstream tool must decode record 0 only —
  reading the last record would silently return the wrong geometry.
- **DXF grade annotation is unreliable.** `TASK5-GRADED`'s DXF writes four
  `# 1` texts, but only points 3 and 4 carry an explicit rule reference in
  the binary; `TASK6-CURVE` carries ten explicit references and its DXF
  writes no `#` texts at all. Treat the binary as authoritative.

## 5. Open items, and the capture that would close each

1. **Grade-rule value layout in the binary (48-byte object records).** Ten
   of eleven payload slots in `TASK5`'s rule-1 record hold 3937 (= 1.00 cm,
   the entered per-step increment); the eleventh is 0 and the other pieces'
   payloads are all zero. Eleven slots cannot be (X, Y) pairs and ten equal
   values do not reproduce the eight per-break increments in the `.RUL`.
   *Capture to disambiguate:* one rule with a **distinct value in every
   size-break row and X ≠ Y** — e.g. X = 0.1, 0.2, 0.3 … cm and
   Y = −0.05, −0.10 … cm. Slot order, pairing and sign convention all fall
   out of one file.
2. **`f1 = 0x0001` vs an explicit reference.** Points 1–2 of `TASK5` have
   `f1 = 1` and no reference while points 3–4 carry reference `1`, yet the
   DXF annotates all four. Either the Rule Number tool only took on two
   points (plausible given knowledge-base §10c/§11) or `f1 = 1` encodes an
   implicit default. *Capture to disambiguate:* a rectangle with rule 1 on
   two adjacent corners and rule 2 on the other two, exported twice — before
   and after applying the second rule.
3. **Unknown scalar fields**: `+0x12` in the field block (always 1);
   `n_sizes+2` u16 (5 with a 7-size table, 4 with a 9-size table); the
   `0x0200` constant; the per-size 0/1 flag; the 8-byte gap after the object
   array that appears only on 7-size tables. None affect geometry.
4. **Interior/drill points, internal cut-outs, mirror lines, multi-piece
   models, non-uniform ("Manual – Uneven") seam allowance, notch *type* and
   width** are untouched by this capture set. Non-uniform seam allowance is
   the highest-value next capture, because the `(begin, end)` pair in the
   segment record is clearly designed to differ and every sample has
   begin == end.

## 6. Using the decoder

```python
import accumark_pds as ap
s = ap.summarize_zip('TASK3-NOTCHED.ZIP')   # or ap.summarize(bytes); ap.decode* for raw structs
s['notches_in']        # [(0.0001, 2.1068), (0.0001, 6.0114)]  inches
s['seam_allow_in']     # [] or [(0.3937, 0.3937)]
s['grade_refs']        # [(point_id, object_record_id), ...]
r = ap.parse_rul(open('TASK6-CURVE.RUL').read())
r['rules']['11'][-1]   # (1.732, 0.866)  cumulative delta at the largest size
```

`ap.summarize()` returns validated fields only; raw block/record structures
are available underneath for further work on the unresolved fields.
