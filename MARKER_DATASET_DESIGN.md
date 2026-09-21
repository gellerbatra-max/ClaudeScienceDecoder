# Controlled dataset for the unplaced-marker unknowns

Purpose: settle what is still open in the marker format by changing **one setting per
run** on a single AccuMark order and reading the marker AccuMark produces. Every run is a
new object named `CLAUDE-D2-*`; nothing the user owns is opened for writing.

## The harness (verified live, 2026-09-21)

1. Explorer, filter box `CLAUDE-D2*`. Select the base order, right-click > **Save As**
   > `CLAUDE-D2-GEN` (a copy; the base order is never edited).
2. Select the copy, ribbon **Easy Order** (opens the Advanced Order Form on the copy).
3. Step 4 - Fabrics: change **Marker Name** (click the cell, End, Shift+Home, Delete, type;
   widen the column to read it back). This is the marker's name. **Do not use Explorer's
   Generate Marker on a copy**: it targets the marker name stored in the order, finds the
   original marker and stops at "Confirm Marker Replace" (Cancel is safe, nothing is
   replaced).
4. Change exactly ONE factor (below), ribbon **Process**, "Save changes" Yes, wait for
   `CLAUDE-D2-GEN : Success`, close the editor (Yes, Yes).
5. Explorer: select the new marker, File > Export Zip (folder `C:\Test\CLAUDE-EXPORTS`),
   OK, OK, OK; click the folder in the tree to clear the selection. **Never Enter on a
   multi-selection** (see the CHANGELOG incident).
6. Decode offline: `python accumark_marker.py <zip> --inventory` and diff against the base
   run. A marker made this way is genuinely as generated (word 40 = 0, `@88` non-zero).

## Factors and what each settles

| id | factor changed (one per run) | hypothesis | readout | status |
|---|---|---|---|---|
| D0 | none: `AD1234 TEST 134` laid (kept from September) vs `CLAUDE-D2-M0` as generated, same order | laying changes only centre / orientation / `@88` / header doubles / type-10 growth | records identical, slot byte map | **DONE** - confirmed, `selftest` row |
| D1 | none: `CLAUDE-D2-M5`, the same order processed again 32 min later under another marker name | the harness is reproducible: only the name and stamps differ | byte diff vs D0 | **DONE** - 18 bytes (4 name digits + stamps), `selftest` row |
| E7a | add a second model whose pieces have NO fabric type in the order (`CLAUDE-GRADE-MODEL`) | the model is dropped, or its pieces appear | model list, order copy, slots | **DONE** - dropped from order and marker (`CLAUDE-D2-E7O`), `selftest` row |
| E7b | two models sharing fabric type M (`LADIES-BLOUSE` + `ZZ-PLM-BLOUSE`), 3 cuts | header @422 / @454 mode on a fresh marker | `header_sums` | **DONE** - `last_model` on both (`CLAUDE-D2-E7B`), `selftest` row |
| F1 | fabric width 134 -> 100 cm | only the width double (header `@396`) changes; no slot or record byte changes | section-1 diff | designed |
| F2 | quantities (2/4/4/2/1 -> 1/1/1/1/1) | section 15 quantity and size-table row count change together; records reused | order copy, size rows, slots | designed |
| F3 | Settings > **Single Size Markers** (Qty 1) | one marker per size; `@88` per (piece, size) for the SAME piece isolates the size dependence | `@88 - head count` constant = C | designed |
| F4 | order-level defaults: **Block Buffer**, **Lay Limits**, **Notch**, **Annotation** (Defaults dialog, Fabric Information) | block buffer changes section 6 (and only that) - settles what the table is for and the side order of its four doubles | section 6, home box | designed; the dialog edits persistent user defaults, so each change is reverted afterwards |
| F5 | what sets the piece-row flag u16 @+14. NOT a model-piece property (no model flag byte separates it, 450 pairs; the SAME LADIES-BLOUSE pieces read 0 in `CLAUDE-D2-E7B` and 1 in `ZZN-F1` / `TEST-2`) and NOT the block buffer (both values occur with and without one). Candidate: the ENGINE that wrote the marker - 0 on Marker Wizard / Easy Order / AccuPlan / imported 1825D-5683D-2303-BD137 markers, 1 on the ZZ-AM (AutoMark), ZZN, ZZC, 2303-CP 150, 418T, 2591A markers (circumstantial, from names) | run the same order through each engine: Process (done: 0), AutoMark job run to completion, Layrule, AccuNest | section 10 row, slot orientation | decode side DONE (`0x0040 == flag @+14`, 9,122 / 9,122 slots); origin open. `Process w/ AutoMark` only writes the SAME as-generated marker and opens the AutoMark Editor (a job scaffold, `CLAUDE-D2-M5` == `CLAUDE-D2-M0`); the job itself was not submitted |
| F6 | pieces of controlled topology built in Pattern Design: 0 / 1 / 2 / 4 internal lines, with / without notches, one curve | C in `@88 = head count + C` follows the internal points; `head count` follows the boundary points | record head words, `@88` | designed - needs new pieces, the heaviest run |

## What the runs so far settled (offline, over the whole corpus of 111 markers)

* `@88 = record head u16 @+10 + C(piece)`; C constant across sizes and markers (107 groups,
  0 exceptions). It is a count of the record's own entries, not a free signature.
* `0x0040 == piece-row flag u16 @+14` (9,122 / 9,122 slots).
* Laying an as-generated marker changes nothing in the records and only centre /
  orientation / area ulp / `@88` in the slots (D0).

## Still open after this round (each has a named run)

C's exact meaning (F6); what sets flag @+14 (F5); what the block-buffer table is for (F4);
`@52 / @54 / @60`; the y excess on the CP 150 unplaced slots; two placed slots 7.2% over
their record. (Closed by E7b: the two-model order's last-model header sums are AccuMark's own
behaviour at generation time.) F1-F3 were not run: they predict only fields already decoded.
