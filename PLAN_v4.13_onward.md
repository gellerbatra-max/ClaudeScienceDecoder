# Plan for this working session: the AccuMark marker decode, v4.13 to v4.17 and what comes next

Written 2026-09-25 from the session's own record (CHANGELOG.md v4.13-v4.17, MARKER_FORMAT_SPEC.md sections 20-24, the memory notes). It states the goal, the rules the work runs under, the loop each step follows, what was done, and the ranked list of what is still open. It is a plan and a status page, not a format spec: the byte facts live in MARKER_FORMAT_SPEC.md.

## 1. Goal

The decoder must read **whatever marker AccuMark produces**, and "fully decoded" is measurable: a verified, nesting-ready job spec (`nest_spec.py`) plus a byte map (`marker_coverage`) whose unknown share keeps falling.

Every claim carries a status tag in the specs: **[V]** proved (live experiment or corpus, with the count), **[?]** open. Anything unseen must produce a named warning, never a silently wrong answer.

## 2. Rules the work runs under

* **Ground truth is made, not guessed.** Patterns, models, orders, markers and DXFs are created by my own processes on scratch copies, and the decoder is checked against what AccuMark itself wrote or plotted.
* **Own processes only.** Drive only processes started by `gerber_launch.py`, through the guarded `gerber_input.py --pid`. Never touch the user's open windows (Explorer, Easy Marking on CLD 4155B LACE 30, the CLD and Dataset Order editors, their Queue Submit, PDS, the Lay Limits ZZLL-3 window).
* **Scratch area `ZZ-CLAUDE-SCRATCH` only; nest and plot copies.** Copy with `amcopy`, remove my own objects with `amdelete` when done, keep the byte evidence in a fixture folder first.
* **Privacy.** The user's real support files carry staff first names: only redacted table bytes go in the repo, and the local branch `v4.8.1-real-418T-support-files` is never merged.
* **No workarounds for classifier denials.** Do not merge or push until the user says so (they have said "merged into main and push" after each version so far). Keep GUI bursts short: the user is often using the machine.
* **Commits** end with `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`. `__version__` stays `'3.0'`; "v4.x" is a CHANGELOG label.
* **Out of my hands:** the `ALL GMT WAY` Lay Limits table (2591A) is the user's to supply. Its DEFAULT row is already read from the marker (MWS, flip 1, single ply); its Bundling is inferred as All Bundle, Same Direction, unconfirmed.

## 3. The loop each version follows

1. Pick one open question; say in one line what would settle it.
2. Try offline first (corpus counts, byte diffs). Go live only when the corpus cannot answer.
3. Live: copy objects into scratch, change ONE variable, generate with AccuMark, keep the files.
4. Decode, cross-check against an independent source (plotted DXF, the order, the table, AutoMark / AccuNest output).
5. Code change (additive keys, old keys unchanged), a `selftest` section with real fixtures, a byte-patch mutation test, and a check that the test fails when the fix is broken.
6. Docs: MARKER_FORMAT_SPEC.md section, CHANGELOG entry with an **Open** line, NEST_SPEC.md / CLAUDE_CODE_HANDOFF.md rows, memory notes.
7. Run the three suites: `python selftest.py` (about 2 min), `python dataset_test.py` (36/36), `python robustness/run.py` (730/730, then `git checkout -- ROBUSTNESS_REPORT.md`).
8. Commit on a `v4.NN-...` branch, report, and ask whether to merge and push.

## 4. What this session did

| Version | Question | Result | Fixtures | Git |
|---|---|---|---|---|
| v4.13 | How does a laid marker say which way a piece lies (the 90-degree collar case)? | Low 3 bits of the slot word = placed orientation (`ORIENT_L`), float32 tilt at +38, collar needs a +90 frame; `.GT_mark` / `.GT_piece` storage-file reader; checked on 72 slots against plotted DXFs | `rotation/` | main `b5b94aa`, pushed |
| v4.14 | What tables does the marker carry itself? | Section 3 = the Notch Parameter Table, section 4 = the Lay Limits rows (12 bytes each), piece-row words (row index, buffer, flip, tilt, fabric count), section-1 counters at 480 / 482 / 490 / 492; marker-only ZIPs now read their own rotation and notch rules | (marker tables in the corpus) | main `26b99b1`, pushed |
| v4.15 | Notch number versus notch code? | A piece keeps the NUMBER (1-99), the marker only the CODE = min(number, 5). Corrects the v4.10 reading | `notchnum/` | main `56c0921`, pushed |
| v4.16 | Does the marker carry the table's spread? What sets the piece flag at +14? | Spread = section 1 u16 at file offset 520 (0 single, 1 face to face, 2 book fold, 3 tubular); the flag = the row's M (major piece) option; Bundling inferred from the stored presets. Corrects the v4.14 "no spread" statement | `spread/` | main `a97ef95`, pushed |
| v4.17 | How does a two-ply marker treat a piece cut once? | Slot bits 0x0080 = X flip, 0x0100 = Y flip (both = X,Y half turn); single ply lists the model's flips exactly, a two-ply marker lets each as-is instance absorb one flipped one (Y, then X,Y, then X); a piece cut once keeps a slot per garment; a no-rotation row keeps the retrieval direction (turn = 180 x (0x2000 XOR flip in {Y, X,Y})); chirality is not kept per slot on `MW` rows | `twoply/` | main `2267406` (branch commit `d39e2f1`), pushed |

Unknown bytes per marker fell from 1,111-1,753 to about 1,031-1,280 (roughly 1.06%) over v4.13-v4.16.

Corrections made on the way (kept in writing): v4.10 "marker notch code = notch number"; v4.14 "the marker does not carry the spread"; earlier readings of sections 3 and 4 ("00 00 b0 07 groups", "12-byte label-config header").

## 5. What is open, ranked

Ranked by value to a nesting consumer and by cost. "Live" means an AccuMark round with my own processes.

| # | Item | Why it matters | How | Cost |
|---|---|---|---|---|
| 1 | `ALL GMT WAY` table (user) | Confirms the inferred Bundling of the real 2591A | The user supplies the `.GT_lay` or a ZIP with it; then compare against `bundling_candidates` | none for me, waiting |
| 2 | **DONE v4.18** (30 of 30 cases, counts up to 4): three or more flips of one kind in a two-ply merge | Completes the two-ply rule for pieces cut 3 or 4 times (pocket flaps, ties) | Live, cheap: only the Model Editor FLIPS cells change; reuse the v4.17 recipe | one short round |
| 3 | **DONE v4.18** (re-scoped: a rotating row hides the retrieval direction, so tested on a no-rotation row in an alternating table, 16 of 16): the 0x2000 x Y composition | v4.17 proved it only on `W` rows | Live: AccuNest on a table whose rows rotate, read the placed directions | one round |
| 4 | **DONE v4.21**: why AccuNest and AutoMark swap mirrored and as-is instances on `MW` rows (the row allows the flip; S = no flip pins the chirality: 905 of 922 vs 188 of 314), and what the `S` option does | Decides whether `mirrored` in the nest spec is a demand or only a preset | Live: two tables identical except for `S`, same order | one round |
| 5 | **DONE v4.22** (a tilt of exactly 45.0 on top of the code; via a W row with flip codes 9-12, not Easy Marking): 45-degree placement | A nester that rotates by 45 needs the encoding | Live: Easy Marking `Rotate 45 CW` driven to a STORED marker (the last attempt was closed before storing); AccuNest's Rotation-45 override placed nothing off the 90-degree grid | GUI-heavy |
| 6 | **DONE v4.21**: the marker's single tilt value is min(cw, ccw), in the table's own unit (degrees with the unit bit) | Tilt limits in the spec | Live: a table with unequal cw / ccw limits | one round |
| 7 | **PARTLY DONE v4.20** (@486, @496, @498, the engine words @568 / @674, @472 identified; @476, @484, @488, @530 open; trailer and section 5 not started): Section 1 counters beyond the four known (+168, +172, +180, +182, +184, +190 ...), trailer state words, section 5 (Annotation copy) | Byte-map coverage | Offline first: twin diffs on the fixtures I now have (`spread/`, `twoply/`, `rotation/`) | offline |
| 8 | Notch numbers above 5 on a corner point; whether the cutter draws different shapes for numbers that read the same code | Notch fidelity | Live in PDS plus a marker plot | GUI-heavy |
| 9 | **DONE v4.19** (exact to 0.004 sq in on 18 slots, unequal block): the exact area a Block buffer adds (the 7.2% BACK-piece excess) | Area checks on blocked markers | Offline from the block-buffer fixtures | offline |
| 10 | Why the collar needs +90 (+90 and +270 look identical), older-vintage multi-row lay limits | Robustness on older markers | Needs an asymmetric collar-like piece; older markers from the user | low priority |
| 11 | **Added v4.23**: plaid / stripe MATCHING rules (directory slots 9, 23, 24): named and bounded, not decoded; the plaid / stripe values (section 1) done | Nesting a plaid job | Decode against the match tables and the engine's `frommed.mra` (both on this machine) | one offline round + maybe live |
| 12 | **Added v4.23**: use the engine's `frommed.mra` (100+ jobs) as an independent check of the nest spec (flags, gaps, tilt, outlines) | The best ground truth for the job spec | Offline: parse it, compare per job | offline |

Recommended order: ~~2 and 3 together in one live round (v4.18)~~ done; next 7 and 9 offline while nothing else is waiting, then 4 and 6, then 5, then 8 and 10.

## 6. Where things stand

* Everything up to and including v4.17 is on `main` and pushed to `origin/main` (v4.17 merge commit `2267406`). The three suites passed on the v4.17 branch (selftest PASS, dataset_test 36/36, robustness 730/730). Nothing is pending except the next version.
* The scratch objects from v4.17 (`ZZQ-*`) are deleted; the byte evidence is in `twoply/`. The older `ZZQB-*` / `ZZQL-S` objects belong to earlier work and were left alone.
* Next step: one live round for items 2 and 3 of section 5 (v4.18), unless the user picks another.
