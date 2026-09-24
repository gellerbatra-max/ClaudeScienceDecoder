"""accumark_marker.py - reader for the non-piece objects of an AccuMark
'XGGT IXPORT DB5.1' export ZIP: the marker (type 9), its order (13), models
(12) and the parameter tables, plus placement of decoded pieces on a laid
marker.

Format knowledge: MARKER_DECODE_PLAN.md (this repo) and, for the slot
layout and the slot->piece binding, gellerbatra-max/dxfparser
docs/accumark-decoded-so-far.md section 6 (verified there on 2,830 placements).

v2 (see CHANGELOG.md): a truncated object raises accumark_errors.TruncatedObject
instead of returning a plausible-looking dict built from wrapped-around bytes;
list_zip() reads each ZIP member by position (ZipInfo) rather than by name, so
members that happen to share a name no longer alias to the same object.

v4 (see CHANGELOG.md; documentation label only, __version__ stays 3.0): the
model list and size table (sections 11-12) are read as the length-prefixed
chain they are (parse_model_list / parse_sizes_section) instead of by regex, so
no model or size is dropped and hyphenated / lettered size names work;
parse_marker falls back to the marker's OWN size table to split record texts
when the pieces are not in the ZIP; read_object reads created/modified from
their fixed trailer offsets instead of scanning for plausible-looking integers.

v4.1 (same label): slots are bound to their (piece, size, model) STRUCTURALLY -
each slot's 6-byte head (record index, piece index, bundle), the size table's
tiling of the slot table and section 10's piece list - with the declared area
demoted to a cross-check (parse_marker(binding='area') keeps the old rule).
The area rule picked an arbitrary size whenever sister sizes tie on area (77 of
97 slots on 2303-BD 137); the drawn DXF's own labels prove the structural size.
Section 10 is read as the length-prefixed chain it is, and section 14's records
are walked from section 13's index instead of by regex.

    import accumark_marker as am
    objs = am.list_zip('2303-BD 137 PLACED.zip')          # every object, typed
    mk   = am.parse_marker(objs['marker'][0]['data'])       # header + placements
    laid = am.place_marker('2303-BD 137 PLACED.zip')        # outlines in the marker frame
"""
import math, re, struct, zipfile
from collections import Counter
import accumark_pds as ap
from accumark_errors import (AccuMarkError, NotAnAccuMarkZip, NestedArchive,
    NotAnAccuMarkObject, TruncatedObject, WrongObjectType, NoSuchObject,
    AmbiguousObject, DecodeError)

u16, i16, i32, u32 = ap.u16, ap.i16, ap.i32, ap.u32
def f64(d, o): return struct.unpack_from('<d', d, o)[0]

__version__ = '3.0'
MAGIC = b'XGGT IXPORT DB5.'
TRAILER = 396
# The trailer's created / modified Unix stamps are aligned u32s at these
# offsets INTO the 396-byte trailer [V: 267 of 269 objects in 103 zips, every
# object type and both export vintages, decode to a real date with created <=
# modified; the other two are library tables whose stamps (2004, 2013) fall
# outside the old 2014-2039 window]. STAMP_LO/HI is only a plausibility window
# (1980-01-01 .. 2040-01-01) that rejects zeros and sentinels.
TRAILER_CREATED, TRAILER_MODIFIED = 0xf4, 0xf8
STAMP_LO, STAMP_HI = 315_532_800, 2_208_988_800
OBJECT_TYPES = {20: 'piece', 12: 'model', 13: 'order', 9: 'marker',
                10: 'marker_geometry', 2: 'annotation', 3: 'block_buffer',
                6: 'lay_limits', 17: 'notch_table', 23: 'rule_table'}

# ------------------------------------------------------------ envelope
def _stamp(tr, off):
    t = u32(tr, off)
    return t if STAMP_LO <= t < STAMP_HI else None

def read_object(d):
    """Envelope shared by every object type and both export vintages [V]:
    name at 0x15, type u16 at 0x7a (the u32 copy is at 0x60 or 0x68
    depending on vintage), payload length u32 at 0x7e, payload from 0x80,
    396-byte trailer with created/modified Unix stamps and user names.

    v2: validates the object is actually long enough to hold what read_object
    claims before slicing it. Note payload (d[0x80:0x80+plen]) and the
    396-byte trailer are NOT sequential, non-overlapping regions in general -
    real small objects (e.g. a 480-byte lay_limits) have payload data sitting
    inside what the trailer's fixed 396-byte tail also covers, so `0x80+plen
    +TRAILER <= len(d)` is not a valid invariant (checked against the corpus:
    it fails on several genuine, correctly-decoding production fixtures).
    What IS reproducibly true, and what the truncation bug actually needs: a
    marker truncated to ~120-200 bytes used to return a plausible-looking
    dict where d[-TRAILER:] covered the *entire* short buffer (header
    included) instead of a real, distinct trailer region - guard against
    that by requiring the buffer be at least TRAILER bytes on its own.

    v4: `created` / `modified` are the aligned u32s at trailer +0xF4 / +0xF8
    (TRAILER_CREATED / TRAILER_MODIFIED), or None when outside the
    STAMP_LO..STAMP_HI plausibility window. They used to be the first two
    values found by sliding a 4-byte window over the whole trailer at EVERY
    byte offset, which matched unaligned junk (the byte runs `66 00 00 00` /
    `62 00 00 00` read as 2024 / 2022 stamps) and agreed with the real fields
    on only 30 of the 269 corpus objects. On library tables copied between
    storage areas `created` can be later than `modified` (M-MARKER: 2023 vs
    2013) - both are reported as stored. `users` is still the old token scan
    of the trailer and includes fragments of the object's own name (the real
    creator / modifier strings sit at +0x110 / +0x162); left unchanged."""
    if not d.startswith(MAGIC): raise NotAnAccuMarkObject('not an AccuMark IXPORT object')
    if len(d) < 0x82:
        raise TruncatedObject('object too short to hold a header', declared=0x82, actual=len(d))
    try:
        name_end = d.index(b'\x00', 0x15)
    except ValueError:
        raise TruncatedObject('object header name is not NUL-terminated (truncated?)',
                               actual=len(d))
    name = d[0x15:name_end].decode('latin1')
    t = u16(d, 0x7a); plen = u32(d, 0x7e)
    if len(d) < TRAILER:
        raise TruncatedObject('object shorter than its own trailer region',
                               source=name, declared=TRAILER, actual=len(d))
    tr = d[-TRAILER:]
    users = [m.group().decode('latin1') for m in re.finditer(rb'[A-Za-z][A-Za-z0-9]{1,30}', tr)]
    return dict(name=name, type=t, kind=OBJECT_TYPES.get(t, 'unknown_%d' % t),
                payload_len=plen, size=len(d), payload=d[0x80:0x80+plen],
                created=_stamp(tr, TRAILER_CREATED), modified=_stamp(tr, TRAILER_MODIFIED),
                users=users, data=d)

def list_zip(path):
    """{kind: [object, ...]} for every XGGT member of an export ZIP.

    v2: reads members by position (ZipInfo from infolist()) rather than by
    name - zipfile.ZipFile.read(name) resolves through a name->info dict, so
    two entries sharing a member name used to alias to the same bytes and
    silently double-count every object in the archive. Each entry is now
    decoded independently regardless of name collisions; duplicate_member_names
    reports any names that occur more than once, for diagnostics.

    v2: a single corrupt/truncated member (read_object raising) is skipped
    and recorded in object_errors rather than aborting the whole listing -
    a 34-member marker zip with one bad piece should still return the other
    33 objects, the same fail-soft-and-record philosophy as
    place_marker/load_pieces (found while building robustness/run.py's
    Oracle C: the old all-or-nothing behaviour meant one corrupted member
    made a caller lose visibility into every OTHER object in the zip)."""
    out = {}; seen_names = {}; obj_errors = []
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            seen_names[info.filename] = seen_names.get(info.filename, 0) + 1
            d = z.read(info)
            if not d.startswith(MAGIC): continue
            try:
                o = read_object(d)
            except Exception as e:
                obj_errors.append(dict(member=info.filename, error=str(e))); continue
            o['member'] = info.filename
            out.setdefault(o['kind'], []).append(o)
    dupes = [n for n, c in seen_names.items() if c > 1]
    if dupes: out['duplicate_member_names'] = dupes
    if obj_errors: out['object_errors'] = obj_errors
    return out

# --------------------------------------------------------------- marker
DIR_OFF, DIR_SLOTS = 0x8a, 42
# v4.1: directory words 0..39 are section offsets; the last two are not.
# Word 40 is a small state code - 0 / 1 / 2 = none / some / all slots placed
# [V: 18 of 18 corpus markers] - and word 41 is 0. Reading 1 or 2 as an
# offset made a bogus section 40 on every laid marker.
DIR_OFFSETS = 40
SLOT = 96
SLOT_HEAD = 6       # a slot's (record index, piece index, bundle) u16s sit 6 bytes BEFORE its body
SEC_SCALARS, SEC_PIECES, SEC_MODELS, SEC_SIZES, SEC_INDEX, SEC_RECORDS, SEC_ORDER_COPY, SEC_SLOTS, SEC_GEOMETRY = 1, 10, 11, 12, 13, 14, 15, 21, 30
SEC_BUFFERS = 6
ROT180_BIT, MIRROR_BIT = 0x2000, 0x0080

def directory(d):
    """42 u32 ABSOLUTE file offsets at 0x8a; 0xffffffff = section absent [V]."""
    return [u32(d, DIR_OFF+4*i) for i in range(DIR_SLOTS)]

def _section(d, dirs, k):
    if k >= DIR_OFFSETS: return None            # v4.1: words 40/41 are state, not offsets
    a = dirs[k]
    if a in (0xffffffff, 0): return None
    # v2: a section's directory offset is trusted absolute file position with
    # no built-in bound - on a truncated object this used to point past EOF
    # and only fail much later, as a bare struct.error deep inside whichever
    # section parser (e.g. parse_slots's '<dddd' unpack). Catch it here,
    # where the offset is still attributable to "this object is truncated"
    # rather than "this struct doesn't unpack".
    if a >= len(d):
        raise TruncatedObject('section %d offset points past end of object' % k,
                               declared=a, actual=len(d))
    later = [v for v in dirs[:DIR_OFFSETS] if v not in (0xffffffff, 0) and v > a]
    return a, (min(later) if later else len(d))

def decode_orient(code):
    """Orientation word -> dict(rot, flip_h, flip_v). Bit 0x2000 = rotate 180,
    bit 0x0080 = mirror; both together = flip about the vertical axis
    (dxfparser, verified on four DXF-drawn orientations; other bits are
    vintage base data)."""
    r180 = bool(code & ROT180_BIT); mirror = bool(code & MIRROR_BIT)
    if r180 and mirror: return dict(rot=0, flip_h=True, flip_v=False)
    if mirror:          return dict(rot=0, flip_h=False, flip_v=True)
    return dict(rot=180 if r180 else 0, flip_h=False, flip_v=False)

def piece_records(d, lo, hi):
    """Section 14: one record per (piece, size) the marker can place [V].
    `[10-byte prefix][f64 area][f64 perimeter][u16 3][u16 1][u16 len]
    [8 x 0]<piece name><cut description><size>G\\0<per-point attribute
    stream>`. Records of the same piece differ only in the size label and a
    trailing counter (2303-BD 137), so the stream is a per-piece attribute
    table, not geometry."""
    out = []
    for m in re.finditer(rb'[A-Za-z0-9][ -~]{5,}\x00', d[lo:hi]):
        o = lo + m.start()
        if o < lo+30 or d[o-8:o] != b'\x00'*8: continue
        area, perim = f64(d, o-30), f64(d, o-22)
        if not (0.0 < area < 1e5 and 0.0 < perim < 1e5): continue
        out.append(dict(offset=o, text=m.group()[:-1].decode('latin1'), area=area,
                        perimeter=perim, prefix=[u16(d, o-40+2*k) for k in range(5)],
                        stream_len=u16(d, o-10)))
    return out

RECORD_HEAD = 48    # bytes from a section-14 record's start to its label text

def piece_records_indexed(d, lo, hi, index):
    """Section 14 walked from section 13's index instead of by regex (v4.1).
    Section 13 is a u32 array of the records' byte offsets, relative to 6 bytes
    before section 14's directory offset, and the label text starts 48 bytes
    into each record [V: 18 of 18 corpus markers; identical - offset, text,
    area, perimeter, prefix, stream_len - to `piece_records` on every one]. The
    walk needs no printable-string heuristic and cannot skip or invent a
    record, and it fixes record ORDER, which the slot heads index into.
    -> the record list, or None when any entry does not validate (the caller
    then falls back to the regex reader)."""
    out = []
    for off in index:
        o = lo - 6 + off + RECORD_HEAD
        if o < lo + 30 or o >= hi: return None
        end = d.find(b'\x00', o, hi)
        if end <= o: return None
        area, perim = f64(d, o-30), f64(d, o-22)
        if not (0.0 < area < 1e5 and 0.0 < perim < 1e5): return None
        out.append(dict(offset=o, text=d[o:end].decode('latin1'), area=area, perimeter=perim,
                        prefix=[u16(d, o-40+2*k) for k in range(5)], stream_len=u16(d, o-10)))
    return out

def declared_piece_names(d):
    """The `-PDSTEXT-` label table names every placed piece [V] - exactly the
    strings the drawn-marker DXF labels use (dxfparser)."""
    names = []
    for m in re.finditer(rb'-PDSTEXT-', d):
        s = d[m.end()+3:m.end()+131].decode('latin1')
        s = re.split(r'[^\x20-\x7e]', s)[0].strip()
        if s and s not in names: names.append(s)
    return names

def split_record(text, names, size_vocab=()):
    """-> (piece name, cut description, size) for a section-14 record text,
    given the declared piece names and (optionally) the piece's size
    vocabulary. Within one marker the cut count never changes between sizes
    (domain rule, dxfparser 2026-08-02) - callers resolving a whole piece at
    once should prefer `sizes_for_piece`."""
    hits = [n for n in names if text.startswith(n)]
    if not hits: return None, None, None
    name = max(hits, key=len)
    tail = text[len(name):]
    if tail.endswith('G'): tail = tail[:-1]
    best = None
    for s in size_vocab:
        if s and tail.endswith(s) and (best is None or len(s) > len(best)): best = s
    if best is None:
        m = re.match(r'^(.*?)(\d{1,2}[A-Z]{0,3})$', tail)
        return name, (m.group(1) if m else tail), (m.group(2) if m else None)
    return name, tail[:-len(best)], best

def sizes_for_piece(texts, name, size_vocab):
    """Resolve every record of one piece together: the one description that
    explains all of them wins (`CUT 1` + `8` beats `CUT ` + `18`)."""
    common = None
    for t in texts:
        tail = t[len(name):]
        if tail.endswith('G'): tail = tail[:-1]
        here = {tail[:-len(s)] for s in size_vocab if s and tail.endswith(s)}
        if here: common = here if common is None else (common & here)
    desc = next(iter(common)) if common and len(common) == 1 else None
    out = {}
    for t in texts:
        if desc is not None:
            tail = t[len(name):]
            if tail.endswith('G'): tail = tail[:-1]
            cand = tail[len(desc):] if tail.startswith(desc) else None
            out[t] = (desc, cand) if cand in size_vocab else split_record(t, [name], size_vocab)[1:]
        else:
            out[t] = split_record(t, [name], size_vocab)[1:]
    return out

PIECE_LIST_HEAD = 28      # section 10's own header: 22 bytes, then the label 'MARKER'

def _walk_piece_list(d, lo, hi):
    """-> (rows, offset where the walk ended, where it must end, header ok).

    Section 10 is a 28-byte header ending in the string `MARKER`, then one
    row per piece, contiguous, closing exactly 6 bytes before section 11's
    offset (the same `-6` convention as sections 11-13) [V: 18 of 18 corpus
    markers, both vintages]:

        <u16 name length> <u16 category length> <24 flag bytes> <name>
        <category> <fabric types: u16 count at flag byte 18, then that many
        <u16 length><text>>

    Flag byte 4 (u16) is a 1-based index into section 6's block-buffer table,
    0xffff for none [V: 18 of 18]; the other flag bytes stay raw."""
    rows = []; stop = min(hi - 6, len(d))
    head_ok = d[lo+22:lo+PIECE_LIST_HEAD] == b'MARKER'
    pos = lo + PIECE_LIST_HEAD
    while head_ok and pos + 28 <= stop:
        n1, n2 = u16(d, pos), u16(d, pos+2)
        if n1 < 1 or pos + 28 + n1 + n2 > stop: break
        name = d[pos+28:pos+28+n1]; cat = d[pos+28+n1:pos+28+n1+n2]
        if not (_printable(name) and _printable(cat)): break
        p = pos + 28 + n1 + n2; fabric_types = []; ok = True
        for _ in range(u16(d, pos+22)):
            if p + 2 > stop: ok = False; break
            n = u16(d, p)
            if p + 2 + n > stop or not _printable(d[p+2:p+2+n]): ok = False; break
            fabric_types.append(d[p+2:p+2+n].decode('latin1')); p += 2 + n
        if not ok: break
        buf = u16(d, pos+8)
        rows.append(dict(offset=pos+28, name=name.decode('latin1'), fabric=cat.decode('latin1'),
                         flag=fabric_types[0] if fabric_types else '', fabric_types=fabric_types,
                         buffer_index=None if buf == 0xffff else buf, raw=d[pos+4:pos+28].hex(),
                         flag14=u16(d, pos+18)))
        pos = p
    return rows, pos, stop, head_ok

def _parse_pieces_regex(d, lo, hi):
    """The pre-v4.1 reader, kept as the fallback for a section 10 whose header
    is not the known one: per piece `<name><fabric code>\\x01\\x00<flag>`."""
    out = []
    for m in re.finditer(rb'([\x20-\x7e]{8,})\x01\x00([A-Z])', d[lo:hi]):
        o = lo + m.start(); s = m.group(1).decode('latin1')
        n1, n2 = u16(d, o-28), u16(d, o-26)     # lengths lead the 24 flag bytes
        if n1 + n2 == len(s): name, fabric = s[:n1], s[n1:]
        else: name, fabric = s, ''
        out.append(dict(offset=o, name=name, fabric=fabric, flag=chr(m.group(2)[0]),
                        raw=d[o-24:o].hex()))
    return out

def parse_pieces_section(d, lo, hi):
    """Section 10: the piece list, one row per piece the marker lays [V]. Keys
    `name`, `fabric` (the category text), `flag` (the first fabric type - AccuMark's
    'Fabric Type' role, A/B/C/D/G/M...) and `raw` are the pre-v4.1 shape;
    `fabric_types` (every type, e.g. LADIES-BLOUSE's collar is M and F) and
    `buffer_index` are new. v4.1: read as the chain it is (_walk_piece_list),
    which also reads the pieces of every CLAUDE-* marker - the old regex needed
    one fabric type and returned [] for a piece with none."""
    rows, _, _, head_ok = _walk_piece_list(d, lo, hi)
    return rows if head_ok and rows else _parse_pieces_regex(d, lo, hi)

def _printable(b):
    return all(32 <= c < 127 for c in b)

MODEL_HEAD = 48
BUFFER_ENTRY = 102

def _walk_order_copy(d, lo, hi):
    """-> ([model block, ...], offset where the walk ended, where it must end).

    Section 15 is the marker's own copy of the ORDER: what is to be cut, per
    model per size, with the quantity. A chain of model blocks starting 6 bytes
    before the directory offset and closing exactly 6 bytes before section
    21's [V: 18 of 18 corpus markers, both vintages]:

        model block = <48-byte header> <name> <fabric types> <size rows>
        header      u16 name length @+0, u16 model ordinal (1-based) @+8,
                    u16 size count @+12, u16 fabric-type count @+14; the other
                    header bytes stay raw
        fabric type <u16 length><text>
        size row    <u16 name length><u16 QUANTITY><24 zero bytes><size name>

    The model names equal section 11's; the QUANTITY equals the number of size-
    table (section 12) rows for that (model, size) - each cut of a size is its
    own row and bundle - and the (model, size) pairs cover the size table
    exactly, on all 18 markers."""
    out = []; pos = lo - 6; stop = min(hi - 6, len(d))
    while pos >= 0 and pos + MODEL_HEAD <= stop:
        n, n_sizes, n_ft = u16(d, pos), u16(d, pos+12), u16(d, pos+14)
        if n < 1 or pos + MODEL_HEAD + n > stop or not _printable(d[pos+MODEL_HEAD:pos+MODEL_HEAD+n]): break
        name = d[pos+MODEL_HEAD:pos+MODEL_HEAD+n].decode('latin1'); p = pos + MODEL_HEAD + n
        fabric_types = []; sizes = []; ok = True
        for _ in range(n_ft):
            if p + 2 > stop: ok = False; break
            m = u16(d, p)
            if p + 2 + m > stop or not _printable(d[p+2:p+2+m]): ok = False; break
            fabric_types.append(d[p+2:p+2+m].decode('latin1')); p += 2 + m
        for _ in range(n_sizes if ok else 0):
            if p + 28 > stop: ok = False; break
            m, q = u16(d, p), u16(d, p+2)
            if p + 28 + m > stop or not _printable(d[p+28:p+28+m]): ok = False; break
            sizes.append(dict(size=d[p+28:p+28+m].decode('latin1'), quantity=q)); p += 28 + m
        if not ok: break
        out.append(dict(name=name, ordinal=u16(d, pos+8), fabric_types=fabric_types, sizes=sizes,
                        header=d[pos:pos+MODEL_HEAD].hex()))
        pos = p
    return out, pos, stop

def parse_order_copy(d, lo, hi):
    """Section 15 -> [{name, ordinal, fabric_types, sizes: [{size, quantity}]}],
    one per model, in the order of section 11's model list (v4.2)."""
    return _walk_order_copy(d, lo, hi)[0]

def parse_block_buffers(d, lo, hi):
    """Section 6 -> [{index, sides}] - the marker's block-buffer table, present
    only on some markers (1825D, 418T, July CP 150, the ZZC / ZZN scratch
    markers; not 2303 Sept, 5683D, 2591A, CLAUDE-*). Entries of 102 bytes from 6
    bytes before the directory offset: `<u16 0><4 x f64 buffer in inches><68 zero
    bytes>` [V framing, 13 markers].

    v4.5: the table is a list of buffer DEFINITIONS. A piece row's `buffer_index`
    (section 10, flag bytes 4..5) is a 0-based index into it, or None (0xffff)
    for a piece with no buffer [V]. Where every piece has its own definition the
    table has `pieces + 1` entries and piece k points at k (1825D, 418T, CP 150,
    ZZC-BIG); ZZC-M1..M3 / ZZN-F1 have 4 entries for 5 pieces, one of them
    unequal ([0.7874, 0.1968, 0, 0]) and one piece with none. (The earlier
    reading - `pieces + 1` entries, entry k = piece k's, entry 0 a marker-wide
    default - was an over-fit to the small corpus.) Which side each double is
    [?]. It is NOT what sets the home box: the same pieces have byte-identical
    home boxes under different tables (ZZC-M1 vs ZZC-BIG)."""
    out = []; pos = lo - 6; stop = min(hi - 6, len(d))
    if pos < 0: return out
    while pos + BUFFER_ENTRY <= stop:
        out.append(dict(index=len(out), sides=[f64(d, pos+2+8*j) for j in range(4)]))
        pos += BUFFER_ENTRY
    return out

SIZE_HDR = 14

def _walk_model_list(d, lo, hi):
    """-> ([model name, ...], offset where the walk ended). `lo`/`hi` are
    section 11's directory span; the chain starts 6 bytes before `lo` (the
    directory offset lands 4 bytes into the first name, 6 past its length)."""
    out = []; pos = lo - 6; stop = min(hi - 6, len(d))
    if pos < 0: return out, pos
    while pos + 2 <= stop:
        n = u16(d, pos)
        if n < 1 or pos + 2 + n > stop or not _printable(d[pos+2:pos+2+n]): break
        out.append(d[pos+2:pos+2+n].decode('latin1')); pos += 2 + n
    return out, pos

def parse_model_list(d, lo, hi):
    """Section 11: the marker's model list, `<u16 length><name>` per model, in
    the order section 12's `model_index` indexes (0-based) [V: 15 of 15 corpus
    markers - the chain closes exactly where the size table's first row
    starts, and on the 2303 markers every name is a model object bundled in
    the same ZIP].

    v4: replaces a reading that took the u16 to be a length AFTER the text
    (`<chars><u16 len>`). That only works while consecutive names happen to
    have equal lengths, so it dropped 3 of the 11 models on 2303-BD 137 and 2
    of 11 on the CP 150 markers, and returned NOTHING on every single-model
    marker (the u16 after the only name is not a length)."""
    return _walk_model_list(d, lo, hi)[0]

def _walk_size_table(d, lo, hi):
    """-> ([row, ...], offset where the walk ended); see parse_sizes_section."""
    out = []; pos = lo - 6; stop = min(hi - 6, len(d))
    if pos < 0: return out, pos
    while pos + SIZE_HDR <= stop:
        n = u16(d, pos); name = d[pos+SIZE_HDR:pos+SIZE_HDR+n]
        if n < 1 or pos + SIZE_HDR + n > stop or not _printable(name): break
        out.append(dict(size=name.decode('latin1'), model_index=u16(d, pos+2), n=u16(d, pos+4),
                        ordinal=u32(d, pos+6), flags=u32(d, pos+10)))
        pos += SIZE_HDR + n
    return out, pos

def parse_sizes_section(d, lo, hi):
    """Section 12: the size table, one row per (model, size) line of the
    order. Each row is a 14-byte descriptor followed by its name [V: 15 of 15
    corpus markers, both export vintages]:

        <u16 name length> <u16 model index (0-based, into the model list)>
        <u16 pieces> <u32 first slot> <u32 flags> <size name>

    `pieces` is how many section-21 placement slots the row owns and `first
    slot` the index of the first of them, so the rows tile the slot table:
    sum(pieces) == len(slots) and first slot == running sum of pieces, on
    every marker checked (97/97 on 2303-BD 137, 72/72 on the CP 150 markers,
    27/27 on 1825D-BD 180). `flags` is 0xffff on the 2303 / CLAUDE / AD1234
    markers and 0 on LADIES-BLOUSE and the 1825D samples [?]. The directory
    offset lands on the `first slot` field, 6 bytes into the first
    descriptor, and the table ends exactly 6 bytes before section 13's offset
    (where that section's u32 array starts), hence the walk from lo - 6.

    v4: replaces a regex that (a) only knew names shaped like
    `\\d{1,2}[A-Z]{0,3}`, so `2-3`, `11-12`, `XS`, `M`, `XL` were never found
    (AD1234, LADIES-BLOUSE and both 1825D markers returned no sizes at all),
    and (b) read the fields AFTER each name, i.e. the NEXT row's descriptor.
    That is why `f0` looked like an unexplained 1/3/4 - read after a name it
    is the next name's length; it is simply each row's own name length - and
    why the model index looked 1-based (it was the following row's 0-based
    index). Size names are unchanged on every marker the old regex could
    read."""
    return _walk_size_table(d, lo, hi)[0]

def parse_slots(d, lo, hi):
    """Section 21: contiguous 96-byte placement slots [V] (dxfparser layout).

    v4.1: every slot also carries its 6-byte HEAD, which sits just BEFORE the
    body (inside the previous slot's last six bytes - the '@90/@92/@94' triple
    earlier notes read as a circular pointer is simply the NEXT slot's head):
    `<u16 record index (0-based, section 14 order)> <u16 piece index (1-based,
    section 10)> <u16 bundle>` [V: 677 of 677 slots on 18 markers - the record's
    declared area matches the slot's, the piece's name starts the record text,
    and the bundle equals both the slot's own bundle and its size-table row]."""
    out = []
    for i, s in enumerate(range(lo, hi-SLOT+1, SLOT)):
        px, py, hx, hy = struct.unpack_from('<dddd', d, s)
        h = s - SLOT_HEAD
        head = (u16(d, h), u16(d, h+2), u16(d, h+4)) if h >= 0 else (None, None, None)
        out.append(dict(slot=s, index=i, x=px, y=py, home_x=hx, home_y=hy,
                        orient_code=u16(d, s+32), area=f64(d, s+42),
                        bundle=u32(d, s+64) & 0xffff, bundle_flags=u32(d, s+64) >> 16,
                        record_index=head[0], piece_index=head[1], bundle_head=head[2],
                        sig88=u16(d, s+88),
                        raw=d[s:s+SLOT].hex(), **decode_orient(u16(d, s+32))))
    return out

def parse_marker(d, size_vocab=None, binding='structural'):
    """Everything readable in a marker object. `size_vocab` = {piece name:
    [size names]} from the piece objects of the same ZIP, used to split the
    record strings; a piece it does not cover is split against the marker's
    own size table (v4), and only a marker with neither falls back to a
    pattern.

    `binding` (v4.1): 'structural' (default) binds each slot to its (piece,
    size, model, record) from the slot head, the size-table tiling and
    section 10 - see _bind_structural - and uses the declared area only for
    slots that cannot be bound that way; 'area' is the pre-v4.1 rule alone,
    kept so a change can be diffed against it."""
    obj = read_object(d)
    if obj['type'] != 9: raise WrongObjectType('not a marker object', got=obj['type'], want=9)
    dirs = directory(d)
    sec = {k: _section(d, dirs, k) for k in range(DIR_SLOTS)}
    mk = dict(name=obj['name'], object=obj, directory=dirs, sections=sec,
              width=f64(d, 396), length=f64(d, 412), total_area=f64(d, 422),
              util=f64(d, 446), unknown_454=f64(d, 454))
    mk['laid'] = mk['length'] > 0 and mk['util'] > 0
    mk['piece_names'] = declared_piece_names(d)
    mk['pieces'] = parse_pieces_section(d, *sec[SEC_PIECES]) if sec[SEC_PIECES] else []
    # v4: sections 11 and 12 are one length-prefixed chain - see
    # parse_model_list / parse_sizes_section. table_ends = (where each walk
    # stopped, where the directory says it must) for check_marker.
    models, m_end = _walk_model_list(d, *sec[SEC_MODELS]) if sec[SEC_MODELS] else ([], None)
    sizes, s_end = _walk_size_table(d, *sec[SEC_SIZES]) if sec[SEC_SIZES] else ([], None)
    mk['models'], mk['sizes'] = models, sizes
    for r in mk['sizes']:
        r['model'] = mk['models'][r['model_index']] if r['model_index'] < len(mk['models']) else None
    mk['table_ends'] = (dict(models=(m_end, sec[SEC_SIZES][0]-6), sizes=(s_end, sec[SEC_SIZES][1]-6))
                        if sec[SEC_MODELS] and sec[SEC_SIZES] else None)
    # v4.1: whether section 10's chain closed where the directory says it must
    walked = _walk_piece_list(d, *sec[SEC_PIECES]) if sec[SEC_PIECES] else None
    mk['piece_list_end'] = (walked[1], walked[2]) if walked and walked[3] and walked[0] else None
    # section 13: u32 byte offsets of the section-14 records, relative to 6 bytes
    # before section 14's directory offset (66 values for 66 records on
    # 2303-BD 137; consecutive differences are the record lengths) [V: 18 of 18]
    mk['record_index'] = []
    if sec[SEC_INDEX] and sec[SEC_RECORDS]:
        n = (sec[SEC_INDEX][1] - sec[SEC_INDEX][0]) // 4
        vals = [u32(d, sec[SEC_INDEX][0]-6+4*k) for k in range(n)]
        if vals and all(vals[k] < vals[k+1] for k in range(len(vals)-1)): mk['record_index'] = vals
    # v4.1: the records are walked from that index (exact, and it fixes their
    # ORDER, which the slot heads index into); the regex reader is the fallback
    # for a marker whose index is missing or does not validate
    walked_records = (piece_records_indexed(d, *sec[SEC_RECORDS], mk['record_index'])
                      if mk['record_index'] and sec[SEC_RECORDS] else None)
    mk['records_source'] = 'index' if walked_records is not None else 'regex'
    mk['records'] = (walked_records if walked_records is not None else
                     piece_records(d, *sec[SEC_RECORDS]) if sec[SEC_RECORDS] else [])
    mk['slots'] = parse_slots(d, *sec[SEC_SLOTS]) if sec[SEC_SLOTS] else []
    mk['placed_word'] = dirs[40] & 0xffff       # 0 / 1 / 2 = none / some / all slots placed [V: 18/18]
    # split every record text: piece / cut description / size. The names come
    # from the -PDSTEXT- label scan AND section 10's own list (v4.1: the scan
    # finds nothing on LADIES-BLOUSE, so all 20 of its records went unsplit)
    split_names = list(dict.fromkeys(mk['piece_names'] + [p['name'] for p in mk['pieces']]))
    by_piece = {}
    for r in mk['records']:
        name, _, _ = split_record(r['text'], split_names)
        r['piece'] = name
        # a record whose text matches no declared piece name never enters
        # by_piece below, so it never gets 'cut'/'size' set there - default
        # them here so a slot binding to this record (by area) doesn't KeyError
        r['cut'] = None; r['size'] = None
        if name: by_piece.setdefault(name, []).append(r)
    # v4: a piece whose own size table is not in `size_vocab` (its piece object
    # is not in the ZIP) is split against the marker's OWN size names instead
    # of by pattern - the pattern cannot tell `CUT X 01` + `2-3` from
    # `CUT X 012-` + `3` (both 1825D markers came out 0/36 right before)
    own_vocab = list(dict.fromkeys(r['size'] for r in mk['sizes']))
    for name, recs in by_piece.items():
        vocab = (size_vocab or {}).get(name) or own_vocab
        res = sizes_for_piece([r['text'] for r in recs], name, vocab) if vocab else {}
        for r in recs:
            desc, size = res.get(r['text']) or split_record(r['text'], [name], vocab)[1:]
            r['cut'] = desc; r['size'] = size
    for s in mk['slots']:
        s['empty'] = (abs(s['x']) < 1e-9 and abs(s['y']) < 1e-9) or s['x'] < -900
    if binding == 'structural': _bind_structural(mk)
    _bind_by_area(mk, only_unbound=(binding == 'structural'))
    placements = [s for s in mk['slots'] if not s['empty']]
    mk['placements'] = placements
    mk['bundles'] = sorted({p['bundle'] for p in placements})
    mk['sum_slot_areas'] = sum(p['area'] for p in placements)
    _add_order_and_state(d, mk, sec)
    mk['tables'] = parse_marker_tables(d, sec, mk['name'])
    return mk

TABLE_LENS = (('marker_name', -4), ('customer', -2), ('order_name', 0), ('reference', 2), ('lay_limits', 4), ('annotation', 6), ('block_buffer', 8),
              ('reserved_10', 10), ('notch_table', 12), ('reserved_14', 14), ('extra', 18))
TABLE_STRINGS = 231     # the name strings start this far into section 2, one after the other, no separators

def parse_marker_tables(d, sec, name=None):
    """v4.8: section 2 ends with the NAMES of the tables the marker was made with. Eleven u16 lengths sit at section start -4, -2, 0, 2, 4, 6, 8, 10, 12, 14
    and 18; the strings follow in that order from section start + 231, without separators. Verified on all 44 markers of the corpus (every vintage): the
    first string is the marker's own name (43 of 44; the 44th is a marker copied without renaming) and `lay_limits` / `annotation` / `block_buffer` /
    `notch_table` equal the names of the type 6 / 2 / 3 / 17 objects bundled next to the marker. -> dict of names, plus `ok` (strings printable and inside
    the section), or None when the marker has no section 2."""
    s2 = sec[2] if len(sec) > 2 else None
    if not s2: return None
    a = s2[0]
    try: lens = [u16(d, a + o) for _, o in TABLE_LENS]
    except struct.error: return None
    pos = a + TABLE_STRINGS; out = {}
    ok = pos + sum(lens) <= s2[1]
    for (k, _), n in zip(TABLE_LENS, lens):
        raw = d[pos:pos + n] if ok else b''
        if not all(32 <= c < 127 for c in raw): ok = False
        out[k] = raw.decode('latin1'); pos += n
    out['ok'] = ok
    out['name_matches'] = name is None or out['marker_name'] == name
    return out

def _add_order_and_state(d, mk, sec):
    """v4.2: the order copy (section 15), the block buffers (section 6), where
    the marker stands (laid state) and how the header's two sums relate to its
    slots. Everything here is additive - no v4.1 key changes."""
    mk['order_copy'] = []; mk['order_copy_end'] = None
    if sec[SEC_ORDER_COPY] and sec[SEC_SLOTS]:
        models, end, stop = _walk_order_copy(d, sec[SEC_ORDER_COPY][0], sec[SEC_SLOTS][0])
        mk['order_copy'] = models; mk['order_copy_end'] = (end, stop) if models else None
    mk['block_buffers'] = parse_block_buffers(d, *sec[SEC_BUFFERS]) if sec[SEC_BUFFERS] else []
    for i, p in enumerate(mk['pieces']):
        bi = p.get('buffer_index')
        p['buffer_ok'] = (bi is None or 0 <= bi < len(mk['block_buffers'])) if mk['block_buffers'] else None
    # header double @430 = the summed declared area of the PLACED slots
    # (= W x L x U / 100) [V: 18 of 18]; 0 on a marker nothing is placed on
    mk['placed_area'] = f64(d, 430)
    # laid state, from three independent sources: directory word 40, the slot
    # coordinates, and the header's own length / utilisation. The slots are
    # authoritative (they are what a nesting run consumes); the others must agree
    n, k = len(mk['slots']), len(mk['placements'])
    by_slots = 'unlaid' if k == 0 else ('laid' if k == n else 'partial')
    # v4.5 (live experiment): directory word 40 is NOT a count of placed slots. It is
    # 0 on a marker as generated (Marker Wizard / AutoMark / Easy Order), 1 once Easy
    # Marking has stored it with fewer than all pieces placed - INCLUDING none at all
    # (CLAUDE-UNP-E1A: opened and stored empty reads 1) - and 2 when all are placed.
    w = mk['placed_word']
    by_word = {0: 'as_generated', 1: 'stored', 2: 'all_placed'}.get(w)
    by_header = 'unlaid' if not mk['laid'] else 'laid or partial'
    word_ok = (w == 0 and k == 0) or (w == 1 and k < n) or (w == 2 and k == n and n > 0)
    mk['laid_state'] = by_slots
    mk['laid_state_sources'] = dict(slots=by_slots, placed_word=by_word, header=by_header,
                                    agree=word_ok and ((by_header == 'unlaid') == (by_slots == 'unlaid')))
    # v4.5: slot u16 @88 is an AS-GENERATED signature, not a "never laid" one. Across
    # 61 markers it is non-zero on every slot of the 24 markers Easy Marking has never
    # stored and 0 on every slot of every marker it has (laid, part-laid, and - live,
    # CLAUDE-UNP-E1A - opened and stored with nothing placed). Laying a piece and
    # returning it leaves NO further trace (E1B differs from E1A by one 1-ulp area byte),
    # so "laid once then cleared" cannot be told from "opened and stored empty". The
    # same store also sets directory word 40 to 1, every slot's orientation bit 0x8000
    # and its centre to (-1000, -1000). Values of @88 (9, 33, 54, ...) are constant per
    # (piece, size) and unexplained [?].
    sig = [s['sig88'] for s in mk['slots']]
    mk['lay_history'] = (('as_generated' if any(sig) else 'stored_empty') if by_slots == 'unlaid' else by_slots)
    mk['header_sums'] = _header_sums(mk)
    mk['sig88_model'] = _sig88_model(mk)

def _sig88_model(mk):
    """v4.7: slot @88 is not an independent number. On an as-generated marker it is
    the bound record's OWN entry count: @88 = record head u16 @+10 (`prefix[1]`, a
    per-size count that grows with the size) + C, where C is one constant PER PIECE -
    the same on every size of that piece and on every marker that carries it (live
    corpus: 107 (marker, piece) groups over 43 markers and 31 pieces, 0 exceptions,
    the fresh twin CLAUDE-D2-M0 included). C is 4 on a piece with at most a grain
    line, 28-32 with grain + mirror lines, 216-266 with ten internal lines and 620+
    with eighteen, so it tracks the piece's INTERNAL geometry [?] exactly what it counts.
    -> dict(applicable, ok, constant={piece: C, or None when it varies})"""
    per = {}
    for s in mk['slots']:
        rc = s.get('record')
        if s['sig88'] and rc:
            per.setdefault(s.get('piece') or ('record %d' % s['record_index']), set()).add(s['sig88'] - rc['prefix'][1])
    return dict(applicable=bool(per), ok=all(len(v) == 1 for v in per.values()),
                constant={p: (next(iter(v)) if len(v) == 1 else None) for p, v in per.items()})

KNOWN_SECTIONS = frozenset({1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 14, 15, 21, 30})    # every directory slot ever seen used
KNOWN_ORIENT_BITS = ROT180_BIT | MIRROR_BIT | 0x0040                                  # what a NEVER-LAID slot's word can carry

def marker_warnings(mk):
    """v4.6: the future-proofing contract. Every way a marker can differ from
    everything the corpus has shown, named - so an unseen variant is LOUD, never
    a silently wrong answer. -> [str]; empty on all 18 fixture markers.

      an unknown directory slot in use (a section this reader has never seen)
      directory word 40 outside 0/1/2, or word 41 non-zero
      a slot of an AS-GENERATED marker (never stored by Easy Marking) whose
        orientation word carries bits outside rot180 / mirror / the 0x0040 bit
        (true of none of them). Not applied once Easy Marking has stored the
        marker: a store sets 0x8000 on every slot (and 0x0004 beside a rot180
        preset), so a stored marker's `preset` is not a clean pre-set pattern -
        on the July CP 150 markers 61 of 71 unplaced slots carry 0x80c7
      the record index missing, so the records came from the regex fallback
      slots the structure could not bind (the area rule filled in, or none)
      a section chain that does not close where the directory says

    The check_marker rows already fail for most of these; this list is what a
    consumer reads without running them, and unplaced_inventory folds it in."""
    w = []
    for k, v in enumerate(mk['directory'][:DIR_OFFSETS]):
        if v not in (0, 0xffffffff) and k not in KNOWN_SECTIONS:
            w.append('directory slot %d is in use but this reader has never seen that section' % k)
    if mk['placed_word'] not in (0, 1, 2): w.append('directory word 40 is %d, expected 0 / 1 / 2' % mk['placed_word'])
    if mk['directory'][41] != 0: w.append('directory word 41 is %#x, expected 0' % mk['directory'][41])
    odd = [s['index'] for s in mk['slots'] if s['orient_code'] & ~KNOWN_ORIENT_BITS] if mk['lay_history'] == 'as_generated' else []
    if odd: w.append('%d slots of an as-generated marker carry orientation bits outside rot180 / mirror / pair (first: slot %d, word %#06x)'
                     % (len(odd), odd[0], mk['slots'][odd[0]]['orient_code']))
    if mk['sections'][SEC_INDEX] and mk.get('records_source') != 'index':
        w.append('section 13 (record index) did not validate: records were read by the fallback regex')
    n_bad = sum(1 for s in mk['slots'] if (s.get('binding') or {}).get('method') != 'structural')
    if n_bad: w.append('%d of %d slots are not bound structurally' % (n_bad, len(mk['slots'])))
    # the cross-checks of the structural binding: a record or slot read at the
    # wrong offset still parses, and only these notice (a first index entry shifted
    # by one byte gave a plausible record with a garbage area on 5683D)
    bind = [s.get('binding') or {} for s in mk['slots'] if (s.get('binding') or {}).get('method') == 'structural']
    n_area = sum(1 for x in bind if not x.get('area_ok'))
    if n_area: w.append("%d slots: the declared area does not equal the bound record's (a record or slot read at the wrong offset?)" % n_area)
    n_bt = sum(1 for x in bind if x.get('bundle_ok') is False or x.get('text_ok') is False)
    if n_bt: w.append('%d slots: the bundle or the record text disagree with the size table' % n_bt)
    for label, end in (('piece list', mk.get('piece_list_end')), ('order copy', mk.get('order_copy_end'))):
        if end and end[0] != end[1]: w.append('the %s chain ends at %#x, the directory says %#x' % (label, end[0], end[1]))
    if mk['sections'][SEC_PIECES] and not mk.get('piece_list_end'):
        w.append('section 10 (piece list) is not the known chain: no header / no rows read, the regex fallback was used')
    if mk['sections'][SEC_ORDER_COPY] and not mk.get('order_copy'):
        w.append('section 15 (order copy) did not parse: no order lines can be stated from the marker itself')
    for label, (got, want) in (mk.get('table_ends') or {}).items():
        if got != want: w.append('the %s chain ends at %#x, the directory says %#x' % (label, got, want))
    sm = mk.get('sig88_model')
    if sm and sm['applicable'] and not sm['ok']:
        w.append('slot @88 is not (record head count + one constant per piece) for: ' + ', '.join(p for p, c in sm['constant'].items() if c is None))
    return w

# --- section 14 stream grammar (v4.7, see MARKER_FORMAT_SPEC.md section 8) --------------------
_STREAM_WBYTES = {0: 8, 1: 3, 2: 4, 3: 5}       # width code -> data bytes: 32 / 12 / 16 / 20 bit x,y pair
_PEN_MOVE = 6                                    # parts in one point beyond which it is a pen move (seen: 7 - 52; ordinary points have 1 - 3)

def _tag_len(t):
    """data bytes of a stream item with tag `t`: bits 6-5 pick the pair width, a CLEAR bit 4
    adds one leading extra byte (meaning open [?]); bit 7 marks the main (last) part."""
    return _STREAM_WBYTES[(t >> 5) & 3] + (0 if t & 0x10 else 1)

def _tag_delta(t, dat):
    w = (t >> 5) & 3
    if not t & 0x10: dat = dat[1:]
    def sg(v, bits): return v - (1 << bits) if v >= 1 << (bits - 1) else v
    if w == 1: return sg(dat[1] | (dat[0] >> 4) << 8, 12), sg(dat[2] | (dat[0] & 15) << 8, 12)
    if w == 2: return sg(u16(dat, 0), 16), sg(u16(dat, 2), 16)
    if w == 3: return sg(u16(dat, 0) | (dat[4] >> 4) << 16, 20), sg(u16(dat, 2) | (dat[4] & 15) << 16, 20)
    return int.from_bytes(dat[:4], 'little', signed=True), int.from_bytes(dat[4:8], 'little', signed=True)

def decode_record_stream(st, pen_move=None):
    """v4.7 [V, partial]: a section-14 record's stream as CONTOURS of (x, y, id) points in
    1e-4 in - the piece's graded outline first, then internal lines. Grammar:

        00 02 00                                   3-byte lead
        [<ASCII tag> 00 <n> 00]*                   header records (S 0x53 seam, M 0x4d mirror,
                                                   F G I H ... : contour kinds and point counts [?])
        point items                                each = prefix parts + one main part + u16 id
        <attribute bytes> <3 bytes>                trailer, first byte 0x09 / 0x01

    A part is `<tag> <data>`. Tag: bit 7 = main (last part of the item), bits 6-5 = width code
    (0: two i32, 1: 12-bit x,y as byte x_hi<<4|y_hi, x lo8, y lo8, 2: two i16, 3: 20-bit x,y as x lo16,
    y lo16, byte x_hi<<4|y_hi), bit 4 CLEAR = one leading extra byte (open [?]). A point's step is the
    SUM of its parts; the first point of a contour is absolute. A prefix with low nibble 0xa CLOSES the
    contour (returns to its start) and its main part is the absolute start of the next contour; tag
    0x00 starts a contour with an absolute 20-bit pair. Nothing is guessed: an unknown situation stops
    the decode and says so.
    -> dict(contours=[[(x, y, id)]], header=[(tag, n)], end, stop, size)"""
    if len(st) < 3: return dict(contours=[], header=[], end=0, stop='short', size=len(st))
    p = 3; header = []; spans = [(0, 3, 'lead')]
    while p + 4 <= len(st) and st[p] < 0x80 and st[p+1] == 0 and st[p+3] == 0:
        header.append((st[p], st[p+2])); spans.append((p, p + 4, 'header')); p += 4
    contours = []; kinds = []; raws = []; cur = None; ck = None; cr = None; x = y = 0; stop = 'end'
    while p < len(st):
        parts = []; q = p; ok = True
        while True:
            if q >= len(st): ok = False; stop = 'truncated at byte %d' % p; break
            t = st[q]
            if t == 0x00 and not parts:                       # a new contour: absolute 20-bit pair, no tag class
                if q + 6 > len(st): ok = False; stop = 'truncated at byte %d' % p; break
                parts.append((0xf8, st[q+1:q+6])); spans += [(q, q + 1, 'tag'), (q + 1, q + 6, 'data')]; q += 6; break
            if t < 0x10 and not t & 0x70:                     # 0x09 ...: the trailer's attribute bytes
                ok = False; stop = 'trailer'; break
            n = _tag_len(t)
            if q + 1 + n > len(st): ok = False; stop = 'truncated at byte %d' % p; break
            parts.append((t, st[q+1:q+1+n])); spans.append((q, q + 1, 'tag'))
            if not t & 0x10: spans.append((q + 1, q + 2, 'extra'))
            spans.append((q + 1 + (0 if t & 0x10 else 1), q + 1 + n, 'data')); q += 1 + n
            if t & 0x80: break
        if not ok: break
        if q + 2 > len(st): stop = 'truncated at byte %d' % p; break
        spans.append((q, q + 2, 'id'))
        dx = dy = 0
        for t, dat in parts:
            a, b = _tag_delta(t, dat); dx += a; dy += b
        mx, my = _tag_delta(*parts[-1])          # the MAIN part alone: a contour's absolute start (the prefix parts of a contour-start item
                                                 # are not a movement - 2303 OUMO-1: six prefixes, then the absolute point)
        if len(parts) > (_PEN_MOVE if pen_move is None else pen_move) and cur is not None:         # a long chain of parts = a pen move / contour start
            x, y = mx, my; cur = []; ck = []; cr = []; contours.append(cur); kinds.append(ck); raws.append(cr)
        elif any((t & 0xf) == 0xa for t, _ in parts[:-1]):
            x, y = mx, my; cur = []; ck = []; cr = []; contours.append(cur); kinds.append(ck); raws.append(cr)
        elif cur is None or st[p] == 0x00:
            x, y = dx, dy; cur = []; ck = []; cr = []; contours.append(cur); kinds.append(ck); raws.append(cr)
        else:
            x += dx; y += dy
        cur.append((x, y, u16(st, q))); cr.append((dx, dy, mx, my))
        # the point's KIND: main tag low nibble 1 = plain (or a NOTCH when an extra byte follows: type = its low nibble,
        # high nibble = a flag); any other low nibble = a TURN (corner point), with a notch type in the extra byte for a
        # corner notch [V 7,208 of 7,209 piece points]
        ex_ = [dat[0] for t, dat in parts if not t & 0x10]
        if parts[-1][0] & 0xf == 1: ck.append(('notch', ex_[-1] & 15) if ex_ else ('plain', None))
        else: ck.append(('turn', (ex_[-1] & 15) or None) if ex_ else ('turn', None))
        p = q + 2
    if stop == 'end': stop = 'trailer'
    # v4.7 (blind tests CLAUDE-D4 and D3): after the perimeter the stream holds the piece's OTHER lines back to back, each contour
    # starting with an ABSOLUTE point that carries no marker of its own. The order (verified against the piece objects of
    # CLAUDE-D4, ID1005 - BACK / FRONT and the 2303 pieces):
    #     perimeter (the CUT line; a fold piece stores ONE HALF)
    #     grain line            2 points - implicit unless the header has a `G`
    #     one contour per header record I (internal line) / H (cutout) / D (drill) / G (grain), `n` points each
    #     the SEW line          a fold piece with seam allowance: the stitch half, as many points as are left over
    #     the mirror line       2 points (`M`) - a fold piece
    # Split only when the arithmetic closes exactly (the points left over = the counts, with a sew half of at least 3 points when the
    # header has S records); F and other records keep the plain split.
    labels = ['perimeter'] + ['other'] * max(0, len(contours) - 1)
    hl = [chr(t) for t, _ in header]
    if len(contours) >= 2 and all(c in 'IHDG!SM' for c in hl):
        lines = [(n, {'I': 'internal', 'H': 'cutout', 'D': 'drill', 'G': 'grain'}[chr(t)]) for t, n in header if chr(t) in 'IHDG']
        plan = ([] if 'G' in hl else [(2, 'grain')]) + lines
        tail = [(2, 'mirror')] if 'M' in hl else []
        flat = [r for cr_ in raws[1:] for r in cr_]; ids = [pt[2] for c_ in contours[1:] for pt in c_]
        left = len(flat) - sum(n for n, _ in plan) - sum(n for n, _ in tail)
        if 'S' in hl:
            # the sew half exists only in the verified fold layout: two S records around an M
            plan = plan + ([(left, 'sew')] if left >= 3 and hl.count('S') == 2 and 'M' in hl else [(-1, 'bad')])
        elif left != 0: plan = [(-1, 'bad')]
        plan = plan + tail
        if all(n >= 0 for n, _ in plan):
            nc = [contours[0]]; nk = [kinds[0]]; labels = ['perimeter']; i0 = 0
            for c_, nm in plan:
                pts = []; xx = yy = 0
                for j in range(c_):
                    sx, sy, mx_, my_ = flat[i0 + j]
                    xx, yy = (mx_, my_) if j == 0 else (xx + sx, yy + sy)
                    pts.append((xx, yy, ids[i0 + j]))
                nc.append(pts); nk.append([('turn', None)] * c_); labels.append(nm); i0 += c_
            # a fold piece must close geometrically: the cut half's and the sew half's first / last points lie ON the mirror line. The
            # newer streams do (BACK, FRONT, the 2303 OUCF pieces, the blouse); the 1825D / 5683D / 2591A / 418T vintage lays these
            # lines out differently (id 0 items, other chains) and fails - then nothing is labelled rather than something wrong
            ok_ = True
            if 'M' in hl:
                mi = labels.index('mirror'); ma, mb = [(x_, y_) for x_, y_, _ in nc[mi]]
                dx_, dy_ = mb[0] - ma[0], mb[1] - ma[1]; ln_ = math.hypot(dx_, dy_)
                def _on(pt): return ln_ < 1 or abs((pt[0] - ma[0]) * dy_ - (pt[1] - ma[1]) * dx_) / ln_ <= 3
                chk = [nc[0][0], nc[0][-1]] + ([nc[labels.index('sew')][0], nc[labels.index('sew')][-1]] if 'sew' in labels else [])
                ok_ = all(_on(pt_[:2]) for pt_ in chk)
            if ok_: contours, kinds = nc, nk
            else: labels = ['perimeter'] + ['other'] * (len(contours) - 1)
    return dict(contours=contours, header=header, end=p, stop=stop, size=len(st), spans=spans, kinds=kinds, labels=labels)

def verify_stream_outline(contour, area, perimeter, tol=0.01):
    """polygon area / perimeter (in, sq in) of a decoded contour against the record head's own
    `area` and `perimeter`: True when both agree within `tol` (observed max 0.29% / 0.04% on 129
    corpus records; a wrong item breaks it by far more). -> (ok, area, perimeter)"""
    if len(contour) < 3: return False, 0.0, 0.0
    a = pr = 0.0
    for i, (x1, y1, _) in enumerate(contour):
        x2, y2, _ = contour[(i + 1) % len(contour)]
        a += x1 * y2 - x2 * y1; pr += math.hypot(x2 - x1, y2 - y1)
    a = abs(a) / 2e8; pr /= 1e4
    return abs(a - area) <= tol * area + 0.01 and abs(pr - perimeter) <= tol * perimeter + 0.05, a, pr

def _unfold_contour(half):
    """a fold piece's stream holds ONE HALF whose first and last point lie on the fold line; the
    full outline is that half plus its mirror image about the line, in reverse. [(x, y, id)] -> same"""
    (x0, y0), (x1, y1) = half[0][:2], half[-1][:2]
    dx, dy = x1 - x0, y1 - y0; l2 = dx * dx + dy * dy
    if not l2: return list(half)
    out = list(half)
    for x, y, _ in reversed(half[1:-1]):
        px, py = x - x0, y - y0; t = (px * dx + py * dy) / l2
        out.append((x0 + 2 * t * dx - px, y0 + 2 * t * dy - py, 0))
    return out

def record_outline(data, rec):
    """the graded outline of section-14 record `rec` read from the STREAM alone (no piece object
    needed): -> dict(points=[(x_in, y_in)], verified, unfolded, area, perimeter, other=[contours in],
    stop, header) or None. The first contour is tried as it stands, then - for a fold piece, whose
    stream holds one half - unfolded about the line through its first and last point; `verified` = the
    polygon reproduces the record head's own area and perimeter (verify_stream_outline). Checked
    against the stored home box too, which the verification never uses: bounding box == home box to
    0.000 in on all 60 foreign marker-only slots (1825D, 5683D) and 2591A / 418T."""
    o = rec['offset']; t = len(rec['text']); st = data[o+t:o+t+rec['stream_len']]
    # the split between contours is the one guess in the grammar (a chain of MORE than `pen_move` parts starts a new
    # contour: 7 parts is a legitimate long step on a BACK piece of the blind test and a real pen move on 2303, 46 on
    # ID1005 - BACK's jump to its mirror line), so try a few values and keep the first whose outline reproduces the
    # record's own area and perimeter - as is, or unfolded
    best = None
    for pm in (_PEN_MOVE, 20, 10 ** 9):
        d = decode_record_stream(st, pm)
        if not d['contours']: continue
        c0 = d['contours'][0]; k0 = list(d['kinds'][0]); unfolded = False
        ok, a, pr = verify_stream_outline(c0, rec['area'], rec['perimeter'])
        if not ok and len(c0) >= 3:
            full = _unfold_contour(c0); ok2, a2, pr2 = verify_stream_outline(full, rec['area'], rec['perimeter'])
            if ok2: c0, ok, a, pr, unfolded = full, True, a2, pr2, True; k0 = k0 + [k0[i] for i in range(len(k0) - 2, 0, -1)]
        if best is None or (ok and not best[0]): best = (ok, d, c0, k0, unfolded, a, pr, pm)
        if ok: break
    if best is None: return None
    ok, d, c0, k0, unfolded, a, pr, pm = best
    ro = dict(points=[(x / 1e4, y / 1e4) for x, y, _ in c0], verified=ok and d['stop'] == 'trailer', unfolded=unfolded,
                pen_move=pm, labels=d.get('labels'), kinds=k0,
                lines=[dict(kind=lb, points=[(x / 1e4, y / 1e4) for x, y, _ in c]) for lb, c in zip((d.get('labels') or [])[1:], d['contours'][1:]) if lb in ('grain', 'internal', 'cutout', 'drill', 'mirror')],
                sew=next(([(x / 1e4, y / 1e4) for x, y, _ in (_unfold_contour(c) if unfolded else c)] for lb, c in zip((d.get('labels') or [])[1:], d['contours'][1:]) if lb == 'sew'), None),
                notches=[(i, k[1], c0[i][0] / 1e4, c0[i][1] / 1e4) for i, k in enumerate(k0) if k[0] == 'notch'],
                area=a, perimeter=pr, other=[[(x / 1e4, y / 1e4) for x, y, _ in c] for c in d['contours'][1:]], stop=d['stop'], header=d['header'])
    # every line above came from a stream whose layout was verified against a piece object (basis 'stream'). The 1825D / 5683D / 2591A / 418T vintage
    # lays its other lines out differently and is not decoded, but its grain line is recognisable: the second contour's first two points are a
    # horizontal segment (exactly dy = 0) - 89 of 89 records, 88 of them inside the outline's box - and every one of 135 grain lines in the bundled piece
    # objects of the corpus is horizontal in the piece frame. Reported as `inferred`, never as verified.
    for l_ in ro['lines']: l_['basis'] = 'stream'
    if not any(l_['kind'] == 'grain' for l_ in ro['lines']) and len(d['contours']) >= 2 and len(d['contours'][1]) >= 2:
        (gx0, gy0, _), (gx1, gy1, _) = d['contours'][1][0], d['contours'][1][1]
        if gy0 == gy1 and gx0 != gx1: ro['lines'].append(dict(kind='grain', points=[(gx0 / 1e4, gy0 / 1e4), (gx1 / 1e4, gy1 / 1e4)], basis='inferred'))
    return ro

def _header_sums(mk):
    """How the header doubles @422 / @454 relate to the slots - a MODE per
    double, not a pass/fail: 'all' (the sum over every slot's declared area /
    record perimeter), 'last_model' (over the last model's slots only), '2x_all'
    (twice the all-slot sum) or 'other'. Observed [V]: 'all' on every marker
    nobody laid and on every single-model marker; on the multi-model 2303
    markers @454 is 'last_model' everywhere and @422 is 'last_model' in the
    unlaid export but 'all' in the laid one; LADIES-BLOUSE's @454 is '2x_all'
    [?]. The cause of the last-model behaviour is unproven."""
    slots = [s for s in mk['slots'] if s.get('record')]
    if not slots or not mk['models']: return dict(area=None, perimeter=None)
    last = mk['models'][-1]
    def mode(header, per):
        vals = {'all': sum(per(s) for s in slots), 'last_model': sum(per(s) for s in slots if s.get('model') == last),
                '2x_all': 2 * sum(per(s) for s in slots)}
        for name, v in vals.items():
            if abs(header - v) <= 1e-6 * max(1.0, abs(v)): return name
        return 'other'
    return dict(area=mode(mk['total_area'], lambda s: s['area']),
                perimeter=mode(mk['unknown_454'], lambda s: s['record']['perimeter']))

def _area_ok(s, rec):
    return abs(rec['area'] - s['area']) <= max(0.05, 1e-3*s['area'])

def _bind_by_area(mk, only_unbound=False):
    """The pre-v4.1 binding, dxfparser's rule: the record whose declared area
    is nearest the slot's (within tolerance, no rival PIECE within 10x the
    gap). It cannot tell sister sizes of one piece apart when they tie on area,
    so it is the fallback for a slot the structure could not bind, not the
    rule - on 2303-BD 137 it picked the wrong size for 77 of 97 slots."""
    for s in mk['slots']:
        if only_unbound and s.get('binding', {}).get('method') == 'structural': continue
        rec = None
        if mk['records']:
            ranked = sorted(mk['records'], key=lambda r: abs(r['area']-s['area']))
            gap = abs(ranked[0]['area']-s['area'])
            if gap <= max(0.05, 1e-3*s['area']):
                rivals = {r['piece'] for r in ranked if abs(r['area']-s['area']) <= max(gap*10, 1e-9)}
                if len(rivals) == 1: rec = ranked[0]
        s['record'] = rec
        s['piece'] = rec['piece'] if rec else None
        s['size'] = rec['size'] if rec else None
        s['model'] = None; s['row'] = None
        s['binding'] = dict(method='area' if rec else 'none', area_ok=bool(rec), bundle_ok=None, text_ok=None)

def _tile_rows(mk):
    """-> [size-row index for each slot], or None when the size table does not
    tile the slot table (then nothing can be bound structurally)."""
    rows, n = mk['sizes'], len(mk['slots'])
    if not rows or sum(r['n'] for r in rows) != n: return None
    out = []; run = 0
    for i, r in enumerate(rows):
        if r['ordinal'] != run: return None
        out += [i] * r['n']; run += r['n']
    return out

def _bind_structural(mk):
    """Bind every slot to (record, piece, size, model) from the file's own
    structure [V: 677 of 677 slots on 18 markers, DXF labels 97/97 on
    2303-BD 137 PLACED]:

      size, model   the size table's tiling of the slot table
      record        the slot head's record index (section 14 order)
      piece         the slot head's piece index (section 10, 1-based)

    The declared area, the slot's own bundle and the record text's `<size>G`
    ending are then CHECKED against that binding, per slot, in s['binding'] -
    never used to choose it. A slot that cannot be bound this way (unseen
    layout) is left for the area rule and says so in s['binding']['method']."""
    tiling = _tile_rows(mk)
    if tiling is None: return
    recs, pieces, rows = mk['records'], mk['pieces'], mk['sizes']
    for s, ri in zip(mk['slots'], tiling):
        rec_i, piece_i = s['record_index'], s['piece_index']
        if rec_i is None or not (0 <= rec_i < len(recs)): continue
        rec, row = recs[rec_i], rows[ri]
        prow = pieces[piece_i-1] if piece_i and 1 <= piece_i <= len(pieces) else None
        piece = prow['name'] if prow and rec['text'].startswith(prow['name']) else rec['piece']
        text_ok = rec['text'].endswith(row['size'] + 'G')
        s['record'], s['piece'], s['size'] = rec, piece, row['size']
        s['model'], s['row'] = row['model'], ri
        s['binding'] = dict(method='structural', area_ok=_area_ok(s, rec),
                            bundle_ok=(s['bundle'] == ri == s['bundle_head']), text_ok=text_ok)
        # the record's own size/cut are now known exactly, not guessed from text
        if text_ok and piece and rec['text'].startswith(piece):
            rec['piece'], rec['size'] = piece, row['size']
            rec['cut'] = rec['text'][len(piece):len(rec['text'])-len(row['size'])-1]

def check_marker(mk):
    """Identities a correct read must satisfy; -> list of (name, ok, detail)."""
    out = []
    W, L, U, A = mk['width'], mk['length'], mk['util'], mk['total_area']
    if mk['laid']:
        # W*L*U/100 == sum of the placed slots' declared areas held on both
        # vintages. The double at 422 is the sum of ALL slots' declared areas
        # (14 of 15 corpus markers, v4), so it equals the placed sum only when
        # every slot is placed - which is why it differed on the July markers
        # (1 of 72 placed). Reported, not asserted: the 2303-BD 137 unlaid
        # export, a marker that had been laid, holds a stale value there.
        # v4.5: the tolerance is relative. AutoMark / AccuNest exports store the
        # utilisation to 0.01% (80.00) and the length to 0.01, so the product is
        # off by ~2e-4 on a large marker (ZZ-AM-1: 13417.98 vs 13420.42); the old
        # absolute 0.01 sq in was calibrated on small hand-laid markers.
        wlu = W*L*U/100
        out.append(('sum(slot areas) == W*L*U', abs(mk['sum_slot_areas'] - wlu) <= max(1e-2, 5e-4 * wlu),
                    f'{mk["sum_slot_areas"]:.4f} vs {wlu:.4f}; @422={A:.4f}'))
        inside = all(0 <= p['y'] <= W and 0 <= p['x'] <= L for p in mk['placements'])
        out.append(('placed centres inside W x L', inside, f'{len(mk["placements"])} placements'))
    out.append(('every placement bound', all(p['record'] for p in mk['placements']),
                f'{sum(1 for p in mk["placements"] if p["record"])}/{len(mk["placements"])}'))
    placed_names = {p['piece'] for p in mk['placements'] if p['piece']}
    listed = {p['name'] for p in mk['pieces']}
    out.append(('placed pieces are in the piece list', placed_names <= listed,
                f'{sorted(placed_names - listed)}' if placed_names - listed else 'ok'))
    out.append(('slot count == directory span', len(mk['slots'])*SLOT ==
                (mk['sections'][SEC_SLOTS][1]-mk['sections'][SEC_SLOTS][0]) if mk['sections'][SEC_SLOTS] else True, ''))
    # v4: the model list and size table must tile sections 11-12 exactly, and
    # the size rows must tile the slot table (both hold on all 15 corpus
    # markers; a failure means a layout this reader has not seen)
    te = mk.get('table_ends')
    if te:
        out.append(('model list + size table tile sections 11-12', all(a == b for a, b in te.values()),
                    ', '.join('%s end %s want %s' % (k, hex(a), hex(b)) for k, (a, b) in te.items())))
    if mk['sizes']:
        run = 0; cumulative = True
        for r in mk['sizes']:
            cumulative = cumulative and r['ordinal'] == run; run += r['n']
        in_range = all(r['model_index'] < len(mk['models']) for r in mk['sizes'])
        out.append(('size table: sum(pieces) == slots, ordinals cumulative, model index in range',
                    run == len(mk['slots']) and cumulative and in_range,
                    f'{run} pieces vs {len(mk["slots"])} slots, {len(mk["sizes"])} rows'))
    # v4.1: rows that count EVERY slot, placed or not - "every placement bound"
    # above is 0/0 on an unlaid marker and says nothing there. Appended, never
    # renamed: dataset/MANIFEST.json keys on the existing names.
    slots = mk['slots']; N = len(slots)
    if N:
        b = [s.get('binding') or {} for s in slots]
        n_struct = sum(1 for x in b if x.get('method') == 'structural')
        out.append(('every slot bound structurally', n_struct == N, f'{n_struct}/{N}'))
        n = sum(1 for x in b if x.get('bundle_ok'))
        out.append(('slot bundle == head bundle == size-row index', n == N, f'{n}/{N}'))
        n = sum(1 for x in b if x.get('area_ok'))
        out.append(('slot declared area == bound record area', n == N, f'{n}/{N}'))
        n = sum(1 for x in b if x.get('text_ok'))
        out.append(('record text ends with the tiled size + G', n == N, f'{n}/{N}'))
    if mk['record_index']:
        out.append(('records == section-13 entries', mk.get('records_source') == 'index'
                    and len(mk['records']) == len(mk['record_index']),
                    f'{len(mk["records"])} records, {len(mk["record_index"])} index entries, read by {mk.get("records_source")}'))
    if mk.get('piece_list_end'):
        a, w = mk['piece_list_end']
        out.append(('piece list tiles section 10', a == w, f'walk end {hex(a)} want {hex(w)}'))
    # v4.2: the order copy, the laid state and the block buffers
    oc = mk.get('order_copy')
    if oc:
        end, stop = mk['order_copy_end']
        rows = Counter((r['model'], r['size']) for r in mk['sizes'])
        seen = Counter((m['name'], s['size']) for m in oc for s in m['sizes'])
        qty_ok = all(rows[(m['name'], s['size'])] == s['quantity'] for m in oc for s in m['sizes'])
        out.append(('order copy tiles section 15; quantity == size-row count',
                    end == stop and [m['name'] for m in oc] == mk['models'] and qty_ok and set(seen) == set(rows),
                    f'{len(oc)} models, {sum(s["quantity"] for m in oc for s in m["sizes"])} cuts, walk end {hex(end)} want {hex(stop)}'))
    ls = mk.get('laid_state_sources')
    if ls:
        out.append(('laid state: placed word, slot coordinates and header agree', ls['agree'],
                    f'{mk["laid_state"]} (word {ls["placed_word"]}, header {ls["header"]})'))
        out.append(('header @430 == sum of placed slot areas',
                    abs(mk['placed_area'] - mk['sum_slot_areas']) <= 1e-6 * max(1.0, mk['sum_slot_areas']),
                    f'{mk["placed_area"]:.4f} vs {mk["sum_slot_areas"]:.4f}'))
    if mk['slots']:
        out.append(('slot @88 signature <=> directory word 40 is 0 (as generated)',
                    any(s['sig88'] for s in mk['slots']) == (mk['placed_word'] == 0),
                    f'{sum(1 for s in mk["slots"] if s["sig88"])} slots with a non-zero @88, word 40 = {mk["placed_word"]}'))
    # v4.7: the marker-level 0x0040 orientation bit is a COPY of the piece row's flag u16 @+14
    # (section 10): slot bit == (flag == 1) on 9,122 of 9,122 slots over 111 markers, and no
    # marker mixes values. What sets that flag (an order / model option) is still open [?].
    prow = mk['pieces']
    pr = [(s, prow[s['piece_index'] - 1]) for s in mk['slots'] if 0 < s['piece_index'] <= len(prow) and 'flag14' in prow[s['piece_index'] - 1]]
    if pr:
        out.append(('slot orientation bit 0x0040 == its piece row flag @+14 (section 10)',
                    all(bool(s['orient_code'] & 0x40) == (p['flag14'] == 1) for s, p in pr),
                    f'{sum(1 for s, p in pr if bool(s["orient_code"] & 0x40) == (p["flag14"] == 1))} of {len(pr)} slots; flags {sorted({p["flag14"] for _, p in pr})}'))
    sm = mk.get('sig88_model')
    if sm and sm['applicable']:
        out.append(('slot @88 = record head count + one constant per piece (as generated)', sm['ok'],
                    f'{len(sm["constant"])} pieces; C = {sorted(v for v in sm["constant"].values() if v is not None)[:6]}'))
    if mk.get('block_buffers'):
        # v4.5: the table holds buffer DEFINITIONS and a piece points at one (0-based)
        # or at none - not "entry k is piece k's". Live scratch markers (ZZC-M1..3,
        # ZZN-F1) have 4 entries for 5 pieces, index 0 used, and one piece with none.
        out.append(('piece buffer indices resolve into the block-buffer table',
                    all(p.get('buffer_ok') for p in mk['pieces']),
                    f'{len(mk["block_buffers"])} entries; indices {[p.get("buffer_index") for p in mk["pieces"]]}'))
    return out

# ------------------------------------------------------------ byte map
COVERAGE_CLASSES = ('identified', 'raw', 'zero_pad', 'opaque', 'unknown')
_LEAD = 6      # every list section's chain starts 6 bytes before its directory offset

def marker_coverage(d, mk=None):
    """v4.4: classify EVERY byte of a marker object, the marker-side sibling
    of accumark_pds.coverage() - the measurable form of "fully decoded".

      identified  a field whose position AND meaning are known
      raw         position and extent known, meaning still open (e.g. the
                  flag bytes of a piece row, the slot's constant sentinels)
      zero_pad    a run of zeros the structure guarantees
      opaque      a blob whose extent is known and whose content is bounded
                  on purpose, not chased: section 14's per-point attribute
                  stream and the embedded type-10 object (topology-only
                  scratch, see MARKER_DECODE_PLAN.md)
      unknown     nothing decodes it

    A byte is claimed by the parser that reads it, ordered so a narrower field
    overrides the broad region around it. -> dict(size, counts, pct,
    sections [{section, start, end, counts}], unknown_runs [(start, end,
    section)], where `section` is the directory slot whose chain span
    [dir[k] - 6, dir[k+1] - 6) holds the run - 0 for the envelope / directory,
    -1 for the trailer). `pct['understood']` = identified + zero_pad."""
    mk = mk or parse_marker(d)
    n = len(d); cls = ['unknown'] * n; own = [0] * n
    dirs = mk['directory']; sec = mk['sections']
    def mark(a, b, label):
        for i in range(max(0, a), min(n, b)): cls[i] = label
    # ownership: the chain span of each used section (the trailer is section -1)
    used = sorted((v, k) for k, v in enumerate(dirs[:DIR_OFFSETS]) if v not in (0, 0xffffffff) and v < n)
    tr0 = n - TRAILER
    for j, (off, k) in enumerate(used):
        a = off - (0 if k == SEC_SCALARS else _LEAD)
        b = (used[j+1][0] - _LEAD) if j+1 < len(used) else tr0
        for i in range(max(0, a), min(n, b)): own[i] = k
    for i in range(max(0, tr0), n): own[i] = -1
    # -- envelope: magic, name, object type, payload length, directory
    mark(0, 0x10, 'identified'); mark(0x15, d.index(b'\x00', 0x15) + 1, 'identified')
    t = u16(d, 0x7a); mark(0x7a, 0x7c, 'identified'); mark(0x7e, 0x82, 'identified')
    for o in (0x60, 0x68):                      # the u32 copy of the type sits at 0x60 or 0x68 by vintage
        if u32(d, o) == t: mark(o, o+4, 'identified')
    mark(DIR_OFF, DIR_OFF + 4*DIR_SLOTS, 'identified')
    # -- section 1: the header scalars (width, length, area, placed area, util, @454)
    if sec[SEC_SCALARS]:
        for o in (396, 412, 422, 430, 446, 454): mark(o, o+8, 'identified')
    # -- section 2 carries the marker's own name; section 5 the -PDSTEXT- label table
    if sec[2]:
        i = d.find(mk['name'].encode('latin1'), sec[2][0], sec[2][1])
        if i >= 0: mark(i, i + len(mk['name']) + 1, 'identified')
        tb = mk.get('tables')
        if tb and tb['ok']:                     # v4.8: the eleven name lengths and the name strings
            for _, o in TABLE_LENS: mark(sec[2][0] + o, sec[2][0] + o + 2, 'identified')
            a0 = sec[2][0] + TABLE_STRINGS; mark(a0, a0 + sum(len(tb[k]) for k, _ in TABLE_LENS), 'identified')
    if sec[5]:
        for m in re.finditer(rb'-PDSTEXT-', d[sec[5][0]-_LEAD:sec[5][1]-_LEAD]):
            a = sec[5][0] - _LEAD + m.start(); mark(a, a + 9, 'identified')
            name = re.split(rb'[^\x20-\x7e]', d[a+12:a+140])[0]
            mark(a + 12, a + 12 + len(name) + 1, 'identified')
    # -- section 6: the block-buffer table, (pieces + 1) x 102 bytes
    if sec[SEC_BUFFERS]:
        for e in range(len(mk['block_buffers'])):
            p = sec[SEC_BUFFERS][0] - _LEAD + e * BUFFER_ENTRY
            mark(p, p + 2, 'raw'); mark(p + 2, p + 34, 'identified'); mark(p + 34, p + BUFFER_ENTRY, 'zero_pad')
    # -- section 10: the piece list
    if sec[SEC_PIECES]:
        lo = sec[SEC_PIECES][0]
        mark(lo, lo + PIECE_LIST_HEAD, 'raw'); mark(lo + 22, lo + PIECE_LIST_HEAD, 'identified')     # ... 'MARKER'
        for p in mk['pieces']:
            if 'fabric_types' not in p: continue        # the regex fallback has no row layout
            r = p['offset'] - 28
            mark(r, r + 4, 'identified'); mark(r + 4, r + 28, 'raw')
            mark(r + 18, r + 20, 'identified')                                                       # flag u16 @+14 == slot bit 0x0040 [V v4.7]
            mark(r + 8, r + 10, 'identified'); mark(r + 22, r + 24, 'identified')                    # buffer index, fabric-type count
            q = p['offset'] + len(p['name']) + len(p['fabric']); mark(p['offset'], q, 'identified')
            for ft in p['fabric_types']: mark(q, q + 2 + len(ft), 'identified'); q += 2 + len(ft)
    # -- section 11 (models), 12 (size table), 13 (record index)
    if sec[SEC_MODELS]:
        p = sec[SEC_MODELS][0] - _LEAD
        for name in mk['models']: mark(p, p + 2 + len(name), 'identified'); p += 2 + len(name)
    if sec[SEC_SIZES]:
        p = sec[SEC_SIZES][0] - _LEAD
        for r in mk['sizes']:
            mark(p, p + 10, 'identified'); mark(p + 10, p + 14, 'raw')                               # the flags word is still open [?]
            mark(p + SIZE_HDR, p + SIZE_HDR + len(r['size']), 'identified'); p += SIZE_HDR + len(r['size'])
    if sec[SEC_INDEX] and mk['record_index']:
        p = sec[SEC_INDEX][0] - _LEAD; mark(p, p + 4*len(mk['record_index']), 'identified')
    # -- section 14: per record a 48-byte head, the label text, then the attribute stream
    if sec[SEC_RECORDS]:
        end14 = sec[SEC_RECORDS][1] - _LEAD; recs = mk['records']
        for i, r in enumerate(recs):
            o = r['offset']; start = o - 48; nxt = (recs[i+1]['offset'] - 48) if i + 1 < len(recs) else end14
            mark(start, o, 'raw')                                                                    # 48-byte head ...
            mark(o - 30, o - 14, 'identified')                                                       # ... area, perimeter
            mark(o - 38, o - 36, 'identified')                                                       # u16 @+10: per-size entry count (slot @88 = it + C) [V v4.7]
            mark(o - 10, o - 8, 'identified'); mark(o - 8, o, 'zero_pad')                            # stream length, 8 zeros
            t_end = o + len(r['text']) + 1; mark(o, t_end, 'identified')
            # v4.7: the stream. Verified against the record's own area / perimeter, everything up to the trailer is
            # identified (tag byte: class + the point kind in its low nibble; extra byte: notch type + a flag nibble
            # [flag open]); the trailer (attribute bytes + 3) stays raw; a stream that does not verify stays opaque
            ro = record_outline(d, r)
            if ro and ro['verified']:
                base = o + len(r['text']); dec = decode_record_stream(d[base:base + r['stream_len']])         # the stream starts AT the label's NUL
                kind = dict(lead='identified', header='identified', data='identified', id='identified', tag='identified', extra='identified')
                for a_, b_, k_ in dec['spans']: mark(base + a_, base + b_, kind[k_])
                mark(base + dec['end'], nxt, 'raw')
            else: mark(t_end, nxt, 'opaque')
    # -- section 15: the order copy
    if sec[SEC_ORDER_COPY]:
        p = sec[SEC_ORDER_COPY][0] - _LEAD
        for m in mk['order_copy']:
            mark(p, p + MODEL_HEAD, 'raw'); mark(p, p + 2, 'identified'); mark(p + 8, p + 10, 'identified'); mark(p + 12, p + 16, 'identified')
            p += MODEL_HEAD; mark(p, p + len(m['name']), 'identified'); p += len(m['name'])
            for ft in m['fabric_types']: mark(p, p + 2 + len(ft), 'identified'); p += 2 + len(ft)
            for s in m['sizes']:
                mark(p, p + 4, 'identified'); mark(p + 4, p + 28, 'zero_pad'); mark(p + 28, p + 28 + len(s['size']), 'identified'); p += 28 + len(s['size'])
    # -- section 21: the slots (the last 6 bytes of a slot body are the next slot's head)
    if sec[SEC_SLOTS]:
        for s in mk['slots']:
            b = s['slot']
            mark(b - SLOT_HEAD, b - SLOT_HEAD + 6, 'identified'); mark(b, b + SLOT, 'raw')
            mark(b, b + 32, 'identified'); mark(b + 32, b + 34, 'identified'); mark(b + 42, b + 50, 'identified'); mark(b + 64, b + 68, 'identified'); mark(b + 88, b + 90, 'identified')
        if mk['slots']: mark(mk['slots'][-1]['slot'] + SLOT - SLOT_HEAD, mk['slots'][-1]['slot'] + SLOT, 'raw')
    # -- section 30: the embedded type-10 object (topology-only scratch): bounded, not chased
    if sec[SEC_GEOMETRY]: mark(sec[SEC_GEOMETRY][0] - _LEAD, tr0, 'opaque')
    # -- trailer: the object's name, created / modified stamps, the two user names
    mark(tr0 + 0x8a, tr0 + 0x8a + len(mk['name']) + 1, 'identified')
    mark(tr0 + TRAILER_CREATED, tr0 + TRAILER_CREATED + 8, 'identified')
    for o in (0x110, 0x162):
        e = d.find(b'\x00', tr0 + o, tr0 + o + 0x52)
        if e > tr0 + o and _printable(d[tr0+o:e]): mark(tr0 + o, e + 1, 'identified')
    counts = Counter(cls); pct = {c: 100.0 * counts.get(c, 0) / n for c in COVERAGE_CLASSES}
    pct['understood'] = pct['identified'] + pct['zero_pad']
    sections = []
    for k in sorted(set(own)):
        idx = [i for i in range(n) if own[i] == k]; cc = Counter(cls[i] for i in idx)
        sections.append(dict(section=k, start=idx[0], end=idx[-1] + 1, bytes=len(idx), counts={c: cc.get(c, 0) for c in COVERAGE_CLASSES}))
    runs = []; i = 0
    while i < n:
        if cls[i] == 'unknown':
            j = i
            while j < n and cls[j] == 'unknown' and own[j] == own[i]: j += 1
            runs.append((i, j, own[i])); i = j
        else: i += 1
    return dict(size=n, counts={c: counts.get(c, 0) for c in COVERAGE_CLASSES}, pct=pct, sections=sections, unknown_runs=runs)

PARSED_SECTIONS = frozenset({6, 11, 12, 13, 14, 15, 21, 30})    # every byte they own is classified on all 18 fixture markers

def coverage_warnings(mk, cv=None):
    """v4.6: bytes inside a section this reader parses that no parser explains.
    On all 18 fixture markers there are none, so any is a field or variant never
    seen before. Costs a pass over every byte, so the CLI runs it, not place_marker."""
    cv = cv or marker_coverage(mk['object']['data'], mk)
    by = Counter()
    for a, b, k in cv['unknown_runs']:
        if k in PARSED_SECTIONS: by[k] += b - a
    return ['section %d: %d bytes are explained by no parser (a field this reader has never seen)' % (k, n)
            for k, n in sorted(by.items())]

# ------------------------------------------------ type-10 object (research)
# The marker's slot 30 embeds a second, complete XGGT object (its own magic,
# name and 396-byte trailer) starting 26-58 bytes into the section - NOT at
# the section's own offset 0. It carries its own 42-slot directory at the
# same 0x8a convention as the marker itself [V, confirmed identically on
# every marker below]. Ruled out as placement geometry: slot 33 (laid-only)
# is a per-placement array but every one of its 72-byte records is a
# constant `ffffffff`+68 zero bytes placeholder, never populated; slot 39
# (95%+ of the object) is the same LENGTH whether laid or not.
#
# Slot 39 turns out not to be uniform filler. Its first ~20-40 KB hold a
# sparse table of 16-byte tagged fields - [V, exact byte match across all
# 10 markers in this repo's corpus]:
#
#     00 00 <u8 id> <7 zero bytes> <u32 LE value> <u16 LE tail> <2 pad>
#
# found by scanning for that zero-run signature; unused slots between real
# fields hold a repeating placeholder cycle (`00 00 01 01 02` or `01 00`),
# not real data, matching the low-entropy/0-1-2-dominated byte histogram
# already noted for this section.
#
# What the fields ARE is only partly settled:
#   id 45 -> (val=4, tail=0) and id 46 -> (val=102, tail=98) are UNIVERSAL
#   FORMAT CONSTANTS: identical, byte for byte, on every one of the 10
#   markers tested (two different styles, laid and unlaid, 0-97 placements,
#   both 2026-07 and 2026-09 export vintages).
#   id 44's value is always exactly 2x id 47's, which is always exactly
#   id 51's value - and all three take one of only two values across the
#   whole corpus: 88/44/44 on every style-2303 marker (BD137 laid+unlaid,
#   the four CP150 corner probes), 8/4/4 on every marker built from a
#   single simple test piece (CLAUDE-GRADE-MARKER, CLAUDE-QTY-TEST,
#   AD1234 TEST 134, LADIES-BLOUSE TEST-2). It tracks which STYLE's piece
#   catalog the marker draws from, not the marker instance: unaffected by
#   laid state, placement count (0, 2, 13, 54 or 97), or marker length/
#   width, and the two 2303 samples agree even though one zip bundles only
#   the 18 referenced pieces and the other bundles the whole ~120-piece
#   style catalog. [?] what it actually counts is not identified.
#   ids 42/48/52/53/56 vary per marker in ways not yet explained; id 53 is
#   ABSENT on the CP150 samples (present, with a value, on BD137 and every
#   single-test-piece marker) - an optional field, not always emitted.
#
# The GAPS between tagged fields are not all the same kind of filler: the
# ~48 KB gap between id 53 and id 54 on `2303-BD 137 PLACED` has a rich
# byte histogram unlike the simple 2- and 5-byte cycles elsewhere. It
# decomposes into a 138-byte `01 00` filler run, a 47,915-byte residual of
# ~12,000 quasi-periodic u16-LE pairs (94-98% period-4 self-similar), and
# 47 trailing zero bytes. An initial guess that the residual re-encoded
# piece perimeter-point attr bytes (it is rich in the exact values used for
# `accumark_pds.POINT_TURN`/`POINT_CURVE`) does NOT hold up: every one of
# the style's 1,366 perimeter points has attr 9, none has attr 10, so the
# gap's ~1,042 tens correspond to nothing in the piece data. Retracted; see
# MARKER_DECODE_PLAN.md's STATUS blocks for what was ruled out and why.
def type10_object(marker_data):
    """The embedded type-10 object's own bytes (magic through its own
    trailer), or None if this marker has no slot 30 / it isn't an XGGT
    object (should not happen on any export seen so far)."""
    dirs = directory(marker_data)
    outer = _section(marker_data, dirs, SEC_GEOMETRY)
    if not outer: return None
    region = marker_data[outer[0]:outer[1]]
    i = region.find(MAGIC)
    return region[i:] if i >= 0 else None

def type10_directory(obj):
    """The type-10 object's own 42-slot directory, same convention as
    `directory()`/`_section()` on the marker itself."""
    return [u32(obj, DIR_OFF+4*i) for i in range(DIR_SLOTS)]

def type10_tagged_fields(marker_data):
    """-> [(byte_offset_in_slot_39, id, value, tail), ...] for the small
    tagged-field table living in slot 39's leading region (see the module
    comment above). Returns [] if this marker has no type-10 object or no
    slot 39. Research-grade: not used by `place_marker`/`check_marker`."""
    obj = type10_object(marker_data)
    if obj is None: return []
    dirs = type10_directory(obj)
    s39 = _section(obj, dirs, 39)
    if not s39: return []
    body = obj[s39[0]:s39[1]][:-TRAILER]
    out = []; i = 0
    while i+16 <= len(body):
        if body[i] == 0 and body[i+1] == 0 and body[i+2] != 0 and all(c == 0 for c in body[i+3:i+10]):
            out.append((i, body[i+2], u32(body, i+10), struct.unpack_from('<H', body, i+14)[0]))
            i += 16
        else:
            i += 1
    return out

# ---------------------------------------------------------------- order
ORDER_TABLE_SLOTS = (('name', 10), ('customer', 12), ('reference', 14), ('lay_limits', 74), ('annotation', 76), ('block_buffer', 78),
                     ('reserved_80', 80), ('notch_table', 82), ('reserved_84', 84), ('extra', 88))
ORDER_TABLE_SLOTS_OLD = (('name', 10), ('customer', 31), ('reference', 52), ('lay_limits', 132), ('annotation', 153), ('block_buffer', 174),
                         ('reserved_80', 195), ('notch_table', 216), ('reserved_84', 237), ('extra', 259))

def parse_order_tables(obj):
    """v4.8: the names an order stores for the tables it was made with - the SAME ten slots the marker copies into its section 2 (parse_marker_tables), so an
    order and its marker agree name for name [V: every order that shares a ZIP with its marker, 34 of 34 with both].
    Newer vintage (V17): ten u16 lengths at payload +10, +12, +14, +74, +76, +78, +80, +82, +84, +88 and the strings back to back from +176; older vintage
    (`COSTORDER`, `LADIES-BLOUSE`, ...): ten 20-character space-padded slots at +10, +31, +52, +132, +153, +174, +195, +216, +237, +259.
    -> dict(vintage, name, customer, reference, lay_limits, annotation, block_buffer, notch_table, extra) or None if the bytes do not fit either layout.
    `name` is the order's marker name - the marker's own name, which need not equal the order object's name."""
    p = obj['payload'] if isinstance(obj, dict) else obj
    if len(p) >= 0x120 and re.fullmatch(rb'[\x20-\x7e]{20}\x00', bytes(p[10:31])):
        out = dict(vintage='v4')
        for k, o in ORDER_TABLE_SLOTS_OLD:
            raw = bytes(p[o:o+20])
            if not all(c == 0 or 32 <= c < 127 for c in raw): return None
            out[k] = raw.replace(b'\x00', b' ').decode('latin1').strip()
        return out
    if len(p) < 176 + 2: return None
    lens = [u16(p, o) for _, o in ORDER_TABLE_SLOTS]; pos = 176; out = dict(vintage='v5')
    if pos + sum(lens) > len(p): return None
    for (k, _), n in zip(ORDER_TABLE_SLOTS, lens):
        raw = bytes(p[pos:pos+n])
        if not all(32 <= c < 127 for c in raw): return None
        out[k] = raw.decode('latin1'); pos += n
    return out

def parse_order(d):
    """Order object (type 13): name, the four table names (lay limits,
    annotation, block buffer, notch), then per model the requested sizes
    with their (still unlabelled [?]) quantity fields."""
    obj = read_object(d)
    if obj['type'] != 13: raise WrongObjectType('not an order object', got=obj['type'], want=13)
    strs = [(m.start(), m.group().decode('latin1')) for m in re.finditer(rb'[\x20-\x7e]{2,}', d[0x80:len(d)-TRAILER])]
    strs = [(o+0x80, s) for o, s in strs]
    models = []
    for o, s in strs:
        if o < 0x300 and s.startswith(obj['name']): continue
        if re.fullmatch(r'\d{1,2}[A-Z]{0,3}', s) and models:
            models[-1]['sizes'].append(dict(size=s, fields=[u16(d, o+len(s)+2*k) for k in range(8)]))
        elif not re.fullmatch(r'\d{1,2}[A-Z]{0,3}', s) and len(s) >= 6:
            models.append(dict(name=s, offset=o, sizes=[]))
    return dict(name=obj['name'], object=obj, models=models, strings=strs[:4], tables=parse_order_tables(obj))

def parse_model(d):
    """Model object (type 12): the pieces of a garment [V for names]."""
    obj = read_object(d)
    if obj['type'] != 12: raise WrongObjectType('not a model object', got=obj['type'], want=12)
    pieces = []
    p = 0x80
    end = len(d) - TRAILER
    while p < end-4:
        n = u16(d, p)
        if 3 <= n <= 64 and p+2+n <= end and all(32 <= c < 127 for c in d[p+2:p+2+n]):
            s = d[p+2:p+2+n].decode('latin1')
            if s != obj['name'] and not s.endswith('.csv'):
                pieces.append(dict(name=s, flags=d[p+2+n:p+2+n+14].hex()))
            p += 2+n; continue
        p += 1
    return dict(name=obj['name'], object=obj, pieces=pieces)

# ------------------------------------------------------------ placement
def transform(outline, pl):
    """Piece outline (inches, its own frame) -> marker frame for one slot:
    mirror/rotate about the outline's own bbox centre, translate to the
    placed centre [V dxfparser, 4 DXF-drawn July markers here]."""
    xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    out = []
    for x, y in outline:
        dx, dy = x-cx, y-cy
        if pl['rot'] == 180: dx, dy = -dx, -dy
        if pl['flip_v']: dy = -dy
        if pl['flip_h']: dx = -dx
        out.append((pl['x']+dx, pl['y']+dy))
    return out

def _chain_lengths(pts):
    acc = [0.0]
    for i in range(1, len(pts)):
        acc.append(acc[-1] + math.hypot(pts[i][0]-pts[i-1][0], pts[i][1]-pts[i-1][1]))
    return acc

def graded_outline(block, size):
    """Perimeter of one decoded piece block at `size` (a size name), in
    inches. Rule deltas are per size-break increments smallest-first
    (FORMAT_SPEC section 3); a point's cumulative move from the base size to
    the target is the sum of the rows between them. Points without a rule
    (curve points, f1 == 1) between two ruled points move by a SIMILARITY of
    the chord joining those two points (the chain keeps its shape while the
    chord is rotated and scaled onto the graded chord) - v4.7, from the blind
    test CLAUDE-D4: 20 unruled points at two sizes match the marker's own
    stream to 1e-4 in, where the earlier chain-proportional blend of the two
    moves (dxfparser, 2026-08-02) is off by up to 0.295 in. Both rules give the
    same answer when the two ruled moves are equal - true of every piece in the
    older corpus, none of which had two different rules on one chain.
    Returns None if the size is not in the table."""
    m = block['meta']; names = [s['name'] for s in m['sizes']]
    if size not in names: return None
    t, b = names.index(size), m['base_index']
    rules = {o['id']: o['deltas'] for o in block['objects']}
    pts = block['perimeter']
    def move(p):
        rid = p['rule_ref']
        if rid is None or rid not in rules: return None
        rows = rules[rid]
        if t == b: return (0, 0)
        if t > b: sel = rows[b:t]
        else: sel = [(-dx, -dy) for dx, dy in rows[t:b]]
        return (sum(r[0] for r in sel), sum(r[1] for r in sel))
    moves = [move(p) for p in pts]
    n = len(pts)
    ruled = [i for i in range(n) if moves[i] is not None]
    if not ruled:
        return [(p['x']/1e4, p['y']/1e4) for p in pts]
    xy = [(p['x'], p['y']) for p in pts]
    out = [None]*n
    for i in ruled: out[i] = (xy[i][0]+moves[i][0], xy[i][1]+moves[i][1])
    for k, i in enumerate(ruled):
        j = ruled[(k+1) % len(ruled)]
        # walk cyclically from i to j
        seq = []
        q = (i+1) % n
        while q != j:
            seq.append(q); q = (q+1) % n
        if not seq: continue
        a = complex(*xy[i]); c = complex(*xy[j]) - a
        if abs(c) < 1e-9:              # one ruled point (or two coincident): a plain translation
            for q in seq: out[q] = (xy[q][0]+moves[i][0], xy[q][1]+moves[i][1])
            continue
        ga = complex(*out[i]); kf = (complex(*out[j]) - ga) / c
        for q in seq:
            z = ga + (complex(*xy[q]) - a) * kf
            out[q] = (z.real, z.imag)
    return [(x/1e4, y/1e4) for x, y in out]

def fold_axis_indices(block, data):
    """A fold half (Mirror Piece) declares its axis as an `M` block whose two
    endpoints coincide with two perimeter points [V 2303 OUCF pieces]. Return
    the indices of those perimeter points, or None. Indices survive grading,
    so the graded outline can be unfolded about its own graded points."""
    pts = [(p['x'], p['y']) for p in block['perimeter']]
    for ax in ap.mirror_lines(data):
        idx = []
        for e in ax:
            k = min(range(len(pts)), key=lambda i: abs(pts[i][0]-e[0]) + abs(pts[i][1]-e[1]))
            if abs(pts[k][0]-e[0]) + abs(pts[k][1]-e[1]) <= 2: idx.append(k)
        if len(idx) == 2 and idx[0] != idx[1]: return tuple(idx)
    return None

def piece_outline(piece, size=None):
    """Finished outline (inches) of a decoded piece at `size`: graded when the
    size is in the piece's table, unfolded when the piece is a fold half.
    `piece` = dict(block=..., data=...). -> (outline, note)."""
    blk, data = piece['block'], piece['data']
    note = ''
    outline = graded_outline(blk, size) if size else None
    if size and outline is None:
        note = 'size %r not in piece table; sample size drawn' % size
    if outline is None:
        outline = [(p['x']/1e4, p['y']/1e4) for p in blk['perimeter']]
    fold = piece.get('fold')
    if fold is None:
        fold = fold_axis_indices(blk, data); piece['fold'] = fold or False
    if fold:
        outline = ap.unfold(outline, (outline[fold[0]], outline[fold[1]]))
        note = (note + '; ' if note else '') + 'unfolded about the declared M axis'
    return outline, note

def load_pieces(objs):
    """-> (pieces, errors). Fails soft per piece by design - one corrupt piece
    must not sink a marker with a hundred others - but v2 keeps *why* instead
    of discarding it: `errors[name]` holds the exception every place_marker()
    caller can now surface (piece_errors below), rather than every failure
    reading identically as the misleading 'piece not in ZIP'.

    v2: a piece object that decodes with zero blocks - a stub/placeholder
    (found on `markers/misc-test-markers/LADIES-BLOUSE TEST-2.zip`: an
    AMXDLL "Include Components" export limitation, already documented in
    MARKER_DECODE_PLAN.md, writes a type-20 envelope+trailer with no real
    field-block payload in between when a referenced piece can't be
    resolved) - now records a named DecodeError instead of the bare
    `IndexError: list index out of range` indexing `blocks[0]` used to
    raise, matching the same fix already applied to accumark_pds.summarize()."""
    pieces = {}; errors = {}
    for o in objs.get('piece', []):
        try:
            blocks = ap.decode(o['data'])['blocks']
            if not blocks:
                raise DecodeError('no piece block found in object payload (stub/placeholder object?)',
                                   source=o['name'])
            pieces[o['name']] = dict(block=blocks[0], data=o['data'])
        except Exception as e:
            pieces[o['name']] = None; errors[o['name']] = e
    return pieces, errors

STREAM_NOTE = "outline read from the marker's own section-14 stream (matches the record's area and perimeter)"

def _slot_geometry(s, pieces, piece_errors, use_grading, mk=None):
    """-> (piece name, size, outline in the PIECE's own frame or None, note). v4.7: a slot whose
    piece object is missing or undecodable falls back to the outline in its record's stream - only
    when that outline reproduces the record's own area and perimeter (verify_stream_outline)."""
    piece = pieces.get(s['piece']) if s['piece'] else None
    if piece is None:
        if s['piece'] in piece_errors: note = 'piece failed to decode: %s' % piece_errors[s['piece']]
        else: note = 'piece not in ZIP' if s['piece'] else 'unbound slot'
        if mk is not None and s.get('record'):
            ro = record_outline(mk['object']['data'], s['record'])
            if ro and ro['verified']: return s['piece'], s['size'], ro['points'], STREAM_NOTE
        return s['piece'], s['size'], None, note
    outline, note = piece_outline(piece, s['size'] if use_grading else None)
    # v4.7 (blind test CLAUDE-D3-BF): a piece object holds the STITCH line and its seam allowances; the marker lays the CUT
    # line (stitch + allowance, e.g. 0.375 / 0.25 in, 1.0 in on a fold edge). When the piece outline does not reproduce the
    # slot's declared area (0.89 there) but the marker's own stream does, the stream outline is the right one
    if mk is not None and s.get('record') and s.get('area') and outline and abs(_shoelace(outline) / s['area'] - 1) > 0.02:
        ro = record_outline(mk['object']['data'], s['record'])
        if ro and ro['verified']: return s['piece'], s['size'], ro['points'], STREAM_NOTE + '; the piece object is the stitch line without its seam allowance'
    return s['piece'], s['size'], outline, note

def unplaced_slots(mk, pieces, piece_errors, use_grading=True):
    """The slots nothing has been laid for -> [(slot, piece, size, outline or
    None, note)], the shape of `placed` but with the outline in the piece's own
    frame (an unplaced slot has no position to transform it to)."""
    out = []
    for s in mk['slots']:
        if s['empty']: out.append((s,) + _slot_geometry(s, pieces, piece_errors, use_grading, mk))
    return out

def _buffer_sides(mk, piece_name):
    """The block-buffer entry a piece points at, (b0, b1, b2, b3) inches; zeros
    for a piece with no buffer index (0xffff) or a marker with no section 6
    (see parse_block_buffers; the side order is [?]). v4.5: a piece with no
    index used to get entry 0 - wrong: entry 0 is an ordinary definition (1 cm on
    ZZC-M1, used by its BK piece), and the piece that has none has none."""
    bufs = mk.get('block_buffers') or []
    row = next((p for p in mk['pieces'] if p['name'] == piece_name), None)
    i = row.get('buffer_index') if row else None
    if i is None or not (0 <= i < len(bufs)): return (0.0, 0.0, 0.0, 0.0)
    return tuple(bufs[i]['sides'])

def _shoelace(p):
    return abs(sum(p[i][0]*p[(i+1) % len(p)][1] - p[(i+1) % len(p)][0]*p[i][1] for i in range(len(p)))) / 2

def unplaced_inventory(mk, pieces=None, piece_errors=None, use_grading=True, geometry=None):
    """v4.2: the CUT ORDER an unplaced (or part-placed) marker states - what
    is still to be laid, on what width, with nothing about where. Everything
    comes from the marker's own structure; the outlines need the piece objects
    in the same ZIP (`pieces` from load_pieces) and are absent - never guessed
    - otherwise: `marker['geometry_available']` says which.

    -> dict(
      marker      name, width / length in inches and cm, laid_state, models,
                  fabric_types, block_buffers (the table's definitions, 4 sides each),
                  geometry_available 'all' | 'some' | 'none' | 'n/a'
      order_lines [{model, size, quantity, bundles}]  one per (model, size)
      slots       one per UNPLACED slot: ordinal, bundle, model, size, piece,
                  category, cut, copies, pair {group, part 'A'|'B'} (a `CUT X02`
                  piece is a mirrored pair), declared_area, perimeter,
                  home_box_in (w, h: home x 2, as stored [V]), bbox_in (that minus the piece's
                  block buffer - an ESTIMATE [?]: the July CP 150 boxes fit it, but the
                  home box does not follow the buffer table on ZZC-M1 vs ZZC-BIG),
                  preset {rot180, mirror, pair_bit, other} - a PRE-SET lay
                  pattern that is reported, never counted as a placement -
                  and, with pieces: outline, checks {bbox_dx, bbox_dy,
                  area_ratio}, note
      totals      slots, placed, area_to_lay, perimeter, min_length_in (area to
                  lay / width: the length a 100%-efficient lay would need),
                  by_size, by_piece
      warnings    every reason to distrust part of the above, by name)"""
    pieces = pieces or {}; piece_errors = piece_errors or {}
    if geometry is None: geometry = unplaced_slots(mk, pieces, piece_errors, use_grading)
    warnings = []
    # (bundle, record) groups of two are a mirrored pair: (plain, mirrored) [V: 116/116 pairs]
    groups = {}
    for s in mk['slots']: groups.setdefault((s['bundle'], s['record_index']), []).append(s)
    pair_of = {}; g = 0
    for members in groups.values():
        if len(members) < 2: continue
        g += 1
        ordered = sorted(members, key=lambda s: (bool(s['orient_code'] & MIRROR_BIT), s['index']))
        for part, s in zip('ABCDEFGH', ordered): pair_of[s['index']] = dict(group=g, part=part)
    piece_row = {p['name']: p for p in mk['pieces']}
    slots = []; n_geo = 0
    for s, pname, size, outline, note in geometry:
        rec = s.get('record') or {}
        b = _buffer_sides(mk, pname)        # (b0, b1, b2, b3): x pair, then y pair [?]
        entry = dict(ordinal=s['index'], bundle=s['bundle'], model=s.get('model'), size=size, piece=pname,
                     category=(piece_row.get(pname) or {}).get('fabric'),
                     cut=rec.get('cut'), copies=len(groups[(s['bundle'], s['record_index'])]),
                     pair=pair_of.get(s['index']), declared_area=s['area'], perimeter=rec.get('perimeter'),
                     home_box_in=(s['home_x']*2, s['home_y']*2),
                     bbox_in=(s['home_x']*2 - (b[0] + b[1]), s['home_y']*2 - (b[2] + b[3])),
                     preset=dict(rot180=bool(s['orient_code'] & ROT180_BIT), mirror=bool(s['orient_code'] & MIRROR_BIT),
                                 pair_bit=bool(s['orient_code'] & 0x0040),
                                 other=s['orient_code'] & ~(ROT180_BIT | MIRROR_BIT | 0x0040)),
                     note=note)
        if note.startswith(STREAM_NOTE) and s.get('record'):
            ro_ = record_outline(mk['object']['data'], s['record'])
            entry['notches'] = [dict(type=n_[1], x=n_[2], y=n_[3]) for n_ in ro_['notches']]
            # the piece's other lines from the stream: grain (direction of the fabric), internal lines, cutouts, drill holes (inches, piece frame)
            gl_ = next((l for l in ro_['lines'] if l['kind'] == 'grain'), None)
            entry['grain'] = gl_['points'] if gl_ else None
            entry['grain_basis'] = gl_['basis'] if gl_ else None      # 'stream' (layout verified against piece objects) | 'inferred' (older vintage: horizontal 2-point segment)
            entry['internal_lines'] = [l['points'] for l in ro_['lines'] if l['kind'] in ('internal', 'cutout')]
            entry['drills'] = [l['points'][0] for l in ro_['lines'] if l['kind'] == 'drill']
            entry['sew_outline'] = ro_.get('sew')      # a fold piece with seam allowance: the STITCH line (the outline above is the cut line)
        if outline:
            xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
            entry.update(outline=outline, checks=dict(
                bbox_dx=s['home_x']*2 - (max(xs)-min(xs)) - (b[0] + b[1]),
                bbox_dy=s['home_y']*2 - (max(ys)-min(ys)) - (b[2] + b[3]),
                area_ratio=_shoelace(outline) / s['area'] if s['area'] else None))
            n_geo += 1
        slots.append(entry)
    # the order: per (model, size) the quantity, from section 15 (else the size table)
    bundles = {}
    for i, r in enumerate(mk['sizes']): bundles.setdefault((r['model'], r['size']), []).append(i)
    if mk.get('order_copy'):
        order_lines = [dict(model=m['name'], size=s['size'], quantity=s['quantity'], bundles=bundles.get((m['name'], s['size']), []))
                       for m in mk['order_copy'] for s in m['sizes']]
    else:
        order_lines = [dict(model=k[0], size=k[1], quantity=len(v), bundles=v) for k, v in bundles.items()]
        warnings.append('no order copy (section 15) read: order lines rebuilt from the size table')
    warnings += marker_warnings(mk)
    if not mk.get('laid_state_sources', {}).get('agree', True): warnings.append('laid-state sources disagree: %s' % mk['laid_state_sources'])
    if 'other' in mk['header_sums'].values(): warnings.append('header @422/@454 sums fit no known mode: %s' % mk['header_sums'])
    n_stream = sum(1 for e in slots if e.get('note', '').startswith(STREAM_NOTE))
    if slots and not pieces and not n_stream: warnings.append('no piece objects in the ZIP: no outlines, bounding boxes are the declared ones only')
    elif slots and not pieces: warnings.append('no piece objects in the ZIP: %d of %d slots have an outline from the marker\'s own stream, the rest have none' % (n_stream, len(slots)))
    for name in sorted(piece_errors): warnings.append('piece %r failed to decode: %s' % (name, piece_errors[name]))
    W = mk['width']; area = sum(s['declared_area'] for s in slots)
    by_size = Counter(s['size'] for s in slots); by_piece = Counter(s['piece'] for s in slots)
    geo = 'n/a' if not slots else ('all' if n_geo == len(slots) else ('none' if not n_geo else 'some'))
    return dict(
        marker=dict(name=mk['name'], width_in=W, width_cm=W*2.54, length_in=mk['length'], laid_state=mk['laid_state'],
                    lay_history=mk['lay_history'],
                    models=list(mk['models']), fabric_types=sorted({t for p in mk['pieces'] for t in p.get('fabric_types', [])}),
                    block_buffers=[list(b['sides']) for b in mk.get('block_buffers', [])], geometry_available=geo,
                    outline_source=('none' if not n_geo else ('stream' if n_stream == n_geo else ('piece' if not n_stream else 'mixed')))),
        order_lines=order_lines, slots=slots,
        totals=dict(slots=len(slots), placed=len(mk['placements']), area_to_lay=area,
                    perimeter=sum(s['perimeter'] or 0 for s in slots), min_length_in=area / W if W else None,
                    by_size=dict(by_size), by_piece=dict(by_piece)),
        warnings=warnings)

def place_marker(path, use_grading=True, as_unlaid=False):
    """Decode a marker ZIP: -> dict(marker, pieces, piece_errors, placed=[(slot,
    piece, size, outline_in_marker_frame or None, note)]).

    v4.2: every marker dict also carries `unplaced` (the same 5-tuples for the
    slots nothing is laid for, outline in the piece's own frame) and
    `inventory` (see unplaced_inventory); the result carries
    `geometry_available` - 'none' when the ZIP holds no decodable piece for the
    markers' slots, so a marker-only ZIP no longer reads like "all fine".

    v4.11 `as_unlaid`: treat every slot of a LAID marker as still to be laid - its positions are ignored, `unplaced` / `inventory` then describe the whole job
    (used to benchmark a nesting engine against the lay AccuMark itself made of the same job; `check_marker` is taken before the change)."""
    objs = list_zip(path)
    if 'marker' not in objs: raise NoSuchObject('no marker object in zip', source=str(path))
    pieces, piece_errors = load_pieces(objs)
    vocab = {n: [s['name'] for s in p['block']['meta']['sizes']] for n, p in pieces.items() if p}
    out = []
    for mo in objs['marker']:
        mk = parse_marker(mo['data'], vocab)
        placed = []
        for s in mk['placements']:
            piece = pieces.get(s['piece']) if s['piece'] else None
            if piece is None:
                if s['piece'] in piece_errors:
                    note = 'piece failed to decode: %s' % piece_errors[s['piece']]
                else:
                    note = 'piece not in ZIP' if s['piece'] else 'unbound slot'
                placed.append((s, s['piece'], s['size'], None, note)); continue
            outline, note = piece_outline(piece, s['size'] if use_grading else None)
            placed.append((s, s['piece'], s['size'], transform(outline, s), note))
        checks = check_marker(mk)
        if as_unlaid:
            for s in mk['slots']: s['empty'] = True
        unplaced = unplaced_slots(mk, pieces, piece_errors, use_grading)
        out.append(dict(marker=mk, placed=placed, unplaced=unplaced, checks=checks,
                        inventory=unplaced_inventory(mk, pieces, piece_errors, use_grading, geometry=unplaced)))
    have = sum(1 for p in pieces.values() if p)
    geo = 'none' if not have else ('all' if all(s.get('piece') in pieces and pieces[s['piece']] for m in out for s in m['marker']['slots']) else 'some')
    return dict(markers=out, pieces=pieces, piece_errors=piece_errors, objects=objs, geometry_available=geo)

def bbox_check(place_result, buffer_in=0.0, which='placed'):
    """No-DXF geometry test: the slot's home centre is the bbox centre of
    the placed (graded) piece in its own frame, so home*2 == bbox + 2*buffer
    on both axes [V dxfparser]. -> rows (piece, size, dx, dy) in inches.

    `which='unplaced'` (v4.2) runs it over the slots nothing is laid for; the
    buffer is then the marker's OWN per-piece block buffer (section 6, zero
    where there is none) and `buffer_in` is ignored."""
    rows = []
    for mkr in place_result['markers']:
        for s, name, size, outline, note in mkr[which]:
            if outline is None: continue
            base, _ = piece_outline(place_result['pieces'][name], size)
            xs = [p[0] for p in base]; ys = [p[1] for p in base]
            w, h = max(xs)-min(xs), max(ys)-min(ys)
            if which == 'unplaced':
                b = _buffer_sides(mkr['marker'], name)
                rows.append((name, size, s['home_x']*2 - w - (b[0]+b[1]), s['home_y']*2 - h - (b[2]+b[3])))
            else:
                rows.append((name, size, s['home_x']*2 - w - 2*buffer_in, s['home_y']*2 - h - 2*buffer_in))
    return rows

def area_check(place_result, which='placed'):
    """Declared area (the slot's record) vs the shoelace area of our finished
    outline at that size -> rows (piece, size, declared, ours, ratio).
    `which='unplaced'` (v4.2) runs it over the slots nothing is laid for."""
    def shoelace(p): return abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p))))/2
    rows = []; seen = set()
    for mkr in place_result['markers']:
        for s, name, size, outline, note in mkr[which]:
            if outline is None or (name, size) in seen: continue
            seen.add((name, size))
            base, _ = piece_outline(place_result['pieces'][name], size)
            a = shoelace(base)
            rows.append((name, size, s['area'], a, a/s['area'] if s['area'] else None))
    return rows

def inventory_report(inv, checks=()):
    """A readable cut order for one marker (the CLI's --inventory). Ends with
    DECODED CLEANLY, or NEEDS A LOOK plus every failing check and warning."""
    m, t = inv['marker'], inv['totals']
    state = ({'as_generated': 'UNLAID (as generated, never stored by Easy Marking)', 'stored_empty': 'UNLAID (stored by Easy Marking with nothing placed)'}[m['lay_history']]
             if m['laid_state'] == 'unlaid' else {'partial': 'PARTLY LAID', 'laid': 'LAID'}[m['laid_state']])
    lines = [f"== {m['name']} - {state} ==",
             f"width {m['width_cm']:.1f} cm ({m['width_in']:.2f} in) | models {', '.join(m['models']) or '-'} | "
             f"fabric types {', '.join(m['fabric_types']) or '-'} | block buffer "
             f"{('%d definitions, %s in' % (len(m['block_buffers']), ' / '.join(sorted({'%.4f' % max(b) for b in m['block_buffers']})))) if m['block_buffers'] else 'none'}"]
    n_cuts = sum(o['quantity'] for o in inv['order_lines'])
    lines.append(f"ORDER: {n_cuts} cuts over {len(inv['order_lines'])} (model, size) lines")
    for o in inv['order_lines']:
        lines.append(f"   {o['model']:24} size {o['size']:>7}  x{o['quantity']}")
    lines.append(f"TO LAY: {t['slots']} pieces ({t['placed']} already placed), area {t['area_to_lay']:.2f} sq in, "
                 f"perimeter {t['perimeter']:.1f} in" + (f", at least {t['min_length_in']:.1f} in of fabric at 100% efficiency"
                                                        if t['min_length_in'] else ''))
    per = {}
    for s in inv['slots']: per.setdefault((s['piece'], s['cut'], s['copies']), []).append(s)
    for (piece, cut, copies), ss in per.items():
        pair = ' (mirrored pair)' if copies == 2 and any(x['pair'] for x in ss) else ''
        lines.append(f"   {piece}  [{ss[0]['category']}]  {cut}{pair}: {len(ss)} slots over {len({x['size'] for x in ss})} sizes")
    pre = Counter((s['preset']['rot180'], s['preset']['mirror']) for s in inv['slots'])
    if pre: lines.append("PRE-SET lay pattern (reported, not placements): " +
                         ', '.join(f"{'rot180' if r else 'rot0'}{'+mirror' if mi else ''} x{n}" for (r, mi), n in sorted(pre.items())))
    geo = m['geometry_available']
    lines.append('GEOMETRY: ' + {'all': 'outlines for every slot', 'some': 'outlines for SOME slots', 'none': 'none - the ZIP holds no piece objects for these slots (declared areas / boxes only)',
                                 'n/a': 'n/a - nothing left to lay'}[geo])
    bad = [f'check failed: {n} ({d})' for n, ok, d in checks if not ok]
    notes = [w for w in inv['warnings'] if not w.startswith('no piece objects')]
    lines.append('DECODED CLEANLY' if not bad and not notes else 'NEEDS A LOOK:' + ''.join('\n   ' + x for x in bad + notes))
    return '\n'.join(lines)

if __name__ == '__main__':
    import json, sys
    if '--nest-spec' in sys.argv:                 # v4.7: the whole job as JSON / DXF / SVG for a nesting engine - see nest_spec.py
        import nest_spec; sys.exit(nest_spec.main([a for a in sys.argv[1:] if a != '--nest-spec']))
    args = [a for a in sys.argv[1:] if not a.startswith('--')]; flags = {a for a in sys.argv[1:] if a.startswith('--')}
    for path in args:
        res = place_marker(path)
        for mkr in res['markers']:
            mk = mkr['marker']
            if '--inventory' in flags:
                mkr['inventory']['warnings'] += coverage_warnings(mk)
                print(json.dumps(mkr['inventory'], default=str, indent=1) if '--json' in flags
                      else inventory_report(mkr['inventory'], mkr['checks']))
                continue
            print(f"{mk['name']}: W {mk['width']*2.54:.2f} cm  L {mk['length']*2.54:.2f} cm  U {mk['util']:.2f}%  "
                  f"{'laid' if mk['laid'] else 'UNLAID'}  {len(mk['placements'])} placements, {len(mk['bundles'])} bundles, "
                  f"{len(mk['records'])} records, {len(mk['pieces'])} pieces listed")
            print(f"   models: {', '.join(mk['models']) or '-'} | sizes: {', '.join(dict.fromkeys(r['size'] for r in mk['sizes'])) or '-'}")
            for name, ok, detail in mkr['checks']:
                print(f"   {'ok ' if ok else 'BAD'} {name}: {detail}")
            for s, name, size, outline, note in mkr['placed'][:8]:
                o = 'rot180' if s['rot'] == 180 else ('flipH' if s['flip_h'] else ('flipV' if s['flip_v'] else 'rot0'))
                print(f"   ({s['x']:8.3f},{s['y']:8.3f}) {o:6} bundle {s['bundle']:3}  {name} [{size}] {note}")
            if not mk['placements']:    # unlaid: nothing placed, so show what the marker does list
                for r in mk['records'][:8]:
                    print(f"   {r['piece']} [{r['size']}] {r['cut']!r}  area {r['area']:.4f}  perimeter {r['perimeter']:.4f}")
