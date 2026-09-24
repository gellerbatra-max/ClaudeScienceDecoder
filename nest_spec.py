#!/usr/bin/env python3
"""nest_spec - turn an AccuMark marker export ZIP into a NESTING JOB a nesting engine can read.

    python nest_spec.py "<marker>.zip" --json job.json [--dxf pieces.dxf] [--svg pieces.svg] [--units cm|mm|in] [--marker NAME]

One command from the ZIP AccuMark exports (marker-only is enough: no piece objects needed, no AccuMark installed) to

    fabric      width (and the shortest length a 100%-efficient lay would need), fabric types, block buffer
    shapes      one per (piece, size, cut) the marker lists: the CUT outline, the seam (stitch) line when the marker holds one,
                notches (position + type), the grain line, internal lines, drill holes, area, perimeter, bounding box
    demand      how many of each shape to lay, and how many of those mirrored - with the mirrored outline written out, so the
                nester needs no mirror convention
    checks      every number a nester will trust, verified against numbers AccuMark itself stored (declared area, stored home box)

Only what is still to be laid is listed: an unlaid marker gives every piece; a part-laid marker gives the unplaced ones (the placed count
is reported). Nothing about WHERE a piece goes is guessed: an unlaid marker has no positions, and the pre-set 0 / 180 degree pattern in it is
a lay pattern, not a constraint.

Coordinates: every shape has its own frame - the lower-left corner of its cut outline's bounding box is (0, 0), x is the grain direction -
in `--units` (default cm); outlines are closed polygons without a repeated last point, counter-clockwise. The grain line is horizontal in
every piece object of the corpus; where the marker stores it in the layout that was verified against piece objects its `basis` is `stream`,
for the older 1825D / 5683D / 2591A / 418T vintage it is `inferred` (see MARKER_FORMAT_SPEC.md). Allowed rotations are NOT stored in the marker
(they live in the Lay Limits table): the spec says `[0, 180]` with basis `assumed`.
"""
import json, math, os, sys
import accumark_marker as am

FORMAT = 'accumark-nest-spec/1'
UNITS = {'in': 1.0, 'cm': 2.54, 'mm': 25.4}


def _area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts))) / 2


def _dedupe(pts):
    out = [p for i, p in enumerate(pts) if i == 0 or (abs(p[0] - pts[i - 1][0]) > 1e-9 or abs(p[1] - pts[i - 1][1]) > 1e-9)]
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-9 and abs(out[0][1] - out[-1][1]) < 1e-9: out.pop()
    return out


def _ccw(pts):
    return list(pts) if _area(pts) >= 0 else list(reversed(pts))


def _crosses(pts):
    """True when two non-adjacent edges of the closed polygon cross (a spiral or a bow-tie)."""
    n = len(pts)
    def orient(a, b, c): return (c[1] - a[1]) * (b[0] - a[0]) - (b[1] - a[1]) * (c[0] - a[0])
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1: continue
            c, d = pts[j], pts[(j + 1) % n]
            if orient(a, b, c) * orient(a, b, d) < 0 and orient(c, d, a) * orient(c, d, b) < 0: return True
    return False


def _mirror_y(pts, y0, y1):
    """reflect about the horizontal line through the middle of [y0, y1] (the grain axis of the piece frame)."""
    return [(x, y0 + y1 - y) for x, y in pts]


def build_nest_spec(path, units='cm', marker=None):
    """-> [spec] one per marker of the ZIP (or the one named `marker`)."""
    if units not in UNITS: raise ValueError('units must be one of %s' % sorted(UNITS))
    k = UNITS[units]; res = am.place_marker(path); out = []
    for mkr in res['markers']:
        mk = mkr['marker']
        if marker and mk['name'] != marker: continue
        inv = mkr['inventory']; inv['warnings'] = list(inv['warnings']) + am.coverage_warnings(mk)
        rows = {p['name']: p for p in mk['pieces']}
        shapes = {}; groups = {}; problems = []
        for e in inv['slots']:
            slot = next(s for s in mk['slots'] if s['index'] == e['ordinal'])
            rec_i = slot['record_index']
            mirrored = bool(e['preset']['mirror'])
            if rec_i not in shapes:
                ol = e.get('outline')
                shp = dict(id='S%03d' % (len(shapes) + 1), piece=e['piece'], model=e['model'], size=e['size'], cut=e['cut'], category=e['category'],
                           fabric_types=(rows.get(e['piece']) or {}).get('fabric_types', []), declared_area=e['declared_area'] * k * k, perimeter=(e['perimeter'] or 0) * k,
                           outline=None, complete=False)
                if ol and len(ol) >= 3:
                    pts = _dedupe([(x, y) for x, y in ol]); x0 = min(p[0] for p in pts); y0 = min(p[1] for p in pts); y1 = max(p[1] for p in pts)
                    def loc(seq): return [((x - x0) * k, (y - y0) * k) for x, y in seq]
                    o = loc(pts); w = max(p[0] for p in o); h = max(p[1] for p in o)
                    sew = e.get('sew_outline'); sew_l = loc(_dedupe(sew)) if sew and len(sew) >= 3 else None
                    grain = e.get('grain'); gpts = loc(grain) if grain else None
                    shp.update(outline=[list(p) for p in _ccw(o)], area=abs(_area(o)), width=w, height=h,
                               seam_outline=[list(p) for p in _ccw(sew_l)] if sew_l else None,
                               notches=[dict(x=(n['x'] - x0) * k, y=(n['y'] - y0) * k, type=n['type']) for n in e.get('notches', [])],
                               grain=dict(points=[list(p) for p in gpts], angle_deg=0.0, basis=e.get('grain_basis')) if gpts else None,
                               internal_lines=[[list(p) for p in loc(l)] for l in e.get('internal_lines', [])],
                               drills=[list(p) for p in loc(e.get('drills', []))],
                               self_intersecting=_crosses(o), complete=True, _y=(0.0, (y1 - y0) * k))
                    # the box AccuMark stored for the piece: equal to the outline's own box on every marker-only ZIP of the corpus (residual 0),
                    # larger by the block buffer (+ a small curve allowance in y) on the July CP 150 markers - `padding` is what it reserves around the piece
                    shp['stored_box'] = [e['home_box_in'][0] * k, e['home_box_in'][1] * k]
                    shp['padding'] = [shp['stored_box'][0] - w, shp['stored_box'][1] - h]
                else: problems.append(f"{e['piece']} {e['size']}: no outline")
                shapes[rec_i] = shp
            g = groups.setdefault((rec_i, mirrored), dict(shape=shapes[rec_i]['id'], quantity=0, mirrored=mirrored, slots=[], bundles=set(), preset_rot180=0))
            g['quantity'] += 1; g['slots'].append(e['ordinal']); g['bundles'].add(e['bundle']); g['preset_rot180'] += int(e['preset']['rot180'])
        # mirrored outlines, written out
        for shp in shapes.values():
            if shp['complete'] and any(g['mirrored'] and g['shape'] == shp['id'] for g in groups.values()):
                y0, y1 = shp.pop('_y'); M = lambda seq: _mirror_y([tuple(p) for p in seq], y0, y1)     # reflect about the grain axis through the middle of the box
                shp['outline_mirrored'] = [list(p) for p in _ccw(M(shp['outline']))]
                if shp.get('seam_outline'): shp['seam_outline_mirrored'] = [list(p) for p in _ccw(M(shp['seam_outline']))]
                shp['notches_mirrored'] = [dict(x=n['x'], y=y1 + y0 - n['y'], type=n['type']) for n in shp['notches']]
                if shp.get('grain'): shp['grain_mirrored'] = dict(shp['grain'], points=[list(p) for p in M(shp['grain']['points'])])
                shp['internal_lines_mirrored'] = [[list(p) for p in M(l)] for l in shp['internal_lines']]
                shp['drills_mirrored'] = [list(p) for p in M(shp['drills'])]
            else: shp.pop('_y', None)
        demand = [dict(shape=g['shape'], quantity=g['quantity'], mirrored=g['mirrored'], slots=g['slots'], bundles=sorted(g['bundles']), preset_rot180=g['preset_rot180'])
                  for g in sorted(groups.values(), key=lambda g: (g['shape'], g['mirrored']))]
        W = inv['marker']['width_cm'] / 2.54 * k
        n_inst = sum(d['quantity'] for d in demand)
        area_all = sum(shapes_by(shapes, d['shape'])['area'] * d['quantity'] for d in demand if shapes_by(shapes, d['shape']).get('complete'))
        spec = dict(
            format=FORMAT, units=units,
            source=dict(file=os.path.basename(path), marker=mk['name'], models=inv['marker']['models'], laid_state=inv['marker']['laid_state'],
                        lay_history=inv['marker']['lay_history'], decoder_version=am.__version__),
            fabric=dict(width=W, fabric_types=inv['marker']['fabric_types'],
                        block_buffer_in=[list(b) for b in inv['marker']['block_buffers']] or None,
                        min_length=(area_all / W) if W else None, min_length_note='total piece area / width: a 100%-efficient lay; not a nesting result'),
            rotation=dict(allowed_deg=[0, 180], basis='assumed: the Lay Limits table is not stored in the marker; grain runs along x in every shape'),
            order_lines=[dict(model=o['model'], size=o['size'], quantity=o['quantity']) for o in inv['order_lines']],
            shapes=[_public(s) for s in sorted(shapes.values(), key=lambda s: s['id'])], demand=demand,
            totals=dict(instances=n_inst, shapes=len(shapes), mirrored_instances=sum(d['quantity'] for d in demand if d['mirrored']),
                        area=area_all, already_placed=inv['totals']['placed'], outline_source=inv['marker'].get('outline_source')),
            warnings=[w for w in inv['warnings'] if not w.startswith('no piece objects')] + problems)
        spec['checks'] = [dict(name=n, ok=bool(ok), detail=d) for n, ok, d in validate_nest_spec(spec, _private=shapes, marker_checks=mkr['checks'], inv=inv, k=k)]
        spec['complete'] = all(c['ok'] for c in spec['checks']) and not problems
        out.append(spec)
    return out


def shapes_by(shapes, sid):
    return next(s for s in shapes.values() if s['id'] == sid)


def _public(s):
    return {k: v for k, v in s.items() if not k.startswith('_')}


def validate_nest_spec(spec, _private=None, marker_checks=(), inv=None, k=1.0):
    """-> [(check, ok, detail)]. Everything here is checked against numbers AccuMark stored itself, not against the decode."""
    rows = []; by_id = {s['id']: s for s in spec['shapes']}
    priv = {s['id']: s for s in (_private or {}).values()}
    n_inst = sum(d['quantity'] for d in spec['demand'])
    rows.append(('every instance to lay has a shape with an outline', all(by_id[d['shape']].get('complete') for d in spec['demand']), f"{len(spec['shapes'])} shapes, {n_inst} instances"))
    rows.append(('demand refers to known shapes only', all(d['shape'] in by_id for d in spec['demand']), ''))
    if inv is not None:
        rows.append(('instances == unplaced slots of the marker', n_inst == inv['totals']['slots'], f"{n_inst} vs {inv['totals']['slots']}"))
        rows.append(('sum(area x quantity) == the marker\'s own area to lay', abs(spec['totals']['area'] - inv['totals']['area_to_lay'] * k * k) <= 0.01 * max(1.0, spec['totals']['area']),
                     f"{spec['totals']['area']:.2f} vs {inv['totals']['area_to_lay'] * k * k:.2f}"))
    comp = [s for s in spec['shapes'] if s.get('complete')]
    bad = [s['id'] for s in comp if s['declared_area'] and abs(s['area'] / s['declared_area'] - 1) > 0.01]
    rows.append(('outline area == the area AccuMark declares for the piece (1%)', not bad, f"{len(comp) - len(bad)} of {len(comp)}" + (f"; off: {bad[:4]}" if bad else '')))
    tol = 2e-3 * k
    bad = [s['id'] for s in comp if any(v < -tol or v > 0.25 * k for v in s['padding'])]
    exact = sum(1 for s in comp if all(abs(v) <= tol for v in s['padding']))
    rows.append(('outline fits the box AccuMark stored (never larger, at most 0.25 in of padding)', not bad,
                 f"{exact} of {len(comp)} exactly equal, {len(comp) - exact - len(bad)} padded (reserve `padding` around them)" + (f"; off: {bad[:4]}" if bad else '')))
    bad = [s['id'] for s in comp if not all(s['outline'][i] != s['outline'][(i + 1) % len(s['outline'])] for i in range(len(s['outline']))) or _area([tuple(p) for p in s['outline']]) <= 0]
    rows.append(('outlines are counter-clockwise closed polygons without repeated points', not bad, ''))
    si = [s['id'] for s in comp if s.get('self_intersecting')]
    rows.append(('self-crossing outlines (informational: a ruffle spiral is legitimate)', True, f"{len(si)}: {si[:4]}" if si else 'none'))
    bad = [s['id'] for s in comp if s.get('outline_mirrored') and abs(abs(_area([tuple(p) for p in s['outline_mirrored']])) - s['area']) > 1e-6 * max(1, s['area'])]
    rows.append(('mirrored outlines have the same area', not bad, ''))
    rows.append(('the marker\'s own checks all pass', all(ok for _, ok, _ in marker_checks), ''))
    return rows


# --------------------------------------------------------------------------------- DXF / SVG
def _grid(spec, gap, row_w):
    """place each shape once, mirrored ones next to it: [(shape, mirrored, dx, dy)]"""
    placed = []; x = y = rowh = 0.0
    for s in spec['shapes']:
        if not s.get('complete'): continue
        for mir in ([False] + ([True] if s.get('outline_mirrored') else [])):
            if x + s['width'] > row_w and x > 0: x = 0.0; y += rowh + gap; rowh = 0.0
            placed.append((s, mir, x, y)); x += s['width'] + gap; rowh = max(rowh, s['height'])
    return placed


def write_dxf(spec, path, gap=None):
    """A piece library as ASCII DXF (R12 entities): one closed POLYLINE per shape on layer CUT (SEAM for the stitch line, INTERNAL, GRAIN as a LINE,
    NOTCH and DRILL as POINTs), a TEXT label 'id piece size xN'. Units are those of the spec ($INSUNITS 4 mm, 5 cm, 1 in)."""
    u = spec['units']; gap = gap if gap is not None else {'cm': 2.0, 'mm': 20.0, 'in': 1.0}[u]; row_w = {'cm': 200.0, 'mm': 2000.0, 'in': 80.0}[u]
    L = []
    def g(c, v): L.append(f'{c:>3}'); L.append(str(v))
    def poly(layer, pts, dx, dy, closed=True):
        g(0, 'POLYLINE'); g(8, layer); g(66, 1); g(70, 1 if closed else 0)
        for x, y in pts: g(0, 'VERTEX'); g(8, layer); g(10, f'{x + dx:.4f}'); g(20, f'{y + dy:.4f}')
        g(0, 'SEQEND'); g(8, layer)
    g(0, 'SECTION'); g(2, 'HEADER'); g(9, '$INSUNITS'); g(70, {'in': 1, 'mm': 4, 'cm': 5}[u]); g(0, 'ENDSEC')
    g(0, 'SECTION'); g(2, 'ENTITIES')
    qty = {}
    for d in spec['demand']: qty.setdefault(d['shape'], [0, 0]); qty[d['shape']][1 if d['mirrored'] else 0] += d['quantity']
    for s, mir, dx, dy in _grid(spec, gap, row_w):
        poly('CUT', s['outline_mirrored'] if mir else s['outline'], dx, dy)
        sw = s.get('seam_outline_mirrored') if mir else s.get('seam_outline')
        if sw: poly('SEAM', sw, dx, dy)
        for l in s.get('internal_lines', []): poly('INTERNAL', l if not mir else _mirror_y([tuple(p) for p in l], 0, s['height']), dx, dy, closed=False)
        if s.get('grain'):
            gp = s['grain']['points'] if not mir else _mirror_y([tuple(p) for p in s['grain']['points']], 0, s['height'])
            g(0, 'LINE'); g(8, 'GRAIN'); g(10, f'{gp[0][0] + dx:.4f}'); g(20, f'{gp[0][1] + dy:.4f}'); g(11, f'{gp[1][0] + dx:.4f}'); g(21, f'{gp[1][1] + dy:.4f}')
        for n in s.get('notches', []):
            y = n['y'] if not mir else s['height'] - n['y']
            g(0, 'POINT'); g(8, 'NOTCH'); g(10, f"{n['x'] + dx:.4f}"); g(20, f'{y + dy:.4f}')
        for p in s.get('drills', []):
            y = p[1] if not mir else s['height'] - p[1]
            g(0, 'POINT'); g(8, 'DRILL'); g(10, f'{p[0] + dx:.4f}'); g(20, f'{y + dy:.4f}')
        q = qty.get(s['id'], [0, 0])
        g(0, 'TEXT'); g(8, 'LABEL'); g(10, f'{dx:.4f}'); g(20, f'{dy - 0.03 * max(s["height"], 1):.4f}'); g(40, f'{max(s["height"] * 0.04, 0.3 if u == "cm" else 3.0 if u == "mm" else 0.12):.3f}')
        g(1, f"{s['id']} {s['piece']} {s['size']} x{q[1] if mir else q[0]}{' mirrored' if mir else ''}")
    g(0, 'ENDSEC'); g(0, 'EOF')
    open(path, 'w', encoding='latin-1', newline='\r\n').write('\n'.join(L) + '\n')


def read_dxf_polylines(path):
    """{layer: [[(x, y), ...], ...]} - a tiny reader for the DXF this module writes (used by the selftest to prove the file says what the JSON says)."""
    t = open(path, encoding='latin-1').read().split('\n'); t = [x.strip() for x in t]; pairs = list(zip(t[0::2], t[1::2]))
    res = {}; cur = None; layer = None
    for c, v in pairs:
        if c == '0':
            if v == 'POLYLINE': cur = []; layer = None
            elif v == 'SEQEND' and cur is not None: res.setdefault(layer, []).append(cur); cur = None
            elif v == 'VERTEX': cur.append([None, None]) if cur is not None else None
        elif c == '8' and cur is not None and layer is None: layer = v
        elif c == '10' and cur: cur[-1][0] = float(v)
        elif c == '20' and cur: cur[-1][1] = float(v)
    return {k: [[tuple(p) for p in pl] for pl in v] for k, v in res.items()}


def write_svg(spec, path):
    u = spec['units']; gap = {'cm': 2.0, 'mm': 20.0, 'in': 1.0}[u]; row_w = {'cm': 200.0, 'mm': 2000.0, 'in': 80.0}[u]; sc = {'cm': 4.0, 'mm': 0.4, 'in': 10.0}[u]
    pl = _grid(spec, gap, row_w); W = max((dx + s['width'] for s, _, dx, _ in pl), default=10); H = max((dy + s['height'] for s, _, _, dy in pl), default=10)
    parts = []
    for s, mir, dx, dy in pl:
        def P(pts): return ' '.join(f'{(x + dx) * sc + 10:.1f},{(H - (y + dy)) * sc + 30:.1f}' for x, y in pts)
        parts.append(f'<polygon points="{P(s["outline_mirrored"] if mir else s["outline"])}" fill="#dbe8ff" stroke="#1a4d8f" stroke-width="1.2"/>')
        sw = s.get('seam_outline_mirrored') if mir else s.get('seam_outline')
        if sw: parts.append(f'<polygon points="{P(sw)}" fill="none" stroke="#c0392b" stroke-width="0.8" stroke-dasharray="4 2"/>')
        if s.get('grain'):
            gp = s['grain']['points'] if not mir else _mirror_y([tuple(p) for p in s['grain']['points']], 0, s['height'])
            parts.append(f'<polyline points="{P(gp)}" stroke="#2a7d2a" stroke-width="1" fill="none"/>')
        for n in s.get('notches', []):
            y = n['y'] if not mir else s['height'] - n['y']; parts.append(f'<circle cx="{(n["x"] + dx) * sc + 10:.1f}" cy="{(H - (y + dy)) * sc + 30:.1f}" r="2.5" fill="#e67e22"/>')
        for p in s.get('drills', []):
            y = p[1] if not mir else s['height'] - p[1]; parts.append(f'<circle cx="{(p[0] + dx) * sc + 10:.1f}" cy="{(H - (y + dy)) * sc + 30:.1f}" r="3" fill="none" stroke="#000"/>')
        parts.append(f'<text x="{dx * sc + 10:.1f}" y="{(H - dy) * sc + 44:.1f}" font-family="sans-serif" font-size="10" fill="#333">{s["id"]} {s["piece"]} {s["size"]}{" (mirrored)" if mir else ""}</text>')
    head = f'{spec["source"]["marker"]} - {spec["totals"]["instances"]} pieces, {spec["totals"]["shapes"]} shapes, fabric width {spec["fabric"]["width"]:.1f} {u}; blue cut, red dashed seam, green grain, orange notch'
    open(path, 'w', encoding='utf-8').write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W * sc + 30:.0f}" height="{H * sc + 70:.0f}"><rect width="100%" height="100%" fill="white"/><text x="10" y="18" font-family="sans-serif" font-size="12">{head}</text>' + ''.join(parts) + '</svg>')


def report(spec):
    t = spec['totals']; f = spec['fabric']; c = spec['checks']
    lines = [f"== {spec['source']['marker']} ({spec['source']['laid_state']}) ==",
             f"fabric width {f['width']:.1f} {spec['units']}; fabric types {', '.join(f['fabric_types']) or '-'}; shortest lay {f['min_length']:.1f} {spec['units']} at 100% efficiency",
             f"{t['instances']} pieces to lay ({t['mirrored_instances']} mirrored) over {t['shapes']} shapes, total area {t['area']:.1f} {spec['units']}^2, outline source {t['outline_source']}"]
    lines += [f"   {'ok ' if x['ok'] else 'BAD'} {x['name']}" + (f": {x['detail']}" if x['detail'] else '') for x in c]
    lines += ['   note: ' + w for w in spec['warnings']]
    lines.append('NEST SPEC COMPLETE' if spec['complete'] else 'NEST SPEC INCOMPLETE - see the BAD lines')
    return '\n'.join(lines)


def main(argv):
    a = [x for x in argv if not x.startswith('--')]
    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv else default
    if not a:
        print(__doc__); return 2
    units = opt('--units', 'cm'); specs = build_nest_spec(a[0], units, opt('--marker'))
    if not specs: print('no such marker in the ZIP'); return 1
    for sp in specs:
        tag = '' if len(specs) == 1 else '.' + ''.join(ch if ch.isalnum() else '_' for ch in sp['source']['marker'])
        for flag, ext, fn in (('--json', '.json', lambda s, p: json.dump(s, open(p, 'w'), indent=1)), ('--dxf', '.dxf', write_dxf), ('--svg', '.svg', write_svg)):
            base = opt(flag)
            if base:
                p = base if not tag else os.path.splitext(base)[0] + tag + (os.path.splitext(base)[1] or ext)
                fn(sp, p); print('wrote', p)
        print(report(sp))
    return 0 if all(s['complete'] for s in specs) else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
