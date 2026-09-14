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
                gap_checked += 1
                import struct as _struct
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
 ('2303-BD137-UNLAID', '2303-BD 137.zip', dict(laid='no', placements=0, slots=97, records=66, pieces_listed=12, bound=0), None),
 ('2303-BD137-PLACED', '2303-BD 137 PLACED.zip', dict(laid='yes', placements=97, bundles=61, bound=97, identity='yes',
                                                    width_cm=137.0, length_cm=377.68, util_pct=71.51, bbox_ok=97, area_ok=12, area_pairs=12,
                                                    dxf_centres=97, dxf_outlines_checked=97,
                                                    folds='2303-B1-A1- OUCF-SP24;2303-B1-A2- OUCF-SP24;2303-B1-DD2- OUCF-SP24;2303-B1-E3- OUCF-SP24'), 'dxf'),
 ('2303-CP150-JULY',   '2303-CP 150 CPL.zip', dict(laid='yes', placements=1, bound=1, identity='yes', dxf_centres=1, area_ok=1, bbox_ok=4), 'dxf'),
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
                                                    bbox_ok=2, dxf_centres=2, dxf_outlines_checked=2), 'dxf'),
]
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
        # 0.0015 in, not the July markers' 0.001: a cm-vintage drawn DXF
        # (2303-BD137-PLACED) round-trips through a /2.54 conversion the
        # inch-native July DXFs don't, costing a little precision - not a
        # decode error (worst seen: July 0.0008, this one 0.0012).
        if dxf and f.get('dxf_centre_worst', 9) > 0.0015: bad.append(f"dxf_centre_worst={f.get('dxf_centre_worst')}")
        print(f"   {'ok ' if not bad else 'FAIL'} {f['name']:30} {'; '.join(bad) if bad else 'as expected'}")
        if bad: fails.append(f"{f['name']}: " + '; '.join(bad))

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
