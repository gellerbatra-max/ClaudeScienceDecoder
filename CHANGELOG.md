# Changelog

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
