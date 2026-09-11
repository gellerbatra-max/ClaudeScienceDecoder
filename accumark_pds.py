
"""accumark_pds.py - decoder for Gerber AccuMark native piece files
(the .tmp member inside an AccuMark 'XGGT IXPORT DB5.1' export ZIP),
plus a parser for the companion ASTM/D6673 .RUL grade-rule table.
Reverse-engineered from a controlled A/B export set; see FORMAT_SPEC.md.

v2 (see CHANGELOG.md): malformed/unusual ZIP input now raises a specific
accumark_errors.AccuMarkError subclass (a ValueError, so v1 `except
ValueError` call sites are unaffected) instead of a bare IndexError,
struct.error or a plausible-looking wrong answer. Every v1 decode result is
unchanged byte-for-byte; selftest.py is the gate that proves it.
"""
import io, re, struct, zipfile
from accumark_errors import (AccuMarkError, NotAnAccuMarkZip, NestedArchive,
    NotAnAccuMarkObject, TruncatedObject, WrongObjectType, NoSuchObject,
    AmbiguousObject, DecodeError)

__version__ = '2.0'
MAGIC = b'XGGT IXPORT DB5.'
UNITS_PER_INCH = 10000.0          # coordinates are int32 in 1e-4 inch

def u16(d,o): return int.from_bytes(d[o:o+2],'little')
def i16(d,o): return int.from_bytes(d[o:o+2],'little',signed=True)
def i32(d,o): return int.from_bytes(d[o:o+4],'little',signed=True)
def u32(d,o): return int.from_bytes(d[o:o+4],'little')

# ---------------------------------------------------------------- metadata
def _find_field_block(d, start=0x60, stop=0x140):
    """The 22-byte field block sits immediately before the concatenated
    metadata strings.  Anchor on 'len_name bytes later there is an ASCII
    run of exactly that length followed by more ASCII'."""
    for o in range(start, stop):
        n = u16(d,o)
        if not 3 <= n <= 64: continue
        s = d[o+22:o+22+n]
        if len(s)==n and all(32<=c<127 for c in s) and all(32<=c<127 for c in d[o+22+n:o+22+n+3]):
            return o
    raise ValueError('metadata field block not found')

def parse_metadata(d, off=None):
    o = _find_field_block(d) if off is None else off
    f = dict(field_off=o)
    f['len_name']    = u16(d,o)
    f['len_annot']   = u16(d,o+2)
    # [V] CAP-C61-MIRROR: this u16 is 0 in every other capture (so reading
    # len_annot as an i32 happened to work by coincidence), but is 2 here -
    # the only capture made with the "Fold Keep" tool (internal fold line + Mirror Piece checkbox). Likely a mirror/flip flag
    # or a count of mirror-related sub-records; meaning unconfirmed.
    f['unk_u16_annot'] = u16(d,o+4)
    f['len_size']    = i32(d,o+6)
    f['len_ruletab'] = i32(d,o+10)
    f['n_perimeter'] = i32(d,o+14)
    f['unk_u16_a']   = u16(d,o+18)
    f['len_sample']  = u16(d,o+20)
    p = o+22
    def take(n):
        nonlocal p
        s = d[p:p+n].decode('latin1'); p += n; return s
    f['name']        = take(f['len_name'])
    f['annotation']  = take(f['len_annot'])
    f['rule_table']  = take(f['len_ruletab'])
    f['size']        = take(f['len_size'])
    f['sample_size'] = take(f['len_sample'])
    f['reserved4']   = d[p:p+4].hex(); p += 4
    f['n_sizes']   = u16(d,p)
    f['unk_u16_b'] = u16(d,p+2)
    f['n_break_rows'] = f['unk_u16_b'] + 1      # size-break rows in the rule table
    f['base_index']= u16(d,p+4)
    f['unk_u16_c'] = u16(d,p+6)
    f['n_obj_rec'] = u16(d,p+8)
    p += 10
    # a false-positive field-block candidate (summarize()'s offset scan) can
    # hand this a garbage n_sizes of up to 65535; each such candidate then
    # built a 65k-entry list - 23,580 candidates on one production piece
    # made summarize() take 58 s. Real tables have a few dozen sizes at most.
    if f['n_sizes'] > 64:
        raise ValueError('implausible n_sizes %d - not a field block' % f['n_sizes'])
    sizes = []
    for _ in range(f['n_sizes']):
        ln, fl = u16(d,p), u16(d,p+2)
        sizes.append(dict(name=d[p+4:p+4+ln].decode('latin1'), flag=fl))
        p += 4+ln
    f['sizes'] = sizes
    f['end'] = p
    return f

# ------------------------------------------ object records = grade rules
def object_record_size(n_rows):
    """i32 id, i32 reserved(0), then one (dx, dy) int32 pair per size-break
    row of the rule table, 1e-4 inch, truncated.  Round 1's five-row tables
    made every record 48 bytes; CAP-RULES-A's eight rows make them 72."""
    return 8 + 8*n_rows

def parse_object_records(d, start, n, n_rows=5):
    recs = []
    size = object_record_size(n_rows)
    # [V] a real file's object-record array always fits before EOF; a
    # false-positive metadata match during summarize()'s brute-force offset
    # scan can hand this garbage n/n_rows (u16s, so up to 65535 each) with no
    # exception anywhere downstream (i32()/u16() silently zero-fill past the
    # buffer) - unbounded, this built a ~400M-element list and hung for
    # minutes on a single bogus candidate (CAP-C62-DART, n=14385,
    # n_rows=13874). Fail fast so the caller's except-and-skip logic works.
    if start + size*n > len(d):
        raise ValueError('object record array would run past EOF - not a real piece block')
    for k in range(n):
        o = start + size*k
        payload = [i32(d,o+4+4*j) for j in range(1+2*n_rows)]
        recs.append(dict(offset=o, id=i32(d,o), payload=payload, reserved=payload[0],
                         deltas=[(payload[1+2*j], payload[2+2*j]) for j in range(n_rows)]))
    return recs

# internal point lists after the perimeter: term(u16) tag(u16) count(u16) flag(u32)
INTERNAL_TAGS = {0x47: 'grain', 0x44: 'drill', 0x49: 'cutout'}
# 0x0000/0x47 grain line, 0xFFFF/0x44 drill points. 0xFFFF/0x49 was first seen
# on a closed circle (CAP-C60-CUTOUT, "cut-out") and the name stuck, but
# CAP-C12-TWOINTLINES [V] shows it's really just "generic user-drawn internal
# line/curve" - a second, plain 2-point open line (Create -> Line -> 2-Point)
# gets the *same* 0x49 tag, not a fourth kind. What actually distinguishes
# the circle from the line is the terminator below (6 vs 3), confirmed by
# this second sample rather than inferred from one. `cutout` is kept as the
# dict/field name for continuity with earlier docs and selftest.py, but reads
# as "kind of drawn internal line," not "is a closed cut-out."
# CAP-C60-CUTOUT itself: a circle drawn fully inside the piece with "Create
# New Piece" unchecked, tessellated into a closed N-point polygon - the last
# point repeats the first exactly. The DXF exporter re-tessellates it again
# at roughly double the point count for display (layers 8 and 85 in that
# capture: 25 and 49 points of the same circle) - the *binary* point count
# (25) is the one that matches this list's own `count` field, not either
# DXF layer number by coincidence.

def _internal_list_label(d, o):
    """After a list's points: a u32 terminator, zero padding, then the 3-byte
    'Lnn' label that names the list just read.  Returns (label, offset past
    the label) or (None, o).  Terminator is 3 for an open list - grain,
    drill, and (CAP-C12-TWOINTLINES [V]) a plain 2-point internal line, all
    tag 0x49 or not - and 6 for a closed loop (CAP-C60-CUTOUT's circle,
    also tag 0x49). The terminator, not the tag, is what signals open vs
    closed [V, corrected 2026-09-11] - confirmed on all 30 corpus fixtures
    with an internal line, directly against the stored geometry (the
    list's first and last point coincide iff the terminator is 6; the one
    apparent exception, CAP-C50-DRILL1's single-point drill "list", reads 3
    despite trivially satisfying first==last, correctly - one point has no
    path to close). decode_piece_block computes and exposes this per list
    as `internal_closed`, from the terminator value directly rather than
    re-deriving it from geometry here - see its own comment."""
    if o+4 > len(d) or i32(d,o) not in (3, 6): return None, o
    p = o+4
    while p < len(d) and d[p] == 0: p += 1
    if p+3 <= len(d) and d[p:p+1] == b'L' and d[p+1:p+3].isdigit():
        return d[p:p+3].decode(), p+3
    return None, o

def _is_internal_header(d, o):
    return o+10 <= len(d) and u16(d,o) in (0, 0xFFFF) and u16(d,o+2) in INTERNAL_TAGS

# ---------------------------------------------------------- point sequences
COORD_LO, COORD_HI = -2_000_000, 2_000_000   # plausible coordinate window
POINT_TURN, POINT_CURVE, POINT_DART_APEX = 0x09, 0x0A, 0x12

def parse_point(d, o):
    """id(i16) x(i32) y(i32) f1(u16) f2(u16)
       [+ rule_ref(i32) pad(u16)  when f1 == 0]
       [+ f2 trailer bytes        when f2 >= 1]"""
    r = dict(offset=o, id=i16(d,o), x=i32(d,o+2), y=i32(d,o+6),
             f1=u16(d,o+10), f2=u16(d,o+12), rule_ref=None, attr=None)
    p = o+14
    # [V] the rule_ref/pad group follows whenever f1's LOW byte is 0, not only
    # when f1 == 0: a numbered corner that also carries a notch has
    # f1 = 0x0100 (notch type in the high byte, as for unnumbered notches)
    # and still carries its rule reference (2303-B1-40E-OUWG-SP24, point 11,
    # rule 10005). Testing f1 == 0 misaligned the run by 6 bytes there and
    # turned the rest of the perimeter into garbage on 8 of 162 production
    # pieces.
    if (r['f1'] & 0xFF) == 0:
        r['rule_ref'] = i32(d,p); r['rule_pad'] = u16(d,p+4); p += 6
    # [V] CAP-C62-DART: f2 is a trailer BYTE COUNT, not a 0/1 flag - a dart
    # leg point has f2==2 (two trailer bytes, e.g. `09 10`/`09 11` for the
    # dart's two legs: same first byte 0x09 as an ordinary turn point, second
    # byte differs between the two legs of one dart - [?] pairing/index,
    # unconfirmed). Every prior sample only ever had f2 in {0,1}, so this was
    # indistinguishable from a plain boolean until now; treating it as a
    # count is backward compatible (f2==1 still reads exactly one byte).
    # Without this fix parse_point_run silently misaligns by 2 bytes on the
    # first dart leg and every following perimeter point decodes as garbage.
    r['attr_bytes'] = None
    if r['f2'] >= 1:
        r['attr_bytes'] = d[p:p+r['f2']]; r['attr'] = r['attr_bytes'][0]; p += r['f2']
    r['size'] = p-o
    # A notch is an unnumbered point (id == -1) whose f1 low byte is 1 AND
    # high byte is nonzero; the high byte is the PDS "Notch Type" number
    # (1..30) chosen in the Add Standard Notch panel [V]
    # (CAP-C40-NOTCH-TYPES: observed 0x0101, 0x0201, 0x0401, 0x0501 for UI
    # types 1, 2, 4 and a fourth placement). The old bit-8-only check
    # (r['f1']>>8 & 1) happened to work only for odd type numbers and
    # silently missed types 2 and 4. The high-byte-nonzero requirement
    # excludes plain unnumbered points (grain-line/drill f1 = 0x0001, high
    # byte 0) from being misread as notches.
    r['is_notch'] = r['id'] == -1 and (r['f1'] & 0xFF) == 1 and (r['f1'] >> 8) != 0
    # a numbered corner point can carry a notch too (f1 high byte = type,
    # low byte 0, rule_ref present) - reported separately so the perimeter
    # point count and the notch count both stay right [V] 2303 wing pieces
    r['is_corner_notch'] = r['id'] != -1 and (r['f1'] & 0xFF) == 0 and (r['f1'] >> 8) != 0
    r['notch_type'] = (r['f1'] >> 8) if (r['is_notch'] or r['is_corner_notch']) else None
    # dart_leg: f2==2 identifies the point structurally regardless of its
    # first attr byte (which reuses 0x09, the ordinary turn-point value) -
    # check this before the attr-byte-based curve/turn checks below [V]
    r['is_dart_leg'] = r['id'] == -1 and r['f2'] == 2 and not r['is_notch']
    r['kind'] = ('notch' if r['is_notch'] else
                 'dart_leg' if r['is_dart_leg'] else
                 'dart_apex' if r['attr'] == POINT_DART_APEX else
                 'curve' if r['attr'] == POINT_CURVE else
                 'turn'  if r['attr'] == POINT_TURN else 'plain')
    return r

def parse_point_run(d, start, n):
    pts = []; o = start
    for _ in range(n):
        if o+14 > len(d): break
        # [V] CAP-C61-MIRROR: metadata's n_perimeter over-counts by one - only
        # 3 of the declared 4 perimeter points are explicit point records,
        # even though the DXF confirms a true 4-corner rectangle. The 4th
        # corner is presumably implied by the mirror axis rather than stored
        # (unconfirmed - only one Fold Keep sample so far). Stop before
        # misreading the next internal-line header (grain/drill/cutout) as a
        # garbage point instead of trusting the declared count blindly.
        if pts and _is_internal_header(d, o): break
        r = parse_point(d,o); pts.append(r); o = r['size']+o
    return pts, o

def find_point_table(d, after, window=64):
    # [V] production pieces (2303 style, 2026-09): the perimeter starts at
    # whatever creation-order id happens to come first (13, 2, 7 ...), never
    # only 1/-1, and the table begins exactly at the end of the object
    # records. Scanning for id 1/-1 skipped real corner points silently
    # (42A-OUWG read 24 of 27) or landed mid-record (17 of 162 pieces garbage).
    pid = i16(d, after)
    if (pid == -1 or 1 <= pid <= 4096) and COORD_LO < i32(d,after+2) < COORD_HI \
       and COORD_LO < i32(d,after+6) < COORD_HI and u16(d,after+10) in (0,1,2,0x101):
        return after
    for o in range(after, min(after+window, len(d)-14)):
        pid = i16(d,o)
        if pid in (1,-1) and COORD_LO < i32(d,o+2) < COORD_HI and COORD_LO < i32(d,o+6) < COORD_HI \
           and u16(d,o+10) in (0,1,2,0x101):
            return o
    raise ValueError('point table not found after %#x' % after)

# ------------------------------------------------- pretable + line table (TLV)
# [V] round-2 tail-section analysis. Layout after the last `Lnn` line-record
# label (decode_piece_block's `block_end` stops one step short of this, at
# the label's own u32 terminator, to stay backward compatible - see
# `_locate_tail` below, which re-finds the label independently):
#
#   Region B - PRETABLE_HEADER_SIZE=52 fixed bytes, `parse_pretable_header()`.
#   Region C - two full re-listings of the perimeter, `parse_point_run`
#              format (15-byte "turn" points regardless of the point's real
#              kind), bracketed by two `10 27 00 00` (10000) markers. The
#              first copy starts at whichever point comes right after point 1
#              (i.e. point 2), the second starts at point 1 - both are the
#              same cyclic perimeter order, just rotated. `parse_point_snapshot()`.
#   Region D - the line table: one `parse_line_table()` record per perimeter
#              edge and per internal line (grain/drill/cutout), in creation
#              order. Every field is a self-describing (tag u8, len u8,
#              payload) TLV *except* tag 0x10, whose length byte is always 0
#              but which really carries a fixed 16-byte `parse_table_point()`
#              struct, itself followed by that point's own `e` child TLVs
#              (0x06 point-name marker, 0x07 notch attribute block, 0x04
#              graded-rule tag, 0x0f unexplained triple on a graded point).
#
# Confirmed by direct byte-offset matching against known perimeter
# coordinates (CAP-C10-PENT) and by mechanically walking a full line-table
# record end-to-end onto the next record's `0a 00` header with zero manual
# offset adjustment (CAP-C42-NOTCH-ALLEDGES) - see FORMAT_SPEC.md for the
# worked examples. `n_perimeter`-scaling fields confirmed across C00/C10/C11
# (4/5/6 points); the collar piece CAP-C14-ANNOT's pretable header reads a
# smaller count than its actual perimeter-point total - unconfirmed why,
# left as [?] rather than forced to fit.
PRETABLE_HEADER_SIZE = 52
SNAPSHOT_MARKER = 10000            # the two `10 27 00 00` bracketing markers

def _locate_tail(d, block_end, search_window=None):
    """Re-find the position right after the block's *last* `Lnn` label
    (Region B's start) and the line table's first record header, independent
    of decode_piece_block's own `block_end` (which stops one step short of
    the label, for backward compatibility with existing callers).

    [V, found and fixed 2026-09-11] `search_window` used to default to a
    fixed 0x600 (1536) bytes - fine for the small CAP-*/TASK* corpus (whose
    largest real gap is nowhere near that), but on real production pieces
    the gap between block_end and the line table's own first record scales
    with piece complexity (Region A's per-edge Lnn records, then Region B/
    C) and regularly exceeds it: found while investigating why
    check_region_c() was failing on so much of the production corpus - 132
    of 156 embedded production piece blocks (108 of 126 pieces' own primary
    record) turned out to have no `tail` at all, not a Region-C-specific
    problem, because this search was silently giving up before ever
    reaching the real line table (observed gaps up to 8098 bytes on
    `2303-BD137-PLACED`'s own pieces - more than 5x the old window). Same
    class of bug as the already-fixed decode() next-block search (FORMAT_
    SPEC.md SS8/SS12) - a fixed window sized to the small hand-captured
    corpus, silently wrong at production scale. Now searches to the end of
    the buffer by default; `search_window` stays available for a caller
    that wants to bound the cost.

    The match location itself is confirmed correct, not spurious: every
    previously-failing block's newly-found line table's kind=1 (perimeter-
    edge) records match the block's own real geometry point-for-point,
    100%, everywhere checked. What this fix does NOT resolve - found
    immediately after fixing it, genuinely open, not yet understood -
    is that most of these same blocks' kind=2 records still fail
    check_line_table(): their points are well-formed (sane ids, sane
    sizes, no runaway) but simply don't coincide with the block's own
    perimeter/internal-line/closing geometry, by large (thousands of
    units), non-uniform deltas that don't fit the already-documented
    seam-offset shape. Real production pieces are genuinely multi-size
    graded, unlike the small single-size test corpus this checker was
    built and proven against - one live hypothesis is that some kind=2
    records store another size's geometry rather than the decoded block's
    own, but that is unconfirmed. See FORMAT_SPEC.md SS11/SS12."""
    end = len(d) if search_window is None else min(block_end+search_window, len(d))
    tm = re.search(rb'\x0a\x00[\x01-\x40]\x00\x00\x00[\x01\x02]\x00[\x01-\x40]\x00\x03\x00', d[block_end:end])
    if not tm: raise ValueError('line table not found after block_end %#x' % block_end)
    table_start = block_end + tm.start()
    labels = [m.start() for m in re.finditer(rb'L[0-9][0-9]', d[block_end:table_start])]
    if not labels: raise ValueError('no Lnn label between block_end and line table')
    pretable_start = block_end + labels[-1] + 3
    return pretable_start, table_start

def parse_pretable_header(d, o):
    """Region B: 52 fixed bytes.

    [V] `n_perimeter_a`/`n_perimeter_b` (appears twice) is NOT simply
    len(perimeter): confirmed by formula across the whole corpus (only
    exception: CAP-C61-MIRROR, explained below) to be the count of
    perimeter points that carry an attr byte at all (`f2 >= 1` - this
    alone excludes notches, which always have f2 == 0) and whose attr is
    not POINT_DART_APEX - i.e. every "real" turn/curve corner, minus a
    dart's own apex point (its two leg points still count). This resolved
    three previously-separate open items at once: CAP-C14-ANNOT's collar
    piece has one plain corner with f2 == 0 (so n reads 4 for its 5 real
    points), CAP-C62-DART's apex is the one dart point excluded (n=6 of 7),
    and CAP-C40/41/42's notches were already excluded by the f2==0 test
    alone. CAP-C61-MIRROR is the sole exception (formula predicts 3, file
    reads 4) - consistent with, not contradicting, the rule: see
    check_line_table()'s docstring and FORMAT_SPEC.md §10.2/§11 for the
    virtual 4th corner this piece's line table (but not its own perimeter
    list) references, which both this field and metadata's own
    `n_perimeter` (§2) count as if it were a real point.

    [V] `n_seamed_edges`/`n_uneven_seamed_edges` (u16 at +14/+20, previously
    logged as "constant 0" - true only because no sample had a seam yet):
    confirmed exactly against `verify_capture.py`'s own seam decoding on
    every seam-carrying sample - `n_seamed_edges` is the number of Lnn
    segments with `seam_flag == 1` (== `cutline_records`), and
    `n_uneven_seamed_edges` counts just the ones where `seam_begin !=
    seam_end` (0 on TASK2-SEAM1CM's uniform 1 cm seam; equal to
    `n_seamed_edges` on CAP-C30/C31, where every seamed edge is
    tapered/uneven).

    Every other field (`magic`, `one`, `c1..c5`) is a raw constant in every
    sample in the corpus - confirmed invariant, but not named, since their
    ROLE (as opposed to their value) is still unknown [?]."""
    r = dict(offset=o,
             magic=u16(d,o), one=u32(d,o+2), n_perimeter_a=u32(d,o+6),
             c1=u32(d,o+10), n_seamed_edges=u16(d,o+14), c2=u32(d,o+16),
             n_uneven_seamed_edges=u16(d,o+20),
             c3=u32(d,o+22), c4=u32(d,o+26), n_perimeter_b=u16(d,o+30),
             c5=u32(d,o+32), n_lines_plus_1=u32(d,o+48))
    r['size'] = PRETABLE_HEADER_SIZE
    return r

def parse_point_snapshot(d, o, n):
    """One of Region C's two full perimeter re-listings: n consecutive
    parse_point-format records (a flattened geometry copy, not the
    authoritative point list). [V, corrected] earlier read these with a
    fixed 15-byte stride, which happens to be right whenever every point in
    the snapshot carries exactly one f2 trailer byte (the common case), but
    silently misaligned the whole rest of the snapshot on any piece where
    one point's re-encoded size differs (confirmed on CAP-C62-DART: byte-
    search for the piece's own known-real coordinates showed 2 of 7
    snapshot1 points mismatching downstream of the first size-21 record).
    Advances by each point's own computed `size`, the same self-describing-
    record technique parse_point_run already uses for the primary point
    table - not a fixed stride."""
    pts, p = [], o
    for _ in range(n):
        r = parse_point(d, p); pts.append(r); p = r['offset'] + r['size']
    return pts, p

def parse_region_c(d, o, n_perimeter, category_name, table_start=None):
    """Region C: snapshot1, a SNAPSHOT_MARKER pair around a zero gap, a
    third tag - **a single u16, value 1 on every sample checked so far
    (CAP-C00-BASE, CAP-C10-PENT [V]; not the same width as marker1/marker2,
    role unknown - kept and reported as `marker3` rather than silently
    skipped)** - then snapshot2, then - immediately before the line table -
    a **second, undelimited copy of the piece's own category name**
    (CAP-C10-PENT [V]: the 12-byte string 'CAP-C10-PENT' sits right at the
    line table's doorstep, with no length prefix or terminator, found by
    searching for the already-known category string rather than guessing a
    fixed gap size). The zero-padded bytes between snapshot2 and that name
    echo are captured raw as `unclassified_gap` rather than force-fit - not
    yet understood; see FORMAT_SPEC.md.

    [V, corrected] snapshot2 was previously read starting immediately after
    marker2, which produced a snapshot2 whose points did not match ANY real
    geometry on every corpus fixture (found via robustness/run.py's Oracle
    C: corrupting a byte inside what was labelled 'snapshot2' never changed
    the decode, because it was garbage that no downstream code depended on
    in the first place - not, as first assumed, an unvalidated-but-correct
    redundant copy). Byte-searching for CAP-C00-BASE's and CAP-C10-PENT's
    own known-real coordinates located the two snapshots precisely: what
    first looked like one more nonzero u32 (0x00010001) between marker2 and
    snapshot2 is actually a 2-byte tag (u16, value 1) immediately followed
    by snapshot2's first point - the old code's 4-byte read consumed half of
    that first point's own id/x field along with the tag, misaligning every
    point after it. A defensive fallback is kept for a fixture where this
    2-byte read does NOT land on a plausible point (coordinates outside
    COORD_LO/COORD_HI): fall back to the old marker2-style nonzero-u32 scan
    rather than emit a snapshot2 the caller can't tell is wrong."""
    snap1, p = parse_point_snapshot(d, o, n_perimeter)
    def _next_nonzero_u32(p):
        while p+4 <= len(d) and u32(d, p) == 0: p += 4
        return u32(d, p), p, p+4           # value, start offset, end offset
    marker1, marker1_off, p = _next_nonzero_u32(p)   # zero-padding before marker1 varies (CAP-C00-BASE [V])
    marker2, marker2_off, p = _next_nonzero_u32(p)
    marker3_off, p2 = p, p+2
    marker3 = u16(d, p)                    # [V] u16, value 1 on every sample checked; role unknown
    if p2+6 <= len(d) and COORD_LO < i32(d, p2+2) < COORD_HI and COORD_LO < i32(d, p2+6) < COORD_HI:
        marker3_size, p = 2, p2
    else:
        marker3, marker3_off, p = _next_nonzero_u32(p)  # fallback: the old (pre-fix) reading
        marker3_size = 4
    snap2, p = parse_point_snapshot(d, p, n_perimeter)
    name_bytes = category_name.encode('latin1')
    name_at = d.find(name_bytes, p, p+400)
    if name_at != -1:
        unclassified_gap = d[p:name_at]
    elif table_start is not None and table_start > p:
        # [V, corrected] no name echo (e.g. a stale pre-edit block, per
        # decode_piece_block's own "predating some feature" note) - the
        # gap between snapshot2 and the line table still genuinely exists
        # in the file (confirmed byte-identical in shape to the name-echo
        # case's own unclassified_gap on TASK6-CURVE's second block) and
        # was previously silently dropped as d[p:p] (empty), hiding real
        # content from this field rather than just leaving it unexplained.
        unclassified_gap = d[p:table_start]
    else:
        unclassified_gap = d[p:p]
    end = name_at + len(name_bytes) if name_at != -1 else p
    return dict(snapshot1=snap1, marker1=marker1, snapshot2=snap2, marker2=marker2,
                marker3=marker3,
                # offsets/widths of the three marker fields themselves (not
                # just their values) - so coverage()'s _block_ranges can mark
                # these known-but-unexplained-role bytes 'identified' rather
                # than leaving them 'unknown' now that the snapshots
                # surrounding them no longer accidentally over-read into them.
                marker1_offset=marker1_off, marker2_offset=marker2_off,
                marker3_offset=marker3_off, marker3_size=marker3_size,
                unclassified_gap_offset=p, unclassified_gap=unclassified_gap,
                name_echo_offset=name_at, end=end), end

SEAM_OFFSET_MAX = 20000            # generous bound (2 in) for a cutline miter/offset - see check_line_table
TABLE_POINT_TAG = 0x10

def parse_table_point(d, o):
    """The 16-byte point struct used *inside* the line table - distinct from
    parse_point's perimeter-record format. `a` is the point's id (-1 for an
    unnumbered/notch point, matching the perimeter's own id convention);
    `e` is the number of child TLVs that immediately follow."""
    return dict(offset=o, x=i32(d,o), y=i32(d,o+4),
                a=u16(d,o+8), b=u16(d,o+10), c=u16(d,o+12), e=u16(d,o+14))

def parse_line_table(d, start, end=None):
    """Region D. See the module-level comment above for the grammar. Stops
    (without raising) at the first byte pattern that isn't a record header -
    on a real file that is always the block's trailer, never mid-record."""
    end = len(d) if end is None else end
    records = []
    o = start
    while o+12 <= end and d[o] == 0x0a and d[o+1] == 0x00:
        idx = i32(d,o+2); kind = u16(d,o+6); n_points = u16(d,o+8); const = u16(d,o+10)
        p = o+12
        tags, points = [], []
        while p+2 <= end:
            if d[p] == 0x0a and d[p+1] == 0x00: break
            tag = d[p]
            if tag == TABLE_POINT_TAG and d[p+1] == 0:
                tp = parse_table_point(d, p+2); p += 18
                children = []
                for _ in range(tp['e']):
                    ctag, cln = d[p], d[p+1]
                    children.append((ctag, d[p+2:p+2+cln]))
                    p += 2+cln
                tp['children'] = children
                points.append(tp)
                if len(points) == n_points: break
                continue
            ctag, ln = d[p], d[p+1]
            tags.append((ctag, d[p+2:p+2+ln])); p += 2+ln
        records.append(dict(offset=o, idx=idx, kind=kind, n_points=n_points,
                            const=const, tags=tags, points=points, end=p))
        o = p
    return records, o

# ---------------------------------------------------------------- top level
def _classify(p):
    t = bytes.fromhex(p['tail'])
    if p['id'] == -1 and len(t) >= 2 and t[1] == 1: return 'notch'
    if p['id'] == -1: return 'unnumbered'
    return 'graded' if len(t) > 5 else 'turn'

def decode_piece_block(d, field_off=None):
    m = parse_metadata(d, field_off)
    objs = parse_object_records(d, m['end'], m['n_obj_rec'], m['n_break_rows'])
    pstart = find_point_table(d, m['end'] + object_record_size(m['n_break_rows'])*m['n_obj_rec'])
    pts, after = parse_point_run(d, pstart, m['n_perimeter'])
    closing = pts[-1] if pts and pts[-1]['id'] == -1 and pts[-1]['f1'] == 2 else None
    perim = pts[:-1] if closing else pts
    # internal lists: grain line first, then drill points (CAP-C50-DRILL1);
    # each is header + points + u32 terminator + zero padding + its 'Lnn'
    # label. [V] the terminator is 3 for an open list (grain, drill, or a
    # multi-point internal line whose start and end differ) and 6 for a
    # closed loop (a multi-point internal line whose first and last stored
    # point coincide, e.g. CAP-C60-CUTOUT's 25-point circular cutout) -
    # confirmed against the actual stored geometry (first==last), not just
    # correlation, on all 30 corpus fixtures with an internal line. A
    # single-point list (a lone drill point, CAP-C50-DRILL1) trivially
    # satisfies "first==last" but reads terminator 3, not 6 - there's no
    # path to close with only one point, so `closed` below requires >=2.
    internal = []; internal_kinds = []; internal_labels = []; internal_closed = []
    internal_terminator_offsets = []; o = after
    while _is_internal_header(d, o):
        kind = INTERNAL_TAGS[u16(d,o+2)]; cnt = u16(d,o+4); o += 10
        seg = []
        for _ in range(cnt):
            # [V] a false-positive metadata match during summarize()'s brute-
            # force offset scan (garbage bytes that happen to look like a
            # valid field block) can hand decode_piece_block a garbage `cnt`
            # here. parse_point()/i32()/u16() never raise on a short slice -
            # Python silently zero-fills - so without this bound a garbage
            # cnt up to 65535 would spin reading fabricated zero points past
            # EOF instead of failing fast (seen on CAP-C62-DART: summarize()
            # hung for minutes on a bogus n_perimeter=768 candidate at a
            # mid-file offset before ever reaching the real dart geometry).
            if o+14 > len(d): break
            r = parse_point(d,o); seg.append(r); o += r['size']
        internal.append(seg); internal_kinds.append(kind)
        term_off = o
        # the file's own signal is the terminator value itself (3 open, 6
        # closed - see the loop's module comment above); geometry is only
        # a cross-check, not the source of truth, matching how this module
        # decodes every other field from raw bytes rather than inferring it.
        term_val = i32(d, term_off) if term_off+4 <= len(d) else None
        closed = term_val == 6
        internal_closed.append(closed); internal_terminator_offsets.append(term_off)
        label, past = _internal_list_label(d, o)
        internal_labels.append(label)
        if label is not None and _is_internal_header(d, past):
            o = past; continue
        break                      # block_end stays at the last list's own terminator
    # tail: pretable header + two perimeter snapshots + the line table -
    # re-anchored independently of `block_end` above (which intentionally
    # stops one step short, at the last list's own terminator, so existing
    # callers of block_end are unaffected). Best-effort: a block this code
    # doesn't otherwise recognise (e.g. a stale pre-edit record predating
    # some feature) simply gets tail=None rather than raising.
    tail = None
    try:
        pretable_off, table_start = _locate_tail(d, o)
        pretable = parse_pretable_header(d, pretable_off)
        # [V, corrected] Region C's two snapshots hold n_perimeter_a points,
        # not len(perim) - the same "corners minus notches/dart-apex" count
        # parse_pretable_header's own docstring already established for a
        # different field. Using len(perim) (the full stored perimeter,
        # notches included) made the snapshot reader walk past its real end
        # on every notched/darted/annotated/curved fixture and start reading
        # marker1's own bytes as if they were one more point - found by
        # cross-validating snapshot1/2 against the real perimeter (robustness/
        # run.py's Oracle C). Clamped defensively: an implausible field
        # (0, or larger than the full perimeter) falls back to len(perim)
        # rather than trust a corrupt/unusual value blindly.
        n_snap = pretable['n_perimeter_a']
        if not (0 < n_snap <= len(perim)): n_snap = len(perim)
        region_c, region_c_end = parse_region_c(
            d, pretable_off+PRETABLE_HEADER_SIZE, n_snap, m['name'], table_start)
        line_records, tail_end = parse_line_table(d, table_start)
        tail = dict(pretable=pretable, region_c=region_c, table_start=table_start,
                    line_records=line_records, tail_end=tail_end)
    except Exception as e:
        tail = dict(error=str(e))
    return dict(meta=m, objects=objs, points_offset=pstart, perimeter=perim,
                closing=closing, internal_lines=internal, internal_kinds=internal_kinds,
                internal_labels=internal_labels, internal_closed=internal_closed,
                internal_terminator_offsets=internal_terminator_offsets,
                block_end=o, tail=tail)

def decode(data):
    """Decode a full piece file; returns dict with one or more piece blocks."""
    if not data.startswith(MAGIC):
        raise NotAnAccuMarkObject('not an AccuMark IXPORT piece file')
    # [V] every object type carries its type code as u16 at 0x7a in both the
    # 2026-07 and 2026-09 export vintages (the u32 copy sits at 0x60 in one
    # and 0x68 in the other); 20 = piece. Markers (9), models (12), orders
    # (13) and the parameter tables must be refused here rather than
    # crashing inside decode_piece_block.
    # v2: a truncated object (too short to hold the 0x80 header + trailer)
    # is a length problem, not a type problem - say so distinctly.
    if len(data) <= 0x80:
        raise TruncatedObject('object too short to hold a header',
                               declared=0x80, actual=len(data))
    otype = u16(data, 0x7a)
    if otype != 20:
        raise WrongObjectType(
            'not a piece object (type %r); see accumark_marker.read_object' % otype,
            got=otype, want=20)
    hdr = dict(magic=data[:18].decode('latin1').rstrip('\x00'),
               db_version=data[16:19].decode('latin1').rstrip('\x00'),
               object_type=otype)
    # trailing piece-name + two identical unix timestamps
    tail = data[-160:]
    ts = []
    for o in range(len(data)-160, len(data)-4):
        v = i32(data,o)
        if 1_500_000_000 < v < 2_200_000_000: ts.append(v)
    blocks = []; block_errors = []; off = None
    while True:
        # [V] start at the payload (0x80), not 0x60: the 2026-07 vintage's
        # header residue at 0x60-0x7f looks enough like a field block to
        # hijack the search on every one of its 122 pieces.
        #
        # [V, corrected 2026-09-11] the second (and later) block's search
        # anchor was `blocks[-1]['block_end']` - the PRE-tail end (perimeter
        # + internal lines only, per decode_piece_block's own docstring) -
        # with a fixed +0x120 (288-byte) window. That window never reaches
        # past the previous block's own tail (pretable header + two Region-C
        # snapshots + the line table, typically 700-1000+ bytes), so this
        # loop has always undercounted piece_records on any file with more
        # than one block - it silently stopped at block 0, never even
        # attempting to search where block 1 actually starts. Undetected
        # until now because summarize()'s own, separate, more expensive
        # brute-force byte scan (used everywhere piece_records actually
        # matters - verify_capture.facts, coverage()) has independently
        # found every block correctly all along; nothing surfaced this
        # gap in decode()'s own documented "one or more piece blocks"
        # contract until investigating what looked like unexplained bytes
        # right after a single-block piece's line table turned out to
        # be, on a two-block piece, block 1's own field block starting
        # a few bytes later (found on CAP-C10-PENT: tail_end=1400, block 1's
        # real field_off=1408 - 992 bytes past the old search window's
        # reach). Anchor from the previous block's tail_end when its tail
        # parsed cleanly (skipping over the tail's own bytes rather than
        # risking a spurious in-tail match) and fall back to block_end
        # otherwise, exactly as before.
        if blocks:
            prev_tail = blocks[-1].get('tail')
            search_from = (prev_tail['tail_end'] if prev_tail and 'error' not in prev_tail
                           else blocks[-1]['block_end'])
        else:
            search_from = 0x80
        try: off = _find_field_block(data, search_from,
                                     (search_from+0x120 if blocks else 0x140))
        except ValueError: break   # normal loop termination: no further field block
        try: b = decode_piece_block(data, off)
        except Exception as e:
            # v2: don't discard *why* - a block that fails to decode is
            # recorded, not silently dropped, so a zero-block result can say
            # what went wrong instead of just being empty (fixes summarize()'s
            # and verify_capture's unguarded blocks[0]).
            block_errors.append(dict(offset=off, error=str(e)))
            break
        blocks.append(b)
        if b['block_end'] >= len(data)-8: break
        if len(blocks) > 8: break
    return dict(header=hdr, timestamps=sorted(set(ts)), blocks=blocks,
                block_errors=block_errors)

# -------------------------------------------------------------- coverage
def _block_ranges(d, m, objs, pstart, block_end, tail, internal_terminator_offsets=(), real=None):
    """Byte ranges 'identified' by one piece block, as (start,end) pairs.
    `block_end` is the pre-tail end (perimeter + internal lines, as computed
    by decode_piece_block - NOT the tail's own end) so that anything between
    regions that isn't actually decoded (the pad+'Lnn'-label gap before the
    pretable header, Region C's `unclassified_gap`, any inter-record padding
    in the line table) is left 'unknown' rather than swallowed by a single
    wide range. Keep this narrow - coverage() is only honest if every marked
    byte is one this module actually assigns a meaning to.

    [V, found 2026-09-11] `real` (the set of (x,y) real-geometry coordinates
    check_region_c already builds) gates whether Region C's own snapshot1/
    snapshot2 ranges get marked at all - found while auditing FORMAT_SPEC.md
    section 12's coverage claims, not by design. On the three seam-
    allowanced fixtures already known to fail check_region_c (CAP-C30-SEAM-
    UNEVEN, CAP-C31-SEAM-TAPER, TASK2-SEAM1CM - FORMAT_SPEC.md SS11), the
    same misalignment that fails the check also, on CAP-C30-SEAM-UNEVEN,
    makes one snapshot2 point read a garbage f2 (attr-byte count) of 17197 -
    parse_point has no bound on f2, so that single 'point' swallows the
    entire rest of the file (17211 bytes) into its own `size`, and the old
    unconditional r.append() then marked all of it 'identified', silently
    inflating that fixture's coverage_pct on data nothing here actually
    understood. Each snapshot is now validated independently (matching
    check_region_c's own per-snapshot loop) before its range is trusted -
    snapshot1 still marks correctly on this exact fixture (it matches real
    geometry) while snapshot2 is correctly left 'unknown'."""
    r = [(m['field_off'], m['end'])]                       # metadata + strings + size list
    if objs: r.append((objs[0]['offset'], objs[-1]['offset']+8+8*len(objs[0]['deltas'])))
    r.append((pstart, block_end))                          # perimeter + internal lines
    # [V, corrected 2026-09-11] block_end stops exactly AT the last internal
    # list's own u32 terminator (3 open / 6 closed - decode_piece_block's
    # `internal_closed`), so (pstart, block_end) above never covers those 4
    # bytes even though their value and meaning are both fully known. Mark
    # every internal list's terminator explicitly, not just the last one -
    # an interior list's terminator sits between two lists and was equally
    # uncovered before.
    for off in internal_terminator_offsets:
        r.append((off, off+4))
    if tail and 'error' not in tail:
        pt = tail['pretable']; rc = tail['region_c']
        r.append((pt['offset']-3, pt['offset']))            # the last 'Lnn' label text itself
        r.append((pt['offset'], pt['offset']+PRETABLE_HEADER_SIZE))
        # [V, corrected] snapshot points are variable width (parse_point_snapshot
        # now advances by each point's own .size, not a fixed 15 - a hardcoded
        # +15 here under-covers coverage() by however many bytes the last point's
        # real size exceeds 15, whenever that point isn't a single-trailer-byte
        # 'plain turn' record).
        def _snapshot_ok(snap):
            return real is None or all((p['x'], p['y']) in real for p in snap)
        if rc['snapshot1'] and _snapshot_ok(rc['snapshot1']):
            r.append((rc['snapshot1'][0]['offset'], rc['snapshot1'][-1]['offset']+rc['snapshot1'][-1]['size']))
        if rc['snapshot2'] and _snapshot_ok(rc['snapshot2']):
            r.append((rc['snapshot2'][0]['offset'], rc['snapshot2'][-1]['offset']+rc['snapshot2'][-1]['size']))
        # the three marker fields between the two snapshots: known position
        # and value, role still unexplained ([?], FORMAT_SPEC.md §11) - the
        # same "identified but not yet understood" status already given to
        # Region B's own unnamed constants, so identified here on the same
        # basis. Previously these bytes were only 'identified' by accident,
        # swept up by the pre-fix snapshot boundary bug overshooting into
        # them; now that the boundaries are correct, mark them explicitly
        # rather than let them read as regressed 'unknown' coverage.
        r.append((rc['marker1_offset'], rc['marker1_offset']+4))
        r.append((rc['marker2_offset'], rc['marker2_offset']+4))
        r.append((rc['marker3_offset'], rc['marker3_offset']+rc['marker3_size']))
        # rc['end'] is computed from wherever snapshot2 parsing actually
        # stopped, so it inherits the same runaway risk snapshot2 itself
        # does - gated the same way.
        if rc['name_echo_offset'] != -1 and _snapshot_ok(rc['snapshot2']):
            r.append((rc['name_echo_offset'], rc['end']))
        for rec in tail['line_records']:
            r.append((rec['offset'], rec['end']))
    return r

def coverage(data, summary=None):
    """Classify every byte of a piece file as identified / zero_pad /
    residue (the documented 3-byte export-noise floor at 0x48) / unknown,
    using everything decode_piece_block + summarize() already parse. This
    is the acceptance metric for 'is the format fully decoded' - see
    FORMAT_SPEC.md and CAPTURE_PLAN.md's Phase 1 status.

    `summary` lets a caller that already ran summarize(data) (verify_capture.
    py's facts(), notably) pass it in rather than pay for a second brute-
    force block scan - summarize() alone is the dominant cost here (~3.5s on
    TASK6-CURVE) since it re-scans the file byte-by-byte for piece-block
    candidates; coverage()'s own classification work is comparatively cheap."""
    d = data
    cls = ['unknown'] * len(d)
    def mark(a, b, label):
        for i in range(max(0,a), min(len(d),b)): cls[i] = label
    mark(0, 0x48, 'identified')            # magic + export name slot (§1)
    mark(0x48, 0x4b, 'residue')            # [V] the 3-byte noise floor
    mark(0x4b, 0x60, 'identified')
    # [V, corrected 2026-09-11] four more header fields whose position and
    # value are already fully known elsewhere in this codebase (read_object's
    # own fields) but were never wired into coverage()'s identified-marking,
    # so they read as 'unknown' despite being understood - found while
    # checking FORMAT_SPEC.md section 12's open items.
    mark(0x60, 0x64, 'identified')         # u32 object-type copy (accumark_marker.read_object)
    mark(0x78, 0x7a, 'identified')         # [V] u16, constant 0x59ba on every corpus fixture
                                            # (piece AND the structurally-different CAP-C63-MODEL
                                            # alike) - confirmed universal, role still unknown [?]
    mark(0x7a, 0x7c, 'identified')         # u16 object type (accumark_marker.read_object / decode())
    mark(0x70, 0x78, 'residue')            # [V] pointer-shaped, clusters by CAPTURE SESSION not
                                            # by piece content - byte-identical between CAP-C00-BASE
                                            # and its 2-minutes-later reexport CAP-C01-REEXPORT (same
                                            # process instance), but differs across the corpus's
                                            # ~4 distinct capture sessions - the same heap/stack
                                            # residue category as the 3-byte noise floor above, a
                                            # second instance of it, not per-piece data
    mark(0x7e, 0x82, 'identified')         # u32 payload length (accumark_marker.read_object's `plen`)
    mark(0x82, 0x83, 'identified')         # [V] u8, constant 0x90 on every corpus fixture including
                                            # the structurally-different CAP-C63-MODEL - confirmed
                                            # universal, role still unknown [?]
    s = summary if summary is not None else summarize(d)
    def _tail_end(b):
        return b['tail']['line_records'][-1]['end'] if b['tail'] and 'error' not in b['tail'] else b['block_end']
    for b in s['blocks']:
        real = {(p['x'], p['y']) for p in b['perimeter']}
        if b.get('closing'): real.add((b['closing']['x'], b['closing']['y']))
        for seg in b['internal_lines']:
            for p in seg: real.add((p['x'], p['y']))
        for a, e in _block_ranges(d, b['meta'], b['objects'], b['points_offset'], b['block_end'], b['tail'],
                                   b.get('internal_terminator_offsets', ()), real=real):
            mark(a, e, 'identified')
    # Region A - the 'Lnn' line-attribute records (parse_segments, FORMAT_SPEC
    # §6) and, on seam-allowanced pieces, the derived-cut-line records
    # (parse_line_geometry) that share the same label convention. These sit
    # between a block's `block_end` and its tail's pretable header and were
    # the single biggest source of false 'unknown' bytes before this was
    # added - decode_piece_block never folds Region A into block_end, and
    # summarize() (matching its own existing usage) scans for them across
    # the whole file rather than per block, so mark them the same way here.
    for rec in s['segments']:
        mark(rec['offset'], rec['end'], 'identified')
    for rec in s['line_geometry']:
        mark(rec['offset'], rec['end'], 'identified')
    # trailer: name slot(s), the two identical timestamps, 'MSI'-style author
    # name(s) - same fixed-purpose fields as the header, just recognised by
    # content rather than a fixed offset since trailer length varies (306 -
    # 440 bytes observed so far, not the ~160 originally guessed in FORMAT_SPEC).
    last_end = _tail_end(s['blocks'][-1])
    cat = s['category'].encode('latin1')
    for m in re.finditer(re.escape(cat), d[last_end:]):
        mark(last_end+m.start(), last_end+m.end(), 'identified')
    for m in re.finditer(rb'MSI', d[last_end:]):            # [?] hardcoded author string
        mark(last_end+m.start(), last_end+m.end(), 'identified')
    last_ts_end = None
    for o in range(last_end, len(d)-4):
        if 1_500_000_000 < i32(d,o) < 2_200_000_000:
            mark(o, o+4, 'identified')
            last_ts_end = o+4
    # [V, found 2026-09-11] immediately after the timestamp pair's own last
    # occurrence, one zero-padded u32 then a constant u32 = 5 - confirmed
    # byte-identical (value 5, exactly 4 bytes after the zero pad) on 20 of
    # 21 corpus fixtures (1-, 2-block, every trailer length 306-440 seen);
    # the one exception, CAP-C30-SEAM-UNEVEN, is one of the three already-
    # documented check_region_c/check_line_table seam-allowance outliers
    # (FORMAT_SPEC.md SS11) and reads the same shape one block earlier, not a
    # genuine counter-example. Not per-piece data - found while auditing
    # section 12's coverage claims for staleness, not previously catalogued
    # anywhere in FORMAT_SPEC.md. Marked identified on the same "known
    # position + value, role still open" basis as Region B's own unnamed
    # constants; its specific meaning remains unexplored.
    if last_ts_end is not None and i32(d, last_ts_end+4) == 5:
        mark(last_ts_end+4, last_ts_end+8, 'identified')
    for i,c in enumerate(cls):
        if c == 'unknown' and d[i] == 0: cls[i] = 'zero_pad'
    counts = {}
    for c in cls: counts[c] = counts.get(c,0)+1
    runs = []
    i = 0
    while i < len(cls):
        if cls[i] == 'unknown':
            j = i
            while j < len(cls) and cls[j] == 'unknown': j += 1
            runs.append((i, j, d[i:j].hex()))
            i = j
        else: i += 1
    return dict(counts=counts, total=len(d), unknown_runs=runs,
                coverage_pct=round(100*(1-counts.get('unknown',0)/len(d)), 2))

def check_line_table(b):
    """Structural consistency check for one decoded block's Region D (line
    table), independent of coverage(): every table point must coincide with
    a point this module already decoded elsewhere in the SAME block
    (perimeter / closing / internal-line). Returns True/False - see
    verify_capture.py's `line_table_consistent` field.

    [V] Two count-based checks were tried and dropped as invalid rather than
    kept as false failures: "one kind-1 record per numbered (id != -1)
    perimeter point" fails on TASK6-CURVE, where a single curved Lnn segment
    carries several numbered points along its length (10/10/8/10 points on
    just 4 segments - the count that varies with grading, not edge count);
    "every kind-1 record has >=2 numbered endpoints" fails on CAP-C10-PENT/
    CAP-C11-HEX, where one (pentagon) or two (hexagon) plain, non-notch
    'turn' points carry id=-1 despite being real corners - apparently
    corners added after a piece's original N-corner base shape don't get a
    sequential id, the same way a notch doesn't ([?], see FORMAT_SPEC.md).
    Point-coincidence is the one invariant that holds everywhere it's been
    checked, INCLUDING catching a real anomaly: CAP-C61-MIRROR's line table
    references a table point (id 5) matching neither of its 3 real perimeter
    points nor its grain line - a virtual/mirrored corner not otherwise
    stored in the piece, still unexplained ([?]).

    [V] Seam-allowanced pieces (CAP-C30/C31, TASK2-SEAM1CM) add one kind-2
    record per seam-allowanced edge, n_points=4: [mitered corner at this
    edge's start, plain offset at start, plain offset at end, mitered corner
    at end]. None of these 4 points are raw stored geometry - they are the
    cut line, each one a real perimeter corner moved by a uniform amount
    along x, y, or both (the seam allowance; a mitered corner moves on both
    axes, a plain offset on one) - so they cannot appear in `real` above.
    Recognised structurally rather than by re-deriving the exact seam value:
    a bad point is accepted if some real point is within +-SEAM_OFFSET_MAX
    on both axes with an integer offset that is 0 on at least one axis, or
    equal in magnitude on both (the diagonal/mitered case). This is a shape
    test, not a coincidence, so it still rejects an unrelated stray point.
    Confirmed this way on TASK2-SEAM1CM's uniform 1 cm seam; still returns
    False ([?]) on CAP-C30-SEAM-UNEVEN/CAP-C31-SEAM-TAPER, whose *uneven*
    seam makes a shared corner's miter the intersection of two differently-
    offset edges (e.g. dx=-3934,dy=-66 - neither axis-aligned nor diagonal),
    not a simple per-corner offset; that needs the corner's two adjacent
    seam_begin/seam_end values threaded through to re-derive properly, which
    is Phase B work, not a parser bug.

    [V, added 2026-09-11] a table point carrying a tag-0x07 child (a notch
    attribute block, §10.3) has its own `c` field set to the Notch Type
    number (1-30) - a THIRD independent copy, alongside the perimeter
    point's own `f1` high byte (§4) and the tag-0x07 payload's own byte 0
    and byte 44. Confirmed on all 10 notch-carrying table points in the
    corpus (CAP-C40-NOTCH-TYPES's 4 distinct types 2/4/5/1, CAP-C41/
    CAP-C42's 6 Type-1 notches): `c` matches `f1` exactly, every time,
    including the one case where the 45-byte payload's own byte 44
    disagreed with everything else (CAP-C40's third notch: `f1`=5, `c`=5,
    payload byte0=5, payload byte44=8 alone reads 8) - two of three
    independent fields agreeing is why FORMAT_SPEC.md no longer treats
    byte 44 as a plausible second reliable copy. Checked here as a genuine
    consistency invariant, not just documented: `c` must equal the
    perimeter's own decoded Notch Type for the same coordinate.

    [V, corrected 2026-09-11] kind=2 is NOT specific to seam allowance - it
    is the line table's echo record for EVERY internal line (grain, drill,
    cutout; §10's `internal_kinds`), one kind=2 record per internal-line
    segment, always present whether or not the piece has a seam at all
    (confirmed on CAP-C00-BASE/CAP-C10-PENT/CAP-C50-DRILL1/CAP-C60-CUTOUT/
    CAP-C12-TWOINTLINES: their grain/drill/cutout kind=2 records match
    b['internal_lines'] point-for-point, exactly, in order - no offset
    involved). These echo records are structurally distinct from genuine
    seam/cutline kind=2 records by their points' own `a` (id) field: every
    point in an internal-line echo has `a == 65535` (unnumbered, the same
    convention id=-1 uses elsewhere), while a genuine seam/cutline record's
    points carry real numbered corner ids (confirmed: no corpus fixture ever
    mixes the two within one record). robustness/run.py's Oracle C is what
    surfaced this: corrupting an internal-line echo's own point on a
    NON-seam piece (CAP-C00-BASE has no seam at all) was passing this check
    anyway, because the pre-fix code applied the seam-offset leniency to
    EVERY kind=2 record indiscriminately - a corrupted echo point still
    landed "near" its own real, uncorrupted internal-line point by dumb
    coincidence (sharing an axis with it) and was waved through as a
    plausible seam miter on a piece that was never seamed. The leniency is
    now scoped to points that actually carry a numbered id, matching what
    real seam/cutline records structurally look like; an internal-line echo
    point must now coincide exactly, like everything else."""
    tail = b.get('tail')
    if not tail or 'error' in tail or not tail.get('line_records'): return False
    real = {(p['x'], p['y']) for p in b['perimeter']}
    if b.get('closing'): real.add((b['closing']['x'], b['closing']['y']))
    for seg in b['internal_lines']:
        for p in seg: real.add((p['x'], p['y']))
    notch_type_by_xy = {(p['x'], p['y']): p['notch_type'] for p in b['perimeter']
                         if p['notch_type'] is not None}
    def _is_seam_offset(pt):
        x, y = pt
        for rx, ry in real:
            dx, dy = x-rx, y-ry
            if dx == 0 and dy == 0: continue
            if max(abs(dx), abs(dy)) > SEAM_OFFSET_MAX: continue
            if dx == 0 or dy == 0 or abs(dx) == abs(dy): return True
        return False
    for rec in tail['line_records']:
        pts = rec['points']
        if not pts: return False
        for tp in pts:
            pt = (tp['x'], tp['y'])
            # the seam-offset leniency only applies to a genuine seam/
            # cutline point (a real numbered corner id) - an internal-line
            # echo point (a == 65535, unnumbered) must coincide exactly.
            is_seam_candidate = rec['kind'] == 2 and tp['a'] != 65535
            if pt not in real and not (is_seam_candidate and _is_seam_offset(pt)):
                return False
            has_notch_tag = any(tag == 0x07 for tag, _ in tp['children'])
            if has_notch_tag and pt in notch_type_by_xy and tp['c'] != notch_type_by_xy[pt]:
                return False
    return True

def check_region_c(b):
    """Structural consistency check for Region C's two perimeter snapshots -
    the same point-coincidence invariant check_line_table already applies to
    the line table, applied here to snapshot1/snapshot2. Added v2 (see
    CHANGELOG.md) alongside the parse_region_c fix it validates: before that
    fix, this check would have failed on every corpus fixture, because
    snapshot2 (and, on notched/darted/annotated/curved pieces, part of
    snapshot1 too) was being read from the wrong offset - not because the
    underlying data was actually unvalidated. Returns True/False; False on a
    fixture with no region_c at all (rather than "not applicable"), the same
    convention check_line_table uses for a missing line table.

    [?] Still returns False on the same three seam-allowanced fixtures
    check_line_table's own docstring already documents as a known gap
    (CAP-C30-SEAM-UNEVEN, CAP-C31-SEAM-TAPER, TASK2-SEAM1CM) - their uneven/
    tapered seam corners aren't plain per-corner offsets on either check, so
    this isn't a new, separate mystery, just the same open one showing up
    in a second place."""
    tail = b.get('tail')
    if not tail or 'error' in tail or not tail.get('region_c'): return False
    rc = tail['region_c']
    real = {(p['x'], p['y']) for p in b['perimeter']}
    if b.get('closing'): real.add((b['closing']['x'], b['closing']['y']))
    for seg in b['internal_lines']:
        for p in seg: real.add((p['x'], p['y']))
    for snap in (rc['snapshot1'], rc['snapshot2']):
        if not snap: return False
        for p in snap:
            if (p['x'], p['y']) not in real: return False
    return True

def _select_piece_member(path, member=None):
    """v2: pick the single piece (type 20) object in a ZIP by content
    (the XGGT magic), not by the `.tmp` extension - so a renamed member
    still decodes, an ambiguous zip is refused by name rather than silently
    resolved by namelist() order (the old bug: the first `.tmp` in a 34-
    member production marker zip is a lay_limits object, not a piece), and a
    zip with no piece at all raises a specific, actionable error instead of
    a bare IndexError.

    `member`, when given, disambiguates a multi-piece zip by exact member
    name."""
    z = zipfile.ZipFile(path)
    source = getattr(path, 'name', None) or (path if isinstance(path, str) else 'zip')
    if member is not None:
        try: d = z.read(member)
        except KeyError:
            raise NoSuchObject('no member %r in zip' % member, source=source)
        if not d.startswith(MAGIC):
            raise NotAnAccuMarkObject('member %r is not an AccuMark object' % member, source=source)
        return member, d
    xggt, nested = [], []
    for n in z.namelist():
        d = z.read(n)
        if d.startswith(MAGIC): xggt.append((n, d))
        elif d[:4] in (b'PK', b'PK'):
            nested.append(n)
    pieces = [(n, d) for n, d in xggt if len(d) > 0x80 and u16(d, 0x7a) == 20]
    if not pieces:
        if nested:
            raise NestedArchive('no AccuMark object at the top level of the zip',
                                 source=source, nested=nested)
        if xggt:
            raise NoSuchObject('zip has %d AccuMark object(s) but none is a piece '
                                '(type 20); see accumark_marker.list_zip' % len(xggt),
                                source=source)
        raise NotAnAccuMarkZip('no AccuMark object found in zip', source=source)
    if len(pieces) > 1:
        raise AmbiguousObject('zip has %d piece objects; pass member= to pick one'
                               % len(pieces), source=source,
                               candidates=[n for n, _ in pieces])
    return pieces[0]

def decode_zip(path, member=None):
    name, d = _select_piece_member(path, member)
    return decode(d)

# ------------------------------------------------------------ .RUL (ASCII)
def parse_rul(text):
    if isinstance(text, bytes): text = text.decode('latin1')
    hdr = dict((k.strip(), v.strip()) for k, v in
               re.findall(r'^([A-Z][A-Z /0-9]*?):\s*(.*)$', text, re.M))
    sizes = hdr.get('SIZE LIST','').split()
    rules = {}
    for m in re.finditer(r'RULE:\s*DELTA\s*(\S+)\r?\n(.*?)(?=RULE:|END)', text, re.S):
        v = [float(x) for x in re.findall(r'-?\d+\.\d+', m.group(2))]
        rules[m.group(1)] = [(v[i], v[i+1]) for i in range(0, len(v), 2)]
    return dict(header=hdr, sizes=sizes, sample_size=hdr.get('SAMPLE SIZE'),
                table=hdr.get('GRADE RULE TABLE'), rules=rules)


# ------------------------------------------------------- perimeter segments
def parse_segments(d, start=0, end=None):
    """Perimeter/internal 'line' records.  Records are NAME-TERMINATED: the
    3-byte ASCII label 'L%02d' that follows a field group is that group's
    line name, so the label preceding a field group names the *previous*
    record.  Attribute-record fields:
        [u16 0x0004, u16 0x000E, u16 n_lines]  (first record only)
        u16 n_points_on_line
        u16 seam_flag      1 -> seam-allowance pair follows
        u16 c(=1)  u16 d(=0)
        i32 seam_begin, i32 seam_end   (iff seam_flag==1; 1e-4 inch)
        [6 zero bytes iff seam_flag==1]
        u32 0x00000003                 terminator
    """
    import re
    end = len(d) if end is None else end
    labels = [start+m.start() for m in re.finditer(rb'L[0-9][0-9]', d[start:end])]
    recs = []
    for k, o in enumerate(labels):
        p = o+3; pre = None
        if u16(d,p) == 4 and u16(d,p+2) == 0x0e:
            pre = u16(d,p+4); p += 6
        n_pts, flag, c, e = u16(d,p), u16(d,p+2), u16(d,p+4), u16(d,p+6)
        if flag not in (0,1) or c != 1 or e != 0 or not 0 < n_pts <= 500: continue
        p += 8
        seam = None
        if flag == 1:
            seam = (i32(d,p), i32(d,p+4)); p += 8+6
        if i32(d,p) != 3: continue
        recs.append(dict(offset=o, fields_offset=o+3, n_lines=pre, n_points=n_pts,
                         seam_flag=flag,
                         seam_begin=seam[0] if seam else None,
                         seam_end=seam[1] if seam else None,
                         name=d[labels[k+1]:labels[k+1]+3].decode() if k+1 < len(labels) else None,
                         end=p+4))                 # past the u32=3 terminator; feeds coverage()
    return recs

def parse_line_geometry(d, start=0, end=None):
    """Line records that carry explicit point pairs (observed only on
    seam-allowanced pieces: the derived cut line).  Signature after the
    label: fe ff 53 00 02 00 01 00 <u16 idx> <u16 idx> then 2 point records."""
    import re
    end = len(d) if end is None else end
    out = []
    for m in re.finditer(rb'L[0-9][0-9]\xfe\xff\x53\x00', d[start:end]):
        o = start+m.start(); p = o+13
        idx = None
        pts = []
        for _ in range(2):
            r = parse_point(d,p); pts.append(r); p += r['size']
        out.append(dict(offset=o, label=d[o:o+3].decode(), idx=idx,
                        pts=[(q['x'],q['y']) for q in pts], end=p))
    return out

# ------------------------------------------------------------ fold axis
def mirror_lines(data):
    """Fold ("Mirror Piece") axes declared in the tail: `L<nn> fe|ff ff 'M' 00`
    then u16 count(=2), u16 1, u16 0xffff (not part of the walk), then two
    ordinary point records (id -1, rule 10001, terminator 09) and a u32 3
    [V 2026-09-09: all four OUCF fold halves of style 2303; dxfparser
    ledger section 13 - 1465 M blocks in a 955-zip corpus all read exactly].
    Returns a list of unique ((x1,y1),(x2,y2)) in 1e-4 inch units (the block
    is repeated in the stale second piece record, hence the dedupe)."""
    out = []
    for m in re.finditer(rb'L[0-9][0-9][\xfe\xff]\xffM\x00', data):
        p = m.end()
        cnt = u16(data, p); p += 6
        pts = []
        for _ in range(cnt):
            r = parse_point(data, p); pts.append((r['x'], r['y'])); p += r['size']
        if len(pts) == 2 and tuple(pts) not in out: out.append(tuple(pts))
    return out

def unfold(pts, axis):
    """Reflect an outline across a fold axis and return the whole piece:
    the stored half plus its mirror image, walked as one closed ring.
    Points lying on the axis are shared, not duplicated. `pts` and `axis`
    in the same units."""
    (x1, y1), (x2, y2) = axis
    dx, dy = x2-x1, y2-y1
    L2 = dx*dx + dy*dy or 1.0
    def refl(p):
        t = ((p[0]-x1)*dx + (p[1]-y1)*dy) / L2
        fx, fy = x1 + t*dx, y1 + t*dy
        return (2*fx - p[0], 2*fy - p[1])
    axis_len = L2**0.5
    def on_axis(p):
        # tolerance scales with the axis so the test works in 1e-4 inch
        # integers and in inches alike (an absolute 0.5 was half an inch when
        # called on inch coordinates and swallowed most of a 1.2 in piece)
        return abs((p[0]-x1)*dy - (p[1]-y1)*dx) / axis_len <= 1e-5 * axis_len
    n = len(pts)
    # rotate so the ring starts just after an on-axis point, if any
    idx = [i for i in range(n) if on_axis(pts[i])]
    if len(idx) >= 2:
        # find the on-axis point after which the off-axis run begins
        start = None
        for i in idx:
            if not on_axis(pts[(i+1) % n]): start = i; break
        if start is None: start = idx[0]
        ring = [pts[(start+k) % n] for k in range(n)]
        # ring[0] is on the axis; the run continues to the next on-axis point
        end = next((k for k in range(1, n) if on_axis(ring[k])), n-1)
        half = ring[:end+1]
        return half + [refl(p) for p in reversed(half[1:-1])]
    return list(pts) + [refl(p) for p in reversed(pts)]

def summarize(data):
    """High-level, validated summary of a piece file."""
    dec = decode(data)
    d = data
    blocks = []
    o = 0x80                          # payload start; header residue above is never a block
    while o < len(d)-40:
        # cheap pre-filter (the same test _find_field_block applies) before
        # the full parse - this loop visits every byte offset of the file
        n = u16(d,o)
        if not (3 <= n <= 64 and all(32 <= c < 127 for c in d[o+22:o+22+n+3])):
            o += 1; continue
        try: m = parse_metadata(d,o)
        except Exception: m = None
        ok = (m and 1 <= m['n_sizes'] <= 40 and 3 <= m['n_perimeter'] <= 5000
              and all(s['name'].isalnum() for s in m['sizes']) and m['name'].isprintable())
        if ok:
            try:
                b = decode_piece_block(d,o)
                # a real block_end is always > o (it consumed at least the
                # 22-byte field block); guard against a false-positive match
                # whose decode "succeeds" but doesn't advance, which would
                # otherwise spin forever re-decoding the same offset [V]
                if b['block_end'] > o:
                    blocks.append(b); o = b['block_end']; continue
            except Exception: pass
        o += 1
        if len(blocks) > 8: break     # matches decode()'s own safety cap
    name_hdr = d[0x15:d.index(b'\x00',0x15)].decode('latin1')
    segs = parse_segments(d)
    if not blocks:
        # v2: a forged/corrupt-but-magic-bearing object can pass decode()'s
        # header check yet contain zero plausible field blocks under this
        # function's own (independent, brute-force) scan - surface that
        # distinctly instead of IndexError on blocks[0].
        raise DecodeError('no piece block found in object payload',
                           source=name_hdr or None)
    b0 = blocks[0]
    return dict(
        header_piece_name = name_hdr,
        db_version = d[:18].decode('latin1').rstrip('\x00'),
        timestamps = dec['timestamps'],
        category   = b0['meta']['name'],
        annotation = b0['meta']['annotation'],
        rule_table = b0['meta']['rule_table'],
        size       = b0['meta']['size'],
        sample_size= b0['meta']['sample_size'],
        sizes      = [s['name'] for s in b0['meta']['sizes']],
        base_index = b0['meta']['base_index'],
        n_blocks   = len(blocks),
        blocks     = blocks,
        perimeter_in = [( p['x']/UNITS_PER_INCH, p['y']/UNITS_PER_INCH) for p in b0['perimeter']],
        notches_in = [(p['x']/UNITS_PER_INCH, p['y']/UNITS_PER_INCH) for p in b0['perimeter'] if p['is_notch']],
        notch_types = [p['notch_type'] for p in b0['perimeter'] if p['is_notch']],
        grade_refs = [(p['id'], p['rule_ref']) for p in b0['perimeter'] if p['rule_ref'] is not None],
        internal_lines_in = [[(q['x']/UNITS_PER_INCH, q['y']/UNITS_PER_INCH) for q in seg]
                             for seg, k in zip(b0['internal_lines'], b0['internal_kinds']) if k == 'grain'],
        drill_points_in = [(q['x']/UNITS_PER_INCH, q['y']/UNITS_PER_INCH)
                           for seg, k in zip(b0['internal_lines'], b0['internal_kinds']) if k == 'drill'
                           for q in seg],
        cutouts_in = [[(q['x']/UNITS_PER_INCH, q['y']/UNITS_PER_INCH) for q in seg]
                     for seg, k in zip(b0['internal_lines'], b0['internal_kinds']) if k == 'cutout'],
        n_break_rows = b0['meta']['n_break_rows'],
        grade_rules = {o_['id']: o_['deltas'] for o_ in b0['objects']},
        segments   = segs,
        line_geometry = parse_line_geometry(d),
        seam_allow_in = sorted({(s['seam_begin']/UNITS_PER_INCH, s['seam_end']/UNITS_PER_INCH)
                                for s in segs if s['seam_flag'] == 1}),
        mirror_lines_in = [tuple((x/UNITS_PER_INCH, y/UNITS_PER_INCH) for x, y in ax)
                           for ax in mirror_lines(d)],
        object_records = [(o_['id'], o_['payload']) for o_ in b0['objects']],
    )

def summarize_zip(path, member=None):
    name, d = _select_piece_member(path, member)
    return summarize(d)
