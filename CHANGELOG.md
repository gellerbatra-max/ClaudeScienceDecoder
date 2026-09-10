# Changelog

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
