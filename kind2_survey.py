#!/usr/bin/env python3
"""Corpus-wide survey of the line table's kind=2 records.

Replaces the prose-only "7226 / 2920 (40%)" figures from CHANGELOG.md /
FORMAT_SPEC.md SS11-SS12 with a persisted, re-runnable measurement: one CSV
row per kind=2 point across every piece object in the corpus, plus a summary
table printed to stdout.

Usage:
    python kind2_survey.py [--out kind2_survey.csv] [--zips GLOB ...]

Reuses accumark_pds.decode / check_line_table and accumark_marker.list_zip
rather than re-implementing parsing. The per-point classification helpers
inside check_line_table are closures and not importable, so this script
re-derives the same three geometric primitives (point-to-segment distance,
nearest-polyline lookup, in-`real`-set membership) standalone - see
accumark_pds.py's check_line_table docstring for the canonical versions
these mirror.
"""
import argparse, csv, glob, math, os, sys

import accumark_pds as ap
import accumark_marker as am
import verify_capture as vc

UNITS = ap.UNITS_PER_INCH


def _seg_dist(pt, a, c):
    ax, ay = a; cx, cy = c; px, py = pt
    dx, dy = cx - ax, cy - ay
    L = dx * dx + dy * dy
    t = 0.0 if L == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _nearest_perimeter_dist(pt, perim):
    """Point-to-segment distance against the closed perimeter polyline."""
    n = len(perim)
    if n == 0:
        return None
    if n == 1:
        return math.hypot(pt[0] - perim[0][0], pt[1] - perim[0][1])
    return min(_seg_dist(pt, perim[i], perim[(i + 1) % n]) for i in range(n))


def default_zip_globs():
    return [
        'CAP-*/*.ZIP', 'CAP-*/*.zip',
        'captures/*/*.ZIP', 'captures/*/*.zip',
        'markers/**/*.zip', 'markers/**/*.ZIP',
    ]


def find_zips(globs, extra):
    paths = []
    for g in globs:
        paths += glob.glob(g, recursive=True)
    for e in extra:
        paths += glob.glob(e, recursive=True)
    seen = set(); out = []
    for p in sorted(paths):
        rp = os.path.normpath(p)
        if rp in seen:
            continue
        seen.add(rp); out.append(p)
    return out


def dxf_for(zip_path):
    """A capture folder's single DXF, if this zip lives in one (CAP-*/, captures/*/)."""
    folder = os.path.dirname(zip_path)
    cands = glob.glob(os.path.join(folder, '*.DXF')) + glob.glob(os.path.join(folder, '*.dxf'))
    return cands[0] if cands else None


def dxf_layer14_polylines(dxf_path, perim_in):
    """Layer-14 (sew line) polylines from the DXF, aligned into the binary
    piece's coordinate frame via the same dominant-vertex-translation trick
    verify_capture.dxf_check uses. Returns [] if there is no layer-14 data
    or no shift could be determined."""
    try:
        polys = vc.dxf_outline(dxf_path)
    except Exception:
        return []
    d1 = [p for pl in polys if pl['layer'] in ('1', '14') for p in pl['pts']]
    if not d1 or not perim_in:
        return []
    from collections import Counter
    votes = Counter((round(qx - px, 4), round(qy - py, 4))
                     for px, py in perim_in for qx, qy in d1)
    if not votes:
        return []
    (tx, ty), _n = votes.most_common(1)[0]
    return [[(x - tx, y - ty) for x, y in pl['pts']] for pl in polys if pl['layer'] == '14']


def survey(zip_paths, out_path):
    fields = [
        'zip', 'member', 'piece_name', 'block', 'record_idx', 'record_kind',
        'n_points', 'point_idx', 'a', 'b', 'c', 'e', 'x', 'y', 'in_real',
        'nearest_perim_units', 'nearest_perim_in', 'nearest_perim_mm',
        'nearest_dxf14_in', 'block_check_line_table',
    ]
    rows_written = 0
    blocks_with_tail = 0
    blocks_passing = 0
    total_k2_points = 0
    not_in_real = 0
    per_piece_unexplained = {}

    with open(out_path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(fields)

        for zpath in zip_paths:
            try:
                objs = am.list_zip(zpath)
            except Exception as e:
                print('  ! skip %s: %s' % (zpath, e), file=sys.stderr)
                continue
            pieces = objs.get('piece', [])
            dxf_path = dxf_for(zpath)

            for o in pieces:
                try:
                    r = ap.decode(o['data'])
                except Exception as e:
                    print('  ! decode error %s!%s: %s' % (zpath, o['member'], e), file=sys.stderr)
                    continue

                for bi, b in enumerate(r['blocks']):
                    t = b.get('tail')
                    if not isinstance(t, dict) or 'error' in t or not t.get('line_records'):
                        continue
                    blocks_with_tail += 1

                    real = {(p['x'], p['y']) for p in b['perimeter']}
                    for seg in b['internal_lines']:
                        real |= {(p['x'], p['y']) for p in seg}
                    if isinstance(b.get('closing'), list):
                        real |= {(p['x'], p['y']) for p in b['closing']}

                    perim = [(p['x'], p['y']) for p in b['perimeter']]
                    perim_in = [(x / UNITS, y / UNITS) for x, y in perim]
                    layer14 = dxf_layer14_polylines(dxf_path, perim_in) if dxf_path else []

                    passed = ap.check_line_table(b)
                    blocks_passing += int(passed)
                    piece_key = (zpath, o['name'])
                    per_piece_unexplained.setdefault(piece_key, 0)

                    for rc in t['line_records']:
                        if rc['kind'] != 2:
                            continue
                        pts = rc['points']
                        for pi, tp in enumerate(pts):
                            pt = (tp['x'], tp['y'])
                            in_real = pt in real
                            total_k2_points += 1
                            d_units = _nearest_perimeter_dist(pt, perim)
                            d_in = d_units / UNITS if d_units is not None else None
                            d_mm = d_in * 25.4 if d_in is not None else None
                            d14 = None
                            if layer14:
                                p_in = (tp['x'] / UNITS, tp['y'] / UNITS)
                                best = None
                                for pl in layer14:
                                    if len(pl) > 1:
                                        dd = _nearest_perimeter_dist(p_in, pl)
                                    else:
                                        dd = math.hypot(p_in[0] - pl[0][0], p_in[1] - pl[0][1])
                                    if best is None or dd < best:
                                        best = dd
                                d14 = best
                            if not in_real:
                                not_in_real += 1
                                per_piece_unexplained[piece_key] += 1

                            w.writerow([
                                zpath, o['member'], o['name'], bi,
                                rc['idx'], rc['kind'], rc['n_points'], pi,
                                tp['a'] if tp['a'] != 65535 else -1, tp['b'], tp['c'], tp['e'],
                                tp['x'], tp['y'], int(in_real),
                                ('%.1f' % d_units) if d_units is not None else '',
                                ('%.4f' % d_in) if d_in is not None else '',
                                ('%.2f' % d_mm) if d_mm is not None else '',
                                ('%.4f' % d14) if d14 is not None else '',
                                int(passed),
                            ])
                            rows_written += 1

    return dict(
        blocks_with_tail=blocks_with_tail,
        blocks_passing=blocks_passing,
        total_k2_points=total_k2_points,
        not_in_real=not_in_real,
        rows_written=rows_written,
        per_piece_unexplained=per_piece_unexplained,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='robustness/kind2_survey.csv')
    parser.add_argument('--zips', nargs='*', default=[])
    args = parser.parse_args()

    zip_paths = find_zips(default_zip_globs(), args.zips)
    print('scanning %d zips...' % len(zip_paths))
    summary = survey(zip_paths, args.out)

    print()
    print('decoder_version: accumark_pds=%s accumark_marker=%s' % (ap.__version__, am.__version__))
    print('blocks with a decodable tail   : %d' % summary['blocks_with_tail'])
    bp = summary['blocks_passing']; bt = max(1, summary['blocks_with_tail'])
    print('blocks passing check_line_table: %d (%.1f%%)' % (bp, 100.0 * bp / bt))
    print('kind=2 points total            : %d' % summary['total_k2_points'])
    tot = max(1, summary['total_k2_points'])
    explained = summary['total_k2_points'] - summary['not_in_real']
    print('kind=2 points explained (in real): %d (%.1f%%)' % (explained, 100.0 * explained / tot))
    print('kind=2 points NOT in real       : %d (%.1f%%)' % (summary['not_in_real'], 100.0 * summary['not_in_real'] / tot))
    print('CSV written: %s (%d rows)' % (args.out, summary['rows_written']))

    worst = sorted(summary['per_piece_unexplained'].items(), key=lambda kv: -kv[1])[:15]
    if worst and worst[0][1] > 0:
        print('\ntop pieces by unexplained kind=2 point count:')
        for (zpath, name), n in worst:
            if n == 0:
                continue
            print('  %5d  %-40s %s' % (n, os.path.basename(zpath), name))


if __name__ == '__main__':
    main()
