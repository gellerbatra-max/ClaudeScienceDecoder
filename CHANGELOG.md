# Changelog

## v4.33 (2026-09-25) - which pieces the engine turns: a bit in the slot (plan item 10)

`__version__` stays `'3.0'`. New fixture `engine/FRAME_TURNS.json`; live evidence from five AccuNest jobs of my own (a legacy AccuMark 9 sample jacket set in three fabric rows, LADIES-BLOUSE collar sizes, the twoply blouse).

* **The collar's frame is flagged in the slot** (MARKER_FORMAT_SPEC.md section 36): bit 0x0200 of the u16 at slot +60 is set on every slot of a piece the engine holds a quarter turn from its stream frame and on no other [V: 14 of 14 turned pieces, 119 of 119 others; on the 46 fixture markers only the 32 LADIES-BLOUSE collars set it]. It needs no placement, so an UNPLACED marker has its frames; it decides the 45-degree collar the home-box method (`frame_offsets`) could not (`frames_ambiguous` is empty there now).
* **Decoder:** `slot['frame_turned']`, `slot['engine_word']`; `frame_from_slots` / `piece_frames`; `mk['frames']`, `mk['frames_ambiguous']`, new `mk['frames_box_disagree']`; the inventory's slot has `frame_turn_deg`; **the nest spec's shape has `engine_frame_turn_deg`** (its docstring says how to use it with the engine-frame angles). The byte map marks @60 identified.
* **Only the size of the turn is stored, not the sign:** collar +90; the sleeve of the jacket set +90 on sizes 2 - 8 and -90 on 10 - 18. What decides the sign is open [?] (it matters only for a piece pinned to one direction). A float at slot +72 (+-(pi/2 - e)) rides along on some markers; not used.
* Selftest: a new section (evidence rows, the 46 fixture markers, an unplaced marker's frames and shape, three bit mutations) and the frame check of the v4.26 section now also asserts the bit (27 of 27); the v4.22 section's `frames_ambiguous` expectations became "the boxes cannot say, the bit does". All three suites pass.

## v4.32 (2026-09-25) - live: the plaid Y offset; PDS rotation is not stored; a piece's category is stored in the piece

`__version__` stays `'3.0'`. Live rounds of my own (Easy Order, Order Editor, Queue Submit, PDS, Model Editor, all my own processes). New fixtures `plaid/ZZPQ-M.GT_mark`, `plaid/ZZPQ-M-frommed.mra`, `plaid/ZZ-PLAID-Y2.GT_match`. Plan items 11 (rest), 10 (collar), 8.

* **Plaid offset Y verified** (MARKER_FORMAT_SPEC.md section 31): a copy of the match table `ZZ-PLAID-U2` patched with Relative stripe (Y) offsets of 2 and 1.5 cm, an Easy Order, Process, AccuNest: section 9's `f64` at +18 = 0.7874 / 0.5906 in = the engine's `MATCHING_OFFSET` y 7874 / 5906 (both Y types relative). 6 plaid markers, 240 instances, 352 rule points equal the engine's now. The match table layout note of my skill was one byte off (the stripe type is 1 byte at P+9, the stripe offset int32 at P+10); corrected.
* **The collar's frame (item 10) - what was tried:** the Model Editor's thumbnail of the LADIES-BLOUSE collar is tall with a vertical line (V17-made pieces are wide with a horizontal one): the engine frame is probably the GRAIN-aligned one and the stream the stored one. A vertical-grain piece cannot be made with V17 tools: the collar rotated 90 / 180 in PDS and saved came back with unrotated geometry, engine frame 0 - PDS does not store a rotation. Left as a hypothesis [?] in section 32.
* **Facts on the way:** a piece's CATEGORY is stored in the piece object (meta name): editing it in the Model Editor rewrites the piece file; the Easy Order Fabrics grid of this machine has Annotation, Target Length and Utilization columns (`easyorder_job.py` column map updated in the skill, `layout` / `columns` keys).
* **Open:** what turns the collar (needs legacy grain data); item 8 (corner-point notch numbers) was not run: only the piece side could differ, the marker keeps the code.

## v4.31 (2026-09-25) - live: the engine's tilt limits come from the table; the order's Target Length / Target Utilization

`__version__` stays `'3.0'`. Two AccuNest jobs and three orders of my own (Order Editor, Lay Limits table `ZZLL-TLT`, Queue Submit; my own processes). New fixtures `engine/ZZR-TL2.GT_mark`, `engine/ZZR-TL3.GT_mark`, `engine/TILT_JOBS.json`. Plan item 12, live.

* **Result** (MARKER_FORMAT_SPEC.md section 35): the engine takes its tilt limits from the Lay Limits TABLE, each side on its own: `CW = -round(10 cw)`, `CCW = +round(10 ccw)` with the table's inches (length tilt) or degrees as they stand, independent of the fabric width (10 of 10 categories of two jobs). Section 1 @404 / @438 are the order's Target Length (inches) and Target Utilization (% x 10) - 79 of 79 pairs and two
  live values; the engine's `TARGET_LENGTH` = area / (width x utilization), else the target length (80 jobs). The three `MWS` jobs of v4.30 are explained too: they ran BEFORE the table gained `S` (job 216-221 at 03:01-03:11, the table saved at 03:22:32; jobs 224 / 227 after it show `FLIP_GROUP` 2).
* **Code.** `mk['order_targets']`, the byte map (@404 / @438), the nest spec's `fabric.target_length` / `target_utilization_pct` / `target_length_at_utilization`, `accumark_engine.engine_tilt_from_table`, `engine_target_length`. **Checks.** `selftest` (new section): the tilt of 10 categories, the targets, a patch.
* **Open:** the same table read for the other Piece Options (F, P, O, Z) needs one job each.

## v4.30 (2026-09-25) - the job's Nest Markers settings decide the engine's flags; the units of the fabric cost / weight

`__version__` stays `'3.0'`. `accumark_engine` 1.1 (`parse_job_settings`, `engine_flags(options, overrides)`, `engine_tilt_limits`). New fixtures `engine/*.job_settings.txt` (the `Job Settings` block of nine jobs) and `engine/ZZROT-*.frommed.mra` (four override jobs). Plan item 12, offline.

* **Result** (MARKER_FORMAT_SPEC.md section 34): `Rotation N` = every category a rotation step of N degrees and no one-way flag; `Flip: Enable` = no no-flip group; a tilt override n = -10 n / +10 n on every category; `Piece Gap` = `GLOBAL_GAP` in inches - together with the Piece Options they give the engine's flags on all 40 style pieces of 8 jobs (28 without the overrides). That explains 4 of the 7 `S`-row jobs with `FLIP_GROUP` 0 (the other 3:
  probably a table edited after the marker). The dialog's fabric cost per metre / weight in gsm are stored x 0.9144 (per yard) / x 0.029493 (oz per sq yd): the units of the section 1 words of v4.27.
* **Code.** `accumark_engine.parse_job_settings`, `engine_flags(options, overrides=None)`, `engine_tilt_limits`. **Checks.** `selftest` (new section): 40 style pieces of 8 jobs, the flags without the overrides fail on 12, the cost / weight units of 5 jobs.
* **Open:** the tilt conversion of a table tilt (0.1574 in -> +-2, one data point); the 3 `MWS` jobs; a blank sixth style piece in `ZZROT-B`'s engine file.

## v4.28 (2026-09-25) - the engine's FOLD_LINE (documentation only)

`FOLD_LINE` of the engine's input file = the first point of the piece's fold (mirror) line from the middle of the unbuffered box, in the engine's frame [V on the two pieces whose stream carries the mirror line]; the collar's fold is horizontal in the stream frame like the BACK's, so the +90 turn is not a fold-direction rule (MARKER_FORMAT_SPEC.md section 32). No code change.

## v4.27 (2026-09-25) - the byte map's residue; the engine's fabric weight and cost

`__version__` stays `'3.0'`. New fixtures `engine/ZZN-B5.GT_mark`, `engine/INTOMED_HEADERS.json` (the header of the engine's OUTPUT file of five jobs). Plan item 7, offline.

* **Result** (MARKER_FORMAT_SPEC.md section 33): two float32 of section 1 (@596 weight, @600 cost) are the engine's `FABRIC_WEIGHT` / `FABRIC_COST` (49 of 49 jobs); the byte map counts unidentified ZERO bytes outside the parsed sections as their own class (`zero`), so `unknown` = unidentified non-zero bytes: **105-371 per fixture marker, 0.21%** (933-1,182 before); @472 / @476 identified.
  What remains is listed in section 33: none of it matters to a nester.
* **Code.** `mk['fabric_weight_cost']`, the byte map (`zero` class, @472 / @476, @596-603). **Checks.** `selftest` (new section; the byte-map row reports `zero`): five made markers against the engine's output header, the unmade marker 0 / 0, a patch, the residue of `ZZN-B5`.
* **Open:** section 5 (annotation table copy), the doubles @404 / @438, the words @484 / @488 / @494 / @522 / @530 / @588, the units of the cost / weight.

## v4.26 (2026-09-25) - the engine's outline: the buffer rectangle on every rule size, the collar's quarter turn

`__version__` stays `'3.0'`. New fixtures `engine/ZZPV-M`, `engine/ZZPS-M` (marker + `frommed.mra`: buffers of 0.0059 and 0.0118 in). Plan items 12 (outline) and 10 (collar frame), offline.

* **Result** (MARKER_FORMAT_SPEC.md section 32): the engine's outline of a piece = the marker's stream outline grown by the section-6 rectangle `(L+R) x (T+B)`, symmetrically about the middle of the box, **for every amount seen** (nine amounts on 223 pieces of 73 jobs, the real 3MM Buffer of 0.15 cm among them: growth equals `rect_growth` within 2%, box within 0.0001 in) - so the v4.24 statement
  "every block-buffer entry is applied as a rectangle" now rests on Buffer and Block amounts alike; the piece gap `GLOBAL_GAP` is a separate job setting. **The LADIES-BLOUSE collar is turned +90 (counter-clockwise) in the engine's frame, not 270** (0.28 in from the +90 turn, 0.98 from 270): the sign v4.13 could not decide. Every other piece of the corpus is in the stream frame; what decides the turn is still open.
* **Code.** None (a measurement release); `selftest` (new section): 27 pieces of 6 jobs, growth / box / frame, the collar +90 against 270. **Open:** the rule that turns the collar; the engine's `FOLD_LINE`; the length-to-angle conversion of a table tilt.

## v4.25 (2026-09-25) - the plaid / stripe matching rules (sections 9, 23, 24)

`__version__` stays `'3.0'`. New fixtures in `plaid/` (four more markers made with Matching tables, `ZZPU-M`, `ZZPY-M`, `ZZP2-M`, `ZZC20-STD`, and the engine's `frommed.mra` of each job). Plan item 11, offline: the engine's own per-piece rules (v4.24) were the ground truth.

* **Result** (MARKER_FORMAT_SPEC.md section 31): section 9 = one 42-byte record per rule (first / second point, first / second category, X / Y type relative / none / same, offset x / y, a fabric rule has category 0 = the marker), section 24 = the blocks (category, bundle, point number, **vertex** = the point's 0-based index in the piece's outline), section 23 = the block start offsets. **Every rule
  of 816 piece instances and every one of 1,264 rule points equal the engine's `frommed.mra` (22 jobs; the point = the outline vertex less the middle of the piece's box, worst 0.0001 in)**; all 25 markers with matching sections on this machine read cleanly.
* **Behaviour change:** `parse_marker` gives `mk['matching']` (`None` without a Matching table); the "matching data not decoded" warning is gone (a marker whose sections do not read cleanly gets a warning that says so); the byte map counts sections 9 / 23 / 24 as identified; the nest spec has `matching` (rules) and `shapes[].matching` (each shape's points, in the shape's frame).
* **Code.** `accumark_marker.parse_matching`, `matching_for_category`, `MATCH_TYPES`; `marker_warnings`; `marker_coverage`; `nest_spec._matching_block`. **Checks.** `selftest` (new section, the v4.23 plaid section adapted): five markers x their engine files (204 instances, 310 points), the ZZ-PLAID rules read back, four byte patches caught (a type, a vertex, the separator of section 24, a start offset of section 23), the nest spec.
* **Open:** the offset Y and the end triple of section 9 (zero / constant in every sample); older matching vintages (none seen); what AccuNest honours; item 11's live half (a Matching table on other pieces than `ZZPLD`) is not needed for the format - the vertex is stored - but would add variety.

## v4.24 (2026-09-25) - the nest engine's own input file as a check; retrieval orientation

`__version__` stays `'3.0'`. New module `accumark_engine.py` (reads `frommed.mra`), new fixtures `engine/` (the `frommed.mra` of jobs 266 / 269 / 272 / 275, made from `twoply/ZZQ-W`, `twoply/ZZQ-A`, `flipcount/ZZR-S`, `deg45/ZZR-45`). Plan item 12, offline only.

* **Result** (MARKER_FORMAT_SPEC.md section 30): the engine's per-instance `ANGLE` / `FLIP_FLAG` equal `retrieval_orientation(model flip, bundle direction, row flip code)` on 136 of 136 instances of the four jobs and on 3,460 of 3,508 over 73 jobs (the 48 exceptions = one LAID marker, whose `ANGLE` is the placed angle). The per-category flags follow the Piece Options
  (`NAP_GROUP` = W, `FLIP_GROUP` = S, `ROTATE_INCR` 0 / 45 / 90 / 180 = W / 4 / 9 / else): 20 of 20. The engine's outline = the piece + the block rectangle: `rect_growth` reproduces its area growth within 1.5% on 20 of 20 kinds - an independent proof of the v4.19 block model. `AM_AREA` = the slot area on 353 of 360 piece kinds.
* **Behaviour change (nest spec):** `demand[].mirrored` is now the engine's `FLIP_FLAG` (the row's flip code composed onto the model flip: a `MW` row with code 9 makes the model's as-is instances mirrored), `retrieval_deg_by_slot` is new (the engine's `ANGLE`), and `allowed_deg_by_slot` turns from the retrieval angle, not from the model's own turn (code 7 = 270). Earlier versions ignored the row's code here.
* **Code.** `accumark_laylimits.code_transform`, `retrieval_orientation`; `accumark_engine.parse_frommed`, `parse_pieces`, `read_engine_file`, `engine_flags`; `nest_spec` (`mirrored`, `retrieval_deg_by_slot`, `allowed_deg_by_slot`, `mirror_binding` unchanged). **Checks.** `selftest` (new section): 136 instances vs `retrieval_orientation` and vs the nest spec, a wrong 0x2000 reading is caught on all 136, 20 style pieces vs `engine_flags`, 20 outlines vs `rect_growth`, `AM_AREA`.
* **Open:** the length-to-angle conversion of a table tilt (`0.1574 in` -> +-0.2 degree: one data point); the 7 of 37 jobs with an `S` row whose `FLIP_GROUP` is 0 (a Nest Markers override?); the matching rules of each piece (plan item 11); `BUNDLE_ID`, `FOLD_LINE`, `RIGHT_FLAG`.

## v4.23 (2026-09-25) - every marker on this machine read; the plaid / stripe values; the matching sections named

`__version__` stays `'3.0'`. New fixtures `plaid/` (two plaid markers, the matching table, the engine's input file of job 117, `GROUND_TRUTH.json`). Not a plan item: a read-only scan of all 219 marker files in every storage area of this machine (the corpus of "whatever AccuMark produces" is much larger than the repo).

* **Result** (MARKER_FORMAT_SPEC.md section 29): no exception on any of 211 unique markers, 176 fully clean. Three things fixed or decoded: (1) the order copy of the `OLDFiles` production vintage lists sizes ordered 0 times - the order-copy check failed on 64 of the 80 real markers; fixed, and the nest spec's `order_lines` drops them; (2) the plaid / stripe repeats and
  offsets are twelve doubles of section 1 (`mk['plaid_stripe']`, nest spec `fabric.plaid_stripe`), which explains the "directory word 41 is 0x32617c1b" seen on 27 markers (the first double overlaps the directory state words); (3) the slot `@88` rule accepts a per-piece spread of 2 (a real production piece).
* **Named, not decoded:** plaid / stripe MATCHING rules (directory slots 9, 23, 24, 25 markers): `MATCHING_SECTIONS`, a warning, `opaque` in the byte map. The ground truth for decoding them exists on this machine (match tables, orders, and the engine's `frommed.mra` text of every AccuNest job).
* **Code.** `mk['plaid_stripe']`, `mk['has_plaid_stripe']`, `MATCHING_SECTIONS`, the matching warning, the byte map (twelve doubles identified, sections 9 / 23 / 24 opaque), `_sig88_model` tolerance, the order-copy check, `nest_spec`. **Checks.** `selftest` (new section): the plaid values, the matching warning, coverage, the nest spec, a stray word 41, the `@88` tolerance;
  `LIVE` corpus numbers unchanged.
* **Not changed / for the record:** the real markers of `OLDFiles`, `CLD`, `Dataset` were only read; none was copied into the repo. **Open:** the matching rules (sections 9, 23, 24) - decode against `frommed.mra`; sections 16 (one old sample); using `frommed.mra` as a check of the nest spec (shapes, flags, gaps).

## v4.22 (2026-09-25) - a 45-degree placement is a tilt of exactly 45 degrees; two more words of section 1

`__version__` stays `'3.0'`. New fixtures `deg45/` (unmade + AccuNest-made marker, the plot DXF, the table copy, `GROUND_TRUTH.json`). Plan item 5, solved without Easy Marking (the last attempt stalled at its Override / Select Piece dialog): a `W` row with the 45-degree flip codes 9-12.

* **Answer** (MARKER_FORMAT_SPEC.md section 28). A table copy whose rows are all `MW` with flip codes 11 / 9 / 10 / 12 / 7 on front / back / collar / cuff / sleeve, nested by AccuNest: the slots carry tilt floats of exactly +-45.0 on top of the low-bits orientation, the sleeve (90-degree code) 0. The decoded outlines lie on the MarkPlot plot to 0.16 in
  on 18 of 18 slots (tilt ignored or inverted misses by 3-11 in). No separate 45-degree encoding exists.
* **A limit found.** A thin piece tilted by 45 degrees has the same bounding box in every frame, so `frame_offsets` chose frame 0 for the collar (7.1 in off the plot; +90 gives 0.16). `frame_ambiguous` / `mk['frames_ambiguous']` name the pieces the home boxes cannot decide (back, collar, cuff here; none on any earlier marker) and `place_marker`'s inventory warns.
* **Section 1.** @472 = the sum over the slots of the record prefix word 3 (the record's attribute points, 94% of 1,319 records), @476 = the sum of prefix word 4 (76 of 100 markers exactly; exceptions listed in the spec). Refines v4.20's per-piece finding.
* **Code.** `frame_ambiguous`, `mk['frames_ambiguous']`, an inventory warning. **Checks.** `selftest` (new section): tilt floats per piece, the plot fit with mutations (tilt ignored / inverted), the collar with and without its frame, the ambiguity list (and none on four earlier markers), the two section 1 sums on 33 fixtures.
* **Scratch state:** `ZZLL-45`, `ZZR-45` (order, marker) removed; my Lay Limits, Order, Queue Submit and MarkPlot processes closed. UI notes: the Lay Limits Editor's flip-code cell needs a click to select, a second click to edit, then the in-cell arrow (real x 577) to open the list; the list's last item (12) is reached with the keyboard (Down x 11, Enter).
* **Open.** Why the collar's stream frame is a quarter turn off (its record has no grain line and an extra 0x46 tag); the meaning of record prefix words 0-2, 4; plan items 8, 10 and the rest of item 7 (@484, @488, @530, @674 counts, the trailer, section 5).

## v4.21 (2026-09-25) - the marker keeps the smaller tilt limit; the S option pins a slot's chirality

`__version__` stays `'3.0'`. New fixtures `tilt/` (two markers, the table copy, `GROUND_TRUTH.json` with the twelve Piece Options read from the editor). Plan items 6 and 4, one live round (my own Lay Limits Editor and Order Editor), the second one closed by the checklist text and by data already held.

* **Item 6** (MARKER_FORMAT_SPEC.md section 27). A table with unequal clockwise / counter-clockwise limits (cm and degrees) -> the marker's section 4 and the piece row's tilt words hold `min(cw, ccw)`: back 0.5 / 0.2 cm -> 0.0787 in, collar 5 / 10 degrees -> 5.0 (unit bit 0x20), cuff 0.3 / 0.5 -> 0.1181, front 20 / 15 cm -> 5.9055, a zero side -> 0.
  The nest spec notes it and `_snapshot_diff` compares with the smaller.
* **Item 4.** The Piece Options checklist: W = one way, flip in X-axis, no rotation; S = allow 180 degree rotation, no flip (all twelve options in the spec). Cross-tab over 42 placed markers / 1,240 slots of asymmetric pieces: rows with S keep each slot's chirality (905 of 922; the 17 exceptions are the flip-override runs `ZZROT-*`), rows without
  S 188 of 314, and the number of mirrored placements per piece differs from the model's in 48 of 102 groups. So the mirrored flags are a preset on a flip-allowed row and a constraint on an S row: `demand[].mirror_binding` = `kept` / `free` (S is not a "symmetric" flag: it forbids flipping).
* **Code.** `nest_spec.py`: `demand[].mirror_binding`, the tilt comparison; `accumark_laylimits.py`: the tilt note, the section-4 docstring.
* **Checks.** `selftest` (new section): the tilt words and rows of both markers against the table values (10 rows, cm and degrees, the zero side), the snapshot-versus-table comparison, the note in the spec, S rows 38 of 38 against other rows 24 of 50 on the fixtures (not `rotation/`), `mirror_binding` per shape of the flipcount marker.
* **Scratch state:** `ZZLL-TLT`, `ZZLL-SM/SS/SW` (made, unused), `ZZR-T`, `ZZR-T2`, `ZZR-P` removed; my Lay Limits and Order Editors closed. One oddity: the Lay Limits Editor's Piece Options popup swallows Alt+F4 - click the Comments box first, then close.
* **Open.** What the F, P, O, Z options do to a marker (only their letters are stored: b2 / b3 bits); plan items 5, 8, 10 and the rest of item 7.

## v4.20 (2026-09-25) - three more counters of section 1, the two engine words, and the attribute-point count

`__version__` stays `'3.0'`. No new fixtures (the folders `twoply/`, `flipcount/`, `spread/`, `rotation/`, `blockarea/` and the corpus were enough). Plan item 7, offline: correlate every varying section 1 word with everything the decoder can count.

* **Found** (MARKER_FORMAT_SPEC.md section 26): @486 = pieces + 1, @496 = the rows of the marker's own Lay Limits table, @498 = the block-buffer entries (97 of 97 markers each); @568 = 128 and @674 = 3 after AccuNest, 0 and 19 on an unmade or AutoMark-made marker (16 fixtures); @472 = the attribute points
  (notch points plus numbered turn points) summed over the slots (29 of 29 fixture markers; exceptions documented: the 2303 vintage, two older sets, and the tubular `ZZQ-T` whose sleeve is missing from the count - its Process ended with warnings); @476 exact per piece on the LADIES-BLOUSE set (10 / 8 / 4 / 8 / 4) with an unknown rule.
* **Code.** `mk['header_counts2']`, `mk['engine_words']`, `mk['nested_by']`, one new check row (the three counters), five words marked identified in the byte map.
* **Checks.** `selftest` (new section): the three counters on 97 markers, @472 on the fixture folders (the tubular exception pinned at -24), @568 / @674 on 16 fixtures, a byte patch on each counter is noticed.
* **Open.** The rule of @476, @484 (slots - c), @488, @530; what @674 = 6 / 9 / 12 counts; the rest of the byte map (section 2's names table, section 5, the trailer).

## v4.19 (2026-09-25) - the area a Block adds; the side order of a block-buffer entry

`__version__` stays `'3.0'`. New fixtures `blockarea/` (unmade + placed marker, the lay table copy, `GROUND_TRUTH.json`). Plan item 9 (PLAN_v4.13_onward.md), started offline and finished with one live round.

* **Answer** (MARKER_FORMAT_SPEC.md section 25). A placed slot of a blocked piece stores its record's area plus the growth of the outline by a rectangle of (left + right) x (top + bottom) in the piece's own frame, turned with the piece. Offline the single corpus data point (BACK, 1 cm block, +44.095) already
  matched the exact Minkowski sum with a square (44.09); a uniform offset (the v4.12 note's 652.9) does not. The live round used `ZZBB-X1` rule 9 (a block with unequal sides 0.0433 / 0.0866 / 0.1299 / 0.1732 in) on every row of a copy of the ZZLL-1 table, AutoMark: 18 placed slots of 5 pieces at
  all four quarter turns and mirrored agree to 0.004 sq in; the home box pads follow the two totals, turned with the piece (the collar with its 90-degree stream frame).
* **Side order settled:** a section-6 entry is `[left, right, top, bottom]`.
* **Code.** `rect_growth` (pure Python, scanline over the piece and every edge swept by the rectangle), `_explain_block_areas` (runs in `parse_marker`: `binding['area_ok']` / `binding['block_added']`), `unplaced_inventory` `slots[].block_added`. The two failed check rows and the "declared area does not equal the bound record's" warning of `ZZC-M3` and
  `ZZN-F1` disappear (`LIVE_ANOMALIES` updated: 0 failing rows, 0 warnings); a slot whose area is neither the record's nor the block's still fails.
* **Checks.** `selftest` (new section): 18 slots explained to 0.01 sq in, the home box pads (18), the two earlier markers, swapped totals / a square / no block rejected, `rect_growth` against a closed form, byte patches (a slot area 1% off is noticed, one equal to its record is accepted as a buffer); mutation-tested (the decoder with the x and y pairs swapped fails).
* **Scratch state:** `ZZLL-BLK`, order and markers `ZZR-K`, `ZZR-KA` removed; my Lay Limits, Order and AutoMark processes closed.
* **Open.** Percentage amounts and the Segment amount on a placed marker; whether an unplaced slot's block appears anywhere before it is laid; plan items 4-8, 10 (item 1 waits for the user's table).

## v4.18 (2026-09-25) - flip counts up to 4 in every spread; the half turn of Y composes with the bundle direction

`__version__` stays `'3.0'`. New fixtures `flipcount/` (4 markers + `GROUND_TRUTH.json`). Plan items 2 and 3 (PLAN_v4.13_onward.md), run as one live round after the user asked for the plan to be followed step by step.

* **Item 2, done.** A model copy (`ZZR-BLOUSE`, FLIPS edited to BACK (0,3,0,0), COLLAR (2,3,0,0), CUFF (1,0,3,0), FRONT (2,2,2,2), SLEEVE (4,1,1,1)), two size-10 garments, three tables: single ply (the baseline: the slots are exactly the flips), face to face and book fold. The v4.17 merge
  rule (each as-is instance absorbs one flipped one, Y first, then X,Y, then X) predicted **30 of 30 (bundle, piece) cases** on the first try, counts up to 4 and two absorptions at once included. MARKER_FORMAT_SPEC.md section 24 updated.
* **Item 3, done and re-scoped.** "On a rotating row" cannot be tested: the nester may turn the piece there. The composition of a Y / X,Y half turn with the bundle's 0x2000 bit was tested on a no-rotation row inside an alternating table (ZZLL-1, FRONT `MW`), AccuNest Draft, no overrides: the front
  piece's 16 instances (each of the 8 bundle x flip combinations twice) all lie at `turn = 180 x (0x2000 XOR flip in {Y, X,Y})`, including Y in the alternating bundle (-> 0). Per-instance chirality was kept on 10 of 16 (the rows with a rotation code, e.g. the sleeve, are not tied to the direction: 0 of 14).
* **Code.** None: the v4.17 decode already implements the rule; this version adds the proof (and no new warning was needed: `marker_warnings` was empty on all three unmade markers).
* **Checks.** `selftest` (new section): 30 flip multisets against the model / the merge rule on 3 spreads, the front piece's direction on 16 of 16 slots with all 8 combinations present twice; mutation-tested (merge order, Y without its half turn). See the STATUS line for the suites.
* **Scratch state:** `ZZR-BLOUSE`, `ZZR-S/F/B` (orders and markers) removed; my Model / Order / Queue Submit processes closed; the original LADIES-BLOUSE model is byte-identical to its backup.
* **Open.** The `S` option's role in the chirality swaps; the rest of PLAN_v4.13_onward.md section 5 (items 4-10; item 1 waits for the user's table).

## v4.17 (2026-09-25) - the flip bits (0x0100 = Y) and how a two-ply marker merges pieces

`__version__` stays `'3.0'`. New fixtures `twoply/` (13 markers + `GROUND_TRUTH.json`). Request: "go to the next step" (open item from v4.16: how a two-ply marker treats a piece with cut quantity 1).

* **Answer to the open item, and more** (MARKER_FORMAT_SPEC.md section 24). Made with my own processes on scratch copies: ONE model (`ZZQ-BLOUSE`, a copy of LADIES-BLOUSE) whose FLIPS columns I edited three times (`--`, X, Y, X,Y counts per piece), one order of two size-10 garments,
  tables of every spread; AutoMark on two markers, AccuNest (Queue Submit, own process) on two more. Slot words: **0x0080 = flip X, 0x0100 = flip Y, both = X,Y** (0x0100 had never occurred; the decoder used to warn about it). A single-ply marker lists exactly the flips the
  model states (90 of 90 multisets). A two-ply marker: each as-is instance absorbs ONE flipped instance (Y first, then X,Y, then X) - a piece cut once keeps its slot per garment, only mirrored pairs halve (15 configurations). No field states "pieces per garment": the slots are the demand.
* **Geometry of the flips.** X and Y are mirror images, X,Y a half turn (AutoMark, sleeve, 14 of 14 slots); a Y / X,Y instance is retrieved turned 180 and this composes with the bundle's 0x2000 direction: on no-rotation rows AccuNest keeps `turn = 180 x (0x2000 XOR flip in {Y, X,Y})` on 32 of 32
  slots (ZZLL-1WAY) and 8 of 8 front slots (ZZLL-1, alternating). Neither engine keeps each slot's chirality on an `MW` row (front piece: AutoMark 3 of 8, AccuNest 9 of 16 kept; the sleeve under `MS`: 14 of 14 and 6 of 6): the flips are a preset, not a constraint.
* **Code.** `accumark_marker.py`: `FLIP_Y_BIT`, `FLIP_LABELS`; slots gain `flip`, `preset_mirrored`, `preset_turn_deg`; `KNOWN_ORIENT_BITS` includes 0x0100; the inventory's `preset` gains `flip`, `mirrored`, `turn_deg` (`mirror` = 0x0080 as before) and `other` excludes 0x0100; the text report names the flips.
  `nest_spec.py`: `demand[].mirrored` = X or Y (X,Y is no longer mirrored), `flip_by_slot`, `preset_turn_deg_by_slot`, `allowed_deg_by_slot` from the turn, `fabric.plies_note`.
* **Checks.** `selftest` (new section): 9 unmade markers x 2 bundles x 5 pieces (90 flip multisets against the model / the two-ply rule), the 0x2000 bundle direction per table, the nest spec (mirrored, flip, turn per slot), AutoMark chirality (14 slots), AccuNest direction (40 slots), a toggled flip bit and an unknown bit (0x0400)
  in a byte patch; mutation-tested (merge order, half turn). `dataset_test`, robustness unchanged (see the STATUS line).
* **Live-run notes.** Model Editor FLIPS cells: double-click, Ctrl+A, type, Enter (without Ctrl+A the digit is appended: `1` -> `31`); Order Editor: the Model Name chooser on the model tab (dots button, real (480,203)) swaps the model; Process with a marker name equal to an existing ORDER asks "Overwrite" (my own copy: Yes);
  AutoMark Editor fields: Ctrl+A is "Add to Job List" and triple-click / Shift+Home do not select - click, End, 30 x Backspace, type; a tubular table (`ZZLL-X2`) ended "Process completed with warnings" (marker still made). Scratch objects made: model `ZZQ-BLOUSE`, orders `ZZQ-S/F/B/T/S2/F2/F3/W/A`, markers `ZZQ-*`, Made `ZZQ-SA/FA/W/A`
  (the original LADIES-BLOUSE model is byte-identical to its backup). My Model / Order / AutoMark / Queue Submit processes were closed; the user's windows were not touched.
* **Open.** Three or more flips of one kind as a two-ply merge (3 x X); the 0x2000 x Y composition on a rotating row; why AccuNest swaps chirality; the other section-1 counters, trailer state words, section 5, 45-degree placement.

## v4.16 (2026-09-24) - the spread is in the marker; the piece flag @+14 is the major-piece option

`__version__` stays `'3.0'`. New fixtures `spread/` (four markers + `GROUND_TRUTH.json`). Request: "go to the next step" (open items: what the marker keeps of the lay table; the piece-row flag @+14).

* **Spread** (MARKER_FORMAT_SPEC.md section 23). Section 1's u16 at file offset 520 = the Lay Limits table's spread: 0 single ply, 1 face to face, 2 book fold, 3 tubular. Found by correlation (56 of 56 corpus markers that bundle their table) and proved live: my own Order Editor,
  one order (`CLAUDE-D4` copy), only the Lay Limits table and the marker name changed - `L` / `ZZLL-F2F-R5` / `ZZLL-BOOKFOLD` / `ZZLL-X2` gave 0 / 1 / 2 / 3. A single-ply marker lays a `CUT X02` pair as two slots (plain + mirror, 6 for 3 sizes), every two-ply
  spread as ONE slot (3): the header counters, size rows and order copy stay. Corrects v4.14's "the marker does not carry the table's spread".
* **The piece-row flag @+14 = the M (major piece) option of the row** (= the slot bit `0x0040`): 341 of 341 piece rows on 78 markers. Closes the open item "what sets it" (not the engine, not an order or model option - two different tables).
* **Bundling inferred.** Not stored, but the presets are: `lay_limits.bundling_candidates` (the modes the stored directions do not contradict) and, when one is left, `bundling` with `bundling_basis: inferred`. The real 2591A -> All Bundle, Same Direction (the missing
  `ALL GMT WAY`); the F2F and book-fold fixtures infer their own table's mode, the tubular one leaves {alternate, same size} which contains its own.
* **Code.** `mk['spread']`, `piece['major']`; check rows (spread is 0-3, flag == the row's M); a `marker_warnings` entry for another value; coverage marks the word; nest spec: `lay_limits.spread` from the marker when no table is bundled (a difference against a
  bundled table is reported like a changed row), `fabric.spread` and `fabric.plies` (1 single ply, 2 for the other three).
* **Checks.** `selftest` (new section): the four markers (word, table, slots, plies, Bundling candidates), the corpus (spread 56 of 56, major 306 of 306), byte patches (a spread word of 7, a major flag against its row's M), the real 2591A / 1825D Bundling; `dataset_test` 36/36; robustness 730/730.
* **Scratch state:** my `ZZSP-*` orders / markers removed; my Order Editor closed; the user's windows untouched.
* **Open.** How a two-ply marker treats a piece with a cut quantity of 1 (only the `CUT X02` pair was measured); whether the tubular spread lays anything differently from face to face (the marker shows no other difference); what the other section-1 counters are.

## v4.15 (2026-09-24) - notch numbers: a piece keeps the number, a marker only min(number, 5)

`__version__` stays `'3.0'`. New fixtures `notchnum/` (a PDS-made piece and its marker + `GROUND_TRUTH.json`). Request: "proceed to the next step" (open item: notch numbers above 15).

* **The finding** (MARKER_FORMAT_SPEC.md section 18). A notch's NUMBER (row of the Notch Parameter Table, 1-99) lives on the piece only - the last byte of the 45-byte tag-0x07 child of its point in the line table. The perimeter point and a
  marker's stream keep the CODE `min(number, 5)`. Live: in PDS (own process; scratch `P-NOTCH` temporarily the 25-notch table so the Type list offers numbers; the Type box set with the keyboard) notches numbered 3, 7, 12, 16, 25, 30, 30 were added to
  a piece whose two imported notches are number 6; Order Editor (own process, a copy of an order) made the marker: the piece stores codes 3 + 8 x 5, and so does the marker's stream at all three sizes. The corpus agrees: 134 notches of the bundled pieces (numbers 5, 6) and the real styles of the scratch area (numbers 1, 2, 4). **Corrects v4.10's "the marker's notch code is the notch number"** - true for 1-4; a code 5 is "5 or higher" (NEED-P-NOTCH: 5 = slit, 6-7 = V, 8-15 = slit).
* **Code.** `accumark_pds.notch_numbers(block)` (+ `summarize()['notch_numbers']`); `accumark_marker.read_storage_piece` (a `.GT_piece` file as the export-shaped object; shares `_wrap_storage` with `read_storage_marker`); nest spec: `notch_table.by_code`
  (candidate numbers per code, `same_geometry`), `notches[].numbers` / `number`, a warning when a used code stands for notches of different shape, `code_note`; `notches_mirrored` carries them.
* **Checks.** `selftest` (new section): the fixture piece and marker, the corpus rule, a byte patch (a number changed to 9 next to code 3 is noticed), the spec's candidates for the PDS marker and for the real 2591A (`NEED-P-NOTCH`, code 5 = numbers 5-15, slit and V).
* **Not understood (recorded).** Editing the notch bytes of a piece FILE by hand - the perimeter point, its line-table twin, the child TLV; numbers 16 / 25, then 15 / 14 - made the order's Process fail with "Error processing, missing components";
  rewriting the identical bytes and the PDS route work. Test pieces must come from PDS.
* **Scratch state restored** (the original `P-NOTCH`, the pristine `CLAUDE-CURVE` piece; my `ZZNN-*` order / model / marker removed); the user's windows were not touched.
* **Open.** What a notch on a corner (turn) point stores for a number above 5; whether the cutter draws different shapes for numbers that read the same code (a marker plot would show it).

## v4.14 (2026-09-24) - the marker carries its own tables: notch table, lay-limits rows, each piece's row

`__version__` stays `'3.0'`. Request: "you can pick and continue" (the open byte-map items; `ALL GMT WAY` left out).

* **Section 3 is the marker's copy of its Notch Parameter Table, section 4 its Lay Limits rows** (MARKER_FORMAT_SPEC.md section 22). Section 3 = the table payload byte for byte (144 / 160 / 304 / 464 bytes; 40 markers equal their bundled table, 6 more
  without the optional zero dword); 16 scratch-set markers (`ZZ-AM-*`, `ZZN-*` ...) hold only its first 60 bytes (five older-layout triplets, no types). Section 4 = 12 bytes per row `u16 flip code, f64 tilt, b2, b3` in table order, no names: 76 of 76 rows of
  the 56 markers that bundle their table agree. The real markers' copies equal the real tables (1825D / 5683D / 2591A: `NEED-P-NOTCH`, 15 numbers). The earlier readings of sections 3 and 4 ("repeating `00 00 b0 07` groups", "a 12-byte
  label-config header") are retracted.
* **The piece row's words:** w1 = the piece's Lay Limits row (0 = DEFAULT), w3 = its buffer rule, w4 = its flip code, w5-w6 = its tilt (i32 x 10000): 287 of 287 piece rows of 56 markers. So the marker states, per piece, the rotation rule it was made with.
* **Code.** `parse_marker` -> `mk['snapshots']` (`notch`, `lay_limits` {rows, piece_rows, ok}, `warnings`) and per piece `lay_row`, `buffer_rule`, `flip_code`, `tilt_raw`; `accumark_notch.parse_notch_snapshot`,
  `accumark_laylimits.parse_snapshot_rows`; `mk['header_counts']` (section 1's four counters at 480 / 482 / 490 / 492 = records, slots, models, size rows, 73 of 73); two `check_marker` rows plus the counters row; `marker_warnings` names a section 3 / 4 that
  does not read or a piece row that disagrees with its row; `marker_coverage` counts sections 3, 4 and the piece words as identified (`PARSED_SECTIONS` now 3, 4, 6, 11-15, 21, 30): unknown bytes per marker 1,111-1,753 -> 1,031-1,280 (1.06%).
* **The nest spec reads a marker-only ZIP's own rules.** `lay_limits.source` / `notch_table.source` = `marker snapshot` (v4.16: with the spread from section 1 + 216 and the Bundling inferred from the presets) when the table is not bundled or supplied (rows are named by the category of the pieces that point at them; spread and bundling stay
  `null` - not in the marker): the real 1825D / 5683D / 418T / 2591A specs no longer say `assumed` - locked one-way, every piece fixed in its preset direction; 2591A's notch numbers 1 and 5 are read from its own copy; the older 60-byte copy gives notches
  1-5 (no types) and a warning. With a table as well, the two are compared (`lay_limits.snapshot`, `notch_table.snapshot`, a warning): the real `NEED- TWO WAY` reads `MWS` now, 1825D / 5683D hold `WS` (the table was edited after them?). The five old expectations
  of `selftest` that a marker-only ZIP reads nothing were rewritten to this.
* **`ALL GMT WAY`** (2591A, not in any file): its DEFAULT row is `MWS`, flip 1, no tilt - from the marker. The Bundling still rests on the presets. The table itself stays welcome.
* **Checks.** `selftest` (new section): 67 markers, the notch copy vs the bundled table (40 equal, 16 older), the 76 rows, the 287 piece rows, byte patches (a wrong flip code or row index on a piece row, a changed option byte in section 4, a broken notch count each show; sections 3 and 4
  leave no unknown byte), the real markers' rows and notch tables through the nest spec; `dataset_test` 36/36; robustness 730/730.
* **Open.** Whether the marker's one tilt is the cw or the ccw limit (equal on every corpus row), and its unit for a table in degrees; section 1's other counters (no sum of records, slots, streams or areas matches); the Annotation copy (section 5); the trailer's
  state words and stamps.

## v4.13 (2026-09-24) - laid-marker rotations: how a placed slot says which way the piece lies

`__version__` stays `'3.0'`. New fixtures `rotation/` (five made markers + three plots + `GROUND_TRUTH.json`). Request: "laid-marker rotations (the 90 degree collar case)".

* **The finding** (MARKER_FORMAT_SPEC.md section 20). The placed orientation of a slot is the LOW THREE BITS of its orientation word: 0 / 4 / 3 / 7 = 0 / 180 / 180 + mirror / mirror, and 2 / 6 / 1 / 5 = the quarter turns 90 / 270 / 90 + mirror /
  270 + mirror (turn counter-clockwise, mirror top-to-bottom first). The `0x2000` / `0x0080` bits the decoder read until now are the PRE-SET of the unlaid marker and stay in the word when a nester lays the piece another way -
  the reason the old rule agreed with 2303 (where both say the same) and put 1,707 pairs of placed pieces on top of each other over the 31 laid markers of the corpus (15 with the new rule; see below).
* **The tilt.** A signed float32 at slot byte +38 is a further tilt in radians, counter-clockwise, applied last: AccuNest's CW / CCW Tilt Limit overrides (10 degrees) gave 10.000 degrees on the two collars that used them; the
  corpus marker `ZZN-B4` holds +-3.0 and +1.5 on 19 slots (its home boxes fix the sign and the order: tilt after the mirror and the turn; no plot exists for it).
* **The collar.** One piece needs a quarter turn (`frame`, +90) between its stream outline and the frame the codes refer to: the LADIES-BLOUSE collar (stream 3.48 x 16.47 in, placed 16.47 x 3.48 at every code, 28 markers). The reader decides it from the
  marker's own home boxes, per piece (`frame_offsets`). This closes the v4.11 observation ("the laid TEST-2 collar is 90 degrees off its stored box") and the `--as-job` flag on it. Why the collar differs is open.
* **The home box** of a placed slot = the placed shape's bounding box + the piece's block buffer TURNED with it: the sleeve's Left 2.0 / Right 0.5 cm land on x at 0 / 180 degrees and on y at 90 / 270 (the independent parity check of the
  quarter turns); a collar tilted 10 degrees adds 2 x 0.1968 x (cos 10 + sin 10) = 0.456 in.
* **Proof.** Four AccuNest runs of a copy of `ZZC-M1` (Nest Markers overrides Rotation 90; Rotation 45; Rotation 45 + tilt limits 10; the earlier W-row run), each plotted: 72 placed slots, every decoded outline on its plotted loop (0.16 in = the plot's
  curve sag, cuffs 0.002), all eight codes measured alone on 32 slots. The same slots with +180 added miss the plot on 56, with the mirror inverted on 48, under the pre-4.13 rule on 47, without the collar frame on 16.
  `orientation_check` (appended to `place_marker`'s `checks`): every placed shape fills its stored home box - 40 laid markers, worst 0.018 in - and fails when one slot is turned 90 degrees.
* **Code.** `parse_slots`: `orient_L`, `placed_rot`, `placed_flip`, `tilt_deg` (None + a `marker_warnings` entry when the float is not an angle); `ORIENT_L`; `transform(outline, slot, frame)` (quarter turns, mirror, any tilt; re-centres the
  turned box on the slot's centre - identical to the old rule for the four old orientations); `frame_offsets`; `orientation_check`; `place_marker` now places a slot by the marker's own stream outline when its piece object is a stub
  (a marker-only ZIP places its slots too; `bbox_check` reads the placed outline's own box); `unplaced_inventory` / the nest spec of a laid marker read as a job (`--as-job`) give the piece-frame stored box `home_box_piece_in`
  (`stored_box` / `padding` null for a tilted slot): TEST-2's four collars are no longer flagged (20 of 20 shapes equal their stored box).
* **Marker files from a storage area.** `read_storage_marker(path)` / `place_marker('<area>\\mark\\Made\\NAME.GT_mark')`: the payload of a `.GT_mark` file equals an export object's, the envelope is rebuilt around it (section 21); `ZZC-M1` reads as its
  export does. A nest that ends "needs approval" (AccuNest with a Marker Border Angle of 30 degrees) leaves a partial marker in `NeedsApproval\` (`rotation/ZZROT-B.GT_mark`: 17 placed, 1 not, no tilts written).
* **Checks.** `selftest` (new section): the plot fit of 72 slots and four mutations, the tilt floats, the 19 tilted `ZZN-B4` slots (home boxes; wrong sign misses 10), the buffer parity on 72 slots, TEST-2 as a job, the corpus overlaps (1,707 -> 15,
  the 15 = three copies of an experiment with a hand-placed slot 6, and slots that touch within the buffer), the runtime check and its mutation, storage files, a NaN tilt word; `dataset_test` 36/36; robustness 730/730.
* **Answered on the way.** The 7.2% by which the BACK piece's placed slot exceeds its record (ZZC-M3, ZZN-F1, every ZZC-M1 nest) is its BLOCK rule (rule 2 = a visible 1 cm added to the piece; the other rules are buffers and leave the area equal).
* **Open.** How a 45-degree placement is stored (AccuNest's Rotation-45 override placed nothing off the 90-degree grid; Easy Marking's `Rotate 45 CW` was not driven to a stored marker - inferred: a tilt of +-45 degrees on top of the code); why the
  collar needs its quarter turn (+90 vs +270 cannot be told on it); the exact area a block adds; what +0.0 vs -0.0 in the tilt float means (a nester writes -0.0).

## v4.12 (2026-09-24) - the Block / Buffer table: what a buffer rule is

`__version__` stays `'3.0'`. New module `accumark_blockbuffer.py`; fixtures `blockbuffer/` (three editor-built tables + `GROUND_TRUTH.json`). Request: "proceed" (the block buffer table).

* **Ground truth.** The Block Buffer editor (`BlockBuff.exe`, own process) showed `ZZBB-USER` (rules 1-8: unequal sides in rule 4, a Block rule, static + dynamic amounts); a rule with nine distinct amounts (rule 9, Block),
  percentages (rule 10) and a two-line comment were added and saved as `ZZBB-X1` / `-X2`; the bytes were read against the numbers typed. Only Left / Top / Right / Bottom accept input - the Segment cells are greyed out.
* **Format** (MARKER_FORMAT_SPEC.md section 19): `u16 line1, u16 line2, u16 n` + comment (the AccuMark 9 `3MM`: 40 comment characters + `u16 n`), then `n` 70-byte entries `(u16 number, u16 type 0 buffer / 1 block, 11 x (i32 amount x 10000, u16 unit))`
  in the order static Left, Top, Right, Bottom, Segment, dynamic Left, Top, Right, Bottom, Segment (+ one slot that is always 0); a length is inches, a percentage of the repeat is unit 2 (50% = 500000); an optional zero dword.
* **The marker's own buffer entries.** A piece's section-6 entry is the STATIC amounts of the rule its Lay Limits row names, four doubles in inches ordered **Left, Right, Top, Bottom** - the sleeve's rule 4 (Left 2.00, Right 0.50 cm)
  is `[0.7874, 0.1968, 0, 0]`. 81 entries on 5 markers (ZZC-M1, ZZC-M3, the 2303 CP 150 set, the real 418T and 1825D) equal the table rule; the wrong table is contradicted. **Top vs Bottom settled by a live run:** lay limits
  `ZZLL-BB9` (FRONT -> rule 9), a copy of ZZC-M1's order (`ZZBB-M9`: lay limits ZZLL-BB9, block buffer `ZZBB-X1` whose rule 9 is Left .11 / Top .22 / Right .33 / Bottom .44 cm, Mode Layrule Search), Process ->
  the FRONT piece's entry in the marker file is `[0.0433, 0.1299, 0.0866, 0.1732]` = **Left, Right, Top, Bottom** (`blockbuffer/GROUND_TRUTH.json`, `selftest`). The old "side order [?]" is closed.
* **Real values.** `3MM` (the user's, 418T / 1825D / ...): rule 1 = Buffer 0.15 cm on every side (0.0591 in, a 3 mm gap between pieces); `3MM-N` the same plus an empty rule 2.
* **Nest spec.** `block_buffer` (bundled / supplied / named only) with `rules`, `rules_used`, `marker_entries`, a per-shape `buffer`, two checks, `--block-buffer`.
* **Open.** The always-zero eleventh slot; the Segment amounts (the editor does not let them be entered here); what a percentage of the repeat means for a marker without plaid.

## v4.11 (2026-09-24) - the reference nester: the spec is enough to nest

`__version__` stays `'3.0'`. New `reference_nester.py` (numpy + Pillow + shapely, reads only the spec JSON). Request: "go to the next step" (the reference consumer proposed earlier).

* **The nester.** Rasterised pieces, largest first, FFT correlation for every position that touches nothing laid, smallest right edge wins, every rotation from `demand[].allowed_deg_by_slot`; `--best` tries 8 order /
  score combinations. Its lay is validated independently with shapely (inside the fabric, no overlap, rotations allowed, all instances laid): `VALID` / `INVALID`.
* **Results.** Every job is valid: 2303 (97 bra cups) 371.5 cm / 72.7% vs AccuMark's own 377.7 cm / 71.5%; AD1234 56.8 cm / 45.9% vs 47.0 cm / 55.7%; `ZZC-M1` 353.7 cm / 55.1% (best of 8: 332.4 cm / 58.7%) vs my
  AccuNest Draft run's 249.8 cm / 79.7% (a plain bottom-left heuristic is far from AccuNest on large irregular pieces); the real 1825D, 5683D, 418T and 2591A jobs 62.8-69.9%, all valid, with the real `MWS` tables
  fixing each piece in its preset direction.
* **The reverse proof.** AccuMark's own lay of the real 2303 job, rebuilt from the SPEC's shapes with the placed marker's positions and orientation flags: 97 valid polygons, no overlap beyond 0.0003 in2, inside the
  53.94 in fabric, area / (W x L) = 71.51% = the marker's utilisation. It confirms outlines, the mirror convention and areas end to end on a real production lay.
* **`--as-job` / `place_marker(as_unlaid=True)`.** A laid marker read as the whole job (positions ignored, `check_marker` taken before the change): `source.job_of_laid_marker`.
* **Observation, not chased.** In the laid `LADIES-BLOUSE TEST-2` the COLLAR stream outline is 90 degrees off its stored home box (8.8 x 41.8 vs 41.8 x 8.8 cm, four sizes; the other pieces agree), so a laid marker may
  carry a piece as placed; the unlaid markers do not show it (that check flags it in the `--as-job` spec).

## v4.10 (2026-09-24) - the Notch Parameter Table: what a notch number is

`__version__` stays `'3.0'`. New module `accumark_notch.py`; fixtures `notch/` (two editor-built tables + `GROUND_TRUTH.json`). Request: "decode the notch tables".

* **Ground truth.** The Notch editor (`Notch.exe`, own process) opened scratch copies of the real `NEED-P-NOTCH` (notches 1-5 and 8-15 = Slit 0.50 cm; 6-7 = V, perimeter 0.50, depth -0.25), `V-NOTCH-ALL CUSTOMERS`
  (25 x V 0.30 / -0.20) and the default `P-NOTCH` (notch 1 = Slit 0.40); a copy of the V table was then edited to one row of every type with distinct numbers and saved under a new name (`ZZNT-X1`, `-X2`), and
  the bytes were read against the numbers typed.
* **Format** (MARKER_FORMAT_SPEC.md section 18): five legacy (perimeter, inside, depth) triplets, `u32 N` at +60, then `N` 16-byte records `(type, perimeter, inside, depth)` from +64 - record k is notch number k;
  lengths x 10000 in inches; types 0 None, 1 Slit, 2 T, 3 V, 4 Castle, 5 Left Check, 6 Right Check, 7 U, 8 No Lift Slit; an optional zero dword at the end. Strict: any other length, a triplet that differs from
  its record or an unknown type is refused.
* **Notch number = the marker's notch code (for 1-4 only: corrected in v4.15 - the code is min(number, 5)).** A piece's Notch Type N is looked up in this table (FORMAT_SPEC: depth is not stored on the piece), and the code in a marker's stream is that number. Confirmed on the
  geometry: the 30 notch spikes of the real AccuNest plot of `ZZC-M1` are all exactly 0.40 cm = notch 1 of the default `P-NOTCH`; the real 1825D / 5683D notches (number 1) are 0.50 cm slits (`NEED-P-NOTCH`).
* **Nest spec.** `notch_table` (bundled / supplied / named only) with `entries` per notch number (kind, perimeter width, inside width, depth, direction), `numbers_used`, two checks, `--notch-table`.
* **Not done / open.** Notch numbers above 15 (the marker stream keeps the number in a nibble), `No Lift Slit` depth semantics (the editor stored depth 0), how the cutter draws a Castle / U in a plot.

## v4.9 (2026-09-24) - the user's real support files: `NEED- TWO WAY`, `G-LAYLIMITS`, `L` read and checked against the real markers

`__version__` stays `'3.0'`. Source: `all support files.zip` (AccuMark Explorer "OldFiles", AccuMark 9 data): lay limits `L`, `G-LAYLIMITS` (418T), `NEED- TWO WAY` (1825D, 5683D), `ONE GMT ONW WAY`;
block buffers `3MM`, `3MM-N`; notch tables `P-NOTCH`, `NEED-P-NOTCH`; annotations `A`, `NEED-MARKER`, `M-MARKER`; the rule table `4155B`; cutter / plotter / environment parameter tables.
`ALL GMT WAY` (2591A) is not in it. Only redacted table bytes are kept in the repo (`laylimits/REAL_SUPPORT_TABLES.json`: no envelope, no user names, the author comment of `G-LAYLIMITS` blanked).

* **Two more table layouts.** `NEED- TWO WAY` (39 bytes) and `ONE GMT ONW WAY` (55) use the V17 header and row layout but stop early - no trailer, or only the weft-skew array. `parse_lay_limits` reads them (`trailer`
  `'none'` / `'skew'`; any other trailer is refused) and the Lay Limits Editor shows scratch copies of the exact bytes as decoded: Single Ply, Alternate Bundle / Alternate Direction, `DEFAULT` = `MWS`, flip 1, rule 1.
  The real `L` is byte for byte the corpus `L`; `G-LAYLIMITS` was checked the same way (older layout, `MWS`).
* **Against the real markers.** Supplied to the marker that names it, `NEED- TWO WAY` agrees with the stored bundle directions of the real 1825D (2 markers) and 5683D markers, `G-LAYLIMITS` with the real 418T marker: 31
  neighbouring bundle pairs, none against. `MWS` (locked) fixes every instance in its preset direction, so those specs are `verified`.
* **A prediction for the missing table.** Every bundle of the real 2591A marker (7 different sizes) is preset to 0: only "All Bundle, Same Direction" fits (the other two Bundling modes are contradicted on all 6 pairs).
  So `ALL GMT WAY` should be All Bundle, Same Direction - to be confirmed when its file arrives. (The names fit: `NEED- TWO WAY` = alternating directions, `ALL GMT WAY` = every garment the same way.)
* **Not useful / not done.** The block buffers again have equal sides (`3MM` 591 and `3MM-N` 590 = 0.059 in), so the side order stays open; the parameter tables (cutter, plotters, layrule search, environment) are
  machine setup, nothing for a nesting job; `parse_rul` reads `.RUL` text, not the binary `4155B` rule-table object (its pieces are not here). The two notch tables define notch geometry (depths 0.1574 in and 0.1968 in
  appear) - decoding them would put notch sizes in the spec; not started.

## v4.8 (2026-09-24) - the Lay Limits table: read from the order / marker, and what a row lets a nester do

`__version__` stays `'3.0'`. New module `accumark_laylimits.py`; new fixtures `laylimits/` (13 tables + `GROUND_TRUTH.json`). Request: "read the lay limits from the order".

**Where the table is named.** The marker's section 2 ends with ten name strings (lay limits, annotation, block buffer, notch table, customer, order name, reference, extra), eleven u16
lengths at section start -4 .. +18 and the strings from section start + 231 - 69 of 69 markers, every vintage, including the user's real `NEED- TWO WAY` / `ALL GMT WAY` / `G-LAYLIMITS`
(`parse_marker(...)['tables']`). The order stores the same slots (V17: u16 lengths at +10 .. +88 and strings from +176; older vintage: ten 20-character slots) and agrees with its marker
on the four table names in 58 of 58 order-marker pairs (`parse_order_tables`, also `parse_order(...)['tables']`). So even a marker-only ZIP says which table it was made with.

**The table itself (object type 6).** Decoded from its bytes with the Lay Limits Editor as ground truth (my own process, scratch area only): `ZZLL-1` read as shown, then `ZZLL-X1` (weft skew,
group, degree units, rule 17, two different tilts), `ZZLL-X2` (every option letter one row at a time, Tubular, Same Size), `ZZLL-X3` (Per Model), each saved under a NEW name and byte-diffed.
Found: spread 0-3 (single ply / face to face / book fold / tubular - the older guess "1 = single ply" was the bundling byte), bundling 0-2 (all same / alternate / same size), Per Model at
payload byte 8, the comment as two 20-character lines, the row header (options are bits: `M W S 9 4 F O N` in b3, `U X Z P` in b2), flip code 1-12, u16 buffer rule, tilt limits x 10000 in inches (or
degrees), weft skew x 10000 in a per-row array after the rows, and the Group column as the text property `Category group`. The older vintage (the user's real `L`, `SINGLE-PLY`) is read for single-row
tables. Every field equals what the editor showed (`selftest`: 15 tables / 37 rows); a mutated table is refused, never guessed.

**Confirmed by the markers themselves.** The table's Bundling predicts the 180-degree pattern stored on the marker's bundles: on 29 markers with a bundled table every neighbouring bundle pair
follows it (alternate bundles differ; `L` = same size same direction is equal within a size and alternates between sizes; all-same is equal) and the wrong Bundling on `CLAUDE-D2-E7B` is
contradicted. The stored presets carry no trace of a flip code (`ZZC-M1` SLEEVE, flip code 7).

**In the nest spec.** `lay_limits` (name, `source`: `bundled` / `supplied` / `named only`, spread, bundling, rows), `rotation` (the DEFAULT row: `allowed_deg`, `flip_x_axis_allowed`, `locked`, tilt, skew,
buffer rule, flags), a per-shape `rotation` from the shape's category row, `demand[].preset_rot180_by_slot`, three new checks, and `--lay-limits NAME.GT_lay|other.zip` for a marker-only ZIP. Without the
table the spec still says `[0, 180]`, `assumed`, and names the missing table in a warning. Semantics (Gerber help): blank = 180 + flip, `W` = one way (no rotation), `S` = no flip, `W`+`S` = locked,
`9` / `4` add 90 / 45 degrees - the one-way behaviour was also measured live earlier (`MW` markers: no reversed piece).

**A real nest settles the `W` question.** `ZZC-M1` (made with `ZZLL-1`: FRONT = `MW`, alternating bundles) was copied in scratch (`amcopy`), nested in AccuNest through my own Queue Submit (Draft, no
Overrides, Made after 70 s) and plotted to DXF (`laylimits/EXPERIMENT_W_ALTERNATE.DXF`, write-up beside it). Each plotted outline was matched to the marker's own stream outline in four orientations: the
four FRONT pieces are two forward, two reversed - exactly the marker's presets - and the sleeves show the four preset x mirror combinations once each. So a one-way piece is fixed in the direction its bundle is
retrieved in; `demand[].allowed_deg_by_slot` = `(180 x preset + allowed_deg) mod 360` encodes it (`selftest` re-derives it from the DXF). Option `4` is read as 45 degree steps (90s included).

**Still open** (MARKER_FORMAT_SPEC.md section 14): the meaning of a row's b2 & 0x07 and of the Group column; older-vintage multi-row tables; whether a row that allows 180 lets the engine turn a piece against
its preset (no piece did in that small nest).

## v4.7 (2026-09-21) - the controlled dataset: `@88` is the record's own count, `0x0040` is a copy of a piece-row flag

Same labelling rule: `__version__` stays `'3.0'`. Design: `MARKER_DATASET_DESIGN.md`.
Fixture: `markers-live/CLAUDE-UNP-D2-TWIN/CLAUDE-D2-M0.zip`.

**How an as-generated marker is made on demand (the harness).** Explorer > select an
Order > right-click > Save As (a copy, e.g. `CLAUDE-D2-GEN`) > Easy Order on the copy >
edit the **Marker Name** cell of Step 4 (the marker takes the name from that cell, NOT
from the order object - Explorer's *Generate Marker* on a copy targets the ORIGINAL
order's marker name and stops at "Confirm Marker Replace") > *Process* > Save changes
> Success. No Easy Marking involved, so the marker is genuinely as generated
(`CLAUDE-D2-M0`: word 40 = 0, 24,496 B). One order object per experiment, so every
byte that differs between two markers is a setting I changed.

**Correction of my own false alarm.** Earlier this session I wrote that *Generate
Marker* had overwritten the scratch marker `AD1234 TEST 134` (laid 25,464 B ->
9,762 B). It had not: the dialog I cancelled was *Confirm Marker Replace* hidden behind
the progress window, and Explorer's Size column showed a stale figure for a while. A
re-export of the marker differs from the September export only in the 57 envelope-stamp
bytes; the laid original is intact. Nothing was replaced.

**Reproducibility.** The same order processed again 32 minutes later under another marker name
(`CLAUDE-D2-M5`, reached through *Process w/ AutoMark*, which only writes the same as-generated
marker and opens the AutoMark Editor as a job scaffold - the job was not submitted) differs from
`CLAUDE-D2-M0` in **18 bytes**: four name digits and stamp bytes. So the harness is deterministic
and any byte that differs between two runs is a setting that was changed (`selftest` row).

**Two more runs of the harness (E7).**
- `CLAUDE-D2-E7O`: I added `CLAUDE-GRADE-MODEL` to the order and typed quantities for it. The order
  saved and the marker processed as `ID1005 - TOP` alone - **a model none of whose pieces carries a
  fabric type of a used fabric row is dropped from the ORDER and the MARKER** (order copy included),
  and the marker decodes exactly like `CLAUDE-D2-M0`. So an order's lines are not the marker's content:
  read the order copy of the marker, not the Order object (`selftest` row).
- `CLAUDE-D2-E7B`: `LADIES-BLOUSE` + `ZZ-PLM-BLOUSE` (both fabric type M), 3 cuts, freshly generated: header
  **@422 / @454 are the LAST model's sums** (3,483.80 sq in / 738.85 in against 7,706.33 / 1,795.84 over
  all 29 slots) - so the `last_model` mode on the 2303 markers is AccuMark's own behaviour at generation
  time, not an artefact of a laid marker. The piece list repeats each piece once per model (10 rows for 5
  pieces), the order copy holds both models, all check rows pass, no warning. (Four of the five blouse
  piece objects in that export are stubs, so `--inventory` says `GEOMETRY: outlines for SOME slots` and
  `NEEDS A LOOK` for them - the export's limit, not a decode fault.) `flag14` is **0** here, on the same
  LADIES-BLOUSE pieces whose `LADIES-BLOUSE TEST-2` / `ZZN-F1` markers carry 1: the flag is NOT a property
  of the model or its pieces, it changes with the marker's origin (`selftest` row).

**The twin.** `AD1234 TEST 134` (laid, 13 pieces, from September) and `CLAUDE-D2-M0`
(as generated, from a Save-As copy of that order with only the marker name changed) share
pieces, sizes, quantities and width, so every difference is what laying does:
- the 13 records are byte-identical (text, area, perimeter, head words, stream length);
- slot bodies differ ONLY in centre (+0..+20: 0,0 vs placed), orientation (+32/+33),
  two 1-ulp area bytes (+41/+42) and `@88` (**213 on every RUFFLE slot as generated, 0
  laid**); record index, piece index, bundle, home box and area are identical;
- section 1 loses its length / utilisation / placed-area doubles when unlaid, word 40
  is 0 vs 2, the name (repeated in sections 2 and 30) changes length;
- the embedded type-10 scratch object is **960 B larger once laid** (a ~1 KB block of
  small offsets, `f0 04 00 00 f8 04 00 00 fc 04 00 00 ff ff ff ff ...`, at its offset
  310..1288 that the unlaid object lacks) - still opaque, but the growth is now located;
- the unlaid marker decodes cleanly with geometry for every slot (`GEOMETRY: outlines
  for every slot`): 13 pieces, 543.25 sq in, 10.3 in minimum length at 134 cm.

**`@88` is not independent - it is the record's own count.** Slot `@88` (as generated)
`= record head u16 @+10 (prefix[1], a per-size count) + C`, with **C one constant per
piece** - the same for every size of the piece and for every marker that carries it:
107 (marker, piece) groups over 43 markers and 31 pieces, **0 exceptions**. RUFFLE 209 +
4 = 213, the rectangle 5 + 4 = 9, LADIES-BLOUSE-BK 105 + 4 = 109 (and 103 + 4 at size 10:
`@88` moves with the size, so the earlier "constant per piece+size" was really "per
record"). C is 4 on a piece with at most a grain line, 28-32 with grain + mirror lines,
216-266 with ten internal lines, 620+ with eighteen: the internal geometry's share of
the entry count. Still open [?]: exactly which entries C counts. New check row
`slot @88 = record head count + one constant per piece (as generated)`, new
`marker_warnings` entry, `mk['sig88_model']`, mutation-tested (one slot's `@88` +1 breaks
the row and raises the warning).

**The marker-level `0x0040` bit is a copy of the piece row's flag u16 @+14
(section 10).** Slot bit `== (flag == 1)` on **9,122 of 9,122 slots over 111 markers**,
and no marker mixes flag values (232 piece rows are 0, 268 are 1, each marker uniform).
That is why it looked marker-level, and why it never tracked the pair bit. Piece rows
now carry `flag14`; new check row `slot orientation bit 0x0040 == its piece row flag
@+14 (section 10)`, mutation-tested. Still open [?]: WHAT (order / model option) sets
the flag. It is not a model-piece property (no model flag byte separates it over 450
marker-piece / model-piece pairs) and not the block buffer (both values occur with and without
one); by name it looks like the ENGINE that wrote the marker (0 on Marker Wizard / Easy Order /
AccuPlan / the imported 1825D, 5683D and 2303-BD 137 markers; 1 on the ZZ-AM, ZZN, ZZC, CP 150,
418T, 2591A and LADIES-BLOUSE TEST-2 markers) - circumstantial until one order is run through
each engine (`MARKER_DATASET_DESIGN.md`, F5).

**Not run, and why.** F1-F3 (width, quantities, single-size markers) predict only header width / section 15 / size rows, all already decoded; F4 (block buffer) needs an unequal buffer object (the only one in the scratch area, ZZBB-1, is 1 cm on all four sides) and a place to assign it - the Step 4 fabric row shows no block-buffer column, and the Defaults dialog looks like app-level defaults (width 137.16 there against 134 on the order), i.e. the user's own settings, which I did not touch; F6 needs pieces of controlled topology from Pattern Design. None is needed to read an unplaced marker; each has its procedure in `MARKER_DATASET_DESIGN.md`.

**The nest spec (8th step) - the deliverable.** `python nest_spec.py "<marker>.zip" --json job.json [--dxf] [--svg] [--units cm|mm|in]` (also
`accumark_marker.py <zip> --nest-spec`) turns a marker-only ZIP into the whole unplaced job for a nesting engine: fabric width and the shortest 100%-efficient length,
one SHAPE per (piece, size, cut) with its cut outline, seam line when the marker holds one, notches, grain, internal lines, drills, area, stored box and `padding`,
and the DEMAND (quantities, with the mirrored outline written out for the mirrored instances). Documented in `NEST_SPEC.md`. Every spec carries its own checks (instances ==
slots, sum of areas == the marker's area to lay, each outline's area == the area AccuMark declared, each outline fits the stored box) and ends `NEST SPEC COMPLETE`.
Verified: the four real marker-only styles (1825D x 2 markers, 5683D, 2591A, 418T), both blind tests, a twin and the 2303 markers - **176 shapes / 243 pieces, all complete**; JSON and DXF
round trips; the spec of a marker-only ZIP equals the spec of the full ZIP (whose outlines come from the piece objects) to 6e-4 cm; units in / cm / mm agree; mirrored geometry;
a part-laid marker (CP 150) lists only what is left; and shapely, knowing nothing about AccuMark, accepts every outline as a valid polygon of exactly the stated area with every
seam line inside its cut line. Found while writing it: the stored home box equals the outline's own box on every marker-only ZIP (even with a block-buffer table present) and is
about 0.12 x 0.19 in larger on the July CP 150 markers - reported as `padding`, not hidden. Not in the spec, and said so: positions, one-way / two-way fabric (Lay Limits are a
separate object - `rotation` is an assumption), notch / drill sizes, and for the older vintage the internal lines, seam lines and a verified grain.

**Fold pieces, and a grain line for every marker-only ZIP (7th step).** The next step after the blind tests: the fold halves of your real styles.
- **The layout of a fold half's stream** (verified against the piece objects of `ID1005 - BACK` / `FRONT` and the 2303 OUCF pieces): the CUT half (the
  outline), then the grain line (2 points), the internal lines (header `I` / `H` / `D` counts), the SEW half - the stitch line, as many points as are left over -
  and the mirror line (2 points). The sew half from the stream equals the piece's stitch line at the base size exactly and at XS / L / XL to 1e-4 in; that piece
  has 7 ruled points and 6 different rule numbers, so it also confirms the chord-similarity grading of the previous step. Grain and internal line are identical at
  every size, the mirror line moves with size (it is the chord of the sew half). So a marker-only ZIP of such a piece now carries its SEAM ALLOWANCE too
  (`sew_outline` in the inventory). The layout is accepted only when it closes geometrically (cut and sew ends lie on the mirror line); 2303 OUCF: the piece's
  perimeter is the cut line there and the marker frame differs from the piece frame by a rigid shift (12 x 1e-4 in on one piece).
- **The older vintage** (the 1825D / 5683D / 2591A / 418T markers - your real styles) lays these lines out differently (id 0 items `(-10000, -1)`, chains
  ending in a `00`-tag item, per-point attribute bytes after the mirror data) and is NOT decoded. Its grain line, however, is recognisable: the second contour's
  first two points are a segment with dy exactly 0 - **89 of 89 records** (88 inside the outline's box) - and every grain line in the bundled piece objects is
  horizontal (81 in the fixtures, 135 over every capture folder). `unplaced_inventory` slots report `grain` with `grain_basis: 'inferred'` for those (117 of 117
  slots of the four marker-only ZIPs), `'stream'` where the layout was verified. It is a position inferred from structure, not a verified read.
- selftest: fold-pieces row (BACK / FRONT at 5 sizes, 35 OUCF records) and a marker-only grain row.

**The second blind test - a piece I designed, imported and made a marker from (6th step).** You asked me to
create the pattern too. With the `accumark-pattern-marker` skill: a 20 x 15 cm panel `CLAUDE-CURVE` written as an ASTM DXF
(`dataset/claude_curve_spec.json`: a rounded corner of 5 points on a 90 degree arc, 2 notches, a drill hole, a grain line, an
internal line, 3 sizes S / M / L, two DIFFERENT grade rules on one chain), imported with the Data Conversion Utility as my own
process, Easy Order -> marker `CLAUDE-D4`, exported (`markers-live/CLAUDE-UNP-D4-CURVE/`, full export = answer key, and a marker-only copy).
Decoded blind, then compared with the piece object I authored:
- order lines, quantities, piece list, laid state, outline verification, 2 type-5 notches per slot: right at once;
- **grain line, internal line and drill hole: wrong.** The stream lays the piece's other lines back to back after the perimeter, each
  starting with an ABSOLUTE point that carries no marker, and I integrated the second and third as steps. Fix: the header records
  `I` (internal line), `H` (cutout), `D` (drill), `G` (grain, implicit 2 points when absent) give each contour's point count, and the counts
  add up exactly to the points left after the perimeter - so the stream is split by them. A contour's start is the item's MAIN part alone
  (a contour-start item can carry up to 6 prefix parts that are not a movement: 2303 OUMO-1). Result: grain, internal lines, cutouts and
  drills equal the piece objects' coordinates on **77 of 77** fixture records (up to 10 lines per 2303 piece), at every size
  (they are not graded), and `unplaced_inventory` slots gain `grain`, `internal_lines`, `drills`;
- **piece-side grading was wrong.** CLAUDE-D4 is the first bundled piece with two different rule numbers on one chain of points (all
  older ones have 0 or 1 ruled point, where any rule gives the same answer). The old rule - blend the two ruled moves by chain length,
  taken from the dxfparser notes - was **0.295 in off** at S and L; the marker's own stream matches a **similarity of the chord**
  between the two ruled points (the chain keeps its shape, the chord is rotated and scaled onto the graded chord) to 1e-4 in on all 20 unruled
  points at both sizes. `graded_outline` now uses it (identical when the two moves are equal, so nothing older changes);
- what the import did: AccuMark rotated the piece 90 degrees so the grain runs along x, and re-ordered the vertices;
- streams: 268 of 268 distinct corpus streams verify (the 3 new ones included). `selftest`: SECOND BLIND TEST row + a corpus row for the
  internal lines; robustness 647 -> 730 (D4 is a seed).
Not covered: a curve AccuMark itself smooths (a DXF has only straight points, so this 'curve' is 5 explicit points), notch types other than 5,
a piece with seam allowance AND a drill.

**The blind test - a marker AccuMark made for me, decoded without fitting (5th step).** You asked me to create
this kind of marker myself. I built it in AccuMark (Easy Order on a fresh order for `ID1005 - TOP`, fabric row `S`,
one of each size XS-XL, marker `CLAUDE-D3-BF`; the fabric-type cell is read-only and a COPIED order only keeps the row
it had - a NEW order lists every fabric type of the model) from pieces that never appeared in a marker before:
**`ID1005 - BACK` and `FRONT`**, real Gerber demo pieces with fold halves, curves, an internal line and seam allowances.
Fixture `markers-live/CLAUDE-UNP-D3-BLIND/`: the full export (answer key) and the same marker with every piece object
stripped (`-MARKER-ONLY.zip`). Result of decoding the marker-only ZIP with the code as it stood:
- order lines, quantities, fabric type, piece list, laid state, warnings: right first time;
- **outlines: none.** My pen-move rule (a chain of more than 6 parts starts a new contour) split a legitimate 7-part step
  of BACK. Fix: `record_outline` tries thresholds 6, 20, never and keeps the first outline that reproduces the record's own
  area and perimeter (the old 255 streams still verify at 6; BACK / FRONT at 20; 265 of 265 now);
- then **10 of 10 slots get an outline whose bounding box equals the stored home box to 0.0001 in** (area within 0.7%);
- **and the answer key disagreed with the old method:** the outline from the piece objects is 1.4 x 0.9 in smaller
  (area ratio 0.89). The piece object holds the STITCH line plus per-segment seam allowances (BACK: 1.0 in on the fold edge,
  0.375 in on three, 0.25 in on one); the marker lays the CUT line. Checked: the stitch-line points sit exactly 0.375 /
  0.25 in inside the decoded outline. `_slot_geometry` therefore prefers the stream outline whenever the piece outline
  fails the slot-area test but the stream verifies (note: "the piece object is the stitch line without its seam
  allowance"). Every earlier fixture had no seam allowance, which is why the piece-side geometry had never disagreed.
`selftest` BLIND TEST row; robustness 561 -> 647 (the blind marker is a seed).

**Point attributes and notches from a marker alone (4th step).** A stream point's kind is in its main tag's low
nibble and its extra byte: low nibble 1 = plain, or a NOTCH when an extra byte follows (type = its low nibble);
any other low nibble = a turn (corner). Against the piece objects' own perimeter points this is right on **7,455 of
7,455** points (notch types included), so `record_outline()` returns `kinds` and `notches`, and the inventory gives
each stream-outlined slot its `notches` (5683D: 36 type-1 notches, from a ZIP with no piece objects). The byte map
counts a verified stream as identified up to its trailer: **identified 32.4%, raw 7.1%, opaque 58.3%** over the 18
markers (44% on 5683D). Left: the extra byte's high nibble and the trailer's last 3 bytes.

**The section-14 stream is geometry - ALL 255 streams decode (3rd step, same day).** Two more rules finished
it. (1) A point with more than 6 parts is a **pen move** (a long jump split into small steps): the next contour
starts where it ends - that was the "unknown tag" chaos in 1825D and 5683D. (2) A **fold piece's** stream holds
one half whose first and last point lie on the fold line (the record's area is twice the half's); the full
outline is the half plus its mirror. Result: **255 of 255 distinct corpus streams** reproduce their own record's
area and perimeter (131 of them after unfolding), and - the independent proof - the bounding box of the decoded
outline equals the slot's stored home box to 0.000 in on all 36 slots of 1825D, 24 of 5683D, 35 of 2591A and 22 of
418T, i.e. the four marker-only ZIPs (your real styles) now read as `GEOMETRY: outlines for every slot` with no
piece object in sight. `record_outline()` returns the outline (`unfolded` flag), `unplaced_inventory` uses it.
Open: the extra byte / low nibble of each tag (a point's attribute), curve-sampling vs control points, what the
header contours are. The byte map now counts a verified stream as identified: over the 18 markers **identified
4.3% -> 28.1%, opaque 91.3 -> 58.3%** (see the 4th step for the final figure); the opaque bytes left are almost all
section 30, the embedded type-10 object.

**The section-14 stream is geometry - the grammar (2nd step, same day).** The first partial decode stopped at
eight unknown tags; they turned out to be one scheme. Every tag is `bit 7 main | bits 6-5 width | bit 4 clear =
extra leading byte`, and **a point's step is the SUM of a chain of prefix parts and one main part** (so `0x33`
= a 12-bit prefix, `0x53` a 16-bit one, `0x41` a 16-bit one with an extra byte, ...). A prefix with low nibble
`0xa` closes the contour and its main part starts the next one (the grain line); tag `0x00` starts a contour
too; the stream opens with 4-byte ASCII header records (`S 24 / M 2 / S 24` on 1825D). RUFFLE now decodes to
**142 of 142** outline points at all five sizes plus its grain line, the rectangle 4 of 4, and - the independent
ground truth for marker-only ZIPs - the polygon of the first contour reproduces the record head's own area and
perimeter (median error 0.0000%, max 0.29% / 0.04%) on **124 of 255 distinct corpus streams**. That includes every
0418T TRS (11) and 2591A LEG (7) record of the MARKER-ONLY ZIPs: `unplaced_inventory` now gives their outlines
(`outline_source: stream`, 22 of 22 slots of 418T, 14 of 35 of 2591A) and on 2591A the bounding box of the
stream outline equals the slot's stored home box exactly (0.000 in), a check the decode never used. Not decoded
yet: 1825D, 5683D (0 parse to the end), the 2303 OUCF fold pieces, 2591A BPNL / POUTH, curved / notched blouse
contours (spec section 8). New: `decode_record_stream`, `verify_stream_outline`, `record_outline`.

**The section-14 stream is geometry - first verified decode (partial).** The plan had declared it
"bounded-opaque"; the fixed part of the head (u16 @+10) and the twin gave the key. A record's stream is
`00 02 00` then items `<tag> <data> <u16 point id>` and the points are the piece's **graded outline in
1e-4 in**: tag `0x99` absolute i32 x/y, `0xf8` / `0xfc` absolute 20-bit x/y (x lo16, y lo16, byte
`x_hi<<4|y_hi`), `0xf9` the same as a signed delta, `0xd1` / `0xd9` signed 16-bit delta, `0xb1` signed
12-bit delta (byte `x_hi<<4|y_hi`, x lo8, y lo8). `accumark_marker.decode_record_stream()` decodes the
leading points and STOPS at the first unknown item: they equal the graded outline **exactly** - the
whole rectangle (4 of 4 points, sizes 2 / 8 / 18) and the first 45 of RUFFLE's 142 points at all five
sizes (8 records, `selftest` row with a bit-flip mutation). Not yet known: the items tagged `0x33 0x53
0x4d 0x21 0x47 0x46 0xd8 0x7a` (0 of 255 corpus streams parse to the end) - so nothing past them is
guessed. The stream's point count exceeds the piece's control points (RUFFLE 209 items for 142
points; LADIES-BLOUSE-BK 105 for 35), so it may hold the finished, curve-sampled cut line. A complete
decode would give outlines from a marker-only ZIP, the one thing the format spec still says is
impossible. The earlier "per-piece attribute table, not geometry" reading is retracted.

**Robustness** 474 -> 561 (the twin is a new seed; canon carries `sig88_model`). The
committed `ROBUSTNESS_REPORT.md` said 303 - it had been restored after every run and was
stale; it is now the real report. selftest PASS, dataset_test 36/36.

## v4.5 (continued, 2026-09-21) - the live experiment: my "never laid" label was wrong

Same labelling rule: `__version__` stays `'3.0'`.

**The experiment** (AccuMark driven live, on Save-As copies of my own scratch marker,
one selection at a time, a screenshot before every click; fixture
`markers-live/CLAUDE-UNP-E1-TWINS/`). `CLAUDE-QTY-TEST` (as generated by the Marker
Wizard: 11 pieces, nothing placed) was opened in Easy Marking and **Saved As E1A with
nothing placed**; then one piece was dragged onto the marker (util 3.45%, 10 unplaced /
1 placed), returned with Piece > Return > Unplaced (back to 11 / 0, 0.00%), and **Saved
As E1B**. Both were exported and decoded.

**Prediction going in (v4.5 part 1): E1B - "laid once, then cleared" - reads slot `@88`
= 0, and a marker that was never touched does not.** Half right and mostly wrong:

- **E1A reads `@88` = 0 too.** So `@88` is not a "never laid" signature; **any Easy
  Marking store clears it**. It is an *as-generated* signature: non-zero on all 24
  markers Easy Marking never stored, 0 on every slot of every marker it has (laid,
  part-laid, stored empty). `@88 != 0 <=> directory word 40 == 0` holds on all 60
  markers, twins included, and is now a check row.
- **A plain store changes more than `@88`** (original -> E1A, all 11 slots the same way):
  directory word 40 **0 -> 1 with zero pieces placed** (so word 40 is a store /
  placement code, not a count of placed slots); centre `0,0 -> -1000,-1000`;
  orientation `0x0000 -> 0x8000` and `0x2000 -> 0xa004` (bit `0x8000` = "stored by Easy
  Marking", and a rot180 preset also gains `0x0004`); home box +5e-5 in in x (rounding to
  the 1e-4 in unit). The header doubles, the areas and every list section are unchanged.
  This also explains the July CP 150 unplaced slots that carry `0x80c7`: those markers
  were stored by Easy Marking.
- **E1B differs from E1A in 12 bytes: the name, timestamps, session residue, and the
  last byte of ONE slot's area double (1 ulp).** Laying a piece and returning it leaves
  no structural trace, so "laid once and cleared" is indistinguishable from "opened and
  stored empty". The decoder therefore no longer claims the distinction.

**Changed in the decoder.** `lay_history` is `as_generated | stored_empty | partial |
laid` (was `never_laid | cleared`, a claim the experiment refuted); the report says
"UNLAID (as generated, never stored by Easy Marking)" or "UNLAID (stored by Easy Marking
with nothing placed)". `laid_state_sources` now treats word 40 as 0 as generated / 1
stored / 2 all placed, so the twins - 0 pieces placed, word 1 - no longer trip the
"laid state ... agree" row (they did, until this was fixed). The orientation-bits warning
applies to as-generated markers only. The check row
`slot @88 signature is zero once anything is placed` is replaced by
`slot @88 signature <=> directory word 40 is 0 (as generated)`.

**Not resolved.** What `@88` counts (9 on a rectangle, then 33, 54, 66, 107 ... per
piece and size), `@52/@54/@60`, what sets the marker-level `0x0040` bit, and the block
buffer table's purpose - those were not reachable with one small marker.

**Verified.** `selftest.py` PASS (the twin test pins every number above and would fail
if a store changed anything else), `dataset_test.py` 36/36, `robustness/run.py` 474/474.

## v4.5 (2026-09-21) - the live round, part 1: 41 real markers from the scratch area

Same labelling rule: `__version__` stays `'3.0'`.

**What was done.** With AccuMark open, the whole `ZZ-CLAUDE-SCRATCH` storage area
was exported read-only from AccuMark Explorer (File > Export Zip, 108 objects,
`C:\Test\CLAUDE-EXPORTS\ZZ-SCRATCH-ALL-20260921.zip`, 382 KB) and pinned as
`markers-live/ZZ-SCRATCH-ALL-20260921/`. It holds **41 markers** made by earlier
work in that area - AutoMark / AccuNest laid, hand-laid, part-laid, never laid,
with unequal block buffers, one with 1,080 pieces - i.e. the variety the 18
hand-built fixtures never had. `markers-live/` is deliberately outside
`markers/` so the strict all-fixtures invariants are not weakened by the five
anomalies below.

**Result: all 41 decode with no exception; 36 are fully clean** (no failing
check, no warning, no unknown byte in a parsed section), including every one of
the 17 never-laid markers. The byte map holds on all 41 (0 leaks; 1,187 - 1,420
unknown bytes each - the same fixed-size set). This is the first test of "read
whatever unplaced marker AccuMark produces" on data nobody shaped for the
decoder, and it exposed two rules that were too narrow and refuted two claims:

- **Fixed: the utilisation identity was over-tight.** `sum(placed areas) ==
  W x L x U` used an absolute 0.01 sq in, calibrated on small hand-laid markers.
  AutoMark exports store the utilisation to 0.01% (`80.00`) and the length to
  0.01, so the product is 2e-4 off on a large marker (ZZ-AM-1: 13417.98 vs
  13420.42) - 9 markers failed on rounding alone. The tolerance is now relative
  (5e-4); a 1% error still fails.
- **Fixed AND retracted: the block-buffer table.** v4.2 said the table has
  `(pieces + 1)` entries, entry k belongs to piece k and entry 0 is a marker-wide
  default. `ZZC-M1..M3` / `ZZN-F1` have **4 entries for 5 pieces**: the table is a
  list of buffer DEFINITIONS (`[0.3937 x4]`, `[0.1968 x4]`, `[0.3937 x4]`,
  `[0.7874, 0.1968, 0, 0]` inches - the last one unequal), and a piece points into
  it by a 0-based index or at none (`0xffff`): BK -> 0, COL -> 1, CUFF -> none, FR
  -> 2, SL -> 3. A piece with no index used to get entry 0 - wrong, and fixed.
  The check row is now `piece buffer indices resolve into the block-buffer table`.
- **Retracted: "the block buffer explains the home box".** v4.2 read the July CP
  150 residual (`home x 2 - bbox` = 0.1182 = 2 x 0.0591 in x) as the buffer. The
  same five pieces in `ZZC-M1` (buffers 0.5 / 1 / none / unequal) and `ZZC-BIG`
  (1 cm everywhere) have **byte-identical home boxes**: the home box does not
  follow the section-6 table. So `bbox_in` in the inventory is now labelled an
  estimate and `home_box_in` (as stored) is exposed beside it; why CP 150 fits is
  open [?]. The block-buffer SIDE ORDER question is therefore moot for the home
  box and still open for what the table is for.
- **New, verified on 59 markers: slot `u16 @88` is a NEVER-LAID signature.** It is
  0 on every placed slot, 0 on EVERY slot (placed or not) of all 6 partly laid
  markers, and non-zero on the slots of all 24 never-laid markers. So an unlaid
  marker is `never_laid` if it carries the signature and predicted `cleared`
  (laid once, all pieces returned) if it does not - `mk['lay_history']`, shown in
  the report. The cleared case has no example in the corpus: a prediction, tested
  live next. Its values (9, 33, 54, 66, 107 ...) are constant per (piece, size)
  and unexplained [?]. New check row `slot @88 signature is zero once anything is
  placed` (all 22 laid + 2 partial pass).
- **Retracted: "0x0040 tracks the pair bit of a `CUT X02` piece".** Across 58
  markers the bit is set on ALL slots of a marker or on NONE (28 / 30, never
  mixed); 2303 and ZZ-COST-A have mirrored pairs and no `0x0040`. It is a
  marker-level setting, not per piece and not the pair. What sets it is open [?]
  (it follows a non-zero section-10 flag word `+6` on most markers but not on the
  foreign 1825D / 5683D / 2591A ones).

**The five anomalies, pinned** (all laid or part-laid; every never-laid marker is
clean): `LADIES-BLOUSE TEST-2` (52 of 54 placed, header `@430` / utilisation
stale); `ZZC-BIGM` (1,080 pieces, `@430` = the true area minus 2^32/1e4 = a
32-bit fixed-point wrap inside AccuMark, utilisation 306%); `ZZN-B7` (`@430`
drifted 1,191 sq in above the placed sum, utilisation right); `ZZC-M3` and
`ZZN-F1` (their 2 placed slots are 7.2% larger than the record they bind to,
cause unknown [?]).

**Not yet done in this round:** the cleared-vs-never-laid experiment on a live
marker (Save As, place one piece, return it, export, read `@88`), and what sets
the `0x0040` bit. Also open: nothing about the two-model / two-fabric order.

**A mistake worth recording, and its size.** After the export, extra Enter presses
meant for the last "Not all components exist" dialogs reached AccuMark Explorer with
all 108 objects still selected, where Enter means "open the selection". That started
a runaway that ran from 09:55 to about 10:20: Explorer launched one editor process
per object about every 30 seconds - **54 editors** (27 Order, 5 Lay Limits, 5 Model,
3 Grade Rule, 3 UserEnv, annotation / cut / notch / plot / search editors ...) and 182
licence-runtime helpers - and opened **about 40 markers as tabs in the user's running
Easy Marking**, next to their own `4155B LACE 30`. Several editors asked "file is
currently opened in another application - open anyway?" (answered No). **Nothing was
saved, modified or deleted**; the cost was windows, file locks and licence sessions
for about half an hour. Recovery, without touching anything the user had open: the
cascade's processes were told apart by start time (all after 09:54; the user's began
days earlier) and closed with `CloseMainWindow` (the same as clicking X - never
kills, never saves), 52 of 53 at once and the 53rd after answering its prompt; the
Easy Marking tabs were closed with the tab menu's **Close All But This** issued from
the USER's tab after checking the title bar, which left exactly their marker (22 of
65 placed, unchanged); the Explorer selection was cleared. The pre-existing scratch
tab `LADIES-BLOUSE TEST-2` was closed too, and two scratch pieces were added to
Pattern Design's in-memory icon menu (not saved). Rules that follow: never press Enter
or double-click with a multi-selection in Explorer; never batch-press a key at a
dialog; deselect (click the folder) as soon as an export is done; and judge each
dialog by a fresh screenshot.

**Verified.** `selftest.py` PASS (live-corpus block: 41 markers, exactly 5
anomalies pinned, buffer-table semantics, tolerance both ways, `@88` incl. the
cleared prediction), `dataset_test.py` 36/36, `robustness/run.py` 474/474.

## v4.6 (2026-09-21) - a marker unlike the corpus announces itself

Same labelling rule: `__version__` stays `'3.0'`. (No v4.5 yet: that number is
reserved for the live-capture round - see "Not done" below.)

The goal is a decoder that reads WHATEVER unplaced marker AccuMark produces in
future. That needs the failure mode to be loud: a variant this reader has never
seen must say so, not return a plausible wrong answer.

- **`marker_warnings(mk)`** names every way a marker can differ from what the
  corpus shows: a directory slot in use that no reader has seen; directory word
  40 outside 0/1/2 or word 41 non-zero; a never-laid slot whose orientation word
  carries bits outside rot180 / mirror / the `0x0040` pair bit; the record index
  missing or non-monotonic (records then came from the regex fallback); slots the
  structure could not bind; a section-10 / 11 / 12 / 15 chain that does not close
  or does not parse; and the two cross-checks of the structural binding - a
  slot's declared area not equal to its bound record's, or its bundle / record
  text disagreeing with the size table. **`coverage_warnings(mk)`** adds bytes
  inside a parsed section that no parser explains (a field never seen). All 18
  fixture markers are silent on both.
- **The cross-checks earn their place.** A first section-13 index entry shifted by
  one byte still produced a plausible-looking record on 5683D (the misaligned
  bytes happened to read as a valid double), so the index's own validation stayed
  quiet; only the per-slot area check noticed. That is why they are warnings and
  not just check rows.
- **`unplaced_inventory` folds them in and the CLI's last line follows:** `python
  accumark_marker.py <zip> --inventory` ends `DECODED CLEANLY`, or `NEEDS A LOOK:`
  with every failing check and warning (byte-map leaks are computed there too - a
  pass over every byte, so not on the `place_marker` path). The intake procedure is
  in `CLAUDE_CODE_HANDOFF.md`.
- **A corpus finding, from writing the orientation warning.** On the four July CP
  150 markers, 61 of 71 UNPLACED slots carry orientation words like `0x80c7`, with
  bits beyond rot180 / mirror / pair, while none of the six never-laid markers'
  slots does. A partly laid marker's unplaced slots were lifted from a lay and
  keep that history, so the warning applies to never-laid markers only, and the
  inventory's `preset` for a PARTLY laid marker is what the slot last was, not a
  clean pre-set pattern.
- **`MARKER_FORMAT_SPEC.md` (new):** the marker's current byte-level spec, tagged
  [V] / [?], separate from `MARKER_DECODE_PLAN.md` (the journal). Seeded from the
  plan's section 1 and everything v4.0-v4.4 established.

Tests: every fixture silent; ten byte patches each raise the warning that names
them (unused directory slot, word 40, word 41, unknown orientation bits, section-13
shift and non-monotonic index, broken section-10 label, section-15 size count, a
slot head past the records, a bundle that disagrees with the size table); and an
unseen variant flips the report to `NEEDS A LOOK`.

**Not done: the live-capture round (v4.5).** Still open and each needing a
controlled AccuMark capture, not more analysis of the existing files: the side
order of unequal block buffers; what sets the `0x0040` pair bit and the pre-set
rot180 alternation; slot `u16 @88` and `@52/@54/@60` (needs a never-laid vs
cleared twin of one marker); the one-sided y excess on the July CP 150 unplaced
slots; two models / two fabric types in one order; size names with spaces.

**Verified.** `selftest.py` PASS, `dataset_test.py` 36/36, `robustness/run.py`
474/474.

## v4.4 (2026-09-21) - a byte map for the marker: "fully decoded" is now a number

Same labelling rule: `__version__` stays `'3.0'`. Additive: `marker_coverage(d)`
in `accumark_marker.py`, the marker-side sibling of `accumark_pds.coverage()`.

Every byte of a marker object is classified: `identified` (position and meaning
known), `raw` (position and extent known, meaning open), `zero_pad`, `opaque`
(a blob whose extent is known and whose content is bounded on purpose) or
`unknown`; each unknown run is attributed to the section whose chain span
`[dir[k] - 6, dir[k+1] - 6)` holds it (0 = envelope / directory, -1 = trailer).

**Result over the 18 fixture markers** (3 KB - 287 KB each):
- Every byte owned by sections 6, 11, 12, 13, 14, 15, 21 and 30 is classified -
  no parsed section leaks an unknown byte. The selftest asserts this, so a parser
  change that loses a section fails; a mutation (a zeroed model-name length) makes
  section 11's bytes fall out of the map.
- **Unknown bytes: 1,187 - 1,829 per marker, 1.38% of all bytes overall, and about
  the same count on a 3 KB marker as on a 280 KB one** - a fixed-size set, not a
  share of the content. Overall: identified 4.1%, raw 2.4%, zero_pad 0.8%,
  opaque 91.3%.
- **The opaque 91.3% is two blobs, bounded on purpose:** section 14's per-point
  attribute stream (extent fixed by section 13's index) and the embedded type-10
  object (section 30; `MARKER_DECODE_PLAN.md`: its slot 39 is a function of piece
  topology only - independent of layout, fabric cost, grading complexity).
- **Where the unknown set lives**, summed over 18 markers: trailer 6,375 B,
  section 1 (header scalars, of 372 B only six doubles are read) 5,688 B, section
  2 (options + marker name) 5,106 B, section 3 4,444 B, section 5 (`-PDSTEXT-`
  label table) 2,760 B, envelope 1,659 B, section 4 264 B, section 10's 6-byte
  lead 98 B.
- **Most of it is constant.** Position-aligned across the 18 markers, of section
  1's 316 unknown byte positions 271 are byte-identical in every marker (45 vary);
  of section 2's aligned positions 228 of 238; section 4 11 of 12; the trailer 222
  of 338 (116 vary). Sections 3 and 5 are variable-length lists (most positions
  are not present in every marker) and need a walker, not a constancy map. So the
  work left is: the ~45 varying bytes of section 1, the varying part of the
  trailer, and structure for sections 2-5 - a short list, each item with a
  method (twin diff against a laid export of the same marker; correlate against
  marker name length / piece count / fabric cost).

**Not claimed.** `raw` is not "understood": the flag bytes of a piece row, a
slot's constant sentinels (`+34..+41`, `+50..+63`, `+68..+87`), slot `u16 @88`
(non-zero on never-laid markers, 0 on laid ones - meaning unknown) and the
size-row `flags` word are counted `raw`, i.e. located but open. The map measures
where knowledge ends; it does not extend it.

**Verified.** `selftest.py` PASS (byte-map guard + mutation), `dataset_test.py`
36/36, `robustness/run.py` 474/474 (no decoder behaviour changed).

## v4.3 (2026-09-21) - the unplaced case is fuzzed and asserted, not just decoded

Same labelling rule: `__version__` stays `'3.0'`. Test infrastructure only; no
decoder behaviour changes.

Three places where an unlaid marker used to pass because nothing looked:
- **`robustness/`: no marker seed was ever unlaid.** Both marker seeds were laid,
  and `canon_place_marker` fingerprinted a marker by its `placements` and
  `outlines` - both empty on a never-laid one - so Oracle A could not have told
  a wrong slot, record, size row or order line from a right one, and Oracle C
  would have failed outright ("no provably-live offsets": an unlaid slot's x / y
  are 0.0, and corrupting a 0.0 high byte still reads ~0). Now the canon
  serialises slots, records, sizes, models, pieces, the order copy, block
  buffers, laid state, header-sum modes and the inventory; `2303-BD137-UNLAID`
  and `5683D-SS21-UNLAID` are seeds; and for a marker with nothing placed
  Oracle C probes the bytes the decoder demonstrably reads on every slot (home
  box, declared area, orientation word, bundle, the slot head) and per record
  (declared area, perimeter). Result: **303 -> 474 checks, all pass** - Oracle A
  84 rows on the two new seeds, Oracle C 87 probes (45 + 42), every one changed
  the decode. Mutations that do not change the byte (a `zero` of a byte that is
  already 0) are now skipped instead of counted as silent misses.
- **`dataset_test.py`: the `reused` branch returned True unconditionally**, so
  the dataset's own listed UNPLACED case (`2303-BD137-UNLAID`) asserted nothing.
  It now requires no failing check row (bar any the manifest entry lists) and
  every slot structurally bound; with the binding re-broken it fails.
- (v4.2's `@430` row already caught the dataset generator; see v4.2.)

**Verified.** `selftest.py` PASS, `dataset_test.py` 36/36, `robustness/run.py`
(full) 474/474.

## v4.2 (2026-09-21) - the unplaced job spec: order lines, laid state, block buffers, and an inventory you can read

Same labelling rule: `__version__` stays `'3.0'`. Purely additive - a diff of
every field, placed outline, geometry check and existing check row against the
v4.1 commit, over all 18 fixture markers, is byte-identical.

**What it is for.** A never-laid marker is a cut order: what must be laid, on
what width, and nothing about where. `unplaced_inventory` turns the parts of
the marker that say so into one structure a nesting run (or a person) can use,
and `python accumark_marker.py <zip> --inventory` prints it as a cut order
ending in `DECODED CLEANLY` or `NEEDS A LOOK:` plus every failing check and
warning. On a marker-only ZIP (no pieces) it reports `geometry none` instead
of looking like "all fine" - the old `piece_errors == {}` was the same for
"all decoded" and "there were none".

- **Section 15 is the ORDER copy [V: 18 of 18].** A chain of model blocks
  closing exactly 6 bytes before section 21: a 48-byte header (name length @+0,
  1-based model ordinal @+8, size count @+12, fabric-type count @+14), the model
  name, its fabric types (`<u16 len><text>`), then per size a row `<u16 name
  len><u16 QUANTITY><24 zero bytes><size name>`. The model names equal section
  11's; **the QUANTITY equals the number of size-table rows for that (model,
  size)** - each cut of a size is its own row and bundle (CLAUDE-QTY-TEST: 3
  rows of size 8, quantity 3; AD1234: XS x2, S x4, M x4, L x2, XL x1) - and the
  pairs cover the size table exactly. This is the per-size quantity the earlier
  notes located in the Order object only; the marker carries its own copy, so a
  marker-only ZIP still states its quantities.
- **Section 6 is the block-buffer table [V framing; ? side order].**
  `(pieces + 1)` entries of 102 bytes from `directory[6] - 6`: `<u16 0><4 x f64
  inches><68 zero bytes>`; every double is 0.0591 in (1.5 mm) on the four
  markers that have one (1825D x2, 418T, July CP 150). A piece row's
  `buffer_index` (section 10, flag bytes 4..5) equals its 1-based position in
  the piece list on all of them, so entry 0 is the marker-wide default and entry
  k piece k's own. (An earlier reading - two u32 words, high word first - came
  from a frame misaligned by four bytes.) It is what makes `home x 2` exceed a
  piece's own bounding box: on the July CP 150 markers the x residual is
  0.1182 in = 2 x 0.0591 with no buffer and 0.0000 with it. Which side each
  double is cannot be told from the corpus - all four are equal - so the file
  order is kept [?] and settled by a live capture with unequal buffers.
- **Laid state, from three independent sources.** `mk['laid_state']` is
  `unlaid | partial | laid` from the slots' own coordinates (what a nesting run
  consumes); `laid_state_sources` also carries directory word 40 and the
  header's length/utilisation, and a check row fails if they disagree (18 of
  18 agree; the header alone cannot tell partial from laid - the July markers
  have length and utilisation but 1 slot placed of 72). Header `@430` is the
  summed declared area of the PLACED slots (= W x L x U / 100), 0 on a never-laid
  marker [V: 18 of 18].
- **Header sums are reported as a MODE, not a pass/fail.** `header_sums` says
  whether `@422` / `@454` equal the sum over `all` slots, the `last_model`'s
  slots, `2x_all`, or `other` (see v4.1 "Observed"): `all/all` on every never-laid
  single-model marker, `last_model/last_model` on the unlaid 2303-BD 137,
  `all/last_model` on its laid twin and on the July markers, `all/2x_all` on
  LADIES-BLOUSE [?]. The selftest pins the mode per fixture, so a marker that fits
  none of them is loud.
- **`unplaced_inventory(mk, pieces=None, piece_errors=None)`** - per unplaced
  slot: ordinal, bundle, model, size, piece, category, cut, copies, **pair**
  (a `CUT X02` piece is a mirrored pair: two slots of one (bundle, record), the
  plain one `A` and the `0x0080`-mirrored one `B` [V: 116 of 116 pairs]),
  declared area, perimeter, `bbox_in` (home x 2 minus the piece's block buffer),
  **preset** orientation (rot180 / mirror / the `0x0040` pair bit / other bits -
  reported as a pre-set lay pattern, never counted as a placement), and with
  pieces in the ZIP the outline, `bbox_dx/dy` and `area_ratio`; plus the order
  lines (model, size, quantity, bundles), totals (area to lay, perimeter, the
  length a 100%-efficient lay would need = area / width, counts by size and by
  piece) and named warnings. `place_marker` returns it as `inventory` and the
  slots' geometry as `unplaced` (the shape of `placed`, outline in the piece's
  own frame) plus `geometry_available`; `bbox_check` / `area_check` take
  `which='unplaced'`.
- **First geometric check that runs on an unlaid marker.** With the corrected
  sizes, `2303-BD 137` (unlaid, 18 pieces bundled): every one of 97 slots' home
  boxes matches the piece's own outline at its tiled size to 0.0156 in (0.02 in
  tolerance), and declared area matches the shoelace area within 1% on 66 of 66
  (piece, size) pairs; `CLAUDE-QTY-TEST` 3/3 to 0.0001 in. The July CP 150
  markers (71 of 72 unplaced, pieces bundled): x is exact once the block buffer
  is subtracted (67 of 71 within 0.02 in), area 36 of 36 pairs, but **y carries a
  one-sided excess of up to 0.0786 in on 48 of 71 slots (never negative)** that
  nothing explains yet [?] - the one placed slot, verified against the drawn
  DXF, is exact (0.0001 in) - so that fixture is held to the 0.08 in curve band
  and its `bbox_ok_unplaced` is deliberately not pinned. Candidates: a notch or
  curve extremum that the stored points understate, not tested.
- **Found by the new checks, not by looking:** `dataset/build.py` patched the
  generated marker's `@422` and utilisation but never `@430`, so the tracked
  `GENERATED-SAMEBBOX-MARKER.zip` carried a stale placed-area double; the new
  `@430 == sum of placed slot areas` row failed on it, the generator now patches
  it, and the marker was regenerated (the 31 piece zips are unchanged).

Added: `parse_order_copy`, `parse_block_buffers`, `unplaced_inventory`,
`unplaced_slots`, `inventory_report`, `--inventory [--json]`; `mk` keys
`order_copy`, `order_copy_end`, `block_buffers`, `placed_area`, `laid_state`,
`laid_state_sources`, `header_sums`; four `check_marker` rows (`order copy tiles
section 15; quantity == size-row count`, `laid state: placed word, slot
coordinates and header agree`, `header @430 == sum of placed slot areas`, `piece
buffer indices == list positions`); twelve `verify_marker.facts` keys
(`laid_state`, `slots_bound`, `unplaced`, `order_cuts`, `geometry`,
`hdr_area_mode`, `hdr_perim_mode`, `bbox_ok_unplaced`, `bbox_n_unplaced`,
`bbox_worst_unplaced`, `area_ok_unplaced`, `area_pairs_unplaced`); selftest rows for all of it, four more mutation
patches (section-15 quantity, directory word 40, `@430`, a block-buffer index -
ten in all with v4.1's), and an inventory test on the marker-only 2591A ZIP
(35 slots, 14 mirrored pairs, geometry none).

**Verified before handing back.** `selftest.py` PASS, `dataset_test.py` 36/36,
`robustness/run.py` (full) 303/303; old-vs-new (v4.1 commit vs working tree) over
all 18 markers: fields, placed outlines by hash, placed bbox/area checks and every
existing check row identical, 3-4 new rows per marker all passing.

Not done, and why: the unequal-buffer side order, what sets the `0x0040` pair
bit, and the CP 150 y excess all need a controlled AccuMark capture (a piece with
a known notch / unequal block buffers / a flip option); slot `u16 @88` and
`@52/@54/@60` need the cleared-vs-never-laid twin. They are next in the plan, not
solved here.

## v4.1 (2026-09-21) - unplaced markers: slots bound by structure, not by area

Same labelling rule as v4.0: `__version__` stays `'3.0'`.

**Trigger.** Planning "fully decode unplaced markers" (a never-laid marker is a
cut order: WHAT to lay, on what width - nothing about where). Three more
never-laid, marker-only samples from the same foreign origin arrived
(`5683D-BD 168 SS21`, `2591A-BD 157 AW SS21`, `418T-BD 160 SHAPESHIFTER`) and
are now fixtures (`markers/5683D-SS21-UNLAID/`, `markers/2591A-SS21-UNLAID/`,
`markers/418T-SHAPESHIFTER-UNLAID/`, byte-identical copies). They decoded without
error, and `check_marker` said 5/5 ok - but two of those five rows read `0/0`
on any unlaid marker, so "ok" proved little. Measuring what the checks did NOT
cover found a real bug.

- **BUG: slot -> size binding by declared area picked an arbitrary size
  whenever sister sizes tie on area.** `parse_marker` bound each slot to the
  section-14 record whose area was nearest (dxfparser's rule) and rejected only
  rival PIECES, so two sizes of one piece with the same area were never a
  conflict and `ranked[0]` won. Measured against the previous build: the size
  changes on **77 of 97 slots of both 2303-BD 137 markers**, 54 of 72 on each
  CP 150 marker (plus 14 slots per marker that were unbound), 11 of 13 on AD1234
  and 1 of 2 on CLAUDE-GRADE-MARKER; on LADIES-BLOUSE all 54 slots were unbound.
  It stayed invisible because style 2303's grading is all placeholder (sister
  sizes share one shape and one area), so no geometric check can tell them
  apart. **Proof of the correct size, independent of area and geometry:** the
  drawn DXF labels every placed piece `<piece> <size>` at its placed centre -
  with the structural binding 97 of 97 placed slots of `2303-BD 137 PLACED` sit
  within 0.001 in of a label reading exactly that; with the old rule 20 of 97.
  The same holds on all four July `2303-CP 150` markers (1 of 1 each, where the
  label is three stacked TEXTs) and on `CLAUDE-GRADE-MARKER` (2 of 2).
- **How a slot is bound now [V: 677 of 677 slots on all 18 markers].** From the
  file's own structure; the declared area, the slot's bundle and the record
  text are CHECKED against it, per slot, never used to choose:
  - `size`, `model` <- the size table (section 12) tiles the slot table:
    row `i` owns slots `ordinal .. ordinal + pieces - 1`;
  - `record` <- the slot's 6-byte **head**, which sits just BEFORE its 96-byte
    body: `<u16 record index (0-based, section-14 order)> <u16 piece index
    (1-based, section 10)> <u16 bundle>`. What earlier notes called the
    "@90/@92/@94 circular triple" is simply the NEXT slot's head;
  - `piece` <- section 10 at `piece index - 1`.
  Agreement: the record's area matches the slot's on 677/677; the piece name
  starts the record text on 466/466 slots of the markers that list pieces;
  `slot bundle == head bundle == size-row index` on 677/677; the record text
  ends with `<tiled size>G` on 677/677.
- **Section 10 (piece list) is a length-prefixed chain [V: 18 of 18].** A
  28-byte header ending in the literal `MARKER`, then contiguous rows
  `<u16 name len><u16 category len><24 flag bytes><name><category><fabric
  types: u16 count at flag byte 18, then that many <u16 len><text>>`, closing
  exactly 6 bytes before section 11. The regex it replaces needed exactly one
  fabric type, so it returned `[]` on every CLAUDE-* marker (which is why
  `placed pieces are in the piece list` was BAD on all four of them and on the
  generated dataset marker) and would have missed LADIES-BLOUSE's collar and cuff
  fabric types (`M`, `F`). Flag bytes 4..5 (u16) are a 1-based index into
  section 6, `0xffff` for none; the rest of the flags stay raw.
- **Section 14 is walked from section 13's index** (offsets relative to 6 bytes
  before `directory[14]`, label text 48 bytes into each record) [V: identical -
  offset, text, area, perimeter, prefix, stream length - to the regex on all 18
  markers]. It cannot skip or invent a record and fixes their order, which the
  slot heads index into; the regex remains the fallback.
- **Directory words 40 and 41 are not offsets.** Word 40 is a state code - 0 /
  1 / 2 = no / some / all slots placed [V: 18 of 18: 0 on every unlaid marker, 1
  on the July 1-of-72 markers, 2 on every fully laid one] - and word 41 is 0.
  `_section` read 1 and 2 as file offsets and made a bogus section 40 on every
  laid marker (11 of 18). Exposed as `mk['placed_word']`.
- **Record split uses both name sources.** The `-PDSTEXT-` label scan finds
  nothing on LADIES-BLOUSE, so all 20 of its records went unsplit; the names now
  also come from section 10, and a record's `size`/`cut` are set exactly from
  its slots' tiled size rather than guessed from the text.

Added:
- `parse_slots` keys `index`, `record_index`, `piece_index`, `bundle_head`;
  `parse_marker(d, size_vocab=None, binding='structural')` (`binding='area'` is
  the old rule alone, kept for diffs and mutation tests); per-slot `model`,
  `row`, `binding={method, area_ok, bundle_ok, text_ok}`; `mk['placed_word']`,
  `records_source`, `piece_list_end`; `piece_records_indexed`,
  `_walk_piece_list`; piece rows gain `fabric_types` and `buffer_index`.
- Six `check_marker` rows that count EVERY slot, placed or not (appended, no
  existing row renamed): `every slot bound structurally`, `slot bundle == head
  bundle == size-row index`, `slot declared area == bound record area`,
  `record text ends with the tiled size + G`, `records == section-13 entries`,
  `piece list tiles section 10`. All pass on all 18 fixture markers.
- `verify_marker.dxf_labels()` and the `dxf_size_labels` fact.
- `selftest.py`: `dxf_size_labels` on the three DXF fixtures; a table-driven
  unplaced block (slots per (piece, size) - the cut quantity, `2` for a `CUT X02`
  mirrored pair - laid state, `@422`/`@454` sums) over the six never-laid
  markers; six byte-patch mutation tests, each breaking exactly the row that
  checks it; a negative control (the old rule scores 20/97 against the DXF).

Changed:
- Slot `size` (and so `record`) on the markers listed above; nothing else in
  any marker's decode changed (no record byte, model, size row, laid state or
  placement moved). `MK` row for `2303-BD137-PLACED`: `area_ok/area_pairs`
  12/12 -> 66/66 (each (piece, size) pair now measured, not 12 arbitrary ones).
- `dataset/build.py` patches areas through the slot binding, so the regenerated
  `GENERATED-SAMEBBOX-MARKER.zip` now has BOTH records patched (the tracked copy
  had record 1 stale - the new area check caught it) and its
  `pre_existing_failures` list is empty. The 31 piece zips are byte-identical in
  content (container timestamps only) and were left as committed.

**Verified before handing back.** `selftest.py` PASS, `dataset_test.py` 36/36,
`robustness/run.py` (full) 303/303. Old-vs-new field diff over all 18 markers
against a `git worktree` of the v4.0 commit: no record byte, model, size row,
laid state, placement count or check row changed except as listed; no check
that passed before fails now; every new row passes everywhere. Mutation tests:
re-breaking the directory-word-40 fix alone yields a bogus section 40 on 11
markers; each of six byte patches (slot-head record, slot-head bundle, section-13
offset, section-10 fabric-type count, size-row piece count, `binding='area'`)
flips exactly its row.

Observed, not changed:
- Header `@422` / `@454` on never-laid markers equal the sums over ALL slots'
  declared areas / record perimeters exactly on the six markers that were laid
  by nobody (1825D x2, 5683D, 2591A, 418T, CLAUDE-QTY-TEST). On the multi-model
  2303 markers `@454` equals the sum over the LAST model's slots only (19.5158 on
  both 2303-BD 137 exports, 104.0376 on CP 150), and `@422` does too in the
  unlaid export (6.2726) but equals the all-slot sum in the laid export of the
  same style (5735.2104). So the earlier "stale value" wording is retracted: the
  arithmetic is exact, the cause (a last-model accumulation that laying
  overwrites?) is unproven [?]. LADIES-BLOUSE `@454` is exactly 2x the all-slot
  perimeter sum, still unexplained [?].
- A July-vintage drawn DXF carries a header line `MODEL:SZ/QTY:<model>:<size>/<qty>`
  (e.g. `2303 MOCUP B1 1:32A/1`) - an answer key for the order lines (model,
  size, quantity) that no check uses yet.

## v4.0 (2026-09-21) - first foreign-origin marker: model list, size table and trailer stamps fixed

v4 is the label for this round's decoder-improvement documentation only:
`__version__` in `accumark_pds.py` / `accumark_marker.py` (and the assertion in
`selftest.py`) deliberately stays `'3.0'`.

**Trigger.** The first marker from outside this project's own AccuMark
install: `1825D-BD 180 SS21.zip`, added as `markers/1825D-SS21-UNLAID/`
(byte-identical copy, 22,297 bytes). It holds two UNLAID kids' markers -
`1825D-GT 168 SS21` (168 cm, 1 piece x 9 sizes) and `1825D-BD 180 SS21` (180
cm, 3 pieces x 9 sizes; sizes `2-3` ... `11-12`, model `CON2-1825D`) -
exported 2020-10-16 by another user (`raveenl`; its own `comments.txt` says
"version 9 data"), with no piece, model or order objects, so it carries no
geometry to reconstruct. Run unmodified, the decoder opened it without error
and read the header, all 36 piece/size records and all 36 slots correctly (the
header's total area and `@454` equal the sums over the records to 1e-13), but
returned `models=[]`, `sizes=[]`, a wrong size and cut description on every
record (`3` / `CUT X 012-` for `2-3` / `CUT X 01`) and 2024 / 2022 for the
trailer's created / modified stamps. Chasing those turned up three defects,
and the model-list one had been silently wrong on production data all along.

- **Size table (section 12) was never read correctly.** `parse_sizes_section`
  was a regex (names shaped `\d{1,2}[A-Z]{0,3}`, delimited by `ff ff 00 00`)
  that took the fields AFTER each name. The table is a chain of rows, each a
  14-byte descriptor followed by its name:
  `<u16 name length><u16 model index, 0-based><u16 pieces><u32 first slot>
  <u32 flags><name>`. So (a) any name outside the old shape was invisible -
  `2-3`, `11-12`, `XS`, `M`, `XL` - and AD1234 TEST 134 (13 rows),
  LADIES-BLOUSE TEST-2 (6) and both 1825D markers (9 each) returned no sizes at
  all; (b) rows whose flag word is 0 rather than `ff ff 00 00` had no
  delimiter; (c) every row carried its successor's fields, which is why `f0`
  (the long-open `[?]` in `MARKER_DECODE_PLAN.md`) looked unexplained - it is
  the name length, seen one row early - and why the model index looked
  1-based. Verified on all 15 distinct corpus markers (both vintages, 1-11
  models, 2-61 rows): the walk from `directory[12] - 6` ends exactly at
  `directory[13] - 6`; `sum(pieces) == len(slots)` (97 x2, 72 x4, 2 x4, 3, 13,
  54, 9, 27); each `first slot` is the running sum of `pieces` from 0; model
  indices are non-decreasing and index the model list; and the size names are
  identical to the old regex's on the 11 markers it could read.
- **Model list (section 11) dropped models.** `parse_marker` took models from
  `_len_after_strings` ("the u16 after a name equals its length"). The list is
  `<u16 length><name>` - length BEFORE - which passes that test only when the
  next name happens to have the same length. It dropped `2303 MOCUP B1 7`,
  `2303 OUCF DD` and `2303 OUCF E` (8 of 11) on 2303-BD 137, `2303 MOCUP B1 9`
  and `B1 11` (9 of 11) on the four CP 150 markers, and returned nothing at all
  for 9 of the 15 markers (every single-model one). New `parse_model_list`
  walks the chain from `directory[11] - 6`; it closes exactly at the size
  table's first row on 15/15, and on the 2303 markers all 11 names are the
  model objects bundled in the same ZIP. `_len_after_strings` is removed.
- **`created` / `modified` were junk on ~89% of objects.** `read_object`
  slid a 4-byte window over the whole 396-byte trailer at every offset and
  kept the first two values that looked like 2014-2039 Unix times (`66 00 00
  00` / `62 00 00 00` read as 2024 / 2022). It agreed with the real fields on
  30 of 269 objects (11.2%) in the repo's 103 zips. The stamps are aligned
  `u32`s at trailer +0xF4 / +0xF8 (`TRAILER_CREATED` / `TRAILER_MODIFIED`):
  all 269 objects (piece 159, model 38, rule table 26, marker 16, order 7, lay
  limits 7, notch table 8, annotation 7, block buffer 1) carry a real date
  there - 267 inside the old 2014-2039 window, the other two shared library
  tables (real stamps 2004-01-08 and 2013-11-06) just outside it, so the
  plausibility window is now 1980-2040 - with created <= modified on 268. The
  exception is the M-MARKER annotation table in the CP 150 zip (created
  2023-01-19, modified 2013-11-06), reported as stored. Independent check: the
  1825D stamps (06:16:15 GT and 06:11:35 BD UTC, 2020-10-16) sit 5 h 30 m and
  5 h 35 m before the ZIP members' local time (11:46:32), in line with the
  ~5.5 h export lag `FORMAT_SPEC.md` section 7 measured on this project's own
  exports.
- **Record split falls back to the marker's own sizes.** When a piece's size
  table is not supplied (its piece object is not in the ZIP) `parse_marker` now
  splits the `<piece><cut><size>G` record text against the marker's size
  table instead of by pattern; the pattern cannot tell `CUT X 01` + `2-3` from
  `CUT X 012-` + `3`. 0/36 records on the 1825D markers had a real size
  before, 36/36 now, with one cut description per piece (`CUT X 01` for
  FROT / OGUS / IGUS, `CUT X01` for BACK). No other fixture's split changed.

**Added.** `check_marker` gained two identities (only when a size table was
read): "model list + size table tile sections 11-12" and "size table:
sum(pieces) == slots, ordinals cumulative, model index in range" - both hold
on 15/15, so a marker with a layout this reader has not seen now says so
instead of being silently mis-read. `mk['sizes']` rows are now `size`,
`model_index` (0-based), `n` (pieces = slots the row owns), `ordinal` (index of
its first slot), `flags`, and `model` (the name `model_index` points at);
`f0` is gone. `mk['table_ends']` records where each walk stopped. The CLI
(`python accumark_marker.py <zip>`) prints models and sizes, and for an
unlaid marker the first 8 records, which it used to omit entirely.

**Verification.** Old-vs-new field diff over every marker zip in the repo (12
zips, 16 markers, from a copy of the v3.0 modules): models changed on all 16
as strict supersets, none lost; size names changed only where the old reader
returned nothing (4 markers); record text / area / perimeter never changed;
the piece / cut / size split changed only on the 36 1825D records;
placements, placed outlines and every pre-existing check identical; the 32
new checks all pass. `python selftest.py` PASS (12 new v4 checks; the new
section fails on the v3.0 decoder, and re-breaking each of the three fixes
separately fails the matching checks), `python dataset_test.py` 36/36,
`python robustness/run.py` (full) 303/303, quick matrix 84/84.

**Observed, not changed.** (1) `users` is still the old token scan of the
trailer and includes fragments of the object's own name (`GT`, `SS21`); the
object's name itself sits at trailer +0x8A (269/269 objects) and two user-name
strings at +0x110 / +0x162 (equal on 252 of 269; both empty on 41, mostly
rule tables; `MSI`, `sachithraper`, `DilshiniS`, `raveenl` ... in this
corpus). (2) The
size-row `flags` word is `0xffff` on 12 of the 15 markers and 0 on
LADIES-BLOUSE and both 1825D markers - meaning unexplained. (3) `@422` is the
sum of ALL slots' declared areas on 14 of 15 markers (equal to W x L x U / 100
only when every slot is placed - this resolves the "holds something else on
the July markers" `[?]` in `check_marker`; the exception is the 2303-BD 137
unlaid export, 6.27, stale). `@454` equals the sum of all slots' record
perimeters on 8 of 15 (1825D x2, CLAUDE-QTY-TEST, CAP-C21-SEC14, the three
CLAUDE-GRADE markers, AD1234) but not on 2303-BD 137 (19.5158), the CP 150
markers (104.04) or LADIES-BLOUSE (exactly 2x there) - still unexplained in
general.

## v3.0 (2026-09-12 to 2026-09-13) - exact kind-2 seam model and structured survey

- Resolved the provisional internal-list names by native-to-ASTM geometry:
  `0x49=internal` (layer 8), `0x48=internal_cutout` (layer 11), and
  `0x4d=mirror` (layer 6). The MOCUP no-edit capture matches 20/20 lists
  across OUMO/INMO; the production OUCF capture matches 2/2.
- Added `verify_capture.py --internal-layers`, a block-aware LINE/POINT/
  POLYLINE checker that aligns each native piece from its layer-1 perimeter
  and requires every internal list to match an equal-length entity on its
  semantic ASTM layer. Added these captures to `selftest.py`.
- Corrected the API names inherited from the historical
  `CAP-C60-CUTOUT`: generic tag `0x49` now appears in `internal_lines_in` and
  `internal_points`; `cutouts_in` / `cutout_points` now mean the verified
  layer-11 `0x48` geometry. Added `grain_lines_in` and `mirrors_in`.
- Fixed `parse_segments()` to accept all observed first-record preambles and
  both seam trailers (immediate `u32 3` and six-zero-padded). Segment and
  explicit cut-line records are now scoped to their owning piece block.
- Added `seam_line_points(block)`: signed chord offsets, linear begin/end
  taper, curve miters, adjacent zero-offset perimeter lines, and consumed
  short edges. It reproduces the controlled TASK2/C30/C31 numbered cut-line
  points to at most one native unit; C30 and C31 now pass
  `line_table_consistent`.
- Added `classify_line_table()` with per-point labels and match evidence while
  retaining `check_line_table()` as the existing bool API. Exact checks run
  before the old axis/diagonal and curved-distance fallbacks.
- Tightened every internal-list entry path to require a complete count walk,
  valid terminator, and trailing `Lnn`, matching the bridged-list validation.
- Expanded `kind2_survey.py` with child tags, seam edge/role, expected point,
  residual, shared-corner record/ID evidence, and nearest perimeter segment.
  On 44 ZIPs / 133 blocks / 13,369
  kind-2 points: 12,992 stored geometry, 294 exact seam-model points, 8
  accepted seam fallbacks, 5 structurally matched internal-curve table-extra
  points, 68 topology-validated `shared_seam_corner` points, and 2 tightly
  bounded `seam_model_quantized` curve points. All **133/133** blocks now pass;
  no point remains in the generic `unexplained` class.
- Identified the final five generic residuals as one exact 46-vs-44 encoding:
  the line table reproduces a stored `0x49` curve in order, inserts one
  near-start point, and repeats the final vertex. Classified the inserted
  point as `internal_curve_table_extra` without guessing its spline/control
  semantics; all five occurrences have delta `(15,22)` or `(16,22)` from the
  stored start vertex and are regression-tested.
- Added classification counts to the robustness canonical form and updated the
  controlled seam expectations and one-unit assertions in `selftest.py`.
- Classified the separate final kind-1 residue: two one-unit
  `stored_geometry_quantized` points and eight
  `shared_graded_perimeter_point` occurrences. The graded points are duplicated
  at adjacent edge boundaries, carry rule-10001 and point-name children, and
  match the same perimeter ID within 25 native units. Added one-copy mutation
  tests for both shared seam corners and shared graded points so topology, not
  proximity alone, is required. Corner-style names remain open for CAP-C36.

## v2.0 (2026-09-11, continued once more #27) - live AccuMark V17 import validation of the generated dataset (decoder v2 plan's last outstanding verification step)

User asked to run the live AccuMark validation: the one verification step
from the decoder v2 plan that was never non-circular, since every other
check (Oracle 1 by construction, Oracle 2 metamorphic, Oracle 3
corruption detection, `dataset_test.py`) runs through this project's own
decoder and writer, so a shared wrong assumption between them could pass
silently. Only importing a generated piece back into AccuMark's own GUI,
completely outside this codebase, can catch that.

**Method**: used `AccuMark Explorer`'s native `Import Zip` (Windows-MCP
desktop control, per this project's standing practice), targeting three
`dataset/generated/` pieces chosen to cover the three structurally
distinct templates: `SKIRT-FRONT` (rect4g, 4 points, no notches),
`BLAZER-BACK` (notch8, 8 points, 4 notches), `SHIRT-SLEEVE-L` (curve34,
34 points, a curved sleeve cap - the template most directly relevant to
this session's curved-seam investigation). Imported into `DATA90`, the
scratch storage area already used for every other live-AccuMark test
fixture in this project (never production data, per the standing rule).

**Result: all three passed, independently of this project's own code.**
AccuMark's own `Import Zip` dialog recognized each as a valid `Piece`
object by name/type/size before the import was even confirmed - the
first independent parse. After import, `AccuMark Explorer`'s built-in
piece preview and `Pattern Design`'s canvas rendered each shape
correctly with no crash or corruption warning: `SKIRT-FRONT` as a clean
4-corner rectangle (13.5in x 22in, matching the drafted aspect ratio);
`BLAZER-BACK` as a rectangle with exactly 4 evenly-spaced notch ticks
along one edge, matching the manifest's `notch_indices` count; and
`SHIRT-SLEEVE-L` as a smooth, continuous curved outline with all 34
points and grade markers placed around it - AccuMark's own curve
rendering, entirely independent of this project's `_nearest_polyline`/
`_seg_path_ok` logic, agreeing that the generated curve data is
coherent.

This closes the last standing item in the decoder v2 plan's Verification
section (item 6, "import 2-3 generated zips back into AccuMark V17
through the GUI"). No code changed this entry - this was a verification
pass, not a fix.

## v2.0 (2026-09-11, continued once more #26) - implemented the interior-window search; found+fixed a second real limit (SEAM_OFFSET_MAX) along the way

User asked to implement the interior-window search flagged as a concrete
next step by the previous entry.

**Added the search**: `_curved_seam_trimmed_indices` slides a small
6-point (`_INTERIOR_SEED`) window across each record; wherever it passes
the existing candidate test, it's greedily grown in both directions for
as long as growing keeps passing, then the search jumps past the found
run. Only the single largest run per record is trusted. Confirmed
correct on the known case: recovers `aCF3B.tmp`'s indices 49-81 (33
points).

**A second real limit found and fixed while verifying the new search
across the rest of the corpus, not left half-checked**: a previously-
unchecked `SI01040A17` object (`aE769.tmp`) has an identical hidden
plateau, but the interior search alone still found nothing there.
Traced to `SEAM_OFFSET_MAX`: this plateau's own offset is a rock-steady
2.756in, stdev < 1 - tighter than almost anything else confirmed in
this investigation, but rejected outright by the old 2in cap regardless
of stdev. Widened to 3in, comfortable margin above the confirmed need.

**Verified both fixes together via corpus-wide diff (191 blocks)**: zero
`check_line_table` results changed anywhere. Net corpus-wide recovery:
2920 of 7226 mismatched kind=2 points (40%), up from 27% before this
entry - a measured improvement, not just a fix for the two example
pieces. `aE78C.tmp` (the third piece in that same size-cluster family)
still shows zero recovery despite both fixes - flagged as a genuinely
open loose end, not assumed identical to its siblings.

`selftest.py` SELFTEST PASS; `dataset_test.py` 36/36; `robustness/
run.py` (full) 303/303. `FORMAT_SPEC.md` §11 updated with both fixes
and the corrected recovery numbers.

## v2.0 (2026-09-11, continued once more #25) - checked the remaining kind=2 records across the rest of the corpus: quantified how much the shipped checks recover, found a mechanical gap and 4 unchecked size tiers

User asked to check the remaining kind=2 records across the rest of the
corpus, rather than the handful of example pieces checked so far.

**Quantified recovery corpus-wide, not just spot-checked**: across every
embedded piece with a tail, 7226 kind=2 points still don't match `real`
directly; the corner-miter + polyline + segment-path checks now validate
1958 of them (27%), leaving 5268 genuinely unresolved.

**The unresolved majority splits into two distinct causes**:
1. Genuine multi-edge bulges (the already-characterized shape) -
   structurally correct to leave open.
2. **A mechanical gap in the shipped checks, not a geometric mystery**:
   `_curved_seam_trimmed_indices` only trims one point from each END of
   a record, modelling a corner miter - it doesn't search for a clean
   window buried in the INTERIOR of a large merged record. `aCF3B.tmp`'s
   own 103-point record has exactly this shape (a genuine plateau at
   indices 49-80 boundary-trimming can never reach), and it isn't alone:
   a previously-unchecked `SI01040A17` object (`aE769.tmp`) has an
   identical 123-point record hiding an 8-point plateau at stdev 0.39.
   Extending the trim to search an interior window is a concrete next
   step - not attempted this pass, since it's a meaningfully larger,
   riskier change (higher false-positive surface than trimming one
   boundary point) needing its own careful design and verification.

**Also found while running this survey**: the `SA60151TH`/`SI01040A17`
family has 11 distinct size-cluster objects per side, not the 7 the
earlier cup-size-correlation check was run against - 4 larger tiers at
the top of the range were never in the original inventory. The one
newly-checked example fits the established pattern rather than
contradicting it, but the full 11-tier correlation has not been re-run.

No code changed - pure investigation. `selftest.py` still passing.
`FORMAT_SPEC.md` §11 updated with the recovery numbers, the mechanical
gap, and the corrected size-tier count.

## v2.0 (2026-09-11, continued once more #24) - checked whether the smaller shifts could be caught too: tightened CURVED_SEAM_STDEV_MAX for a ~3x sensitivity improvement

User asked to check whether the 500/5000-unit shifts left undetected by
the previous entry's segment-path fix could be caught too.

**The segment-path check can't help here**: a shift of a few thousand
units stays within the same locally-coherent segment neighbourhood as
its genuine neighbours (checked directly - a 500-unit shift still
nearest-matches the expected segment), so `_seg_path_ok` was never going
to catch it; only the distance stdev moves for shifts this size.

**Tightened `CURVED_SEAM_STDEV_MAX` from 200 to 60 instead.** Gathering
every confirmed curved-seam stdev found across this whole investigation
(0.3-47.5 units, across six different pieces) showed the original
200-unit threshold had far more headroom than any genuine case actually
needed. A 500-unit (0.05in) shift on `BACK`'s own record 9 now shows
stdev 10.9 (still passes - genuinely indistinguishable from real
sub-tolerance variance), but a 3000-unit (0.3in) shift shows 64.5 and is
now correctly rejected - the old 200-unit threshold let anything under
~8000 units (0.8in) through, so this is roughly a 3x sensitivity
improvement.

**Verified via corpus-wide diff (191 blocks: 156 production + 35
small-corpus)**: zero `check_line_table` results changed anywhere -
every genuine confirmed match in the corpus stays comfortably under the
new threshold. Shifts below roughly 2500-3000 units remain genuinely
undetectable - not a gap a tighter threshold alone can close without
risking false rejection of real data, since the tightest confirmed
genuine match already measures 47.5.

`selftest.py` SELFTEST PASS; `dataset_test.py` 36/36; `robustness/
run.py` (full) 303/303. `FORMAT_SPEC.md` §11 and `CURVED_SEAM_STDEV_
MAX`'s own comment updated with the full stdev range and the tightening
rationale.

## v2.0 (2026-09-11, continued once more #23) - implemented the corner-miter check for BACK/FRONT's seam values, and found+fixed a real corruption-detection gap in the process

User asked to implement the corner-miter check for `AD1234 TEST 134`'s
`BACK`/`FRONT` seam values, flagged as a genuine possibility the
previous entry deliberately left unattempted.

**Added `_curved_seam_trimmed_indices`**: `check_line_table` now trims
at most one point from either end of a kind=2 record before testing for
a tight offset - a corner-miter boundary is structurally one point, not
a run. `BACK`'s 11-point record 9 now correctly validates its own 9
interior points at the genuine 3750-unit (0.375in) offset, stdev 0.3,
while its own first/last points (the transition values shared with
neighbouring records) stay correctly unresolved.

**Added a polyline candidate** (`_nearest_polyline`, point-to-segment
distance against the whole real perimeter as one closed curve, not just
individual `kind=1` edges) - needed because these records don't sit
parallel to any single stored edge, only to the perimeter as a whole,
the same reason the bra-cup family's own clean segments needed it.

**Found and fixed a real corruption-detection gap within this same
pass, not shipped blind**: deliberately corruption-testing the new
polyline candidate before trusting it found that a single point shifted
by 20000 units (2in) produced a *lower* stdev (1.7) than the genuine
data - completely undetected by distance alone, because the real
perimeter can have multiple roughly-parallel regions a corrupted point
coincidentally lands near. Fixed with `_seg_path_ok`: each point's own
nearest polyline segment must now move consistently in one direction
with no single step larger than a small bound - a real curve traces
adjacent segments in order (this fixture's genuine run steps by exactly
1 every time; `aCF3B.tmp`'s already-confirmed plateau steps by up to 4,
still one direction), and the 20000-unit corruption jumps against the
flow of its own neighbours, now rejected. Smaller, localized shifts
(500 and 5000 units, checked directly) still slip through - the same
coarse-tolerance limitation every seam check in this function already
has, not a new weakness this specific check introduced.

**Verified via corpus-wide diff (191 blocks: 156 production + 35
small-corpus)**: zero `check_line_table` results changed anywhere,
confirmed both before and after the corruption-detection fix - additive
at the per-point level, doesn't flip any fixture's own overall pass/
fail, same honest scope as every extension in this investigation.

`selftest.py` SELFTEST PASS; `dataset_test.py` 36/36; `robustness/
run.py` (full) 303/303. `FORMAT_SPEC.md` §11 updated with the fix and
the corruption-detection finding.

## v2.0 (2026-09-11, continued once more #22) - surveyed the rest of the corpus for more bridging chains: found two new, genuinely different manifestations of the same phenomenon

User asked to keep surveying the corpus for more bridging chains beyond
the `SA60151TH`/`SI01040A17` bra piece family.

**Inventoried every distinct piece name across every marker zip in the
repo.** `CLAUDE-GRADE-TEST` and `RUFFLE` already have `check_line_table()
== True` - nothing to chase. Two others do have mismatched kind=2
records, and both are genuinely new, distinct manifestations:

**`OUCF`** (a fold-half piece, 4 size-cluster objects, 8-9 perimeter
points - the small end of the corpus): the *same* clean+bulge shape as
the bra cups, just far smaller and strikingly size-invariant. All 4
objects land on the identical clean plateau (0.197in) and bulge peak
(0.237in) to the unit, and - unlike every bra-cup case - touch the real
perimeter (distance exactly 0) at *both* ends of the chain, not just
one. Consistent with a small, fixed-width construction detail (a facing
or binding) that doesn't scale with size, independent evidence for the
"real per-piece construction parameter" reading from the previous entry.

**`BACK`/`FRONT`** (`AD1234 TEST 134`, sizes XS-XL - a different garment
and order entirely): a different manifestation, not another bulging
curve. Their extra records sit at multiple discrete, exactly round
offsets - 10000, 3750, 2500 units (1.000in, 0.375in, 0.250in to the
unit, standard fractional seam-allowance widths) - each held essentially
constant across an 11-point run, connected by short records that
visibly transition between neighbouring values. Much closer in
character to the small corpus's own already-documented "uneven/tapered
seam" item (`CAP-C30-SEAM-UNEVEN`/`CAP-C31-SEAM-TAPER`) than to the bra
cup's smooth single bulge - multiple constant-but-different per-edge
seam values joined by corner miters, confirmed at production scale with
round, standard-width values. Checked directly, not assumed: even the
individually-clean 3750-unit run doesn't pass `_curved_seam_record_ok`
(its per-single-edge stdev is too high), meaning it isn't parallel to
any one stored edge either, same as the bra cup's own bridging segments.

**Net picture**: the "clean-offset-plus-transition" shape now shows up
on every real, non-trivial piece with a mismatched line table checked so
far, across three unrelated pieces/garments and several different
magnitude scales - strong evidence this is one systematic AccuMark
computation (a per-edge seam/facing allowance with corner miters,
generalizing the small corpus's own narrower "uneven seam" item), not a
decode artifact or coincidence specific to one piece family. Not fixed,
same reasoning as before: loosening the corruption-sensitive check to
accept these would risk accepting genuine corruption too.

No code changed - pure investigation. `selftest.py` still passing.
`FORMAT_SPEC.md` §11 updated with both new pieces' findings.

## v2.0 (2026-09-11, continued once more #21) - checked the other bulging chains (SI01040A17 lining side) for the same shape nuance: it holds, even more starkly, plus a striking SA/SI seam-allowance ratio

User asked to check the other bulging chains for the same shape nuance
found on the `SA60151TH` (shell) side.

**The nuance holds on the `SI01040A17` (lining) side too, even more
starkly.** `aCEFF.tmp` and `aCF15.tmp` (the 32B/32C-tier lining
counterparts of `aCF10.tmp`/`aCF26.tmp`, which showed a milder
"moderate uniform offset, no dip" version of the pattern) have **zero**
unmatched kind=2 records - `check_line_table()` returns **True** for
both, every one of their 10 kind=2 records captured as a genuine
`internal_lines` segment by the internal-line-list walker fix. Not a
milder version of the shape nuance, its complete absence - consistent
with these two smaller cup sizes' lining pieces genuinely not needing
whatever structural feature (wire channel, molding seam) produces the
bulge on larger sizes.

**A second, unplanned finding surfaced by checking the other 5 lining
pieces**: their clean-offset value is almost exactly **double** the
matching shell piece's - `aCEFC.tmp` 0.787in -> `aCEFD.tmp` 1.575in;
`aCF13.tmp` 0.787 -> `aCF12.tmp` 1.575; `aCF29.tmp` 0.787 -> `aCF28.tmp`
1.575; `aCF3E.tmp` 0.787 -> `aCF3D.tmp` 1.575 (four of five land on the
*identical* 1.575in, not just close); `aCF3B.tmp` 1.181 -> `aCF2B.tmp`
1.969 is the one imperfect case (1.67x). Landing exactly on the same
value for 4 of 5 pieces is a believable, real construction relationship
(lining seam allowance built to roughly double the shell's), not
coincidence.

No code changed - pure investigation. `selftest.py` still passing.
`FORMAT_SPEC.md` §11 updated with both findings.

## v2.0 (2026-09-11, continued once more #20) - checked whether the bulge magnitude correlates with cup size: it doesn't, but the split's own shape does

User asked to check whether the bulge's peak magnitude correlates with
cup size across the `SA60151TH` piece family.

**No measurable correlation.** Ordered all 7 size-cluster objects by
their own "sister size" cup-volume tier (32A < 32B < 32C < 32D < 32DD <
32E < 34E - the standard bra-sizing convention behind each piece's own
multi-label size list, e.g. `['36B','38A','32D','34C']` all sharing one
physical cup volume) and measured each piece's bulge peak the same way
as the earlier per-piece table: 2.593, 1.753, 2.540, 3.095, 1.898, 3.139,
2.519 in. **Pearson r = 0.277** against the tier ordering - weak, not
meaningfully different from no correlation at n=7.

**A different, genuine nuance found while gathering the data, not the
correlation itself**: `aCF10.tmp` (32B) and `aCF26.tmp` (32C) don't show
the sharp tight-offset/big-bulge split the other 5 pieces do at all -
their own extra curve sits at one moderately-elevated, gently-oscillating
distance the whole way (1.60-1.75in / 2.39-2.54in respectively), never
dipping to the ~0.79-1.18in baseline the other 5 pieces share. So the
picture isn't "5 clean+bulge, 2 exceptions" either - the *shape* changes
with size (two middle cup tiers show one moderate near-uniform offset;
the smallest tier and the three largest show the sharp two-regime split)
even though the bulge's own peak value doesn't correlate with size in any
simple way. Root cause of either pattern remains unidentified.

No code changed - pure investigation. `selftest.py` still passing.
`FORMAT_SPEC.md` §11 updated with the correlation result and the
aCF10/aCF26 nuance.

## v2.0 (2026-09-11, continued once more #19) - aCF3B.tmp checked for a different edge grouping: same clean+bulge split, just packaged as one merged record

User asked to check whether `aCF3B.tmp` (the one piece that didn't split
cleanly in the previous entry) splits with a different edge grouping.

**It does - the split was there all along, hidden inside one record.**
The previous pass only computed a single stdev for `aCF3B.tmp`'s whole
103-point closed-loop record 6 (2023 - looked uniformly bad) instead of
plotting its own per-point distance profile. Doing that finds a 32-point
plateau (indices 49-80) at a near-perfect constant 11811 units (1.181 in)
from `kind1` edge 0 - stdev **1.3**, the tightest of any clean segment
found in this whole investigation - with the record's other ~71 points
bulging up to 1.9 in away, the same shape as every other piece checked.

**Why it looked different**: topology, not a missing pattern. This
piece's own `kind1` edge decomposition merges what other pieces split
into several edges into one large 57-point edge 0 (edge sizes here are
`[57,2,32,13,2]`, not the more even 5-edge split other pieces have), and
AccuMark's own derived seam/cutline computation followed suit, emitting
one combined kind=2 record for the whole loop instead of one per
corner-to-corner transition.

**Net result: 7 of 7 pieces checked in this family now show the split**,
not 6 of 7 - `aCF3B.tmp` just required looking inside a single record
instead of across several separate ones. Root cause of the bulge itself
still unidentified, same as before.

No code changed - pure investigation. `selftest.py` still passing.
`FORMAT_SPEC.md` §11's comparison table and summary corrected from "6 of
7" to "7 of 7".

## v2.0 (2026-09-11, continued once more #18) - checked the other bridging chains: the clean-offset + bulge split reproduces across the whole piece family

User asked to check the other bridging chains too, beyond `aCEFC.tmp`'s
chain A.

**Confirmed the same split generalizes**, not a one-piece anecdote: every
piece checked in the `SA60151TH`/`SI01040A17` family splits into one
portion with a tight, near-constant perpendicular offset from the real
perimeter and another that bulges smoothly inward and back -

| piece | clean portion | stdev | bulging portion(s) |
|---|---|---|---|
| `aCEFC.tmp` | records 8+9, 0.79 in | 2.2-2.3 | records 6/7, peak 2.2-2.6 in |
| `aCF12.tmp` | record 10, 1.57 in | ~1 (polyline) | records 8/9, peak 3.0-3.9 in |
| `aCF13.tmp` | record 10, 0.79 in | 47.5 | records 8/9, mean 1.5-2.4 in |
| `aCF3E.tmp` | record 10, 0.79 in | 8.7 | records 8/9, mean 1.7-1.8 in |
| `aCF29.tmp` | records 9+10, 0.84-1.13 in | 151-861 | records 7/8, mean 1.6-2.5 in |

The clean portion's own offset magnitude *varies by piece* (0.79 in on
three, 1.13-1.57 in on two others) - a point in favour of this being real
per-piece design data (a chosen seam-allowance width) rather than an
artifact, since an artifact wouldn't plausibly track a believable,
piece-specific construction value. `aCF3B.tmp` doesn't split this cleanly
(one 103-point record, no separately-clean sub-portion found) - not
investigated further.

**Root cause of the bulge itself remains unidentified** - no DXF ground
truth or garment-construction domain expertise was available to name the
feature - but it is now an established, reproducible fact across at
least 6 of 7 pieces checked, not a single-piece oddity. No fix attempted
or warranted: `_curved_seam_record_ok`'s constant-offset test correctly
keeps rejecting the bulging portions.

No code changed - pure investigation. `selftest.py` still passing.
`FORMAT_SPEC.md` §11 updated with the full per-piece table.

## v2.0 (2026-09-11, continued once more #17) - checked chain A's own "bridges a corner" mystery: constant-offset hypothesis definitively ruled out, real shape characterized

User asked to check the remaining "chains bridge a corner" mystery on
`aCEFC.tmp`'s chain A (records 8/7/6/9), left open when the curved-seam
check was implemented.

**Ruled out the point-density explanation directly**: re-measured
records 6/7 against the *entire* real perimeter as a connected polyline
(point-to-line-segment distance, not just nearest stored point) rather
than assuming sparse points were hiding a real match. Same result as
before: not a constant offset by any measure.

**What the shape actually is**: record 6's distance from the perimeter
rises smoothly from 14019 to a peak of 25929 units (2.59 in) near its
midpoint, then falls back to 7077 at its far end; record 7 rises from
6777 to a peak of 21835 (2.18 in) and falls back to 14019 - exactly
matching record 6's own start, confirming the connection point rather
than coincidence. This is a smooth, coherent, closed curve - not noise,
not a mismatch - that runs close to the piece's own edge only near the
edge2/edge3 corner (where records 8/9's confirmed ~0.79 in offset sits)
and bulges inward by up to 2.6 in through the rest of its path.
Structurally consistent with a real, distinct construction feature (on
this bra cup piece, plausibly a molded-cup seam or underwire-channel
line) rather than a seam allowance at all - not confirmed as that
specifically, only ruled out as a constant offset.

**Deliberately not fixed, and correctly so**: `_curved_seam_record_ok`'s
constant-offset test correctly keeps rejecting this. Extending it to
accept a smoothly-varying offset would risk accepting genuine corruption
too - the same standing caution FORMAT_SPEC.md already documents around
loosening seam-tolerance checks (§10.1's uneven-seam item).

No code changed - pure investigation. `selftest.py` still passing.
`FORMAT_SPEC.md` §11/§12 updated; also corrected a stale note there that
still described the internal-feature-detection gap as "not yet fixed" -
it was fixed in the previous entry.

## v2.0 (2026-09-11, continued once more #16) - implemented the internal-line-list walker fix with the IMPORT stop

User asked to implement the fix the previous entry scoped: bridge the
real gap in `decode_piece_block`'s internal-line-list loop, stopping at
an Import Component boundary rather than crossing into it.

**Added**: `_next_internal_header(d, start, limit)` scans forward for the
next internal-line-list header, bounded by the first `IMPORT` marker (or
another `piece_record`'s own field block, `_looks_like_field_block`) at
or after `start`. `decode_piece_block`'s loop calls it whenever a list's
own label isn't immediately followed by another header, instead of
giving up. `aCEFC.tmp` now decodes all 6 of its real internal-line
segments (grain + 5 cutout), not 1.

**One bug found and fixed within this same pass, via a corpus-wide diff
rather than trusting the first version**: `_is_internal_header`'s own
4-byte test is loose enough that real production data can satisfy it by
coincidence - `aCF2B.tmp`'s own rule table did, and the first version of
`_next_internal_header` accepted it as a genuine 8th internal-line
segment (0 points, no real label after it), which broke that block's tail
parsing outright (coverage_pct 64.81% -> 52.89%, a real regression).
Fixed by requiring a candidate to walk cleanly through its own claimed
points AND produce a genuine trailing `Lnn` label before being trusted -
the same bar `decode_piece_block`'s own loop already requires for a
normal same-position continuation - not just the loose header pattern
alone.

**`_block_ranges()` updated alongside this, not left to drift**: the old
single `(pstart, block_end)` span assumed the perimeter and every
internal list sit back-to-back with nothing unaccounted for between them
- no longer true once a bridged gap can exist. Each internal list is now
marked individually, up to `decode_piece_block`'s own `internal_label_
end_offsets[i]` (the position right after that list's own terminator+
padding+label - genuinely parsed either way, whether the next list
continues immediately or only after a bridge), so a bridged gap stays
honestly `unknown` instead of being silently swallowed by one wide range.

**Verified safe across the full corpus**, not just the two example
pieces: 21 small-corpus fixtures + 2 `captures/` fixtures + 302 embedded
production objects, comparing `coverage()` output against the pre-fix
code. Zero `coverage_pct` decreases anywhere (confirmed only after fixing
the `aCF2B.tmp` false-positive bug above - the first version had several).
`check_line_table`'s and `check_region_c`'s own pass/fail results are
unchanged on every fixture that already passed.

`selftest.py` SELFTEST PASS; `dataset_test.py` 36/36; `robustness/run.py`
(full) 303/303. `FORMAT_SPEC.md` §11/§12 updated to mark this fixed
rather than "well-scoped, not yet implemented."

## v2.0 (2026-09-11, continued once more #15) - investigated the duplicate header block: it's an Import Component reference, not a stale duplicate or a missed block

User asked to investigate the second grain+cutout header sequence found
~12KB into `aCEFC.tmp`, past this block's own `tail_end`, that the
previous entry deliberately left unresolved.

**Resolved, not just narrowed down.** Two of the three original
hypotheses were ruled out directly: the second occurrence's own point
*coordinates* are entirely different from the first's (checked point-by-
point, not assumed - refutes "stale duplicate"), and `summarize()`'s own
brute-force scan (which visits every byte of the file) finds no second
metadata field block anywhere after `block_end` (refutes "undetected
second `piece_records` block").

**What it actually is**: 33 bytes past `tail_end` sits literal ASCII
`32AIMPORT11` - this piece's own base size immediately followed by the
word "IMPORT". Checked across the whole marker zip: the identical marker,
at the identical `tail_end + 33` offset, appears on **all 14**
`SA60151TH`/`SI01040A17` piece objects in this one marker, each tagged
with that specific piece's own base size (`32A`, `32B`, `32D`, `36D`,
`36C`, `38D` - matching one-for-one). This is a real, already-documented
AccuMark behavior from earlier in this project's history
(`MARKER_DECODE_PLAN.md`'s "Include Components" findings, previously seen
only in its *failure* mode on `LADIES-BLOUSE TEST-2`) - an Import
Component reference. What follows it is the imported component's own
grain/cutout internal-line data, structurally identical in shape to the
host piece's own section (same header format, same tag) but genuinely
different content, which is exactly why the coordinates don't match.

**Consequence for the fix flagged last entry**: extending
`decode_piece_block`'s internal-line-list walker to reach `aCEFC.tmp`'s
own missed cutout segments now has a well-defined stop condition (the
`IMPORT` marker, or a decoded field block) instead of an open question -
the earlier caution about conflating two copies was justified, and is now
resolved rather than just avoided. Still not implemented this pass:
identifying the boundary and safely walking past it are separate pieces
of work.

No code changed - pure investigation, docstrings/comments only.
`selftest.py` still passing. `FORMAT_SPEC.md` §11/§12 and
`_curved_seam_record_ok`'s own docstring updated.

## v2.0 (2026-09-11, continued once more #14) - checked the remaining kind=2 records for another pattern: they chain into continuous curves, one of which is a genuine internal feature the decoder currently misses

User asked to check the still-unmatched `kind=2` records (the ones
`_curved_seam_record_ok` correctly leaves failing) for another pattern,
rather than leaving them as an undifferentiated majority.

**Finding 1 - they chain together.** Consecutive kind=2 records share
exact endpoint coordinates: `aCEFC.tmp`'s records 12/13/14 close into one
104-point loop; records 8/7/6/9 close into a second, 73-point loop that
includes the two already-fixed records (8, 9) as two of its four
segments; `aCF12.tmp`'s records 8/9/10 form a third, open 73-point chain
the same way. A record that only matches a single perimeter edge cleanly
is a sub-segment of a longer curve that bridges across a corner - the
"confirmed subset" from the previous entry was never separate from the
unmatched majority, it's literally part of the same closed curves.

**Finding 2 - at least one chain is a real internal feature the decoder
never captures.** `aCEFC.tmp`'s 104-point loop has its own raw header in
the file: `ffff 4900 0024 0001 000000` (`INTERNAL_TAGS[0x49]` = `cutout`,
count 36) at byte offset 2931 - walked directly with `parse_point`, its
36 points are byte-for-byte identical, in order, to record 12's own
points. `decode_piece_block`'s internal-line-list loop never reaches it:
something occupies the bytes between the grain line's own chain (ending
~1524) and this header (2931) that isn't itself a recognised internal-
line header, so the loop correctly stops before getting there. This
piece's real internal-feature count is 4 (grain + 3 cutout segments), not
the 1 `internal_lines`/`internal_kinds` currently reports - a concrete,
byte-confirmed gap.

**Not fixed this pass**: a near-identical second copy of the exact same
grain+cutout header sequence exists again ~12,000 bytes further into the
same file (offset ~14039), well past this block's own `tail_end`
(12737) - a stale pre-edit duplicate, an undetected second
`piece_records` block, or something else isn't known. Extending the
internal-line-list walker without understanding this first risks
conflating the current copy with the stale one, so it's flagged as a
concrete, well-scoped next step rather than rushed.

**One correction to the previous entry's own numbers**, caught by
re-checking rather than reusing them: `aCF12.tmp`'s records 5/6/7 (also a
closed 3-segment loop) were miscounted among the "confirmed curved
subset" in the previous entry - they in fact already match `real`
exactly (they *are* `internal_lines`' own 3 correctly-decoded `cutout`
segments on that piece, `[2, 34, 34, 34]` points) and were never part of
the mismatch. A separately cited "record 13" match was a 2-point record -
excluded by `_curved_seam_record_ok`'s own `len(pts) >= 4` gate
regardless of its stdev, not a real second example. Both corrected here,
in `FORMAT_SPEC.md`, and in `_curved_seam_record_ok`'s own docstring/
comment.

No code changed - pure investigation, `selftest.py` still passing
(nothing touched). `FORMAT_SPEC.md` §11/§12 updated with both findings
and the correction.

## v2.0 (2026-09-11, continued once more #13) - implemented the curved seam-offset check for the confirmed subset

User asked to implement the curved-seam check the previous entry found
but deliberately left unshipped.

**Added `check_line_table._curved_seam_record_ok()`**: accepts a kind=2
record as a whole - never point-by-point - when every one of its points
sits within `SEAM_OFFSET_MAX` (2in) of the *same* `kind=1` perimeter edge
record with a tight, consistent standard deviation
(`CURVED_SEAM_STDEV_MAX = 200` units, comfortably above the confirmed
cases' 2-59 unit stdev and well below the ambiguous/unrelated records'
hundreds-to-thousands). Gated to records of at least 4 points, so a 1-2
point internal-line echo (a lone drill point, a 2-point grain line)
can't satisfy "consistency" by coincidence.

**One correction made along the way**: the confirmed curved-seam records
turned out to be **unnumbered** (`a == 65535`), not numbered like the
small rectangle corpus's mitered-corner seam points - they're edge-
interior offset points, not corner-derived. The fallback is scoped by
record size instead of the existing numbered/unnumbered split, which
would otherwise have excluded exactly the records this fix targets.

**Verified safe and correct, not just wider**: a corpus-wide diff against
the pre-fix code (156 production blocks, 35 small-corpus blocks) shows
**zero fixtures flip their overall `check_line_table` result** - every
piece with a genuine curved-seam record also has at least one other,
still-unexplained `kind=2` record, so the block as a whole correctly
keeps failing. What changed, confirmed directly: the specific targeted
records (`aCEFC.tmp`'s 8/9, `aCF12.tmp`'s 10/13) now validate for the
right reason instead of failing for a reason that was never about them.
Corruption sensitivity checked directly: shifting one confirmed record's
point by 5000 units (0.5in) breaks the fit and is correctly rejected (a
50-500 unit shift is not caught, comparable to the existing per-point
seam-offset check's own coarse tolerance - not a new category of
weakness). `robustness/run.py`'s full Oracle C suite (which already
exercises `2303-BD137-PLACED` specifically) stayed 303/303.

`selftest.py` SELFTEST PASS; `dataset_test.py` 36/36; `robustness/run.py`
(full) 303/303. `FORMAT_SPEC.md` §11/§12 updated to record the fix and
its honestly-scoped result (narrower than "these pieces now decode",
exactly "these specific records now validate correctly").

## v2.0 (2026-09-11, continued once more #12) - investigated the kind=2 multi-size mismatch hypothesis: refuted, replaced with a confirmed curved seam-allowance finding

User asked to investigate the "kind=2 records might store another
graded size's geometry" hypothesis the previous entry left open.

**Refuted, not just unconfirmed**: `2303-BD137-PLACED`'s `aCEFC.tmp`
(piece `SA60151TH`) has exactly one size (`32A`) in its own size table,
so `graded_outline()` to another size isn't possible from this object at
all - and its mismatched points don't match any of the zip's other
`SA60151TH`-named piece objects either (AccuMark splits this bra piece
across several independently-stored size-cluster objects; checked all
five others directly, zero point matches).

**What the points actually are, found by checking rather than continuing
to speculate**: plotting one mismatched `kind=2` record's points in order
shows a smooth, continuously-connected curve (small, consistent step
distances, one clear direction) - not corrupted data. Measuring every
`kind=2` record against its nearest point on each `kind=1` perimeter edge
record finds a subset with a near-perfectly constant offset: `aCEFC.tmp`
record 8 sits 7877 units (0.79 in) +/- 2 units from perimeter edge record
2, across all 23 points; a second, different production piece
(`SI01040A17`'s `aCF12.tmp`) shows the same shape at 1576-1581 units +/-
44-59. These are genuine seam-allowance/cut-line curves, at realistic
magnitudes well inside the existing `SEAM_OFFSET_MAX` (2 in) tolerance -
just far larger than the small `CAP-*`/`TASK2-SEAM1CM` test corpus's seam
values, and critically **curved** (the offset direction rotates
continuously along the edge) rather than the single axis-aligned/45°-
diagonal per-corner offset `check_line_table`'s `_is_seam_offset()` was
built and proven against. That function only accepts `dx==0 or dy==0 or
abs(dx)==abs(dy)`, so a curved perpendicular offset is rejected no matter
how small the actual distance is - explaining why `SEAM_OFFSET_MAX`
alone didn't already cover it.

**Not the whole story**: only a minority of `kind=2` records show this
clean a single-edge match (2 of 9 on `aCEFC.tmp`, 2-3 of 10 on
`aCF12.tmp`, both with 2-59 unit standard deviation); the rest match
their best edge far more loosely (hundreds to thousands of units stdev) -
likely compound/corner-spanning seams or a distinct, still-unidentified
feature. **Not fixed this pass**: generalising `_is_seam_offset` to
accept a curved, any-direction offset is a real, tractable next step for
the confirmed subset, but doing it safely needs a per-record consistency
requirement (not just a looser per-point distance check) to avoid
weakening Oracle C's corruption detection on these exact production
fixtures - and it wouldn't resolve the remaining majority anyway, so left
open rather than shipped half-solved. No code changed this pass, pure
investigation; `FORMAT_SPEC.md` §11 and §12 rewritten to replace the
retracted multi-size hypothesis with this evidence-based finding.

## v2.0 (2026-09-11, continued once more #11) - checked production 2303 pieces for the seam-fixture signature; found the "150/156 fail check_region_c" figure was mostly a different, now-fixed bug, and surfaced a bigger new one

User asked to check the production 2303 pieces for the same runaway
snapshot signature (`id=512, x=65536`) found on the three small-corpus
seam fixtures. Answer: only 18 of the 150 production blocks that fail
`check_region_c` actually show it. The other 132 were a separate,
unrelated bug this pass found and fixed.

**Root cause of the other 132**: `_locate_tail()`'s line-table search
used a fixed 0x600 (1536-byte) window after `block_end` - plenty for the
small `CAP-*`/`TASK*` corpus, but production pieces regularly need up to
8098 bytes before the real line table starts, so `tail` parsing (and
therefore Region B/C/D entirely) was failing outright on 132 of 156
production blocks (108 of 126 pieces' own primary record) before ever
reaching Region C. `check_region_c` was correctly reporting "fail" by its
own documented convention for "nothing to check," not because Region C
itself was corrupt - the earlier entry (#9/#10) had conflated the two.

**Fixed**: `_locate_tail` now searches to the end of the buffer instead of
a fixed window - same class of bug as the already-documented `decode()`
next-block-search fix (§8/§12), a window sized to the small hand-captured
corpus that silently broke at production scale. Confirmed the newly-found
location is correct, not a spurious match: every affected block's kind=1
(perimeter-edge) line-table records now match real geometry 100%.
`selftest.py` SELFTEST PASS (small corpus numbers unchanged, as expected -
the old window was never too small there); `dataset_test.py` 36/36;
`robustness/run.py` (full) 303/303.

**That fix immediately surfaced a third, separate, still-unexplained
problem**, found by checking rather than assuming the fix was a full
resolution: even with the line table correctly located, most production
blocks' `kind=2` records still don't coincide with the block's own
decoded geometry - individually well-formed points (unlike the runaway
bug), just describing something `real` doesn't contain, by large,
non-uniform deltas that don't fit the seam-offset shape. Unconfirmed
hypothesis: another graded size's geometry, since real production pieces
are multi-size and nothing this project's checks were built against is.
This is now the format's largest open item, well past the original
3-fixture seam-allowance footnote.

`FORMAT_SPEC.md` §11 and §12 rewritten to separate all three findings
(the genuine 18-block runaway bug, the now-fixed 132-block window bug,
and the new still-open kind=2/multi-size mismatch) instead of the
previous entry's conflated framing; `_locate_tail`'s docstring updated to
match, including retracting an unverified claim it originally shipped
with.

## v2.0 (2026-09-11, continued once more #10) - confirmed the other two small-corpus seam outliers share the exact same Region-C desync bug

User asked to check `CAP-C31-SEAM-TAPER` and `TASK2-SEAM1CM` (the other
two of the three small-corpus fixtures the previous entry's fix already
covered) for the same runaway-snapshot bug found on `CAP-C30-SEAM-UNEVEN`.
Confirmed directly rather than assumed: both desync at the identical
first point (`id=512, x=65536`) and cascade into the same kind of
impossible values, not a different failure mode - the only difference is
blast radius (631 and 335 garbage bytes respectively, vs. `CAP-C30-SEAM-
UNEVEN`'s 17,211), because `parse_point_snapshot` reads a fixed `n=4` on
these plain rectangles rather than running unbounded. Both fixtures'
`coverage()` output (95.35% and 94.99%) was already corrected by the
previous commit's fix, since the per-point real-geometry gate doesn't
depend on span size - no code change needed, this pass only confirmed and
documented it. `selftest.py` SELFTEST PASS (no code touched).
`FORMAT_SPEC.md` §11 gained a confirming paragraph.

## v2.0 (2026-09-11, continued once more #9) - audited section 12's gap list; found and fixed a real coverage() over-marking bug, much bigger in scope than it first looked

User asked to check that FORMAT_SPEC.md section 12's "remaining gaps" list
is fully up to date. Found three real issues, not just stale wording.

**Stale claim fixed**: section 12's bullet on `unclassified_gap` said
Region C's `n_perimeter` mismatches, `CAP-C61-MIRROR`'s virtual 4th
corner, "are now explained" - but §10.2 itself is titled "located, not
fully explained" (which of two equally-fitting derivations produced that
corner's value is still open) and §11 still calls the raw gap bytes
"not yet understood". Rewritten to separate what's actually resolved
(the `n_perimeter_a` count, the corner's *location*) from what remains
open (its derivation, and the gap bytes themselves).

**New, previously uncatalogued trailer field found**: a `u32 = 5`
immediately after one zero-padded `u32` right after the trailer's own
repeated timestamp pair (§7), before the `MSI` author-name echo. Confirmed
byte-identical on 20 of 21 `CAP-*`/`TASK*` fixtures (the one exception is
explained below, not a counter-example). Wired into `coverage()` as
`identified` (position+value known, role open - same basis as Region B's
own unnamed constants).

**Much bigger finding, while gathering evidence for the above**: checking
`CAP-C30-SEAM-UNEVEN`'s own unknown-byte runs turned up a snapshot2 "point"
with a computed `.size` of 17,211 bytes inside a 3,444-byte file - `_block_
ranges()` was marking Region C's snapshot ranges `identified` as soon as
they were computed, with no sanity check, so a desynced/runaway snapshot
(`parse_point`'s `f2` attr-byte-count field has no bound) got silently
counted as "understood." This alone had inflated `CAP-C30-SEAM-UNEVEN`'s
`coverage_pct` from an honest 94.69% to a reported 99.91% - which section
12, until this fix, cited as the corpus's *best* result. Checking the
production corpus (`markers/`, 156 piece blocks) for the same issue found
it's **not** limited to the 3 small-corpus seam outliers `check_region_c`
already documented as a known gap: **150 of 156 production blocks fail
`check_region_c`**, and on every one of them the same over-marking bug was
inflating `coverage_pct`, in the worst case observed by tens of thousands
of bytes (one snapshot point's `.size` computed as 50,505 - itself larger
than the 29,195-byte file it's inside). FORMAT_SPEC.md §11's "passes on
every fixture except three" claim did not hold at all for real production
data; corrected.

**Fixed properly**: `_block_ranges()` now takes the block's own real
geometry (`real`, the same set `check_region_c` builds) and marks each
snapshot's range - and the name-echo range downstream of where snapshot2
ends - only when every one of that snapshot's own points coincides with
real geometry. Verified by a corpus-wide diff against the pre-fix code:
only the fixtures `check_region_c` already flags bad show a coverage
*decrease* (the correct outcome - garbage no longer counted as identified);
every other fixture's `unknown_bytes` only decreases by one field (the new
trailer constant above). `selftest.py` SELFTEST PASS; `dataset_test.py`
36/36; `robustness/run.py` (full) 303/303 - none of this touches geometry,
grading, or notch decoding, only the informational coverage metric.

Section 12's corpus-wide coverage range corrected to **94.69-99.49%**
(worst case now honestly `CAP-C30-SEAM-UNEVEN`, not falsely its best
case); §11 rewritten with the corrected `check_region_c` pass-rate finding
and the coverage-marking bug fix; section 12 gained two new bullets (the
now-much-larger-in-scope Region-C desync gap, and the fix itself) plus the
new trailer-constant bullet.

## v2.0 (2026-09-11, continued once more #8) - §10.3's remaining notch-attribute-payload items checked

User asked to check the remaining §10.3 "Still open" items: the `07 2d`
notch-attribute payload's byte 0/byte 44 discrepancy, the table-point
struct's `b`/`c` fields, and the `0f 0a` triples.

**Table-point `c` resolved: a third independent copy of Notch Type.**
Every table point carrying a tag-`07` (notch attribute) child also has its
own `c` field set to the Notch Type number (1-30) - confirmed on all 10
notch-carrying table points in the corpus (`CAP-C40-NOTCH-TYPES`'s 4
distinct types 2/4/5/1, `CAP-C41`/`CAP-C42`'s 6 Type-1 notches). This
matters for the byte-44 question left open by a previous entry: on
`CAP-C40-NOTCH-TYPES`'s one disputed notch, the 45-byte payload's byte 0
and byte 44 disagree (5 vs 8) while the perimeter point's `f1` high byte
reads 5. `c` also reads 5, matching `f1`/byte0. With two of three
independent fields agreeing, byte 44 is the outlier, not a second
reliable copy as previously hypothesized - that hypothesis is retracted.
`why` byte 44 diverges (capture-time UI mis-click vs genuine distinct
semantics) remains open without a controlled re-capture.

**Fixed properly, not just documented**: `accumark_pds.check_line_table()`
now cross-checks `c` against the perimeter's own decoded Notch Type for
every notch-carrying table point, turning this from a passive observation
into a live consistency gate - verified to actually catch corruption by
flipping a `c` byte on `CAP-C40-NOTCH-TYPES` and confirming
`check_line_table` flips `True -> False`.

**`0f 0a` triples reverified, still genuinely open.** Re-scanned every
piece object in the corpus exhaustively (262 piece objects, matched by
object type rather than file extension so nothing is missed) for
non-placeholder `0f 0a` payloads: zero found, matching the existing
documented claim. A raw byte-level scan of the whole repo tree does turn
up a few `0f 0a` byte pairs inside the production marker files
(`2303-CP150-JULY`), but those sit inside an unrelated object type
(marker, type 9, not piece, type 20) with no TLV-tag meaning there - a
false lead, not a counterexample. No capture yet has a real one to decode
against.

`selftest.py` SELFTEST PASS; `dataset_test.py` 36/36; `robustness/run.py`
(full, not quick) 303/303. `FORMAT_SPEC.md` §10.2 (`b`/`c` field
description), §10.3 (all three "Still open" bullets), and its section-12
summary list of remaining gaps updated; `accumark_pds.check_line_table`'s
docstring updated with the full discovery writeup.

## v2.0 (2026-09-11, continued once more #7) - the CAP-C60-CUTOUT block_end=6 outlier: fully explained, now real decoded data

User asked to check the `CAP-C60-CUTOUT` `block_end`-value-6 outlier the
previous entry left open ("doesn't obviously track point count, list
count, or any other already-decoded field tried"). It was already
explained - in `accumark_pds._internal_list_label`'s own docstring, which
the previous investigation hadn't cross-referenced before writing up the
finding as open: the value is each internal list's own terminator, **3
for an open list, 6 for a closed loop**.

**Confirmed directly against geometry, not just correlation**, on all 30
corpus fixtures with an internal line: `CAP-C60-CUTOUT`'s 25-point cutout
has `points[0] == points[-1]` exactly (`(468585, 253862)` both ends) and
reads terminator 6; every other fixture's internal lines are open (first
!= last) and read 3. The one apparent counter-example,
`CAP-C50-DRILL1`'s single-point drill "list", trivially satisfies
`first == last` (one point equals itself) but reads 3 - correctly, since
a single point has no path to close; refining the rule to require >= 2
points makes it 30/30 consistent.

**Fixed properly rather than just documented**: this was previously
computed only as an internal parser validation gate
(`_internal_list_label` checks the terminator is 3 or 6 to recognise the
boundary at all) and then discarded - never exposed as decoded
information, and never wired into `coverage()`'s identified-marking
(explaining why it read as `unknown` in the first place).
`decode_piece_block` now returns `internal_closed` (a bool per internal
list, parallel to `internal_kinds`/`internal_labels`) computed from the
terminator value directly, plus `internal_terminator_offsets`;
`coverage()` marks every terminator's 4 bytes `identified` using them.
`robustness/canon.canon_decode` now includes `internal_closed`, closing a
real Oracle C gap - corrupting a closed-loop terminator byte was
previously invisible to any check; confirmed detected now by flipping
`CAP-C60-CUTOUT`'s own terminator and checking the canon changes.

`selftest.py` SELFTEST PASS; `robustness/run.py` still 303/303 (with the
new corruption case exercised, not just theoretically fixed);
`dataset_test.py` still 36/36. `FORMAT_SPEC.md` section 12 and
`_internal_list_label`'s own docstring updated.

## v2.0 (2026-09-11, continued once more #6) - checked FORMAT_SPEC.md section 12's remaining [?] items

User asked to check the still-open `[?]` items in section 12. Worked the
two concrete ones named there (the header-residue scalars at +0x60/+0x70-
+0x83, and the internal-line list's own terminator boundary) with the
same methodology used throughout this session: gather the bytes across
the whole corpus, test for reexport stability and cross-piece constancy,
correlate against already-known fields.

**Header residue (+0x60-+0x83): four fields resolved, one new gap
narrowed.**

- `+0x60` (u32) and `+0x7a` (u16) turned out to be the object-type fields
  `accumark_marker.read_object` already documents ("u32 copy at 0x60" /
  "u16 at 0x7a") - fully known, just never wired into `accumark_pds.
  coverage()`'s identified-marking. Same for `+0x7e` (u32), `read_object`'s
  own `plen` (payload length) field. All three now marked `identified`.
- `+0x78` (u16, `0x59ba`) and `+0x82` (u8, `0x90`) are **newly confirmed
  universal constants** - byte-identical across every corpus fixture
  checked, including the structurally-different `CAP-C63-MODEL` (a
  manifest format, not a real piece). Not residue (residue varies
  between exports; these never do, anywhere in the corpus). Marked
  `identified` on the same "known position + value, role still open"
  basis Region B's own unnamed constants already carry.
- `+0x70`-`+0x77` (8 bytes, pointer-shaped) is confirmed genuine
  **heap/stack residue** - byte-identical between `CAP-C00-BASE` and its
  2-minutes-later, unedited reexport `CAP-C01-REEXPORT` (same process
  instance), but differing across the corpus's several distinct capture
  sessions. A second instance of the same category already documented at
  the 3-byte noise floor (+0x48); now marked `residue` instead of
  `unknown` to match.
- Net result: `coverage()`'s identified rate rose on every fixture
  checked - e.g. `CAP-C00-BASE` 98.57% -> **99.35%**,
  `CAP-C30-SEAM-UNEVEN` 99.54% -> **99.88%**.

**Internal-line list terminator: narrowed, not closed.** A u32 sitting
exactly at `block_end` reads a constant `3` on 28 of 29 corpus fixtures
(every point count, every notch/seam/drill/cutout combination, 1- and
2-record pieces alike) - the one exception, `CAP-C60-CUTOUT`, reads `6`
and is also the one fixture with an unusually large internal-line list (a
25-point cutout loop, vs. 2-4 points everywhere else). The doubling
doesn't obviously track point count, list count, or any other already-
decoded field tried against it. Left open rather than force-fit - a real,
narrower, more precisely bounded mystery than "an unexplained scalar
near the terminator" was before.

**Confirmed purely additive - impossible to regress anything**: every
change in this pass adds `identified`/`residue` marks to bytes previously
`unknown`; none narrows or removes an existing mark. `selftest.py`
SELFTEST PASS; `robustness/run.py` still 303/303; `dataset_test.py` still
36/36. `FORMAT_SPEC.md` section 12 updated with the full writeup above.

## v2.0 (2026-09-11, continued once more #5) - the trailer field gap wasn't trailer content: a real decode() bug found and fixed

User asked to check the "trailer field gap" `FORMAT_SPEC.md` §12 listed as
unexplained ("a handful of small ints at the very start of the trailer...
none yet tied to a control or value in the UI").

**It wasn't trailer content on most of the corpus at all.** Gathered the
28 bytes right after every block's own line-table end (`tail_end`) across
every fixture and cross-referenced against known piece properties - the
same methodology already used elsewhere in this project to crack
`n_perimeter_a` and the seam-edge counts. Two distinct things were hiding
inside what looked like one mystery:

1. **A genuine, universal 8-byte constant** - `00 06 00 00 01 00 00 00` -
   confirmed byte-for-byte identical after every block's line table on
   every corpus fixture checked (single- or multi-record, 4- to 34-point,
   notched/seamed/plain). Its own meaning is still open, but it is now
   confirmed as a fixed marker, not per-piece data.
2. **A real bug in `accumark_pds.decode()`'s multi-block loop**, found by
   noticing that on 2-record pieces, what came right after that 8-byte
   marker looked nothing like trailer content - it was block 1's own
   metadata field block, which `decode()` was silently never finding.
   Root cause: the loop searched for the next block starting from the
   *previous* block's `block_end` (the pre-tail position, per
   `decode_piece_block`'s own docstring) with a fixed 288-byte window -
   never wide enough to reach past that block's own tail (pretable header
   + two Region-C snapshots + the line table, typically 700-1000+ bytes).
   So `decode()` has *always* silently stopped at block 0 on every multi-
   record piece in the corpus - undetected because `summarize()`'s
   separate, more expensive, independent brute-force byte scan (used
   everywhere `piece_records` actually matters: `verify_capture.facts`,
   `coverage()`) already found every block correctly, so nothing in the
   existing, passing test suite ever exercised `decode()`'s own multi-
   block completeness.

**Fixed**: the next block's search now anchors from the previous block's
`tail_end` (skipping past its tail rather than searching inside it) when
that tail parsed cleanly, falling back to `block_end` otherwise (unchanged
for the 2 production piece captures whose tail doesn't parse at all - a
separate, deeper, pre-existing gap, not touched here). Verified against
`summarize()`'s independently-computed block counts on all 28 parseable
corpus fixtures: `decode()` now finds exactly the same count everywhere a
tail parses.

**With that fixed, one more field resolved cleanly**: the *last* block's
own trailer-opening 20 bytes contain a u32 at a fixed +12 offset that
equals `n_blocks - 1` - 0 on every 1-record fixture, 1 on every 2-record
fixture, confirmed on all 26 non-outlier fixtures with a valid tail. This
is the first byte-level, fixed-position confirmation of `piece_records`
stored in the file itself, rather than only inferrable by brute-force
scanning. `CAP-C62-DART` isn't a counter-example - it's the same already-
documented 106-byte trailer insertion (its 2 extra dart points), which
shifts this whole region by exactly 106 bytes for that one fixture.

**Found and fixed along the way**: `dataset/templates.py` and
`dataset_test.py` both asserted `len(blocks) == 1` for generated pieces -
harmless before this fix (since `decode()` used to undercount anyway) but
now correctly fails on the two dataset templates that are genuinely
2-record pieces (`dart7`/`CAP-C62-DART`, `notch8`/`CAP-C40-NOTCH-TYPES`).
Both now accept any block count and always use block 0, matching the
"decode record 0, ignore the rest" convention `FORMAT_SPEC.md` section 8
already documents and every other caller in this codebase already follows.
`dataset/build.py` regenerated; every generated piece's actual bytes are
confirmed byte-identical to before (only zip-container metadata differs) -
this fix only changes how many blocks `decode()` *reports*, not which
bytes `retarget()` patches.

**Confirmed no coverage_pct/unknown_bytes change anywhere** (spot-checked
directly, since `coverage()` was already established to use `summarize()`'s
block list, never `decode()`'s) - this fix is purely additive to
`decode()`'s own completeness.

`FORMAT_SPEC.md` sections 8 and 12 updated to match. `selftest.py`
SELFTEST PASS. `robustness/run.py` still 303/303. `dataset_test.py` still
36/36 (against the regenerated dataset).

## v2.0 (2026-09-11, continued once more #4) - LADIES-BLOUSE decode failure investigated: not a bug, plus a real error-message fix found along the way

User asked to investigate why all 5 pieces in `LADIES-BLOUSE TEST-2.zip`
fail to decode (flagged, not chased, in the previous entry).

**Root cause: not a decoder bug - a known, already-documented AccuMark
export limitation, confirmed by this project's own prior-session capture
notes** (`MARKER_DECODE_PLAN.md`'s 2026-09-10 STATUS block): exporting this
marker hit the "Include Components silently drops pieces" limitation
already on record elsewhere in this project - "0 of 5 needed pieces came
through". Byte-level investigation confirms exactly that shape: each of
the 5 objects has a fully legitimate XGGT envelope and trailer (real
timestamps, the standard heap-residue pattern, correctly classified as
type 20 by `read_object`/`list_zip`) but **no valid metadata field block
anywhere in the payload** - `accumark_pds._find_field_block` was tried
across the entire file (not just `decode()`'s narrow default window) and
found nothing real; the one candidate a wider ad-hoc search turned up
(`LADIES-BLOUSE-COL` at offset 0x277) decodes to obvious garbage
(`len_size=1879047945`) confirming it's a false-positive coincidence, not
a genuine field block. Readable-looking fragments in the payload ("BACK",
"CUT1", "A1-LADIES") are real terminology but not stored in the standard
length-prefixed layout - consistent with a placeholder/stub object AccuMark
wrote when the referenced component couldn't be resolved at export time,
not a differently-encoded real piece. These are correctly-behaving
decoder refusals, not something to make succeed by force-fitting a parse.

**Found and fixed along the way**: `accumark_marker.load_pieces` had the
exact same unguarded-`blocks[0]` pattern `accumark_pds.summarize()` used to
have (fixed earlier in this v2 effort) - a piece that decodes with zero
blocks raised a bare `IndexError: list index out of range` instead of a
named error. `place_marker`'s existing `piece_errors` mechanism (previous
v2 fix) already caught and recorded it without crashing, but with an
unhelpful message. Now raises `DecodeError('no piece block found in object
payload (stub/placeholder object?)', source=<piece name>)`, matching
`summarize()`'s equivalent fix and giving all three affected entry points
(`decode()`, `summarize()`, `load_pieces()`/`place_marker()`) consistent,
correctly-scoped behaviour on this exact input shape.

`selftest.py` SELFTEST PASS; `robustness/run.py` still 303/303;
`dataset_test.py` still 36/36.

## v2.0 (2026-09-11, continued once more #3) - the whole corpus checked: 99 pieces, 2 explained regressions, 0 bugs

User asked to check the rest of the corpus. Extended the same worktree-diff
method to every remaining fixture: `captures/TASK1-5` + the 2 production
piece captures, and every remaining `markers/*` zip (`CLAUDE-GRADE-MARKER`,
`CLAUDE-QTY-TEST`, `COSTORDER`, `CAP-C21-SEC14`, `CLAUDE-GRADE-FCFW1`,
`CLAUDE-GRADE-REARR1`, `misc-test-markers/AD1234 TEST 134.zip`,
`misc-test-markers/LADIES-BLOUSE TEST-2.zip`). **99 pieces checked across
the entire corpus** (every `CAP-C*`/`captures/*`/`markers/*` zip in the
repo).

**One more real regression found, and it's the most dramatic evidence yet
that the Region-C fix matters**: `AD1234 TEST 134`'s `ID1005 - RUFFLE`
piece, 21 -> 38 unknown bytes. Root cause, precisely diagnosed: this piece
has `len(perimeter) = 142` (a ruffled/gathered edge with many small stored
points) but `n_perimeter_a = 4` (only 4 real corners). The pre-fix code,
using `len(perim)` for the snapshot count, read a **142-point snapshot2**
spanning bytes **4644 to 6774** - running straight through the rest of the
line table and into the trailer, incorrectly marking ~2130 bytes
"identified" that have nothing to do with any snapshot. The fix correctly
reads 4 points (2592-2652). Exactly the same root-cause pattern already
established for the 3 `CAP-C*` regressions and `TASK6-CURVE` (bytes
correctly reclassified from bug-inflated-identified to honest-unknown), at
a scale that makes unmistakably clear why the fix was necessary on real,
complex garment pieces, not just the small controlled probes.

No further code fix applies here (unlike the marker1/2/3 and
`unclassified_gap`-capture fixes in the two entries above): the freed
territory is a mix of already-fixed `unclassified_gap` bytes and genuine,
still-unexplained scattered trailer fields (FORMAT_SPEC.md already
documents this trailer-field gap generally) - nothing here has a
known value or bounded structure left to mark 'identified' without
overclaiming.

**Pre-existing, unrelated finding, not a regression**: all 5 pieces in
`LADIES-BLOUSE TEST-2.zip` fail to decode any block at all - on BOTH the
pre-fix and current code, identically (`decode()` returns zero blocks for
each). Zero delta, so explicitly not something this session's fixes caused
or could have caused; flagged here for visibility, not investigated
further (out of scope for a regression check).

**Final tally across the whole corpus**: 99 pieces checked, 0 regressions
unaccounted for, 2 fully-explained non-bug coverage decreases (both
documented above and in the two preceding changelog entries), 5 pieces
with a pre-existing, unrelated decode gap. `selftest.py` SELFTEST PASS;
`robustness/run.py` still 303/303; `dataset_test.py` still 36/36.

## v2.0 (2026-09-11, continued once more #2) - TASK6-CURVE and the 2303 production fixtures checked too

User asked to extend the same old-vs-new `coverage()` check to `TASK6-CURVE`
(the 34-point graded curve piece - not a `CAP-C*` fixture, so outside the
previous sweep) and the 2303 production marker zips' embedded pieces (the
only real, non-synthetic multi-piece corpus data: `2303-BD137-PLACED`,
`2303-BD137-UNLAID`, `2303-CP150-JULY` - 80 pieces total including the
`CAP-C*` set, extracted via `accumark_marker.list_zip`).

**2303 production pieces: zero regressions.** All 59 embedded pieces across
the three marker zips either improved or held steady; two pieces
(`2303-B1-INMO-2-SP24`, `2303-B1-INMO-4-SP24`, both appearing in all three
zips) jumped from ~75% to **99.9%+** coverage - the Region-C fix's benefit
scales to real, complex production geometry, not just the small controlled
`CAP-C*` probes.

**TASK6-CURVE: one real regression, fully explained, not a bug.**
25 -> 33 unknown bytes (99.54% -> 99.39%). Diffing the exact unknown byte-
runs (same method as the three `CAP-C*` regressions above) placed all 8 new
bytes inside `unclassified_gap` - the zero-padded region between Region C's
snapshot2 and the line table that `FORMAT_SPEC.md` already documents as
"not yet understood [?]". Confirmed by content, not just position: the new
bytes are the first ~20 of an 96-byte run (`5e 00...00 05 00 00 00 01...`)
byte-identical in shape to `TASK6-CURVE`'s own already-known, already-
captured `unclassified_gap` on its OTHER piece block. Same root cause as
the three `CAP-C*` regressions: the pre-fix bug's over-long snapshot2
accidentally swallowed some of this territory as "identified"; the fix
correctly stops at the real boundary, so these bytes now honestly read as
unknown. Unlike marker1/2/3 (fixed in the previous entry), there is no
known value to mark 'identified' here - the content genuinely isn't
understood yet, so leaving it 'unknown' is the correct, un-overclaiming
result, not a defect to paper over.

**Found and fixed along the way**: `parse_region_c` was silently dropping
`unclassified_gap` entirely (returning it empty, `d[p:p]`) whenever no name
echo was found - which turns out to be exactly `TASK6-CURVE`'s second
block (a stale pre-edit block, `decode_piece_block`'s own docstring already
anticipates these predate some feature and can lack an echo). The ~96
bytes of real, present file content in that gap were invisible to the
returned dict even though `coverage()` correctly treated them as unknown
either way. `parse_region_c` now accepts the caller's already-known
`table_start` and, when there's no name echo, bounds `unclassified_gap` by
it instead of discarding the region - a data-completeness fix (accurate
introspection for future investigation), not a coverage-classification
change: `coverage_pct` is unaffected (confirmed unchanged, 33/99.39%
before and after this specific fix).

`selftest.py` SELFTEST PASS; `robustness/run.py` still 303/303;
`dataset_test.py` still 36/36 throughout.

## v2.0 (2026-09-11, continued once more) - three coverage regressions found and fixed

User asked to check `unknown_bytes`/`coverage_pct` for regressions across
the Region-C fix, rather than trust the improvement at a glance. Compared
every `CAP-C*` fixture's `accumark_pds.coverage()` output byte-for-byte
between the pre-fix commit (`21ee87c`, checked out into a throwaway git
worktree) and the fix (`90c7e4d`) - not from memory of earlier terminal
output.

**Result: coverage improved on every fixture except three, which each
regressed by exactly +2 unknown bytes** (`CAP-C41-NOTCH-WIDTH` 40->42,
`CAP-C62-DART` 74->76, `CAP-C14-ANNOT` 25->27). Root cause, found by
diffing the exact unknown byte-runs before/after: `parse_region_c`'s three
marker fields between snapshot1 and snapshot2 (`marker1`, `marker2`,
`marker3` - see the Region-C fix entry below) were never explicitly marked
'identified' in `_block_ranges()` (`coverage()`'s byte-range accounting).
Before the fix, the buggy snapshot1 over-read on these three fixtures
happened to run far enough to swallow marker1's bytes as an accidental
side effect, so they read as "identified" purely by coincidence. The fix
correctly stops snapshot1 at its real end, so those marker bytes are no
longer accidentally covered - and since nothing explicitly claimed them,
they correctly fell to 'unknown'. Not a real defect in the fix itself (the
bytes were never legitimately "identified" to begin with, just
coincidentally swept up), but worth completing properly rather than
leaving as a regression.

**Fixed**: `parse_region_c` now also returns `marker1_offset`,
`marker2_offset`, `marker3_offset`/`marker3_size` (not just each marker's
value); `_block_ranges()` marks all three ranges 'identified' - the same
"identified but role unexplained" status already given to Region B's own
unnamed constants (FORMAT_SPEC.md's existing convention). Re-ran the same
old-vs-new comparison: **zero regressions, every fixture improved**, e.g.
`CAP-C00-BASE` 27->22 unknown bytes (98.25%->98.57%), `CAP-C30-SEAM-UNEVEN`
169->16 (95.09%->99.54%) - the coverage improvement from the Region-C fix
itself, now complete rather than partially offset by these three marker
gaps. `robustness/run.py` still 303/303; `dataset_test.py` still 36/36;
`selftest.py` SELFTEST PASS.

## v2.0 (2026-09-11, continued again) - the last Oracle-C gap closed: 303/303

The Region-C fix below left 9 Oracle-C cases behind, all on `CAP-C00-BASE` -
a piece with **no seam allowance at all**. Investigating found a second,
unrelated bug: `check_line_table`'s seam-offset leniency (`_is_seam_offset`,
+-`SEAM_OFFSET_MAX` = 2in) was being applied to **every** `kind=2` line-table
record, but `kind=2` is not specific to seam allowance - it is the line
table's echo record for **every internal line** (grain, drill, cutout), one
per segment, present on any piece that has one, seamed or not. Confirmed
point-for-point exact (no offset at all) on `CAP-C00-BASE`, `CAP-C10-PENT`,
`CAP-C50-DRILL1`, `CAP-C60-CUTOUT`, `CAP-C12-TWOINTLINES`. So a corrupted
echo point on a non-seam piece still landed "near" its own real, uncorrupted
point by sheer coincidence (sharing an X or Y axis with it) and was waved
through by the seam-miter tolerance meant for genuine cut-line records on
an actually-seamed piece.

**The fix**: internal-line echoes are structurally distinguishable from
genuine seam/cutline records by their points' own id field - every point in
an echo carries `a == 65535` (unnumbered, the id=-1 convention), while every
seam/cutline point in the corpus carries a real numbered corner id (no
fixture mixes the two within one record). The leniency now only applies to
points with a numbered id; an internal-line echo point must coincide
exactly with `real`, like every other checked point.

`robustness/run.py`'s Oracle C: 294/303 -> **303/303, all passing** - no
open corruption-detection gaps remain. `check_line_table`'s existing,
correctly-conservative `False` result on the three genuinely-uneven-seam
fixtures (`CAP-C30-SEAM-UNEVEN`, `CAP-C31-SEAM-TAPER`, `TASK2-SEAM1CM`) is
untouched - that is a real, documented, separate open item (the seam
corner's own miter math, not a leniency-scoping bug), not affected by this
fix. `selftest.py` SELFTEST PASS throughout; `dataset_test.py` unaffected
(this is a validation-logic fix, not a byte-parsing change - no generated
dataset file changed).

## v2.0 (2026-09-11, continued) - Region-C snapshot parser fix

`ROBUSTNESS_REPORT.md`'s Recommendations section originally flagged Region
C's two perimeter snapshots (`parse_region_c`/`parse_point_snapshot`) as
"parsed but not cross-validated" - Oracle C could corrupt a byte inside
what was labelled snapshot2 without the decode changing. Investigating
found the actual cause: **a real parser bug, not an unvalidated-but-correct
redundant copy.**

- `parse_point_snapshot` advanced by a hardcoded 15 bytes per point. Correct
  whenever every point re-encodes to exactly one f2 trailer byte (the usual
  case), but wrong on any piece where one point's real size differs -
  confirmed on `CAP-C62-DART`, where the parse silently misaligned partway
  through snapshot1 itself. Now advances by each point's own computed
  `size`, the same self-describing-record technique `parse_point_run`
  already used for the primary point table.
- `parse_region_c` read snapshot2 starting immediately after `marker2`.
  Byte-searching for `CAP-C00-BASE`'s and `CAP-C10-PENT`'s own known-real
  coordinates located snapshot2's true start precisely: there is one more
  2-byte tag (`marker3`, value 1 on every sample checked, role otherwise
  unknown) between `marker2` and snapshot2's first point that the old code
  was reading half of as if it were that point's own id/x field, offsetting
  every point after it by a few bytes for the rest of the snapshot. Fixed,
  with a defensive fallback to the old (pre-fix) reading if the corrected
  2-byte read doesn't land on plausible coordinates.
- The snapshot point count was `len(perim)` (the full stored perimeter,
  notches and dart-apex included). Region C's snapshots only re-list
  `n_perimeter_a` points - the same "corners minus notches/dart-apex" count
  `parse_pretable_header`'s own docstring already established for a
  different field - so a notched, darted, annotated or curved piece's
  snapshot reader ran past the snapshots' real end and started reading
  `marker1`'s own bytes as a bogus extra point.

**New:** `accumark_pds.check_region_c(b)` - the same point-coincidence
invariant `check_line_table` already applies to the line table, applied to
both Region-C snapshots. Surfaced as `region_c_consistent` in
`verify_capture.facts()`, and wired into `robustness/canon.canon_piece_full`
so Oracle C actually exercises it.

**Verified clean** (`region_c_consistent=yes`, snapshot geometry matches the
real perimeter exactly) on every corpus fixture except the same three
seam-allowanced pieces `check_line_table` already documents as a known,
separate gap (`CAP-C30-SEAM-UNEVEN`, `CAP-C31-SEAM-TAPER`,
`TASK2-SEAM1CM`) - not a new mystery, the same open one (uneven/tapered
seam corners aren't plain per-corner offsets) showing up in a second place.
`robustness/run.py`'s Oracle C: 249/303 -> 294/303. The remaining 9 failures
are a distinct, narrower, newly-surfaced finding - not Region C - documented
in `ROBUSTNESS_REPORT.md`'s Recommendations.

**On "no change to any v1 decode result" below**: still true for every fact
`selftest.py` asserts (perimeter, notches, area, grading, placements - the
v2.0 gate) - nothing there moved. What DID change, correctly: Region C's
previously-wrong snapshot2 content (and, on a few fixtures, part of
snapshot1) is now the real data, and `accumark_pds.coverage()`'s
`unknown_bytes`/`coverage_pct` improved on several fixtures accordingly
(e.g. `CAP-C30-SEAM-UNEVEN`: 169 unknown bytes / 95.09% -> 19 / 99.45%) -
bytes that used to be misclassified because the snapshot boundaries
themselves were wrong are now correctly attributed. `dataset/build.py`
regenerated: the drafted geometry (`dataset/MANIFEST.json`) is unchanged,
but `dataset/templates.coord_offsets` now correctly locates snapshot2's
bytes too (it previously missed them, the same bug this whole fix
addresses), so `dataset/write.retarget` patches ~20 more bytes per
generated piece than before - snapshot2 in every one of the 31 generated
pieces was, until this fix, silently left holding stale TEMPLATE
coordinates instead of the drafted panel's own. Caught by re-running
`dataset_test.py` (still 36/36 - the fix improves internal consistency,
it does not change any checked fact) rather than by inspection; worth
noting as a concrete example of why Oracle C's redundant-copy checking
matters even for output this project already treated as fully verified.

## v2.0 (2026-09-11)

`accumark_pds.__version__` / `accumark_marker.__version__` == `'2.0'`, asserted
by `selftest.py`.

**No change to any v1 decode result.** Every fixture `selftest.py` already
checked (piece captures, `CAP-C*` round-2 captures, marker fixtures) decodes
to byte-identical facts before and after this release - that equivalence is
the v2 acceptance gate, not a side effect. v2 is entirely additive: a new
exception taxonomy, ten input-handling defect fixes, and two new validation
suites that prove both.

### New: `accumark_errors` - a public exception taxonomy

```
AccuMarkError(ValueError)                # ValueError base: v1 `except ValueError` call sites keep working
 |- NotAnAccuMarkZip
 |   `- NestedArchive                    # zip has no AccuMark object at top level, but holds nested zip(s)
 |- ObjectError
 |   |- NotAnAccuMarkObject              # magic missing
 |   |- TruncatedObject                  # declared length exceeds bytes present
 |   `- WrongObjectType                  # object type is not the one requested
 |- NoSuchObject                         # no marker / no piece / no <kind> in the zip
 |- AmbiguousObject                      # duplicate members, or N candidates where 1 expected
 |- DecodeError                          # a block/section failed to parse
 `- NotADxf                              # a DXF reader was given a file with no DXF evidence
```

Every subclass carries `.source` (the zip path or member name) so a raised
error names what went wrong and where.

### Fixed (found by empirical probing this session, in memory, nothing
written to disk until the fix was verified)

1. **`accumark_marker.read_object`** - an object shorter than its own
   396-byte trailer used to return a plausible-looking dict where
   `d[-TRAILER:]` covered the whole short buffer, header included, instead
   of a real trailer region. Now raises `TruncatedObject`. (The
   initially-planned invariant `len(d) >= 0x80+plen+TRAILER` was checked
   against the real corpus and found **false** for genuine small objects
   like `lay_limits`/`annotation` - their payload and trailer regions
   legitimately overlap - so the shipped fix validates `len(d) >= TRAILER`
   instead, which is what the demonstrated truncation cases actually
   needed. Recorded here because it is the kind of correction only real-data
   testing catches.)
2. **`accumark_marker.list_zip`** - members are now read by position
   (`ZipInfo` from `infolist()`) instead of by name; two entries sharing a
   member name used to alias to the same bytes through `zipfile`'s
   name-to-info dict, silently losing one object's real content.
   `duplicate_member_names` reports collisions for diagnostics. A single
   corrupt/truncated member is now skipped and recorded in
   `object_errors` rather than aborting the whole listing (found while
   building `robustness/run.py`'s Oracle C - the old all-or-nothing
   behaviour meant one bad member made a caller lose every other object in
   the zip too).
3. **`accumark_pds.decode_zip` / `summarize_zip`** - select the candidate
   piece by magic (matching `list_zip`), not the first `.tmp` in
   zip-namelist order. On the 34-`.tmp` production marker, that first
   `.tmp` is a `lay_limits` object, so the old code's result depended on
   zip member ordering. Zero piece candidates now raises `NoSuchObject`
   (or `NestedArchive` if the zip contains a zip - previously a bare
   `IndexError` on every wrapper/nested zip in the corpus); more than one
   raises `AmbiguousObject` listing the candidates, with a new `member=`
   parameter to disambiguate.
4. **`accumark_marker.load_pieces` / `place_marker`** - a piece that fails
   to decode is now recorded in `piece_errors` instead of being reported
   downstream as the misleading "piece not in ZIP"; `verify_marker.facts`
   gains a `pieces_failed` fact.
5. **`accumark_pds.decode`** - block-loop failures are collected into
   `block_errors` instead of being silently discarded (the loop's normal
   termination path - `_find_field_block` raising when no further block
   exists - is unchanged).
6. **`accumark_pds.summarize`** - `blocks[0]` on a forged/corrupt object
   now raises `DecodeError` instead of a bare `IndexError`.
7. **`accumark_marker._section`** - the 42 section-directory offsets are
   validated against `len(d)` before use, raising `TruncatedObject`
   instead of a later bare `struct.error` deep inside `parse_slots`.
8. **`verify_capture.load`** - `SystemExit` replaced with
   `NotAnAccuMarkZip`/`NoSuchObject`, catchable by a library caller; the
   CLI's `main()` now catches `AccuMarkError` for the same
   stderr-and-exit-2 behaviour.
9. **`verify_marker.dxf_marker` / `verify_capture.dxf_outline`** - raise
   `NotADxf` when a file shows no DXF evidence (no `SECTION` group, no
   `$ACADVER`) instead of silently returning an empty-but-"successful"
   result indistinguishable from a real, empty drawing.

**Not changed:** the `u16`/`i16`/`i32`/`u32` byte accessors in
`accumark_pds` still return `0` past end-of-buffer rather than raising -
this is load-bearing for the deliberate fail-soft field-block scanning
documented at `accumark_pds.py:90-93` and `:425`. Fixes 1 and 7 remove the
ways a truncated buffer reaches those accessors with attacker-adjacent
(here: corruption-adjacent) intent; the accessors themselves are unchanged.

**v1 compatibility debt, noted for v3:** `AccuMarkError` subclasses
`ValueError` specifically so v1 `except ValueError` call sites did not need
to change for this release. A future major version could narrow that base
once callers have migrated to catching `AccuMarkError` directly.

### New: `dataset/` - a generated garment dataset

31 pattern pieces across five garments (A-line skirt, trouser, shirt,
blazer, dress), drafted from assumed size-12 body measurements onto seven
real corpus templates (4- through 8-point shapes, a 34-point curve, and a
9-size graded rectangle), by editing genuine AccuMark piece objects'
coordinate *values* in place - never their record structure. Every
generated piece is verified against its drafted ground truth
(`dataset/MANIFEST.json`) before being written: exact perimeter match,
matching area, matching notch positions, and (where the template carries
real, non-placeholder grading) a delta-invariance check across every
declared size. `python dataset/build.py` regenerates it deterministically;
`python dataset_test.py` re-verifies it.

Also one new marker (`GENERATED-SAMEBBOX-MARKER`: a real marker's embedded
piece reshaped to a different point arrangement inside the same bounding
box, with the marker's own area-bearing fields repatched to match) plus
four existing corpus markers reused for scale/edge-case coverage (up to 97
placements, an unplaced marker), clearly labelled by provenance in the
manifest. See `dataset/build.py`'s module docstring for why marker
*placement count* is not synthesized (it would require extending the
section-21 slot directory - a structural edit this project stays away
from) and for exactly which templates carry real vs. placeholder grading.

### New: `robustness/` - the three-oracle ZIP robustness suite

- **Oracle A** (metamorphic invariance): 21 structural ZIP transforms x
  4 seeds - all pass. Compression method, member order, folder nesting,
  path separators, extra/junk members, name casing/length/charset, missing
  optional members, archive comment, and timestamps all provably do not
  change the decode.
- **Oracle B** (controlled-failure contract): malformed/unusual inputs -
  empty files, truncated containers, zero-object zips, wrapper/nested
  zips, wrong-object-type zips, duplicate members, truncated objects -
  each raises a specific, declared exception, never `SystemExit`, a bare
  stdlib exception, or a silent wrong answer. All pass.
- **Oracle C** (corruption detection): mutates a byte the decoder's own
  parse proved carries a coordinate or slot value; the decoder must either
  raise or produce a different result. Confirms defects 1-9 above are
  fixed. Also surfaces a genuine, not-yet-resolved finding: perimeter
  coordinates are stored 5-7 times per point, and corrupting one of the
  *redundant* copies (not the authoritative point-table copy, which Oracle
  C does catch) is undetectable at the current fact level - see
  `ROBUSTNESS_REPORT.md`'s Recommendations section.

`python robustness/run.py` runs the full matrix and writes
`ROBUSTNESS_REPORT.md`; `--quick` runs a reduced matrix. `selftest.py` runs
the quick matrix on every invocation, gated on Oracles A/B (any failure
there is a regression) with Oracle C's known redundant-copy gap reported
informationally, the same way the existing coverage section is.
