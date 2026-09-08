#!/usr/bin/env python3
"""verify_capture.py - validate an AccuMark PDS capture before you trust it.

Two modes:

  report            decode a capture folder and print what the piece file
                    actually contains
  --baseline DIR    structurally diff this capture against a baseline capture
                    and classify every differing byte run, so a GUI action
                    that silently did nothing is caught on the machine that
                    produced it rather than three days later

A capture folder is <NAME>/ containing <NAME>.ZIP, <NAME>.DXF, <NAME>.RUL
(the DXF export drops the .RUL beside it automatically).

Expectations are asserted with --expect KEY=VALUE (repeatable); the process
exits non-zero if any fails, so it can gate a capture loop.

  KEY                  meaning
  perimeter_points     count of perimeter point records (excl. closing)
  notches              count of notch vertices
  notch_types          semicolon list of notch Type numbers (1..30), in perimeter order
  drill_points         count of interior/drill points (0x44 internal list)
  graded_points        count of points carrying an explicit rule reference
  rule_ids             semicolon list of referenced object-record ids
  piece_records        count of piece records in the file (2 => pasted copy)
  seam_cm              uniform seam allowance in cm (0 = none)
  uneven_seam          yes|no  - segments disagree, or begin != end
  segment_points       semicolon list of per-segment point counts
  structural_change    yes|no  - requires --baseline
  dxf_match            yes     - decoded outline matches the DXF
  line_records         semicolon list, one count per piece record (block),
                       of Region D (TLV line table) records - see
                       accumark_pds.py's tail-section docs / FORMAT_SPEC.md
  line_table_consistent yes|no - every table point in every block coincides
                       with independently-decoded geometry (accumark_pds.
                       check_line_table); 'no' on a block whose geometry
                       isn't fully explained yet (see FORMAT_SPEC.md [?]s)
  unknown_bytes        byte count accumark_pds.coverage() could not assign
                       to any known field (excludes zero padding and the
                       3-byte export-noise floor) - 0 is the sign-off target
  coverage_pct         100 * (1 - unknown_bytes / file size)

Pass --coverage to also print the unknown-byte run list (offset, length,
hex) instead of just the summary counts.
"""
import argparse, glob, os, re, sys, zipfile, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import accumark_pds as ap

# ----------------------------------------------------------------- loading
def load(folder):
    folder = folder.rstrip('/\\')
    z = glob.glob(os.path.join(folder, '*.ZIP')) + glob.glob(os.path.join(folder, '*.zip'))
    if not z: raise SystemExit(f'no .ZIP in {folder}')
    zf = zipfile.ZipFile(z[0])
    tmp = [n for n in zf.namelist() if n.lower().endswith('.tmp')]
    if not tmp: raise SystemExit(f'{z[0]} has no .tmp member - not an AccuMark piece export')
    data = zf.read(tmp[0])
    dxf = (glob.glob(os.path.join(folder,'*.DXF')) + glob.glob(os.path.join(folder,'*.dxf')) or [None])[0]
    rul = (glob.glob(os.path.join(folder,'*.RUL')) + glob.glob(os.path.join(folder,'*.rul')) or [None])[0]
    return dict(folder=folder, zip=z[0], data=data, dxf=dxf, rul=rul)

# ------------------------------------------------------------ DXF geometry
def dxf_outline(path):
    L = [l.rstrip('\n') for l in open(path, errors='replace')]
    pr = [(L[i].strip(), L[i+1].strip()) for i in range(0, len(L)-1, 2)]
    polys, cur, lay, x = [], None, None, None
    for k, v in pr:
        if k == '0':
            if v == 'POLYLINE': cur = {'layer': None, 'pts': []}; polys.append(cur)
            elif v == 'VERTEX': x = {}
            continue
        if k == '8' and cur is not None and cur['layer'] is None: cur['layer'] = v
        if k == '10' and x is not None: x['x'] = float(v)
        if k == '20' and x is not None:
            x['y'] = float(v); cur['pts'].append((x['x'], x['y'])); x = None
    return polys

def dxf_check(cap):
    """Compare the binary perimeter with the DXF outline.

    The ASTM export writes the sew line (layer 14) only for edges that carry a
    seam allowance (CAP-C31-SEAM-TAPER: 2 of 4 edges), so outline vertices are
    gathered from layers 14 and 1 together, and the two point sets are aligned
    by the most common vertex-to-vertex translation rather than by bounding
    box - a seam widens the layer-1 box without moving the perimeter."""
    if not cap['dxf']: return None, 'no DXF in folder'
    polys = dxf_outline(cap['dxf'])
    layers = {p['layer'] for p in polys}
    D = [p for pl in polys if pl['layer'] in ('1', '14') for p in pl['pts']]
    if not D: return None, 'no boundary polyline in DXF'
    s = ap.summarize(cap['data'])
    B = [(p['x']/ap.UNITS_PER_INCH, p['y']/ap.UNITS_PER_INCH) for p in s['blocks'][0]['perimeter']]
    from collections import Counter
    votes = Counter((round(qx-px, 4), round(qy-py, 4)) for px, py in B for qx, qy in D)
    (tx, ty), n = votes.most_common(1)[0]
    worst = 0.0
    for px, py in B:
        px, py = px+tx, py+ty
        worst = max(worst, min(abs(px-qx)+abs(py-qy) for qx, qy in D))
    segs = [len(pl['pts']) for pl in polys if pl['layer'] == '1']
    lay = '14+1' if '14' in layers else '1'
    return worst, (f'max|delta|={worst:.6f} in vs DXF layer {lay} '
                   f'(shift {tx:+.4f},{ty:+.4f} from {n} anchor vertices); L1 polyline points={segs}')

# --------------------------------------------------------------- diff mode
def classify_runs(a, b):
    """Aligned diff of two piece files; label every differing run so that a GUI
    edit which never reached the file cannot hide among the bytes that always
    differ between two exports (piece name, uninitialised heap residue,
    last-saved timestamps) or among a pure change of storage position."""
    def name_span(d):
        try: return (0x15, d.index(b'\x00', 0x15) + 1)
        except ValueError: return (0x15, 0x15)

    zones = []                                     # every copy of either name
    for d in (a, b):
        s0, s1 = name_span(d)
        nm = d[s0:s1-1]
        if not nm: continue
        o = d.find(nm)
        while o != -1:
            zones.append((o - 2, o + len(nm) + 4))
            o = d.find(nm, o + 1)

    stamps = []                                    # every plausible epoch u32
    for d in (a, b):
        for o in range(max(0, len(d) - 400), len(d) - 4):
            v = ap.i32(d, o)
            if 1_500_000_000 < v < 2_200_000_000:
                stamps.append((o - 1, o + 5))

    if len(a) == len(b):          # equal length -> positional diff is exact,
        runs = []                 # and avoids difflib's insert/delete guesses
        i = 0
        while i < len(a):
            if a[i] != b[i]:
                j = i
                while j < len(a) and a[j] != b[j]: j += 1
                runs.append(dict(off=i, n_a=j-i, n_b=j-i, a=a[i:j], b=b[i:j], kind=None))
                i = j
            else:
                i += 1
    else:
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        runs = [dict(off=i1, n_a=i2 - i1, n_b=j2 - j1, a=a[i1:i2], b=b[j1:j2], kind=None)
                for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != 'equal']

    for r in runs:                                 # pass 1: positional classes
        o = r['off']
        if any(z0 <= o < z1 for z0, z1 in zones):
            r['kind'] = 'name'
        elif 0x12 <= o < 0x15 or 0x23 <= o < 0x88:
            r['kind'] = 'heap-residue'
        elif any(z0 <= o < z1 for z0, z1 in stamps):
            r['kind'] = 'timestamp'

    deltas = {}                                    # pass 2: rigid translation
    for r in runs:
        if r['kind'] or r['n_a'] != r['n_b'] or r['n_a'] > 4: continue
        for o in range(max(0, r['off'] - 3), r['off'] + 1):
            if o + 4 > min(len(a), len(b)): continue
            va, vb = ap.i32(a, o), ap.i32(b, o)
            if ap.COORD_LO < va < ap.COORD_HI and ap.COORD_LO < vb < ap.COORD_HI and va != vb:
                deltas.setdefault(vb - va, []).append(r)
    for d, members in sorted(deltas.items(), key=lambda kv: -len(kv[1])):
        if len(members) < 3: continue              # x and y each get a class
        for r in members:
            if r['kind'] is None: r['kind'] = 'coord-translation(%+d)' % d

    for r in runs:
        if r['kind'] is None: r['kind'] = 'STRUCTURAL'
        r['a'], r['b'] = r['a'][:24].hex(), r['b'][:24].hex()
    return runs

# ------------------------------------------------------------------ facts
def facts(cap):
    s = ap.summarize(cap['data'])
    b0 = s['blocks'][0]
    # s['segments'] is one L-line attribute record per edge, but concatenated
    # across every piece block/record in the file - block 0 (current/edited
    # geometry) always comes first, followed by any stale pre-edit block(s).
    # Slice by the number of *numbered* perimeter points (edges), not the
    # total perimeter-point count, since notches (id == -1) add extra
    # perimeter points without adding edges (CAP-C42-NOTCH-ALLEDGES: 4 edges,
    # 8 perimeter points once each edge gets one notch).
    n_edges = sum(1 for p in b0['perimeter'] if p['id'] != -1)
    segs = s['segments'][:n_edges]
    seam = [(g['seam_begin'], g['seam_end']) for g in segs if g['seam_flag']]
    uneven = bool(seam) and (len({sv for pair in seam for sv in pair}) > 1 or len(seam) != len(segs))
    # tail-section facts (Region B/C/D - the pretable header, perimeter
    # snapshots and TLV line table; see accumark_pds.py's module docs and
    # FORMAT_SPEC.md). block0's tail only, except line_records/consistent
    # which report every block so a stale second record's own table is
    # visible too.
    tails = [b['tail'] for b in s['blocks']]
    line_records = ';'.join(str(len(t['line_records'])) if t and 'error' not in t else 'ERR' for t in tails)
    consistent = all(ap.check_line_table(b) for b in s['blocks'])
    t0 = tails[0]
    if t0 and 'error' not in t0:
        recs0 = t0['line_records']
        line_points = sum(len(r['points']) for r in recs0)
        line_kinds = ';'.join(str(r['kind']) for r in recs0)
        notch_blocks = sum(1 for r in recs0 for p in r['points'] for tag, _ in p['children'] if tag == 0x07)
        graded_tags = sum(1 for r in recs0 for p in r['points'] for tag, _ in p['children'] if tag == 0x04)
    else:
        line_points = notch_blocks = graded_tags = None
        line_kinds = ''
    cov = ap.coverage(cap['data'], summary=s)
    f = dict(
        file_bytes=len(cap['data']),
        exported_name=s['header_piece_name'], category=s['category'],
        annotation=s['annotation'], rule_table=s['rule_table'],
        size=s['size'], sample_size=s['sample_size'], n_sizes=len(s['sizes']),
        base_size=s['sizes'][s['base_index']] if s['sizes'] else None,
        piece_records=s['n_blocks'],
        perimeter_points=len(b0['perimeter']),
        notches=len(s['notches_in']),
        notch_types=';'.join(str(t) for t in s['notch_types']),
        drill_points=len(s['drill_points_in']),
        cutout_points=';'.join(str(len(c)) for c in s['cutouts_in']),
        graded_points=len(s['grade_refs']),
        rule_ids=';'.join(str(r) for _, r in s['grade_refs']),
        segment_points=';'.join(str(g['n_points']) for g in segs),
        seam_cm=round(seam[0][0]/ap.UNITS_PER_INCH*2.54, 4) if seam else 0.0,
        uneven_seam='yes' if uneven else 'no',
        cutline_records=len(s['line_geometry']),
        object_record_ids=';'.join(str(i) for i, _ in s['object_records']),
        n_break_rows=s['n_break_rows'],
        grade_rules=' | '.join(f"{i}:" + ','.join(f'{dx}/{dy}' for dx, dy in dl)
                               for i, dl in s['grade_rules'].items() if any(dl)) or 'none embedded',
        unix_timestamp=s['timestamps'][0] if s['timestamps'] else None,
        line_records=line_records, line_points=line_points, line_kinds=line_kinds,
        notch_blocks=notch_blocks, graded_tags=graded_tags,
        line_table_consistent='yes' if consistent else 'no',
        unknown_bytes=cov['counts'].get('unknown', 0), coverage_pct=cov['coverage_pct'],
    )
    if cap['rul']:
        r = ap.parse_rul(open(cap['rul'], errors='replace').read())
        f['rul_table'] = r['table']; f['rul_n_rules'] = len(r['rules'])
        f['rul_sizes'] = ' '.join(r['sizes'])
    return f, s

# ------------------------------------------------------------------- main
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('folder')
    p.add_argument('--baseline', help='capture folder to diff against')
    p.add_argument('--expect', action='append', default=[], metavar='KEY=VALUE')
    p.add_argument('--coverage', action='store_true',
                   help='print the accumark_pds.coverage() unknown-byte run list')
    a = p.parse_args(argv)

    cap = load(a.folder)
    f, s = facts(cap)
    print(f"== {os.path.basename(cap['folder'])}  ({f['file_bytes']} bytes)")
    for k in ('exported_name','category','annotation','rule_table','size','sample_size',
              'n_sizes','base_size','piece_records','perimeter_points','notches','notch_types','drill_points',
              'cutout_points','graded_points','rule_ids','segment_points','seam_cm','uneven_seam',
              'cutline_records','object_record_ids','n_break_rows','grade_rules',
              'rul_table','rul_n_rules','rul_sizes',
              'line_records','line_points','line_kinds','notch_blocks','graded_tags',
              'line_table_consistent','unknown_bytes','coverage_pct'):
        if k in f and f[k] not in (None, ''): print(f'   {k:18} {f[k]}')
    worst, msg = dxf_check(cap)
    print(f'   dxf                {msg}')
    f['dxf_match'] = 'yes' if (worst is not None and worst <= 2e-4) else 'no'

    if a.coverage:
        cov = ap.coverage(cap['data'], summary=s)
        print(f"\n-- coverage: {cov['coverage_pct']}% "
              f"({cov['counts']}, {len(cov['unknown_runs'])} unknown runs)")
        for lo, hi, hx in cov['unknown_runs']:
            print(f'   {lo:#07x}-{hi:#07x} ({hi-lo:3d}B): {hx}')

    if a.baseline:
        base = load(a.baseline)
        runs = classify_runs(base['data'], cap['data'])
        struct = [r for r in runs if r['kind'] == 'STRUCTURAL']
        print(f"\n-- diff vs {os.path.basename(base['folder'])}: "
              f"{len(base['data'])} -> {len(cap['data'])} bytes, {len(runs)} runs, "
              f"{len(struct)} structural")
        for r in runs:
            tag = '**' if r['kind'] == 'STRUCTURAL' else '  '
            print(f"  {tag} {r['kind']:13} @{r['off']:#07x} -{r['n_a']}/+{r['n_b']} "
                  f"{r['a']} -> {r['b']}")
        f['structural_change'] = 'yes' if struct else 'no'
        if not struct:
            print('  !! no structural difference: the intended edit did NOT reach the '
                  'saved piece (name/timestamp/heap bytes only)')

    ok = True
    for e in a.expect:
        k, _, want = e.partition('=')
        got = f.get(k)
        if got is None:
            print(f'EXPECT {k}: UNKNOWN (needs --baseline?)'); ok = False; continue
        hit = str(got) == want or (
            _isnum(want) and _isnum(str(got)) and abs(float(got)-float(want)) < 1e-6)
        print(f"EXPECT {k}={want}: {'PASS' if hit else 'FAIL (got %s)' % got}")
        ok &= hit
    if a.expect: print('RESULT:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1

def _isnum(x):
    try: float(x); return True
    except ValueError: return False

if __name__ == '__main__':
    sys.exit(main())
