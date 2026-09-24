#!/usr/bin/env python3
"""accumark_notch - read an AccuMark NOTCH PARAMETER TABLE (`P-NOTCH`, `.GT_notpt`) (v4.10).

    python accumark_notch.py "<export>.zip" [--json]          # every notch table in a ZIP
    python accumark_notch.py C:\\userroot\\storage\\AREA\\notpt\\P-NOTCH.GT_notpt

The table defines the notches a piece can carry: up to 99, each with a TYPE (Slit, T, V, Castle, Left Check, Right Check, U, No Lift Slit), a
PERIMETER WIDTH (the gap at the piece edge), an INSIDE WIDTH (the width at the bottom) and a DEPTH (positive = an internal notch, negative = an external
one such as a Castle or an external V). A notch on a piece is identified by its NOTCH NUMBER, the row of this table; a marker's stream keeps only the CODE min(number, 5) (v4.15: 1-4 are the numbers, 5 means 5 or higher).

Byte format, VERIFIED against the Notch editor (Notch.exe): a table saved from the editor with one row of every type and distinct numbers
(`ZZNT-X1`, `ZZNT-X2` in `notch/`), plus the real `NEED-P-NOTCH`, `V-NOTCH-ALL CUSTOMERS` and the default `P-NOTCH`, each shown by the editor and
compared with the bytes:

    table (a `.GT_notpt` file has these bytes from 0x90; an export ZIP object from 0x8a, `payload_len` of them)
      5 x ( i32 perimeter, i32 inside, i32 depth )      the first five notches again, in the older three-value layout (always equal to records 1-5)
      u32 N                                             the number of records = the highest notch number kept (a table ends at its last defined notch)
      N x ( u32 type, i32 perimeter, i32 inside, i32 depth )     record k = notch number k
      [ u32 0 ]                                         optional trailer
    lengths are x 10000 in INCHES (0.30 cm = 1181, -0.20 cm = -787); type 0 = None (an undefined number), 1 Slit, 2 T, 3 V, 4 Castle, 5 Left Check,
    6 Right Check, 7 U, 8 No Lift Slit (the 8 types the editor offers, in its list order).

A table whose length is not exactly 64 + 16 N (+ 4 zero bytes), whose first five triplets differ from records 1-5, or with an unknown type code is refused.
"""
import json, os, struct, sys

__version__ = '1.0'

NOTCH_TYPES = {0: 'none', 1: 'slit', 2: 't', 3: 'v', 4: 'castle', 5: 'left_check', 6: 'right_check', 7: 'u', 8: 'no_lift_slit'}
NOTCH_LABELS = {0: 'None', 1: 'Slit', 2: 'T', 3: 'V', 4: 'Castle', 5: 'Left Check', 6: 'Right Check', 7: 'U', 8: 'No Lift Slit'}
_FILE_OFF, _EXPORT_OFF, _HEAD = 0x90, 0x8a, 64


class NotchTableError(ValueError):
    pass


def _parse(t):
    if len(t) < _HEAD: raise NotchTableError('table shorter than its header')
    n = struct.unpack_from('<I', t, 60)[0]
    if n > 99: raise NotchTableError(f'{n} records (at most 99)')
    end = _HEAD + 16 * n
    if len(t) not in (end, end + 4) or (len(t) == end + 4 and any(t[end:])): raise NotchTableError(f'length {len(t)} is not 64 + 16 x {n} (+ a zero dword)')
    legacy = [struct.unpack_from('<iii', t, 12 * i) for i in range(5)]
    rows = []
    for i in range(n):
        ty, per, ins, dep = struct.unpack_from('<Iiii', t, _HEAD + 16 * i)
        if ty not in NOTCH_TYPES: raise NotchTableError(f'notch {i + 1}: unknown type code {ty}')
        rows.append((ty, per, ins, dep))
    for i in range(5):
        want = rows[i][1:] if i < n else (0, 0, 0)
        if legacy[i] != want: raise NotchTableError(f'the first-five triplets differ from record {i + 1}')
    return n, rows, len(t) == end + 4


def parse_notch_table(source, name=None):
    """-> dict(name, count, notches, by_number, trailer). `notches` = the DEFINED notches (type != none), each dict(number, type, type_name, label,
    perimeter_in, inside_in, depth_in, direction) with lengths in inches; `by_number` maps number -> that dict. `source`: an object dict from
    accumark_marker.list_zip, raw table bytes, or a `.GT_notpt` path. Raises NotchTableError on anything that does not close exactly."""
    if isinstance(source, str):
        d = open(source, 'rb').read(); t = d[_FILE_OFF:]; name = name or os.path.splitext(os.path.basename(source))[0]
    elif isinstance(source, dict):
        d = source['data']; t = bytes(d[_EXPORT_OFF:_EXPORT_OFF + source['payload_len']]); name = name or source.get('name')
        if len(t) != source['payload_len']: raise NotchTableError('object shorter than its own payload length')
    else: t = bytes(source)
    try: n, rows, trailer = _parse(t)
    except struct.error as e: raise NotchTableError(str(e))
    notches = []
    for i, (ty, per, ins, dep) in enumerate(rows):
        if ty == 0: continue
        notches.append(dict(number=i + 1, type=ty, type_name=NOTCH_TYPES[ty], label=NOTCH_LABELS[ty], perimeter_in=per / 1e4, inside_in=ins / 1e4, depth_in=dep / 1e4,
                            direction='external' if dep < 0 else 'internal'))
    return dict(name=name, count=n, notches=notches, by_number={x['number']: x for x in notches}, trailer=trailer,
                basis='decoded: every field verified against the Notch editor')


def parse_notch_snapshot(t, name=None):
    """v4.14: the notch table a MARKER carries as its own section 3 (a copy taken when the marker was made). Byte for byte the table object's payload (36 of 58 markers, +6 with the optional
    zero dword), or - on 16 scratch-set markers (written by another path) - only its first 60 bytes, the five older-layout triplets (perimeter, inside, depth) of notches 1-5 with no type code and no count.
    -> the dict of parse_notch_table plus `vintage` ('table' | 'legacy-5-triplets'); a legacy notch has `type` None. Raises NotchTableError for any other length that does not close."""
    t = bytes(t)
    if len(t) != 60:
        r = parse_notch_table(t, name=name); r['vintage'] = 'table'; return r
    legacy = [struct.unpack_from('<iii', t, 12 * i) for i in range(5)]
    notches = [dict(number=i + 1, type=None, type_name=None, label=None, perimeter_in=p / 1e4, inside_in=s / 1e4, depth_in=d / 1e4, direction=None if d == 0 else ('external' if d < 0 else 'internal'))
               for i, (p, s, d) in enumerate(legacy) if (p, s, d) != (0, 0, 0)]
    return dict(name=name, count=5, notches=notches, by_number={x['number']: x for x in notches}, trailer=False, vintage='legacy-5-triplets',
                basis='partial: only the five older-layout triplets of notches 1-5 (no type codes, no count) - what the older engine copied into the marker')


def load_zip_notch_tables(path, listing=None):
    """{name: parsed table} for every notch-table object of an export ZIP (unreadable ones listed in `_errors`)."""
    import accumark_marker as am
    out = {}; errs = []
    for o in (listing if listing is not None else am.list_zip(path)).get('notch_table', []):
        try: out[o['name']] = parse_notch_table(o)
        except NotchTableError as e: errs.append((o['name'], str(e)))
    if errs: out['_errors'] = errs
    return out


def describe(t):
    L = [f"{t.get('name')}: {t['count']} record(s), {len(t['notches'])} defined"]
    for n in t['notches']:
        L.append(f"  {n['number']:>3} {n['label']:<12} perimeter {n['perimeter_in'] * 2.54:.2f} cm  inside {n['inside_in'] * 2.54:.2f} cm  depth {n['depth_in'] * 2.54:+.2f} cm ({n['direction']})")
    return '\n'.join(L)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv); as_json = '--json' in a; a = [x for x in a if x != '--json']
    if not a: print(__doc__); return 2
    tabs = {}
    for f in a:
        if f.lower().endswith('.zip'): tabs.update({f'{os.path.basename(f)}:{k}': v for k, v in load_zip_notch_tables(f).items() if k != '_errors'})
        else: tabs[f] = parse_notch_table(f)
    if as_json: print(json.dumps(tabs, indent=1, default=str))
    else:
        for v in tabs.values(): print(describe(v))
    return 0


if __name__ == '__main__':
    sys.exit(main())
