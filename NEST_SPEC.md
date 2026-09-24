# Nest spec - an unplaced AccuMark marker as a nesting job

```
python nest_spec.py "<marker>.zip" --json job.json [--dxf pieces.dxf] [--svg pieces.svg] [--units cm|mm|in] [--marker NAME] [--lay-limits NAME.GT_lay|other.zip] [--notch-table NAME.GT_notpt|other.zip] [--block-buffer NAME.GT_block|other.zip] [--as-job]
python accumark_marker.py "<marker>.zip" --nest-spec --json job.json          # same thing
```

Input: the ZIP AccuMark exports for a marker (Explorer > Export Zip). A **marker-only** ZIP is enough - no piece objects, no order, no AccuMark install. The one thing a
marker-only ZIP cannot give is the **Lay Limits table** (how pieces may be turned): the marker names it, the ZIP must bundle it (export with components) or you pass it
(`--lay-limits NAME.GT_lay`, a file from the storage area's `lay` folder, or another ZIP that holds it) - see *Lay limits* below.
Output: one spec per marker in the ZIP (`job.<marker>.json` when a ZIP holds several), each ending `NEST SPEC COMPLETE` or naming the check that failed.
Verified on the four real marker-only styles (1825D x2 markers, 5683D, 2591A, 418T), the two blind tests (CLAUDE-D3-BF, CLAUDE-D4), a twin of an order and the 2303 markers -
176 shapes / 243 pieces - and read back by an independent geometry library (shapely): every outline is a valid polygon of exactly the stated area.

## What is in it (`format: accumark-nest-spec/1`)

| key | meaning |
|---|---|
| `units` | `cm` (default), `mm` or `in` - every length and area below (area = units squared) |
| `source` | ZIP name, marker name, models, `laid_state` (`unlaid` / `partial`), `lay_history`, decoder version, `job_of_laid_marker` (`--as-job`: a LAID marker read as the whole job, positions ignored), `tables` (the names the marker stores: `lay_limits`, `annotation`, `block_buffer`, `notch_table`) |
| `fabric` | `width`; `fabric_types`; `block_buffer_in` (the marker's own buffer entries in inches, ordered Left, Right, Top / Bottom) ; `min_length` = total area / width (a 100%-efficient lay, **not** a nesting result) |
| `rotation` | the DEFAULT row of the Lay Limits table (`allowed_deg`, `flip_x_axis_allowed`, `locked`, `initial_orientation`, `tilt_limit`, `weft_skew_deg`, `buffer_rule`, `group`, `options`, `flags`) with `basis: verified: table NAME, row DEFAULT`; without the table `allowed_deg: [0, 180]`, `basis: assumed: ...` and a warning naming the missing table. Every shape of another category carries its own `rotation` |
| `lay_limits` | `name`, `source` (`bundled` / `supplied` / `named only` / `none`), `parsed`, `vintage`, `spread` (`single_ply` / `face_to_face` / `book_fold` / `tubular`), `bundling` (`all_bundle_same_direction` / `alternate_bundle_alternate_direction` / `same_size_same_direction`), `per_model`, `comment`, `rows[]` (one per category, each with the same fields as `rotation`), `bundle_pattern` (do the marker's stored bundle directions follow `bundling`?), `order_names` (what the bundled order says, when there is one) |
| `order_lines` | `model`, `size`, `quantity` as the marker's own order copy states them |
| `shapes[]` | one per (piece, size, cut) - see below |
| `demand[]` | `shape`, `quantity`, `mirrored`, `slots` (the marker's own slot numbers), `bundles`, `preset_rot180` (how many of them AccuMark had pre-set to 180 degrees), `preset_rot180_by_slot` (the same, one 0 / 1 per slot: the direction the bundle is retrieved in), `allowed_deg_by_slot` (per slot: the rotations the instance may take = `(180 x preset + allowed_deg) mod 360`: `[0]` or `[180]` for a one-way row, `[0, 180]` when 180 is allowed - see *Lay limits*) |
| `totals` | `instances`, `shapes`, `mirrored_instances`, `area`, `already_placed` (a part-laid marker lists only what is left), `outline_source` (`stream` = read from the marker itself) |
| `checks[]`, `complete` | every number a nester will trust, checked against numbers AccuMark stored itself; `complete` = all ok |
| `warnings[]` | anything unusual (the coverage of the byte map, an unparsed piece, ...) |

A **shape** has its own frame: the lower-left corner of its cut outline's bounding box is (0, 0) and x is the grain direction.

| key | meaning |
|---|---|
| `id`, `piece`, `model`, `size`, `cut`, `category`, `fabric_types` | identity |
| `outline` | the **cut line**: a closed polygon, counter-clockwise, no repeated last point |
| `seam_outline` | the stitch line, only when the marker holds one (a fold piece with seam allowance); it lies inside the cut line |
| `area`, `declared_area`, `perimeter`, `width`, `height` | `area` is computed from `outline`; `declared_area` is the number AccuMark stored - they agree to 1% (checked) |
| `stored_box`, `padding` | the box AccuMark stored for the piece and `stored_box - (width, height)`. `0` on every marker-only ZIP of the corpus; about 0.12 x 0.19 in on the July CP 150 markers (block buffer + curve allowance): **reserve that much around the piece** |
| `buffer` | only when the Lay Limits and the Block Buffer table are known: the rule this shape's row names - `rule`, `kind` (`buffer` / `block`), `static` and `dynamic` amounts per side (`left`, `top`, `right`, `bottom`, `segment`: `{value, unit}` in the spec units, or percent of the repeat) |
| `notches[]` | `x`, `y`, `type` = the NOTCH NUMBER: the row of the Notch Parameter Table the marker names - what it looks like is in `notch_table.entries[type]` |
| `grain` | `points` (2), `angle_deg` 0, `basis`: `stream` (read from a stream layout verified against piece objects) or `inferred` (the older 1825D / 5683D / 2591A / 418T vintage: a horizontal 2-point segment, 89 of 89 records - not a verified read) |
| `rotation` | only when the Lay Limits table is known: the row of this shape's `category` (else DEFAULT): `row`, `matched` (`category` / `default`), `allowed_deg`, `flip_x_axis_allowed`, ... and `basis` |
| `internal_lines[]`, `drills[]` | internal lines / cutouts and drill holes, `[]` when none (or when the layout is the older, undecoded one) |
| `outline_mirrored`, `seam_outline_mirrored`, `notches_mirrored`, `grain_mirrored`, `internal_lines_mirrored`, `drills_mirrored` | present when some instances are mirrored: the same geometry reflected about the grain axis through the middle of the box, written out so a nester needs no mirror convention |
| `self_intersecting` | `true` for a ruffle spiral (legitimate) |
| `complete` | `false` when the marker gave no outline for the shape |

## What it does NOT say

* **Positions.** An unlaid marker has none; the 0 / 180 degree pattern in it is a pre-set lay pattern.
* **Whether the fabric is one-way, unless the Lay Limits table is available.** The marker names its table but does not contain it (`lay_limits.source: named only`); the real production table `ALL GMT WAY` (2591A) is not in the corpus, so that spec says `assumed`. `NEED- TWO WAY` (1825D, 5683D) and `G-LAYLIMITS` (418T) are read from the user's support files: pass `all support files.zip` (or the `.GT_lay` files) as `--lay-limits` and those specs are `verified` (`MWS`: locked, every piece fixed in its preset direction).
* **Notch sizes, unless the Notch Parameter Table is available** (`notch_table.source: named only`: the spec has the notch number but not its shape), **drill sizes**, **piece and fabric rules of a nester** (buffers between pieces beyond `padding`, matching, splicing).
* For the older marker vintage: internal lines, drills, seam lines and the mirror line of a fold piece (see `MARKER_FORMAT_SPEC.md`), and a *verified* grain (it is `inferred`).

## Checks (each a row in `checks`)

instances == the marker's unplaced slots; sum(area x quantity) == the marker's own area to lay (1%); every outline's area == the area AccuMark declares (1%);
every outline fits the stored box (never larger, at most 0.25 in of padding); outlines are counter-clockwise closed polygons; mirrored outlines have the same area;
the marker's own structural checks all pass; every instance has a shape with an outline. When the Lay Limits table is known: it is read to its last byte (structure closes exactly), every shape has a rotation rule, and the marker's stored bundle directions agree with the table's Bundling (informational when there is nothing to compare).

`nest_spec.py` also writes a **DXF piece library** (one `CUT` polyline per shape and mirrored copy, `SEAM`, `INTERNAL`, `GRAIN`, `NOTCH`, `DRILL`, a label `S001 piece size xN`,
`$INSUNITS` set) and an **SVG** preview.

## Lay limits - what a row allows

The table is decoded from its bytes and checked against what the Lay Limits Editor itself shows (`laylimits/GROUND_TRUTH.json`, `MARKER_FORMAT_SPEC.md` section 16). A row is chosen by the piece's
`category` (case-insensitive), else the `DEFAULT` row. Meaning of the options (Gerber help, "Piece Options"; the W / no-reversed-pieces behaviour was also measured live in AccuNest
markers, `multi-fabric-oneway.md`: the `MW` markers had no reversed piece, the control with the blank default table had 12):

| options | `allowed_deg` | `flip_x_axis_allowed` |
|---|---|---|
| blank | `[0, 180]` | yes |
| `W` (one way) | `[0]` | yes |
| `S` | `[0, 180]` | no |
| `W` + `S` | `[0]`, `locked: true` | no |
| `9` adds `90, 270`; `4` adds every 45 degree step (`45, 90, 135, ...`: a reading of "allows 45 degree rotation", the 90s follow from two 45s) | | |

`flip_x_axis_allowed` is a *permission* to reflect the piece about the grain axis (`outline_mirrored` is that reflection); the demand's `mirrored` count still says which instances are mirror images.
`M O N X P U Z F` are reported as `flags` (major, optional, not plotted, not cut, pair orientation kept, area not counted, may lie inside a splice mark, folds allowed) - a nester that
does not care can ignore them. `buffer_rule` is the number of the row in the Block Buffer table the order names; `tilt_limit` is `{unit: 'length' | 'degrees', cw, ccw}` (a length is in inches, whatever
`units` the spec uses); `weft_skew_deg` is the knit skew; `group` is the Group column (meaning not documented by Gerber).

**Open (stated, not guessed):**

* `allowed_deg` is measured from the orientation the piece is *retrieved* in. With `Alternate Bundle, Alternate Direction` (or `Same Size, Same Direction`) the marker stores 180 degrees on every
  other bundle (`preset_rot180_by_slot`). **Measured (AccuNest, `laylimits/EXPERIMENT_W_ALTERNATE.md`):** the four FRONT pieces of `ZZC-M1` (`MW`, alternating bundles) came out two forward and two reversed,
  exactly as preset - a `W` piece is fixed in the direction its bundle was retrieved in, hence `allowed_deg_by_slot`. Not measured: that a row allowing 180 lets the engine turn a piece *against* its preset
  (none did in that small draft nest). The presets themselves are proved to follow the table's Bundling (29 markers, `bundle_pattern`).
* `initial_orientation` (the flip code, e.g. 7 = rotate 90 CW) is not stored in the marker's slots (the SLEEVE pieces of `ZZC-M1`, flip code 7, carry only the 0 / 180 preset bits), so the spec cannot say
  whether the piece outlines already include it; treat it as information.
* Older-vintage tables (the user's real `L`, `SINGLE-PLY`) are read for a single row only; their tilt and skew bytes are zero in every sample and reported only when they are.

## Notches - what a notch number is

A notch on a shape is a NOTCH NUMBER (`type`). The marker names a Notch Parameter Table (`source.tables.notch_table`, e.g. `P-NOTCH`, `NEED-P-NOTCH`); the table is bundled when the ZIP is exported with its
components, or passed as `--notch-table NAME.GT_notpt` (from the storage area's `notpt` folder) or another ZIP. Then `notch_table.entries` maps each defined number to
`kind` (`slit`, `t`, `v`, `castle`, `left_check`, `right_check`, `u`, `no_lift_slit`), `perimeter_width` (the gap at the piece edge), `inside_width` (the width at the bottom) and `depth`
(spec units; positive = cut into the piece, negative = sticking out, `direction` says which), and `numbers_used` lists the numbers the shapes carry. Without the table `notch_table.source` is
`named only` and a warning says so. Verified in the Notch editor and against a real plot (every notch spike of a nested `ZZC-M1` is exactly the table's 0.40 cm depth); `MARKER_FORMAT_SPEC.md` section 18.
The real 1825D / 5683D notch (number 1) is a 0.50 cm slit; the default `P-NOTCH` defines notch 1 as a 0.40 cm slit; `V-NOTCH-ALL CUSTOMERS` (2303) is 25 external Vs, perimeter 0.30 cm, depth -0.20 cm.
The DXF / SVG piece libraries still draw a notch as a point.

## Reference consumer - `reference_nester.py`

`python reference_nester.py job.json [--res 0.15] [--best] [--svg lay.svg] [--dxf lay.dxf] [--out lay.json]` is a nesting engine that reads **only** the spec JSON (numpy, Pillow, shapely; no marker, no ZIP,
no decoder). It takes the fabric width, every instance (`shapes[].outline`, or `outline_mirrored` for mirrored instances), the rotations each instance may take (`demand[].allowed_deg_by_slot`) and the gap
(`--gap`, else the block buffer), rasterises the pieces, and places them largest first with an FFT search for the position with the smallest right edge. It is a bottom-left heuristic - built to be *valid*,
not to compete with AccuNest - and its lay is checked independently with shapely (inside the fabric, no overlap, every rotation allowed, every instance laid): the last line is `VALID` or `INVALID`.

`--as-job` on `nest_spec.py` reads a LAID marker as the whole job (positions ignored), so any lay AccuMark made becomes a benchmark. Results (fabric widths and AccuMark's own numbers from the markers):

| job | pieces | AccuMark's lay | reference nester (`--res 0.2`) |
|---|---|---|---|
| 2303-BD 137 (bra cups), laid by AccuMark | 97 | 377.7 cm, 71.5% | 371.5 cm, 72.7% - valid |
| AD1234 TEST 134 (laid marker as a job) | 13 | 47.0 cm, 55.7% | 56.8 cm, 45.9% - valid |
| ZZC-M1, nested by my own AccuNest run (Draft) | 18 | 249.8 cm, 79.7% | 353.7 cm, 55.1% (`--best`: 332.4 cm, 58.7%) - valid |
| real 1825D / 5683D / 418T / 2591A (unlaid) | 27 / 24 / 22 / 35 | - | 68.8 cm 63.6% / 47.3 cm 65.0% / 503.8 cm 62.8% / 135.1 cm 69.9% - all valid |

The proof that matters is validity, not length: every job comes out `VALID` - the rotations follow the Lay Limits (the real `MWS` tables fix each 1825D / 5683D / 418T instance in its preset direction), mirrored
instances use `outline_mirrored`, nothing overlaps. And the other direction: AccuMark's own 2303 lay, rebuilt from the *spec's* shapes with the placed marker's positions and flags, has no overlap (worst 0.0003 in2),
stays inside the 137 cm fabric and reproduces the marker's utilisation (71.51%) - so the shapes, mirror convention and areas in the spec are the ones AccuMark laid.

## Block / buffer - the space around a piece

The marker names a Block Buffer table (`source.tables.block_buffer`, e.g. `3MM`); a Lay Limits row names a rule of it by number (`buffer_rule`). With both tables (bundled, or `--lay-limits` / `--block-buffer`)
the spec's `block_buffer.rules` gives every rule its kind and its amounts (Left / Top / Right / Bottom / Segment, static and dynamic) and each shape's `buffer` is the rule of its category. The real `3MM`
rule 1 is a Buffer of 0.15 cm per side: two pieces end 0.3 cm apart. Static amounts apply when the order is processed; dynamic ones may be added or removed while marking. A buffer is invisible space around the
piece (keeps the cutter blade off the neighbour), a block a visible zone. `block_buffer.marker_entries` compares the marker's own section-6 entries with the table (`equal` / `different`); a nester that wants one
number for the gap between pieces can use `fabric.block_buffer_in` (what `reference_nester.py` does: twice the largest side), one that wants per-shape space uses `shapes[].buffer`.
