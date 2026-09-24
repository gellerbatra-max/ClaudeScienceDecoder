#!/usr/bin/env python3
"""accumark_laylimits - read an AccuMark LAY LIMITS table (object type 6, `.GT_lay`) and turn a row into the
orientation rules a nesting engine needs (v4.8).

    python accumark_laylimits.py "<export>.zip" [--json]       # every lay-limits table in a ZIP
    python accumark_laylimits.py C:\\userroot\\storage\\AREA\\lay\\NAME.GT_lay    # a table file straight from a storage area

What a Lay Limits table is (Gerber help, "Lay Limits Editor"): the general rules for how pieces may be placed - how the fabric is spread
(single ply / face to face / book fold / tubular), how the bundles are laid (all one direction / alternate bundles reversed / same size one
direction), and one row per piece CATEGORY (plus DEFAULT for every other one) with the piece options M W S 9 4 F O N X P U Z, a flip code, a
block / buffer rule number, a tilt limit and a weft skew.

Byte format, VERIFIED against the editor's own grid on six tables (ZZLL-1, -X1, -X2, -X3 were built one setting at a time in the Lay Limits Editor and
diffed; `L` and `SINGLE-PLY` are the older vintage) and the recorded settings of nine single-row tables - see MARKER_FORMAT_SPEC.md section 16:

    table (a `.GT_lay` file has these bytes from 0x90, an export ZIP object from 0x8a, `payload_len` of them):
      u16 line1_len, u16 line2_len    the comment, wrapped at 20 characters
      u8 spread                       0 single ply, 1 face to face, 2 book fold, 3 tubular
      u8 bundling                     0 all bundles same direction, 1 alternate bundles alternate direction, 2 same size same direction
      u16 n_rows
      u8 per_model, 7 x 00
      comment text (line1_len + line2_len characters)
      n_rows x ( u16 name_len, u8 b2, u8 b3, u8 flip_code, u8 units_flag, u16 buffer_rule, i32 tilt_cw, i32 tilt_ccw, name )
          b3  piece options  M 0x80, W 0x40, S 0x20, 9 0x10, 4 0x08, F 0x04, O 0x02, N 0x01
          b2  piece options  U 0x80, X 0x40, Z 0x10, P 0x08;  0x20 = the tilt unit is DEGREES (units_flag is then 1);  0x07: not meaning-bearing
          tilt   the tilt limit x 10000, in INCHES (a length tilt shown as cm is converted) or in DEGREES when the unit flag is set
      u32 1, u32 0
      u32 4 * n_rows, n_rows x i32   weft skew x 10000, in degrees
      u32 0x7f, u32 0
      u32 length, u32 n_properties, n_properties x ( u32 length, u32 1, u32 0, u32 len, name, u32 4 + len2, u32 len2, text )
          the one property seen is `Category group` = the group column as a comma list ("0,0,3,0,0,0"); absent when every group is 0

The older vintage (`.GT_lay` type byte 4: the user's real `L` table, `SINGLE-PLY`) keeps a 40-character comment, then spread, bundling, u16
n_rows and the row with a name padded to 20 characters; only single-row tables are read (spread, bundling, options, flip code and buffer rule
verified against the editor on `L` and `SINGLE-PLY`); its tilt / skew bytes are zero in every sample and are reported only when they are.
"""
import json, os, struct, sys, zipfile

__version__ = '1.0'

SPREADS = {0: 'single_ply', 1: 'face_to_face', 2: 'book_fold', 3: 'tubular'}
BUNDLINGS = {0: 'all_bundle_same_direction', 1: 'alternate_bundle_alternate_direction', 2: 'same_size_same_direction'}
BUNDLING_LABELS = {0: 'All Bundle, Same Direction', 1: 'Alternate Bundle, Alternate Direction', 2: 'Same Size, Same Direction'}
SPREAD_LABELS = {0: 'Single Ply', 1: 'Face To Face', 2: 'Book Fold', 3: 'Tubular'}
OPTION_ORDER = 'MWS94FONXPUZ'
OPTION_MEANING = {'M': 'major piece', 'W': 'one way: flip about the X axis, no rotation', 'S': '180 degree rotation, no flip', '9': 'allows 90 degree rotation',
                  '4': 'allows 45 degree rotation', 'F': 'allows folds for mirrored pieces', 'O': 'optional piece', 'N': 'do not plot', 'X': 'do not cut',
                  'P': 'pair orientation maintained', 'U': 'area not included in the marker', 'Z': 'may lie completely inside a splice mark'}
_B3 = (('M', 0x80), ('W', 0x40), ('S', 0x20), ('9', 0x10), ('4', 0x08), ('F', 0x04), ('O', 0x02), ('N', 0x01))
_B2 = (('U', 0x80), ('X', 0x40), ('Z', 0x10), ('P', 0x08))
_B2_DEGREES = 0x20
# the editor's own labels; `rotate_deg` counter-clockwise, `flip` about the named axis (x_axis: y -> -y, y_axis: x -> -x), rotation first
FLIP_CODES = {1: ('Original Digitized Position', 0, None), 2: ('Rotate 180 Degrees', 180, None), 3: ('Flip about Y-axis', 0, 'y_axis'),
              4: ('Flip about X-axis', 0, 'x_axis'), 5: ('Rotate 90 degrees, CCW, Flip X-axis', 90, 'x_axis'), 6: ('Rotate 90 degrees, CCW', 90, None),
              7: ('Rotate 90 degrees, CW', -90, None), 8: ('Rotate 90 degrees, CW, Flip X-axis', -90, 'x_axis'),
              9: ('Rotate 45 degrees, CCW, Flip X-axis', 45, 'x_axis'), 10: ('Rotate 45 degrees, CCW', 45, None),
              11: ('Rotate 45 degrees, CW', -45, None), 12: ('Rotate 45 degrees, CW, Flip X-axis', -45, 'x_axis')}
_MAGIC_OFF = 0x90       # a storage-area `.GT_lay` file = 0x90 bytes of envelope + the table
_EXPORT_OFF = 0x8a      # in an export ZIP object the table starts 10 bytes into the payload region (after `00 00 90 00 00 00 00 00 00 00`) and is `payload_len` long


class LayLimitsError(ValueError):
    pass


def _u16(b, o): return struct.unpack_from('<H', b, o)[0]
def _u32(b, o): return struct.unpack_from('<I', b, o)[0]
def _i32(b, o): return struct.unpack_from('<i', b, o)[0]


def _printable(b): return all(32 <= c < 127 for c in b)


def _row(name, b2, b3, flip, uflag, rule, cw, ccw, raw):
    letters = [l for l, m in _B3 if b3 & m] + [l for l, m in _B2 if b2 & m]
    letters.sort(key=OPTION_ORDER.index)
    degrees = bool(b2 & _B2_DEGREES)
    fl = FLIP_CODES.get(flip)
    return dict(category=name, options=''.join(letters), flip_code=flip,
                flip=dict(label=fl[0], rotate_deg=fl[1], flip=fl[2]) if fl else None,
                buffer_rule=rule, tilt_unit='degrees' if degrees else 'length',
                tilt_cw=cw / 1e4 if cw is not None else None, tilt_ccw=ccw / 1e4 if ccw is not None else None,
                units_consistent=(uflag == 1) == degrees, raw=raw)


def _parse_v5(p):
    if len(p) < 16 + 16: raise LayLimitsError('payload too short')
    l1, l2 = _u16(p, 0), _u16(p, 2); spread, bund, n = p[4], p[5], _u16(p, 6)
    if l1 > 40 or l2 > 40 or spread not in SPREADS or bund not in BUNDLINGS or not 1 <= n <= 200 or any(p[9:16]):
        raise LayLimitsError('header does not look like a V17 lay-limits table')
    comment = p[16:16 + l1 + l2]
    if not _printable(comment): raise LayLimitsError('comment is not text')
    pos = 16 + l1 + l2; rows = []
    for _ in range(n):
        if pos + 16 > len(p): raise LayLimitsError('row chain runs past the payload')
        nl = _u16(p, pos)
        if not 1 <= nl <= 64 or pos + 16 + nl > len(p): raise LayLimitsError('bad row name length')
        name = p[pos + 16:pos + 16 + nl]
        if not _printable(name): raise LayLimitsError('row name is not text')
        h = p[pos:pos + 16]
        rows.append(_row(name.decode('latin1'), h[2], h[3], h[4], h[5], _u16(h, 6), _i32(h, 8), _i32(h, 12), h.hex()))
        pos += 16 + nl
    t = p[pos:]
    if len(t) < 8 + 4 + 4 * n + 8 + 8 or _u32(t, 0) != 1 or _u32(t, 8) != 4 * n: raise LayLimitsError('trailer does not start with the weft-skew array')
    skew = [_i32(t, 12 + 4 * i) / 1e4 for i in range(n)]
    q = 12 + 4 * n
    if _u32(t, q) != 0x7f: raise LayLimitsError('missing 0x7f marker after the weft-skew array')
    q += 8; props = {}
    plen, pcount = _u32(t, q), _u32(t, q + 4)
    if q + 4 + plen != len(t): raise LayLimitsError('property block does not close at the end of the payload')
    e = q + 8
    for _ in range(pcount):
        el = _u32(t, e); body = t[e:e + el]
        if len(body) != el or body[4:12] != b'\x01\x00\x00\x00\x00\x00\x00\x00': raise LayLimitsError('property entry header')
        nl = _u32(body, 12); vt, vl = _u32(body, 16 + nl), _u32(body, 16 + nl + 4)
        if el != 24 + nl + vl or vt != 4 + vl or not _printable(body[16:16 + nl]) or not _printable(body[16 + nl + 8:]): raise LayLimitsError('property entry does not close')
        props[body[16:16 + nl].decode('latin1')] = body[16 + nl + 8:].decode('latin1'); e += el
    if e != len(t): raise LayLimitsError('property entries do not close at the end of the payload')
    groups = [int(x) for x in props['Category group'].split(',')] if 'Category group' in props else [0] * n
    if len(groups) != n: raise LayLimitsError('group list length differs from the row count')
    for r, s, g in zip(rows, skew, groups): r['weft_skew_deg'] = s; r['group'] = g
    return dict(vintage='v5', spread=spread, bundling=bund, per_model=bool(p[8]), comment=comment.decode('latin1'), rows=rows, properties=props,
                basis='decoded: every field verified against the Lay Limits Editor grid')


def _parse_v4(p):
    if len(p) < 44 + 20 + 6: raise LayLimitsError('payload too short')
    spread, bund, n = p[40], p[41], _u16(p, 42)
    if spread not in SPREADS or bund not in BUNDLINGS or n != 1: raise LayLimitsError('not a single-row older-vintage lay-limits table')
    name = p[44:64].decode('latin1').rstrip(' \x00')
    if not name or not _printable(p[44:64].rstrip(b'\x00')): raise LayLimitsError('row name is not text')
    b2, b3, flip, rule = p[64], p[65], p[66], _u16(p, 68)
    rest = p[70:]
    zero = not any(rest)
    r = _row(name, b2, b3, flip, 0, rule, 0 if zero else None, 0 if zero else None, p[64:].hex())
    r['tilt_unit'] = 'length'; r['units_consistent'] = True
    r['weft_skew_deg'] = 0.0 if zero else None; r['group'] = 0
    comment = p[:40].decode('latin1').replace('\x00', ' ').strip()
    return dict(vintage='v4', spread=spread, bundling=bund, per_model=False, comment=comment, rows=[r], properties={},
                basis='partial: single-row older-vintage table; spread, bundling, options, flip code and buffer rule verified against the editor'
                      + ('' if zero else '; tilt / skew bytes are non-zero and not decoded'))


def parse_lay_limits(source, name=None):
    """Lay Limits table -> dict(name, vintage, spread, spread_label, bundling, bundling_label, per_model, comment, rows, properties, basis, warnings).
    `source` is an object dict from accumark_marker.list_zip, the raw table bytes, or a `.GT_lay` file path. Raises LayLimitsError
    when the bytes do not close exactly - an unseen variant is refused, never guessed."""
    if isinstance(source, str):
        d = open(source, 'rb').read(); payload = d[_MAGIC_OFF:]; name = name or os.path.splitext(os.path.basename(source))[0]
    elif isinstance(source, dict):
        d = source['data']; payload = bytes(d[_EXPORT_OFF:_EXPORT_OFF + source['payload_len']]); name = name or source.get('name')
        if len(payload) != source['payload_len']: raise LayLimitsError('object shorter than its own payload length')
    else: payload = bytes(source)
    errs = []
    for fn in (_parse_v5, _parse_v4):
        try: t = fn(payload); break
        except (LayLimitsError, struct.error, IndexError, KeyError, ValueError) as e: errs.append(f'{fn.__name__[1:]}: {e}')
    else: raise LayLimitsError('unrecognised lay-limits table (' + '; '.join(errs) + ')')
    t.update(name=name, spread_label=SPREAD_LABELS[t['spread']], spread_name=SPREADS[t['spread']], bundling_name=BUNDLINGS[t['bundling']],
             bundling_label=BUNDLING_LABELS[t['bundling']], warnings=[])
    if not any(r['category'].upper() == 'DEFAULT' for r in t['rows']): t['warnings'].append('no DEFAULT row: pieces of an unlisted category have no rule')
    for r in t['rows']:
        if r['flip_code'] not in FLIP_CODES: t['warnings'].append(f"{r['category']}: flip code {r['flip_code']} is not one of 1-12")
        if not r['units_consistent']: t['warnings'].append(f"{r['category']}: the two unit flags disagree")
    return t


def row_for(table, category):
    """The row that governs a piece of `category`: its own row, else DEFAULT (case-insensitive) - [row, 'category' | 'default' | None]."""
    up = (category or '').upper()
    for r in table['rows']:
        if r['category'].upper() == up and up != 'DEFAULT': return r, 'category'
    for r in table['rows']:
        if r['category'].upper() == 'DEFAULT': return r, 'default'
    return None, None


def orientation_rules(row, table=None):
    """What a nesting engine may do with a piece under one row (Gerber help, "Piece Options"): blank options allow a 180 degree rotation and a
    flip about the X axis; W removes the rotation (one-way), S removes the flip, W and S together lock the piece; 9 adds the 90 degree
    rotations, 4 every 45 degree step. A permission is not an obligation: the marker's `mirrored` demand says which instances are mirror images. `initial_orientation`
    is the flip code - how the piece is turned when it is first picked from the Marker Making menu (a lay pattern the nester need not follow)."""
    o = set(row['options']); fl = row['flip']
    rot = [0] + ([] if 'W' in o else [180]) + ([90, 270] if '9' in o else []) + ([45, 90, 135, 225, 270, 315] if '4' in o else [])
    notes = []
    if 'W' in o and o & set('94'): notes.append('W (no rotation) is combined with 9 / 4: the extra rotations are listed as allowed, check the table')
    tilt = None
    if row['tilt_cw'] or row['tilt_ccw']:
        tilt = dict(unit=row['tilt_unit'], cw=row['tilt_cw'], ccw=row['tilt_ccw'])
    return dict(allowed_deg=sorted(set(rot)), flip_x_axis_allowed='S' not in o, locked=('W' in o and 'S' in o),
                initial_orientation=dict(code=row['flip_code'], **(fl or {})), tilt_limit=tilt, weft_skew_deg=row.get('weft_skew_deg'),
                buffer_rule=row['buffer_rule'], group=row.get('group'), options=row['options'],
                flags={k: (k in o) for k in ('M', 'F', 'O', 'N', 'X', 'P', 'U', 'Z') if k in o}, notes=notes)


def load_zip_tables(path, listing=None):
    """{table name: parsed table} for every lay-limits object of an export ZIP (unparseable ones are skipped and listed in `_errors`); `listing` = an
    accumark_marker.list_zip result already in hand."""
    import accumark_marker as am
    out = {}; errs = []
    for o in (listing if listing is not None else am.list_zip(path)).get('lay_limits', []):
        try: out[o['name']] = parse_lay_limits(o)
        except LayLimitsError as e: errs.append((o['name'], str(e)))
    if errs: out['_errors'] = errs
    return out


def describe(t):
    L = [f"{t.get('name')}  [{t['vintage']}]  spread: {t['spread_label']}  bundling: {t['bundling_label']}" + ('  per model' if t['per_model'] else '')]
    if t['comment'].strip(): L.append(f"  comment: {t['comment']}")
    for r in t['rows']:
        tl = '' if not (r['tilt_cw'] or r['tilt_ccw']) else f"  tilt {r['tilt_cw']}/{r['tilt_ccw']} {'deg' if r['tilt_unit'] == 'degrees' else 'in'}"
        L.append(f"  {r['category']:<18} options {r['options'] or '-':<6} flip {r['flip_code']:>2} ({(r['flip'] or {}).get('label', '?')})  rule {r['buffer_rule']}"
                 f"  group {r.get('group')}  skew {r.get('weft_skew_deg')}{tl}")
    return '\n'.join(L)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv); as_json = '--json' in a; a = [x for x in a if x != '--json']
    if not a: print(__doc__); return 2
    tabs = {}
    for f in a:
        if f.lower().endswith('.zip'): tabs.update({f'{os.path.basename(f)}:{k}': v for k, v in load_zip_tables(f).items() if k != '_errors'})
        else: tabs[f] = parse_lay_limits(f)
    if as_json: print(json.dumps({k: {x: y for x, y in v.items()} for k, v in tabs.items()}, indent=1, default=str))
    else:
        for k, v in tabs.items(): print(describe(v))
    return 0


if __name__ == '__main__':
    sys.exit(main())
