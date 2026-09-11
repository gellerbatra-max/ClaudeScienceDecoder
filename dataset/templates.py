"""dataset/templates.py - the corpus fixtures used as source shapes for the
generated garment dataset (see dataset/build.py).

Nothing here invents new AccuMark record structure: every generated piece is
a genuine corpus piece object with its coordinate VALUES overwritten in
place (dataset/write.py), never its layout. coord_offsets() locates every
byte position a coordinate value occupies by walking the decoder's own
parse (accumark_pds.decode_piece_block) rather than by guessing offsets or
blind byte search - the latter was tried during this session's probing and
found to silently corrupt output when a newly-written value collided with
an as-yet-unpatched old one (see MARKER_DECODE_PLAN.md / CHANGELOG.md).

Templates and what they carry (point count, notch/dart presence, grading):
established empirically against this repo's existing fixture corpus - see
build.py's module docstring for the measured native sizes.
"""
import os, zipfile
import accumark_pds as ap
import accumark_marker as am

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# name -> (zip path relative to repo root, 'pattern'|'marker')
# 'pattern': a plain <name>.tmp + ver.5 export - decode_zip/list_zip find the
#   single piece directly. 'marker': the piece is embedded inside a marker
#   zip (list_zip / am.list_zip must be used to extract it).
TEMPLATE_SOURCES = {
    'rect4':   ('CAP-C00-BASE/CAP-C00-BASE.zip', 'pattern'),
    'pent5':   ('CAP-C10-PENT/CAP-C10-PENT.ZIP', 'pattern'),
    'hex6':    ('CAP-C11-HEX/CAP-C11-HEX.ZIP', 'pattern'),
    'dart7':   ('CAP-C62-DART/CAP-C62-DART.ZIP', 'pattern'),
    'notch8':  ('CAP-C40-NOTCH-TYPES/CAP-C40-NOTCH-TYPES.ZIP', 'pattern'),
    'curve34': ('captures/TASK6-CURVE/TASK6-CURVE.ZIP', 'pattern'),
    # sizes 2-18 (9 sizes), the only rect4-shaped template with that range -
    # the piece embedded in the grading-fixture marker built earlier this
    # project (MARKER_DECODE_PLAN.md).
    'rect4g':  ('markers/CLAUDE-GRADE-MARKER/CLAUDE-GRADE-MARKER.zip', 'marker'),
}


def _load_pattern_zip(rel):
    path = os.path.join(HERE, rel)
    with zipfile.ZipFile(path) as z:
        d = [z.read(i) for i in z.infolist() if z.read(i).startswith(ap.MAGIC)]
    pieces = [x for x in d if len(x) > 0x80 and ap.u16(x, 0x7a) == 20]
    assert len(pieces) == 1, (rel, len(pieces))
    return pieces[0]


def _load_marker_zip_piece(rel):
    path = os.path.join(HERE, rel)
    objs = am.list_zip(path)
    pieces = objs.get('piece', [])
    assert len(pieces) == 1, (rel, len(pieces))
    return pieces[0]['data']


def load_template(name):
    """-> dict(data, block, old_name (str), old_name_bytes, sizes, grade_rules).
    `data` is the raw piece object bytes (post-magic, pre-anything-else);
    `block` is accumark_pds.decode(data)['blocks'][0]."""
    rel, kind = TEMPLATE_SOURCES[name]
    data = _load_pattern_zip(rel) if kind == 'pattern' else _load_marker_zip_piece(rel)
    dec = ap.decode(data)
    # a second block, when present, is the stale pre-edit duplicate
    # (FORMAT_SPEC.md section 8: "Decode record 0 and ignore the rest") -
    # dart7/CAP-C62-DART and notch8/CAP-C40-NOTCH-TYPES are genuinely
    # 2-record pieces, which decode() now correctly reports (fixed
    # 2026-09-11 - see CHANGELOG.md); block 0 is always the one that
    # matters, matching every other caller in this codebase.
    assert dec['blocks'], name
    block = dec['blocks'][0]
    s = ap.summarize(data)
    old_name = s['header_piece_name']
    return dict(
        template=name, data=data, block=block,
        old_name=old_name, old_name_bytes=old_name.encode('latin1'),
        sizes=[x['name'] for x in block['meta']['sizes']],
        grade_rules=s.get('grade_rules', {}),
        perimeter=[(p['x'], p['y']) for p in block['perimeter']],
    )


def coord_offsets(data, block):
    """{(x, y): [(x_byte_offset, y_byte_offset), ...]} for every occurrence
    of every perimeter coordinate pair this block's own parse identified:
    the point table (perimeter + closing + internal lines/notches/drills),
    both Region-C snapshots, and the line table's 16-byte point records.
    Every offset here is a location accumark_pds itself decoded a coordinate
    from - retargeting only ever overwrites bytes the decoder already
    proved are coordinate bytes, never bytes reached by inference."""
    out = {}

    def add(pt, xo, yo):
        out.setdefault((pt['x'], pt['y']), []).append((xo, yo))

    for p in block['perimeter']:
        add(p, p['offset'] + 2, p['offset'] + 6)
    if block.get('closing'):
        c = block['closing']; add(c, c['offset'] + 2, c['offset'] + 6)
    for seg in block.get('internal_lines') or []:
        for p in seg:
            add(p, p['offset'] + 2, p['offset'] + 6)
    tail = block.get('tail') or {}
    rc = tail.get('region_c')
    if rc:
        for p in rc.get('snapshot1') or []:
            add(p, p['offset'] + 2, p['offset'] + 6)
        for p in rc.get('snapshot2') or []:
            add(p, p['offset'] + 2, p['offset'] + 6)
    for rec in tail.get('line_records') or []:
        for tp in rec.get('points') or []:
            out.setdefault((tp['x'], tp['y']), []).append((tp['offset'], tp['offset'] + 4))
    return out
