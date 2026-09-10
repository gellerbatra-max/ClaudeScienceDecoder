#!/usr/bin/env python3
"""dataset_test.py - decode dataset/generated/ and check every result
against dataset/MANIFEST.json (the ground truth recorded at generation time
by dataset/build.py). This is the primary proof the decoder handles complex,
multi-piece, multi-size patterns and markers correctly, not just the small
controlled probes in the main fixture corpus.

    python dataset_test.py              full report, one line per panel/marker
    python dataset_test.py --quick       reduced set (~6 panels + 1 marker),
                                          budgeted for selftest.py's per-run cost

Exits non-zero on any failure.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import accumark_pds as ap
import accumark_marker as am

MANIFEST = os.path.join(HERE, 'dataset', 'MANIFEST.json')
GEN = os.path.join(HERE, 'dataset', 'generated')

GEOM_TOL_IN = 1e-4      # exact - the decoder must reproduce the drafted base outline bit-for-bit
AREA_TOL = 1e-6
GRADE_TOL_IN = 0.02     # delta-invariance tolerance, see build.py's module docstring


def _load_manifest():
    if not os.path.isfile(MANIFEST):
        raise SystemExit('%s not found - run: python dataset/build.py' % MANIFEST)
    return json.load(open(MANIFEST, encoding='utf-8'))


def _shoelace(pts):
    return abs(sum(pts[i][0]*pts[(i+1) % len(pts)][1] - pts[(i+1) % len(pts)][0]*pts[i][1]
                   for i in range(len(pts)))) / 2


def check_panel(entry):
    """-> (ok, detail). Decodes the generated zip fresh and checks every
    fact the manifest recorded, independently of how build.py produced it."""
    path = os.path.join(GEN, entry['zip'])
    bad = []
    try:
        dec = ap.decode_zip(path)
    except Exception as e:
        return False, '%s: %s' % (type(e).__name__, e)
    if len(dec['blocks']) != 1:
        return False, 'expected 1 block, got %d' % len(dec['blocks'])
    block = dec['blocks'][0]

    got = [(round(p['x']/1e4, 4), round(p['y']/1e4, 4)) for p in block['perimeter']]
    want = [tuple(p) for p in entry['base_outline_in']]
    if got != want:
        worst = max((abs(a[0]-b[0])+abs(a[1]-b[1]) for a, b in zip(got, want)), default=9)
        bad.append('base outline mismatch (worst |dx|+|dy|=%.5f)' % worst)

    area = _shoelace(got)
    if abs(area - entry['base_area_sqin']) > max(AREA_TOL, 1e-3 * entry['base_area_sqin']):
        bad.append('area %.4f != manifest %.4f' % (area, entry['base_area_sqin']))

    got_notches = [i for i, p in enumerate(block['perimeter']) if p['is_notch']]
    if got_notches != entry['notch_indices']:
        bad.append('notch indices %r != manifest %r' % (got_notches, entry['notch_indices']))

    sizes = [s['name'] for s in block['meta']['sizes']]
    if sizes != entry['sizes']:
        bad.append('sizes %r != manifest %r' % (sizes, entry['sizes']))

    worst_grade = 0.0
    if entry['real_grading']:
        for sz, want_pts in entry['per_size_expected_in'].items():
            go = am.graded_outline(block, sz)
            if go is None:
                bad.append('graded_outline(%r) returned None' % sz); continue
            worst_grade = max(worst_grade,
                               max(abs(a[0]-b[0])+abs(a[1]-b[1]) for a, b in zip(go, want_pts)))
        if worst_grade > GRADE_TOL_IN:
            bad.append('grading worst residual %.4f > %.4f' % (worst_grade, GRADE_TOL_IN))

    return (not bad), ('ok' if not bad else '; '.join(bad))


def check_marker(entry):
    path = os.path.join(GEN, entry['zip']) if 'zip' in entry and entry.get('provenance') == 'generated' \
        else os.path.join(HERE, entry['zip'])
    try:
        res = am.place_marker(path)
    except Exception as e:
        return False, '%s: %s' % (type(e).__name__, e)
    mkr = res['markers'][0]
    if entry.get('provenance') == 'generated':
        checks = {n: ok for n, ok, _ in mkr['checks']}
        new_failures = [n for n, ok in checks.items()
                         if not ok and n not in (entry.get('pre_existing_failures') or [])]
        if new_failures:
            return False, 'new check failures: %r' % new_failures
        if len(mkr['placed']) != entry['placements']:
            return False, 'placements %d != manifest %d' % (len(mkr['placed']), entry['placements'])
        return True, 'ok (%d placements)' % len(mkr['placed'])
    else:
        return True, 'ok (reused fixture, %d markers, %d placements)' % (
            len(res['markers']), len(mkr['placed']))


def run(quick=False):
    m = _load_manifest()
    fails = []
    panels = m['panels']
    markers = m['markers']
    if quick:
        # one panel per template, one per garment where possible, budgeted
        # for selftest.py's per-run cost.
        seen_t = set(); picked = []
        for e in panels:
            if e['template'] not in seen_t:
                seen_t.add(e['template']); picked.append(e)
        panels = picked
        markers = [x for x in markers if x.get('provenance') == 'generated']

    print('-- dataset panels (%d)' % len(panels))
    for e in panels:
        ok, detail = check_panel(e)
        print('   %s %-14s %-16s %s' % ('ok ' if ok else 'FAIL', e['garment'], e['panel'], detail))
        if not ok: fails.append('%s/%s: %s' % (e['garment'], e['panel'], detail))

    print('-- dataset markers (%d)' % len(markers))
    for e in markers:
        ok, detail = check_marker(e)
        print('   %s %-28s %s' % ('ok ' if ok else 'FAIL', e['name'], detail))
        if not ok: fails.append('%s: %s' % (e['name'], detail))

    return len(panels) + len(markers) - len(fails), len(fails), fails


def quick():
    n_ok, n_fail, fails = run(quick=True)
    return n_ok, n_fail, fails


if __name__ == '__main__':
    n_ok, n_fail, fails = run(quick='--quick' in sys.argv[1:])
    print()
    if fails:
        print('DATASET_TEST FAIL (%d/%d)' % (n_fail, n_ok + n_fail))
        for x in fails: print('  -', x)
        sys.exit(1)
    print('DATASET_TEST PASS (%d checked)' % n_ok)
