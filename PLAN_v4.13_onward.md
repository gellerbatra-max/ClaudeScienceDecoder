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
| v4.18 | Flip counts above 2; the half turn of Y with the bundle direction | 30 of 30 counts up to 4 in every spread; direction composes with 0x2000 | `flipcount/` | main `e0d6f6a`, pushed |
| v4.19 | The area a Block buffer adds | Rectangle dilation by (L+R) x (T+B), side order Left, Right, Top, Bottom; exact to 0.004 sq in | `blockarea/` | main `fe1f7b7`, pushed |
| v4.20 | More of section 1 | @472 / @476 sums, @486 pieces + 1, @496 lay rows, @498 block entries, the engine words | (fixtures above) | main `408b8f9`, pushed |
| v4.21 | Tilt limits and the `S` option | The marker keeps min(cw, ccw) in the table's unit; S pins each slot's chirality (905 of 922 vs 188 of 314) | `tilt/` | main `2b6136b`, pushed |
| v4.22 | A 45-degree placement | Tilt +-45.0 on top of the code (flip codes 9-12); the collar's frame is ambiguous when thin and tilted | `deg45/` | main `064ce2d`, pushed |
| v4.23 | Every marker on this machine (211 unique) | No exception; plaid / stripe values = 12 doubles of section 1; matching sections 9 / 23 / 24 named; @88 tolerance 2 | `plaid/` | main `5fc30f9`, pushed |
| v4.24 | Can the nest engine's own input file check the spec? | `frommed.mra`: orientation = `retrieval_orientation` (136 of 136), flags = Piece Options, outline = piece + block rectangle; nest spec `mirrored` / `retrieval_deg_by_slot` corrected | `engine/` | branch `v4.24-engine-input-check` |
| v4.25 | What are the plaid / stripe matching sections? | Section 9 = rules (points, categories, types, offsets), 24 = blocks with the outline vertex, 23 = start offsets; equal to the engine's rules on 816 instances | `plaid/` (more markers + engine files) | branch `v4.25-plaid-matching` |
| v4.26 | What does the engine do with the buffer, and in which frame? | Every section-6 entry = a symmetric rectangle growth (nine amounts, 223 pieces of 73 jobs); the collar is turned +90 (not 270); the rule for the turn is open | `engine/` (two more jobs) | branch `v4.26-residue` |
| v4.27 | What is left in the byte map? | Fabric weight / cost = the engine's (@596 / @600); zero bytes their own class; 105-371 non-zero unidentified bytes per marker, none needed by a nester | `engine/` (ZZN-B5, INTOMED_HEADERS.json) | branch `v4.27-byte-map` |
| v4.30 | What does the Nest Markers dialog change in the engine's input? | Rotation N, Flip: Enable, tilt and piece-gap overrides give the flags (40 of 40 style pieces); fabric cost / weight units per yard / oz per sq yd | `engine/` (job settings, four override jobs) | branch `v4.30-overrides` |
| v4.31 | What tilt does the engine take, and what are @404 / @438? (live) | The table's two sides x 10 (inches or degrees), width-independent; the order's Target Length (in) and Target Utilization (% x 10) | `engine/` (two jobs, TILT_JOBS.json) | branch `v4.31-live-rounds` |
| v4.32 | Plaid Y offset; can the collar's frame rule be found live? | Y offset verified (live, 6 markers / 240 instances); PDS rotation is not stored, so a vertical-grain piece cannot be made: the grain hypothesis stays open | `plaid/` (ZZPQ-M, ZZ-PLAID-Y2) | branch `v4.32-plaid-notch-collar` |
| v4.33 | What flags the collar's quarter turn in the engine? | bit 0x0200 of the slot word @+60 (14 of 14 turned pieces, 119 of 119 others; works unplaced; decides the 45-degree collar); the sign of the turn is not stored | `engine/FRAME_TURNS.json` | branch `v4.33-legacy-frames` |
| v4.34 | Notch numbers above 5 on a corner point | corner notches were dropped by the stream read and the nest spec: now `corner_notches` (piece == stream 201 of 201 + 86 records); the streams of six unverified records show a corner type 9 (not clamped: a hint), an edge notch is clamped to 5; a live PDS corner notch above 15 not run | none new | branch `v4.34-corner-notches` |
| v4.35 | Corner notch numbers, live | a DCU-imported corner notch is code 5 in piece and stream (clamped like an edge notch); the raw 9 of a real style is another creation path [?]; an unverified record (head area 101.364 vs polygon 93.000) is open | `notchnum/ZZCN*` | branch `v4.35-corner-notch-live` |
| v4.36 | Is the ZZCN area gap the corner notches? | yes: the no-notch and edge-notch controls verify, the two-corner-notch piece has +8.364 sq in, +0.307 in and a +1.092 in taller stored box; the dimension behind it is open | `notchnum/ZZCN2*` | branch `v4.36-corner-notch-control` |
| v4.37 | What decides the engine's quarter turn? | offline: not aspect, grain, internal lines, fold or the piece meta words (86 pieces, one turned); open | none | branch `v4.37-turn-negatives` |

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
| 7 | **MOSTLY DONE v4.27** (byte map: unidentified non-zero bytes 933-1,182 -> 105-371 per marker; fabric weight / cost @596 / @600 identified; open: section 5, the doubles @404 / @438, a few words): Section 1 counters, trailer state words, section 5 (Annotation copy) | Byte-map coverage | Offline | offline |
| 8 | **MOSTLY DONE v4.34** (offline: corner notches read and in the nest spec, a corner type 9 seen unclamped [hint]; open: a live PDS corner notch above 15, how the cutter draws corner vs edge notches): Notch numbers above 5 on a corner point; whether the cutter draws different shapes for numbers that read the same code | Notch fidelity | Live in PDS plus a marker plot | GUI-heavy |
| 9 | **DONE v4.19** (exact to 0.004 sq in on 18 slots, unequal block): the exact area a Block buffer adds (the 7.2% BACK-piece excess) | Area checks on blocked markers | Offline from the block-buffer fixtures | offline |
| 10 | **PARTLY DONE v4.26 / v4.33** (v4.33: which pieces the engine turns = the slot bit @+60 0x0200, works unplaced; sign and WHY open) (the sign: the engine's outline is the stream outline turned +90, not 270; the rule that turns it is open): why the collar needs +90; older-vintage multi-row lay limits (open) | Robustness on older markers | Needs an asymmetric collar-like piece; older markers from the user | low priority |
| 11 | **DONE v4.25** (sections 9 / 23 / 24 = rules / start offsets / blocks with the outline vertex; 816 instances and 1,264 points equal the engine's; the plaid / stripe values were v4.23): plaid / stripe MATCHING rules | Nesting a plaid job | Decoded against the match tables and the engine's `frommed.mra` | offline |
| 12 | **PARTLY DONE v4.24** (`accumark_engine.py`, `engine/`): the engine's `frommed.mra` as an independent check: orientation 136 of 136 (3,460 of 3,508 over 73 jobs), flags 20 of 20, outline = piece + block rectangle 20 of 20; v4.30 / v4.31: the job's overrides give the flags, the engine reads the tilt limits from the TABLE (-round(10 cw) / +round(10 ccw)), the three odd `MWS` jobs ran before the table gained S | The best ground truth for the job spec | Offline: parse it, compare per job | offline |

Recommended order: ~~2 and 3 together in one live round (v4.18)~~ done; next 7 and 9 offline while nothing else is waiting, then 4 and 6, then 5, then 8 and 10.

## 6. Where things stand

* Everything up to and including v4.28 is on `main` and pushed to `origin/main` (v4.28 merge commit `026c8df`). The three suites pass on every version (selftest PASS, dataset_test 36/36, robustness 730/730). Standing order of 2026-09-25 (follow the ranked list, commit and push as suitable, keep issues for the end): everything that could be done offline or with the engine's own files is done.
* The scratch objects from v4.17 (`ZZQ-*`) are deleted; the byte evidence is in `twoply/`. The older `ZZQB-*` / `ZZQL-S` objects belong to earlier work and were left alone.
* What is left (needs a live round, older samples, or the user): item 1 (`ALL GMT WAY` table, the user's); the rule that turns the collar +90 in the engine frame (item 10, needs a second collar-like piece in PDS); the table-tilt to engine-limit conversion and the `S` rows whose FLIP_GROUP is 0 (item 12, one live round); item 8 (notch numbers above 5, PDS); section 5 and a few section 1 words (item 7, low value); older multi-row lay-limit vintages (item 10, older markers). A readable version of this plan: the Artifact page.
