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
| `markers/` | (2026-09-09) six production markers of style 2303 + four drawn DXFs — regression fixtures run by `selftest.py` |
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
