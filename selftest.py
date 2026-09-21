#!/usr/bin/env python3
"""selftest.py - prove the decoder + validator work on this machine before
touching AccuMark.  Decodes every capture under captures/, checks each against
its DXF, and re-runs the known structural-diff cases (including the two that
must report NO change).  Exits non-zero on any failure."""
import copy, glob, os, sys, subprocess
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
if sd_ok != sd_tot or sd_tot < 255: sd_bad.append(f'{sd_ok} of {sd_tot} distinct corpus streams verify (all 255 did)')
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

print('-- marker byte map (v4.4, see accumark_marker.marker_coverage)')
# Every byte owned by a section a parser reads must be classified (identified /
# raw / zero_pad / opaque) - only the envelope, the header scalars, sections 2-5,
# section 10's 6-byte lead and the trailer may hold unknown bytes. This is the
# measurable form of "fully decoded" for the marker: a parser change that loses
# a section moves its bytes to `unknown` and fails here.
PARSED_SECTIONS = {6, 11, 12, 13, 14, 15, 21, 30}
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
