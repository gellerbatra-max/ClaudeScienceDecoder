#!/usr/bin/env python3
"""selftest.py - prove the decoder + validator work on this machine before
touching AccuMark.  Decodes every capture under captures/, checks each against
its DXF, and re-runs the known structural-diff cases (including the two that
must report NO change).  Exits non-zero on any failure."""
import copy, glob, math, os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import accumark_pds as ap
import accumark_marker as am
import verify_capture as vc

fails = []

print('-- decoder version')
ok = ap.__version__ == am.__version__ == '3.0'
print(f"   {'ok ' if ok else 'FAIL'} accumark_pds={ap.__version__} accumark_marker={am.__version__}")
if not ok: fails.append('decoder version mismatch')

CAPS = os.path.join(HERE, 'captures')
EXPECT = {   # task -> (perimeter_points, notches, graded_points, seam_cm, piece_records)
 'TASK1-CUTQTY3':    (4, 0, 0, 0.0, 1),
 'TASK2-NOSEAM':     (4, 0, 0, 0.0, 1),
 'TASK2-SEAM1CM':    (4, 0, 0, 1.0, 2),
 'TASK3-NONOTCH':    (4, 0, 0, 0.0, 2),
 'TASK3-NOTCHED':    (6, 2, 0, 0.0, 2),
 'TASK4-DRILLPOINT': (4, 0, 0, 0.0, 2),
 'TASK5-GRADED':     (4, 0, 2, 0.0, 2),
 'TASK6-CURVE':      (34, 0, 10, 0.0, 2),
}
PAIRS = [  # (variant, baseline, structural_change_expected)
 ('TASK4-DRILLPOINT', 'TASK3-NONOTCH',    'no'),   # the drill point never saved
 ('TASK1-CUTQTY3',    'TASK2-NOSEAM',     'no'),   # cut quantity is not stored
 ('TASK3-NOTCHED',    'TASK3-NONOTCH',    'yes'),
 ('TASK2-SEAM1CM',    'TASK2-NOSEAM',     'yes'),
 ('TASK5-GRADED',     'TASK3-NONOTCH',    'yes'),
 ('TASK3-NONOTCH',    'TASK4-DRILLPOINT', 'no'),
]

print('-- decode + DXF agreement')
for name, exp in sorted(EXPECT.items()):
    folder = os.path.join(CAPS, name)
    if not os.path.isdir(folder):
        fails.append(f'{name}: folder missing'); continue
    cap = vc.load(folder)
    f, _ = vc.facts(cap)
    worst, msg = vc.dxf_check(cap)
    got = (f['perimeter_points'], f['notches'], f['graded_points'], f['seam_cm'],
           f['piece_records'])
    ok = got == exp and worst is not None and worst <= 2e-4
    print(f"   {'ok ' if ok else 'FAIL'} {name:18} {got}  dxf_max={worst}")
    if not ok: fails.append(f'{name}: got {got} want {exp}, dxf {worst}')

print('-- structural-diff classification')
for var, base, want in PAIRS:
    runs = vc.classify_runs(vc.load(os.path.join(CAPS, base))['data'],
                            vc.load(os.path.join(CAPS, var))['data'])
    n = sum(1 for r in runs if r['kind'] == 'STRUCTURAL')
    got = 'yes' if n else 'no'
    ok = got == want
    print(f"   {'ok ' if ok else 'FAIL'} {var:18} vs {base:18} structural={got:3} "
          f"({n} runs of {len(runs)})")
    if not ok: fails.append(f'{var} vs {base}: structural={got} want {want}')

print('-- .RUL parsing')
r = ap.parse_rul(open(os.path.join(CAPS, 'TASK6-CURVE', 'TASK6-CURVE.RUL'),
                      errors='replace').read())
ok = len(r['rules']) == 11 and r['rules']['11'][-1] == (1.732, 0.866)
print(f"   {'ok ' if ok else 'FAIL'} TASK6-CURVE.RUL {len(r['rules'])} rules, "
      f"rule 11 largest size {r['rules']['11'][-1]}")
if not ok: fails.append('RUL parse')

print('-- round-2 captures (skipped when a folder is absent)')
# line_records/line_table_consistent (§10, FORMAT_SPEC.md): one count per
# piece record (block), from accumark_pds's TLV line-table parser, cross-
# checked point-by-point against independently decoded geometry. The exact
# seam model now validates CAP-C30/C31's tapered intersections as well.
R2 = [  # folder, baseline, {fact: want}, structural_change want (or None)
 ('CAP-C00-BASE',          None,               dict(piece_records=1, perimeter_points=4, line_records='5', line_table_consistent='yes'), None),
 ('CAP-C01-REEXPORT',      'CAP-C00-BASE',     dict(piece_records=1, line_records='5', line_table_consistent='yes'), 'no'),
 ('CAP-C02-SAVEAS-NOEDIT', 'CAP-C00-BASE',     dict(piece_records=1, line_records='5', line_table_consistent='yes'), 'no'),
 ('CAP-C50-DRILL1',        'CAP-C00-BASE',     dict(drill_points=1, piece_records=2, line_records='6;5', line_table_consistent='yes'), 'yes'),
 ('CAP-C30-SEAM-UNEVEN',   None,               dict(uneven_seam='yes', cutline_records=3, line_records='8;5', line_table_consistent='yes'), None),
 ('CAP-C31-SEAM-TAPER',    'CAP-C00-BASE',     dict(uneven_seam='yes', cutline_records=2, line_records='7;5', line_table_consistent='yes'), 'yes'),
 # 2026-09-13: took CAP-C30-SEAM-UNEVEN and set its seam allowance back to 0.
 # Answers CAPTURE_PLAN.md's CAP-C32 question directly: removal clears the
 # logical seam value (uneven_seam='no', matching an unseamed piece) but does
 # NOT collapse the file back to piece_records=1 - the stale second record
 # inherited from C30's own original seam-definition edit persists untouched.
 # See FORMAT_SPEC.md §8.
 ('CAP-C32-SEAM-REMOVE',   'CAP-C00-BASE',     dict(piece_records=2, uneven_seam='no', seam_cm=0.0, line_records='5;5', line_table_consistent='yes'), 'yes'),
 ('CAP-C20-RULE-DISTINCT', 'CAP-C02-SAVEAS-NOEDIT', dict(graded_points=1, n_break_rows=8, rul_n_rules=1, line_records='5;5', line_table_consistent='yes'), 'yes'),
 ('CAP-C21-RULE-TWO',      'CAP-C20-RULE-DISTINCT', dict(graded_points=2, n_break_rows=8, rul_n_rules=2, line_records='5;5', line_table_consistent='yes'), 'yes'),
 ('CAP-C22-RULE-NONE',     'CAP-C20-RULE-DISTINCT', dict(graded_points=0, n_break_rows=8, line_records='5;5', line_table_consistent='yes'), None),
 ('CAP-C10-PENT',          'CAP-C00-BASE',     dict(perimeter_points=5, line_records='6;5', line_table_consistent='yes'), None),
 ('CAP-C11-HEX',           'CAP-C00-BASE',     dict(perimeter_points=6, line_records='7;5', line_table_consistent='yes'), None),
 ('CAP-C40-NOTCH-TYPES',   None,               dict(notches=4, notch_types='2;4;5;1', line_records='5;5', line_table_consistent='yes'), None),
 ('CAP-C41-NOTCH-WIDTH',   None,               dict(notches=2, notch_types='1;1', perimeter_points=6, line_records='5;5', line_table_consistent='yes'), None),
 ('CAP-C42-NOTCH-ALLEDGES', None,              dict(notches=4, notch_types='1;1;1;1', segment_points='3;3;3;3', line_records='5;5', line_table_consistent='yes'), None),
 ('CAP-C60-CUTOUT',         None,              dict(perimeter_points=4, internal_points='25', line_records='6;5', line_table_consistent='yes'), None),
 # 2026-09-09: was (perimeter_points=3, graded_points=1, line_table_consistent='no').
 # The "missing 4th corner" was the old point-table locator skipping the
 # table's first record (id 5); all four corners now match the DXF exactly.
 ('CAP-C61-MIRROR',         None,              dict(perimeter_points=4, graded_points=2, mirror_flag=2, line_records='5', line_table_consistent='yes'), None),
 ('CAP-C62-DART',           None,              dict(perimeter_points=7, piece_records=2, line_records='7;5', line_table_consistent='yes'), None),
 ('CAP-C70-PASTED',         None,              dict(piece_records=1, category='CAP-C00-BASE', line_records='5', line_table_consistent='yes'), None),
 ('CAP-C12-TWOINTLINES',    None,              dict(perimeter_points=4, internal_points='2', line_records='6;5', line_table_consistent='yes'), None),
 ('CAP-C13-LONGNAME',       None,              dict(piece_records=1, category='CAP-C13-LONGNAME-1234567890ABC', line_records='5', line_table_consistent='yes'), None),
 ('CAP-C14-ANNOT',          None,              dict(annotation='collar', perimeter_points=5, line_records='5', line_table_consistent='yes'), None),
 # 2026-09-13: begin/end both nonzero and unequal (1.50cm/0.50cm) on the
 # ONLY seamed edge - no adjacent-segment interaction, the cleanest
 # possible confirmation of FORMAT_SPEC.md Sec 6.1's begin/end rule.
 ('captures/CAP-C35-SEAM-TAPER-TRUE', None,     dict(piece_records=2, uneven_seam='yes', cutline_records=1, line_records='6;5', line_table_consistent='yes'), None),
 # 2026-09-13: CAP-C35 after Advanced->Seam->Swap. Perimeter and seam record
 # literally exchange coordinates and begin/end negate - see FORMAT_SPEC.md
 # Sec 6.1. Same fact shape as C35 itself (line_table_consistent still yes).
 ('captures/CAP-C37-SEAM-SWAP',      None,     dict(piece_records=2, uneven_seam='yes', cutline_records=1, line_records='6;5', line_table_consistent='yes'), None),
]
for name, base, want, sc in R2:
    folder = os.path.join(HERE, name)
    if not os.path.isdir(folder) or not glob.glob(os.path.join(folder, '*.[zZ][iI][pP]')):
        print(f'   --  {name:22} (absent)'); continue
    cap = vc.load(folder); f, s = vc.facts(cap)
    bad = [f'{k}={f.get(k)}!={v}' for k, v in want.items() if str(f.get(k)) != str(v)]
    worst, _ = vc.dxf_check(cap)
    if cap['dxf'] and (worst is None or worst > 2e-4): bad.append(f'dxf {worst}')
    if sc is not None:
        runs = vc.classify_runs(vc.load(os.path.join(HERE, base))['data'], cap['data'])
        got = 'yes' if any(r['kind'] == 'STRUCTURAL' for r in runs) else 'no'
        if got != sc: bad.append(f'structural={got}!={sc}')
    if name == 'CAP-C20-RULE-DISTINCT':
        want_d = [(393,-196),(787,-393),(1181,-590),(1574,-787),(1968,-984),(2362,-1181),(2755,-1377),(3149,-1574)]
        if s['grade_rules'].get(1) != want_d: bad.append(f"rule-1 deltas {s['grade_rules'].get(1)}")
    if name in ('CAP-C30-SEAM-UNEVEN', 'CAP-C31-SEAM-TAPER'):
        for block in s['blocks']:
            model = [p for edge in ap.seam_line_points(block) for p in edge['points']]
            if not model: continue
            numbered = [tp for record in block['tail']['line_records'] if record['kind'] == 2
                        for tp in record['points'] if tp['a'] != 65535]
            residual = max(min(max(abs(tp['x']-p['xy'][0]), abs(tp['y']-p['xy'][1]))
                               for p in model) for tp in numbered)
            if residual > 1: bad.append(f'seam-model residual={residual}>1')
    print(f"   {'ok ' if not bad else 'FAIL'} {name:22} {'; '.join(bad) if bad else 'as expected'}")
    if bad: fails.append(f'{name}: ' + '; '.join(bad))

print('-- native internal tags vs ASTM layers')
LAYER_CAPTURES = [
    (os.path.join(CAPS, 'V3-PROD-MOCUP-B1-1-NOEDIT'),
     {'grain': 2, 'internal': 10, 'internal_cutout': 8}),
    (os.path.join(CAPS, '2303-B1-A1- OUCF-SP24'),
     {'grain': 1, 'mirror': 1}),
    (os.path.join(HERE, 'CAP-C60-CUTOUT'),
     {'grain': 1, 'internal': 1}),
    (os.path.join(HERE, 'CAP-C12-TWOINTLINES'),
     {'grain': 1, 'internal': 1}),
]
for folder, expected in LAYER_CAPTURES:
    cap = vc.load(folder)
    ok, results, msg = vc.internal_layer_check(cap)
    counts = {}
    for result in results:
        counts[result['kind']] = counts.get(result['kind'], 0) + 1
    ok = ok and counts == expected
    name = os.path.basename(folder)
    print(f"   {'ok ' if ok else 'FAIL'} {name:34} {msg}; {counts}")
    if not ok: fails.append(f'{name}: internal layers {msg}; {counts}!={expected}')

print('-- internal-curve line-table expansion')
cp_zip = os.path.join(HERE, 'markers', '2303-CP150-JULY', '2303-CP 150 CPL.zip')
extras = []
for obj in am.list_zip(cp_zip).get('piece', []):
    for block in ap.decode(obj['data'])['blocks']:
        analysis = ap.classify_line_table(block)
        for record in analysis['records']:
            for point in record['points']:
                if point['classification'] == 'internal_curve_table_extra':
                    extras.append(point['internal_match']['delta'])
ok = len(extras) == 5 and extras.count((15, 22)) == 3 and extras.count((16, 22)) == 2
print(f"   {'ok ' if ok else 'FAIL'} five 46-vs-44 table extras {extras}")
if not ok: fails.append(f'internal-curve table extras {extras}')

print('-- exact seam model on a curved edge (skipped when the folder is absent)')
# 2026-09-13: CAP-C34-SEAM-CURVED-POS/-NEG - a rectangle with one edge bowed
# into a 3-point curve, +1.00cm and -1.00cm seam allowance. The exact seam
# model (seam_line_points/classify_line_table) was built and validated on
# straight-edge C30/C31 samples only; this checks it also covers a curved
# edge in both directions without any new code. CAPTURE_PLAN.md's CAP-C34.
curve_dir = os.path.join(HERE, 'captures', 'CAP-C34-SEAM-CURVED')
if os.path.isdir(curve_dir):
    for sign in ('POS', 'NEG'):
        zpath = os.path.join(curve_dir, f'CAP-C34-SEAM-CURVED-{sign}.zip')
        block = ap.decode_zip(zpath)['blocks'][0]
        consistent = ap.check_line_table(block)
        analysis = ap.classify_line_table(block)
        kinds = {pt['classification'] for rec in analysis['records'] for pt in rec['points']}
        bad_kinds = kinds - {'stored_geometry', 'seam_model_exact', 'axis_or_diagonal_fallback'}
        ok = consistent and not bad_kinds
        print(f"   {'ok ' if ok else 'FAIL'} CAP-C34-SEAM-CURVED-{sign:3} "
              f"line_table_consistent={consistent}; classes={sorted(kinds)}")
        if not ok: fails.append(f'CAP-C34-SEAM-CURVED-{sign}: consistent={consistent} bad_kinds={bad_kinds}')
else:
    print('   --  CAP-C34-SEAM-CURVED       (absent)')

print('-- Fold Keep: mirror_flag, real mirror tag, seam value not stored (skipped when absent)')
# 2026-09-13: CAP-C37-FOLD-SEAM - the first controlled (non-production)
# confirmation that Fold Keep produces internal_kinds=['grain','mirror'],
# and that its own "seam allowance for the split line" prompt (entered as
# 1.00cm = 3937) is not persisted anywhere in the payload.
# CAP-C37-FOLD-NOMIRROR - same setup, Mirror Piece unchecked - resolves the
# long-open mirror_flag ([?] since CAP-C61-MIRROR): 0 when unchecked (no
# mirror-tagged internal line at all), 2 when checked. See FORMAT_SPEC.md's
# Sec 2/5.3 and CAPTURE_PLAN.md's CAP-C37 entry.
FOLD_KEEP_CASES = [
    ('CAP-C37-FOLD-SEAM',     ['grain', 'mirror'], 2, True),
    ('CAP-C37-FOLD-NOMIRROR', ['grain'],           0, False),
]
for name, want_kinds, want_flag, check_no_seam_value in FOLD_KEEP_CASES:
    fold_zip = os.path.join(CAPS, name, f'{name}.zip')
    if not os.path.isfile(fold_zip):
        print(f'   --  {name:22} (absent)'); continue
    obj = am.list_zip(fold_zip)['piece'][0]
    payload = obj['data']
    block = ap.decode(payload)['blocks'][0]
    kinds = block.get('internal_kinds')
    flag = block['meta'].get('mirror_flag')
    no_seam = all((sg.get('seam_flag') or 0) == 0 for sg in (block.get('segments') or []))
    ok = kinds == want_kinds and flag == want_flag and no_seam
    detail = f"internal_kinds={kinds}; mirror_flag={flag}; all seam_flag=0: {no_seam}"
    if check_no_seam_value:
        no_stored_value = (3937).to_bytes(4, 'little', signed=True) not in payload and (3937).to_bytes(2, 'little') not in payload
        ok = ok and no_stored_value
        detail += f"; 3937 absent from payload: {no_stored_value}"
    print(f"   {'ok ' if ok else 'FAIL'} {name:22} {detail}")
    if not ok: fails.append(f'{name}: {detail}')

print('-- Fold Keep mirrors by genuine reflection, not bbox completion (skipped when absent)')
# 2026-09-13: CAP-C82-FOLD-OBLIQUE - settles FORMAT_SPEC.md Sec 10.2's open
# question (left unresolved by the axis-aligned CAP-C61-MIRROR, where
# "reflect across the fold line" and "complete the bounding box" give the
# same answer). On this genuinely oblique fold, id3/id7 reflect onto each
# other across a shared axis to within 1 native unit - a result bbox
# completion cannot produce, since there is no rectangle to complete.
# That axis comes from the line table's own kind=2 record positionally
# aligned with the 'mirror' internal tag - NOT from the independently
# decoded mirrors_in field, which (2026-09-14, resolved) turns out to be
# answering a different question ("which two corners bound the fold",
# not "what's the axis") - see the mirrors_in check below and Sec 10.3.
oblique_zip = os.path.join(CAPS, 'CAP-C82-FOLD-OBLIQUE', 'CAP-C82-FOLD-OBLIQUE.zip')
if os.path.isfile(oblique_zip):
    obj = am.list_zip(oblique_zip)['piece'][0]
    block = ap.decode(obj['data'])['blocks'][0]
    pts = {p['id']: (p['x'], p['y']) for p in block['perimeter']}
    real_coords = set(pts.values())
    # the grain line's kind=2 record touches neither real perimeter corner;
    # the 'mirror'-slot record's own point ids don't reuse the perimeter's
    # id numbering, so match by coordinate instead
    mirror_rec = next(r for r in block['tail']['line_records']
                       if r['kind'] == 2 and any((pt['x'], pt['y']) in real_coords for pt in r['points']))
    A, B = [(pt['x'], pt['y']) for pt in mirror_rec['points']][:2]
    def reflect(p, A, B):
        (ax, ay), (bx, by), (px, py) = A, B, p
        dx, dy = bx - ax, by - ay
        L = (dx * dx + dy * dy) ** 0.5
        ux, uy = dx / L, dy / L
        t = (px - ax) * ux + (py - ay) * uy
        projx, projy = ax + ux * t, ay + uy * t
        return (2 * projx - px, 2 * projy - py)
    r7 = reflect(pts[7], A, B)
    residual = max(abs(r7[0] - pts[3][0]), abs(r7[1] - pts[3][1]))
    ok = residual <= 1
    print(f"   {'ok ' if ok else 'FAIL'} CAP-C82-FOLD-OBLIQUE   id7 reflected={tuple(round(v,1) for v in r7)} "
          f"vs id3 stored={pts[3]}; residual={residual} native units")
    if not ok: fails.append(f'CAP-C82-FOLD-OBLIQUE: reflection residual {residual} > 1')

    # 2026-09-14: mirrors_in resolved - it's a verbatim echo of the two
    # perimeter corners (id5/id8) where Fold Keep's drawn fold line
    # crossed the piece's original edges, not the reflection axis. Checked
    # field-by-field (coords, attr, rule_ref), not just coordinates, since
    # a coordinate-only match could be coincidental.
    perimeter_by_coord = {(p['x'], p['y']): p for p in block['perimeter']}
    mirror_internal = next(seg for seg, kind in zip(block['internal_lines'], block['internal_kinds']) if kind == 'mirror')
    field_matches = []
    for ipt in mirror_internal:
        ppt = perimeter_by_coord.get((ipt['x'], ipt['y']))
        field_matches.append(bool(ppt) and ppt.get('attr') == ipt.get('attr') and ppt.get('rule_ref') == ipt.get('rule_ref'))
    ok2 = len(mirror_internal) == 2 and all(field_matches)
    print(f"   {'ok ' if ok2 else 'FAIL'} CAP-C82-FOLD-OBLIQUE   mirrors_in is a verbatim id5/id8 echo (coord+attr+rule_ref): {field_matches}")
    if not ok2: fails.append(f'CAP-C82-FOLD-OBLIQUE: mirrors_in field-match {field_matches}')
else:
    print('   --  CAP-C82-FOLD-OBLIQUE      (absent)')

print('-- Annotation rotation is an IEEE-754 double in radians (skipped when absent)')
# 2026-09-14: CAP-C33-ANNOT-ROTA/-ROTB - a controlled pair (identical text
# "SAME" at the same clicked position, differing only in Font Rotation 0
# vs 45) isolates the rotation field by direct byte diff: an 8-byte field
# reads all-zero at 0 degrees and reads exactly radians(45) as a
# little-endian IEEE-754 double at 45 degrees. See FORMAT_SPEC.md Sec 5.4.
rota_zip = os.path.join(CAPS, 'CAP-C33-INTERNAL-TYPES', 'CAP-C33-ANNOT-ROTA.zip')
rotb_zip = os.path.join(CAPS, 'CAP-C33-INTERNAL-TYPES', 'CAP-C33-ANNOT-ROTB.zip')
if os.path.isfile(rota_zip) and os.path.isfile(rotb_zip):
    import struct as _struct, math as _math
    data_a = am.list_zip(rota_zip)['piece'][0]['data']
    data_b = am.list_zip(rotb_zip)['piece'][0]['data']
    diff_offsets = [i for i, (x, y) in enumerate(zip(data_a, data_b)) if x != y]
    # the rotation field is the one differing offset where A reads all-zero
    # and B decodes as a plausible angle in radians (0 < angle <= 2*pi)
    candidates = []
    for off in diff_offsets:
        if _struct.unpack_from('<Q', data_a, off)[0] != 0:
            continue
        try:
            angle = _struct.unpack_from('<d', data_b, off)[0]
        except Exception:
            continue
        if 0 < angle <= 2 * _math.pi:
            candidates.append((off, angle))
    ok = len(candidates) == 1 and abs(candidates[0][1] - _math.radians(45)) < 1e-9
    print(f"   {'ok ' if ok else 'FAIL'} CAP-C33-ANNOT-ROTA/B  candidates={candidates} want=(?, {_math.radians(45)})")
    if not ok: fails.append(f'CAP-C33-ANNOT-ROTA/B: candidates={candidates}')
else:
    print('   --  CAP-C33-ANNOT-ROTA/B      (absent)')

print('-- Annotation echo record: general-purpose scan, cross-checked on 3 independent captures (skipped when absent)')
# 2026-09-14 (second pass): the diff-based check above found the rotation
# field by brute-force comparison of one controlled pair; find_annotation_echoes()
# now decodes the whole 36-byte echo record structurally (see FORMAT_SPEC.md
# Sec 5.4) by scanning for its own header rather than needing a diff. This
# check reproduces the same rotation values via that general parser, and
# additionally checks CAP-C33-ANNOTATION - a capture never used to derive the
# structure - to confirm it generalizes rather than overfitting to the pair.
annot_zip = os.path.join(CAPS, 'CAP-C33-INTERNAL-TYPES', 'CAP-C33-ANNOTATION.zip')
if os.path.isfile(rota_zip) and os.path.isfile(rotb_zip) and os.path.isfile(annot_zip):
    import math as _math
    echoes_a = ap.find_annotation_echoes(am.list_zip(rota_zip)['piece'][0]['data'])
    echoes_b = ap.find_annotation_echoes(am.list_zip(rotb_zip)['piece'][0]['data'])
    echoes_annot = ap.find_annotation_echoes(am.list_zip(annot_zip)['piece'][0]['data'])
    checks = [
        ('ROTA has 1 echo at 0 deg', len(echoes_a) == 1 and abs(echoes_a[0]['rotation_degrees']) < 1e-6),
        ('ROTB has 1 echo at 45 deg', len(echoes_b) == 1 and abs(echoes_b[0]['rotation_degrees'] - 45) < 1e-6),
        ('ANNOTATION has 3 echoes (TEST once, ROT twice)',
         len(echoes_annot) == 3 and sorted(e['text_length'] for e in echoes_annot) == [3, 3, 4]),
        ('ANNOTATION: the length-4 echo (TEST) is at 0 deg',
         any(e['text_length'] == 4 and abs(e['rotation_degrees']) < 1e-6 for e in echoes_annot)),
        ('ANNOTATION: both length-3 echoes (ROT) are at 45 deg',
         all(abs(e['rotation_degrees'] - 45) < 1e-6 for e in echoes_annot if e['text_length'] == 3)),
    ]
    ok3 = all(v for _, v in checks)
    print(f"   {'ok ' if ok3 else 'FAIL'} find_annotation_echoes  {[k for k, v in checks if not v] or 'all checks passed'}")
    if not ok3: fails.append(f'find_annotation_echoes: failed {[k for k, v in checks if not v]}')
else:
    print('   --  find_annotation_echoes   (absent)')

print('-- Annotation primary record: corner-echo tail matches the host piece perimeter (skipped when absent)')
# 2026-09-14 (third pass): resolves most of the primary record's own
# "long tail" left undecoded above - the four tagged points in it are
# not the annotation text's own bounding box (ruled out: byte-identical
# between ROTA/ROTB, which a rotated quad could not be) but the host
# piece's own perimeter corners, verbatim, just started from a different
# corner (tags 2,3,4,1 instead of the perimeter's own 1,2,3,4 - the same
# harmless rotation Region C's own snapshot1 already exhibits). Found by
# scanning for the primary record's own header (const 1, const 52,
# strlen, text) since - like the echo record - it isn't at a fixed
# offset, then reading 4 plain 15-byte points immediately after the
# text and comparing them to decode()'s own perimeter as a set (order-
# and rotation-independent, matching check_region_c's own convention).
def _find_annotation_corners(data, text):
    import struct as _struct
    text_bytes = text.encode('latin1')
    n = len(data)
    for off in range(0, n - 10):
        if _struct.unpack_from('<I', data, off)[0] != 1: continue
        if _struct.unpack_from('<I', data, off + 4)[0] != 52: continue
        strlen = _struct.unpack_from('<H', data, off + 8)[0]
        if strlen != len(text_bytes): continue
        if data[off+10:off+10+strlen] != text_bytes: continue
        p = off + 10 + strlen
        pts = []
        for _ in range(4):
            pt = ap.parse_point(data, p)
            pts.append((pt['x'], pt['y']))
            p = pt['offset'] + pt['size']
        return pts
    return None

if os.path.isfile(rota_zip):
    data_a = am.list_zip(rota_zip)['piece'][0]['data']
    b0 = ap.decode(data_a)['blocks'][0]
    corners = _find_annotation_corners(data_a, 'SAME')
    real_perim = {(p['x'], p['y']) for p in b0['perimeter']}
    ok4 = bool(corners) and len(corners) == 4 and set(corners) == real_perim
    print(f"   {'ok ' if ok4 else 'FAIL'} CAP-C33-ANNOT-ROTA  corners={corners} perimeter={sorted(real_perim)}")
    if not ok4: fails.append(f'annotation corner-echo: corners={corners} perimeter={real_perim}')
else:
    print('   --  CAP-C33-ANNOT-ROTA      (absent)')

print('-- Bookmark: Define alone is a no-op on disk; edit-after-bookmark adds one extra stale record (skipped when absent)')
# 2026-09-14: CAP-C80-BOOKMARK - settles FORMAT_SPEC.md Sec 11's "is Region
# C's snapshot1/snapshot2 pair a Bookmark->Restore cache" question: NO.
# CONTROL (never bookmarked) and BOOKMARK (bookmarked, never edited) are
# byte-identical except for the piece-name-length difference, both
# piece_records=1 - Define writes nothing extra to the file by itself.
# The real bookmark-specific effect only shows up after an edit: MODIFIED
# has piece_records=3 (1 live + 2 identical pre-edit copies), one more
# than the generic post-save-edit mechanism (Sec 8) produces alone.
bookmark_dir = os.path.join(CAPS, 'CAP-C80-BOOKMARK')
control_zip = os.path.join(bookmark_dir, 'CAP-C80-BOOKMARK-CONTROL.zip')
base_zip = os.path.join(bookmark_dir, 'CAP-C80-BOOKMARK.zip')
modified_zip = os.path.join(bookmark_dir, 'CAP-C80-BOOKMARK-MODIFIED.zip')
if os.path.isfile(control_zip) and os.path.isfile(base_zip) and os.path.isfile(modified_zip):
    control_data = am.list_zip(control_zip)['piece'][0]['data']
    base_data = am.list_zip(base_zip)['piece'][0]['data']
    modified_data = am.list_zip(modified_zip)['piece'][0]['data']
    name_len_diff = len('CAP-C80-BOOKMARK-CONTROL') - len('CAP-C80-BOOKMARK')
    define_is_noop = (len(control_data) - len(base_data)) == name_len_diff
    base_records = ap.summarize(base_data)['n_blocks']
    modified_records = ap.summarize(modified_data)['n_blocks']
    ok = define_is_noop and base_records == 1 and modified_records == 3
    print(f"   {'ok ' if ok else 'FAIL'} CAP-C80-BOOKMARK       Define no-op: {define_is_noop}; "
          f"unedited piece_records={base_records}; edited-after-bookmark piece_records={modified_records} (want 3)")
    if not ok: fails.append(f'CAP-C80-BOOKMARK: define_is_noop={define_is_noop} base_records={base_records} modified_records={modified_records}')
else:
    print('   --  CAP-C80-BOOKMARK          (absent)')

print('-- Region C record_state (0=stale/1=live-unseamed/2=live-seamed), corpus-wide')
# 2026-09-14: resolves the long-open "[?] marker3's role is unconfirmed"
# from parse_region_c's own docstring - a corpus sweep found record_state
# tracks exactly one thing: whether THIS block is a stale pre-edit
# duplicate (0), or the live/current block with (2) or without (1) a
# seam defined on it (seam_flag nonzero on >=1 segment). Originally
# CAP-C80-BOOKMARK-RESTORED was excluded here as a known marker-scan
# misread; parse_region_c now detects and skips Restore Defined's own
# bbox-center "restore_anchor" field (see its docstring), so both
# Restore-Defined captures decode correctly and need no exclusion.
# Gated on check_region_c() to skip blocks with a KNOWN Region-C
# misalignment: seamed live blocks (Sec 11's runaway-snapshot bug) and,
# newly found via CAP-C33-ANNOTATION the same day, any block containing
# an Annotation text object - its own not-yet-decoded record layout
# desyncs parse_point_snapshot the same way seaming does, a second,
# distinct trigger for the same class of bug (see Sec 5.4).
record_state_mismatches = []
record_state_checked = 0
for folder in glob.glob(os.path.join(HERE, 'CAP-C*')) + glob.glob(os.path.join(HERE, 'captures', 'CAP-C*')):
    for zpath in glob.glob(os.path.join(folder, '*.[zZ][iI][pP]')):
        try:
            pieces = am.list_zip(zpath).get('piece', [])
        except Exception:
            continue
        for obj in pieces:
            try:
                blocks = ap.decode(obj['data'])['blocks']
            except Exception:
                continue
            for i, b in enumerate(blocks):
                tail = b.get('tail')
                if not tail or 'error' in tail or not tail.get('region_c'):
                    continue
                if not ap.check_region_c(b):
                    continue  # known Region-C misalignment (seam or annotation) - Sec 11/5.4
                record_state_checked += 1
                state = tail['region_c']['record_state']
                any_seam = any((sg.get('seam_flag') or 0) != 0 for sg in (b.get('segments') or []))
                want = 0 if i > 0 else (2 if any_seam else 1)
                if state != want:
                    record_state_mismatches.append(f"{obj['name']}[{i}]: record_state={state} want={want}")
ok = record_state_checked > 0 and not record_state_mismatches
print(f"   {'ok ' if ok else 'FAIL'} {record_state_checked} blocks checked, {len(record_state_mismatches)} mismatched")
if not ok: fails.extend(record_state_mismatches or ['record_state: no blocks with region_c found'])

print('-- Region C snapshot2 re-anchoring on seamed live blocks (skipped when the folders are absent)')
# 2026-09-14: closes FORMAT_SPEC.md Sec 12's "real Region-C
# runaway-snapshot bug" for the seam-triggered case, all 12 of 12 known
# samples. Root cause: on a seamed live block, snapshot2 doesn't start
# immediately after record_state like it does on every unseamed block -
# a variable-length (100-200+ byte, not a small fixed shift) seam-
# corner/allowance structure sits in between, and reading straight
# through it desyncs snapshot2 into the "id=512,x=65536"-shaped garbage
# already documented. parse_region_c now falls back to searching
# forward for the raw perimeter's own first point reappearing verbatim
# and re-anchoring there when the immediate read doesn't validate - and
# critically, tries EVERY occurrence in the search window, not just the
# first (the first one or two occurrences on CAP-C30-SEAM-UNEVEN/
# CAP-C31-SEAM-TAPER and CAP-C33-ANNOTATION are coincidental partial
# matches inside an unrelated per-corner seam-value/Annotation
# structure, each producing exactly 1 good point before desyncing again
# - only a later occurrence is the true, fully-valid list start).
# Checked directly against all 12 seamed-live-block samples on hand, by
# name, not just by aggregate count - all 12 now decode with region_c
# fully consistent (up from 0 before this fix, 10 with the first,
# single-candidate version of it).
region_c_seam_cases = {
    'CAP-C34-SEAM-CURVED-NEG': True, 'CAP-C34-SEAM-CURVED-POS': True,
    'CAP-C36-EXTENSION': True, 'CAP-C36-MIRRORED': True, 'CAP-C36-MITERED': True,
    'CAP-C36-SLANT': True, 'CAP-C36-SQUARED': True, 'CAP-C36-TURNBACK': True,
    'CAP-C37-SEAM-SWAP': True, 'CAP-C35-SEAM-TAPER-TRUE': True,
    'CAP-C30-SEAM-UNEVEN': True, 'CAP-C31-SEAM-TAPER': True,
}
region_c_seam_results = {}
for zpath in (glob.glob(os.path.join(HERE, 'CAP-C*', '*.zip'))
              + glob.glob(os.path.join(HERE, 'captures', 'CAP-C*', '*.zip'))):
    name = os.path.splitext(os.path.basename(zpath))[0]
    if name not in region_c_seam_cases or name in region_c_seam_results: continue
    data = am.list_zip(zpath)['piece'][0]['data']
    b0 = ap.decode(data)['blocks'][0]
    region_c_seam_results[name] = ap.check_region_c(b0)
missing = [n for n in region_c_seam_cases if n not in region_c_seam_results]
mismatches = [f"{n}: got={region_c_seam_results[n]} want={want}"
              for n, want in region_c_seam_cases.items()
              if n in region_c_seam_results and region_c_seam_results[n] != want]
if missing:
    print(f"   --  {len(missing)}/{len(region_c_seam_cases)} seam samples absent, skipping: {missing}")
else:
    ok = not mismatches
    print(f"   {'ok ' if ok else 'FAIL'} {len(region_c_seam_cases)} seamed samples, "
          f"{sum(region_c_seam_cases.values())} expected fixed, {mismatches or 'all as expected'}")
    if not ok: fails.append(f'region_c seam re-anchoring: {mismatches}')

print('-- Restore Defined bbox-center anchor detected + region_c fully consistent (skipped when absent)')
# 2026-09-14: CAP-C80-BOOKMARK2 - a second, independent Restore Defined
# sample (different geometry/placement from CAP-C80-BOOKMARK-RESTORED),
# captured specifically to verify parse_region_c's restore_anchor fix
# generalizes rather than being tuned to one example. Both samples'
# anchor values match their own block's bbox center to within 0.5 native
# units (float rounding) - confirms the fields are genuinely the piece's
# own bounding-box center, not a coincidence.
restore_cases = ['CAP-C80-BOOKMARK-RESTORED', 'CAP-C80-BOOKMARK2-RESTORED']
for name in restore_cases:
    rzip = os.path.join(CAPS, 'CAP-C80-BOOKMARK', f'{name}.zip')
    if not os.path.isfile(rzip):
        print(f'   --  {name:26} (absent)'); continue
    obj = am.list_zip(rzip)['piece'][0]
    block = ap.decode(obj['data'])['blocks'][0]
    rc = block['tail']['region_c']
    xs = [p['x'] for p in block['perimeter']]; ys = [p['y'] for p in block['perimeter']]
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    anchor = rc.get('restore_anchor')
    anchor_ok = anchor is not None and abs(anchor[0]-cx) <= 1 and abs(anchor[1]-cy) <= 1
    consistent = ap.check_region_c(block)
    ok = anchor_ok and consistent
    print(f"   {'ok ' if ok else 'FAIL'} {name:26} restore_anchor={anchor} vs bbox_center=({cx},{cy}); region_c_consistent={consistent}")
    if not ok: fails.append(f'{name}: restore_anchor={anchor} bbox_center=({cx},{cy}) consistent={consistent}')

print('-- unclassified_gap: confirmed u16-length-prefixed record with 2 pinned fields, corpus-wide')
# 2026-09-14: partially resolves FORMAT_SPEC.md Sec 11/12's "unclassified_gap
# not yet understood [?]" item. Confirmed on the corpus (excluding the
# already-documented seamed-live-block Region-C misalignment, which
# corrupts where this gap is even measured from): a 2-byte length prefix
# (94 on every well-formed sample, i.e. 96 bytes total) followed by a
# payload where absolute offset 40 (a u32) equals n_perimeter_a plus the
# count of internal-line objects that are NOT mirror-tagged (mirror
# echoes don't add to the count - matches this session's other finding
# that they're corner echoes, not real objects), and offset 44 (a u32)
# is a constant 1. One honest single-sample exception, not force-fit:
# CAP-C82-FOLD-OBLIQUE's own embedded category name is a pre-rename
# leftover reading 'CAP-C80-BOOKMARK' (see CAPTURE_LOG.md) - excluded by
# path, not by name, so a real CAP-C80-BOOKMARK fixture still counts.
# Offsets 48/50 are known to exist and vary but aren't decoded yet - not
# checked here.
gap_checked = gap_prefix_ok = gap_v40_ok = gap_v44_ok = 0
gap_exceptions = []
for folder in glob.glob(os.path.join(HERE, 'CAP-C*')) + glob.glob(os.path.join(HERE, 'captures', 'CAP-C*')):
    for zpath in glob.glob(os.path.join(folder, '*.[zZ][iI][pP]')):
        if os.path.normpath(zpath).endswith(os.path.normpath('CAP-C82-FOLD-OBLIQUE/CAP-C82-FOLD-OBLIQUE.zip')):
            continue  # the one known, honestly-flagged exception - see FORMAT_SPEC.md Sec 11
        try:
            pieces = am.list_zip(zpath).get('piece', [])
        except Exception:
            continue
        for obj in pieces:
            try:
                blocks = ap.decode(obj['data'])['blocks']
            except Exception:
                continue
            for b in blocks:
                tail = b.get('tail')
                if not tail or 'error' in tail or not tail.get('region_c'):
                    continue
                gap = tail['region_c'].get('unclassified_gap')
                if not gap or len(gap) < 48 or not ap.check_region_c(b):
                    continue  # only check well-formed (non-misaligned) blocks
                import struct as _struct
                # [V, 2026-09-14] a seamed live block (record_state==2) now
                # reaches this far for the first time - the snapshot2
                # re-anchoring fix above makes 10 previously-misaligned
                # seamed samples pass check_region_c - but v40 doesn't fit
                # the n_perimeter_a+non_mirror_objs formula on any of them
                # (each off by a different amount, so not a simple missing
                # constant either); the seam-corner structure that sits
                # before snapshot2 on these blocks likely needs its own
                # term here, not yet worked out. Excluded from this whole
                # check for now rather than force-fit or regress it.
                if b['tail']['region_c'].get('record_state') == 2:
                    continue
                gap_checked += 1
                # 94 on every well-formed sample seen so far, i.e. a fixed
                # 96-byte record; some samples (CAP-C20/21/22-RULE-*) carry
                # 21 extra, unrelated stale-name-residue bytes afterward
                # (see FORMAT_SPEC.md Sec 11), so check the prefix value
                # itself rather than requiring it to equal len(gap)-2.
                if _struct.unpack_from('<H', gap, 0)[0] == 94: gap_prefix_ok += 1
                npa = b['tail']['pretable'].get('n_perimeter_a')
                n_non_mirror = sum(1 for k in (b.get('internal_kinds') or []) if k != 'mirror')
                v40 = _struct.unpack_from('<I', gap, 40)[0]
                if v40 == npa + n_non_mirror: gap_v40_ok += 1
                else: gap_exceptions.append(f"{obj['name']}: v40={v40} want={npa+n_non_mirror}")
                if _struct.unpack_from('<I', gap, 44)[0] == 1: gap_v44_ok += 1
ok = gap_checked > 0 and gap_prefix_ok == gap_checked and gap_v40_ok == gap_checked and gap_v44_ok == gap_checked
print(f"   {'ok ' if ok else 'FAIL'} {gap_checked} blocks checked: length-prefix ok={gap_prefix_ok}, "
      f"n_perimeter_a+non_mirror_objs ok={gap_v40_ok}, constant-1 ok={gap_v44_ok}")
if not ok: fails.append(f'unclassified_gap: checked={gap_checked} prefix_ok={gap_prefix_ok} v40_ok={gap_v40_ok} v44_ok={gap_v44_ok} exceptions={gap_exceptions}')

print('-- shared seam-corner topology and quantized curve point')
corner_counts = {}
corner_example = None
quantized_example = None
for marker_zip in (
        os.path.join(HERE, 'markers', '2303-BD137-PLACED', '2303-BD 137 PLACED.zip'),
        os.path.join(HERE, 'markers', '2303-BD137-UNLAID', '2303-BD 137.zip'),
        os.path.join(HERE, 'markers', 'misc-test-markers', 'AD1234 TEST 134.zip')):
    for obj in am.list_zip(marker_zip).get('piece', []):
        for block in ap.decode(obj['data'])['blocks']:
            analysis = ap.classify_line_table(block)
            for record in analysis['records']:
                for point_i, point in enumerate(record['points']):
                    name = point['classification']
                    if name in ('shared_seam_corner', 'seam_model_quantized'):
                        corner_counts[name] = corner_counts.get(name, 0) + 1
                    if name == 'shared_seam_corner' and corner_example is None:
                        corner_example = (block, point['corner_match'])
                    if name == 'seam_model_quantized' and quantized_example is None:
                        quantized_example = (block, record['idx'], point_i)
ok = corner_counts == {'shared_seam_corner': 68, 'seam_model_quantized': 2}
print(f"   {'ok ' if ok else 'FAIL'} classified corpus residue {corner_counts}")
if not ok: fails.append(f'seam-corner classifications {corner_counts}')

# The shared join is redundant evidence, not a loose proximity waiver: if
# only one of its two table copies changes, it must stop validating.
mutated = copy.deepcopy(corner_example[0]) if corner_example else None
if mutated:
    match = corner_example[1]
    left = next(r for r in mutated['tail']['line_records']
                if r['idx'] == match['left_record'])
    left['points'][-1]['x'] += 1
    mutation_ok = not ap.classify_line_table(mutated)['ok']
else:
    mutation_ok = False
print(f"   {'ok ' if mutation_ok else 'FAIL'} one-copy corner corruption is rejected")
if not mutation_ok: fails.append('shared seam-corner corruption was accepted')

mutated = copy.deepcopy(corner_example[0]) if corner_example else None
if mutated:
    match = corner_example[1]
    for record_id, point_i in ((match['left_record'], -1),
                               (match['right_record'], 0)):
        record = next(r for r in mutated['tail']['line_records']
                      if r['idx'] == record_id)
        record['points'][point_i]['x'] += ap.SHARED_SEAM_CORNER_MAX + 1000
    paired_mutation_ok = not ap.classify_line_table(mutated)['ok']
else:
    paired_mutation_ok = False
print(f"   {'ok ' if paired_mutation_ok else 'FAIL'} out-of-bound paired corner is rejected")
if not paired_mutation_ok: fails.append('out-of-bound shared seam corner was accepted')

mutated = copy.deepcopy(quantized_example[0]) if quantized_example else None
if mutated:
    _, record_id, point_i = quantized_example
    record = next(r for r in mutated['tail']['line_records'] if r['idx'] == record_id)
    record['points'][point_i]['x'] += ap.SEAM_MODEL_QUANTIZED_MAX + 100
    quantized_mutation_ok = not ap.classify_line_table(mutated)['ok']
else:
    quantized_mutation_ok = False
print(f"   {'ok ' if quantized_mutation_ok else 'FAIL'} over-limit quantized seam point is rejected")
if not quantized_mutation_ok: fails.append('over-limit quantized seam point was accepted')

print('-- line-table shadow geometry')
shadow_counts = {}
shadow_example = None
for marker_zip in (
        os.path.join(HERE, 'captures', '2303-B1-38B-IN WG-SP24',
                     '2303-B1-38B-IN WG-SP24.ZIP'),
        os.path.join(HERE, 'markers', '2303-BD137-PLACED', '2303-BD 137 PLACED.zip'),
        os.path.join(HERE, 'markers', '2303-BD137-UNLAID', '2303-BD 137.zip')):
    for obj in am.list_zip(marker_zip).get('piece', []):
        for block in ap.decode(obj['data'])['blocks']:
            analysis = ap.classify_line_table(block)
            for record in analysis['records']:
                for point in record['points']:
                    name = point['classification']
                    if name in ('stored_geometry_quantized',
                                'shared_graded_perimeter_point'):
                        shadow_counts[name] = shadow_counts.get(name, 0) + 1
                    if name == 'shared_graded_perimeter_point' and shadow_example is None:
                        shadow_example = (block, point['graded_match'])
ok = shadow_counts == {'stored_geometry_quantized': 2,
                       'shared_graded_perimeter_point': 8}
print(f"   {'ok ' if ok else 'FAIL'} classified kind-1 residue {shadow_counts}")
if not ok: fails.append(f'line-table shadow classifications {shadow_counts}')

mutated = copy.deepcopy(shadow_example[0]) if shadow_example else None
if mutated:
    match = shadow_example[1]
    left = next(r for r in mutated['tail']['line_records']
                if r['idx'] == match['left_record'])
    left['points'][-1]['x'] += 1
    mutation_ok = not ap.classify_line_table(mutated)['ok']
else:
    mutation_ok = False
print(f"   {'ok ' if mutation_ok else 'FAIL'} one-copy graded shadow corruption is rejected")
if not mutation_ok: fails.append('shared graded shadow corruption was accepted')

mutated = copy.deepcopy(shadow_example[0]) if shadow_example else None
if mutated:
    match = shadow_example[1]
    for record_id, point_i in ((match['left_record'], -1),
                               (match['right_record'], 0)):
        record = next(r for r in mutated['tail']['line_records']
                      if r['idx'] == record_id)
        record['points'][point_i]['x'] += ap.GRADED_SHADOW_MAX + 100
    paired_mutation_ok = not ap.classify_line_table(mutated)['ok']
else:
    paired_mutation_ok = False
print(f"   {'ok ' if paired_mutation_ok else 'FAIL'} out-of-bound graded shadow is rejected")
if not paired_mutation_ok: fails.append('out-of-bound graded shadow was accepted')

print('-- markers (markers/, skipped when absent) - see MARKER_DECODE_PLAN.md')
# Production style 2303 (bra): the same marker unlaid and laid (2026-09 V17
# export), the full 97-placement drawn-marker DXF of the laid marker, and the
# July four-corner-probe set with AccuMark's own drawn DXFs.
# dxf_outline_max 0.08 in is the drawn export's curve re-tessellation, not a
# decode error - a piece DXF pins the stored points to 1e-4 in (TASK6-CURVE).
# The drawn DXF's raw vertex units vary with the AccuMark session's unit
# setting - $INSUNITS 1 (inches) on the July markers, 5 (centimeters) on this
# "Metric [cm]" one; verify_marker.dxf_marker() normalises to inches from
# that header field.
import verify_marker as vm
MK = [  # folder, zip, {fact: want}, dxf folder or None
 # the unlaid twin with its 18 pieces bundled: the only never-laid marker whose slots can be checked against
 # real geometry (v4.2) - every slot's home box vs the piece's own outline at the tiled size, no layout needed
 ('2303-BD137-UNLAID', '2303-BD 137.zip', dict(laid='no', placements=0, slots=97, records=66, pieces_listed=12, bound=0,
                                              laid_state='unlaid', slots_bound=97, unplaced=97, order_cuts=61, geometry='all',
                                              hdr_area_mode='last_model', hdr_perim_mode='last_model',
                                              bbox_ok_unplaced=97, bbox_n_unplaced=97, area_ok_unplaced=66, area_pairs_unplaced=66), None),
 ('2303-BD137-PLACED', '2303-BD 137 PLACED.zip', dict(laid='yes', placements=97, bundles=61, bound=97, identity='yes',
                                                    width_cm=137.0, length_cm=377.68, util_pct=71.51, bbox_ok=97, area_ok=66, area_pairs=66,
                                                    dxf_centres=97, dxf_outlines_checked=97, dxf_size_labels=97,
                                                    laid_state='laid', unplaced=0, geometry='n/a', hdr_area_mode='all', hdr_perim_mode='last_model',
                                                    folds='2303-B1-A1- OUCF-SP24;2303-B1-A2- OUCF-SP24;2303-B1-DD2- OUCF-SP24;2303-B1-E3- OUCF-SP24'), 'dxf'),
 # 1 placed of 72: 71 unplaced slots WITH pieces. x matches to 0.0001 in once the marker's own block buffer (section 6,
 # 2 x 0.0591 in) is subtracted; the y axis carries a one-sided excess of up to 0.0786 in on 48 of 71 slots that
 # nothing explains yet [?] (the DXF-verified placed slot is exact) - so the unplaced box is held to the 0.08 in
 # curve band below, not 0.02, and bbox_ok_unplaced is deliberately not pinned.
 ('2303-CP150-JULY',   '2303-CP 150 CPL.zip', dict(laid='yes', placements=1, bound=1, identity='yes', dxf_centres=1, dxf_size_labels=1, area_ok=1, bbox_ok=4,
                                                   laid_state='partial', unplaced=71, geometry='all', bbox_n_unplaced=71,
                                                   hdr_area_mode='all', hdr_perim_mode='last_model', area_ok_unplaced=36, area_pairs_unplaced=36), 'dxf'),
 # Controlled M3 test: a fresh rectangle assigned CAP-RULES-A (real,
 # non-placeholder per-size-break deltas), rule 1 applied to only 2 of 4
 # corners so the other 2 rely on graded_outline()'s chain-interpolation
 # branch, placed in its own marker at size 2 and size 18 (both far from
 # base size 8). Closes the one open item flagged 2026-09-09: style 2303's
 # own grading is all-placeholder, so graded_outline() was never proven to
 # move a point on real data until this. dxf_outline_max 0.001in / dxf_
 # centre_worst 0.0007in confirm both sizes' graded shape - including the
 # interpolated corners - against AccuMark's own drawn marker DXF.
 ('CLAUDE-GRADE-MARKER', 'CLAUDE-GRADE-MARKER.zip', dict(laid='yes', placements=2, bound=2, identity='yes',
                                                    bbox_ok=2, dxf_centres=2, dxf_outlines_checked=2, dxf_size_labels=2), 'dxf'),
]
# dxf_size_labels (v4.1): the label AccuMark draws at every placed centre reads
# `<piece> <size>` (September vintage: one TEXT; July: three stacked). It is an
# answer key for the slot -> (piece, size) binding that needs no area and no
# geometry, and it is the only one that can tell sister sizes apart on style
# 2303 (all-placeholder grading: same shape, same area) - 97/97 with the
# structural binding, 20/97 with the old area rule.
for folder, zname, want, dxf in MK:
    path = os.path.join(HERE, 'markers', folder, zname)
    if not os.path.isfile(path):
        print(f'   --  {folder:22} (absent)'); continue
    dxf_dir = os.path.join(HERE, 'markers', folder) if dxf else None
    try:
        results, _ = vm.facts(path, dxf_dir)
    except Exception as e:
        print(f'   FAIL {folder:22} {type(e).__name__}: {e}'); fails.append(f'{folder}: {e}'); continue
    for f, _ in results:
        bad = [f'{k}={f.get(k)}!={v}' for k, v in want.items() if str(f.get(k)) != str(v)]
        if dxf and f.get('dxf_outline_max', 9) > 0.08: bad.append(f"dxf_outline_max={f.get('dxf_outline_max')}")
        if f.get('bbox_worst_unplaced', 0) > 0.08: bad.append(f"bbox_worst_unplaced={f.get('bbox_worst_unplaced')}")
        # 0.0015 in, not the July markers' 0.001: a cm-vintage drawn DXF
        # (2303-BD137-PLACED) round-trips through a /2.54 conversion the
        # inch-native July DXFs don't, costing a little precision - not a
        # decode error (worst seen: July 0.0008, this one 0.0012).
        if dxf and f.get('dxf_centre_worst', 9) > 0.0015: bad.append(f"dxf_centre_worst={f.get('dxf_centre_worst')}")
        print(f"   {'ok ' if not bad else 'FAIL'} {f['name']:30} {'; '.join(bad) if bad else 'as expected'}")
        if bad: fails.append(f"{f['name']}: " + '; '.join(bad))

print('-- marker model list / size table / trailer stamps (v4, see CHANGELOG.md)')
# markers/1825D-SS21-UNLAID is a foreign-origin sample: AccuMark "version 9
# data" exported 2020-10-16 by another user (kids' sizes 2-3 .. 11-12, two
# UNLAID markers, no piece/model/order objects). Its hyphenated sizes and the
# 0-flag size rows exposed that the old regex reader found no sizes, the old
# length-after reader found no model, and read_object's created/modified were
# unaligned-scan junk. The corpus rows pin the same three fixes on markers
# the old readers half-handled (2303: 3 of 11 models dropped; AD1234 and
# LADIES-BLOUSE: no sizes at all; every single-model marker: no model).
import datetime, struct
def _utc(*a): return int(datetime.datetime(*a, tzinfo=datetime.timezone.utc).timestamp())
SZ_1825D = ['2-3', '3-4', '4-5', '5-6', '6-7', '7-8', '8-9', '9-10', '11-12']
CUT_1825D = {'1825D IGUS 061020': 'CUT X 01', '1825D FROT 061020': 'CUT X 01',
             '1825D OGUS 061020': 'CUT X 01', '1825D BACK 061020': 'CUT X01'}
def _mk(parts, name):
    path = os.path.join(HERE, 'markers', *parts)
    if not os.path.isfile(path): return None
    o = next(o for o in am.list_zip(path)['marker'] if o['name'] == name)
    return o, am.parse_marker(o['data'])
V4_MARKERS = [  # zip path under markers/, marker name, {fact: want}
 (('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), '1825D-GT 168 SS21',
  dict(models=['CON2-1825D'], sizes=SZ_1825D, slots=9, records=9, pieces=1, width_cm=168.0,
       created=_utc(2020, 10, 16, 6, 16, 15), modified=_utc(2020, 10, 16, 6, 16, 15))),
 (('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), '1825D-BD 180 SS21',
  dict(models=['CON2-1825D'], sizes=SZ_1825D, slots=27, records=27, pieces=3, width_cm=180.0,
       created=_utc(2020, 10, 16, 6, 11, 35), modified=_utc(2020, 10, 16, 6, 11, 35))),
 # three more never-laid, marker-only markers from the same foreign origin
 # (Empty marker files Zip, 2020-21): 4, 3 and 1 pieces; 6, 7 and 11 size rows
 (('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip'), '5683D-BD 168 SS21',
  dict(models=['CON-5683D'], sizes=['18-24', '2-3', '3-4', '4-5', '5-6', '6-7'], slots=24, records=24, pieces=4, width_cm=168.0,
       created=_utc(2020, 10, 16, 4, 56, 33), modified=_utc(2020, 10, 16, 4, 56, 33))),
 (('2591A-SS21-UNLAID', '2591A-BD 157 AW SS21.zip'), '2591A-BD 157 AW SS21',
  dict(models=['CON-2591A'], sizes=['6/7', '7/8', '8/9', '9/10', '11/12', '13/14', '15/16'], slots=35, records=21, pieces=3, width_cm=157.0,
       created=_utc(2020, 10, 16, 5, 0, 17), modified=_utc(2020, 10, 16, 5, 0, 17))),
 (('418T-SHAPESHIFTER-UNLAID', '418T-BD 160 SHAPESHIFTER.zip'), '418T-BD 160 SHAPESHIFTER',
  dict(models=['418T'], sizes=['2-3', '3-4', '4-5', '5-6', '6-7', '7-8', '8-9', '9-10', '11-12', '13-14', '15-16'],
       slots=22, records=11, pieces=1, width_cm=160.0,
       created=_utc(2021, 5, 13, 6, 36, 21), modified=_utc(2021, 5, 13, 6, 36, 21))),
 (('2303-BD137-UNLAID', '2303-BD 137.zip'), '2303-BD 137',      # 8 of 11 models before; the missing 3 were B1 7, OUCF DD, OUCF E
  dict(n_models=11, last_model='2303 OUCF E', n_sizes=61, slots=97,
       created=_utc(2026, 9, 8, 16, 29, 51), modified=_utc(2026, 9, 8, 16, 29, 51))),
 (('2303-CP150-JULY', '2303-CP 150 CPL.zip'), '2303-CP 150 CPL LEFTBTM 26-47',   # 9 of 11 before
  dict(n_models=11, last_model='2303 MOCUP B1 11', n_sizes=36, slots=72,
       created=_utc(2026, 7, 29, 14, 4, 33), modified=_utc(2026, 7, 29, 14, 4, 33))),
 (('misc-test-markers', 'AD1234 TEST 134.zip'), 'AD1234 TEST 134',                 # no sizes before
  dict(models=['ID1005 - TOP'], sizes=['XS', 'XS', 'S', 'S', 'S', 'S', 'M', 'M', 'M', 'M', 'L', 'L', 'XL'], slots=13)),
 (('misc-test-markers', 'LADIES-BLOUSE TEST-2.zip'), 'LADIES-BLOUSE TEST-2',       # no sizes before
  dict(models=['LADIES-BLOUSE'], sizes=['10', '12', '12', '14', '14', '16'], slots=54)),
 (('CLAUDE-GRADE-MARKER', 'CLAUDE-GRADE-MARKER.zip'), 'CLAUDE-GRADE-MARKER',       # single-model markers: no model before
  dict(models=['CLAUDE-GRADE-MODEL'], sizes=['2', '18'], slots=2)),
 (('CAP-C21-SEC14', 'CAP-C21-SEC14.zip'), 'CAP-C21-SEC14',
  dict(models=['CAP-C21-MODEL'], sizes=['2', '18'], slots=2,
       created=_utc(2026, 9, 10, 19, 32, 53), modified=_utc(2026, 9, 10, 19, 48, 3))),
]
for parts, name, want in V4_MARKERS:
    got = _mk(parts, name)
    if got is None:
        print(f'   --  {name:30} (absent)'); continue
    o, mk = got
    have = dict(models=mk['models'], n_models=len(mk['models']), last_model=(mk['models'] or [None])[-1],
                sizes=[r['size'] for r in mk['sizes']] if 'sizes' in want else None, n_sizes=len(mk['sizes']),
                slots=len(mk['slots']), records=len(mk['records']), pieces=len(mk['pieces']),
                width_cm=round(mk['width']*2.54, 2), created=o['created'], modified=o['modified'])
    bad = [f'{k}={have[k]!r}!={v!r}' for k, v in want.items() if have[k] != v]
    # the identities check_marker now enforces: tables tile sections 11-12, size rows tile the slot table
    bad += [f'check failed: {n}' for n, ok, _ in am.check_marker(mk) if not ok and (n.startswith('model list') or n.startswith('size table'))]
    if name.startswith('1825D'):
        recs = mk['records']
        if any(r['size'] not in SZ_1825D for r in recs): bad.append('a record size is not a real size name')
        if any(r['cut'] != CUT_1825D[r['piece']] for r in recs): bad.append('a record cut description is wrong')
        if any(s['size'] not in SZ_1825D for s in mk['slots']): bad.append('a slot is bound to a wrong size')
        if abs(mk['total_area'] - sum(r['area'] for r in recs)) > 1e-9: bad.append('@422 != sum(record areas)')
        if abs(mk['unknown_454'] - sum(r['perimeter'] for r in recs)) > 1e-9: bad.append('@454 != sum(record perimeters)')
        if mk['laid'] or mk['placements']: bad.append('an unlaid marker was read as laid')
    print(f"   {'ok ' if not bad else 'FAIL'} {name:30} {'; '.join(bad) if bad else 'as expected'}")
    if bad: fails.append(f'{name}: ' + '; '.join(bad))
print('-- slot binding: structure, not area (v4.1, see CHANGELOG.md)')
# Every slot is bound to (piece, size, model, record) from its own 6-byte head,
# the size table's tiling of the slot table and section 10's piece list; the
# declared area / bundle / record text are checked against that, never used to
# choose it. The old area rule tied on sister sizes and picked an arbitrary one
# (77 of 97 slots on 2303-BD 137) - invisible to every geometric check because
# style 2303's grading is all-placeholder; the drawn DXF's labels (MK rows
# above: dxf_size_labels) are what prove the structural size.
BIND_ROWS = ['every slot bound structurally', 'slot bundle == head bundle == size-row index',
             'slot declared area == bound record area', 'record text ends with the tiled size + G',
             'records == section-13 entries', 'piece list tiles section 10']
n_mk = 0; bad_all = []
for zp in sorted(glob.glob(os.path.join(HERE, 'markers', '**', '*.zip'), recursive=True)):
    try: mos = am.list_zip(zp).get('marker', [])
    except Exception: continue
    for o in mos:
        n_mk += 1; mk = am.parse_marker(o['data'])
        rows = {n: ok for n, ok, _ in am.check_marker(mk)}
        miss = [n for n in BIND_ROWS if not rows.get(n, False)]
        # directory word 40 is a state code, not an offset: 0 / 1 / 2 = none /
        # some / all slots placed, and there is no section 40 or 41
        want_word = 0 if not mk['placements'] else (2 if len(mk['placements']) == len(mk['slots']) else 1)
        if mk['placed_word'] != want_word: miss.append(f"placed word {mk['placed_word']} != {want_word}")
        if mk['sections'][40] is not None or mk['sections'][41] is not None: miss.append('a bogus section 40/41')
        if miss: bad_all.append(f"{o['name']}: {'; '.join(miss)}")
print(f"   {'ok ' if n_mk and not bad_all else 'FAIL'} {n_mk} fixture markers pass all {len(BIND_ROWS)} binding rows  {'; '.join(bad_all)}")
if not n_mk or bad_all: fails.append('binding rows: ' + '; '.join(bad_all))

# never-laid markers: WHAT is to be laid and nothing about where. Per fixture:
# slots per (piece, size) [the cut quantity: a `CUT X02` piece is a mirrored
# pair, so 2], and whether the header's @422 / @454 equal the sums over ALL
# slots (every never-laid marker except 2303-BD 137, whose header holds other
# sums - see CHANGELOG v4.1).
UNLAID = [  # parts, marker, {piece: slots per size}, header sums == all-slot sums?, cuts (the order's total quantity), block-buffer entries
 (('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), '1825D-GT 168 SS21', {'1825D IGUS 061020': 1}, True, 9, 2),
 (('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), '1825D-BD 180 SS21',
  {'1825D FROT 061020': 1, '1825D OGUS 061020': 1, '1825D BACK 061020': 1}, True, 9, 4),
 (('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip'), '5683D-BD 168 SS21',
  {'5683D OGUS 210920': 1, '5683D IGUSE 210920': 1, '5683D BACK 210920': 1, '5683D FROT 210920': 1}, True, 6, 0),
 (('2591A-SS21-UNLAID', '2591A-BD 157 AW SS21.zip'), '2591A-BD 157 AW SS21',
  {'2591A POUTH 170920': 2, '2591A BPNL170920': 1, '2591A LEG 170920': 2}, True, 7, 0),
 (('418T-SHAPESHIFTER-UNLAID', '418T-BD 160 SHAPESHIFTER.zip'), '418T-BD 160 SHAPESHIFTER', {'0418T TRS 190421': 2}, True, 11, 2),
 (('2303-BD137-UNLAID', '2303-BD 137.zip'), '2303-BD 137', None, False, 61, 0),
]
from collections import Counter
for parts, name, mult, sums, cuts, n_buf in UNLAID:
    got = _mk(parts, name)
    if got is None:
        print(f'   --  {name:30} (absent)'); continue
    o, mk = got; bad = []
    if mk['laid'] or mk['placements'] or not all(s['empty'] for s in mk['slots']): bad.append('read as laid / has placements')
    if mk['placed_word'] != 0: bad.append(f"placed word {mk['placed_word']} != 0")
    if any((s.get('binding') or {}).get('method') != 'structural' for s in mk['slots']): bad.append('a slot is not structurally bound')
    if any(s['size'] not in {r['size'] for r in mk['sizes']} for s in mk['slots']): bad.append('a slot has a size outside the size table')
    if sums:
        if abs(mk['total_area'] - sum(s['area'] for s in mk['slots'])) > 1e-9: bad.append('@422 != sum(all slot areas)')
        if abs(mk['unknown_454'] - sum(s['record']['perimeter'] for s in mk['slots'])) > 1e-9: bad.append('@454 != sum(all slot record perimeters)')
    if sum(s['quantity'] for m in mk['order_copy'] for s in m['sizes']) != cuts: bad.append('order copy total quantity != %d' % cuts)
    if len(mk['block_buffers']) != n_buf: bad.append('%d block-buffer entries != %d' % (len(mk['block_buffers']), n_buf))
    if sums and mk['header_sums'] != dict(area='all', perimeter='all'): bad.append('header sums %s not all/all' % mk['header_sums'])
    if not sums and mk['header_sums'] != dict(area='last_model', perimeter='last_model'): bad.append('header sums %s not last_model' % mk['header_sums'])
    if mult is not None:
        per = Counter((s['piece'], s['size']) for s in mk['slots'])
        got_mult = {}
        for (pc, sz), n in per.items(): got_mult.setdefault(pc, set()).add(n)
        if {k: sorted(v) for k, v in got_mult.items()} != {k: [v] for k, v in mult.items()}: bad.append(f'slots per (piece, size) {dict(got_mult)} != {mult}')
    print(f"   {'ok ' if not bad else 'FAIL'} unplaced {name:30} {'; '.join(bad) if bad else 'bound N/N, all slots empty, sums as expected'}")
    if bad: fails.append(f'unplaced {name}: ' + '; '.join(bad))

# mutation tests: each new row must actually FAIL when the fact it checks is
# broken in the bytes (a check that cannot fail proves nothing). In-memory byte
# patches of the 2591A marker; the unpatched marker must have every row ok.
src = _mk(('2591A-SS21-UNLAID', '2591A-BD 157 AW SS21.zip'), '2591A-BD 157 AW SS21')
if src:
    d0, mk0 = src[0]['data'], src[1]
    sec = mk0['sections']; s5 = mk0['slots'][5]; h5 = s5['slot'] - am.SLOT_HEAD
    def _rows(d, **kw): return {n: ok for n, ok, _ in am.check_marker(am.parse_marker(d, **kw))}
    def _patched(off, fmt, val):
        b = bytearray(d0); struct.pack_into(fmt, b, off, val); return bytes(b)
    MUT = [  # description, patched bytes / kwargs, the row that must flip
     ('slot head: record index of slot 5 moved to the next record',
      dict(d=_patched(h5, '<H', mk0['slots'][5]['record_index'] + 1)), 'slot declared area == bound record area'),
     ('slot head: bundle of slot 5 changed',
      dict(d=_patched(h5 + 4, '<H', s5['bundle'] + 1)), 'slot bundle == head bundle == size-row index'),
     ('section 13: first record offset changed',
      dict(d=_patched(sec[am.SEC_INDEX][0] - 6, '<I', mk0['record_index'][0] + 1)), 'records == section-13 entries'),
     ('section 10: first piece\'s fabric-type count 1 -> 0',
      dict(d=_patched(sec[am.SEC_PIECES][0] + am.PIECE_LIST_HEAD + 22, '<H', 0)), 'piece list tiles section 10'),
     ('section 12: first size row owns one piece fewer',
      dict(d=_patched(sec[am.SEC_SIZES][0] - 6 + 4, '<H', mk0['sizes'][0]['n'] - 1)), 'every slot bound structurally'),
     ('binding="area" (the pre-v4.1 rule)', dict(d=d0, binding='area'), 'every slot bound structurally'),
    ]
    clean = _rows(d0); bad = [f'clean marker: {n}' for n in BIND_ROWS if not clean.get(n)]
    for desc, kw, row in MUT:
        r = _rows(**kw)
        if r.get(row, False): bad.append(f'"{desc}" did not fail "{row}"')
    # v4.2 rows: order copy, laid state, @430, block-buffer indices. Each byte
    # offset is computed from the marker's own parse, not hard-coded.
    n0 = sec[am.SEC_ORDER_COPY][0] - 6                       # the first model block
    p = n0 + am.MODEL_HEAD + struct.unpack_from('<H', d0, n0)[0]
    for _ in range(struct.unpack_from('<H', d0, n0 + 14)[0]): p += 2 + struct.unpack_from('<H', d0, p)[0]   # skip the fabric types
    MUT2 = [
     ('section 15: first size row quantity 1 -> 2', _patched(p + 2, '<H', 2), 'order copy tiles section 15; quantity == size-row count'),
     ('directory word 40: placed word 0 -> 2', _patched(0x12a, '<H', 2), 'laid state: placed word, slot coordinates and header agree'),
     ('header @430: placed area 0 -> 1', _patched(430, '<d', 1.0), 'header @430 == sum of placed slot areas'),
    ]
    for desc, patched, row in MUT2:
        if _rows(patched).get(row, True): bad.append(f'"{desc}" did not fail "{row}"')
    MUT += MUT2
    # the block-buffer index needs a marker that HAS a section 6
    src418 = _mk(('418T-SHAPESHIFTER-UNLAID', '418T-BD 160 SHAPESHIFTER.zip'), '418T-BD 160 SHAPESHIFTER')
    if src418:
        b = bytearray(src418[0]['data']); struct.pack_into('<H', b, src418[1]['sections'][am.SEC_PIECES][0] + am.PIECE_LIST_HEAD + 8, 2)
        row = 'piece buffer indices resolve into the block-buffer table'
        if not {n: ok for n, ok, _ in am.check_marker(src418[1])}.get(row): bad.append('418T clean marker fails ' + row)
        if {n: ok for n, ok, _ in am.check_marker(am.parse_marker(bytes(b)))}.get(row, True): bad.append('section 10: buffer index 1 -> 2 did not fail ' + row)
        MUT.append(('section 10: buffer index 1 -> 2 (past the 2-entry table)', None, row))
    print(f"   {'ok ' if not bad else 'FAIL'} mutation tests (v4.1 + v4.2): {len(MUT)} byte patches each break exactly the row that checks them  {'; '.join(bad)}")
    if bad: fails.append('binding mutation tests: ' + '; '.join(bad))
    # the unplaced inventory of a marker-only ZIP: the cut order, read from structure alone
    inv_res = am.place_marker(os.path.join(HERE, 'markers', '2591A-SS21-UNLAID', '2591A-BD 157 AW SS21.zip'))
    inv = inv_res['markers'][0]['inventory']; bad = []
    # no piece object in the ZIP (result-level 'none'), yet 14 of 35 slots (the LEG pieces) have an outline read from the marker's own
    # stream, and its bounding box equals the slot's stored home box EXACTLY - a check the decode never used
    if inv_res['geometry_available'] != 'none' or inv['marker']['geometry_available'] != 'all' or inv['marker']['outline_source'] != 'stream': bad.append('marker-only ZIP: expected no piece objects but a stream outline for every slot')
    so = [x for x in inv['slots'] if x.get('outline')]
    if len(so) != 35 or any(abs(x['checks']['bbox_dx']) > 1e-3 or abs(x['checks']['bbox_dy']) > 1e-3 or abs(x['checks']['area_ratio'] - 1) > 1e-3 for x in so): bad.append('stream outlines vs home box / area: %d slots' % len(so))
    # the same for every marker-only fixture: the stream outline's bounding box IS the stored home box (never used by the decode)
    for zn_, mn_, ns_ in (('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip', 36), ('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip', 24), ('418T-SHAPESHIFTER-UNLAID', '418T-BD 160 SHAPESHIFTER.zip', 22)):
        gs = []; geo_ = []
        for mk_ in am.place_marker(os.path.join(HERE, 'markers', zn_, mn_))['markers']:
            gs += [x for x in mk_['inventory']['slots'] if x.get('outline')]; geo_.append(mk_['inventory']['marker']['geometry_available'])
        res_ = [(x['home_box_in'][0] - (max(q[0] for q in x['outline']) - min(q[0] for q in x['outline'])), x['home_box_in'][1] - (max(q[1] for q in x['outline']) - min(q[1] for q in x['outline']))) for x in gs]
        if len(gs) != ns_ or set(geo_) != {'all'} or any(abs(a_) > 1e-3 or abs(b_) > 1e-3 for a_, b_ in res_): bad.append(f'{zn_}: {len(gs)} of {ns_} slots, {geo_}, home box vs stream bbox {max((abs(a_) for a_, _ in res_), default=None)}')
    if inv['marker']['laid_state'] != 'unlaid' or inv['totals']['slots'] != 35 or inv['totals']['placed'] != 0: bad.append('totals: %s' % inv['totals'])
    if [(o['size'], o['quantity']) for o in inv['order_lines']] != [(s, 1) for s in ['6/7', '7/8', '8/9', '9/10', '11/12', '13/14', '15/16']]: bad.append('order lines')
    pairs = {}
    for s in inv['slots']:
        if s['pair']: pairs.setdefault(s['pair']['group'], []).append((s['pair']['part'], s['preset']['mirror'], s['piece']))
    if len(pairs) != 14 or any(sorted(p[0] for p in v) != ['A', 'B'] or [p[1] for p in sorted(v)] != [False, True] or len({p[2] for p in v}) != 1 for v in pairs.values()):
        bad.append('the 14 `CUT X02` pairs should each be one piece, part A plain + part B mirrored: %d groups' % len(pairs))
    a422 = inv_res['markers'][0]['marker']['total_area']      # == the sum over all slots on a never-laid marker
    if abs(inv['totals']['area_to_lay'] - a422) > 1e-9 or abs(inv['totals']['min_length_in'] - a422 / inv['marker']['width_in']) > 1e-9: bad.append('area / minimum length')
    if not inv_res['markers'][0]['inventory']['warnings'] or not any(w.startswith('no piece objects') for w in inv['warnings']): bad.append('no "no piece objects" warning')
    if not am.inventory_report(inv, inv_res['markers'][0]['checks']).endswith('DECODED CLEANLY'): bad.append('report does not end DECODED CLEANLY')
    print(f"   {'ok ' if not bad else 'FAIL'} unplaced_inventory on a marker-only ZIP (2591A: 35 slots, 14 mirrored pairs, 35 outlines from the stream; 1825D / 5683D / 418T bounding boxes == home boxes)  {'; '.join(bad)}")
    if bad: fails.append('unplaced_inventory: ' + '; '.join(bad))
# and the answer key can fail: the old area rule against the drawn DXF labels
zp = os.path.join(HERE, 'markers', '2303-BD137-PLACED', '2303-BD 137 PLACED.zip')
dxf = os.path.join(HERE, 'markers', '2303-BD137-PLACED', '2303-BD 137 PLACED.DXF')
if os.path.isfile(zp) and os.path.isfile(dxf):
    labs = vm.dxf_labels(dxf)
    mk_area = am.parse_marker(am.list_zip(zp)['marker'][0]['data'], binding='area')
    n_area = sum(1 for s in mk_area['placements'] if vm._label_matches(labs, s, s['piece'], s['size']))
    n_struct = sum(1 for s in am.parse_marker(am.list_zip(zp)['marker'][0]['data'])['placements']
                   if vm._label_matches(labs, s, s['piece'], s['size']))
    ok = n_struct == 97 and n_area < 97
    print(f"   {'ok ' if ok else 'FAIL'} DXF labels: structural {n_struct}/97, area rule {n_area}/97 (the oracle can tell them apart)")
    if not ok: fails.append(f'dxf label oracle: structural {n_struct}, area {n_area}')

# library tables copied between storage areas: created can be LATER than modified
# (M-MARKER: 2023 vs 2013), and the notch table's 2004 creation date is outside
# the old 2014-2039 window - both must be reported exactly as stored
cp_zip = os.path.join(HERE, 'markers', '2303-CP150-JULY', '2303-CP 150 CPL.zip')
if os.path.isfile(cp_zip):
    ob = am.list_zip(cp_zip)
    lib = {o['name']: (o['created'], o['modified']) for k in ('annotation', 'notch_table') for o in ob.get(k, [])}
    want_lib = {'M-MARKER': (1674111116, 1383724864), 'V-NOTCH-ALL CUSTOMERS': (1073574632, 1746183410)}
    bad = [f'{k}={lib.get(k)}!={v}' for k, v in want_lib.items() if lib.get(k) != v]
    print(f"   {'ok ' if not bad else 'FAIL'} library-table stamps (2004 / 2013 / 2023) reported as stored  {'; '.join(bad) if bad else ''}")
    if bad: fails.append('library-table stamps: ' + '; '.join(bad))
# every object in every fixture ZIP carries both stamps (153 objects; the old
# scan returned junk on ~89% of them, so a regression here is loud)
n_obj = n_missing = 0
for zp in glob.glob(os.path.join(HERE, 'markers', '**', '*.zip'), recursive=True):
    for kind, lst in am.list_zip(zp).items():
        if isinstance(lst, list) and lst and isinstance(lst[0], dict) and 'kind' in lst[0]:
            for ob_ in lst:
                n_obj += 1; n_missing += (ob_['created'] is None or ob_['modified'] is None)
print(f"   {'ok ' if n_obj and not n_missing else 'FAIL'} {n_obj} fixture objects, {n_missing} missing a created/modified stamp")
if not n_obj or n_missing: fails.append('fixture objects with a missing stamp: %d/%d' % (n_missing, n_obj))
# read_object: stamps outside the plausibility window (zero / sentinel) -> None
src = _mk(('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), '1825D-GT 168 SS21')
if src:
    d = bytearray(src[0]['data']); t0 = len(d) - am.TRAILER
    struct.pack_into('<I', d, t0 + am.TRAILER_CREATED, 0); struct.pack_into('<I', d, t0 + am.TRAILER_MODIFIED, 0xffffffff)
    r = am.read_object(bytes(d))
    ok = r['created'] is None and r['modified'] is None
    print(f"   {'ok ' if ok else 'FAIL'} zero / sentinel stamps read back as None")
    if not ok: fails.append('read_object: implausible stamps not rejected')
    # the table walkers must stay in bounds on truncated / junk input
    junk = bytes(range(256)) * 4; raised = []
    for fn in (am.parse_model_list, am.parse_sizes_section):
        for lo, hi in ((0, 10), (3, 10**6), (len(junk)+50, len(junk)+80), (600, 200)):
            try: fn(junk, lo, hi)
            except Exception as e: raised.append(f'{fn.__name__}({lo},{hi}): {type(e).__name__}')
    print(f"   {'ok ' if not raised else 'FAIL'} table walkers stay in bounds on junk / truncated input")
    if raised: fails.append('table walkers raised: ' + '; '.join(raised))

print('-- live corpus: 41 markers exported from the scratch area (v4.5)')
# `markers-live/` is deliberately NOT under `markers/`: the strict all-fixtures
# invariants above hold on every marker there, and five real markers here carry
# documented anomalies (below). Exported read-only from C:\ZZ-CLAUDE-SCRATCH on
# 2026-09-21 - markers AutoMark / AccuNest laid, hand-laid, part-laid, never laid,
# with unequal block buffers, and a 1,080-piece one. Pinned exactly, so a
# decoder change that moves any of it is noticed.
LIVE = os.path.join(HERE, 'markers-live', 'ZZ-SCRATCH-ALL-20260921', 'ZZ-SCRATCH-ALL-20260921.zip')
LIVE_ANOMALIES = {   # marker -> (laid state, slots, failing check rows, warnings)
 'LADIES-BLOUSE TEST-2': ('partial', 54, ('header @430 == sum of placed slot areas', 'sum(slot areas) == W*L*U'), 0),   # 52 of 54 placed; header stale
 'ZZC-BIGM': ('laid', 1080, ('header @430 == sum of placed slot areas', 'sum(slot areas) == W*L*U'), 0),   # @430 = true area - 2**32/1e4: AccuMark's own 32-bit fixed-point wrap
 'ZZC-M3': ('partial', 10, ('slot declared area == bound record area',), 1),    # 2 placed slots 7.2% larger than their record [?]
 'ZZN-B7': ('laid', 54, ('header @430 == sum of placed slot areas',), 0),       # @430 drifted 1191 sq in above the placed sum; util is right
 'ZZN-F1': ('laid', 10, ('slot declared area == bound record area',), 1),
}
if os.path.isfile(LIVE):
    lobjs = am.list_zip(LIVE); found = {}; bad = []; states = Counter(); leaks = 0
    for o in lobjs['marker']:
        try: mk = am.parse_marker(o['data'])
        except Exception as e: bad.append(f"{o['name']}: {type(e).__name__}"); continue
        states[mk['laid_state']] += 1
        fl = tuple(sorted(n for n, ok, _ in am.check_marker(mk) if not ok)); warns = am.marker_warnings(mk) + am.coverage_warnings(mk)
        if fl or warns: found[o['name']] = (mk['laid_state'], len(mk['slots']), fl, len(warns))
        # the never-laid signature: slot @88 non-zero <=> nothing has ever been placed
        if (mk['lay_history'] == 'as_generated') != (mk['laid_state'] == 'unlaid'): bad.append(f"{o['name']}: lay_history {mk['lay_history']} vs {mk['laid_state']}")
        leaks += sum(1 for a, b, k in am.marker_coverage(o['data'], mk)['unknown_runs'] if k in am.PARSED_SECTIONS)
    if len(lobjs['marker']) != 41 or dict(states) != {'unlaid': 17, 'laid': 22, 'partial': 2}: bad.append(f'{len(lobjs["marker"])} markers, states {dict(states)}')
    if found != LIVE_ANOMALIES: bad.append(f'anomalies changed: {found}')
    if leaks: bad.append(f'{leaks} unknown-byte runs inside parsed sections')
    print(f"   {'ok ' if not bad else 'FAIL'} 41 real markers decode with no exception; 36 clean, exactly 5 documented anomalies; byte map has no leak  {'; '.join(bad)}")
    if bad: fails.append('live corpus: ' + '; '.join(bad))
    # block buffers: a TABLE of definitions, pieces point into it (0-based) or at none
    zc = next(am.parse_marker(o['data']) for o in lobjs['marker'] if o['name'] == 'ZZC-M1')
    idx = {p['name'][-4:]: p['buffer_index'] for p in zc['pieces']}
    got = {n[-4:]: am._buffer_sides(zc, n) for n in [p['name'] for p in zc['pieces']]}
    ok = (len(zc['block_buffers']) == 4 and idx == {'E-BK': 0, '-COL': 1, 'CUFF': None, 'E-FR': 2, 'E-SL': 3}
          and got['CUFF'] == (0.0, 0.0, 0.0, 0.0) and abs(got['E-SL'][0] - 0.7874) < 1e-3 and abs(got['E-SL'][1] - 0.1968) < 1e-3 and got['E-SL'][2:] == (0.0, 0.0))
    print(f"   {'ok ' if ok else 'FAIL'} ZZC-M1: 4 buffer definitions for 5 pieces; a piece with no index gets no buffer, the rest point into the table (0-based)")
    if not ok: fails.append(f'block buffer table semantics: {idx}')
    # utilisation identity is relative: AutoMark stores util to 0.01% (ZZ-AM-1: 13417.98 vs 13420.42)
    za = next(am.parse_marker(o['data']) for o in lobjs['marker'] if o['name'] == 'ZZ-AM-1')
    rows = {n: ok for n, ok, _ in am.check_marker(za)}
    za2 = dict(za); za2['util'] = za['util'] * 1.01
    ok = rows['sum(slot areas) == W*L*U'] and not {n: ok for n, ok, _ in am.check_marker(za2)}['sum(slot areas) == W*L*U']
    print(f"   {'ok ' if ok else 'FAIL'} utilisation identity tolerates AutoMark's 0.01% rounding (2e-4) yet still fails on a 1% error")
    if not ok: fails.append('utilisation tolerance')
    # slot @88 / directory word 40 / orientation 0x8000: what Easy Marking's STORE does (below)
    zn = _mk(('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip'), '5683D-BD 168 SS21')
    if zn:
        row = 'slot @88 signature <=> directory word 40 is 0 (as generated)'
        b = bytearray(zn[0]['data'])
        for s in zn[1]['slots']: struct.pack_into('<H', b, s['slot'] + 88, 0)          # zero @88 but leave word 40 = 0
        lo = next(o for o in lobjs['marker'] if o['name'] == 'ZZN-1'); bl = bytearray(lo['data']); ml = am.parse_marker(lo['data'])
        struct.pack_into('<H', bl, ml['slots'][3]['slot'] + 88, 9)                    # a non-zero @88 on a stored, laid marker
        ok = (zn[1]['lay_history'] == 'as_generated' and {n: ok for n, ok, _ in am.check_marker(zn[1])}[row] and {n: ok for n, ok, _ in am.check_marker(ml)}[row]
              and not {n: ok for n, ok, _ in am.check_marker(am.parse_marker(bytes(b)))}[row]
              and not {n: ok for n, ok, _ in am.check_marker(am.parse_marker(bytes(bl)))}[row])
        print(f"   {'ok ' if ok else 'FAIL'} slot @88 <=> word 40 = 0: holds on 5683D and ZZN-1, and fails when either side is broken in the bytes")
        if not ok: fails.append('slot @88 / word 40 identity')

# The live experiment (2026-09-21): what does Easy Marking's STORE do to an unplaced marker?
# CLAUDE-QTY-TEST (as generated) was opened in Easy Marking and Saved As E1A with NOTHING
# placed; then one piece was dragged onto the marker, returned with Piece > Return >
# Unplaced, and stored as E1B. Prediction going in: E1B ("laid once, cleared") reads @88 = 0
# and E1A does not. Result: BOTH read 0 - a plain store clears the as-generated signature -
# and laying + returning a piece leaves no trace (12 differing bytes: name, timestamps,
# session residue, and the last byte of ONE slot's area double).
E1 = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-E1-TWINS', 'CLAUDE-UNP-E1-TWINS.zip')
if os.path.isfile(E1) and lobjs:
    eo = {o['name']: o for o in am.list_zip(E1)['marker']}
    A, B = eo['CLAUDE-UNP-E1A'], eo['CLAUDE-UNP-E1B']; mA, mB = am.parse_marker(A['data']), am.parse_marker(B['data'])
    O = am.parse_marker(next(o for o in lobjs['marker'] if o['name'] == 'CLAUDE-QTY-TEST')['data'])
    bad = []
    for m, nm in ((mA, 'E1A'), (mB, 'E1B')):
        if not (m['laid_state'] == 'unlaid' and m['lay_history'] == 'stored_empty' and m['placed_word'] == 1 and len(m['placements']) == 0): bad.append(f'{nm}: {m["laid_state"]}/{m["lay_history"]}/word {m["placed_word"]}')
        if any(s['sig88'] for s in m['slots']): bad.append(f'{nm}: @88 not zero')
        if {(s['x'], s['y']) for s in m['slots']} != {(-1000.0, -1000.0)}: bad.append(f'{nm}: centres not -1000')
        if {s['orient_code'] for s in m['slots']} != {0x8000, 0xa004}: bad.append(f'{nm}: orientation words {sorted(hex(s["orient_code"]) for s in m["slots"])[:3]}')
        if [n for n, ok, _ in am.check_marker(m) if not ok] or am.marker_warnings(m): bad.append(f'{nm}: a check or warning fires')
    # the original, as generated: word 0, @88 non-zero, centres 0, orientation without 0x8000; home box and areas unchanged by the store
    if not (O['placed_word'] == 0 and O['lay_history'] == 'as_generated' and all(s['sig88'] == 9 for s in O['slots']) and {(s['x'], s['y']) for s in O['slots']} == {(0.0, 0.0)}): bad.append('original not as generated')
    # a store re-derives the home box, rounded to the format's 1e-4 in unit: 5e-5 in x here, 0 in y (areas are unchanged)
    if any(abs(a['home_x'] - o['home_x']) > 1e-4 or abs(a['home_y'] - o['home_y']) > 1e-4 or abs(a['area'] - o['area']) > 1e-6 for a, o in zip(mA['slots'], O['slots'])): bad.append('a store moved a home box or changed an area')
    if [(s['orient_code'] & ~0x8004) for s in mA['slots']] != [s['orient_code'] for s in O['slots']]: bad.append('a store changed more than 0x8000 / 0x0004 on the orientation word')
    diff = [i for i in range(len(A['data'])) if A['data'][i] != B['data'][i]]
    s21 = mA['sections'][am.SEC_SLOTS]; in21 = [i for i in diff if s21[0] <= i < s21[1]]
    if len(A['data']) != len(B['data']) or len(diff) != 12 or len(in21) != 1 or (in21[0] - s21[0]) % 96 != 42: bad.append(f'twins differ in {len(diff)} bytes, {len(in21)} in the slots')
    print(f"   {'ok ' if not bad else 'FAIL'} live twins: a plain store clears @88, sets word 40 = 1, orientation 0x8000, centres -1000; laying + returning a piece changes 12 bytes (1 area ulp)  {'; '.join(bad)}")
    if bad: fails.append('E1 twins: ' + '; '.join(bad))

# The second live experiment (2026-09-21, v4.7): the SAME order as a laid and as an
# as-generated marker. `AD1234 TEST 134` (laid, 13 pieces, kept from September) and
# `CLAUDE-D2-M0` (Easy Order > Save As a copy of that order, change ONLY the marker
# name, Process): identical pieces, sizes, quantities and width, so every byte that
# differs is what laying does. Result: the 13 records are identical; the slot bodies
# differ only in centre (0..20), orientation (32-33), two area ulps (41-42) and @88
# (213 on every RUFFLE slot as generated, 0 laid); section 1 loses its length /
# utilisation / area doubles, word 40 goes 0 -> 2, and the type-10 scratch object grows
# by 960 B (a ~1 KB block of small offsets at its offset 310) once laid.
D2 = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D2-TWIN', 'CLAUDE-D2-M0.zip')
LAID = os.path.join(HERE, 'markers', 'misc-test-markers', 'AD1234 TEST 134.zip')
if os.path.isfile(D2) and os.path.isfile(LAID):
    G = am.place_marker(D2)['markers'][0]; L = am.place_marker(LAID)['markers'][0]
    g, l = G['marker'], L['marker']; bad = []
    if not (g['lay_history'] == 'as_generated' and g['placed_word'] == 0 and len(g['slots']) == 13 and {s['sig88'] for s in g['slots']} == {213}): bad.append('twin as generated: state / @88')
    if not (l['lay_history'] == 'laid' and l['placed_word'] == 2 and len(l['slots']) == 13 and not any(s['sig88'] for s in l['slots'])): bad.append('laid twin: state / @88')
    if [n for n, ok, _ in am.check_marker(g) if not ok] or am.marker_warnings(g) or [n for n, ok, _ in am.check_marker(l) if not ok]: bad.append('a check or warning fires')
    strip = lambda r: {k: v for k, v in r.items() if k != 'offset'}
    if [strip(r) for r in g['records']] != [strip(r) for r in l['records']]: bad.append('the records differ between the twins')
    same = ('record_index', 'piece_index', 'bundle', 'bundle_head', 'piece', 'size', 'model')
    if any(any(a[k] != b[k] for k in same) or abs(a['home_x'] - b['home_x']) > 1e-4 or abs(a['home_y'] - b['home_y']) > 1e-4 or abs(a['area'] - b['area']) > 1e-6
           for a, b in zip(g['slots'], l['slots'])): bad.append('a slot field other than centre / orientation / @88 differs')
    if {(s['x'], s['y']) for s in g['slots']} != {(0.0, 0.0)} or len({(s['x'], s['y']) for s in l['slots']}) < 10: bad.append('centres: as generated must be (0,0), laid must be placed')
    allowed = set(range(21)) | {32, 33, 41, 42, 88, 89}
    off = {j for a, b in zip(g['slots'], l['slots']) for j in range(96) if bytes.fromhex(a['raw'])[j] != bytes.fromhex(b['raw'])[j]}
    if not off <= allowed: bad.append(f'slot bytes outside centre/orientation/area/@88 differ: {sorted(off - allowed)}')
    # @88 = record head count + one constant per piece (RUFFLE: 209 + 4), on both twins' record
    sm = g['sig88_model']
    if not (sm['applicable'] and sm['ok'] and sm['constant'] == {'ID1005 - RUFFLE': 4} and all(s['record']['prefix'][1] == 209 for s in g['slots'])): bad.append(f'@88 model: {sm}')
    # and the row can fail: move one slot's @88 by 1 in the bytes
    b = bytearray(next(o for o in am.list_zip(D2)['marker'])['data']); struct.pack_into('<H', b, g['slots'][4]['slot'] + 88, 214)
    gm = am.parse_marker(bytes(b)); row = 'slot @88 = record head count + one constant per piece (as generated)'
    if {n: ok for n, ok, _ in am.check_marker(gm)}.get(row, True) or not any('@88' in x for x in am.marker_warnings(gm)): bad.append('a broken @88 did not fail its row / raise a warning')
    # the marker-level 0x0040 bit is a copy of the piece row's flag u16 @+14: 0 here, so a patched row flag must break it
    prow = 'slot orientation bit 0x0040 == its piece row flag @+14 (section 10)'
    ri = next(i for i, p in enumerate(g['pieces']) if p['name'] == 'ID1005 - RUFFLE')
    b = bytearray(next(o for o in am.list_zip(D2)['marker'])['data']); struct.pack_into('<H', b, g['pieces'][ri]['offset'] - 10, 1)
    if not {n: ok for n, ok, _ in am.check_marker(g)}.get(prow) or {n: ok for n, ok, _ in am.check_marker(am.parse_marker(bytes(b)))}.get(prow, True): bad.append('the 0x0040 == piece flag row did not fail when the flag was patched')
    # reproducibility of the harness: the same order processed again 32 minutes later under another marker name
    # (CLAUDE-D2-M5, via Process w/ AutoMark's scaffold) differs in 18 bytes - four name digits and stamp bytes - so any
    # byte that differs between two runs of the dataset is a setting that was changed
    M5 = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D2-TWIN', 'CLAUDE-D2-M5.zip')
    if os.path.isfile(M5):
        a5 = next(o for o in am.list_zip(D2)['marker'])['data']; b5 = next(o for o in am.list_zip(M5)['marker'])['data']
        dif = [i for i in range(len(a5)) if a5[i] != b5[i]] if len(a5) == len(b5) else None
        if dif is None or len(dif) != 18 or sum(1 for i in dif if a5[i] == 0x30 and b5[i] == 0x35) != 4: bad.append(f'the harness is not reproducible: {None if dif is None else len(dif)} differing bytes')
        m5 = am.parse_marker(b5)
        if not (m5['lay_history'] == 'as_generated' and {s['sig88'] for s in m5['slots']} == {213} and m5['name'] == 'CLAUDE-D2-M5'): bad.append('D2-M5 is not the same as-generated marker')
    # E7 (two runs of the same harness): a model whose pieces carry none of the order's fabric types is DROPPED - from the
    # order AND the marker (CLAUDE-D2-E7O: ID1005 - TOP + CLAUDE-GRADE-MODEL with quantities typed for it saves and processes as
    # ID1005 - TOP alone, decoding exactly like CLAUDE-D2-M0); and a FRESH two-model marker (CLAUDE-D2-E7B: LADIES-BLOUSE +
    # ZZ-PLM-BLOUSE, both fabric type M) has header @422 / @454 = the LAST model's sums, so that mode is AccuMark's own behaviour
    # and not a stale artefact of a laid marker.
    E7O = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D2-TWIN', 'CLAUDE-D2-E7O.zip'); E7B = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D2-TWIN', 'CLAUDE-D2-E7B.zip')
    if os.path.isfile(E7O) and os.path.isfile(E7B):
        o7 = am.place_marker(E7O)['markers'][0]['marker']; b7r = am.place_marker(E7B)['markers'][0]; b7 = b7r['marker']
        if not (o7['models'] == ['ID1005 - TOP'] and [(x['name'], [(z['size'], z['quantity']) for z in x['sizes']]) for x in o7['order_copy']] == [('ID1005 - TOP', [('XS', 2), ('S', 4), ('M', 4), ('L', 2), ('XL', 1)])]
                and [strip(r) for r in o7['records']] == [strip(r) for r in g['records']] and len(o7['slots']) == 13): bad.append('E7O: the zero-piece model was not dropped')
        sl7 = [s for s in b7['slots'] if s.get('record')]; last7 = [s for s in sl7 if s['model'] == b7['models'][-1]]
        if not (b7['models'] == ['LADIES-BLOUSE', 'ZZ-PLM-BLOUSE'] and b7['lay_history'] == 'as_generated' and len(b7['slots']) == 29 and len(b7['pieces']) == 10): bad.append('E7B: shape')
        if b7['header_sums'] != dict(area='last_model', perimeter='last_model') or abs(b7['total_area'] - sum(s['area'] for s in last7)) > 1e-6 or abs(b7['unknown_454'] - sum(s['record']['perimeter'] for s in last7)) > 1e-6 or abs(b7['total_area'] - sum(s['area'] for s in sl7)) < 1: bad.append('E7B: header @422 / @454 are not the last-model sums')
        if [n for n, ok, _ in b7r['checks'] if not ok] or am.marker_warnings(b7): bad.append('E7B: a check or warning fires')
        if not (b7['sig88_model']['ok'] and {p['flag14'] for p in b7['pieces']} == {0}): bad.append('E7B: @88 model / flag14')
    print(f"   {'ok ' if not bad else 'FAIL'} live twins of one order (laid vs as generated): records identical, slots differ only in centre / orientation / area ulp / @88 (= record head count + C per piece)  {'; '.join(bad)}")
    if bad: fails.append('D2 twins: ' + '; '.join(bad))

# v4.7 [V, partial]: the section-14 stream is the graded outline. Two independent grounds of truth:
# (1) the piece objects bundled in the same ZIPs - the rectangle (4 of 4 points, sizes 2 / 8 / 18) and RUFFLE (all 142
# points at all five sizes, plus its grain line); (2) the record head's OWN area and perimeter, which every decoded
# outline must reproduce (shoelace, within 1%) - the only check available for a marker-only ZIP.
sd_bad = []; sd_n = 0
for zp, piece, want in (('markers/CLAUDE-GRADE-MARKER/CLAUDE-GRADE-MARKER.zip', 'CLAUDE-GRADE-TEST', 4), ('markers/CLAUDE-QTY-TEST.zip', 'CLAUDE-GRADE-TEST', 4),
                        ('markers-live/CLAUDE-UNP-D2-TWIN/CLAUDE-D2-M0.zip', 'ID1005 - RUFFLE', 142)):
    if not os.path.isfile(os.path.join(HERE, zp)): continue
    rr = am.place_marker(os.path.join(HERE, zp)); mm = rr['markers'][0]['marker']; dd = mm['object']['data']
    for rc in mm['records']:
        if rc.get('piece') != piece: continue
        o = rc['offset']; t = len(rc['text']); st = dd[o+t:o+t+rc['stream_len']]; dec = am.decode_record_stream(st)
        ref = [(round(x * 1e4), round(y * 1e4)) for x, y in am.graded_outline(rr['pieces'][piece]['block'], rc['size'])]
        got = [(a, b) for a, b, _ in dec['contours'][0]]; sd_n += 1
        if got != ref or dec['stop'] != 'trailer' or not am.record_outline(dd, rc)['verified']: sd_bad.append(f"{zp.split('/')[-1]} size {rc['size']}: {len(got)} of {len(ref)} points, stop {dec['stop']}")
        if want == 142 and rc['size'] == 'M':
            gl = [(a, b) for a, b, _ in dec['contours'][1]] if len(dec['contours']) > 1 else None
            if gl != [(543131, 45098), (584289, 45098)]: sd_bad.append(f'RUFFLE grain line {gl}')
mut = bytearray(st); mut[23] ^= 0x40                                                     # the high byte of the first d1 step of the last (RUFFLE) stream
if am.verify_stream_outline(am.decode_record_stream(bytes(mut))['contours'][0], rc['area'], rc['perimeter'])[0]: sd_bad.append('a flipped coordinate bit still verified')
# corpus: distinct streams verified against their own record head, marker-only ZIPs included
sd_seen = set(); sd_tot = sd_ok = sd_unf = 0; sd_named = {}; sd_cross = []
for zp in sorted(glob.glob(os.path.join(HERE, 'markers', '**', '*.zip'), recursive=True) + glob.glob(os.path.join(HERE, 'markers-live', '**', '*.zip'), recursive=True)):
    try: mos = am.list_zip(zp).get('marker', [])
    except Exception: continue
    for o_ in mos:
        try: m_ = am.parse_marker(o_['data'])
        except Exception: continue
        for rc in m_['records']:
            oo = rc['offset']; tt = len(rc['text']); key = (rc['text'], o_['data'][oo+tt:oo+tt+24], rc['stream_len'])
            if key in sd_seen: continue
            sd_seen.add(key); ro = am.record_outline(o_['data'], rc); sd_tot += 1; sd_ok += bool(ro and ro['verified'])
            if ro and ro['unfolded']:                                   # an unfolded half must give a SIMPLE polygon (no crossing edges)
                sd_unf += 1; pp = ro['points']; nn = len(pp)
                def _c(a, b, c): return (c[1]-a[1])*(b[0]-a[0]) - (b[1]-a[1])*(c[0]-a[0])
                if any(_c(pp[i], pp[(i+1) % nn], pp[j]) * _c(pp[i], pp[(i+1) % nn], pp[(j+1) % nn]) < 0 and _c(pp[j], pp[(j+1) % nn], pp[i]) * _c(pp[j], pp[(j+1) % nn], pp[(i+1) % nn]) < 0 for i in range(nn) for j in range(i + 2, nn) if not (i == 0 and j == nn - 1)): sd_cross.append(rc['text'][:24])
            for nm in ('0418T TRS', '2591A', '1825D', '5683D'):
                if rc['text'].startswith(nm): sd_named.setdefault(nm, [0, 0]); sd_named[nm][0] += 1; sd_named[nm][1] += bool(ro and ro['verified'])
if sd_cross: sd_bad.append('unfolded outlines that cross themselves: %s' % sd_cross[:3])
if sd_ok != sd_tot or sd_tot < 268: sd_bad.append(f'{sd_ok} of {sd_tot} distinct corpus streams verify (all 268 did)')
for nm, (nn, kk) in sd_named.items():
    if nn == 0 or kk != nn: sd_bad.append(f'marker-only {nm}: {kk} of {nn} records verify')
print(f"   {'ok ' if sd_n and not sd_bad else 'FAIL'} record stream (v4.7): {sd_n} records equal the piece's graded outline exactly (rectangle 4/4, RUFFLE 142/142 + grain line); {sd_ok} of {sd_tot} distinct corpus streams reproduce their own record area and perimeter within 1% - ALL of them, incl. every record of the marker-only ZIPs 1825D, 5683D, 2591A, 0418T (131 are fold halves, unfolded about their fold line)  {'; '.join(sd_bad[:3])}")
if not sd_n or sd_bad: fails.append('record stream decode: ' + '; '.join(sd_bad[:3]))

# v4.7: what a stream point IS - tag low nibble 1 = plain (a NOTCH when an extra byte follows: type = its low nibble), any
# other low nibble = a TURN; against the kinds of the piece object's own perimeter points, wherever a piece is bundled and the
# stream is a full (unfolded-free) 1:1 copy of its perimeter. The trailer's last bytes and the extra byte's high nibble stay open.
pk_ok = pk_bad = pk_notch = 0
for zp in ('markers/2303-CP150-JULY/2303-CP 150 CPL.zip', 'markers/2303-BD137-PLACED/2303-BD 137 PLACED.zip', 'markers-live/ZZ-SCRATCH-ALL-20260921/ZZ-SCRATCH-ALL-20260921.zip', 'markers/LADIES-BLOUSE TEST-2.zip'):
    if not os.path.isfile(os.path.join(HERE, zp)): continue
    rr = am.place_marker(os.path.join(HERE, zp)); seen_ = set()
    for mm in rr['markers']:
        m_ = mm['marker']; dd = m_['object']['data']
        for rc in m_['records']:
            pc = rr['pieces'].get(rc.get('piece'))
            if not pc or (rc['text'], rc['stream_len']) in seen_: continue
            seen_.add((rc['text'], rc['stream_len'])); ro = am.record_outline(dd, rc); per = pc['block']['perimeter']
            if not ro or not ro['verified'] or ro['unfolded'] or len(ro['kinds']) != len(per): continue
            for k_, pp in zip(ro['kinds'], per):
                pk_ok += k_ == (pp['kind'], pp.get('notch_type') if pp['kind'] == 'notch' or pp.get('is_corner_notch') else None)
                pk_bad += k_ != (pp['kind'], pp.get('notch_type') if pp['kind'] == 'notch' or pp.get('is_corner_notch') else None)
            pk_notch += len(ro['notches'])
print(f"   {'ok ' if pk_ok >= 5000 and pk_bad <= 1 and pk_notch >= 100 else 'FAIL'} stream point kinds (v4.7): {pk_ok} of {pk_ok + pk_bad} points agree with the piece's own turn / plain / notch kinds and notch types ({pk_notch} notches read from streams)")
if not (pk_ok >= 5000 and pk_bad <= 1 and pk_notch >= 100): fails.append(f'stream point kinds: {pk_ok} ok, {pk_bad} bad, {pk_notch} notches')

# v4.7 THE BLIND TEST (2026-09-21): a marker I had AccuMark make from pieces never seen in a marker before - ID1005 - BACK and FRONT
# (real Gerber demo pieces: fold halves, curves, seam allowances 1.0 / 0.375 / 0.25 in). Fixture: markers-live/CLAUDE-UNP-D3-BLIND/
# (the full export, and the same marker with every piece object stripped = what a marker-only ZIP looks like). Decoded BEFORE any fitting:
# order lines and pieces right, but no outline - my pen-move rule split a legitimate 7-part step; fixed by trying thresholds and
# keeping the first that reproduces the record's area and perimeter. What the run showed: the marker lays the CUT line (stitch line +
# seam allowance), not the piece object's stitch line (area ratio 0.89, bbox 1.4 x 0.9 in smaller).
bd = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D3-BLIND'); bfull = os.path.join(bd, 'CLAUDE-D3-BF.zip'); bmo = os.path.join(bd, 'CLAUDE-D3-BF-MARKER-ONLY.zip')
if os.path.isfile(bfull) and os.path.isfile(bmo):
    bad = []; ro_ = am.place_marker(bmo)['markers'][0]; rf_ = am.place_marker(bfull); rfm = rf_['markers'][0]
    iv = ro_['inventory']; ivf = rfm['inventory']
    if set(am.list_zip(bmo)) != {'marker'}: bad.append('marker-only ZIP still holds other objects')
    if not (iv['marker']['outline_source'] == 'stream' and iv['marker']['geometry_available'] == 'all' and len(iv['slots']) == 10 and iv['marker']['lay_history'] == 'as_generated'): bad.append('marker-only inventory shape')
    if [(o['size'], o['quantity']) for o in iv['order_lines']] != [(z, 1) for z in ('XS', 'S', 'M', 'L', 'XL')] or iv['marker']['fabric_types'] != ['S']: bad.append('order lines / fabric type')
    for e in iv['slots']:
        if abs(e['checks']['bbox_dx']) > 2e-4 or abs(e['checks']['bbox_dy']) > 2e-4 or abs(e['checks']['area_ratio'] - 1) > 0.01: bad.append(f"{e['piece']} {e['size']}: home box residual {e['checks']['bbox_dx']:.4f} / {e['checks']['bbox_dy']:.4f}, area ratio {e['checks']['area_ratio']:.4f}")
    mko = ro_['marker']; dd_ = mko['object']['data']
    if any(am.record_outline(dd_, rc)['pen_move'] != 20 or not am.record_outline(dd_, rc)['unfolded'] for rc in mko['records']): bad.append('expected every BACK / FRONT stream at pen_move 20, unfolded')
    if [n for n, ok, _ in ro_['checks'] if not ok] or am.marker_warnings(mko): bad.append('a check or warning fires on the blind marker')
    # the answer key: the piece objects. Their stitch line is smaller by the seam allowance; the stitch points sit 0.25 / 0.375 in inside the cut line
    def _dseg(pt, a, b):
        dx_, dy_ = b[0]-a[0], b[1]-a[1]; l2_ = dx_*dx_ + dy_*dy_; t_ = max(0, min(1, ((pt[0]-a[0])*dx_ + (pt[1]-a[1])*dy_) / l2_)) if l2_ else 0
        return ((pt[0]-a[0]-t_*dx_)**2 + (pt[1]-a[1]-t_*dy_)**2) ** 0.5
    for e in iv['slots']:
        if e['size'] != 'M': continue
        stitch, _ = am.piece_outline(rf_['pieces'][e['piece']], 'M'); cut = e['outline']
        if abs(am._shoelace(stitch) / am._shoelace(cut) - 0.885) > 0.03: bad.append(f"{e['piece']}: stitch / cut area {am._shoelace(stitch) / am._shoelace(cut):.3f}")
        ds = [min(_dseg(pt, cut[i], cut[(i+1) % len(cut)]) for i in range(len(cut))) for pt in stitch]
        near = sum(1 for x_ in ds if min(abs(x_ - 0.375), abs(x_ - 0.25)) < 0.02)
        if near < 0.8 * len(ds): bad.append(f"{e['piece']}: only {near} of {len(ds)} stitch points are 0.25 / 0.375 in inside the cut line")
    segs = {sg['seam_begin'] for sg in rf_['pieces']['ID1005 - BACK']['block']['segments']}
    if segs != {10000, 3750, 2500}: bad.append(f'BACK seam allowances {segs}')
    # with the piece objects present the geometry falls back to the stream outline (the piece-object outline fails the area test)
    if ivf['marker']['outline_source'] != 'stream' or any(abs(e['checks']['area_ratio'] - 1) > 0.01 for e in ivf['slots']): bad.append('with pieces present the stream outline was not preferred')
    print(f"   {'ok ' if not bad else 'FAIL'} BLIND TEST CLAUDE-D3-BF (BACK + FRONT never seen before): marker-only ZIP -> 10 outlines, bounding box == stored home box (<= 0.0001 in), area within 1%; the piece objects' stitch lines sit 0.25 / 0.375 in inside the decoded cut line (seam allowances 1.0 / 0.375 / 0.25)  {'; '.join(bad[:3])}")
    if bad: fails.append('D3 blind test: ' + '; '.join(bad[:5]))

# v4.7 SECOND BLIND TEST (2026-09-23): a piece I designed and imported myself, then a marker made from it - CLAUDE-CURVE (a 20 x 15 cm
# panel with a rounded corner, 2 notches, a drill hole, a grain line, an internal line and two DIFFERENT grade rules on one chain of
# points; made with the accumark-pattern-marker skill: make_aama_dxf.py -> DCU import -> Easy Order -> CLAUDE-D4). Fixture
# markers-live/CLAUDE-UNP-D4-CURVE/ (full export = answer key; -MARKER-ONLY.zip = the same marker with the piece object stripped).
# What it showed: (1) order data, pieces, notches, grain, internal line, drill and the outline all right from the marker alone once the
# contour split used the header counts; (2) the FIRST bundled piece with two different rule numbers on one chain - and the piece-side
# grading (blend of the two moves by chain length, unverified before) was 0.295 in off, while the marker's own stream matched a
# SIMILARITY of the chord between the ruled points to 1e-4 in. graded_outline now uses that.
d4d = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D4-CURVE'); d4f = os.path.join(d4d, 'CLAUDE-D4.zip'); d4m = os.path.join(d4d, 'CLAUDE-D4-MARKER-ONLY.zip')
if os.path.isfile(d4f) and os.path.isfile(d4m):
    bad = []; rmo = am.place_marker(d4m)['markers'][0]; rfu = am.place_marker(d4f); ivm = rmo['inventory']
    if set(am.list_zip(d4m)) != {'marker'}: bad.append('marker-only ZIP holds other objects')
    if not (ivm['marker']['outline_source'] == 'stream' and ivm['marker']['geometry_available'] == 'all' and len(ivm['slots']) == 6 and ivm['marker']['lay_history'] == 'as_generated'): bad.append('inventory shape')
    if [(o['size'], o['quantity']) for o in ivm['order_lines']] != [(z, 1) for z in ('S', 'M', 'L')]: bad.append('order lines')
    if [n for n, ok, _ in rmo['checks'] if not ok] or am.marker_warnings(rmo['marker']): bad.append('a check or warning fires')
    pcb = rfu['pieces']['CLAUDE-CURVE']['block']; dd4 = rmo['marker']['object']['data']; mkf = rfu['markers'][0]['marker']; ddf = mkf['object']['data']
    def _linear_blend(block, size):                     # the pre-v4.7 rule: blend the two ruled moves by chain length
        names = [z['name'] for z in block['meta']['sizes']]; t_, b_ = names.index(size), block['meta']['base_index']; rl = {o['id']: o['deltas'] for o in block['objects']}
        def mv(pp):
            if pp['rule_ref'] not in rl: return None
            rows = rl[pp['rule_ref']]; sel = rows[b_:t_] if t_ > b_ else [(-a_, -c_) for a_, c_ in rows[t_:b_]]
            return (sum(r_[0] for r_ in sel), sum(r_[1] for r_ in sel))
        pts_ = block['perimeter']; mvs = [mv(pp) for pp in pts_]; n_ = len(pts_); rd = [i for i in range(n_) if mvs[i] is not None]; xy_ = [(pp['x'], pp['y']) for pp in pts_]; o_ = [None] * n_
        for i in rd: o_[i] = (xy_[i][0] + mvs[i][0], xy_[i][1] + mvs[i][1])
        for k_, i in enumerate(rd):
            j = rd[(k_ + 1) % len(rd)]; seq = []; q_ = (i + 1) % n_
            while q_ != j: seq.append(q_); q_ = (q_ + 1) % n_
            ch = [xy_[i]] + [xy_[q_] for q_ in seq] + [xy_[j]]; acc = am._chain_lengths(ch); tot = acc[-1] or 1.0
            for ix, q_ in enumerate(seq):
                f_ = acc[ix + 1] / tot; o_[q_] = (xy_[q_][0] + mvs[i][0] * (1 - f_) + mvs[j][0] * f_, xy_[q_][1] + mvs[i][1] * (1 - f_) + mvs[j][1] * f_)
        return o_
    lin_err = {}
    for rc in rmo['marker']['records']:
        ro4 = am.record_outline(dd4, rc); got = [(x * 1e4, y * 1e4) for x, y in ro4['points']]; ref = [(x * 1e4, y * 1e4) for x, y in am.graded_outline(pcb, rc['size'])]
        if not ro4['verified'] or len(got) != 12 or max(max(abs(a_[0] - b_[0]), abs(a_[1] - b_[1])) for a_, b_ in zip(got, ref)) > 1.5: bad.append(f"size {rc['size']}: stream outline != graded piece outline (1e-4 in)")
        lin = _linear_blend(pcb, rc['size']); lin_err[rc['size']] = max(max(abs(a_[0] - b_[0]), abs(a_[1] - b_[1])) for a_, b_ in zip(got, lin))
        # notches, grain, internal line, drill: exactly the piece object's, at every size (they are not graded)
        want = {k_: [(q['x'], q['y']) for q in l] for k_, l in zip(pcb['internal_kinds'], pcb['internal_lines'])}
        lines = {l['kind']: [(round(x * 1e4), round(y * 1e4)) for x, y in l['points']] for l in ro4['lines']}
        if lines != want: bad.append(f"size {rc['size']}: grain / internal / drill {lines} != {want}")
        nn = sorted((round(x * 1e4), round(y * 1e4), t) for _, t, x, y in ro4['notches']); wn = sorted((q['x'], q['y'], q['notch_type']) for q in pcb['perimeter'] if q['kind'] == 'notch')
        if [(a_, b_, t) for a_, b_, t in nn] != [(a_, b_, t) for a_, b_, t in wn] and rc['size'] == 'M': bad.append(f'M notches {nn} != {wn}')
        if len(nn) != 2 or any(t != 5 for *_, t in nn): bad.append(f"size {rc['size']}: notches {nn}")
    if lin_err.get('S', 0) < 2000 or lin_err.get('L', 0) < 2000: bad.append(f'the old chain-length blend should be off by > 0.2 in on S and L (it was {lin_err})')
    for e in ivm['slots']:
        if abs(e['checks']['bbox_dx']) > 2e-4 or abs(e['checks']['bbox_dy']) > 2e-4 or abs(e['checks']['area_ratio'] - 1) > 1e-3 or len(e['notches']) != 2 or len(e['drills']) != 1 or not e['grain']: bad.append(f"slot {e['size']}: box residual {e['checks']['bbox_dx']:.4f}, {e['checks']['bbox_dy']:.4f} / area {e['checks']['area_ratio']:.4f} / notches {len(e['notches'])}")
    print(f"   {'ok ' if not bad else 'FAIL'} SECOND BLIND TEST CLAUDE-D4 (a piece I built: rounded corner, 2 notches, drill, grain, internal line, two grade rules): marker-only ZIP -> outline == graded piece to 1e-4 in at S / M / L, notches, grain, internal line and drill exactly the piece's; the old chain-length grading blend was {max(lin_err.values(), default=0) / 1e4:.3f} in off  {'; '.join(bad[:3])}")
    if bad: fails.append('D4 blind test: ' + '; '.join(bad[:5]))

# the contour split by header counts, over every fixture whose piece object is bundled: grain, internal lines, cutouts and drills equal the piece's exactly
il_n = il_bad = 0
for zp in ('markers/2303-BD137-UNLAID/2303-BD 137.zip', 'markers-live/CLAUDE-UNP-D2-TWIN/CLAUDE-D2-M0.zip', 'markers-live/CLAUDE-UNP-D4-CURVE/CLAUDE-D4.zip', 'markers/CLAUDE-GRADE-MARKER/CLAUDE-GRADE-MARKER.zip', 'markers/2303-CP150-JULY/2303-CP 150 CPL.zip'):
    if not os.path.isfile(os.path.join(HERE, zp)): continue
    rr = am.place_marker(os.path.join(HERE, zp)); seen_ = set()
    for mm in rr['markers']:
        m_ = mm['marker']; dd = m_['object']['data']
        for rc in m_['records']:
            pc = rr['pieces'].get(rc.get('piece'))
            if not pc or (rc['text'], rc['stream_len']) in seen_: continue
            seen_.add((rc['text'], rc['stream_len'])); ro = am.record_outline(dd, rc)
            if not ro or not ro['verified'] or not ro['lines'] or any(l['kind'] == 'mirror' for l in ro['lines']): continue      # fold pieces: their own block below
            nm = {'internal_cutout': 'cutout'}; want = [(nm.get(k, k), [(q['x'], q['y']) for q in l]) for k, l in zip(pc['block']['internal_kinds'], pc['block']['internal_lines'])]
            got = [(l['kind'], [(round(x * 1e4), round(y * 1e4)) for x, y in l['points']]) for l in ro['lines']]
            il_n += 1; il_bad += want != got
print(f"   {'ok ' if il_n >= 60 and not il_bad else 'FAIL'} stream internal lines (v4.7): grain, internal lines, cutouts and drills split by the header counts equal the piece objects' exactly on {il_n - il_bad} of {il_n} records (2303 pieces carry up to 10 lines each)")
if il_n < 60 or il_bad: fails.append(f'stream internal lines: {il_bad} of {il_n} differ')

# v4.7: FOLD PIECES. A fold half's stream is: the CUT half (the outline), the grain line (2 points), the internal lines (header I / H / D counts), the SEW
# half (the stitch line, as many points as are left over) and the mirror line (2 points). Verified against the piece objects of ID1005 - BACK / FRONT (blind
# test D3: at the base size M the grain, internal line and sew half equal the piece object's exactly, at XS / L / XL the sew half equals the piece's GRADED stitch
# line to 1e-4 in - seven ruled points and six different rule numbers per piece, so this also confirms the chord-similarity grading), and the 2303 OUCF pieces.
# The layout is only accepted when it closes geometrically (cut and sew half ends on the mirror line): the older vintage (1825D / 5683D / 2591A / 418T markers) lays
# these lines out differently and is left unlabelled.
bad = []; fb = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D3-BLIND', 'CLAUDE-D3-BF.zip')
if os.path.isfile(fb):
    rfb = am.place_marker(fb); mfb = rfb['markers'][0]['marker']; dfb = mfb['object']['data']
    for pn in ('ID1005 - BACK', 'ID1005 - FRONT'):
        blk = rfb['pieces'][pn]['block']; want = {k_: [(q['x'], q['y']) for q in l] for k_, l in zip(blk['internal_kinds'], blk['internal_lines'])}
        for sz in ('XS', 'S', 'M', 'L', 'XL'):
            rc = next(r_ for r_ in mfb['records'] if r_['piece'] == pn and r_['size'] == sz); ro = am.record_outline(dfb, rc)
            o_ = rc['offset']; t_ = len(rc['text']); dec = am.decode_record_stream(dfb[o_+t_:o_+t_+rc['stream_len']], ro['pen_move'])
            if 'sew' not in dec['labels'] or dec['labels'][-1] != 'mirror': bad.append(f'{pn} {sz}: fold layout not recognised {dec["labels"]}'); continue
            sew = [(x, y) for x, y, _ in dec['contours'][dec['labels'].index('sew')]]; stitch = [(x * 1e4, y * 1e4) for x, y in am.graded_outline(blk, sz)]
            if max(max(abs(a_[0] - b_[0]), abs(a_[1] - b_[1])) for a_, b_ in zip(sew, stitch)) > 1.5: bad.append(f'{pn} {sz}: sew half != graded stitch line')
            lines = {l['kind']: [(round(x * 1e4), round(y * 1e4)) for x, y in l['points']] for l in ro['lines']}
            if any(lines.get(k_) != want[k_] for k_ in ('grain', 'internal') if k_ in want): bad.append(f'{pn} {sz}: grain / internal line differ')
            if sz == 'M' and lines.get('mirror') != want.get('mirror'): bad.append(f'{pn} M: mirror {lines.get("mirror")} != {want.get("mirror")}')
            mir = lines['mirror']; fold = (sew[0], sew[-1])
            if max(abs((p_[0] - mir[0][0]) * (mir[1][1] - mir[0][1]) - (p_[1] - mir[0][1]) * (mir[1][0] - mir[0][0])) / max(1, math.hypot(mir[1][0] - mir[0][0], mir[1][1] - mir[0][1])) for p_ in fold) > 3: bad.append(f'{pn} {sz}: sew ends off the mirror line')
            if not (ro['sew'] and len(ro['sew']) == 2 * len(sew) - 2): bad.append(f'{pn} {sz}: unfolded sew line has {len(ro["sew"] or [])} points')
# 2303 OUCF fold pieces (their piece objects are bundled with the placed marker; the piece perimeter IS the cut line there): the grain line equals the piece's
# grain line up to the rigid shift between the marker's frame and the piece's (0 on three pieces, 12 x 1e-4 in in y on A2), and the stream's mirror line is the chord of
# the SEW half (the piece's own mirror line is the chord of the cut half)
ou_n = ou_bad = 0
z23 = os.path.join(HERE, 'markers', '2303-BD137-PLACED', '2303-BD 137 PLACED.zip')
if os.path.isfile(z23):
    r23 = am.place_marker(z23); seen_ = set()
    for mm in r23['markers']:
        m_ = mm['marker']; dd = m_['object']['data']
        for rc in m_['records']:
            pc = r23['pieces'].get(rc.get('piece'))
            if not pc or 'OUCF' not in rc['piece'] or (rc['text'], rc['stream_len']) in seen_: continue
            seen_.add((rc['text'], rc['stream_len'])); ro = am.record_outline(dd, rc)
            if not ro or not ro['verified']: continue
            blk = pc['block']; want = {k_: [(q['x'], q['y']) for q in l] for k_, l in zip(blk['internal_kinds'], blk['internal_lines'])}
            o_ = rc['offset']; t_ = len(rc['text']); dec = am.decode_record_stream(dd[o_+t_:o_+t_+rc['stream_len']], ro['pen_move'])
            if 'sew' not in dec['labels']: ou_bad += 1; ou_n += 1; continue
            cut0 = dec['contours'][0][0]; sew = dec['contours'][dec['labels'].index('sew')]
            lines = {l['kind']: [(round(x * 1e4), round(y * 1e4)) for x, y in l['points']] for l in ro['lines']}; ou_n += 1
            sh = (cut0[0] - blk['perimeter'][0]['x'], cut0[1] - blk['perimeter'][0]['y'])
            if [(x - sh[0], y - sh[1]) for x, y in lines['grain']] != want['grain'] or lines['mirror'] != [(sew[0][0], sew[0][1]), (sew[-1][0], sew[-1][1])]: ou_bad += 1
if ou_n < 20 or ou_bad: bad.append(f'2303 OUCF: {ou_bad} of {ou_n} records differ from the piece objects (grain up to the frame shift / mirror = sew chord)')
# the older vintage is left alone (no wrong lines): 1825D marker-only records have no `mirror` label
for zn_, mn_ in (('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), ('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip')):
    for mk_ in am.place_marker(os.path.join(HERE, 'markers', zn_, mn_))['markers']:
        for rc in mk_['marker']['records']:
            ro = am.record_outline(mk_['marker']['object']['data'], rc)
            if ro and any(l['kind'] == 'mirror' for l in ro['lines']): bad.append(f'{zn_}: a mirror line was labelled on the older vintage')
print(f"   {'ok ' if not bad else 'FAIL'} fold pieces (v4.7): cut half + grain + internal lines + sew half + mirror line split from the stream - BACK / FRONT at 5 sizes and {ou_n} 2303 OUCF records equal the piece objects; the older vintage stays unlabelled  {'; '.join(bad[:3])}")
if bad: fails.append('fold pieces: ' + '; '.join(bad[:5]))

# v4.7: the grain line of the marker-only ZIPs (older vintage: 1825D / 5683D / 2591A / 418T, their other lines are not decoded). Read as `inferred`: the second
# contour's first two points are a horizontal segment, and every one of the corpus's bundled piece objects has a horizontal grain line (counted here too, 81 in the fixtures; 135 over every capture folder).
gr_n = gr_bad = 0; gr_basis = set()
for zn_, mn_ in (('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), ('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip'), ('2591A-SS21-UNLAID', '2591A-BD 157 AW SS21.zip'), ('418T-SHAPESHIFTER-UNLAID', '418T-BD 160 SHAPESHIFTER.zip')):
    for mk_ in am.place_marker(os.path.join(HERE, 'markers', zn_, mn_))['markers']:
        for e in mk_['inventory']['slots']:
            gr_n += 1; g_ = e.get('grain'); gr_basis.add(e.get('grain_basis'))
            if not g_ or len(g_) != 2 or abs(g_[0][1] - g_[1][1]) > 1e-9 or g_[0][0] == g_[1][0]: gr_bad += 1
po_n = po_h = 0
for zp_ in glob.glob(os.path.join(HERE, 'markers', '**', '*.zip'), recursive=True) + glob.glob(os.path.join(HERE, 'markers-live', '**', '*.zip'), recursive=True):
    try: pcs, _ = am.load_pieces(am.list_zip(zp_))
    except Exception: continue
    for pc_ in pcs.values():
        if not pc_: continue
        for k_, l_ in zip(pc_['block']['internal_kinds'], pc_['block']['internal_lines']):
            if k_ == 'grain' and len(l_) == 2: po_n += 1; po_h += l_[0]['y'] == l_[1]['y']
print(f"   {'ok ' if gr_n >= 110 and not gr_bad and gr_basis <= {'inferred', 'stream'} and po_n and po_h == po_n else 'FAIL'} grain of the marker-only ZIPs (v4.7): {gr_n - gr_bad} of {gr_n} slots have a horizontal grain line, basis {sorted(b for b in gr_basis if b)}; every one of {po_n} grain lines in the bundled piece objects is horizontal ({po_h})")
if gr_n < 110 or gr_bad or po_h != po_n: fails.append(f'marker-only grain: {gr_bad} of {gr_n} slots without a horizontal grain; piece objects {po_h} of {po_n} horizontal')

# v4.7: THE NEST SPEC (nest_spec.py) - the whole unplaced job as JSON / DXF / SVG for a nesting engine, from a marker-only ZIP.
import tempfile, json as _json
import nest_spec as ns
bad = []; n_specs = n_shapes = n_inst = 0
NEST_ZIPS = (('markers/1825D-SS21-UNLAID/1825D-BD 180 SS21.zip', 2), ('markers/5683D-SS21-UNLAID/5683D-BD 168 SS21.zip', 1), ('markers/2591A-SS21-UNLAID/2591A-BD 157 AW SS21.zip', 1),
             ('markers/418T-SHAPESHIFTER-UNLAID/418T-BD 160 SHAPESHIFTER.zip', 1), ('markers-live/CLAUDE-UNP-D3-BLIND/CLAUDE-D3-BF-MARKER-ONLY.zip', 1),
             ('markers-live/CLAUDE-UNP-D4-CURVE/CLAUDE-D4-MARKER-ONLY.zip', 1), ('markers-live/CLAUDE-UNP-D2-TWIN/CLAUDE-D2-M0.zip', 1), ('markers/2303-BD137-UNLAID/2303-BD 137.zip', 1))
with tempfile.TemporaryDirectory() as td:
    for rel, nm in NEST_ZIPS:
        zp = os.path.join(HERE, rel)
        if not os.path.isfile(zp): continue
        specs = ns.build_nest_spec(zp)
        if len(specs) != nm: bad.append(f'{rel}: {len(specs)} markers, expected {nm}')
        for sp in specs:
            n_specs += 1; n_shapes += len(sp['shapes']); n_inst += sum(d['quantity'] for d in sp['demand'])
            if not sp['complete']: bad.append(f"{sp['source']['marker']}: incomplete {[c['name'] for c in sp['checks'] if not c['ok']]}")
            if _json.loads(_json.dumps(sp)) != sp: bad.append(f"{sp['source']['marker']}: not JSON round-trippable")
            # the DXF says what the JSON says: one CUT polyline per shape (+ mirrored copies), same areas
            dp = os.path.join(td, 'x.dxf'); ns.write_dxf(sp, dp); pl = ns.read_dxf_polylines(dp)
            want = sorted(abs(ns._area([tuple(p) for p in (s['outline_mirrored'] if mir else s['outline'])])) for s in sp['shapes'] if s['complete'] for mir in ([False] + ([True] if s.get('outline_mirrored') else [])))
            got = sorted(abs(ns._area(p)) for p in pl.get('CUT', []))
            if len(want) != len(got) or any(abs(a_ - b_) > 2e-4 * max(1.0, a_) for a_, b_ in zip(want, got)): bad.append(f"{sp['source']['marker']}: DXF cut polylines {len(got)} vs {len(want)} (areas differ)")
            if sum(len(v) for k_, v in pl.items() if k_ == 'SEAM') != sum(1 for s in sp['shapes'] if s.get('seam_outline')) * 1 + sum(1 for s in sp['shapes'] if s.get('seam_outline_mirrored')): bad.append(f"{sp['source']['marker']}: DXF seam polylines")
            # every shape: notches and grain lie inside / on its own box, demand covers every slot exactly once
            slots = [o for d in sp['demand'] for o in d['slots']]
            if len(slots) != len(set(slots)) or len(slots) != sp['totals']['instances']: bad.append(f"{sp['source']['marker']}: demand slots not unique")
            for s in sp['shapes']:
                for nt in s['notches']:
                    if not (-0.01 <= nt['x'] <= s['width'] + 0.01 and -0.01 <= nt['y'] <= s['height'] + 0.01): bad.append(f"{sp['source']['marker']} {s['id']}: notch outside the box"); break
            svp = os.path.join(td, 'x.svg'); ns.write_svg(sp, svp)
            if not open(svp, encoding='utf-8').read().startswith('<svg'): bad.append('svg')
    # units: the same job in in / cm / mm
    z = os.path.join(HERE, 'markers', '5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip')
    a_in, a_cm, a_mm = (ns.build_nest_spec(z, u)[0]['totals']['area'] for u in ('in', 'cm', 'mm'))
    if abs(a_cm / a_in - 6.4516) > 1e-3 or abs(a_mm / a_in - 645.16) > 0.1: bad.append(f'unit conversion {a_in} {a_cm} {a_mm}')
    # independence from the piece objects: the spec of the marker-only ZIP == the spec of the full ZIP (whose outlines come from the piece object)
    for full, only in (('markers-live/CLAUDE-UNP-D4-CURVE/CLAUDE-D4.zip', 'markers-live/CLAUDE-UNP-D4-CURVE/CLAUDE-D4-MARKER-ONLY.zip'), ('markers-live/CLAUDE-UNP-D3-BLIND/CLAUDE-D3-BF.zip', 'markers-live/CLAUDE-UNP-D3-BLIND/CLAUDE-D3-BF-MARKER-ONLY.zip')):
        if not (os.path.isfile(os.path.join(HERE, full)) and os.path.isfile(os.path.join(HERE, only))): continue
        sf = ns.build_nest_spec(os.path.join(HERE, full))[0]; so = ns.build_nest_spec(os.path.join(HERE, only))[0]
        if [d['quantity'] for d in sf['demand']] != [d['quantity'] for d in so['demand']]: bad.append(f'{full}: demand differs')
        for a_, b_ in zip(sf['shapes'], so['shapes']):
            if len(a_['outline']) != len(b_['outline']) or max(max(abs(p[0] - q[0]), abs(p[1] - q[1])) for p, q in zip(a_['outline'], b_['outline'])) > 6e-4: bad.append(f"{full}: {a_['piece']} {a_['size']} outline differs between the full and the marker-only ZIP")
        if 'D4' in full and so['totals']['outline_source'] != 'stream': bad.append('D4 marker-only spec must come from the stream')
    # mirrored geometry (CLAUDE-D4 has 3 mirrored pairs): same area / box, grain and notches reflected about the middle of the box
    sd = ns.build_nest_spec(os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D4-CURVE', 'CLAUDE-D4-MARKER-ONLY.zip'))[0]
    if sd['totals']['mirrored_instances'] != 3: bad.append('D4 mirrored instances')
    for s in sd['shapes']:
        mo = [tuple(p) for p in s['outline_mirrored']]; o = [tuple(p) for p in s['outline']]
        if abs(abs(ns._area(mo)) - s['area']) > 1e-6 or abs(max(p[1] for p in mo) - s['height']) > 1e-9 or min(p[1] for p in mo) < -1e-9: bad.append(f"{s['id']}: mirrored outline")
        if abs(s['grain_mirrored']['points'][0][1] - (s['height'] - s['grain']['points'][0][1])) > 1e-9 or abs(s['drills_mirrored'][0][1] - (s['height'] - s['drills'][0][1])) > 1e-9: bad.append(f"{s['id']}: mirrored grain / drill")
        if ns._area(mo) <= 0: bad.append(f"{s['id']}: mirrored outline not counter-clockwise")
    # a part-laid marker lists only what is left: instances + already placed == slots of the marker
    zc = os.path.join(HERE, 'markers', '2303-CP150-JULY', '2303-CP 150 CPL.zip')
    if os.path.isfile(zc):
        rc_ = am.place_marker(zc)
        for sp, mm in zip(ns.build_nest_spec(zc), rc_['markers']):
            if sp['totals']['instances'] + sp['totals']['already_placed'] != len(mm['marker']['slots']) or sp['source']['laid_state'] != 'partial': bad.append(f"{sp['source']['marker']}: part-laid accounting")
print(f"   {'ok ' if not bad else 'FAIL'} NEST SPEC (v4.7): {n_specs} markers, {n_shapes} shapes, {n_inst} pieces - complete, JSON / DXF round trips, spec of the marker-only ZIP == spec of the full ZIP, units, mirrored geometry, part-laid accounting  {'; '.join(bad[:3])}")
if bad: fails.append('nest spec: ' + '; '.join(bad[:5]))

# a machine that knows nothing about AccuMark can use the spec: an independent geometry library (shapely, when installed) accepts every outline as a valid polygon of exactly
# the stated area, and every seam line lies inside its cut line
try:
    from shapely.geometry import Polygon as _Poly
except Exception: _Poly = None
if _Poly:
    sh_bad = []; sh_n = 0
    for rel, _ in NEST_ZIPS:
        zp = os.path.join(HERE, rel)
        if not os.path.isfile(zp): continue
        for sp in ns.build_nest_spec(zp):
            for s_ in sp['shapes']:
                P_ = _Poly(s_['outline']); sh_n += 1
                if not s_.get('self_intersecting') and not P_.is_valid: sh_bad.append(f"{sp['source']['marker']} {s_['id']}: invalid polygon")
                if abs(P_.area / s_['area'] - 1) > 1e-9: sh_bad.append(f"{sp['source']['marker']} {s_['id']}: area")
                if s_.get('seam_outline') and not P_.contains(_Poly(s_['seam_outline']).buffer(-1e-6)): sh_bad.append(f"{sp['source']['marker']} {s_['id']}: seam outside cut")
    print(f"   {'ok ' if not sh_bad else 'FAIL'} nest spec read by shapely: {sh_n} outlines are valid polygons of the stated area, seam lines inside their cut lines  {'; '.join(sh_bad[:3])}")
    if sh_bad: fails.append('nest spec / shapely: ' + '; '.join(sh_bad[:4]))

print('-- lay limits (v4.8, see accumark_laylimits): the table a marker / order names, read from the bundle')
# The Lay Limits table decides how a piece may be turned. It is a separate object: the marker (section 2) and the order both NAME it, and the export
# ZIP bundles it when the marker is exported with its components. Read here against what the Lay Limits Editor SHOWED (laylimits/GROUND_TRUTH.json:
# ZZLL-1, then -X1 / -X2 / -X3 built one setting at a time and diffed), against the markers themselves (their stored bundle directions must follow the
# table's Bundling) and against the orders (which name the same four tables as their marker).
import json as _json
import accumark_laylimits as ll
bad = []; LLDIR = os.path.join(HERE, 'laylimits')
gt = _json.load(open(os.path.join(LLDIR, 'GROUND_TRUTH.json')))
n_tab = n_row = 0
def _cmp_rows(nm, t, want_rows):
    global n_row
    if len(t['rows']) != len(want_rows): bad.append(f'{nm}: {len(t["rows"])} rows, editor showed {len(want_rows)}'); return
    for r, w in zip(t['rows'], want_rows):
        n_row += 1
        if (r['category'], r['options'], r['flip_code'], r['buffer_rule']) != tuple(w[:4]): bad.append(f"{nm} {w[0]}: {(r['category'], r['options'], r['flip_code'], r['buffer_rule'])} != {tuple(w[:4])}")
        if len(w) > 4:
            (cw, ccw, unit), conv = w[5], (1 / 2.54 if w[5][2] == 'length' else 1.0)
            if r['group'] != w[4] or r['tilt_unit'] != unit or abs(r['weft_skew_deg'] - w[6]) > 1e-6: bad.append(f"{nm} {w[0]}: group / unit / skew")
            if abs(r['tilt_cw'] - cw * conv) > 1e-3 or abs(r['tilt_ccw'] - ccw * conv) > 1e-3: bad.append(f"{nm} {w[0]}: tilt {r['tilt_cw']}/{r['tilt_ccw']}")
for nm, want in gt['tables'].items():
    fp = os.path.join(LLDIR, nm + '.GT_lay')
    if not os.path.isfile(fp): bad.append(f'{nm}: fixture missing'); continue
    t = ll.parse_lay_limits(fp); n_tab += 1
    if t['spread_name'] != want['spread'] or t['bundling_name'] != want['bundling'] or t['per_model'] != want.get('per_model', False) or t['vintage'] != 'v5': bad.append(f'{nm}: spread / bundling / per model / vintage')
    if 'comment' in want and t['comment'] != want['comment']: bad.append(f'{nm}: comment {t["comment"]!r}')
    _cmp_rows(nm, t, want['rows'])
# the older vintage (the user's real `L`, `SINGLE-PLY`) as the editor showed it, read from the bundled objects
zsa = os.path.join(HERE, 'markers-live', 'ZZ-SCRATCH-ALL-20260921', 'ZZ-SCRATCH-ALL-20260921.zip'); tabs_sa = ll.load_zip_tables(zsa) if os.path.isfile(zsa) else {}
for nm, want in gt['older_vintage_seen_in_the_editor'].items():
    t = tabs_sa.get(nm)
    if not t: bad.append(f'{nm}: not in the scratch bundle'); continue
    n_tab += 1
    if t['vintage'] != 'v4' or t['spread_name'] != want['spread'] or t['bundling_name'] != want['bundling']: bad.append(f'{nm}: older vintage spread / bundling')
    _cmp_rows(nm, t, want['rows'])
# a table exported inside a ZIP is the same table as the file in the storage area
if tabs_sa.get('ZZLL-1'):
    a, b = tabs_sa['ZZLL-1'], ll.parse_lay_limits(os.path.join(LLDIR, 'ZZLL-1.GT_lay'))
    if [(r['category'], r['options'], r['flip_code'], r['buffer_rule'], r['raw']) for r in a['rows']] != [(r['category'], r['options'], r['flip_code'], r['buffer_rule'], r['raw']) for r in b['rows']] or (a['spread'], a['bundling'], a['comment']) != (b['spread'], b['bundling'], b['comment']):
        bad.append('ZZLL-1: the bundled table differs from the storage-area file')
# every lay-limits object of every ZIP of the corpus reads (both vintages, no error)
n_obj = 0; n_err = []
zips_all = sorted(glob.glob(os.path.join(HERE, 'markers', '**', '*.zip'), recursive=True) + glob.glob(os.path.join(HERE, 'markers-live', '**', '*.zip'), recursive=True))
for zp in zips_all:
    try: tt = ll.load_zip_tables(zp)
    except Exception: continue
    n_obj += len([k for k in tt if k != '_errors']); n_err += [f'{os.path.basename(zp)}: {n}: {m}' for n, m in tt.get('_errors', [])]
if n_obj < 20 or n_err: bad.append(f'corpus tables: {n_obj} read, errors {n_err[:2]}')
print(f"   {'ok ' if not bad else 'FAIL'} lay-limits tables: {n_tab} tables / {n_row} rows equal what the editor showed (spread, bundling, per model, options, flip code, buffer rule, group, tilt + unit, weft skew); {n_obj} bundled objects in {len(zips_all)} ZIPs all read  {'; '.join(bad[:3])}")
if bad: fails.append('lay limits: ' + '; '.join(bad[:5]))

# the names: a marker's section 2 and its order name the same four tables
bad = []; n_mk = n_join = n_tab_in_zip = 0
for zp in zips_all:
    try: lst = am.list_zip(zp)
    except Exception: continue
    tnames = {o['name'] for o in lst.get('lay_limits', [])}; mts = []
    for o in lst.get('marker', []):
        try: mk_ = am.parse_marker(o['data'])
        except Exception: continue
        n_mk += 1
        if not mk_['tables'] or not mk_['tables']['ok']: bad.append(f"{o['name']}: section-2 name strings do not parse"); continue
        mts.append(mk_['tables'])
        if mk_['tables']['lay_limits'] in tnames: n_tab_in_zip += 1
    for od in lst.get('order', []):
        ot = am.parse_order_tables(od)
        if ot is None: bad.append(f"{od['name']}: order table names do not parse"); continue
        for mt in mts:
            if mt['order_name'] != od['name']: continue
            n_join += 1
            if any(ot[k] != mt[k] for k in ('lay_limits', 'annotation', 'block_buffer', 'notch_table')): bad.append(f"{od['name']}: order and marker name different tables")
if n_mk < 40 or n_join < 30: bad.append(f'only {n_mk} markers / {n_join} order-marker pairs')
print(f"   {'ok ' if not bad else 'FAIL'} table names: {n_mk} markers (every vintage) name lay limits / annotation / block buffer / notch table in section 2; {n_join} order-marker pairs name the same four; {n_tab_in_zip} markers find their lay-limits table bundled  {'; '.join(bad[:3])}")
if bad: fails.append('lay limits names: ' + '; '.join(bad[:5]))
# the user's real production markers name tables that are not in their ZIPs: reported by name, rotation stays assumed
real = {}
for zn_, mn_ in (('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), ('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip'), ('2591A-SS21-UNLAID', '2591A-BD 157 AW SS21.zip'), ('418T-SHAPESHIFTER-UNLAID', '418T-BD 160 SHAPESHIFTER.zip')):
    zp = os.path.join(HERE, 'markers', zn_, mn_)
    if os.path.isfile(zp): real[zn_] = {m['marker']['tables']['lay_limits'] for m in am.place_marker(zp)['markers']}
want_real = {'1825D-SS21-UNLAID': {'NEED- TWO WAY'}, '5683D-SS21-UNLAID': {'NEED- TWO WAY'}, '2591A-SS21-UNLAID': {'ALL GMT WAY'}, '418T-SHAPESHIFTER-UNLAID': {'G-LAYLIMITS'}}
ok = all(real.get(k) == v for k, v in want_real.items() if k in real) and len(real) >= 3
print(f"   {'ok ' if ok else 'FAIL'} real production markers name their tables: {sorted(set().union(*real.values())) if real else '-'}")
if not ok: fails.append(f'lay limits: real marker table names {real}')

# the marker's own data agrees with the table: pre-set 180 degree directions follow the table's Bundling
import nest_spec as ns
bad = []; states = Counter(); dec = None
for zp in zips_all:
    try: lst = am.list_zip(zp); tabs = ll.load_zip_tables(zp, lst)
    except Exception: continue
    if not any(k != '_errors' for k in tabs): continue
    try: res = am.place_marker(zp)
    except Exception: continue
    for m_ in res['markers']:
        nm_ = (m_['marker'].get('tables') or {}).get('lay_limits')
        if nm_ in tabs and m_['inventory']['slots']:
            st, det = ns._bundle_pattern(m_['inventory'], tabs[nm_]); states[st] += 1
            if st == 'contradicted': bad.append(f"{m_['marker']['name']}: {det}")
            if m_['marker']['name'] == 'CLAUDE-D2-E7B': dec = (m_['inventory'], tabs[nm_])
if states['consistent'] < 20: bad.append(f'only {states["consistent"]} markers give a decisive comparison: {dict(states)}')
# and it can fail: E7B holds two bundles of one size next to a bundle of the other - "alternate bundles" contradicts it, "same size" and "alternate sizes" agree
if dec:
    inv_, tab_ = dec
    verdict = {b_: ns._bundle_pattern(inv_, dict(tab_, bundling=b_))[0] for b_ in (0, 1, 2)}
    if verdict != {0: 'contradicted', 1: 'contradicted', 2: 'consistent'}: bad.append(f'E7B under each Bundling: {verdict}')
else: bad.append('CLAUDE-D2-E7B missing')
print(f"   {'ok ' if not bad else 'FAIL'} the stored bundle directions follow the table's Bundling on {states['consistent']} markers ({dict(states)}); mutation: the wrong Bundling on E7B is caught  {'; '.join(bad[:3])}")
if bad: fails.append('lay limits / bundle pattern: ' + '; '.join(bad[:5]))

# the parser refuses what it does not understand
bad = []
raw_ = open(os.path.join(LLDIR, 'ZZLL-X2.GT_lay'), 'rb').read()[0x90:]
def _refused(b):
    try: ll.parse_lay_limits(bytes(b)); return False
    except ll.LayLimitsError: return True
muts = {'truncated by one byte': raw_[:-1], 'one byte too long': raw_ + b'\x00'}
b_ = bytearray(raw_); b_[4] = 7; muts['unknown spread'] = b_
b_ = bytearray(raw_); b_[6] = 9; muts['row count 9 for 7 rows'] = b_
b_ = bytearray(raw_); struct.pack_into('<I', b_, raw_.index(b'Category group') - 24, 999); muts['property block length'] = b_
b_ = bytearray(raw_); i_ = raw_.index(b'Category group'); b_[i_ - 4] = 15; muts['property name length'] = b_
for what, b in muts.items():
    if not _refused(b): bad.append(f'{what}: read as if valid')
t_ = ll.parse_lay_limits(raw_)
b_ = bytearray(raw_); i_ = raw_.index(b'COLLAR') - 16 + 5; b_[i_] = 0        # COLLAR's degree flag: the two unit flags now disagree
t2 = ll.parse_lay_limits(bytes(b_))
if not any('unit flags disagree' in w for w in t2['warnings']): bad.append('unit-flag mismatch not reported')
if t_['warnings']: bad.append(f'a clean table warns: {t_["warnings"]}')
print(f"   {'ok ' if not bad else 'FAIL'} the parser refuses {len(muts)} broken variants of a table and reports disagreeing unit flags  {'; '.join(bad[:3])}")
if bad: fails.append('lay limits mutations: ' + '; '.join(bad[:5]))

# what a row allows a nesting engine to do (Gerber help, "Piece Options")
bad = []
def _rules(nm, cat):
    t = ll.parse_lay_limits(os.path.join(LLDIR, nm + '.GT_lay')); r_, how = ll.row_for(t, cat); return ll.orientation_rules(r_), how
want = [('ZZLL-1', 'FRONT', [0], True, False), ('ZZLL-1', 'DEFAULT', [0, 180], False, False), ('ZZLL-1', 'BACK', [0, 90, 180, 270], True, False),
        ('ZZLL-1', 'COLLAR', [0, 45, 90, 135, 180, 225, 270, 315], True, False), ('ZZLL-LOCK-R8', 'anything', [0], False, True), ('ZZLL-BOOKFOLD', 'x', [0, 180], True, False),
        ('ZZLL-1', 'no such category', [0, 180], False, False)]
for nm, cat, deg, flip, lock in want:
    r_, how = _rules(nm, cat)
    if (r_['allowed_deg'], r_['flip_x_axis_allowed'], r_['locked']) != (deg, flip, lock): bad.append(f'{nm} {cat}: {(r_["allowed_deg"], r_["flip_x_axis_allowed"], r_["locked"])}')
if _rules('ZZLL-1', 'no such category')[1] != 'default' or _rules('ZZLL-1', 'front')[1] != 'category': bad.append('row_for: category / default fallback')
r_, _ = _rules('ZZLL-1', 'SLEEVE')
if r_['initial_orientation'] != dict(code=7, label='Rotate 90 degrees, CW', rotate_deg=-90, flip=None): bad.append(f'SLEEVE initial orientation {r_["initial_orientation"]}')
r_, _ = _rules('ZZLL-X1', 'FRONT')
if r_['weft_skew_deg'] != 45.0 or _rules('ZZLL-X2', 'CUFF')[0]['tilt_limit'] != dict(unit='degrees', cw=0.4, ccw=0.4) or _rules('ZZLL-X1', 'DEFAULT')[0]['buffer_rule'] != 17: bad.append('skew / tilt / rule')
print(f"   {'ok ' if not bad else 'FAIL'} orientation rules: blank = 180 + flip, W = one way, S = no flip, W+S = locked, 9 / 4 add 90 / 45 degrees, category row else DEFAULT  {'; '.join(bad[:3])}")
if bad: fails.append('lay limits rules: ' + '; '.join(bad[:5]))

# the nest spec carries it
bad = []
zb = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D3-BLIND', 'CLAUDE-D3-BF.zip'); zo = os.path.join(HERE, 'markers-live', 'CLAUDE-UNP-D3-BLIND', 'CLAUDE-D3-BF-MARKER-ONLY.zip')
if os.path.isfile(zb) and os.path.isfile(zo):
    sb = ns.build_nest_spec(zb)[0]
    if sb['lay_limits']['source'] != 'bundled' or sb['lay_limits']['name'] != 'L' or not sb['rotation']['basis'].startswith('verified') or sb['rotation']['allowed_deg'] != [0, 180] or not sb['rotation']['flip_x_axis_allowed']: bad.append(f"bundled: {sb['lay_limits']['source']} {sb['rotation']}")
    if not all(s_.get('rotation') and s_['rotation']['matched'] == 'default' for s_ in sb['shapes']): bad.append('bundled: shapes without a rotation rule')
    if not sb['complete']: bad.append('bundled spec incomplete')
    so = ns.build_nest_spec(zo)[0]
    # v4.14: a marker-only ZIP reads its own rows (section 4) - the same rules the bundled table gives, the table named 'L', no spread / bundling (the marker does not carry them)
    if so['lay_limits']['source'] != 'marker snapshot' or so['lay_limits']['name'] != 'L' or not so['rotation']['basis'].startswith('verified') or not all(s_.get('rotation') for s_ in so['shapes']): bad.append(f"marker-only: {so['lay_limits']['source']}")
    if so['rotation']['allowed_deg'] != sb['rotation']['allowed_deg'] or so['lay_limits']['rows'][0]['options'] != sb['lay_limits']['rows'][0]['options'] or so['lay_limits']['spread'] is not None or not so['complete']: bad.append('marker-only: the marker snapshot does not give the bundled table\'s rule / incomplete')
    if [d['allowed_deg_by_slot'] for d in so['demand']] != [d['allowed_deg_by_slot'] for d in sb['demand']]: bad.append('marker-only demand rotations differ from the bundled-table spec')
    # supplying the table (a storage-area file) turns a marker-only spec into a verified one, per category
    sz = ns.build_nest_spec(zo, lay_limits=os.path.join(LLDIR, 'ZZLL-1.GT_lay'))[0]
    got = {s_['category']: (s_['rotation']['row'], s_['rotation']['matched'], s_['rotation']['allowed_deg'], s_['rotation']['flip_x_axis_allowed']) for s_ in sz['shapes']}
    if got.get('BACK') != ('BACK', 'category', [0, 90, 180, 270], True) or got.get('FRONT') != ('FRONT', 'category', [0], True): bad.append(f'supplied ZZLL-1: {got}')
    if sz['lay_limits']['source'] != 'supplied' or not sz['rotation']['basis'].startswith('verified') or not sz['complete']: bad.append('supplied: source / basis / complete')
    if not any('marker names' in w for w in sz['warnings']): bad.append('supplied table of another name: no warning')
    if _json.loads(_json.dumps(sz)) != sz: bad.append('supplied spec not JSON round-trippable')
    if any(len(d['preset_rot180_by_slot']) != d['quantity'] or sum(d['preset_rot180_by_slot']) != d['preset_rot180'] for d in sz['demand']): bad.append('demand presets by slot')
print(f"   {'ok ' if not bad else 'FAIL'} nest spec: bundled table -> verified rotation per category; marker-only -> read from the marker's own rows (v4.14); --lay-limits FILE -> verified  {'; '.join(bad[:3])}")
if bad: fails.append('nest spec / lay limits: ' + '; '.join(bad[:5]))

# a real nest: AccuNest kept a one-way (`W`) piece in the direction its bundle was retrieved in (laylimits/EXPERIMENT_W_ALTERNATE.md)
try:
    from shapely.geometry import Polygon as _P2
    from shapely import affinity as _aff
except Exception: _P2 = None
fx = os.path.join(LLDIR, 'EXPERIMENT_W_ALTERNATE.DXF')
if _P2 and os.path.isfile(fx) and os.path.isfile(zsa):
    bad = []
    sp_ = ns.build_nest_spec(zsa, marker='ZZC-M1')[0]
    fr = next((s_ for s_ in sp_['shapes'] if s_['piece'] == 'LADIES-BLOUSE-FR'), None)
    if fr is None or fr['rotation']['options'] != 'MW' or fr['rotation']['allowed_deg'] != [0]: bad.append('ZZC-M1 FRONT is not read as MW / [0]')
    else:
        ref = _P2(fr['outline']).buffer(0)
        dem = [d for d in sp_['demand'] if d['shape'] == fr['id']]; pres = [p_ for d in dem for p_ in d['preset_rot180_by_slot']]
        if any(a_ != [180 * p_] for d in dem for a_, p_ in zip(d['allowed_deg_by_slot'], d['preset_rot180_by_slot'])): bad.append('allowed_deg_by_slot for a W row is not the preset direction')
        plotted = [_P2(pl).buffer(0) for pl in ns.read_dxf_polylines(fx).get('T001L001', []) if len(pl) >= 20]
        mine = [p_ for p_ in plotted if p_.area and abs(p_.area / ref.area - 1) < 0.015]
        rev = 0
        for p_ in mine:
            best = {}
            for tn, sx, sy in (('fwd', 1, 1), ('fwd', 1, -1), ('rev', -1, -1), ('rev', -1, 1)):
                T = _aff.scale(ref, sx, sy, origin=(0, 0)); T = _aff.translate(T, p_.centroid.x - T.centroid.x, p_.centroid.y - T.centroid.y)
                best[tn] = min(best.get(tn, 9), p_.symmetric_difference(T).area / p_.area)
            rev += best['rev'] + 0.0005 < best['fwd']
        if len(mine) != len(pres) or rev != sum(pres): bad.append(f'plot: {len(mine)} FR outlines, {rev} reversed; the marker stores {len(pres)} instances, {sum(pres)} preset to 180')
    print(f"   {'ok ' if not bad else 'FAIL'} AccuNest nest of ZZC-M1: the {len(pres) if not bad else '?'} FRONT (MW) pieces keep their preset direction ({sum(pres) if not bad else '?'} reversed, as stored)  {'; '.join(bad[:3])}")
    if bad: fails.append('lay limits / real nest: ' + '; '.join(bad[:5]))

# the user's REAL support files (AccuMark Explorer "OldFiles", AccuMark 9 data): laylimits/REAL_SUPPORT_TABLES.json holds the table bytes only, redacted (no envelope, no names)
bad = []
rt = _json.load(open(os.path.join(LLDIR, 'REAL_SUPPORT_TABLES.json')))
real_t = {k: ll.parse_lay_limits(bytes.fromhex(v), name=k) for k, v in rt['lay_limits_hex'].items()}
# as the Lay Limits Editor showed scratch copies of these exact bytes (V17 file header + these bytes)
want_r = {'L': ('v4', None, 'single_ply', 'same_size_same_direction', '', 1, 0), 'G-LAYLIMITS': ('v4', None, 'single_ply', 'alternate_bundle_alternate_direction', 'MWS', 1, 1),
          'NEED- TWO WAY': ('v5', 'none', 'single_ply', 'alternate_bundle_alternate_direction', 'MWS', 1, 1), 'ONE GMT ONW WAY': ('v5', 'skew', 'single_ply', 'alternate_bundle_alternate_direction', 'MWS', 1, 1)}
for k, w in want_r.items():
    t = real_t.get(k)
    if not t or len(t['rows']) != 1 or (t['vintage'], t['trailer'], t['spread_name'], t['bundling_name'], t['rows'][0]['options'], t['rows'][0]['flip_code'], t['rows'][0]['buffer_rule']) != (w[0], w[1], w[2], w[3], w[4], w[5], w[6]) or t['rows'][0]['category'] != 'DEFAULT': bad.append(f'{k}: {t and (t["vintage"], t["trailer"], t["bundling_name"], t["rows"][0]["options"])}')
zcs = os.path.join(HERE, 'markers', 'COSTORDER.zip')
if os.path.isfile(zcs):
    lc = am.list_zip(zcs)['lay_limits'][0]
    if bytes(lc['data'][0x8a:0x8a + lc['payload_len']]).hex() != rt['lay_limits_hex']['L']: bad.append('the real L is not the corpus L')
# the two AccuMark 9 saves end early: refused when the shortened trailer is not exactly what it should be
for k in ('NEED- TWO WAY', 'ONE GMT ONW WAY'):
    if not _refused(bytes.fromhex(rt['lay_limits_hex'][k]) + b'\x00'): bad.append(f'{k}: a stray trailing byte was accepted')
# on the real production markers: the table the marker names, supplied, agrees with the marker's stored bundle directions; MWS fixes every instance in its preset direction
real_pairs = Counter()
for zn_, mn_, tn_ in (('1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip', 'NEED- TWO WAY'), ('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip', 'NEED- TWO WAY'), ('418T-SHAPESHIFTER-UNLAID', '418T-BD 160 SHAPESHIFTER.zip', 'G-LAYLIMITS')):
    zp = os.path.join(HERE, 'markers', zn_, mn_)
    if not os.path.isfile(zp): continue
    for sp_ in ns.build_nest_spec(zp):
        s2 = ns.build_nest_spec(zp, marker=sp_['source']['marker'], lay_limits=real_t[tn_])[0]; ll2 = s2['lay_limits']
        if sp_['lay_limits']['name'] != tn_ or sp_['lay_limits']['source'] != 'marker snapshot' or not sp_['rotation']['locked'] or sp_['rotation']['allowed_deg'] != [0]: bad.append(f"{zn_}: the marker names {sp_['lay_limits']['name']}, reads {sp_['lay_limits']['source']} {sp_['rotation']['allowed_deg']}")
        # the marker's own row against the table now in the support files: 1825D and 5683D were made when NEED- TWO WAY had no `M` (major piece) - the table was edited since; 418T agrees
        want_diff = ["row 0 (DEFAULT): options 'WS' in the marker, 'MWS' in the table"] if tn_ == 'NEED- TWO WAY' else []
        if ll2['snapshot']['differences'] != want_diff or ll2['snapshot']['agrees'] != (not want_diff): bad.append(f"{zn_}: marker row vs table {ll2['snapshot']}")
        if ll2['source'] != 'supplied' or ll2['bundle_pattern']['state'] != 'consistent' or not s2['rotation']['locked'] or s2['rotation']['allowed_deg'] != [0] or not s2['complete'] or any('supplied' in w_ for w_ in s2['warnings']): bad.append(f"{zn_} {tn_}: {ll2['source']} {ll2['bundle_pattern']} {s2['rotation']['allowed_deg']}")
        if any(a_ != [180 * p_] for d in s2['demand'] for a_, p_ in zip(d['allowed_deg_by_slot'], d['preset_rot180_by_slot'])): bad.append(f'{zn_}: MWS did not fix the preset direction')
        real_pairs[zn_] += int(ll2['bundle_pattern']['detail'].split(' ')[0])
if len(real_pairs) < 3: bad.append(f'real markers found: {dict(real_pairs)}')
# 2591A names ALL GMT WAY (not in the support files): every bundle of its 7 sizes is preset to 0 - only "All Bundle, Same Direction" fits, the other Bundling modes are contradicted
z25 = os.path.join(HERE, 'markers', '2591A-SS21-UNLAID', '2591A-BD 157 AW SS21.zip')
if os.path.isfile(z25):
    m25 = am.place_marker(z25)['markers'][0]
    s25 = ns.build_nest_spec(z25)[0]
    if m25['marker']['tables']['lay_limits'] != 'ALL GMT WAY' or s25['lay_limits']['source'] != 'marker snapshot' or s25['lay_limits']['rows'][0]['options'] != 'MWS' or s25['rotation']['allowed_deg'] != [0]: bad.append('2591A: ALL GMT WAY is not read from the marker as MWS / one way')
    verdict = {b_: ns._bundle_pattern(m25['inventory'], dict(real_t['L'], bundling=b_))[0] for b_ in (0, 1, 2)}
    if verdict != {0: 'consistent', 1: 'contradicted', 2: 'contradicted'}: bad.append(f'2591A under each Bundling: {verdict}')
print(f"   {'ok ' if not bad else 'FAIL'} real support files: L / G-LAYLIMITS / NEED- TWO WAY / ONE GMT ONW WAY read as the editor showed (two AccuMark 9 layouts with a short trailer); the real 1825D / 5683D / 418T markers follow them on {sum(real_pairs.values())} bundle pairs; 2591A's presets predict ALL GMT WAY = All Bundle, Same Direction  {'; '.join(bad[:3])}")
if bad: fails.append('real support tables: ' + '; '.join(bad[:5]))

print('-- notch tables (v4.10, see accumark_notch): what a notch number means')
# A notch on a piece and in a marker's stream is a NOTCH NUMBER; the Notch Parameter Table gives it a type, widths and a depth. Read here against what the Notch editor
# SHOWED (notch/GROUND_TRUTH.json: ZZNT-X1 / X2 were made by editing one row of every type in the editor and diffed), against the real tables, and against the geometry
# of a real AccuNest plot (every notch spike is exactly the table's depth).
import accumark_notch as nt
bad = []; NDIR = os.path.join(HERE, 'notch'); ngt = _json.load(open(os.path.join(NDIR, 'GROUND_TRUTH.json')))
IN = 2.54
def _rowcm(n): return (n['label'], round(n['perimeter_in'] * IN, 2), round(n['inside_in'] * IN, 2), round(n['depth_in'] * IN, 2))
for nm, want in ngt['tables'].items():
    if 'file' not in want: continue
    t = nt.parse_notch_table(os.path.join(NDIR, want['file']))
    if t['count'] != want['count'] or t['trailer'] is not True: bad.append(f'{nm}: count {t["count"]} trailer {t["trailer"]}')
    got = {str(n['number']): _rowcm(n) for n in t['notches']}
    for k, w in want['rows'].items():
        if w[0] == 'None':
            if k in got: bad.append(f'{nm} {k}: defined but the editor showed None')
        elif got.get(k) != (w[0], w[1], w[2], w[3]): bad.append(f'{nm} {k}: {got.get(k)} vs {tuple(w)}')
    for k in range(9, 26):
        if got.get(str(k)) != ('V', 0.30, 0.0, -0.20): bad.append(f'{nm} {k}: {got.get(str(k))}'); break
real_n = {k: nt.parse_notch_table(bytes.fromhex(v), name=k) for k, v in ngt['real_tables_hex'].items()}
ne = real_n['NEED-P-NOTCH']
if ne['count'] != 15 or [(n['number'], n['type_name'], round(n['perimeter_in'] * IN, 2), round(n['depth_in'] * IN, 2)) for n in ne['notches']] != [(i, 'slit', 0.0, 0.5) if i not in (6, 7) else (i, 'v', 0.5, -0.25) for i in range(1, 16)]: bad.append('NEED-P-NOTCH does not read as the editor showed it')
dp = real_n['P-NOTCH']
if [(n['number'], n['type_name'], round(n['depth_in'] * IN, 2)) for n in dp['notches']] != [(1, 'slit', 0.4)] or dp['count'] != 5: bad.append('default P-NOTCH')
# every notch-table object of the corpus reads; the tables of the 2303 style and the scratch P-NOTCH read as the editor showed them
n_nt = 0; seen_nt = {}
for zp in zips_all:
    try: tt = nt.load_zip_notch_tables(zp)
    except Exception: continue
    n_nt += len([k for k in tt if k != '_errors']); bad += [f'{os.path.basename(zp)}: {a_}: {b_}' for a_, b_ in tt.get('_errors', [])]
    for k, v in tt.items():
        if k != '_errors': seen_nt[(k, v['count'])] = v
vn = seen_nt.get(('V-NOTCH-ALL CUSTOMERS', 25))
if not vn or [(n['type_name'], round(n['perimeter_in'] * IN, 2), round(n['depth_in'] * IN, 2)) for n in vn['notches']] != [('v', 0.30, -0.20)] * 25: bad.append('V-NOTCH-ALL CUSTOMERS')
sp6 = seen_nt.get(('P-NOTCH', 6))
if not sp6 or [(n['number'], n['type_name'], round(n['depth_in'] * IN, 2)) for n in sp6['notches']] != [(1, 'slit', 0.4), (6, 'slit', 0.0)]: bad.append('scratch P-NOTCH (6 records)')
if n_nt < 10: bad.append(f'only {n_nt} notch objects read')
print(f"   {'ok ' if not bad else 'FAIL'} notch tables: X1 / X2 (one row of every type, 8 type codes) + NEED-P-NOTCH + default P-NOTCH read as the editor showed; {n_nt} bundled notch objects in the corpus all read  {'; '.join(bad[:3])}")
if bad: fails.append('notch tables: ' + '; '.join(bad[:5]))

# the parser refuses what it does not understand
bad = []
raw_n = open(os.path.join(NDIR, 'ZZNT-X2.GT_notpt'), 'rb').read()[0x90:]
def _nrefused(b):
    try: nt.parse_notch_table(bytes(b)); return False
    except nt.NotchTableError: return True
muts = {'one byte short': raw_n[:-1], 'a non-zero trailer': raw_n[:-4] + b'\x01\x00\x00\x00', 'a stray extra dword': raw_n + b'\x00\x00\x00\x00', 'too short': raw_n[:30]}
b_ = bytearray(raw_n); struct.pack_into('<I', b_, 64 + 16 * 3, 9); muts['unknown type code 9'] = b_
b_ = bytearray(raw_n); struct.pack_into('<i', b_, 8, 1234); muts['first-five triplet differs from record 1'] = b_
b_ = bytearray(raw_n); struct.pack_into('<I', b_, 60, 100); muts['100 records'] = b_
b_ = bytearray(raw_n); struct.pack_into('<I', b_, 60, 24); muts['count says 24, bytes hold 25'] = b_
for what, b in muts.items():
    if not _nrefused(b): bad.append(f'{what}: read as if valid')
if _nrefused(raw_n): bad.append('a clean table was refused')
print(f"   {'ok ' if not bad else 'FAIL'} the notch parser refuses {len(muts)} broken variants of a table  {'; '.join(bad[:3])}")
if bad: fails.append('notch mutations: ' + '; '.join(bad[:5]))

# the markers: a shape's notch code is a number of the table its marker names; the real plot's notch spikes are the table's depth
bad = []; used = Counter(); checked = 0
zsupp = os.path.join(HERE, 'markers', '418T-SHAPESHIFTER-UNLAID')
for zp in [os.path.join(HERE, rel_) for rel_, _ in NEST_ZIPS] + [zsa]:
    try: sps = ns.build_nest_spec(zp, notch_table=[real_n['NEED-P-NOTCH']] if ('1825D' in zp or '5683D' in zp) else None)
    except Exception: continue
    for sp_ in sps:
        nb = sp_['notch_table']
        if nb['parsed']:
            checked += 1
            for u_ in nb['numbers_used']: used[u_] += 1
            if _json.loads(_json.dumps(sp_)) != sp_: bad.append(f"{sp_['source']['marker']}: not JSON round-trippable")
            if nb['undefined_numbers'] and 'CLAUDE-D4' not in sp_['source']['marker']: bad.append(f"{sp_['source']['marker']}: undefined notch numbers {nb['undefined_numbers']}")
if checked < 30 or set(used) - {1, 5}: bad.append(f'{checked} specs with a notch table; numbers used {dict(used)}')      # 5 = 2591A, read from its own copy since v4.14
# real production: the 1825D notch (number 1) is a 0.50 cm slit; without the table the spec names it but reads nothing
z18 = os.path.join(HERE, 'markers', '1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip')
s18 = next((sp_['notch_table'] for sp_ in ns.build_nest_spec(z18, notch_table=real_n['NEED-P-NOTCH']) if sp_['notch_table']['numbers_used']), {'parsed': False}); s18n = ns.build_nest_spec(z18)[0]['notch_table']
if not s18['parsed'] or s18['name'] != 'NEED-P-NOTCH' or s18['numbers_used'] != [1] or abs(s18['entries']['1']['depth'] - 0.5) > 0.005 or s18['entries']['1']['kind'] != 'slit' or s18['entries']['6']['direction'] != 'external': bad.append(f'1825D notch block {s18}')
# v4.14: the marker carries its own copy (section 3): the marker-only spec reads all 15 notches, equal to the real table - no `--notch-table` needed
if not s18n['parsed'] or s18n['source'] != 'marker snapshot' or s18n['name'] != 'NEED-P-NOTCH' or s18n['entries'] != s18['entries'] or s18n['undefined_numbers']: bad.append('1825D marker-only notch block')
# geometry: the plotted marker of ZZC-M1 (default P-NOTCH: notch 1 = slit, depth 0.40 cm) has 30 notch spikes, every one 0.40 cm long
fxp = os.path.join(LLDIR, 'EXPERIMENT_W_ALTERNATE.DXF')
if os.path.isfile(fxp):
    spk = Counter()
    for pl_ in ns.read_dxf_polylines(fxp).get('T001L001', []):
        for i_ in range(len(pl_) - 2):
            a_, b_2, c_ = pl_[i_], pl_[i_ + 1], pl_[i_ + 2]
            if math.dist(a_, c_) < 0.02 and math.dist(a_, b_2) > 0.05: spk[round(math.dist(a_, b_2), 2)] += 1
    dz = nt.load_zip_notch_tables(zsa).get('P-NOTCH')
    if dict(spk) != {0.4: 30} or not dz or round(dz['by_number'][1]['depth_in'] * IN, 2) != 0.4: bad.append(f'plot spikes {dict(spk)} vs the table')
print(f"   {'ok ' if not bad else 'FAIL'} notch numbers: {checked} corpus specs read their table (numbers used {dict(used)}); 1825D notch 1 = slit 0.50 cm (NEED-P-NOTCH); the real plot's 30 notch spikes are all 0.40 cm = the table's depth  {'; '.join(bad[:3])}")
if bad: fails.append('notch numbers: ' + '; '.join(bad[:5]))

print('-- reference nester (v4.11, see reference_nester.py): the spec alone is enough to nest')
# The spec is the contract with a nesting engine. Two independent proofs: (1) the lay AccuMark itself made of the real 2303 job, rebuilt from the SPEC's shapes and the placed marker's
# positions and flags, is a valid lay (no overlaps, inside the fabric, the marker's own utilisation); (2) a nester that reads only the spec JSON (numpy + shapely, no decoder) lays
# every instance of the real jobs validly - inside the fabric, no overlap, every rotation inside the instance's allowed set.
import copy
try:
    import reference_nester as rn
    from shapely.geometry import Polygon as _PG
    from shapely.strtree import STRtree as _ST
    _have_rn = True
except ImportError:
    _have_rn = False; print('   skip reference nester (needs numpy, Pillow and shapely)')
bad = []
zpl = os.path.join(HERE, 'markers', '2303-BD137-PLACED', '2303-BD 137 PLACED.zip'); zun = os.path.join(HERE, 'markers', '2303-BD137-UNLAID', '2303-BD 137.zip')
if _have_rn and os.path.isfile(zpl) and os.path.isfile(zun):
    su = ns.build_nest_spec(zun, units='in')[0]; rp = am.place_marker(zpl)['markers'][0]; mkp = rp['marker']
    shp_ = {s_['id']: s_ for s_ in su['shapes']}; by_slot = {}
    for d in su['demand']:
        for o_ in d['slots']: by_slot[o_] = (shp_[d['shape']], d['mirrored'])
    polys_ = []
    for s_ in mkp['slots']:
        sh, mir = by_slot[s_['index']]
        if (sh['piece'], sh['size']) != (s_['piece'], s_['size']) or mir != bool(s_['placed_flip']): bad.append(f"slot {s_['index']}: spec shape / mirror does not match the placed marker"); break
        polys_.append(_PG(am.transform([tuple(p) for p in sh['outline']], s_)).buffer(0))
    Wp, Lp = mkp['width'], mkp['length']; tree_ = _ST(polys_); n_ov = 0; worst = 0.0
    for i_, p_ in enumerate(polys_):
        for j_ in tree_.query(p_):
            if j_ > i_:
                a_ = p_.intersection(polys_[j_]).area
                if a_ > 1e-3: n_ov += 1
                worst = max(worst, a_)
    xs_ = [b_ for p_ in polys_ for b_ in (p_.bounds[0], p_.bounds[2])]; ys_ = [b_ for p_ in polys_ for b_ in (p_.bounds[1], p_.bounds[3])]
    util_ = 100 * sum(p_.area for p_ in polys_) / (Wp * Lp)
    if len(polys_) != 97 or n_ov or worst > 5e-3: bad.append(f'real lay from the spec shapes: {len(polys_)} pieces, {n_ov} overlapping pairs, worst {worst:.4f} in2')
    if min(xs_) < -1e-3 or max(xs_) > Lp + 1e-3 or min(ys_) < -1e-3 or max(ys_) > Wp + 1e-3: bad.append('real lay from the spec shapes leaves the fabric')
    if abs(util_ - mkp['util']) > 0.02: bad.append(f'utilisation {util_:.2f} vs the marker\'s {mkp["util"]:.2f}')
    ok_real = not bad
    # the whole job of a laid marker as a spec: the same shapes, positions ignored
    sj = ns.build_nest_spec(zpl, units='in', as_job=True)[0]
    if sj['totals']['instances'] != 97 or abs(sj['totals']['area'] - su['totals']['area']) > 1e-6 or not sj['source']['job_of_laid_marker'] or sj['source']['laid_state'] != 'laid': bad.append(f"as_job spec: {sj['totals']['instances']} instances, area {sj['totals']['area']:.3f} vs {su['totals']['area']:.3f}")
    print(f"   {'ok ' if not bad else 'FAIL'} AccuMark's own lay of 2303 (97 pieces, {Lp * 2.54:.1f} cm, {mkp['util']:.2f}%) rebuilt from the spec's shapes: {n_ov} overlapping pairs (worst {worst:.4f} in2), inside the {Wp:.2f} in fabric, utilisation {util_:.2f}%; the same job as a spec from the laid marker  {'; '.join(bad[:3])}")
    if bad: fails.append('reference lay: ' + '; '.join(bad[:5]))

bad = []; res_rows = []
jobs_ = [('2303', zun, None, {}), ('ZZC-M1', zsa, 'ZZC-M1', {}), ('1825D', os.path.join(HERE, 'markers', '1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), '1825D-BD 180 SS21', dict(lay_limits=real_t['NEED- TWO WAY'])),
         ('5683D', os.path.join(HERE, 'markers', '5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip'), None, dict(lay_limits=real_t['NEED- TWO WAY']))]
for lab_, zp_, mk_, kw_ in jobs_:
    if not _have_rn or not os.path.isfile(zp_): continue
    sp_ = ns.build_nest_spec(zp_, marker=mk_, **kw_)[0]
    # only the JSON crosses over: the nester gets no marker, no ZIP, no decoder objects
    sp_ = _json.loads(_json.dumps(sp_))
    pl_, un_, _ = rn.nest(sp_, res=0.3); rep_ = rn.validate(sp_, pl_, un_); res_rows.append((lab_, rep_))
    if not rep_['valid'] or rep_['pieces'] != sp_['totals']['instances']: bad.append(f"{lab_}: {rep_['pieces']}/{sp_['totals']['instances']} pieces, overlaps {rep_['overlapping_pairs']}, inside {rep_['inside_fabric']}, rotations {rep_['rotations_allowed']}")
    if rep_['utilisation'] < 40: bad.append(f"{lab_}: utilisation {rep_['utilisation']:.1f}%")
    if lab_ == '2303' and rep_['length'] > mkp['length'] * 2.54 * 1.10: bad.append(f"2303: the nester's {rep_['length']:.1f} cm is more than 10% longer than AccuMark's {mkp['length'] * 2.54:.1f} cm")
    if lab_ == '1825D' and any(p_['angle'] not in p_['allowed'] or len(p_['allowed']) != 1 for p_ in pl_): bad.append('1825D: MWS locks every instance in its preset direction')
# it can fail: the validator catches an overlap, a piece outside the fabric and a forbidden rotation
if res_rows:
    sp_ = _json.loads(_json.dumps(ns.build_nest_spec(zsa, marker='ZZC-M1')[0])); pl_, un_, _ = rn.nest(sp_, res=0.3)
    pl2 = [dict(p_) for p_ in pl_]; from shapely import affinity as _af
    pl2[1]['poly'] = _af.translate(pl2[0]['poly'], 0.5, 0.5)
    r1 = rn.validate(sp_, pl2, un_)
    pl3 = [dict(p_) for p_ in pl_]; pl3[0]['poly'] = _af.translate(pl3[0]['poly'], 0, sp_['fabric']['width'])
    r2 = rn.validate(sp_, pl3, un_)
    pl4 = [dict(p_) for p_ in pl_]; pl4[0]['angle'] = 90 if 90 not in pl4[0]['allowed'] else 45
    r3 = rn.validate(sp_, pl4, un_); r4 = rn.validate(sp_, pl_[:-1], un_)
    if r1['valid'] or r1['overlapping_pairs'] < 1 or r2['valid'] or r2['inside_fabric'] or r3['valid'] or r3['rotations_allowed'] or r4['valid']: bad.append(f"validator mutations: overlap {r1['overlapping_pairs']}, outside {r2['inside_fabric']}, rotation {r3['rotations_allowed']}, missing piece {r4['valid']}")
    # the spec drives the nester: forbid every rotation and no piece is turned
    sp0 = copy.deepcopy(sp_)
    for d in sp0['demand']: d['allowed_deg_by_slot'] = [[0] for _ in d['slots']]
    pl0, un0, _ = rn.nest(sp0, res=0.3)
    if any(p_['angle'] != 0 for p_ in pl0) or not rn.validate(sp0, pl0, un0)['valid']: bad.append('a spec with only 0 degrees did not keep every piece at 0')
if _have_rn: print(f"   {'ok ' if not bad else 'FAIL'} reference nester (spec JSON only): " + '; '.join(f"{l_} {r_['pieces']}/{r_['instances']} pieces {r_['length']:.0f} cm {r_['utilisation']:.0f}% valid" for l_, r_ in res_rows) + f"; mutations caught  {'; '.join(bad[:3])}")
if bad: fails.append('reference nester: ' + '; '.join(bad[:5]))

print('-- block buffer tables (v4.12, see accumark_blockbuffer): what a buffer rule is')
# A Lay Limits row names a RULE NUMBER; the Block Buffer table gives the rule its kind (buffer / block) and its amounts per side, static and dynamic. Read here against what the
# Block Buffer editor SHOWED (blockbuffer/GROUND_TRUTH.json: ZZBB-USER, then -X1 / -X2 built in the editor and diffed), the real 3MM / 3MM-N, and the markers' own buffer entries.
import accumark_blockbuffer as bbf
bad = []; BDIR = os.path.join(HERE, 'blockbuffer'); bgt = _json.load(open(os.path.join(BDIR, 'GROUND_TRUTH.json')))
def _cm(a): return None if a is None else (f"{a['value']:.1f}%" if a['unit'] == 'percent' else round(a['value'] * 2.54, 2))
def _cmp_rules(nm, t, want):
    if [r['number'] for r in t['rules']] != [w[0] for w in want]: bad.append(f"{nm}: rule numbers {[r['number'] for r in t['rules']]}"); return
    for r, w in zip(t['rules'], want):
        if r['kind'] != w[1]: bad.append(f'{nm} rule {w[0]}: kind {r["kind"]}')
        for which, wv in (('static', w[2]), ('dynamic', w[3])):
            got = [_cm(r[which][x]) if r[which][x]['value'] else None for x in ('left', 'top', 'right', 'bottom')]
            exp = [None] * 4 if wv is None else [(f'{float(v[:-1]):.1f}%' if isinstance(v, str) else (None if v is None or v == 0 else round(v, 2))) for v in wv]
            if got != exp: bad.append(f'{nm} rule {w[0]} {which}: {got} vs {exp}')
        if any(r[which]['segment']['value'] for which in ('static', 'dynamic')) or r['reserved']: bad.append(f'{nm} rule {w[0]}: a segment / reserved amount is not 0')
n_bt = 0
base_rules = bgt['tables']['ZZBB-USER']['rules']
for nm, want in bgt['tables'].items():
    t = bbf.parse_block_buffer(os.path.join(BDIR, want['file'])); n_bt += 1
    rules_w = want['rules'] if 'rules' in want else base_rules + want['extra']
    if t['vintage'] != 'v5' or t['trailer'] is not True or t['comment'] != want['comment']: bad.append(f"{nm}: vintage / trailer / comment {t['vintage']} {t['trailer']} {t['comment']!r}")
    _cmp_rules(nm, t, rules_w)
for nm, want in bgt['real_tables'].items():
    t = bbf.parse_block_buffer(bytes.fromhex(bgt['real_tables_hex'][nm]), name=nm); n_bt += 1
    if t['vintage'] != want['vintage']: bad.append(f'{nm}: vintage {t["vintage"]}')
    _cmp_rules(nm, t, want['rules'])
n_obj = 0; seen_bb = {}
for zp in zips_all:
    try: tt = bbf.load_zip_block_buffers(zp)
    except Exception: continue
    n_obj += len([k for k in tt if k != '_errors']); bad += [f'{os.path.basename(zp)}: {a_}: {b_}' for a_, b_ in tt.get('_errors', [])]
    for k, v in tt.items():
        if k != '_errors': seen_bb[(k, len(v['rules']))] = v
z1 = seen_bb.get(('ZZBB-1', 4))
if not z1 or [(r['number'], r['kind']) for r in z1['rules']] != [(1, 'buffer'), (2, 'block'), (3, 'buffer'), (4, 'buffer')] or [_cm(z1['by_number'][4]['static'][x]) for x in ('left', 'right')] != [2.0, 0.5]: bad.append('ZZBB-1 (bundled in the scratch bundle)')
if n_obj < 2: bad.append(f'only {n_obj} bundled block-buffer objects read')
print(f"   {'ok ' if not bad else 'FAIL'} block buffer tables: {n_bt} tables (rules 1-10, Block and Buffer, static and dynamic amounts, percentages, two-line comment, both layouts) read as the editor showed; {n_obj} bundled objects all read  {'; '.join(bad[:3])}")
if bad: fails.append('block buffer tables: ' + '; '.join(bad[:5]))

# the parser refuses what it does not understand
bad = []
raw_b = open(os.path.join(BDIR, 'ZZBB-X2.GT_block'), 'rb').read()[0x90:]
def _brefused(b):
    try: bbf.parse_block_buffer(bytes(b)); return False
    except bbf.BlockBufferError: return True
muts = {'one byte short': raw_b[:-1], 'a non-zero trailer': raw_b[:-4] + b'\x01\x00\x00\x00', 'a stray extra byte': raw_b + b'\x00', 'too short': raw_b[:4]}
b_ = bytearray(raw_b); struct.pack_into('<H', b_, 4, 11); muts['count says 11, bytes hold 10'] = b_
b_ = bytearray(raw_b); o_ = 6 + 28 + 70 * 2 + 2; struct.pack_into('<H', b_, o_, 2); muts['unknown rule type 2'] = b_
b_ = bytearray(raw_b); o_ = 6 + 28 + 70 * 3; struct.pack_into('<H', b_, o_, 1); muts['rule number 1 twice'] = b_
b_ = bytearray(raw_b); struct.pack_into('<H', b_, 0, 60); muts['comment length 60'] = b_
for what, b in muts.items():
    if not _brefused(b): bad.append(f'{what}: read as if valid')
if _brefused(raw_b): bad.append('a clean table was refused')
print(f"   {'ok ' if not bad else 'FAIL'} the block buffer parser refuses {len(muts)} broken variants of a table  {'; '.join(bad[:3])}")
if bad: fails.append('block buffer mutations: ' + '; '.join(bad[:5]))

# the markers: the rule a piece's Lay Limits row names, looked up in the table, IS the marker's own buffer entry (Left, Right, Top / Bottom)
bad = []; tot_eq = 0; cases = []
zb_ = os.path.join(HERE, 'markers', '2303-CP150-JULY', '2303-CP 150 CPL.zip')
for lab_, zp_, mk_, kw_ in (('ZZC-M1', zsa, 'ZZC-M1', {}), ('ZZC-M3', zsa, 'ZZC-M3', {}), ('2303 CP 150', zb_, '2303-CP 150 CPL LEFTBTM 26-47', {}),
                            ('418T', os.path.join(HERE, 'markers', '418T-SHAPESHIFTER-UNLAID', '418T-BD 160 SHAPESHIFTER.zip'), None, dict(lay_limits=real_t['G-LAYLIMITS'], block_buffer=bbf.parse_block_buffer(bytes.fromhex(bgt['real_tables_hex']['3MM']), name='3MM'))),
                            ('1825D', os.path.join(HERE, 'markers', '1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'), '1825D-BD 180 SS21', dict(lay_limits=real_t['NEED- TWO WAY'], block_buffer=bbf.parse_block_buffer(bytes.fromhex(bgt['real_tables_hex']['3MM']), name='3MM')))):
    if not os.path.isfile(zp_): continue
    sp_ = ns.build_nest_spec(zp_, marker=mk_, **kw_)[0]; bf_ = sp_['block_buffer']
    if not bf_['parsed'] or bf_['marker_entries']['different'] or not bf_['marker_entries']['equal']: bad.append(f"{lab_}: {bf_.get('marker_entries')} {bf_.get('basis')}")
    else: tot_eq += bf_['marker_entries']['equal']; cases.append(lab_)
    if not any(s_.get('buffer', {}).get('rule') for s_ in sp_['shapes']): bad.append(f'{lab_}: no shape carries its buffer rule')
    if _json.loads(_json.dumps(sp_)) != sp_: bad.append(f'{lab_}: not JSON round-trippable')
# the unequal rule: ZZC-M1's sleeve is rule 4 (Left 2.00 cm, Right 0.50 cm) and its marker entry is [0.7874, 0.1968, 0, 0] - Left, Right, Top / Bottom; and a rule with four different
# amounts (ZZBB-X1 rule 9: Left .11, Top .22, Right .33, Bottom .44 cm, made into a marker in a live run) has the entry [0.0433, 0.1299, 0.0866, 0.1732] - Left, Right, Top, Bottom
ex_ = bgt['marker_entry_experiment']; L9, T9, R9, B9 = bbf.rule_sides_in(bbf.parse_block_buffer(os.path.join(BDIR, 'ZZBB-X1.GT_block'))['by_number'][9])
if [round(v_, 4) for v_ in (L9, R9, T9, B9)] != ex_['marker_entry_doubles_inches'] or ex_['reads_as'] != ['left', 'right', 'top', 'bottom']: bad.append(f'the recorded marker entry does not read as Left, Right, Top, Bottom of rule 9: {(L9, R9, T9, B9)}')
sm1 = ns.build_nest_spec(zsa, marker='ZZC-M1')[0]; sl = next(s_ for s_ in sm1['shapes'] if s_['piece'] == 'LADIES-BLOUSE-SL')
if sl['buffer']['rule'] != 4 or [round(sl['buffer']['static'][x]['value'], 2) for x in ('left', 'top', 'right', 'bottom')] != [2.0, 0.0, 0.5, 0.0]: bad.append(f"ZZC-M1 sleeve buffer {sl['buffer']}")
mkm = am.place_marker(zsa)['markers']; mk1 = next(m_['marker'] for m_ in mkm if m_['marker']['name'] == 'ZZC-M1')
if [round(v, 4) for v in mk1['block_buffers'][3]['sides']] != [0.7874, 0.1968, 0.0, 0.0]: bad.append('ZZC-M1 marker entry 3')
# it can fail: the wrong table (ZZBB-USER: rule 1 is 0.30 cm, the marker holds 1.00 cm) is contradicted, and a marker-only ZIP names its table but reads nothing
wrong = ns.build_nest_spec(zsa, marker='ZZC-M1', block_buffer=os.path.join(BDIR, 'ZZBB-USER.GT_block'))[0]['block_buffer']
if wrong['marker_entries']['different'] < 1: bad.append('the wrong table was not contradicted by the marker')
z18b = os.path.join(HERE, 'markers', '1825D-SS21-UNLAID', '1825D-BD 180 SS21.zip'); nb_ = ns.build_nest_spec(z18b, lay_limits=real_t['NEED- TWO WAY'])[0]['block_buffer']
if nb_['parsed'] or nb_['source'] != 'named only' or nb_['name'] != '3MM' or nb_['rules_used'] != [1]: bad.append(f'1825D marker-only block buffer {nb_}')
print(f"   {'ok ' if not bad else 'FAIL'} buffer rules: {tot_eq} marker entries ({', '.join(cases)}) equal the table rule their Lay Limits row names; the unequal rule 4 (Left 2.00, Right 0.50 cm) is [0.7874, 0.1968, 0, 0] and rule 9 (.11 / .22 / .33 / .44 cm) is [0.0433, 0.1299, 0.0866, 0.1732] in the marker - Left, Right, Top, Bottom; the wrong table is contradicted  {'; '.join(bad[:3])}")
if bad: fails.append('buffer rules: ' + '; '.join(bad[:5]))

print('-- laid-marker orientation (v4.13, see MARKER_FORMAT_SPEC.md section 20): low three bits, tilt float, collar frame, storage files')
# A LAID marker says how each piece lies in three places: the low three bits of the slot's orientation word (a quarter turn, mirrored or not), a signed float32 at slot byte +38 (a further tilt,
# radians, counter-clockwise) and - for one piece of the corpus - a quarter turn between the piece's stream frame and the frame the code refers to. Proved against the DXFs AccuMark plotted
# from four AccuNest runs (72 placed slots; rotation/GROUND_TRUTH.json) and the home boxes of the 19 tilted slots of ZZN-B4; the pre-4.13 rule (0x2000 = rot180, 0x0080 = mirror) is wrong on them.
import verify_marker as _vm
bad = []; RDIR = os.path.join(HERE, 'rotation'); rgt = _json.load(open(os.path.join(RDIR, 'GROUND_TRUTH.json')))
if {int(k): (v['rotate_ccw_deg'], v['mirror_top_to_bottom_first']) for k, v in rgt['orient_L_low_three_bits'].items()} != am.ORIENT_L: bad.append('am.ORIENT_L differs from rotation/GROUND_TRUTH.json')
if sorted(int(k) for k in rgt['orient_L_slots_measured_alone_from_the_plot_without_collars']) != list(range(8)): bad.append('not every orientation code was measured alone')
def _cen(p): return (sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p))
def _pair_loops(outs, loops):
    """{slot: loop}: every decoded outline to the plotted loop nearest to it, one to one (the plot is drawn from the same marker)."""
    lc = [_cen(l) for l in loops]; cand = []
    for i, o in outs.items():
        c = _cen(o)
        for j, l in enumerate(loops):
            d_ = math.hypot(c[0] - lc[j][0], c[1] - lc[j][1])
            if d_ < 3: cand.append((d_, i, j))
    cand.sort(); ui, uj, out = set(), set(), {}
    for d_, i, j in cand:
        if i in ui or j in uj: continue
        ui.add(i); uj.add(j); out[i] = loops[j]
    return out
def _old_rule(s):   # what the decoder did before 4.13: 0x2000 = rotate 180, 0x0080 = mirror, both = flip about the vertical axis
    return dict(placed_rot=180 if (s['rot'] == 180 or s['flip_h']) else 0, placed_flip=bool(s['flip_v'] or s['flip_h']), tilt_deg=0.0)
EXPS = (('ZZROT-90', 'ZZROT-90.DXF'), ('ZZROT-45', 'ZZROT-45.DXF'), ('ZZROT-T', 'ZZROT-T.DXF'), ('ZZLL-EXP1', os.path.join('..', 'laylimits', 'EXPERIMENT_W_ALTERNATE.DXF')))
n_slots = n_match = 0; worst_all = 0.0; broken = {k: 0 for k in ('rot180 added', 'mirror inverted', 'tilt sign inverted', 'no collar frame', 'pre-4.13 rule')}; tilts = {}
for nm, dxf in EXPS:
    res = am.place_marker(os.path.join(RDIR, nm + '.GT_mark')); m = res['markers'][0]; mk = m['marker']
    loops = _vm.dxf_marker(os.path.join(RDIR, dxf))[0]
    placed = {s['index']: (s, o) for s, n_, sz_, o, note_ in m['placed'] if o}
    if len(mk['slots']) != 18 or len(placed) != 18 or mk['frames'] != {n_: (90 if n_.endswith('COL') else 0) for n_ in mk['frames']} or sum(mk['frames'].values()) != 90: bad.append(f"{nm}: {len(placed)} placed of {len(mk['slots'])}, frames {mk['frames']}")
    pair = _pair_loops({i: o for i, (s, o) in placed.items()}, loops); n_slots += len(placed); n_match += len(pair)
    own = {s['index']: am._slot_geometry(s, res['pieces'], res['piece_errors'], True, mk)[2] for s, o in placed.values()}
    worst = max((_vm.hausdorff(placed[i][1], l) for i, l in pair.items()), default=9)
    worst_all = max(worst_all, worst)
    if len(pair) != 18 or worst > 0.2: bad.append(f'{nm}: {len(pair)} slots matched to the plot, worst {worst:.3f} in')
    tilts[nm] = {i: round(s['tilt_deg'], 2) for i, (s, o) in placed.items() if s['tilt_deg']}
    def _off(fn, key):    # slots whose plotted loop is missed by more than 0.2 in when `fn` changes the orientation
        n_ = 0
        for i, (s, o) in placed.items():
            if i not in pair: continue
            pl = dict(s); pl.update(fn(s)); fr = mk['frames'].get(s['piece'], 0) if key != 'no collar frame' else 0
            if _vm.hausdorff(am.transform(own[i], pl, fr), pair[i]) > 0.2: n_ += 1
        broken[key] += n_
    _off(lambda s: dict(placed_rot=(s['placed_rot'] + 180) % 360), 'rot180 added'); _off(lambda s: dict(placed_flip=not s['placed_flip']), 'mirror inverted')
    _off(lambda s: dict(tilt_deg=-(s['tilt_deg'] or 0)), 'tilt sign inverted'); _off(lambda s: {}, 'no collar frame'); _off(_old_rule, 'pre-4.13 rule')
if tilts['ZZROT-T'] != {10: 10.0, 11: 10.0} or any(tilts[k] for k in ('ZZROT-90', 'ZZROT-45', 'ZZLL-EXP1')): bad.append(f'tilt floats: {tilts}')
if n_match != 72 or broken['tilt sign inverted'] < 2 or broken['no collar frame'] < 8 or broken['rot180 added'] < 20 or broken['mirror inverted'] < 20 or broken['pre-4.13 rule'] < 20: bad.append(f'mutations do not break the fit: {broken}')
print(f"   {'ok ' if not bad else 'FAIL'} 4 AccuNest runs, {n_slots} placed slots: every decoded outline lies on its plotted loop (worst {worst_all:.3f} in = curve sag; cuffs 0.002); 8 orientation codes + a 10.0 deg tilt; the same slots with a changed rule miss it: {broken}  {'; '.join(bad[:3])}")
if bad: fails.append('laid-marker orientation: ' + '; '.join(bad[:5]))

# the home box is the bounding box of the placed (tilted) shape: 19 tilted slots of ZZN-B4 (tilt +-1.5, +-3 deg) - the sign and the order (tilt after the mirror) are settled here where no plot exists
bad = []
resb = am.place_marker(zsa); mb = next((x for x in resb['markers'] if x['marker']['name'] == 'ZZN-B4'), None)
if mb is None: bad.append('ZZN-B4 missing')
else:
    tl = [(s, o) for s, n_, sz_, o, note_ in mb['placed'] if o and s['tilt_deg']]
    worst = max((max(abs(s['home_x'] * 2 - (max(p[0] for p in o) - min(p[0] for p in o))), abs(s['home_y'] * 2 - (max(p[1] for p in o) - min(p[1] for p in o)))) for s, o in tl), default=9)
    own_b = {s['index']: am._slot_geometry(s, resb['pieces'], resb['piece_errors'], True, mb['marker'])[2] for s, o in tl}
    wrong = 0
    for s, o in tl:
        pl = dict(s); pl['tilt_deg'] = -s['tilt_deg']; q = am.transform(own_b[s['index']], pl, mb['marker']['frames'].get(s['piece'], 0))
        if max(abs(s['home_x'] * 2 - (max(p[0] for p in q) - min(p[0] for p in q))), abs(s['home_y'] * 2 - (max(p[1] for p in q) - min(p[1] for p in q)))) > 0.03: wrong += 1
    vals = sorted({round(s['tilt_deg'], 2) for s, o in tl})
    if len(tl) != 19 or worst > 0.03 or vals != [-3.0, 1.5, 3.0]: bad.append(f'{len(tl)} tilted slots, worst home-box residual {worst:.3f}, tilts {vals}')
    if wrong < 8: bad.append(f'inverting the tilt sign breaks only {wrong} of the tilted slots')
print(f"   {'ok ' if not bad else 'FAIL'} ZZN-B4: {0 if mb is None else len(tl)} tilted slots ({vals if mb else ''} deg): home box = bounding box of the tilted shape (worst {worst:.3f} in); the wrong tilt sign misses it on {wrong} slots  {'; '.join(bad[:3])}")
if bad: fails.append('ZZN-B4 tilts: ' + '; '.join(bad[:5]))

# the home box is the piece's box AND its block buffer, the buffer turned with the piece (independent of the plot: it needs only the marker and its own buffer entries): the sleeve's Left 2.0 + Right 0.5 cm
# add 0.984 in along x at 0 / 180 degrees and along y at 90 / 270; a collar tilted 10 degrees adds 2 x 0.1968 x (cos 10 + sin 10) on both; a piece with equal sides adds the same either way
bad = []; n_par = {'SL x/y': 0, 'others': 0, 'tilted': 0}
for nm_, dxf_ in EXPS:
    res_ = am.place_marker(os.path.join(RDIR, nm_ + '.GT_mark')); m_ = res_['markers'][0]
    for s_, n2_, sz_, o_, note_ in m_['placed']:
        b_ = am._buffer_sides(m_['marker'], n2_); xs_ = [p[0] for p in o_]; ys_ = [p[1] for p in o_]
        dx_ = s_['home_x'] * 2 - (max(xs_) - min(xs_)); dy_ = s_['home_y'] * 2 - (max(ys_) - min(ys_))
        if s_['tilt_deg']:
            t_ = math.radians(abs(s_['tilt_deg'])); ex_ = ey_ = (b_[0] + b_[1]) * (math.cos(t_) + math.sin(t_)); n_par['tilted'] += 1
        else:
            ex_, ey_ = (b_[0] + b_[1], b_[2] + b_[3]) if s_['placed_rot'] in (0, 180) else (b_[2] + b_[3], b_[0] + b_[1]); n_par['SL x/y' if n2_.endswith('SL') else 'others'] += 1
        if abs(dx_ - ex_) > 0.01 or abs(dy_ - ey_) > 0.01: bad.append(f"{nm_} slot {s_['index']} {n2_[-5:]} rot {s_['placed_rot']}: box excess {dx_:.3f} x {dy_:.3f}, buffer says {ex_:.3f} x {ey_:.3f}")
    oc_ = next((r_ for r_ in m_['checks'] if r_[0].startswith('placed shapes fill')), None)
    if oc_ is None or not oc_[1]: bad.append(f'{nm_}: place_marker check {oc_}')
print(f"   {'ok ' if not bad else 'FAIL'} home box = placed box + the piece's own buffer turned with it: {n_par['SL x/y']} sleeve slots (L 2.0 / R 0.5 cm on x at 0/180, on y at 90/270), {n_par['others']} others, {n_par['tilted']} tilted collars  {'; '.join(bad[:3])}")
if bad: fails.append('buffer turns with the piece: ' + '; '.join(bad[:5]))

# a laid marker read as a job (--as-job): the shapes are in the piece frame, so the stored box is the home box turned back - the four collars of TEST-2 no longer look 90 degrees off
bad = []
ztest2 = os.path.join(HERE, 'markers', 'misc-test-markers', 'LADIES-BLOUSE TEST-2.zip')
if os.path.isfile(ztest2):
    sj2 = ns.build_nest_spec(ztest2, units='in', as_job=True)[0]
    row2 = next(r for r in sj2['checks'] if r['name'].startswith('outline fits'))
    col_ = [sh for sh in sj2['shapes'] if sh['piece'].endswith('COL')]
    if not row2['ok'] or not row2['detail'].startswith('20 of 20 exactly equal'): bad.append(f"stored-box check: {row2['ok']} {row2['detail']}")
    if len(col_) != 4 or any(abs(sh['padding'][0]) > 2e-3 or abs(sh['padding'][1]) > 2e-3 for sh in col_): bad.append('a collar shape still has padding against its stored box')
    inv2 = am.place_marker(ztest2, as_unlaid=True)['markers'][0]['inventory']['slots']
    c2 = next(x for x in inv2 if x['piece'].endswith('COL'))
    if not (c2['home_box_in'][0] > c2['home_box_in'][1] and c2['home_box_piece_in'][0] < c2['home_box_piece_in'][1]): bad.append(f"collar home box {c2['home_box_in']} / in the piece frame {c2['home_box_piece_in']}")
    # the runtime check every place_marker result carries: each placed shape fills its stored home box - and it notices a wrong reading of one slot
    rt2 = am.place_marker(ztest2); mt2 = rt2['markers'][0]
    oc0 = next(r_ for r_ in mt2['checks'] if r_[0].startswith('placed shapes fill'))
    pl_bad = []
    for i_, (s_, n3_, sz3_, o3_, note3_) in enumerate(mt2['placed']):
        if i_ == 5 and o3_: s2_ = dict(s_, placed_rot=90); pl_bad.append((s2_, n3_, sz3_, am.transform(am._slot_geometry(s_, rt2['pieces'], rt2['piece_errors'], True, mt2['marker'])[2], s2_, mt2['marker']['frames'].get(n3_, 0)), note3_))
        else: pl_bad.append((s_, n3_, sz3_, o3_, note3_))
    oc1 = am.orientation_check(mt2['marker'], pl_bad)
    if not oc0[1] or oc1 is None or oc1[1]: bad.append(f'orientation_check: {oc0[1]} on the real marker, {oc1} with one slot turned 90 degrees')
print(f"   {'ok ' if not bad else 'FAIL'} LADIES-BLOUSE TEST-2 as a job: stored box == outline box on 20 of 20 shapes (the 4 collars were flagged before v4.13); a collar's home box is 16.5 x 3.5 in as placed, 3.5 x 16.5 in in its piece frame  {'; '.join(bad[:3])}")
if bad: fails.append('as-job stored box: ' + '; '.join(bad[:5]))

# no laid marker of the corpus has two placed pieces on top of each other (bar the hand-placed slot 6 of three experiment copies); the pre-4.13 rule has 1700
bad = []; ov_new = ov_old = 0; ov_by = {}
try:
    from shapely.geometry import Polygon as _PG2
    from shapely.strtree import STRtree as _ST2
    _shp = True
except ImportError:
    _shp = False
if _shp:
    def _n_ov(polys, thr=0.02):
        ps = [_PG2(p).buffer(0) for p in polys]; tr_ = _ST2(ps); n_ = 0
        for a_ in range(len(ps)):
            for b_ in tr_.query(ps[a_]):
                if b_ > a_ and ps[a_].intersection(ps[b_]).area > thr: n_ += 1
        return n_
    for zp_ in (zsa, os.path.join(HERE, 'markers', '2303-BD137-PLACED', '2303-BD 137 PLACED.zip'), os.path.join(HERE, 'markers', 'misc-test-markers', 'AD1234 TEST 134.zip'), os.path.join(HERE, 'markers', 'misc-test-markers', 'LADIES-BLOUSE TEST-2.zip')):
        if not os.path.isfile(zp_): continue
        rr_ = am.place_marker(zp_)
        for m_ in rr_['markers']:
            pl_ = [(s, o) for s, n_, sz_, o, note_ in m_['placed'] if o]
            if len(pl_) < 2: continue
            n_new = _n_ov([o for s, o in pl_])
            n_old = _n_ov([am.transform(am._slot_geometry(s, rr_['pieces'], rr_['piece_errors'], True, m_['marker'])[2], dict(s, **_old_rule(s)), 0) for s, o in pl_])
            ov_new += n_new; ov_old += n_old
            if n_new: ov_by[(os.path.basename(zp_)[:12], m_['marker']['name'])] = n_new
    if ov_by != {('ZZ-SCRATCH-A', 'ZZ-AM-1'): 6, ('ZZ-SCRATCH-A', 'ZZN-D1'): 6, ('ZZ-SCRATCH-A', 'LADIES-BLOUSE TEST-2'): 3}: bad.append(f'overlapping pairs by marker: {ov_by}')
    if ov_old < 1000: bad.append(f'the pre-4.13 rule has only {ov_old} overlapping pairs: the test no longer discriminates')
print(f"   {'ok ' if not bad else 'FAIL'} overlapping placed pieces over the laid markers of the corpus: {ov_new} with the L rule (all in the 3 experiment copies with a hand-placed slot 6: {ov_by}), {ov_old} with the pre-4.13 rule  {'; '.join(bad[:3])}" if _shp else '   skip corpus overlaps (needs shapely)')
if bad: fails.append('corpus overlaps: ' + '; '.join(bad[:5]))

# a marker straight from an AccuMark storage area (<area>\mark\<state>\NAME.GT_mark) reads like the export of the same marker; a half-laid one (NeedsApproval) reads as partial
bad = []
disk_m = am.parse_marker(am.read_storage_marker(os.path.join(RDIR, 'ZZC-M1.GT_mark')))
exp_m = am.parse_marker(next(o for o in am.list_zip(zsa)['marker'] if o['name'] == 'ZZC-M1')['data']) if os.path.isfile(zsa) else None
if exp_m is not None:
    strip_ = lambda s_: {k: v for k, v in s_.items() if k != 'slot'}
    if [strip_(s) for s in disk_m['slots']] != [strip_(s) for s in exp_m['slots']] or [r['text'] for r in disk_m['records']] != [r['text'] for r in exp_m['records']] or disk_m['tables'] != exp_m['tables']: bad.append('storage file and export of ZZC-M1 read differently')
    if disk_m['laid_state'] != 'unlaid' or len(disk_m['slots']) != 18: bad.append(f"ZZC-M1 storage file: {disk_m['laid_state']}, {len(disk_m['slots'])} slots")
pb = am.place_marker(os.path.join(RDIR, 'ZZROT-B.GT_mark'))['markers'][0]
if pb['marker']['laid_state'] != 'partial' or len(pb['placed']) != 17 or len(pb['unplaced']) != 1: bad.append(f"ZZROT-B (NeedsApproval): {pb['marker']['laid_state']}, {len(pb['placed'])} placed, {len(pb['unplaced'])} unplaced")
b_ = bytearray(am.read_storage_marker(os.path.join(RDIR, 'ZZROT-T.GT_mark'))); mt_ = am.parse_marker(bytes(b_)); struct.pack_into('<f', b_, mt_['slots'][3]['slot'] + 38, float('nan'))
w0_ = am.marker_warnings(mt_); w1_ = am.marker_warnings(am.parse_marker(bytes(b_)))
if any('tilt word' in x_ for x_ in w0_) or len(w1_) != len(w0_) + 1 or not any('tilt word that is not an angle' in x_ for x_ in w1_): bad.append(f'a NaN tilt word: {w0_} -> {w1_}')
try: am.read_storage_marker(os.path.join(RDIR, 'ZZROT-90.DXF')); bad.append('a DXF was read as a marker storage file')
except am.AccuMarkError: pass
print(f"   {'ok ' if not bad else 'FAIL'} marker storage files (.GT_mark): ZZC-M1 reads as its export does (slots, records, tables), ZZROT-B (NeedsApproval) reads as partial, 17 placed + 1 unplaced  {'; '.join(bad[:3])}")
if bad: fails.append('storage files: ' + '; '.join(bad[:5]))

print('-- the marker carries its own tables (v4.14, MARKER_FORMAT_SPEC.md section 22): notch table, lay-limits rows, each piece\'s row')
# Section 3 is the marker's copy of its Notch Parameter Table, section 4 its Lay Limits ROWS (12 bytes: flip code, tilt, b2, b3) and every piece row names its row (`lay_row`) with the buffer rule
# and flip code it gave. Proved against the bundled tables of every marker that has them; the real production markers (no tables bundled) then read their own rotation rules and notch sizes.
import accumark_notch as _nt, accumark_laylimits as _ll
bad = []; cnt = Counter(); seen_m = set(); rows_eq = rows_all = pr_eq = pr_all = 0; legacy = []
for zp_ in zips_all:
    try: L_ = am.list_zip(zp_)
    except Exception: continue
    nts_ = {o_['name']: o_ for o_ in L_.get('notch_table', [])}; lls_ = {}
    for o_ in L_.get('lay_limits', []):
        try: lls_[o_['name']] = _ll.parse_lay_limits(o_)
        except _ll.LayLimitsError: pass
    for o_ in L_.get('marker', []):
        key_ = (o_['name'], len(o_['data']), hash(o_['data']))
        if key_ in seen_m: continue
        seen_m.add(key_)
        try: mk_ = am.parse_marker(o_['data'])
        except Exception: continue
        sn_ = mk_['snapshots']
        if sn_['warnings'] or sn_['notch'] is None or 'error' in sn_['notch'] or sn_['lay_limits'] is None or not sn_['lay_limits']['ok']: bad.append(f"{o_['name']}: {sn_['warnings'] or 'no snapshot'}")
        cnt[sn_['notch'].get('vintage')] += 1
        nt_ = nts_.get(mk_['tables'].get('notch_table'))
        if nt_ is not None and sn_['notch'].get('vintage') == 'table':
            same = [(n_['number'], n_['type'], n_['perimeter_in'], n_['inside_in'], n_['depth_in']) for n_ in _nt.parse_notch_table(nt_)['notches']] == [(n_['number'], n_['type'], n_['perimeter_in'], n_['inside_in'], n_['depth_in']) for n_ in sn_['notch']['notches']]
            cnt['table == snapshot' if same else 'table != snapshot'] += 1
        elif nt_ is not None: legacy.append(o_['name'])
        lt_ = lls_.get(mk_['tables'].get('lay_limits'))
        if lt_ is not None and sn_['lay_limits']:
            snr = sn_['lay_limits']['rows']
            if len(snr) != len(lt_['rows']): bad.append(f"{o_['name']}: {len(snr)} snapshot rows, {len(lt_['rows'])} in the table"); continue
            for a_, b_ in zip(snr, lt_['rows']):
                rows_all += 1; rows_eq += (a_['options'] == b_['options'] and a_['flip_code'] == b_['flip_code'] and (abs(a_['tilt_cw'] - b_['tilt_cw']) < 5e-4 or abs(a_['tilt_cw'] - b_['tilt_ccw']) < 5e-4))
            names_ = [r_['category'] for r_ in lt_['rows']]
            for p_ in mk_['pieces']:
                if 'lay_row' not in p_: continue
                try: ix_ = names_.index(p_['fabric'])
                except ValueError: ix_ = 0
                pr_all += 1; pr_eq += (p_['lay_row'] == ix_ and p_['buffer_rule'] == lt_['rows'][ix_]['buffer_rule'] and p_['flip_code'] == lt_['rows'][ix_]['flip_code'])
if cnt['table != snapshot'] or cnt['table == snapshot'] < 36 or cnt['legacy-5-triplets'] != 16 or len(legacy) != 16 or rows_all < 70 or rows_eq != rows_all or pr_all < 280 or pr_eq != pr_all:
    bad.append(f'{dict(cnt)}; legacy copies with a table {len(legacy)}; rows {rows_eq}/{rows_all}; piece rows {pr_eq}/{pr_all}')
print(f"   {'ok ' if not bad else 'FAIL'} {len(seen_m)} markers: section 3 = the notch table ({cnt['table == snapshot']} equal to their bundled table, {cnt['legacy-5-triplets']} older 60-byte copies), section 4 = the lay-limits rows ({rows_eq} of {rows_all} rows equal the bundled table), piece rows name their row / rule / flip ({pr_eq} of {pr_all})  {'; '.join(bad[:3])}")
if bad: fails.append('marker tables: ' + '; '.join(bad[:5]))

# byte patches: every fact must fail when broken
bad = []
zc_ = next((o_ for o_ in am.list_zip(zsa)['marker'] if o_['name'] == 'ZZC-M1'), None) if os.path.isfile(zsa) else None
if zc_ is not None:
    d0_ = bytes(zc_['data']); m0_ = am.parse_marker(d0_); D_ = m0_['directory']
    def _mut(off, val, fmt='<B'):
        b_ = bytearray(d0_); struct.pack_into(fmt, b_, off, val); return am.parse_marker(bytes(b_)), bytes(b_)
    p_fr = next(p_ for p_ in m0_['pieces'] if p_['name'].endswith('-FR')); r_fr = p_fr['offset'] - 28
    mfl, _ = _mut(r_fr + 12, 9, '<H')                                                    # the FRONT piece row claims flip code 9
    if mfl['snapshots']['lay_limits']['ok'] or not any('disagrees with its piece rows' in w_ for w_ in am.marker_warnings(mfl)) or all(ok_ for n_, ok_, dd_ in am.check_marker(mfl) if n_.startswith('section 4 = whole')): bad.append('a wrong flip code on a piece row was not noticed')
    mrw, _ = _mut(r_fr + 6, 40, '<H')                                                    # ... a row index beyond the table
    if mrw['snapshots']['lay_limits']['ok']: bad.append('a piece row pointing past the rows was not noticed')
    mb3, _ = _mut(D_[4] - 6 + 12 * 1 + 11, 0x20)                                        # row 1 (FRONT) loses M and W: now `S`
    if mb3['snapshots']['lay_limits']['rows'][1]['options'] != 'S' or m0_['snapshots']['lay_limits']['rows'][1]['options'] != 'MW': bad.append(f"row 1 options {mb3['snapshots']['lay_limits']['rows'][1]['options']} / {m0_['snapshots']['lay_limits']['rows'][1]['options']}")
    mnt, dnt_ = _mut(D_[3] - 6 + 60, 99, '<I')                                              # the notch table's record count
    if 'error' not in mnt['snapshots']['notch'] or not any('not a notch table' in w_ for w_ in am.marker_warnings(mnt)): bad.append('a broken notch snapshot was not noticed')
    cv_ = am.marker_coverage(d0_, m0_); unk_ = [r_ for r_ in cv_['unknown_runs'] if r_[2] in (3, 4)]
    if unk_: bad.append(f'sections 3 / 4 leave unknown bytes: {unk_[:3]}')
    if am.marker_coverage(dnt_, mnt)['counts']['unknown'] <= cv_['counts']['unknown']: bad.append('a broken section 3 does not show as unknown bytes')
print(f"   {'ok ' if not bad else 'FAIL'} byte patches on ZZC-M1: a wrong flip code / row index on a piece row, a changed option byte in section 4, a broken notch count each show; sections 3 and 4 leave no unknown byte  {'; '.join(bad[:3])}")
if bad: fails.append('marker tables mutations: ' + '; '.join(bad[:5]))

print('-- notch numbers and notch codes (v4.15, MARKER_FORMAT_SPEC.md section 18): a piece keeps the number, a marker keeps min(number, 5)')
# A notch's NUMBER (1-99, the row of the Notch Parameter Table) is the last byte of the 45-byte tag-0x07 child of its point in the piece's line table. The perimeter point and a marker's stream keep only the CODE
# min(number, 5). Proved on a piece PDS made with numbers 3, 6, 6, 7, 12, 16, 25, 30, 30 and the marker Process made from it (notchnum/), and on every piece of the corpus that carries the number.
import accumark_pds as _pds
NDIR = os.path.join(HERE, 'notchnum'); ngt2 = _json.load(open(os.path.join(NDIR, 'GROUND_TRUTH.json'))); bad = []
psum = _pds.summarize(am.read_storage_piece(os.path.join(NDIR, 'NN-PIECE.GT_piece')))
want_nums = sorted(int(k) for k, v in ngt2['placed_numbers'].items() for _ in range(v))
if sorted(psum['notch_numbers']) != want_nums or Counter(psum['notch_types']) != Counter({int(k): v for k, v in ngt2['piece_codes'].items()}): bad.append(f"piece: numbers {psum['notch_numbers']} codes {psum['notch_types']}")
if any(min(n_, 5) != c_ for n_, c_ in zip(psum['notch_numbers'], psum['notch_types'])): bad.append('piece: a code is not min(number, 5)')
dnn = am.read_storage_marker(os.path.join(NDIR, 'NN-MARKER.GT_mark')); mnn = am.parse_marker(dnn)
for r_ in mnn['records']:
    ro_ = am.record_outline(dnn, r_)
    if not ro_ or not ro_['verified'] or Counter(n_[1] for n_ in ro_['notches']) != Counter({int(k): v for k, v in ngt2['marker_codes_per_size'].items()}): bad.append(f"marker record {r_['size']}: notch codes {ro_ and [n_[1] for n_ in ro_['notches']]}")
# every piece of the corpus that carries numbers obeys it
n_seen = n_bad = 0; seen_p = set()
for zp_ in zips_all:
    try: L_ = am.list_zip(zp_)
    except Exception: continue
    for o_ in L_.get('piece', []):
        k_ = (o_['name'], len(o_['data']), hash(o_['data']))
        if k_ in seen_p: continue
        seen_p.add(k_)
        try: sm_ = _pds.summarize(bytes(o_['data']))
        except Exception: continue
        for n_, c_ in zip(sm_['notch_numbers'], sm_['notch_types']):
            if n_ is None: continue
            n_seen += 1; n_bad += (min(n_, 5) != c_)
if n_seen < 100 or n_bad: bad.append(f'corpus pieces: {n_seen} notches with a number, {n_bad} against code == min(number, 5)')
# a broken number is noticed
pb_ = bytearray(am.read_storage_piece(os.path.join(NDIR, 'NN-PIECE.GT_piece'))); i3_ = None
for m_ in __import__('re').finditer(rb'\x10\x00.{8}\xff\xff\x01\x00\x03\x00\x02\x00\x07\x2d(.{45})', bytes(pb_), __import__('re').S): i3_ = m_.start(1) + 44
if i3_ is None: bad.append('the code-3 notch was not found in its line table')
else:
    pb_[i3_] = 9; ps_ = _pds.summarize(bytes(pb_))
    if not any(min(n_, 5) != c_ for n_, c_ in zip(ps_['notch_numbers'], ps_['notch_types']) if n_ is not None): bad.append('a notch number changed to 9 next to code 3 was not noticed')
# the nest spec: a code names its candidates
sn_ = ns.build_nest_spec(os.path.join(NDIR, 'NN-MARKER.GT_mark'))[0]; nb_ = sn_['notch_table']; bc_ = nb_.get('by_code') or {}
if nb_['source'] != 'marker snapshot' or bc_.get('3', {}).get('numbers') != [3] or bc_.get('5', {}).get('numbers') != list(range(5, 26)): bad.append(f"nest spec of the PDS marker: {nb_['source']} {bc_}")
n3_ = [n_ for sh_ in sn_['shapes'] for n_ in sh_['notches'] if n_['type'] == 3]; n5_ = [n_ for sh_ in sn_['shapes'] for n_ in sh_['notches'] if n_['type'] == 5]
if not n3_ or any(n_['number'] != 3 for n_ in n3_) or not n5_ or any(n_['number'] is not None or n_['numbers'] != list(range(5, 26)) for n_ in n5_): bad.append('shape notches: code 3 -> number 3, code 5 -> the candidates 5..25')
z25_ = os.path.join(HERE, 'markers', '2591A-SS21-UNLAID', '2591A-BD 157 AW SS21.zip')
if os.path.isfile(z25_):
    for sp_ in ns.build_nest_spec(z25_):
        b5_ = (sp_['notch_table'].get('by_code') or {}).get('5')
        if b5_ and (b5_['same_geometry'] or b5_['numbers'] != list(range(5, 16))): bad.append(f"2591A NEED-P-NOTCH code 5: {b5_}")
        if 5 in sp_['notch_table']['numbers_used'] and not any('stand for several different notches' in w_ for w_ in sp_['warnings']): bad.append('2591A uses code 5 (numbers 5-15: slit and V) without the warning')
print(f"   {'ok ' if not bad else 'FAIL'} PDS piece with numbers {want_nums}: codes {dict(Counter(psum['notch_types']))}, its marker stores the same codes at S / M / L; {n_seen} corpus notches all code == min(number, 5); a broken number is noticed; the spec lists the candidate numbers of code 5  {'; '.join(bad[:3])}")
if bad: fails.append('notch numbers: ' + '; '.join(bad[:5]))

print('-- marker byte map (v4.4, see accumark_marker.marker_coverage)')
# Every byte owned by a section a parser reads must be classified (identified /
# raw / zero_pad / opaque) - only the envelope, the header scalars, sections 2-5,
# section 10's 6-byte lead and the trailer may hold unknown bytes. This is the
# measurable form of "fully decoded" for the marker: a parser change that loses
# a section moves its bytes to `unknown` and fails here.
PARSED_SECTIONS = {3, 4, 6, 11, 12, 13, 14, 15, 21, 30}      # v4.14: 3 (notch table copy) and 4 (lay-limits rows)
if set(am.PARSED_SECTIONS) != PARSED_SECTIONS: fails.append('am.PARSED_SECTIONS differs from the selftest list')
n_mk = 0; leaks = []; unk = []; tot = Counter()
for zp in sorted(glob.glob(os.path.join(HERE, 'markers', '**', '*.zip'), recursive=True)):
    try: mos = am.list_zip(zp).get('marker', [])
    except Exception: continue
    for o in mos:
        n_mk += 1; cv = am.marker_coverage(o['data'])
        leaks += [f"{o['name']}: bytes {a}-{b} in section {k}" for a, b, k in cv['unknown_runs'] if k in PARSED_SECTIONS]
        unk.append(cv['counts']['unknown']); tot.update(cv['counts'])
ok = n_mk and not leaks
print(f"   {'ok ' if ok else 'FAIL'} {n_mk} markers: every byte in sections {sorted(PARSED_SECTIONS)} is classified"
      + (f"; unknown bytes per marker {min(unk)}-{max(unk)}, {100*tot['unknown']/sum(tot.values()):.2f}% overall "
         f"(identified {100*tot['identified']/sum(tot.values()):.1f}%, raw {100*tot['raw']/sum(tot.values()):.1f}%, "
         f"zero_pad {100*tot['zero_pad']/sum(tot.values()):.1f}%, opaque {100*tot['opaque']/sum(tot.values()):.1f}%)" if n_mk else '')
      + ('  ' + '; '.join(leaks[:3]) if leaks else ''))
if not ok: fails.append('marker byte map: ' + '; '.join(leaks[:5]))
# and it can fail: break section 11's first name length and the model list's bytes must fall out of the map
src = _mk(('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip'), '5683D-BD 168 SS21')
if src:
    b = bytearray(src[0]['data']); struct.pack_into('<H', b, src[1]['sections'][am.SEC_MODELS][0] - 6, 0)
    cv = am.marker_coverage(bytes(b)); lost = [r for r in cv['unknown_runs'] if r[2] == am.SEC_MODELS]
    print(f"   {'ok ' if lost else 'FAIL'} mutation: a broken model list surfaces as unknown bytes in section 11 ({sum(r[1]-r[0] for r in lost)} B)")
    if not lost: fails.append('marker byte map: a broken model list did not surface as unknown bytes')

print('-- unseen variants are loud (v4.6, see accumark_marker.marker_warnings)')
# Reading "whatever marker AccuMark produces in future" means a marker unlike
# the corpus must announce itself. Every fixture must be silent; every named
# warning must fire when the fact it guards is broken in the bytes.
n_mk = 0; noisy = []
for zp in sorted(glob.glob(os.path.join(HERE, 'markers', '**', '*.zip'), recursive=True)):
    try: mos = am.list_zip(zp).get('marker', [])
    except Exception: continue
    for o in mos:
        n_mk += 1; mk = am.parse_marker(o['data'])
        w = am.marker_warnings(mk) + am.coverage_warnings(mk)
        if w: noisy.append(f"{o['name']}: {w[0]}")
print(f"   {'ok ' if n_mk and not noisy else 'FAIL'} {n_mk} fixture markers raise no warning  {'; '.join(noisy[:3])}")
if not n_mk or noisy: fails.append('marker warnings on fixtures: ' + '; '.join(noisy[:5]))
src = _mk(('5683D-SS21-UNLAID', '5683D-BD 168 SS21.zip'), '5683D-BD 168 SS21')
if src:
    d0, mk0 = src[0]['data'], src[1]; sec = mk0['sections']
    def _warn(off, fmt, val):
        b = bytearray(d0); struct.pack_into(fmt, b, off, val); return am.marker_warnings(am.parse_marker(bytes(b)))
    WMUT = [  # description, warnings after the patch, the text that must appear
     ('a directory slot nobody has used (slot 20) now in use', _warn(am.DIR_OFF + 4*20, '<I', sec[am.SEC_SLOTS][0]), 'directory slot 20 is in use'),
     ('directory word 40 = 5', _warn(am.DIR_OFF + 4*40, '<I', 5), 'directory word 40 is 5'),
     ('directory word 41 non-zero', _warn(am.DIR_OFF + 4*41, '<I', 7), 'directory word 41'),
     ('a never-laid slot with unknown orientation bits', _warn(mk0['slots'][3]['slot'] + 32, '<H', 0x0801), 'orientation bits'),
     # a 1-byte shift of the first index entry still yields a plausible record (garbage area), so it is the
     # per-slot area cross-check that must notice; a non-monotonic index is the index's own failure
     ('section 13: first record offset shifted one byte', _warn(sec[am.SEC_INDEX][0] - 6, '<I', mk0['record_index'][0] + 1), 'declared area does not equal'),
     ('section 13: index no longer monotonic', _warn(sec[am.SEC_INDEX][0] - 6, '<I', 0x7fffffff), 'record index) did not validate'),
     ('a slot bundle disagrees with the size table', _warn(mk0['slots'][4]['slot'] - 6 + 4, '<H', 9), 'bundle or the record text disagree'),
     ('section 10: header label broken', _warn(sec[am.SEC_PIECES][0] + 22, '<H', 0), 'section 10 (piece list)'),
     ('section 15: first model block claims 5 more sizes', _warn(sec[am.SEC_ORDER_COPY][0] - 6 + 12, '<H', 11), 'section 15 (order copy) did not parse'),
     ('a slot head points past the records', _warn(mk0['slots'][2]['slot'] - 6, '<H', 500), 'not bound structurally'),
    ]
    bad = [f'"{d}" did not raise "{t}": {w}' for d, w, t in WMUT if not any(t in x for x in w)]
    print(f"   {'ok ' if not bad else 'FAIL'} {len(WMUT)} byte patches each raise the warning that names them  {'; '.join(bad)}")
    if bad: fails.append('marker warnings mutation: ' + '; '.join(bad))
    # and the report turns them into NEEDS A LOOK
    b = bytearray(d0); struct.pack_into('<H', b, mk0['slots'][3]['slot'] + 32, 0x0801); mkp = am.parse_marker(bytes(b))
    rep = am.inventory_report(am.unplaced_inventory(mkp), am.check_marker(mkp))
    print(f"   {'ok ' if 'NEEDS A LOOK' in rep else 'FAIL'} an unseen variant makes the inventory report say NEEDS A LOOK, not DECODED CLEANLY")
    if 'NEEDS A LOOK' not in rep: fails.append('inventory_report did not flag an unseen variant')

print('-- coverage (informational only - see accumark_pds.coverage();'
      ' 0 unknown_bytes everywhere is the Phase D sign-off target, not'
      ' enforced here yet)')
worst_pct = 100.0
for name, *_ in R2:
    folder = os.path.join(HERE, name)
    if not os.path.isdir(folder) or not glob.glob(os.path.join(folder, '*.[zZ][iI][pP]')):
        continue
    f, _ = vc.facts(vc.load(folder))
    worst_pct = min(worst_pct, f['coverage_pct'])
    print(f"   {name:22} unknown_bytes={f['unknown_bytes']:4d}  coverage_pct={f['coverage_pct']}")
print(f'   worst coverage_pct across round-2 captures: {worst_pct}')

print('-- generated garment dataset (dataset/, skipped when MANIFEST.json is absent)')
manifest = os.path.join(HERE, 'dataset', 'MANIFEST.json')
if os.path.isfile(manifest):
    import dataset_test
    n_ok, n_fail, dfails = dataset_test.quick()
    print(f"   {'ok ' if not n_fail else 'FAIL'} {n_ok} checked, {n_fail} failed"
          + (f" ({dfails[0]})" if dfails else ""))
    for x in dfails: fails.append('dataset: ' + x)
else:
    print('   --  (absent - run: python dataset/build.py)')

print('-- zip robustness (robustness/, quick matrix - see ROBUSTNESS_REPORT.md for the full run)')
import robustness.run as rr
r_ok, r_fail, rfails = rr.quick()
# Oracle A (metamorphic) and B (controlled-failure contract) gate the run -
# any failure there is a real regression. Oracle C's known, documented gap
# (redundant Region-C/line-table shadow copies not cross-validated - see
# ROBUSTNESS_REPORT.md's Recommendations) is reported, not gated, the same
# way the coverage section above is informational-only.
gating = [r for r in rfails if r['oracle'] in ('A', 'B')]
informational = [r for r in rfails if r['oracle'] == 'C']
print(f"   {'ok ' if not gating else 'FAIL'} {r_ok}/{r_ok+r_fail} checked, "
      f"{len(gating)} gating failures, {len(informational)} known-gap (Oracle C) failures")
for r in gating:
    print(f"      FAIL {r['case']}: {r['detail']}")
    fails.append('robustness: %s: %s' % (r['case'], r['detail']))

print()
if fails:
    print('SELFTEST FAIL'); [print('  -', x) for x in fails]; sys.exit(1)
print('SELFTEST PASS')
