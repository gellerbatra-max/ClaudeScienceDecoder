#!/usr/bin/env python3
"""reference_nester - a deliberately simple nesting engine that reads ONLY a nest spec JSON (nest_spec.py) - the proof that the spec is nesting-ready (v4.11).

    python nest_spec.py "<marker>.zip" --json job.json [--lay-limits ...] [--notch-table ...]
    python reference_nester.py job.json [--res 0.15] [--gap 0] [--out lay.json] [--dxf lay.dxf] [--svg lay.svg] [--order area|long|wide|hull|size] [--score right|left|slant] [--best]

It knows nothing about AccuMark: no marker, no ZIP, no decoder. From the spec it takes the fabric width, every instance to lay (shape outline, or `outline_mirrored` for mirrored
instances), the rotations each instance may take (`demand[].allowed_deg_by_slot`, from the Lay Limits table when the spec has it) and the gap between pieces (`--gap`, else the
block buffer of the spec, else 0). Pieces are rasterised (numpy), largest first; for each piece and each allowed rotation an FFT correlation finds every position that does not touch
what is already laid, and the one with the smallest right edge wins. It is a bottom-left heuristic - meant to be valid, not to compete with AccuNest - and its result is checked
independently with shapely: every piece inside the fabric, no two pieces overlapping, every rotation inside the allowed set. `--order` / `--score` change how pieces are ordered and positions ranked;
`--best` tries all combinations and keeps the shortest valid lay (8 runs).

The spec is the contract: a lay is valid when this file says `VALID`. Compare the length / utilisation with a real AccuMark lay of the same job (selftest does, on the real 2303 marker).
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from shapely import affinity
from shapely.geometry import Polygon
from shapely.strtree import STRtree

__version__ = '1.0'


def _instances(spec):
    shapes = {s['id']: s for s in spec['shapes']}; out = []
    for d in spec['demand']:
        s = shapes[d['shape']]
        if not s.get('complete'): continue
        outline = s['outline_mirrored'] if d['mirrored'] and s.get('outline_mirrored') else s['outline']
        for slot, allowed in zip(d['slots'], d['allowed_deg_by_slot']):
            out.append(dict(slot=slot, shape=s['id'], piece=s['piece'], size=s['size'], mirrored=d['mirrored'], outline=outline, allowed=list(allowed) or [0]))
    return out


def _oriented(outline, angle):
    p = Polygon(outline).buffer(0)
    if p.geom_type != 'Polygon': p = max(p.geoms, key=lambda g: g.area)
    p = affinity.rotate(p, angle, origin='centroid')
    minx, miny, _, _ = p.bounds
    return affinity.translate(p, -minx, -miny)


def _mask(poly, res, margin):
    """raster of `poly` grown by `margin`; the polygon's own lower-left corner sits at pixel (margin / res, margin / res)."""
    g = poly.buffer(margin, join_style=2)
    if g.geom_type != 'Polygon': g = max(g.geoms, key=lambda x: x.area)
    w = int(math.ceil((poly.bounds[2] + 2 * margin) / res)) + 2; h = int(math.ceil((poly.bounds[3] + 2 * margin) / res)) + 2
    im = Image.new('L', (w, h), 0); ImageDraw.Draw(im).polygon([((x + margin) / res, (y + margin) / res) for x, y in g.exterior.coords], fill=1)
    return np.asarray(im, dtype=np.float32)


def nest(spec, res=0.15, gap=None, order='area', log=None, score='right'):
    """-> (placed, unplaced, params). placed = the instances with `poly` (shapely, in fabric coordinates: x along the length, y across the width) and `angle`."""
    W = spec['fabric']['width']; inst = _instances(spec)
    if gap is None:
        bb = spec['fabric'].get('block_buffer_in') or []
        k = {'in': 1.0, 'cm': 2.54, 'mm': 25.4}[spec['units']]
        gap = 2 * max((max(b) for b in bb), default=0.0) * k if bb else 0.0
    margin = gap / 2 + 0.6 * res
    H = int(math.floor(W / res))
    area_all = sum(Polygon(i['outline']).buffer(0).area for i in inst)
    O = np.zeros((H, int(area_all / max(W, 1e-9) / 0.45 / res) + 200), dtype=np.float32)
    cache = {}
    def cands_of(it):
        key = (it['shape'], it['mirrored'], tuple(it['allowed']))
        if key not in cache:
            cache[key] = []
            for a in it['allowed']:
                po = _oriented(it['outline'], a); cache[key].append((a, po, _mask(po, res, margin)))
        return cache[key]
    def _ext(i): b = Polygon(i['outline']).bounds; return (b[2] - b[0], b[3] - b[1])
    keys = {'area': lambda i: (-Polygon(i['outline']).area, i['shape']), 'size': lambda i: (i['size'], -Polygon(i['outline']).area),
            'long': lambda i: (-max(_ext(i)), i['shape']), 'wide': lambda i: (-_ext(i)[1], -_ext(i)[0], i['shape']), 'hull': lambda i: (-Polygon(i['outline']).convex_hull.area, i['shape'])}
    inst.sort(key=keys[order])
    placed = []; unplaced = []
    for n, it in enumerate(inst):
        best = None
        while True:
            fo = np.fft.rfft2(O)
            for a, po, M in cands_of(it):
                hm, wm = M.shape
                if hm > H or wm > O.shape[1]: continue
                corr = np.fft.irfft2(fo * np.conj(np.fft.rfft2(M, s=O.shape)), s=O.shape)
                ok = corr[:H - hm + 1, :O.shape[1] - wm + 1] < 0.5
                if not ok.any(): continue
                x = int(np.where(ok.any(axis=0))[0][0]); y = int(np.where(ok[:, x])[0][0])
                key = (x + wm, y) if score == 'right' else ((x, y) if score == 'left' else (x + wm / 2.0 + 0.5 * y * wm / max(H, 1), y))
                if best is None or key < best[0]: best = (key, a, po, M, x, y)
            if best is not None or all(M.shape[0] > H for _, _, M in cands_of(it)) or O.shape[1] * res > 100 * W: break
            O = np.concatenate([O, np.zeros_like(O)], axis=1)
        if best is None: unplaced.append(it); continue
        _, a, po, M, x, y = best
        O[y:y + M.shape[0], x:x + M.shape[1]] = np.maximum(O[y:y + M.shape[0], x:x + M.shape[1]], M)
        placed.append(dict(it, angle=a, poly=affinity.translate(po, x * res + margin, y * res + margin)))
        if log and (n + 1) % 20 == 0: log(f'  laid {n + 1}/{len(inst)}')
    return placed, unplaced, dict(res=res, gap=gap, margin=margin)


def validate(spec, placed, unplaced, tol=1e-6):
    W = spec['fabric']['width']; polys = [p['poly'] for p in placed]
    L = max((p.bounds[2] for p in polys), default=0.0); area = sum(p.area for p in polys)
    inside = all(p.bounds[1] >= -tol and p.bounds[3] <= W + tol and p.bounds[0] >= -tol for p in polys)
    tree = STRtree(polys); worst = 0.0; n_ov = 0; gmin = None
    for i, p in enumerate(polys):
        for j in tree.query(p):
            if j <= i: continue
            a = p.intersection(polys[j]).area
            if a > tol: n_ov += 1; worst = max(worst, a)
            d = p.distance(polys[j]); gmin = d if gmin is None else min(gmin, d)
    rules = all(p['angle'] in p['allowed'] for p in placed)
    n_inst = len(placed) + len(unplaced)
    return dict(pieces=len(placed), unplaced=len(unplaced), instances=n_inst, length=L, width=W, area=area, utilisation=100 * area / (W * L) if L else 0.0, inside_fabric=inside,
                overlapping_pairs=n_ov, worst_overlap=worst, min_gap=gmin, rotations_allowed=rules,
                valid=inside and n_ov == 0 and rules and not unplaced and n_inst == sum(d['quantity'] for d in spec['demand']))


def write_dxf(spec, placed, path):
    L = []
    def g(c, v): L.append(f'{c:>3}'); L.append(str(v))
    g(0, 'SECTION'); g(2, 'ENTITIES')
    for p in placed:
        g(0, 'POLYLINE'); g(8, 'CUT'); g(66, 1); g(70, 1)
        for x, y in list(p['poly'].exterior.coords)[:-1]: g(0, 'VERTEX'); g(8, 'CUT'); g(10, f'{x:.4f}'); g(20, f'{y:.4f}')
        g(0, 'SEQEND'); g(8, 'CUT')
    g(0, 'ENDSEC'); g(0, 'EOF')
    open(path, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(L) + '\n')


def write_svg(spec, placed, rep, path):
    sc = 800.0 / max(rep['length'], 1e-9); W = rep['width']; H = W * sc + 40
    parts = [f'<rect x="10" y="30" width="{rep["length"] * sc:.1f}" height="{W * sc:.1f}" fill="none" stroke="#999"/>']
    for p in placed:
        pts = ' '.join(f'{10 + x * sc:.1f},{30 + (W - y) * sc:.1f}' for x, y in list(p['poly'].exterior.coords)[:-1])
        parts.append(f'<polygon points="{pts}" fill="{"#f3d9d9" if p["angle"] % 360 == 180 else "#dbe8ff"}" stroke="#1a4d8f" stroke-width="0.6"/>')
    head = f'{spec["source"]["marker"]}: {rep["pieces"]} pieces, length {rep["length"]:.1f} {spec["units"]}, utilisation {rep["utilisation"]:.1f}% (blue 0 deg, red 180 deg)'
    open(path, 'w', encoding='utf-8').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{rep["length"] * sc + 30:.0f}" height="{H:.0f}"><rect width="100%" height="100%" fill="white"/><text x="10" y="20" font-family="sans-serif" font-size="12">{head}</text>' + ''.join(parts) + '</svg>')


def main(argv):
    a = [x for x in argv if not x.startswith('--')]
    def opt(n, d=None): return argv[argv.index(n) + 1] if n in argv else d
    if not a: print(__doc__); return 2
    spec = json.load(open(a[0])); res = float(opt('--res', 0.15)); gap = opt('--gap'); gap = float(gap) if gap is not None else None
    if '--best' in argv:
        runs = []
        for o in ('area', 'long', 'wide', 'hull'):
            for sc in ('right', 'left'):
                pl, un, inf = nest(spec, res, gap, o, score=sc); rp = validate(spec, pl, un); runs.append((not rp['valid'], rp['length'], o, sc, pl, un, inf, rp)); print(f"  {o:5} {sc:5}: length {rp['length']:.1f}, {rp['utilisation']:.1f}%")
        _, _, o, sc, placed, unplaced, info, rep = min(runs, key=lambda r: r[:2]); info = dict(info, order=o, score=sc)
    else:
        placed, unplaced, info = nest(spec, res, gap, opt('--order', 'area'), log=print, score=opt('--score', 'right'))
        rep = validate(spec, placed, unplaced)
    if opt('--out'): json.dump(dict(report=rep, params=info, placements=[dict(slot=p['slot'], shape=p['shape'], angle=p['angle'], mirrored=p['mirrored'], polygon=[list(c) for c in p['poly'].exterior.coords[:-1]]) for p in placed]), open(opt('--out'), 'w'), indent=1)
    if opt('--dxf'): write_dxf(spec, placed, opt('--dxf'))
    if opt('--svg'): write_svg(spec, placed, rep, opt('--svg'))
    print(f"{spec['source']['marker']}: {rep['pieces']}/{rep['instances']} pieces laid, length {rep['length']:.2f} {spec['units']} on {rep['width']:.2f} wide, utilisation {rep['utilisation']:.2f}%, "
          f"overlapping pairs {rep['overlapping_pairs']}, min gap {rep['min_gap']}, rotations allowed {rep['rotations_allowed']}, inside fabric {rep['inside_fabric']}")
    print('VALID' if rep['valid'] else 'INVALID')
    return 0 if rep['valid'] else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
