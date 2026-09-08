
"""accumark_pds.py - decoder for Gerber AccuMark native piece files
(the .tmp member inside an AccuMark 'XGGT IXPORT DB5.1' export ZIP),
plus a parser for the companion ASTM/D6673 .RUL grade-rule table.
Reverse-engineered from a controlled A/B export set; see FORMAT_SPEC.md.
"""
import io, re, struct, zipfile

MAGIC = b'XGGT IXPORT DB5.'
UNITS_PER_INCH = 10000.0          # coordinates are int32 in 1e-4 inch

def u16(d,o): return int.from_bytes(d[o:o+2],'little')
def i16(d,o): return int.from_bytes(d[o:o+2],'little',signed=True)
def i32(d,o): return int.from_bytes(d[o:o+4],'little',signed=True)

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
    also tag 0x49). Two independent samples now agree the terminator, not
    the tag, is what signals open vs closed."""
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
    if r['f1'] == 0:
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
    r['notch_type'] = (r['f1'] >> 8) if r['is_notch'] else None
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
    for o in range(after, min(after+window, len(d)-14)):
        pid = i16(d,o)
        if pid in (1,-1) and COORD_LO < i32(d,o+2) < COORD_HI and COORD_LO < i32(d,o+6) < COORD_HI \
           and u16(d,o+10) in (0,1,2,0x101):
            return o
    raise ValueError('point table not found after %#x' % after)

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
    # each is header + points + u32 3 + zero padding + its 'Lnn' label
    internal = []; internal_kinds = []; internal_labels = []; o = after
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
        label, past = _internal_list_label(d, o)
        internal_labels.append(label)
        if label is not None and _is_internal_header(d, past):
            o = past; continue
        break                      # block_end stays at the last list's u32 3
    return dict(meta=m, objects=objs, points_offset=pstart, perimeter=perim,
                closing=closing, internal_lines=internal, internal_kinds=internal_kinds,
                internal_labels=internal_labels, block_end=o)

def decode(data):
    """Decode a full piece file; returns dict with one or more piece blocks."""
    if not data.startswith(MAGIC):
        raise ValueError('not an AccuMark IXPORT piece file')
    hdr = dict(magic=data[:18].decode('latin1').rstrip('\x00'),
               db_version=data[16:19].decode('latin1').rstrip('\x00'))
    # trailing piece-name + two identical unix timestamps
    tail = data[-160:]
    ts = []
    for o in range(len(data)-160, len(data)-4):
        v = i32(data,o)
        if 1_500_000_000 < v < 2_200_000_000: ts.append(v)
    blocks = []; off = None
    while True:
        try: off = _find_field_block(data, (blocks[-1]['block_end'] if blocks else 0x60),
                                     (blocks[-1]['block_end']+0x120 if blocks else 0x140))
        except ValueError: break
        try: b = decode_piece_block(data, off)
        except Exception: break
        blocks.append(b)
        if b['block_end'] >= len(data)-8: break
        if len(blocks) > 8: break
    return dict(header=hdr, timestamps=sorted(set(ts)), blocks=blocks)

def decode_zip(path):
    z = zipfile.ZipFile(path)
    name = [n for n in z.namelist() if n.lower().endswith('.tmp')][0]
    return decode(z.read(name))

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
        recs.append(dict(fields_offset=o+3, n_lines=pre, n_points=n_pts,
                         seam_flag=flag,
                         seam_begin=seam[0] if seam else None,
                         seam_end=seam[1] if seam else None,
                         name=d[labels[k+1]:labels[k+1]+3].decode() if k+1 < len(labels) else None))
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
                        pts=[(q['x'],q['y']) for q in pts]))
    return out

def summarize(data):
    """High-level, validated summary of a piece file."""
    dec = decode(data)
    d = data
    blocks = []
    o = 0x60
    while o < len(d)-40:
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
        object_records = [(o_['id'], o_['payload']) for o_ in b0['objects']],
    )

def summarize_zip(path):
    z = zipfile.ZipFile(path)
    name = [n for n in z.namelist() if n.lower().endswith('.tmp')][0]
    return summarize(z.read(name))
