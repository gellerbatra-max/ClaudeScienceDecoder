# Capture plan — what to build in AccuMark next, and why

Each item names the **unresolved field it closes**, the PDS steps, and the
`verify_capture.py` command that must pass **on the Windows machine, before
you move to the next item**. That last part is not optional: TASK4 in the
first round produced a file whose drill point had silently never been saved,
and nobody found out until the files were off the machine.

Conventions for every capture:

- Folder `CAP-<id>-<SLUG>/`, piece named the same, containing
  `<NAME>.ZIP` + `<NAME>.DXF` (the DXF export drops `<NAME>.RUL` beside it).
- **Create pieces fresh** (Create → Rectangle / Line), never by
  Copy-Piece → Paste-Piece, except where a capture explicitly tests pasting.
  Pasted pieces carry a stale second piece record and keep the *source*
  piece's category, which contaminates every differential comparison.
- **Do not move the piece on the canvas** between a baseline and its
  variant. The validator can label a rigid translation, but an unmoved piece
  gives a diff with nothing to label.
- `mkdir` the destination folder *before* opening the Export dialog
  (knowledge base §5), export ZIP **and** ASTM DXF into it, tick
  **Include Grade Rule Table** for anything graded, then `ls` to confirm.
- Run the verify command. On `RESULT: FAIL`, fix it in PDS and re-export.
  Never bank a failing capture and move on.

---

## Phase 0 — baseline and the no-op reference

**CAP-C00-BASE** · establishes the reference geometry
Create → Rectangle, 30 × 20 cm. No seam, no notch, no grade rule applied.
Save As `CAP-C00-BASE`, export.
```
python verify_capture.py CAP-C00-BASE --expect piece_records=1 \
  --expect perimeter_points=4 --expect notches=0 --expect seam_cm=0 --expect dxf_match=yes
```

**CAP-C01-REEXPORT** · **the most important capture in the plan**
Export `CAP-C00-BASE` a second time, to a second folder, with **no edit of
any kind in between**.
```
python verify_capture.py CAP-C01-REEXPORT --baseline CAP-C00-BASE --expect structural_change=no
```
This measures the bytes that differ between two exports of an identical
piece on *your* machine — heap residue and last-saved timestamps. Everything
downstream depends on that set being known, because it is the noise floor
against which "did my edit reach the file?" is judged.

---

## Phase 1 — the unparsed tail section (largest gap; blocks round-trip writing)

The decoder assigns only 24–35 % of each file's bytes to an identified field.
Roughly half the remainder is zero padding whose length rule is unknown, and
there is one large section (847 bytes in TASK1, two runs of 1852 and 1312 in
TASK6) carrying a tag/length/value grammar (`0b 04 <u32>`, `0c 04 <u32>`,
`0d 08 <u64>`, `10 00 <point>`) plus a re-listing of the perimeter with
one-character point names `'0'` and `'1'`. These captures make every field in
it that scales with a count identifiable by arithmetic.

**CAP-C10-PENT** · 5-sided piece, fresh. `--expect perimeter_points=5 --expect segment_points=2;2;2;2;2`
**CAP-C11-HEX** · 6-sided piece, fresh. `--expect perimeter_points=6`
Three point counts (4, 5, 6) turn "which offsets scale with n" into a linear
fit rather than a guess.

**CAP-C12-TWOINTLINES** · C00 rectangle + a *second* internal line.
Purpose: the internal-line list count field, and the `L%02d` numbering, which
currently jumps (`L04`, `L08`…`L11`) for reasons unexplained.
`--baseline CAP-C00-BASE --expect structural_change=yes`

**CAP-C13-LONGNAME** · rectangle identical to C00 but named with 30
characters. Purpose: separates length-prefixed strings from fixed-width
fields throughout the file, and confirms whether padding lengths are absolute
or relative.

**CAP-C14-ANNOT** · rectangle with a different annotation/description text
(C00 will read `RECTANGLE`). Same purpose, for the annotation string.

---

## Phase 2 — grade-rule values (the 48-byte object records)

The blocker: every rule captured so far uses **one uniform increment**
(1.00 cm, X = Y), so the eleven payload slots are indistinguishable from each
other. One rule with all-distinct values resolves slot order, (X,Y) pairing,
sign convention and unit in a single file.

**CAP-C20-RULE-DISTINCT**
In `RuleTable.exe`: new library `CAP-RULES-A`; smallest 2, base 8, step 2,
next size breaks 10, 12, 14, 16, 18 (type them in — they do not
auto-populate). Rule number 1, per size-break row:

| row | X (cm) | Y (cm) |
|---|---|---|
| 2–4 | 0.10 | −0.05 |
| 4–6 | 0.20 | −0.10 |
| 6–8 | 0.30 | −0.15 |
| 8–10 | 0.40 | −0.20 |
| 10–12 | 0.50 | −0.25 |
| 12–14 | 0.60 | −0.30 |
| 14–16 | 0.70 | −0.35 |
| 16–18 | 0.80 | −0.40 |

Save. In PDS assign `CAP-RULES-A` to a fresh rectangle, then apply rule 1 to
**exactly one corner**. Export with Include Grade Rule Table.
```
python verify_capture.py CAP-C20-RULE-DISTINCT --expect graded_points=1 --expect rul_n_rules=1
```
Note the **8–10 row matters**: in both earlier rule tables that row was left
blank, which is why TASK5's `.RUL` shows a zero delta between sizes 8 and 10.
Fill it this time.

**CAP-C21-RULE-TWO** · add rule 2 to the same library (X = 1.00 cm every row,
Y = 0). Apply rule 1 to corner 1 and rule 2 to corner 2.
`--expect graded_points=2` — and `rule_ids` must show two *distinct* ids.
Purpose: confirms the per-point → object-record mapping and that payloads are
per-rule.

**CAP-C22-RULE-NONE** · the same piece with `CAP-RULES-A` assigned but **no
rule applied to any point**.
```
python verify_capture.py CAP-C22-RULE-NONE --baseline CAP-C20-RULE-DISTINCT --expect graded_points=0
```
Purpose: settles whether the point flag `f1 = 0x0001` means "no grade rule"
or "rule 1 by default" — currently ambiguous, because TASK5's DXF annotated
four corners `# 1` while only two carried an explicit reference.

---

## Phase 3 — seam allowance

Uniform allowance is solved (per-segment `(begin, end)` int32 pair, 1 cm =
3937). Every sample has `begin == end` and all four segments equal, so the
pair's purpose is inferred, not shown.

**CAP-C30-SEAM-UNEVEN** · Advanced → Seam → Define, type **Manual – Uneven**:
1.00 cm on the left edge, 0.50 cm on the top edge, 0 on the other two.
```
python verify_capture.py CAP-C30-SEAM-UNEVEN --expect uneven_seam=yes
```
Purpose: per-segment independence, and whether a zero-allowance segment
clears its flag or writes an explicit 0.

**CAP-C31-SEAM-TAPER** · a tapered allowance along a single edge (different
at each end), if the tool offers it. This is the direct test of `begin` vs
`end`; if PDS cannot express it, record that in the plan and skip.

**CAP-C32-SEAM-REMOVE** · take C30 and remove the seam.
`--baseline CAP-C00-BASE` — does removal restore the original bytes, or leave
residue? This matters because six of the eight first-round files carry a
second piece record that appears to be inherited from the seam experiment.

---

## Phase 4 — notches

Only one notch type has been seen (`f1 = 0x0101`), with no width, depth or
angle field identified.

**CAP-C40-NOTCH-TYPES** · four notches on the *same* edge, one of each type
the Notch dropdown offers (Slit / T / Castle / V-notch), at 2, 4, 6 and 8 cm
from the corner. `--expect notches=4` — **DONE (round 2)**: Notch Type
(1-30) is the high byte of `f1`, not a bit flag; see FORMAT_SPEC.md §4.
**CAP-C41-NOTCH-WIDTH** · two standard notches with different width/depth, if
those are settable. — **DONE (round 2)**: Depth is not settable independent
of Type (no accessible Edit control in the panel) and is not stored in the
piece file at all — two same-Type notches are byte-identical apart from
(x, y).
**CAP-C42-NOTCH-ALLEDGES** · one notch on each of the four edges.
`--expect segment_points=3;3;3;3` — confirms notch→segment assignment order.
— **DONE (round 2)**: PASS; also exposed and fixed a `verify_capture.py` bug
where `segment_points` picked up stale-block L-line records once a piece had
more perimeter points (with notches) than edges.

Phase 4 is now closed.

---

## Phase 5 — interior / drill points (redo of the failed TASK4)

**CAP-C50-DRILL1** · C00 rectangle + one interior drill point.
```
python verify_capture.py CAP-C50-DRILL1 --baseline CAP-C00-BASE --expect structural_change=yes
```
If this prints `no structural difference`, the point did **not** save — go
back into PDS, place it again, Save As again, re-export. Do not proceed until
it passes. This is exactly the failure that wasted TASK4.

**CAP-C51-DRILL3** · three interior points at distinct positions → count
field and record stride.

---

## Phase 6 — remaining primitives, lower priority

**CAP-C60-CUTOUT** internal cut-out — **DONE (round 2)**: a circle drawn via
Create→Circles→Center with "Create New Piece" unchecked becomes a third
internal-list kind (header `0xFFFF/0x0049`), a closed N-point polygon,
terminator `6` not `3`. See FORMAT_SPEC.md §5.2.

**CAP-C61-MIRROR** mirror/fold line — captured (round 2), export PASSES, but
**decoding is not done**: `Modify→Fold Keep` (internal line required, not a
perimeter edge) produces a piece whose metadata header has 3 extra zero
`u16` fields, which crashes `accumark_pds.py`'s `parse_metadata`/
`find_point_table`. Follow-up: give `parse_metadata` a variant path for
Fold-Keep pieces. See CAPTURE_LOG.md's CAP-C61-MIRROR row for the exact byte
layout and GUI workflow (fold line must be internal; the tool silently
renames the piece to "Pn", needing a Save-As to restore the intended name).

**CAP-C62-DART** dart or pleat · **CAP-C63-MODEL** a two-piece model exported
together (tests whether one file can hold two *genuine* pieces, as opposed to
the stale-duplicate case). Not started.

**CAP-C70-PASTED** · Copy-Piece/Paste-Piece C00, Save As a new name, export.
`--expect piece_records=2` and `category=CAP-C00-BASE`. Confirms the
stale-second-record and category findings rather than leaving them inferred
from six accidental instances.

---

## Priority if time is short

1. `CAP-C01-REEXPORT` — nothing else is interpretable without the noise floor. **DONE (round 2)** — noise floor is 3 bytes at 0x48.
2. `CAP-C20-RULE-DISTINCT` — closes the single largest *semantic* gap. **DONE (round 2)**, plus bonus `CAP-C21-RULE-TWO` and `CAP-C22-RULE-NONE` — grade-rule object-record layout fully solved.
3. `CAP-C30-SEAM-UNEVEN` — the field most obviously designed to vary. **DONE (round 2)**, plus bonus `CAP-C31-SEAM-TAPER` — begin/end semantics solved.
4. `CAP-C50-DRILL1` — recovers a feature currently at zero evidence. **DONE (round 2)** — drill points solved (internal list tag 0x44).
5. `CAP-C10-PENT` + `CAP-C11-HEX` — the only route to full byte accounting,
   and therefore to writing files rather than only reading them. **DONE (round 2)** — also exposed that L-labels are creation-order, not perimeter-order.

Also captured ad hoc: `CAP-C00-BASE` (fresh baseline), `CAP-C02-SAVEAS-NOEDIT`
(isolates what actually creates the second piece record — it's editing, not
Save-As or pasting). All 13 round-2 captures pass `selftest.py`'s regression
table. Remaining items (Phase 1 tail-section byte accounting beyond the
priority list, Phase 4 notches, Phase 6 primitives) are still open.
