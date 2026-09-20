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
                         buffer_index=None if buf == 0xffff else buf, raw=d[pos+4:pos+28].hex()))
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
    return mk

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
        out.append(('sum(slot areas) == W*L*U', abs(mk['sum_slot_areas'] - W*L*U/100) < 1e-2,
                    f'{mk["sum_slot_areas"]:.4f} vs {W*L*U/100:.4f}; @422={A:.4f}'))
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
    return out

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
    return dict(name=obj['name'], object=obj, models=models, strings=strs[:4])

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
    (curve points, f1 == 1) move by chain-proportional interpolation between
    their neighbouring ruled points - the rule the user settled for
    dxfparser (2026-08-02). Returns None if the size is not in the table."""
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
        chain = [xy[i]] + [xy[q] for q in seq] + [xy[j]]
        acc = _chain_lengths(chain); total = acc[-1] or 1.0
        for idx, q in enumerate(seq):
            f = acc[idx+1]/total
            mx = moves[i][0]*(1-f) + moves[j][0]*f
            my = moves[i][1]*(1-f) + moves[j][1]*f
            out[q] = (xy[q][0]+mx, xy[q][1]+my)
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

def place_marker(path, use_grading=True):
    """Decode a marker ZIP: -> dict(marker, pieces, piece_errors, placed=[(slot,
    piece, size, outline_in_marker_frame or None, note)])."""
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
        out.append(dict(marker=mk, placed=placed, checks=check_marker(mk)))
    return dict(markers=out, pieces=pieces, piece_errors=piece_errors, objects=objs)

def bbox_check(place_result, buffer_in=0.0):
    """No-DXF geometry test: the slot's home centre is the bbox centre of
    the placed (graded) piece in its own frame, so home*2 == bbox + 2*buffer
    on both axes [V dxfparser]. -> rows (piece, size, dx, dy) in inches."""
    rows = []
    for mkr in place_result['markers']:
        for s, name, size, outline, note in mkr['placed']:
            if outline is None: continue
            base, _ = piece_outline(place_result['pieces'][name], size)
            xs = [p[0] for p in base]; ys = [p[1] for p in base]
            w, h = max(xs)-min(xs), max(ys)-min(ys)
            rows.append((name, size, s['home_x']*2 - w - 2*buffer_in, s['home_y']*2 - h - 2*buffer_in))
    return rows

def area_check(place_result):
    """Declared area (the slot's record) vs the shoelace area of our finished
    outline at that size -> rows (piece, size, declared, ours, ratio)."""
    def shoelace(p): return abs(sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p))))/2
    rows = []; seen = set()
    for mkr in place_result['markers']:
        for s, name, size, outline, note in mkr['placed']:
            if outline is None or (name, size) in seen: continue
            seen.add((name, size))
            base, _ = piece_outline(place_result['pieces'][name], size)
            a = shoelace(base)
            rows.append((name, size, s['area'], a, a/s['area'] if s['area'] else None))
    return rows

if __name__ == '__main__':
    import sys
    for path in sys.argv[1:]:
        res = place_marker(path)
        for mkr in res['markers']:
            mk = mkr['marker']
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
