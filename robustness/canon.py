"""robustness/canon.py - canonicalise a decode result for metamorphic
comparison (Oracle A) and corruption detection (Oracle C): two decodes are
"the same answer" iff their canon() strings are equal.

Dropped deliberately (variant-dependent, not decoder output): the zip
member name (`member`), raw object bytes (`data`/`payload` - hashed
instead, see below), and list_zip's raw `objects` sub-dict when it appears
nested inside a place_marker() result (already covered by canonicalising
list_zip's own output separately).

Kept: for every object, (kind, name, type, payload_len, sha256(payload)) -
hashing the payload is what proves "same bytes in, same bytes out" without
carrying megabytes through the comparison. For a marker: header scalars,
every placement, every placed outline, and check_marker's pass/fail list.

Every collection is sorted by a stable key before serialising - list_zip
and place_marker both return objects in zip-namelist order, which several
Oracle-A variants (reversed order, shuffled order) deliberately change,
so raw list order must never be compared.

Floats are rounded to 1e-9 before serialising: every real coordinate in
this format is an int32 in 1e-4 inch (or an f64 slot value with far more
precision headroom than that), so nothing genuine sits within 1e-9 of a
rounding boundary - anything that moves at that scale is a real
difference, not float noise.
"""
import hashlib, json


def _round(x):
    if isinstance(x, float):
        return round(x, 9)
    return x


def _obj_key(o):
    return dict(
        kind=o.get('kind'), name=o.get('name'), type=o.get('type'),
        payload_len=o.get('payload_len'),
        payload_sha256=hashlib.sha256(o.get('payload', b'')).hexdigest(),
    )


def canon_list_zip(objs):
    """objs: the dict returned by accumark_marker.list_zip()."""
    out = {}
    for kind, items in objs.items():
        if kind == 'duplicate_member_names':
            out[kind] = sorted(items)
            continue
        rows = [_obj_key(o) for o in items]
        rows.sort(key=lambda r: (r['kind'], r['name'], r['payload_sha256']))
        out[kind] = rows
    return json.dumps(out, sort_keys=True, default=str)


def _placement_key(s):
    return dict(
        piece=s.get('piece'), size=s.get('size'),
        x=_round(s.get('x')), y=_round(s.get('y')),
        home_x=_round(s.get('home_x')), home_y=_round(s.get('home_y')),
        orient_code=s.get('orient_code'), area=_round(s.get('area')),
        bundle=s.get('bundle'),
    )


def canon_place_marker(res):
    """res: the dict returned by accumark_marker.place_marker()."""
    markers = []
    for mkr in res['markers']:
        mk = mkr['marker']
        placements = sorted((_placement_key(s) for s in mk['placements']),
                             key=lambda r: json.dumps(r, sort_keys=True, default=str))
        outlines = []
        for s, name, size, outline, note in mkr['placed']:
            outlines.append(dict(
                piece=name, size=size,
                outline=[[_round(x), _round(y)] for x, y in outline] if outline else None,
            ))
        outlines.sort(key=lambda r: json.dumps(r, sort_keys=True, default=str))
        checks = sorted([n, ok] for n, ok, _ in mkr['checks'])
        markers.append(dict(
            name=mk['name'], width=_round(mk['width']), length=_round(mk['length']),
            util=_round(mk['util']), total_area=_round(mk['total_area']), laid=mk['laid'],
            placements=placements, outlines=outlines, checks=checks,
        ))
    markers.sort(key=lambda r: json.dumps(r, sort_keys=True, default=str))
    piece_errors = sorted(res.get('piece_errors', {}).keys())
    pieces = sorted((n, dict(sizes=[s['name'] for s in p['block']['meta']['sizes']])
                      if p else None) for n, p in res['pieces'].items())
    return json.dumps(dict(markers=markers, pieces=pieces, piece_errors=piece_errors),
                       sort_keys=True, default=str)


def canon_decode(dec):
    """dec: the dict returned by accumark_pds.decode()."""
    blocks = []
    for b in dec['blocks']:
        perim = [[_round(p['x']/1e4), _round(p['y']/1e4)] for p in b['perimeter']]
        blocks.append(dict(
            n_perimeter=len(b['perimeter']), perimeter=perim,
            n_notches=sum(1 for p in b['perimeter'] if p['is_notch']),
            sizes=[s['name'] for s in b['meta']['sizes']],
            name=b['meta']['name'],
        ))
    return json.dumps(dict(blocks=blocks, block_errors=len(dec.get('block_errors') or [])),
                       sort_keys=True, default=str)


def canon_piece_full(data):
    """Wider than canon_decode(): also runs verify_capture.facts(), which
    exercises accumark_pds's OWN cross-checks - line_table_consistent
    (the line table against the perimeter) and region_c_consistent (Region
    C's two perimeter snapshots against the perimeter, added alongside the
    v2 parse_region_c fix this check validates - see CHANGELOG.md) -
    independently of block['perimeter'] itself. A coordinate is stored 5-7
    times per point (point table, two Region-C snapshots, the line table);
    corrupting a redundant copy that isn't the point-table copy leaves
    block['perimeter'] unchanged, so canon_decode() alone would call it
    inert. facts() is what actually proves whether that redundant copy is
    cross-validated by anything the decoder does."""
    import verify_capture as vc
    dec_canon = canon_decode(__import__('accumark_pds').decode(data))
    try:
        f, _ = vc.facts(dict(folder='.', zip='mem', data=data, dxf=None, rul=None))
        facts_part = dict(line_table_consistent=f.get('line_table_consistent'),
                           region_c_consistent=f.get('region_c_consistent'),
                           notches=f.get('notches'), perimeter_points=f.get('perimeter_points'),
                           graded_points=f.get('graded_points'),
                           unknown_bytes=f.get('unknown_bytes'))
    except Exception as e:
        facts_part = dict(error='%s: %s' % (type(e).__name__, e))
    return dec_canon + '|' + json.dumps(facts_part, sort_keys=True, default=str)
