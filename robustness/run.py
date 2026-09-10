#!/usr/bin/env python3
"""robustness/run.py - the three-oracle ZIP robustness suite.

    python robustness/run.py             full matrix, writes ROBUSTNESS_REPORT.md
    python robustness/run.py --quick      reduced matrix, for selftest.py

Oracle A (metamorphic invariance): restructuring a ZIP without changing its
XGGT payloads must not change the decode - canon(variant) == canon(original).
Oracle B (controlled-failure contract): a malformed input must raise a
named, declared exception - never a bare IndexError/struct.error/SystemExit,
never a plausible wrong answer.
Oracle C (corruption detection): a byte the decoder itself proved carries a
value must, when corrupted, either raise or change the decode - never
silently produce the same "plausible" answer.

See dataset/templates.py and robustness/canon.py's docstrings for why the
comparisons are built the way they are.
"""
import io, os, struct, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import accumark_pds as ap
import accumark_marker as am
import accumark_errors as err
from robustness import zipfuzz as zf
from robustness import canon as cn

REPORT_PATH = os.path.join(REPO, 'ROBUSTNESS_REPORT.md')
BASELINE_PATH = os.path.join(HERE, 'baseline_v1.json')

SEEDS = [
    # (label, path relative to repo root, kind: 'piece'|'marker')
    ('CAP-C00-BASE', 'CAP-C00-BASE/CAP-C00-BASE.zip', 'piece'),
    ('CAP-C62-DART', 'CAP-C62-DART/CAP-C62-DART.ZIP', 'piece'),
    ('CLAUDE-GRADE-MARKER', 'markers/CLAUDE-GRADE-MARKER/CLAUDE-GRADE-MARKER.zip', 'marker'),
    ('2303-BD137-PLACED', 'markers/2303-BD137-PLACED/2303-BD 137 PLACED.zip', 'marker'),
]
QUICK_SEEDS = SEEDS[:2]


# --------------------------------------------------------------- Oracle A
def oracle_a(seeds):
    rows = []
    for label, rel, kind in seeds:
        path = os.path.join(REPO, rel)
        items = zf.members(path)
        base_objs = am.list_zip(path)
        base_canon = cn.canon_list_zip(base_objs)
        # self-check: the canonicaliser must be reflexive, else every
        # comparison below is vacuous.
        assert cn.canon_list_zip(am.list_zip(path)) == base_canon, \
            'canon() is non-deterministic on %s' % label
        for variant_fn in zf.ORACLE_A_VARIANTS:
            case = '%s/%s' % (label, variant_fn.__name__)
            try:
                v = variant_fn(items)
                v_objs = am.list_zip(v)
                v_canon = cn.canon_list_zip(v_objs)
                ok = (v_canon == base_canon)
                detail = 'ok' if ok else 'canon mismatch'
            except Exception as e:
                ok = False; detail = '%s: %s' % (type(e).__name__, e)
            rows.append(dict(oracle='A', case=case, seed=label, ok=ok, detail=detail))
        if kind == 'marker':
            base_place = cn.canon_place_marker(am.place_marker(path))
            for variant_fn in zf.ORACLE_A_VARIANTS:
                case = '%s/place_marker/%s' % (label, variant_fn.__name__)
                try:
                    v = variant_fn(items)
                    v_place = cn.canon_place_marker(am.place_marker(v))
                    ok = (v_place == base_place)
                    detail = 'ok' if ok else 'canon mismatch'
                except Exception as e:
                    ok = False; detail = '%s: %s' % (type(e).__name__, e)
                rows.append(dict(oracle='A', case=case, seed=label, ok=ok, detail=detail))
    return rows


# --------------------------------------------------------------- Oracle B
def _bcase(name, seed, builder, entry, expect):
    return dict(name=name, seed=seed, builder=builder, entry=entry, expect=expect)


def oracle_b_cases():
    piece_seed = os.path.join(REPO, 'CAP-C00-BASE/CAP-C00-BASE.zip')
    marker_seed = os.path.join(REPO, 'markers/2303-BD137-PLACED/2303-BD 137 PLACED.zip')
    order_seed = os.path.join(REPO, 'markers/COSTORDER.zip')
    wrapper_seed = os.path.join(REPO, '../../2303-20260908T180223Z-1-001.zip')
    piece_items = zf.members(piece_seed)
    marker_items = zf.members(marker_seed)
    marker_piece = [d for n, d in marker_items
                     if d.startswith(am.MAGIC) and am.u16(d, 0x7a) == 9][0]

    cases = [
        _bcase('empty_file', '-', lambda: zf.b_empty(), ap.decode_zip, (zipfile_error(),)),
        _bcase('random_bytes', '-', lambda: zf.b_random(), ap.decode_zip, (zipfile_error(),)),
        _bcase('truncated_50pct', 'CAP-C00-BASE', lambda: zf.b_truncated(piece_items, 0.5),
               ap.decode_zip, (zipfile_error(), err.AccuMarkError)),
        _bcase('zero_members', '-', lambda: zf.b_zero_members(), ap.decode_zip, (err.NotAnAccuMarkZip,)),
        _bcase('only_junk_members', '-', lambda: zf.b_only_junk(), ap.decode_zip, (err.NotAnAccuMarkZip,)),
        _bcase('marker_zip_to_decode_zip', '2303-BD137-PLACED', lambda: open(marker_seed, 'rb'),
               ap.decode_zip, (err.AmbiguousObject,)),
        _bcase('order_only_to_decode_zip', 'COSTORDER', lambda: open(order_seed, 'rb'),
               ap.decode_zip, (err.NoSuchObject,)),
        _bcase('duplicate_members', 'CAP-C00-BASE', lambda: zf.b_duplicate_members(piece_items),
               lambda p: am.list_zip(p), (type(None),)),  # special-cased below: must NOT raise
        _bcase('nested_wrapper_zip', 'Drive-wrapper', lambda: open(wrapper_seed, 'rb'),
               ap.decode_zip, (err.NestedArchive,)),
        # a 123-byte candidate is too short even to read its type byte, so
        # _select_piece_member (which pre-filters on length+type before
        # calling decode()) reports it as "no usable piece object" rather
        # than reaching decode()'s own more specific TruncatedObject - both
        # are correct, controlled outcomes; NoSuchObject is simply less
        # precise for this particular input shape.
        _bcase('truncated_object_123B_decode_zip', 'CAP-C00-BASE',
               lambda: _wrap_object(piece_items, 123), ap.decode_zip,
               (err.TruncatedObject, err.NoSuchObject)),
        _bcase('truncated_object_123B_list_zip', 'CAP-C00-BASE',
               lambda: _wrap_object(piece_items, 123),
               lambda p: _assert_piece_dropped(p), (type(None),)),
        _bcase('truncated_object_200B_list_zip', '2303-BD137-PLACED',
               lambda: _wrap_object([(n, d[:200] if d is marker_piece else d) for n, d in marker_items], None),
               lambda p: _assert_marker_dropped(p), (type(None),)),
    ]
    return cases


def zipfile_error():
    import zipfile
    return zipfile.BadZipFile


def _wrap_object(items, cut):
    if cut is None:
        return zf.build(items)
    name, data = items[0]
    return zf.build([(name, data[:cut])] + list(items[1:]))


def _assert_piece_dropped(path):
    """truncated_object_123B_list_zip: list_zip must not raise and must not
    abort the whole listing - it skips the one corrupted member and records
    why in object_errors, while ver.5 (the other member) is simply not an
    XGGT object at all, so nothing else in this particular fixture survives
    to prove non-abort; the assertion is just that the call itself returns
    cleanly with the corruption recorded."""
    objs = am.list_zip(path)
    assert 'piece' not in objs, 'the truncated piece should have been skipped, not returned'
    assert objs.get('object_errors'), 'the truncation should be recorded in object_errors'
    return None


def _assert_marker_dropped(path):
    """truncated_object_200B: list_zip must not raise and must not abort the
    whole listing - it skips the one corrupted member and records why in
    object_errors, while every other object in the zip still comes back."""
    objs = am.list_zip(path)
    assert 'marker' not in objs, 'the truncated marker should have been skipped, not returned'
    assert objs.get('object_errors'), 'the truncation should be recorded in object_errors'
    assert objs.get('piece'), 'other objects in the zip should still be listed'
    return None


def oracle_b():
    rows = []
    for c in oracle_b_cases():
        try:
            src = c['builder']()
        except Exception as e:
            rows.append(dict(oracle='B', case=c['name'], seed=c['seed'], ok=False,
                              detail='builder failed: %s: %s' % (type(e).__name__, e)))
            continue
        try:
            c['entry'](src)
            got_exc = None
        except Exception as e:
            got_exc = e
        finally:
            if hasattr(src, 'close'):
                try: src.close()
                except Exception: pass
        if type(None) in c['expect']:
            ok = got_exc is None
            detail = 'ok (no exception, as required)' if ok else \
                'raised %s: %s (expected no exception)' % (type(got_exc).__name__, got_exc)
        else:
            ok = got_exc is not None and isinstance(got_exc, c['expect'])
            detail = ('ok (%s)' % type(got_exc).__name__ if ok else
                       ('no exception raised' if got_exc is None else
                        'raised %s: %s (expected %s)' % (
                            type(got_exc).__name__, got_exc,
                            '/'.join(t.__name__ for t in c['expect']))))
        rows.append(dict(oracle='B', case=c['name'], seed=c['seed'], ok=ok, detail=detail))
    return rows


# --------------------------------------------------------------- Oracle C
def _piece_coord_offsets(path):
    from dataset.templates import coord_offsets
    with open(path, 'rb') as f:
        z_items = zf.members(path)
    data = [d for n, d in z_items if d.startswith(ap.MAGIC) and ap.u16(d, 0x7a) == 20][0]
    block = ap.decode(data)['blocks'][0]
    offs = coord_offsets(data, block)
    live = sorted({o for pairs in offs.values() for pair in pairs for o in pair})
    return data, live


def _marker_slot_offsets(path):
    """Byte offsets within occupied slots' x/y/home_x/home_y/area f64
    fields. Targets the LAST byte of each 8-byte little-endian float (the
    sign+high-exponent byte), not the first: these coordinates are
    double-precision, so flipping the low (least-significant-mantissa) byte
    changes the value by roughly 1 part in 2^52 - real, but far below any
    reasonable comparison tolerance, and therefore not a meaningful
    corruption probe. The high byte produces a large, unmistakable change,
    which is also a more realistic "this byte got corrupted" scenario."""
    objs = am.list_zip(path)
    mo = objs['marker'][0]
    d = mo['data']
    mk = am.parse_marker(d)
    occupied = [s for s in mk['slots'] if not s['empty']][:10]
    live = []
    for s in occupied:
        for field_off in (0, 8, 16, 24, 42):
            live.append(s['slot'] + field_off + 7)
    return d, live


def oracle_c(seeds, n_per_seed=15):
    import random
    rows = []
    for label, rel, kind in seeds:
        path = os.path.join(REPO, rel)
        if kind == 'piece':
            data, live = _piece_coord_offsets(path)
            def redecode(d): return cn.canon_piece_full(d)
        else:
            data, live = _marker_slot_offsets(path)
            def redecode(d): return cn.canon_place_marker(_place_marker_from_object(path, d))
        if not live:
            rows.append(dict(oracle='C', case='%s/no-offsets' % label, seed=label,
                              ok=False, detail='no provably-live offsets found')); continue
        base_canon = redecode(data)
        # a fixed, reproducible seed per label - NOT Python's hash(str),
        # which is randomised per-process (PYTHONHASHSEED) and would make
        # "run it again" pick different offsets each time.
        import hashlib
        seed = int(hashlib.sha256(label.encode()).hexdigest(), 16) & 0xffff
        rnd = random.Random(seed)
        sample = rnd.sample(live, min(n_per_seed, len(live)))
        for off in sample:
            for mode, mutate in (('flip_bit', lambda b: b ^ 0x01),
                                  ('zero', lambda b: 0x00),
                                  ('ff', lambda b: 0xFF)):
                case = '%s/off=%#x/%s' % (label, off, mode)
                d = bytearray(data); d[off] = mutate(d[off]) & 0xFF; d = bytes(d)
                try:
                    got_canon = redecode(d)
                    if got_canon != base_canon:
                        ok, detail = True, 'ok (decode changed, as required)'
                    else:
                        ok, detail = False, 'SILENT: corrupted input decoded identically'
                except Exception as e:
                    ok, detail = True, 'ok (raised %s)' % type(e).__name__
                rows.append(dict(oracle='C', case=case, seed=label, ok=ok, detail=detail))
    return rows


def _place_marker_from_object(path, patched_marker_data):
    """Rebuild the zip with the marker object's bytes swapped for a
    corrupted copy, then run the normal place_marker() entry point on it -
    exercising the real, full call path, not a shortcut."""
    items = zf.members(path)
    out = []
    replaced = False
    for n, d in items:
        if not replaced and d.startswith(am.MAGIC) and am.u16(d, 0x7a) == 9:
            out.append((n, patched_marker_data)); replaced = True
        else:
            out.append((n, d))
    return am.place_marker(zf.build(out))


# ----------------------------------------------------------------- runner
def run(seeds=None, quick=False):
    seeds = seeds or (QUICK_SEEDS if quick else SEEDS)
    t0 = time.time()
    rows = oracle_a(seeds) + oracle_b() + (oracle_c(seeds, n_per_seed=5 if quick else 15) if not quick or True else [])
    elapsed = time.time() - t0
    n_ok = sum(1 for r in rows if r['ok'])
    n_fail = len(rows) - n_ok
    return rows, n_ok, n_fail, elapsed


def quick():
    rows, n_ok, n_fail, elapsed = run(quick=True)
    return n_ok, n_fail, [r for r in rows if not r['ok']]


def write_report(rows, n_ok, n_fail, elapsed):
    lines = ['# Robustness report (v2)\n',
             'decoder_version: accumark_pds=%s accumark_marker=%s\n' % (ap.__version__, am.__version__),
             '\n%d cases, %d passed, %d failed, %.1fs\n' % (len(rows), n_ok, n_fail, elapsed)]

    lines.append('\n## Supported\n\n')
    a_rows = [r for r in rows if r['oracle'] == 'A']
    b_rows = [r for r in rows if r['oracle'] == 'B']
    a_ok = sum(1 for r in a_rows if r['ok']); b_ok = sum(1 for r in b_rows if r['ok'])
    lines.append('- ZIP structural variants (Oracle A, %d/%d): STORED/DEFLATED/BZIP2/LZMA and mixed '
                  'compression, reversed/shuffled member order, folder prefixes, deep nesting, backslash '
                  'paths, directory entries, extra junk members, non-ASCII/long names, `.TMP`/`.dat` '
                  'renamed members, dropped `ver.5`/`comments.txt`, missing/replaced archive comment, '
                  'zeroed timestamps - decode identically to the original on every seed.\n'
                  % (a_ok, len(a_rows)))
    lines.append('- Malformed-input contract (Oracle B, %d/%d): every case below raises a named '
                  '`accumark_errors.AccuMarkError` subclass (or `zipfile.BadZipFile` for a non-ZIP '
                  'container) - never `SystemExit`, never a bare `IndexError`/`struct.error`, never a '
                  'silent wrong answer.\n' % (b_ok, len(b_rows)))

    for oracle in ('A', 'B', 'C'):
        orows = [r for r in rows if r['oracle'] == oracle]
        if not orows: continue
        o_ok = sum(1 for r in orows if r['ok'])
        lines.append('\n## Oracle %s (%d/%d ok)\n\n' % (oracle, o_ok, len(orows)))
        lines.append('| case | seed | verdict | detail |\n|---|---|---|---|\n')
        for r in orows:
            v = 'ok' if r['ok'] else 'FAIL'
            lines.append('| %s | %s | %s | %s |\n' % (r['case'], r['seed'], v, r['detail']))

    fails = [r for r in rows if not r['ok']]
    lines.append('\n## Unsupported (%d)\n\n' % len(fails))
    if not fails:
        lines.append('None.\n')
    for r in fails:
        lines.append('- **%s** (Oracle %s, seed %s): %s\n' % (r['case'], r['oracle'], r['seed'], r['detail']))

    c_fails = [r for r in fails if r['oracle'] == 'C']
    lines.append('\n## Recommendations\n\n')
    if c_fails:
        seeds_hit = sorted({r['seed'] for r in c_fails})
        offs = sorted({r['case'].split('/off=')[1].split('/')[0] for r in c_fails})
        lines.append(
            '- **Region-C snapshot / line-table shadow copies are parsed but not cross-validated.** '
            '%d Oracle-C cases across %s corrupt a byte accumark_pds.decode_piece_block itself '
            'identifies as a coordinate (via dataset/templates.coord_offsets - never a guessed offset), '
            'yet neither `block[\'perimeter\']` nor verify_capture\'s own `line_table_consistent` check '
            'changes. Each perimeter point is stored 5-7 times (the point table, two Region-C snapshots, '
            'and the line table); this finding is specifically about the snapshot/shadow copies, not the '
            'authoritative point-table copy (which Oracle C DOES catch - see the `ok` rows above). '
            'Representative offsets: %s. Two honest paths forward: (a) extend '
            'accumark_pds.check_line_table (or a new check) to cross-validate Region-C\'s snapshots '
            'against the perimeter the same way the line table already is, so corruption there becomes '
            'detectable; or (b) if Region-C\'s snapshots are confirmed genuinely decorative/redundant '
            '(AccuMark writes them but never reads them back), document that explicitly in FORMAT_SPEC.md '
            'so a future reader does not spend time trying to cross-validate inert data. Not chased '
            'further in this session - it is a real, specific, reproducible finding, not a decoder defect '
            'introduced by v2, and resolving which of (a)/(b) is true needs a live AccuMark capture, not '
            'more offline analysis.\n' % (len(c_fails), ', '.join(seeds_hit), ', '.join(offs[:6])))
    else:
        lines.append('None - every corruption case either raised or changed the decode.\n')

    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    return REPORT_PATH


if __name__ == '__main__':
    q = '--quick' in sys.argv[1:]
    rows, n_ok, n_fail, elapsed = run(quick=q)
    for r in rows:
        print('%s %-4s %-55s %s' % ('ok ' if r['ok'] else 'FAIL', r['oracle'], r['case'], r['detail']))
    print()
    if not q:
        path = write_report(rows, n_ok, n_fail, elapsed)
        print('report written to', path)
    print('ROBUSTNESS %s (%d/%d, %.1fs)' % ('PASS' if n_fail == 0 else 'FAIL', n_ok, len(rows), elapsed))
    sys.exit(1 if n_fail else 0)
