#!/usr/bin/env python3
"""accumark_engine - read the nest engine's own INPUT FILE (`frommed.mra`) (v4.24).

    python accumark_engine.py "<job>\\frommed.mra" [--json]

For every AccuNest job the Queue front end writes `C:\\Users\\Public\\Gerber Technology\\Queue\\ultramrk_umq\\<job>\\frommed.mra`: a plain-text rendering of everything the engine is told about the job, made from the marker, its
order and its tables (`intomed.mra` is what the engine wrote back). Blocks of `KEY value` lines: a header (`MARKER_NAME`, `MARKER_WIDTH`, `SPREAD`, `GLOBAL_GAP`, `MATCHING_TYPE`, `STRIPE_` / `PLAID_` lists ...), one `BEGIN_ST_PC` per style piece
(CATEGORY-named: `NAP_GROUP`, `FLIP_GROUP`, `CW_TILT_LIMIT`, `CCW_TILT_LIMIT`, `ROTATE_INCR`, `FOLDABLE_FLAG`, `BUNDLE_GROUP`), one `BEGIN_SIZE` / `BEGIN_ST_PC_SZ` per size, and one `BEGIN_PIECE` per piece INSTANCE (`BUNDLE_ID`,
`SPS_INDEX`, `ANGLE`, `FLIP_FLAG`, `AM_AREA`, `LOCATION`, `POINT_COUNT` + points) followed by its matching rules. Lengths are integers in 1e-4 inch, angles in 1e-2 degree, tilt limits in 1e-1 degree.

It is an INDEPENDENT ground truth for the job spec: `retrieval_orientation` (accumark_laylimits) reproduces its ANGLE / FLIP_FLAG for 3,460 instances of 73 jobs, and `engine_flags` its per-piece flags for every Piece Options row seen.
Nothing here is needed to read a marker; it checks the reading against what AccuMark itself handed its nester.
"""
import json, re, sys

__version__ = '1.0'
_LINE = re.compile(r'^([A-Z_0-9]+)(?:\s+(.*))?$')
_PT = re.compile(r'\((-?\d+),(-?\d+)\)')


def _num(v):
    try: return int(v)
    except ValueError:
        try: return float(v)
        except ValueError: return v.strip("'")


def parse_frommed(path_or_text):
    """-> (header, style_pieces, sizes, size_pieces, text): everything before the first BEGIN_PIECE (the piece instances are read by parse_pieces)."""
    txt = path_or_text if '\n' in path_or_text else open(path_or_text, 'r', errors='replace').read()
    hdr = {}; stp = []; sizes = []; sps = []
    ends = {'END_ST_PC': stp, 'END_SIZE': sizes, 'END_ST_PC_SZ': sps}
    begins = ('BEGIN_ST_PC', 'BEGIN_SIZE', 'BEGIN_ST_PC_SZ', 'BEGIN_STYLE')
    cur = None
    for ln in txt.split('\n'):
        m = _LINE.match(ln.rstrip())
        if not m: continue
        k, v = m.group(1), (m.group(2) or '').strip()
        if k == 'BEGIN_PIECE': break
        if k in begins: cur = {}
        elif k in ends: ends[k].append(cur); cur = None
        elif k.startswith(('BEGIN_', 'END_')): continue
        elif cur is not None: cur[k] = _num(v)
        elif k not in hdr: hdr[k] = _num(v)
    return hdr, stp, sizes, sps, txt


def parse_pieces(txt):
    """the piece INSTANCES of the text: -> [dict]. (Kept apart from parse_frommed: the piece blocks have no closing line before their matching rules.)"""
    pcs = []; cur = None; in_pts = False; pts = []; rule = None
    for ln in txt.split('\n'):
        ln = ln.rstrip()
        if in_pts:
            if ln.startswith('END_PIECE_POINTS'):
                in_pts = False; cur['points_in'] = [(int(a) / 1e4, int(b) / 1e4) for a, b in pts]; pts = []
            else: pts += _PT.findall(ln)
            continue
        m = _LINE.match(ln)
        if not m: continue
        k, v = m.group(1), (m.group(2) or '').strip()
        if k == 'BEGIN_PIECE':
            if cur is not None: pcs.append(cur)
            cur = {'matching_rules': []}; continue
        if cur is None: continue
        if k == 'BEGIN_PIECE_POINTS': in_pts = True; continue
        if k == 'BEGIN_MATCHING_RULE': rule = {}; continue
        if k == 'END_MATCHING_RULE': cur['matching_rules'].append(rule); rule = None; continue
        if k in ('BEGIN_MATCHING_RULES', 'END_MATCHING_RULES', 'END_PIECE'): continue
        if k.startswith(('BEGIN_', 'END_')) and k not in ('BEGIN_PIECE',):
            if k in ('BEGIN_ST_PC', 'BEGIN_SIZE', 'BEGIN_STYLE', 'BEGIN_ST_PC_SZ'): pcs.append(cur); cur = None
            continue
        if rule is not None: rule[k] = tuple(int(a) for a in _PT.findall(v)[0]) if v.startswith('(') else _num(v)
        else: cur[k] = tuple(int(a) for a in _PT.findall(v)[0]) if v.startswith('(') else _num(v)
    if cur is not None: pcs.append(cur)
    out = []
    for p in pcs:
        if 'PIECE_INDEX' not in p: continue
        loc = p.get('LOCATION')
        out.append(dict(index=p['PIECE_INDEX'], bundle_id=p.get('BUNDLE_ID'), sps_index=p.get('SPS_INDEX'), angle_deg=p.get('ANGLE', 0) / 100.0, flip=bool(p.get('FLIP_FLAG')),
                        am_area=p.get('AM_AREA'), picked=bool(p.get('PICKED_FLAG')), placed=bool(p.get('PLACED_FLAG')),
                        location_in=None if not loc or loc[0] <= -9e6 else (loc[0] / 1e4, loc[1] / 1e4), points_in=p.get('points_in', []), matching_rules=p['matching_rules'],
                        right=bool(p.get('RIGHT_FLAG')), fold_line=p.get('FOLD_LINE')))
    return out


def read_engine_file(path):
    """-> dict(header, style_pieces, sizes, size_pieces, pieces) of a frommed.mra"""
    hdr, stp, sizes, sps, txt = parse_frommed(path)
    return dict(header=hdr, style_pieces=stp, sizes=sizes, size_pieces=sps, pieces=parse_pieces(txt))


def engine_flags(options):
    """The per-style-piece flags the engine is given for a Piece Options string (no Nest Markers overrides): `NAP_GROUP` 2 for a one-way piece (W) else 0, `FLIP_GROUP` 2 when the flip is forbidden (S) else 0,
    `ROTATE_INCR` the rotation step in degrees - 0 for W, 45 for `4`, 90 for `9`, otherwise 180 [V: 19 (options, flip code, spread) rows of 73 jobs; the Nest Markers overrides change them: Rotation 45 / 90 -> ROTATE_INCR,
    Flip Enable -> FLIP_GROUP 0, Tilt Limit n degrees -> CW / CCW_TILT_LIMIT -+ 10 n]. The tilt column: 0.1 degree units (10 degrees = 100)."""
    o = set(options)
    return dict(NAP_GROUP=2 if 'W' in o else 0, FLIP_GROUP=2 if 'S' in o else 0,
                ROTATE_INCR=0 if 'W' in o else (45 if '4' in o else (90 if '9' in o else 180)))


if __name__ == '__main__':
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    d = read_engine_file(sys.argv[1])
    if '--json' in sys.argv: print(json.dumps(d, indent=1, default=str))
    else:
        h = d['header']
        print(f"{h.get('MARKER_NAME')}: width {h.get('MARKER_WIDTH', 0) / 1e4:.3f} in, spread {h.get('SPREAD')}, {len(d['style_pieces'])} style pieces, {len(d['sizes'])} sizes, {len(d['pieces'])} piece instances")
        for sp in d['style_pieces']: print('   ', {k: sp[k] for k in ('PIECE_NAME', 'NAP_GROUP', 'FLIP_GROUP', 'CW_TILT_LIMIT', 'CCW_TILT_LIMIT', 'ROTATE_INCR') if k in sp})
