# Nest spec - an unplaced AccuMark marker as a nesting job

```
python nest_spec.py "<marker>.zip" --json job.json [--dxf pieces.dxf] [--svg pieces.svg] [--units cm|mm|in] [--marker NAME] [--lay-limits NAME.GT_lay|other.zip]
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
| `source` | ZIP name, marker name, models, `laid_state` (`unlaid` / `partial`), `lay_history`, decoder version, `tables` (the names the marker stores: `lay_limits`, `annotation`, `block_buffer`, `notch_table`) |
| `fabric` | `width`; `fabric_types`; `block_buffer_in` (the buffer definitions in inches, side order unverified) ; `min_length` = total area / width (a 100%-efficient lay, **not** a nesting result) |
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
| `notches[]` | `x`, `y`, `type` (5 and 1 seen) |
| `grain` | `points` (2), `angle_deg` 0, `basis`: `stream` (read from a stream layout verified against piece objects) or `inferred` (the older 1825D / 5683D / 2591A / 418T vintage: a horizontal 2-point segment, 89 of 89 records - not a verified read) |
| `rotation` | only when the Lay Limits table is known: the row of this shape's `category` (else DEFAULT): `row`, `matched` (`category` / `default`), `allowed_deg`, `flip_x_axis_allowed`, ... and `basis` |
| `internal_lines[]`, `drills[]` | internal lines / cutouts and drill holes, `[]` when none (or when the layout is the older, undecoded one) |
| `outline_mirrored`, `seam_outline_mirrored`, `notches_mirrored`, `grain_mirrored`, `internal_lines_mirrored`, `drills_mirrored` | present when some instances are mirrored: the same geometry reflected about the grain axis through the middle of the box, written out so a nester needs no mirror convention |
| `self_intersecting` | `true` for a ruffle spiral (legitimate) |
| `complete` | `false` when the marker gave no outline for the shape |

## What it does NOT say

* **Positions.** An unlaid marker has none; the 0 / 180 degree pattern in it is a pre-set lay pattern.
* **Whether the fabric is one-way, unless the Lay Limits table is available.** The marker names its table but does not contain it (`lay_limits.source: named only`); the real production table `ALL GMT WAY` (2591A) is not in the corpus, so that spec says `assumed`. `NEED- TWO WAY` (1825D, 5683D) and `G-LAYLIMITS` (418T) are read from the user's support files: pass `all support files.zip` (or the `.GT_lay` files) as `--lay-limits` and those specs are `verified` (`MWS`: locked, every piece fixed in its preset direction).
* **Notch and drill sizes** (only positions and, for notches, a type code), **piece and fabric rules of a nester** (buffers between pieces beyond `padding`, matching, splicing).
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
