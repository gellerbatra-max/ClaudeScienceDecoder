#!/usr/bin/env python3
"""verify_marker.py - validate an AccuMark marker export before you trust it.

  python verify_marker.py <marker.zip>                      report what the marker holds
  python verify_marker.py <marker.zip> --dxf <drawn.dxf|folder>
                                                            check placements + outlines against
                                                            AccuMark's own drawn-marker DXF export
  python verify_marker.py <marker.zip> --baseline <other.zip>
                                                            structural diff of the marker objects
  ... --expect KEY=VALUE (repeatable; non-zero exit on any failure)

  KEY               meaning
  laid              yes|no
  placements        number of occupied slots
  bundles           number of distinct bundle indices
  bound             placements bound to a (piece,size) record
  pieces_listed     pieces the marker declares (section 10)
  records           (piece,size) records (section 14)
  width_cm / length_cm / util_pct   header values (tolerance 0.05 cm / 0.01 %)
  identity          yes  - sum of placed declared areas == W*L*U
  bbox_ok           placements whose graded/unfolded bbox matches home*2 (0.02 in)
  area_ok           (piece,size) pairs whose outline area matches the declared area (1 %)
  dxf_centres       placements whose centre matches a drawn shape (0.01 in)
  dxf_outline_max   worst outline Hausdorff vs the drawn shapes, inches (<= value)
"""
import glob, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import accumark_pds as ap
import accumark_marker as am

# ---------------------------------------------------------- drawn DXF
def dxf_marker(path):
    """Polylines of a drawn-marker DXF (plot-style export: one polyline per
    edge run, labels as TEXT) -> (loops, meta, marker name). Chunks are
    chained by shared endpoints into closed loops; the loop spanning the
    whole drawing is the marker boundary and is dropped."""
    L = [l.rstrip('\r\n') for l in open(path, encoding='latin1')]
    pairs = [(L[i].strip(), L[i+1]) for i in range(0, len(L)-1, 2)]
    # $INSUNITS (header group 70) tells us what unit the raw X/Y vertex
    # coordinates below are in - 1=inches (the July markers), 5=centimeters
    # (this vintage's "Metric [cm]" AccuMark session; confirmed against
    # 2303-BD-137-PLACED.DXF, whose raw polyline bbox is exactly 377.68 x
    # 137.0 = the marker's own length_cm/width_cm). Everything else in this
    # tool (placements, outlines) is in inches, so normalise here rather
    # than downstream.
    insunits = 1
    for i, (k, v) in enumerate(pairs):
        if k == '9' and v.strip() == '$INSUNITS':
            for k2, v2 in pairs[i+1:i+4]:
                if k2 == '70': insunits = int(v2); break
            break
    scale = {4: 1/25.4, 5: 1/2.54, 6: 1/0.0254}.get(insunits, 1.0)
    polys, cur, texts, x, inv = [], None, [], None, False
    for k, v in pairs:
        if k == '0':
            if v == 'POLYLINE': cur = []; polys.append(cur); inv = False
            elif v == 'VERTEX': inv = True
            elif v in ('SEQEND', 'TEXT', 'ENDSEC'): inv = False
        elif inv and k == '10': x = float(v)
        elif inv and k == '20' and x is not None: cur.append((x*scale, float(v)*scale)); x = None
        elif k == '1': texts.append(v.strip())
    polys = [p for p in polys if len(p) >= 2]
    meta, mk = {}, ''
    for t in texts:
        m = re.match(r'W=([\d.]+)CM L=(\d+)M ([\d.]+)CM U=([\d.]+)%', t)
        if m: meta = dict(width_cm=float(m.group(1)), length_cm=float(m.group(2))*100+float(m.group(3)), util=float(m.group(4)))
        m = re.match(r'W=([\d.]+)IN L=(\d+)YD ([\d.]+)IN U=([\d.]+)%', t)
        if m: meta = dict(width_cm=float(m.group(1))*2.54, length_cm=(float(m.group(2))*36+float(m.group(3)))*2.54, util=float(m.group(4)))
        if t.startswith('MK:'): mk = t[3:].strip()
    loops = _stitch(polys)
    if loops:
        span = max(loops, key=lambda p: (max(q[0] for q in p)-min(q[0] for q in p))*(max(q[1] for q in p)-min(q[1] for q in p)))
        loops = [l for l in loops if l is not span] or loops
    return loops, meta, mk

def _stitch(polys, tol=5e-3):
    chains = [list(p) for p in polys]; loops = []
    while chains:
        path = chains.pop(0); grew = True
        while grew and math.dist(path[0], path[-1]) > tol:
            grew = False
            for c in list(chains):
                for cc in (c, c[::-1]):
                    if math.dist(path[-1], cc[0]) <= tol: path += cc[1:]; chains.remove(c); grew = True; break
                    if math.dist(cc[-1], path[0]) <= tol: path = cc[:-1] + path; chains.remove(c); grew = True; break
                if grew: break
        if len(path) >= 4 and math.dist(path[0], path[-1]) <= tol: loops.append(path)
    return loops

def _pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy
    t = 0 if L2 == 0 else max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx), py-(ay+t*dy))

def _pt_poly(p, poly):
    return min(_pt_seg(p, poly[i], poly[(i+1) % len(poly)]) for i in range(len(poly)))

def hausdorff(a, b):
    return max(max(_pt_poly(p, b) for p in a), max(_pt_poly(p, a) for p in b))

# ------------------------------------------------------------- facts
def facts(path, dxf=None, buffer_in=None):
    res = am.place_marker(path)
    out = []
    for mkr in res['markers']:
        mk = mkr['marker']; f = {}
        f['name'] = mk['name']
        f['laid'] = 'yes' if mk['laid'] else 'no'
        f['width_cm'] = round(mk['width']*2.54, 2); f['length_cm'] = round(mk['length']*2.54, 2)
        f['util_pct'] = round(mk['util'], 2); f['area_422'] = round(mk['total_area'], 4)
        f['placements'] = len(mk['placements']); f['bundles'] = len(mk['bundles'])
        f['bound'] = sum(1 for p in mk['placements'] if p['record'])
        f['pieces_listed'] = len(mk['pieces']); f['records'] = len(mk['records'])
        f['models'] = len(mk['models']); f['sizes'] = len(mk['sizes']); f['slots'] = len(mk['slots'])
        f['fabrics'] = ';'.join(sorted({p['fabric'] for p in mk['pieces'] if p['fabric']}))
        ident = next((ok for n, ok, _ in mkr['checks'] if n.startswith('sum(slot areas)')), None)
        f['identity'] = 'yes' if ident else ('no' if ident is False else 'n/a')
        f['pieces_in_zip'] = sum(1 for p in res['pieces'].values() if p)
        f['pieces_missing'] = ';'.join(sorted({p['piece'] for p in mk['placements'] if p['piece'] and not res['pieces'].get(p['piece'])}))
        # geometry self-checks that need no answer key
        buf = buffer_in
        if buf is None:
            # the July markers carry a 3 mm block buffer: home*2 - bbox = 2*buffer;
            # infer it from the median residual of the non-fold placements
            rows = am.bbox_check(res, 0.0)
            if rows:
                dxs = sorted(r[2] for r in rows); buf = max(0.0, dxs[len(dxs)//2]/2)
                if buf < 0.005: buf = 0.0
        f['buffer_in'] = round(buf or 0.0, 4)
        rows = am.bbox_check(res, buf or 0.0)
        f['bbox_ok'] = sum(1 for r in rows if abs(r[2]) <= 0.02 and abs(r[3]) <= 0.02)
        f['bbox_worst'] = round(max([max(abs(r[2]), abs(r[3])) for r in rows] or [0]), 4)
        arows = am.area_check(res)
        f['area_ok'] = sum(1 for r in arows if r[4] and abs(r[4]-1) <= 0.01)
        f['area_pairs'] = len(arows)
        f['area_worst'] = round(max([abs(r[4]-1) for r in arows if r[4]] or [0]), 4)
        f['folds'] = ';'.join(sorted({n for n, p in res['pieces'].items() if p and p.get('fold')}))
        f['notes'] = ';'.join(sorted({n for *_, n in mkr['placed'] if n and 'unfold' not in n}))
        if dxf:
            f.update(dxf_facts(mkr, dxf))
        out.append((f, mkr))
    return out, res

def dxf_facts(mkr, dxf):
    mk = mkr['marker']; f = {}
    paths = [dxf] if os.path.isfile(dxf) else glob.glob(os.path.join(dxf, '*.dxf')) + glob.glob(os.path.join(dxf, '*.DXF'))
    # a case-insensitive filesystem (Windows) matches both globs against the
    # same file - dedupe so a single-DXF folder is still detected as such
    seen = set(); paths = [p for p in paths if not (os.path.normcase(p) in seen or seen.add(os.path.normcase(p)))]
    chosen = None
    for p in paths:
        loops, meta, name = dxf_marker(p)
        if name == mk['name'] or len(paths) == 1: chosen = (p, loops, meta, name); break
        if os.path.splitext(os.path.basename(p))[0] == mk['name']: chosen = (p, loops, meta, name); break
    if not chosen:
        f['dxf'] = 'no drawn DXF matches marker %r' % mk['name']; return f
    p, loops, meta, name = chosen
    f['dxf'] = os.path.basename(p)
    if meta:
        f['dxf_width_cm'] = meta['width_cm']; f['dxf_length_cm'] = round(meta['length_cm'], 2); f['dxf_util_pct'] = meta['util']
    centres = []
    for lp in loops:
        xs = [q[0] for q in lp]; ys = [q[1] for q in lp]
        centres.append(((min(xs)+max(xs))/2, (min(ys)+max(ys))/2))
    used = set(); ok = 0; worst_c = 0.0; worst_o = 0.0; n_o = 0
    for s, pname, size, outline, note in mkr['placed']:
        cand = [(math.hypot(c[0]-s['x'], c[1]-s['y']), i) for i, c in enumerate(centres) if i not in used]
        if not cand: continue
        dc, i = min(cand); used.add(i); worst_c = max(worst_c, dc)
        if dc <= 0.01: ok += 1
        if outline:
            h = hausdorff(outline, loops[i]); worst_o = max(worst_o, h); n_o += 1
    f['dxf_shapes'] = len(loops); f['dxf_centres'] = ok; f['dxf_centre_worst'] = round(worst_c, 4)
    f['dxf_outline_max'] = round(worst_o, 4); f['dxf_outlines_checked'] = n_o
    return f

# ------------------------------------------------------ section diff
def section_diff(a, b):
    """Compare two marker objects section by section (the 42-slot directory
    makes an aligned diff trivial even when the files differ in length).
    Header residue (0x12-0x7f), the name slots and the trailer stamps are
    NOISE; a section whose bytes differ is STRUCTURAL; a section that moved
    only because an earlier one grew is reported as SHIFTED."""
    da, db = am.directory(a), am.directory(b)
    out = []
    def sec(d, dirs, k):
        s = am._section(d, dirs, k); return d[s[0]:s[1]] if s else None
    if a[0x15:0x60] != b[0x15:0x60]: out.append(dict(section='name', kind='NOISE', detail='object name slot'))
    for k in range(am.DIR_SLOTS):
        sa, sb = sec(a, da, k), sec(b, db, k)
        if sa is None and sb is None: continue
        if sa is None or sb is None:
            out.append(dict(section=str(k), kind='STRUCTURAL', detail='section present in one file only')); continue
        if sa == sb:
            if da[k] != db[k]: out.append(dict(section=str(k), kind='SHIFTED', detail=f'+{db[k]-da[k]} bytes, content identical'))
            continue
        if k == am.SEC_GEOMETRY:
            out.append(dict(section=str(k), kind='GEOMETRY', detail=f'embedded type-10 object differs ({len(sa)} -> {len(sb)} bytes)')); continue
        if len(sa) == len(sb):
            runs = 0; i = 0
            while i < len(sa):
                if sa[i] != sb[i]:
                    runs += 1
                    while i < len(sa) and sa[i] != sb[i]: i += 1
                i += 1
            out.append(dict(section=str(k), kind='STRUCTURAL', detail=f'{runs} differing runs in {len(sa)} bytes'))
        else:
            out.append(dict(section=str(k), kind='STRUCTURAL', detail=f'length {len(sa)} -> {len(sb)}'))
    ta, tb = a[-396:], b[-396:]
    if ta != tb: out.append(dict(section='trailer', kind='NOISE', detail='timestamps / users'))
    return out

# -------------------------------------------------------------- main
def _isnum(x):
    try: float(x); return True
    except ValueError: return False

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help'): print(__doc__); return 0
    path = argv.pop(0); dxf = None; base = None; expects = []; buffer_in = None
    while argv:
        a = argv.pop(0)
        if a == '--dxf': dxf = argv.pop(0)
        elif a == '--baseline': base = argv.pop(0)
        elif a == '--expect': expects.append(argv.pop(0))
        elif a == '--buffer-mm': buffer_in = float(argv.pop(0))/25.4
        else: print('unknown option', a); return 2
    results, res = facts(path, dxf, buffer_in)
    fails = []
    for f, mkr in results:
        print(f"== {f['name']}")
        for k, v in f.items():
            if k != 'name': print(f"   {k:20} {v}")
        for e in expects:
            k, want = e.split('=', 1)
            if k == 'structural_change': continue          # checked in the --baseline block
            got = f.get(k)
            if got is None: fails.append(f'{k}: no such fact'); continue
            if k in ('width_cm', 'length_cm'): ok = abs(float(got)-float(want)) <= 0.05
            elif k == 'util_pct': ok = abs(float(got)-float(want)) <= 0.01
            elif k == 'dxf_outline_max': ok = float(got) <= float(want)
            elif _isnum(want) and _isnum(got): ok = float(got) == float(want)
            else: ok = str(got) == want
            print(f"   {'ok ' if ok else 'FAIL'} expect {k}={want} (got {got})")
            if not ok: fails.append(f'{k}={got} want {want}')
    if base:
        a = am.list_zip(base)['marker'][0]['data']; b = am.list_zip(path)['marker'][0]['data']
        changed = section_diff(a, b)
        n = sum(1 for s in changed if s['kind'] == 'STRUCTURAL')
        print(f"   structural_change     {'yes' if n else 'no'} (sizes {len(a)} -> {len(b)})")
        for s in changed: print(f"      {s['section']:>10} {s['kind']:10} {s['detail']}")
        for e in expects:
            if e.startswith('structural_change='):
                want = e.split('=')[1]; got = 'yes' if n else 'no'
                if got != want: fails.append(f'structural_change={got} want {want}')
    print('RESULT:', 'FAIL' if fails else 'PASS')
    for x in fails: print('  -', x)
    return 1 if fails else 0

if __name__ == '__main__':
    sys.exit(main())
