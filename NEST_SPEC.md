# Nest spec - an unplaced AccuMark marker as a nesting job

```
python nest_spec.py "<marker>.zip" --json job.json [--dxf pieces.dxf] [--svg pieces.svg] [--units cm|mm|in] [--marker NAME]
python accumark_marker.py "<marker>.zip" --nest-spec --json job.json          # same thing
```

Input: the ZIP AccuMark exports for a marker (Explorer > Export Zip). A **marker-only** ZIP is enough - no piece objects, no order, no AccuMark install.
Output: one spec per marker in the ZIP (`job.<marker>.json` when a ZIP holds several), each ending `NEST SPEC COMPLETE` or naming the check that failed.
Verified on the four real marker-only styles (1825D x2 markers, 5683D, 2591A, 418T), the two blind tests (CLAUDE-D3-BF, CLAUDE-D4), a twin of an order and the 2303 markers -
176 shapes / 243 pieces - and read back by an independent geometry library (shapely): every outline is a valid polygon of exactly the stated area.

## What is in it (`format: accumark-nest-spec/1`)

| key | meaning |
|---|---|
| `units` | `cm` (default), `mm` or `in` - every length and area below (area = units squared) |
| `source` | ZIP name, marker name, models, `laid_state` (`unlaid` / `partial`), `lay_history`, decoder version |
| `fabric` | `width`; `fabric_types`; `block_buffer_in` (the buffer definitions in inches, side order unverified) ; `min_length` = total area / width (a 100%-efficient lay, **not** a nesting result) |
| `rotation` | `allowed_deg: [0, 180]`, `basis: assumed` - the Lay Limits table is not stored in the marker, so one-way / two-way is NOT known; grain runs along x in every shape |
| `order_lines` | `model`, `size`, `quantity` as the marker's own order copy states them |
| `shapes[]` | one per (piece, size, cut) - see below |
| `demand[]` | `shape`, `quantity`, `mirrored`, `slots` (the marker's own slot numbers), `bundles`, `preset_rot180` (how many of them AccuMark had pre-set to 180 degrees: a lay pattern, not a constraint) |
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
| `internal_lines[]`, `drills[]` | internal lines / cutouts and drill holes, `[]` when none (or when the layout is the older, undecoded one) |
| `outline_mirrored`, `seam_outline_mirrored`, `notches_mirrored`, `grain_mirrored`, `internal_lines_mirrored`, `drills_mirrored` | present when some instances are mirrored: the same geometry reflected about the grain axis through the middle of the box, written out so a nester needs no mirror convention |
| `self_intersecting` | `true` for a ruffle spiral (legitimate) |
| `complete` | `false` when the marker gave no outline for the shape |

## What it does NOT say

* **Positions.** An unlaid marker has none; the 0 / 180 degree pattern in it is a pre-set lay pattern.
* **Whether the fabric is one-way.** Lay Limits are a separate AccuMark object; `rotation` is an assumption and says so.
* **Notch and drill sizes** (only positions and, for notches, a type code), **piece and fabric rules of a nester** (buffers between pieces beyond `padding`, matching, splicing).
* For the older marker vintage: internal lines, drills, seam lines and the mirror line of a fold piece (see `MARKER_FORMAT_SPEC.md`), and a *verified* grain (it is `inferred`).

## Checks (each a row in `checks`)

instances == the marker's unplaced slots; sum(area x quantity) == the marker's own area to lay (1%); every outline's area == the area AccuMark declares (1%);
every outline fits the stored box (never larger, at most 0.25 in of padding); outlines are counter-clockwise closed polygons; mirrored outlines have the same area;
the marker's own structural checks all pass; every instance has a shape with an outline.

`nest_spec.py` also writes a **DXF piece library** (one `CUT` polyline per shape and mirrored copy, `SEAM`, `INTERNAL`, `GRAIN`, `NOTCH`, `DRILL`, a label `S001 piece size xN`,
`$INSUNITS` set) and an **SVG** preview.
