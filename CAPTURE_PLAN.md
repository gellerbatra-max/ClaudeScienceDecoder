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

**CAP-C12-TWOINTLINES** · C00 rectangle + a *second* internal line —
**DONE (round 2)**: a plain open 2-point line gets the same `0x0049` tag as
`CAP-C60-CUTOUT`'s closed circle, distinguished only by its terminator
(`3` open vs `6` closed) — confirmed with a second independent sample.
Labels stayed sequential (no jump) in this capture, suggesting the `L04,
L08…L11` jump seen on `CAP-C10-PENT` correlates with editing perimeter
points after the piece's first save, not merely with having a second
internal object. See FORMAT_SPEC.md §5.2 and CAPTURE_LOG.md.

**CAP-C13-LONGNAME** · rectangle identical to C00 but named with 30
characters — **DONE (round 2)**: file grew by exactly 18 bytes (the name's
length difference from C00's 12 characters), and `_find_field_block`
locates the metadata block at the identical header offset in both files —
confirms the header name (§1) is a fixed-width slot while the piece-record's
own name string (§2) is genuinely length-prefixed. See FORMAT_SPEC.md §1.

**CAP-C14-ANNOT** · rectangle with a different annotation/description text
(C00 will read `RECTANGLE`) — **DONE (round 2)**: a piece made with
Create→Collar instead of Rectangle reads `annotation = "collar"` (lowercase,
vs `RECTANGLE`'s uppercase) — confirms `annotation` is a literal
per-creation-tool string parsed as length-prefixed text. See
FORMAT_SPEC.md §2.

**Phase 1 status: all five items done** (`CAP-C10-PENT`/`CAP-C11-HEX` were
already completed earlier in round 2). The large 847/1852/1312-byte
tag/length/value tail sections themselves remained unparsed byte-for-byte
at the time; these five captures resolved the *count-scaling* fields
(perimeter count, internal-line kind/open-closed, header vs piece-record
name/annotation string handling) rather than the full tail-section grammar.

**Update (tail-section decode, no new captures):** the tail is now fully
parsed as a pre-table header + two perimeter snapshots + a TLV-encoded line
table — see FORMAT_SPEC.md §10/§11 for the grammar and `accumark_pds.
coverage()`/`check_line_table()` for the validation. 93–99.5% of every
capture's bytes are now `identified`, up from the tail being entirely
opaque; remaining `[?]`s are catalogued in FORMAT_SPEC.md §12.

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

**CAP-C61-MIRROR** mirror/fold line — **DONE (round 2, follow-up session)**:
the original crash diagnosis above (3 extra u16 fields) was wrong; the real
cause was a single mis-modeled field (`len_annot` read as u32 when it's
really u16 + a separate, previously-always-zero flag field) plus
metadata's `n_perimeter` over-counting by one on this piece. Both fixed;
`CAP-C61-MIRROR` now decodes with dxf residual 0.000000. See FORMAT_SPEC.md
§2/§4 and CAPTURE_LOG.md's CAP-C61-MIRROR row.

**CAP-C62-DART** dart or pleat — **DONE (round 2)**: Advanced→Darts→Add cuts
a dart directly into the perimeter as 3 new points (two dart-leg points plus
an apex), not an internal line. Exposed and fixed two decoder bugs along the
way (`f2` is a trailer byte count, not a 0/1 flag; two unbounded-loop hangs
on false-positive metadata matches). See FORMAT_SPEC.md §4 and
CAPTURE_LOG.md's CAP-C62-DART row.

**CAP-C63-MODEL** a two-piece model exported together — **DONE (round 2)**:
answered directly, no decoder bug involved. A Model-level export (File→
Export→Export Models) is a completely different, much smaller manifest
format (621 bytes) that `decode()` correctly finds zero piece blocks in —
it doesn't embed either piece's geometry, just references them by name. The
"one file holds two genuine pieces" scenario does not occur via Model
export; the stale-duplicate-record case remains the only way two piece
blocks appear in one `.tmp`. See FORMAT_SPEC.md §8.

**CAP-C70-PASTED** · Copy-Piece/Paste-Piece C00, Save As a new name, export —
**DONE (round 2)**. `category=CAP-C00-BASE` confirmed directly as expected,
but `piece_records=1`, not the 2 originally guessed here — this sharpens
rather than contradicts the stale-second-record trigger rule: pasting a
piece reaches the same "placed, saved under a new name, never edited" state
as `CAP-C02-SAVEAS-NOEDIT`, and only a subsequent edit produces the second
record. See FORMAT_SPEC.md §8 and CAPTURE_LOG.md's CAP-C70-PASTED row.

**Phase 6 status: all five items done.**

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
