# Handing this work to Claude Code on the Windows machine

## What to copy

Unzip `pds_decoder_handoff.zip` into a working folder on the Windows laptop
(e.g. `C:\pds-decoder\`). It contains:

| file | role |
|---|---|
| `accumark_pds.py` | the decoder — read an AccuMark piece file / `.RUL` |
| `verify_capture.py` | the validator — gates every new capture |
| `selftest.py` | proves the toolchain works before you touch PDS |
| `FORMAT_SPEC.md` | byte-level format spec, claims tagged `[V]` / `[?]` |
| `PDS_DECODE_FINDINGS.md` | what is solved, what is not, corrections to the GUI notes |
| `CAPTURE_PLAN.md` | the ordered list of captures to build, and why each one |
| `AGENT_KNOWLEDGE_BASE.md` | your own PDS GUI-automation notes, carried forward |
| `captures/TASK1…TASK6/` | the eight first-round captures — baselines + regression fixtures |
| `accumark_marker.py` | (2026-09-09) reader for marker / order / model objects, slot→piece binding, placement transform, grading + fold unfolding |
| `verify_marker.py` | (2026-09-09) the marker validator: report, `--expect`, `--dxf` against a drawn-marker DXF, `--baseline` section diff |
| `rotation/` | (2026-09-24) laid-marker rotations: five markers read straight from AccuMark storage (`.GT_mark`: four AccuNest runs with Rotation / tilt overrides, one needing approval, plus the unlaid `ZZC-M1`), three plotted DXFs and `GROUND_TRUTH.json` (the eight orientation codes, the tilt float, the collar frame); `accumark_marker.read_storage_marker` reads such files |
| `accumark_marker.parse_marker_snapshots` (v4.14) | a marker's sections 3 / 4 are its own copies of the notch table and the lay-limits rows and each piece row names its row: `mk['snapshots']`, per piece `lay_row` / `buffer_rule` / `flip_code`; the nest spec of a marker-only ZIP reads them (`source: marker snapshot`) |
| `notchnum/` | (2026-09-24) a piece made in PDS with notch numbers 3-30 and the marker made from it: a piece keeps the notch NUMBER (`accumark_pds.notch_numbers`), a marker only `min(number, 5)`; `accumark_marker.read_storage_piece` reads a `.GT_piece` file |
| `spread/` | (2026-09-24) four markers made from one order with one Lay Limits table of each spread (single ply, face to face, book fold, tubular): section 1 +216 = the spread; `mk['spread']`, `piece['major']` (= the row's M option) |
| `accumark_blockbuffer.py`, `blockbuffer/` | (2026-09-24) reader for Block / Buffer tables (`.GT_block` / bundled objects): rule number -> buffer or block, amounts per side, static and dynamic; `blockbuffer/` = three tables built in the Block Buffer editor + `GROUND_TRUTH.json` |
| `reference_nester.py` | (2026-09-24) a nesting engine that reads only a nest spec JSON (numpy, Pillow, shapely) and validates its own lay: the proof the spec is nesting-ready; `python reference_nester.py job.json --best --svg lay.svg` |
| `accumark_notch.py`, `notch/` | (2026-09-24) reader for Notch Parameter Tables (`.GT_notpt` / bundled objects): notch number -> kind, widths, depth; `notch/` = two tables built in the Notch editor + `GROUND_TRUTH.json` |
| `accumark_laylimits.py`, `laylimits/` | (2026-09-24) reader for Lay Limits tables (`.GT_lay` / bundled objects) and the rotation rules a row gives a nester; `laylimits/` = 13 tables built one setting at a time in the editor + `GROUND_TRUTH.json` + a real AccuNest experiment (`EXPERIMENT_W_ALTERNATE.*`) |
| `markers/` | (2026-09-09) six production markers of style 2303 + four drawn DXFs (2026-09-21: plus `1825D-SS21-UNLAID/`, two unlaid markers from another AccuMark install) — regression fixtures run by `selftest.py` |
| `MARKER_DECODE_PLAN.md` | marker format facts, status table, and what to ask for next |
| `pds_decoded.json`, `pds_decode_validation.csv` | reference decode of those eight |

Python 3.9+ with no third-party packages. First command on the laptop:

```
cd C:\pds-decoder
python selftest.py
```

That decodes all eight existing captures, checks each against its DXF, and
re-runs six known structural-diff cases including the two that must report
*no* change. If it prints `SELFTEST PASS`, the toolchain is good. If not, fix
that before starting PDS — a broken validator is worse than none.

## First prompt for Claude Code

> You are continuing a reverse-engineering project on the Gerber AccuMark
> native piece-file format. You drive AccuMark Pattern Design V17 on this
> Windows machine through Windows MCP (screenshot + mouse/keyboard; there is
> no API).
>
> Read these first, in order: `PDS_DECODE_FINDINGS.md` (state of play),
> `CAPTURE_PLAN.md` (what to build and why), `AGENT_KNOWLEDGE_BASE.md` (how
> this GUI actually behaves — it documents real traps: tool panels that
> silently ignore typed input, Escape discarding work, folder-rename failures
> in the Export dialog, and the Rule Number dialog's Track/Stop modes).
> `FORMAT_SPEC.md` is reference; you do not need to hold it in your head.
>
> Run `python selftest.py` and confirm `SELFTEST PASS` before opening PDS.
>
> Then work `CAPTURE_PLAN.md` in order, starting at Phase 0. For each item:
> 1. `mkdir` the destination folder before opening the Export dialog.
> 2. Build the piece in PDS. Create pieces fresh — never Copy/Paste — unless
>    the item says otherwise, and do not move the piece on the canvas between
>    a baseline and its variant.
> 3. Export both ZIP and ASTM DXF into that folder; tick "Include Grade Rule
>    Table" for anything graded. `dir` the folder to confirm the files landed.
> 4. Run the item's `verify_capture.py` command. **If it prints
>    `RESULT: FAIL`, or `no structural difference`, the GUI action did not
>    reach the saved piece: go back into PDS, redo it, Save As again,
>    re-export, and re-verify. Do not move on and do not explain the failure
>    away.** This is the exact failure that wasted a capture last round.
> 5. Append one line to `CAPTURE_LOG.md`: item id, what you did, verifier
>    verdict, and anything the GUI did that the knowledge base does not
>    already describe.
>
> After each phase, decode the new captures and update `FORMAT_SPEC.md`:
> promote a field from `[?]` to `[V]` only when a capture *demonstrates* it,
> and say which capture. If a capture contradicts the spec, change the spec —
> it was written from eight files and is expected to be incomplete, not
> right. Add any new PDS behaviour you discover to
> `AGENT_KNOWLEDGE_BASE.md`.
>
> Do not invent AccuMark behaviour you have not observed on screen, and do
> not report a capture as good on the strength of PDS's own "Process
> Completed" dialog — that confirms the operation ran, not that the file
> contains what you intended. `verify_capture.py` is the only acceptable
> evidence.

## The loop, in one line

`mkdir → build in PDS → export ZIP+DXF → verify_capture.py → log → next`

## Useful commands

```
python verify_capture.py CAP-C30-SEAM-UNEVEN
python verify_capture.py CAP-C50-DRILL1 --baseline CAP-C00-BASE --expect structural_change=yes
python -c "import accumark_pds as a, json; print(json.dumps(a.summarize_zip('CAP-C00-BASE/CAP-C00-BASE.ZIP')['grade_refs']))"
```

`verify_capture.py --help` lists every `--expect` key.

## A new unplaced (never-laid) marker arrives

Whatever AccuMark exports - your own, or a marker from another install - read it
before anything else:

```
python accumark_marker.py "some marker.zip" --inventory
```

It prints the cut order (width, order lines, pieces with cuts and mirrored
pairs, area to lay, the fabric length a 100%-efficient lay needs) and ends with
one of two lines:

- `DECODED CLEANLY` - every check passes, no warning was raised, and every byte
  in the sections the reader parses is explained. If the ZIP holds no piece
  objects the report says `GEOMETRY: none` - that is a limit of the export (no
  outlines, declared areas and boxes only), not a decode failure.
- `NEEDS A LOOK:` plus the failing checks and the named warnings
  (`marker_warnings`, `coverage_warnings`). The marker differs from everything
  seen so far. Do not trust the numbers above the line for that marker; add the ZIP
  under `markers/<NAME>/`, note it in a `MARKER_DECODE_PLAN.md` STATUS block, and
  find which fact broke (`python accumark_marker.py <zip>` lists every check row).

To MAKE a marker of your own to test a hypothesis (one setting changed at a time, an
as-generated marker on demand, reproducible to 18 bytes), follow the harness in
`MARKER_DATASET_DESIGN.md` - and never use Explorer's *Generate Marker* on a copy of an
order, it targets the original's marker.

To hand the job to a nesting engine: `python nest_spec.py "some marker.zip" --json job.json [--dxf pieces.dxf] [--svg pieces.svg]` (format in `NEST_SPEC.md`;
ends `NEST SPEC COMPLETE` or names the failing check).

How pieces may be turned lives in the **Lay Limits table**, which the marker only names (section 2). Export the marker *with its components* (the ZIP then bundles the table and the
spec's `rotation` says `verified`), or hand the table over: `--lay-limits NAME.GT_lay` (from `C:\userroot\storage\<AREA>\lay\`) or another ZIP that holds it. `python accumark_laylimits.py <zip or file>`
prints a table. A marker-only export of the user's real styles names `NEED- TWO WAY` / `ALL GMT WAY` / `G-LAYLIMITS`: those tables are not in the corpus, so their specs say `assumed`.

`--inventory --json` gives the same thing as data. The byte-level spec is
`MARKER_FORMAT_SPEC.md`; `python -c "import accumark_marker as m; ..."`
`m.marker_coverage(data)` says where the unexplained bytes are.

## Two things to keep in mind

**Byte coverage is ~25 %.** The decoder extracts every field the first round
set out to find, and validates them against the DXF, but it can only name a
quarter of the bytes in each file. It reads; it cannot write. Phase 1 of the
capture plan is what changes that, and until it lands, do not describe the
format as understood.

**The DXF is a check, not an oracle.** It matched the binary geometry
perfectly on all eight pieces, so use it for that. But its grade-rule
annotation is unreliable — TASK5's DXF wrote four `# 1` texts where the
binary carried two explicit references, and TASK6's wrote none where the
binary carried ten. Where they disagree, the binary is authoritative.
