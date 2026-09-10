"""accumark_marker.py - reader for the non-piece objects of an AccuMark
'XGGT IXPORT DB5.1' export ZIP: the marker (type 9), its order (13), models
(12) and the parameter tables, plus placement of decoded pieces on a laid
marker.

Format knowledge: MARKER_DECODE_PLAN.md (this repo) and, for the slot
layout and the slot->piece binding, gellerbatra-max/dxfparser
docs/accumark-decoded-so-far.md section 6 (verified there on 2,830 placements).

    import accumark_marker as am
    objs = am.list_zip('2303-BD 137 PLACED.zip')          # every object, typed
    mk   = am.parse_marker(objs['marker'][0]['data'])       # header + placements
    laid = am.place_marker('2303-BD 137 PLACED.zip')        # outlines in the marker frame
"""
import math, re, struct, zipfile
import accumark_pds as ap

u16, i16, i32, u32 = ap.u16, ap.i16, ap.i32, ap.u32
def f64(d, o): return struct.unpack_from('<d', d, o)[0]

MAGIC = b'XGGT IXPORT DB5.'
TRAILER = 396
OBJECT_TYPES = {20: 'piece', 12: 'model', 13: 'order', 9: 'marker',
                10: 'marker_geometry', 2: 'annotation', 3: 'block_buffer',
                6: 'lay_limits', 17: 'notch_table', 23: 'rule_table'}

# ------------------------------------------------------------ envelope
def read_object(d):
    """Envelope shared by every object type and both export vintages [V]:
    name at 0x15, type u16 at 0x7a (the u32 copy is at 0x60 or 0x68
    depending on vintage), payload length u32 at 0x7e, payload from 0x80,
    396-byte trailer with created/modified Unix stamps and user names."""
    if not d.startswith(MAGIC): raise ValueError('not an AccuMark IXPORT object')
    name = d[0x15:d.index(b'\x00', 0x15)].decode('latin1')
    t = u16(d, 0x7a); plen = u32(d, 0x7e)
    tr = d[-TRAILER:]
    stamps = [u32(tr, o) for o in range(0, len(tr)-4)
              if 1_400_000_000 < u32(tr, o) < 2_200_000_000]
    users = [m.group().decode('latin1') for m in re.finditer(rb'[A-Za-z][A-Za-z0-9]{1,30}', tr)]
    return dict(name=name, type=t, kind=OBJECT_TYPES.get(t, 'unknown_%d' % t),
                payload_len=plen, size=len(d), payload=d[0x80:0x80+plen],
                created=stamps[0] if stamps else None,
                modified=stamps[1] if len(stamps) > 1 else None,
                users=users, data=d)

def list_zip(path):
    """{kind: [object, ...]} for every XGGT member of an export ZIP."""
    out = {}
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            d = z.read(n)
            if not d.startswith(MAGIC): continue
            o = read_object(d); o['member'] = n
            out.setdefault(o['kind'], []).append(o)
    return out

# -------------------------------------------------------------- strings
def _len_after_strings(d, lo, hi, minlen=3):
    """Strings stored as <chars><u16 len> (the marker's model and size lists
    write the length AFTER the text). Returns [(offset, text)]."""
    out = []
    for m in re.finditer(rb'[\x20-\x7e]{%d,}' % minlen, d[lo:hi]):
        s = m.group(); o = lo + m.start()
        # the run may glue several strings together (`...B1 1\x0f\x00` breaks
        # them, so usually not) - accept when the u16 after it equals its length
        if o+len(s)+2 <= hi and u16(d, o+len(s)) == len(s):
            out.append((o, s.decode('latin1')))
    return out

# --------------------------------------------------------------- marker
DIR_OFF, DIR_SLOTS = 0x8a, 42
SLOT = 96
SEC_SCALARS, SEC_PIECES, SEC_MODELS, SEC_SIZES, SEC_INDEX, SEC_RECORDS, SEC_ORDER_COPY, SEC_SLOTS, SEC_GEOMETRY = 1, 10, 11, 12, 13, 14, 15, 21, 30
ROT180_BIT, MIRROR_BIT = 0x2000, 0x0080

def directory(d):
    """42 u32 ABSOLUTE file offsets at 0x8a; 0xffffffff = section absent [V]."""
    return [u32(d, DIR_OFF+4*i) for i in range(DIR_SLOTS)]

def _section(d, dirs, k):
    a = dirs[k]
    if a in (0xffffffff, 0): return None
    later = [v for v in dirs if v not in (0xffffffff, 0) and v > a]
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

def parse_pieces_section(d, lo, hi):
    """Section 10: per placed piece `<name><fabric code>\\x01\\x00<flag>` with
    the two string lengths and 22 flag bytes stored just before the text [V]."""
    out = []
    for m in re.finditer(rb'([\x20-\x7e]{8,})\x01\x00([A-Z])', d[lo:hi]):
        o = lo + m.start(); s = m.group(1).decode('latin1')
        n1, n2 = u16(d, o-28), u16(d, o-26)     # lengths lead the 24 flag bytes
        if n1 + n2 == len(s): name, fabric = s[:n1], s[n1:]
        else: name, fabric = s, ''
        out.append(dict(offset=o, name=name, fabric=fabric, flag=chr(m.group(2)[0]),
                        raw=d[o-24:o].hex()))
    return out

def parse_sizes_section(d, lo, hi):
    """Section 12: one row per (model, size) the order requests, each
    `<size name><u16 f0><u16 model index, 1-based><u16 pieces in model>
    <u32 ordinal><ffff><0000>` [V for model index / pieces / ordinal on
    2303-BD 137: 59 rows = the order's 59 (model,size) lines]. The name is
    delimited by the `ff ff 00 00` that ends the previous row; `f0` takes
    1/3/4 and is not the string length [?]."""
    out = []
    for m in re.finditer(rb'(?:^|\xff\xff\x00\x00)(\d{1,2}[A-Z]{0,3})(?=[\x00-\x1f])', d[lo:hi]):
        o = lo + m.start(1); s = m.group(1).decode('latin1'); p = o+len(s)
        out.append(dict(size=s, f0=u16(d, p), model_index=u16(d, p+2), n=u16(d, p+4),
                        ordinal=u32(d, p+6)))
    return out

def parse_slots(d, lo, hi):
    """Section 21: contiguous 96-byte placement slots [V] (dxfparser layout)."""
    out = []
    for s in range(lo, hi-SLOT+1, SLOT):
        px, py, hx, hy = struct.unpack_from('<dddd', d, s)
        out.append(dict(slot=s, x=px, y=py, home_x=hx, home_y=hy,
                        orient_code=u16(d, s+32), area=f64(d, s+42),
                        bundle=u32(d, s+64) & 0xffff, bundle_flags=u32(d, s+64) >> 16,
                        raw=d[s:s+SLOT].hex(), **decode_orient(u16(d, s+32))))
    return out

def parse_marker(d, size_vocab=None):
    """Everything readable in a marker object. `size_vocab` = {piece name:
    [size names]} from the piece objects of the same ZIP, used to split the
    record strings; without it the size is taken by pattern."""
    obj = read_object(d)
    if obj['type'] != 9: raise ValueError('not a marker object (type %d)' % obj['type'])
    dirs = directory(d)
    sec = {k: _section(d, dirs, k) for k in range(DIR_SLOTS)}
    mk = dict(name=obj['name'], object=obj, directory=dirs, sections=sec,
              width=f64(d, 396), length=f64(d, 412), total_area=f64(d, 422),
              util=f64(d, 446), unknown_454=f64(d, 454))
    mk['laid'] = mk['length'] > 0 and mk['util'] > 0
    mk['piece_names'] = declared_piece_names(d)
    mk['pieces'] = parse_pieces_section(d, *sec[SEC_PIECES]) if sec[SEC_PIECES] else []
    # the directory's model-list offset lands 4 bytes into the first name on
    # both vintages [V]; the piece-list strings before it end in `01 00 41`
    # and cannot pass the length-after test, so widening the window is safe
    mk['models'] = ([s for _, s in _len_after_strings(d, sec[SEC_MODELS][0]-48, sec[SEC_MODELS][1])]
                    if sec[SEC_MODELS] else [])
    mk['sizes'] = parse_sizes_section(d, *sec[SEC_SIZES]) if sec[SEC_SIZES] else []
    mk['records'] = piece_records(d, *sec[SEC_RECORDS]) if sec[SEC_RECORDS] else []
    # section 13: u32 cumulative byte offsets of the section-14 records; the
    # array starts 6 bytes before the directory offset [?] (66 values for 66
    # records on 2303-BD 137; consecutive differences are the record lengths)
    mk['record_index'] = []
    if sec[SEC_INDEX] and sec[SEC_RECORDS]:
        n = (sec[SEC_INDEX][1] - sec[SEC_INDEX][0]) // 4
        vals = [u32(d, sec[SEC_INDEX][0]-6+4*k) for k in range(n)]
        if all(vals[k] < vals[k+1] for k in range(len(vals)-1)): mk['record_index'] = vals
    mk['slots'] = parse_slots(d, *sec[SEC_SLOTS]) if sec[SEC_SLOTS] else []
    # split every record text: piece / cut description / size
    by_piece = {}
    for r in mk['records']:
        name, _, _ = split_record(r['text'], mk['piece_names'])
        r['piece'] = name
        # a record whose text matches no declared piece name never enters
        # by_piece below, so it never gets 'cut'/'size' set there - default
        # them here so a slot binding to this record (by area) doesn't KeyError
        r['cut'] = None; r['size'] = None
        if name: by_piece.setdefault(name, []).append(r)
    for name, recs in by_piece.items():
        vocab = (size_vocab or {}).get(name) or []
        res = sizes_for_piece([r['text'] for r in recs], name, vocab) if vocab else {}
        for r in recs:
            desc, size = res.get(r['text']) or split_record(r['text'], [name], vocab)[1:]
            r['cut'] = desc; r['size'] = size
    # bind slots to records by declared area (nearest within tolerance, no
    # rival within 10x the gap - dxfparser's rule)
    placements = []
    for s in mk['slots']:
        empty = (abs(s['x']) < 1e-9 and abs(s['y']) < 1e-9) or s['x'] < -900
        s['empty'] = empty
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
        if not empty: placements.append(s)
    mk['placements'] = placements
    mk['bundles'] = sorted({p['bundle'] for p in placements})
    mk['sum_slot_areas'] = sum(p['area'] for p in placements)
    return mk

def check_marker(mk):
    """Identities a correct read must satisfy; -> list of (name, ok, detail)."""
    out = []
    W, L, U, A = mk['width'], mk['length'], mk['util'], mk['total_area']
    if mk['laid']:
        # W*L*U/100 == sum of the placed slots' declared areas held on both
        # vintages; the double at 422 equals it on the 2026-09 export but
        # holds something else on the 2026-07 one [?], so it is reported, not asserted
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
    if obj['type'] != 13: raise ValueError('not an order object')
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
    if obj['type'] != 12: raise ValueError('not a model object')
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
    pieces = {}
    for o in objs.get('piece', []):
        try: pieces[o['name']] = dict(block=ap.decode(o['data'])['blocks'][0], data=o['data'])
        except Exception: pieces[o['name']] = None
    return pieces

def place_marker(path, use_grading=True):
    """Decode a marker ZIP: -> dict(marker, pieces, placed=[(slot, piece,
    size, outline_in_marker_frame or None, note)])."""
    objs = list_zip(path)
    if 'marker' not in objs: raise ValueError('no marker object in %s' % path)
    pieces = load_pieces(objs)
    vocab = {n: [s['name'] for s in p['block']['meta']['sizes']] for n, p in pieces.items() if p}
    out = []
    for mo in objs['marker']:
        mk = parse_marker(mo['data'], vocab)
        placed = []
        for s in mk['placements']:
            piece = pieces.get(s['piece']) if s['piece'] else None
            if piece is None:
                placed.append((s, s['piece'], s['size'], None, 'piece not in ZIP' if s['piece'] else 'unbound slot')); continue
            outline, note = piece_outline(piece, s['size'] if use_grading else None)
            placed.append((s, s['piece'], s['size'], transform(outline, s), note))
        out.append(dict(marker=mk, placed=placed, checks=check_marker(mk)))
    return dict(markers=out, pieces=pieces, objects=objs)

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
            for name, ok, detail in mkr['checks']:
                print(f"   {'ok ' if ok else 'BAD'} {name}: {detail}")
            for s, name, size, outline, note in mkr['placed'][:8]:
                o = 'rot180' if s['rot'] == 180 else ('flipH' if s['flip_h'] else ('flipV' if s['flip_v'] else 'rot0'))
                print(f"   ({s['x']:8.3f},{s['y']:8.3f}) {o:6} bundle {s['bundle']:3}  {name} [{size}] {note}")
