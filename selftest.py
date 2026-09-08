#!/usr/bin/env python3
"""selftest.py - prove the decoder + validator work on this machine before
touching AccuMark.  Decodes every capture under captures/, checks each against
its DXF, and re-runs the known structural-diff cases (including the two that
must report NO change).  Exits non-zero on any failure."""
import glob, os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import accumark_pds as ap
import verify_capture as vc

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

fails = []
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
R2 = [  # folder, baseline, {fact: want}, structural_change want (or None)
 ('CAP-C00-BASE',          None,               dict(piece_records=1, perimeter_points=4), None),
 ('CAP-C01-REEXPORT',      'CAP-C00-BASE',     dict(piece_records=1), 'no'),
 ('CAP-C02-SAVEAS-NOEDIT', 'CAP-C00-BASE',     dict(piece_records=1), 'no'),
 ('CAP-C50-DRILL1',        'CAP-C00-BASE',     dict(drill_points=1, piece_records=2), 'yes'),
 ('CAP-C30-SEAM-UNEVEN',   None,               dict(uneven_seam='yes', cutline_records=3), None),
 ('CAP-C31-SEAM-TAPER',    'CAP-C00-BASE',     dict(uneven_seam='yes', cutline_records=2), 'yes'),
 ('CAP-C20-RULE-DISTINCT', 'CAP-C02-SAVEAS-NOEDIT', dict(graded_points=1, n_break_rows=8, rul_n_rules=1), 'yes'),
 ('CAP-C21-RULE-TWO',      'CAP-C20-RULE-DISTINCT', dict(graded_points=2, n_break_rows=8, rul_n_rules=2), 'yes'),
 ('CAP-C22-RULE-NONE',     'CAP-C20-RULE-DISTINCT', dict(graded_points=0, n_break_rows=8), None),
 ('CAP-C10-PENT',          'CAP-C00-BASE',     dict(perimeter_points=5), None),
 ('CAP-C11-HEX',           'CAP-C00-BASE',     dict(perimeter_points=6), None),
 ('CAP-C40-NOTCH-TYPES',   None,               dict(notches=4, notch_types='2;4;5;1'), None),
 ('CAP-C41-NOTCH-WIDTH',   None,               dict(notches=2, notch_types='1;1', perimeter_points=6), None),
 ('CAP-C42-NOTCH-ALLEDGES', None,              dict(notches=4, notch_types='1;1;1;1', segment_points='3;3;3;3'), None),
 ('CAP-C60-CUTOUT',         None,              dict(perimeter_points=4, cutout_points='25'), None),
 ('CAP-C61-MIRROR',         None,              dict(perimeter_points=3, graded_points=1), None),
 ('CAP-C62-DART',           None,              dict(perimeter_points=7, piece_records=2), None),
 ('CAP-C70-PASTED',         None,              dict(piece_records=1, category='CAP-C00-BASE'), None),
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
    print(f"   {'ok ' if not bad else 'FAIL'} {name:22} {'; '.join(bad) if bad else 'as expected'}")
    if bad: fails.append(f'{name}: ' + '; '.join(bad))

print()
if fails:
    print('SELFTEST FAIL'); [print('  -', x) for x in fails]; sys.exit(1)
print('SELFTEST PASS')
