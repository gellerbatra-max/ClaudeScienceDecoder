# Changelog

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
