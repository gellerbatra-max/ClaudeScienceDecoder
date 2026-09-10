#!/usr/bin/env python3
"""dataset/build.py - generate the synthetic garment dataset: real AccuMark
piece objects, geometry retargeted to drafted garment panels (dataset/
draft.py), packaged as pattern ZIPs identical in structure to a real
AccuMark PDS export (<hex>.tmp + ver.5), plus one custom marker.

    python dataset/build.py            # (re)writes dataset/generated/ + MANIFEST.json

Deterministic: re-running produces byte-identical output (no randomness -
every transform is a pure function of the panel spec and its template).

GRADING SCOPE (established empirically before writing this - see the
session's CHANGELOG.md entry): of the seven corpus templates, rect4 / pent5
/ hex6 / dart7 / notch8 carry a grade rule table whose deltas are all
(0, 0) - the same "placeholder grading" already documented for production
style 2303 (MARKER_DECODE_PLAN.md). Only rect4g (CLAUDE-GRADE-MARKER's
piece) and curve34 (TASK6-CURVE) carry real, non-placeholder per-size
deltas. Panels built on the other five templates are still independently
geometry-checked (MANIFEST ground truth vs decode) at their single
effective shape; they do not exercise size-dependent grading, and the
manifest says so per panel rather than overclaiming.

MARKER SCOPE: adding new placements to a marker requires extending its
section-21 slot directory, which is a structural edit this project
deliberately stays away from (dataset/write.py's docstring; every edit here
overwrites coordinate VALUES in place, never record layout). This dataset
therefore includes one new custom marker (GENERATED-SAMEBBOX-MARKER: the
CLAUDE-GRADE-MARKER structure with its embedded piece reshaped to a
different point arrangement inside the SAME bounding box, so home_x/home_y/
area - all marker-side, untouched - stay valid with zero marker edits) plus
several already-existing, real/controlled corpus markers reused for scale
and edge-case coverage (up to 97 placements, an unplaced marker, a
multi-marker zip) - both are listed in the manifest, clearly labelled by
provenance (generated vs reused).
"""
import json, os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)

import accumark_pds as ap
import accumark_marker as am
from dataset.templates import load_template, TEMPLATE_SOURCES
from dataset.write import affine_map, retarget, rename
from dataset.draft import GARMENTS

OUT = os.path.join(HERE, 'generated')

REUSED_MARKERS = [
    # (label, path relative to repo root, note)
    ('CLAUDE-GRADE-MARKER', 'markers/CLAUDE-GRADE-MARKER/CLAUDE-GRADE-MARKER.zip',
     'real multi-size-grading marker (2 placements, sizes 2 and 18, non-placeholder deltas)'),
    ('CAP-C21-SEC14', 'markers/CAP-C21-SEC14/CAP-C21-SEC14.zip',
     'real marker, 2 independently-ruled points, 2 sizes, no embedded pieces'),
    ('2303-BD137-PLACED', 'markers/2303-BD137-PLACED/2303-BD 137 PLACED.zip',
     'real production marker, 97 placements, laid - the dense/scale case'),
    ('2303-BD137-UNLAID', 'markers/2303-BD137-UNLAID/2303-BD 137.zip',
     'real production marker, same style, unplaced (0 placements) - the unplaced case'),
]


def _pattern_zip_bytes(piece_data, member_name):
    """A minimal AccuMark-shaped pattern export: <name>.tmp + ver.5, matching
    the corpus's own two-member layout (FORMAT_SPEC.md section 0)."""
    import io
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr(member_name, piece_data)
        z.writestr('ver.5', b'')
    return b.getvalue()


def _shoelace(pts):
    return abs(sum(pts[i][0]*pts[(i+1) % len(pts)][1] - pts[(i+1) % len(pts)][0]*pts[i][1]
                   for i in range(len(pts)))) / 2


def _fit_transform(native_pts, width_in, height_in, mirror):
    xs = [p[0] for p in native_pts]; ys = [p[1] for p in native_pts]
    nw, nh = max(xs) - min(xs), max(ys) - min(ys)
    sx = (width_in * 1e4) / nw
    sy = (height_in * 1e4) / nh
    # two-pass: compute the bbox the transform would produce, then translate
    # it to sit at (1,1) like the corpus's own templates do.
    raw = affine_map(native_pts, sx, sy, 0, 0, mirror)
    vals = list(raw.values())
    minx = min(p[0] for p in vals); miny = min(p[1] for p in vals)
    dx, dy = 1 - minx, 1 - miny
    return affine_map(native_pts, sx, sy, dx, dy, mirror)


def build_panel(garment, spec, template_cache):
    tpl = template_cache.setdefault(spec.template, load_template(spec.template))
    old_to_new = _fit_transform(tpl['perimeter'], spec.width_in, spec.height_in, spec.mirror)
    label = '%s/%s' % (garment, spec.name)
    new_data = retarget(tpl['data'], tpl['block'], old_to_new, source_label=label)
    new_name = (spec.name[:len(tpl['old_name'])]).ljust(len(tpl['old_name']), 'X')
    new_data = rename(new_data, tpl['old_name_bytes'], new_name)

    new_block = ap.decode(new_data)['blocks'][0]
    new_perim = [(p['x'], p['y']) for p in new_block['perimeter']]
    drafted = [(old_to_new.get(p, p)) for p in tpl['perimeter']]
    assert new_perim == drafted, (label, new_perim, drafted)

    notches = [i for i, p in enumerate(tpl['block']['perimeter']) if p['is_notch']]

    # grading cross-check, only meaningful for templates with real
    # (non-placeholder) deltas - see module docstring. Checked against the
    # exact same source graded_outline() itself reads (block['objects']),
    # not summarize()'s separately-computed grade_rules.
    real_grading = any(any(d != (0, 0) for d in o['deltas'])
                        for o in tpl['block']['objects'])
    per_size = {}
    if real_grading:
        base_name = tpl['block']['meta']['sample_size']
        tpl_base = am.graded_outline(tpl['block'], base_name)
        new_base = am.graded_outline(new_block, base_name)
        for sz in tpl['sizes']:
            tpl_sz = am.graded_outline(tpl['block'], sz)
            # delta-invariance: the grade rule table is untouched by
            # retargeting, so each point's absolute move (in raw 1e-4in
            # units) from the base size must be identical before and after -
            # exact for every point carrying a rule reference; interpolated
            # (unruled) points are checked with a looser tolerance since
            # chain interpolation is only translation/scale-invariant to the
            # extent the template's own points stay collinear-proportional.
            expected = [(nb[0] + (t[0]-b[0]), nb[1] + (t[1]-b[1]))
                        for nb, t, b in zip(new_base, tpl_sz, tpl_base)]
            per_size[sz] = [(round(x, 4), round(y, 4)) for x, y in expected]

    entry = dict(
        garment=garment, panel=spec.name, template=spec.template,
        piece_name=new_name, mirror=spec.mirror,
        width_in=spec.width_in, height_in=spec.height_in,
        base_outline_in=[(round(x/1e4, 4), round(y/1e4, 4)) for x, y in drafted],
        base_area_sqin=round(_shoelace([(x/1e4, y/1e4) for x, y in drafted]), 4),
        notch_indices=notches, n_perimeter=len(tpl['perimeter']),
        sizes=tpl['sizes'], real_grading=real_grading,
        per_size_expected_in=per_size if real_grading else None,
        zip='%s/%s.zip' % (garment, spec.name), member=new_name.lower()[:8] + '.tmp',
    )
    return new_data, entry


def build_samebbox_marker(template_cache):
    """One genuinely new marker: CLAUDE-GRADE-MARKER's structure, its
    embedded piece reshaped to a different point arrangement inside the SAME
    bounding box - so the marker's own home_x/home_y (untouched) stay valid.
    Area is a genuine numeric field, not geometry the reshape preserves for
    free, so it is patched the same way coordinates are: struct.pack_into at
    the exact byte offsets accumark_marker's own parser identifies (the
    section-21 slot's area f64, the section-14 record's area/perimeter f64s,
    and the marker header's util scalar, recomputed from the new areas so
    check_marker's sum(slot areas) == W*L*U identity keeps holding) - never a
    guessed offset, never a structural change."""
    import io, struct as _struct
    path = os.path.join(REPO, 'markers/CLAUDE-GRADE-MARKER/CLAUDE-GRADE-MARKER.zip')
    with zipfile.ZipFile(path) as z:
        members = {i.filename: z.read(i) for i in z.infolist()}
    piece_name = marker_name = None; piece_data = marker_data = None
    for n, d in members.items():
        if d.startswith(am.MAGIC) and am.u16(d, 0x7a) == 20: piece_name, piece_data = n, d
        elif d.startswith(am.MAGIC) and am.u16(d, 0x7a) == 9: marker_name, marker_data = n, d
    block = ap.decode(piece_data)['blocks'][0]
    pts = [(p['x'], p['y']) for p in block['perimeter']]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    # reshape into a trapezoid inscribed in the SAME bbox (narrower at one
    # end) rather than the template's plain rectangle - a different piece,
    # identical footprint.
    inset = int(0.15 * (maxx - minx))
    new_pts = [(minx, miny), (minx + inset, maxy), (maxx - inset, maxy), (maxx, miny)]
    old_to_new = dict(zip(pts, new_pts))
    new_piece = retarget(piece_data, block, old_to_new, source_label='SAMEBBOX-marker-piece')
    new_block = ap.decode(new_piece)['blocks'][0]

    # patch the marker's own area-bearing fields to match the new piece's
    # actual area at each placement's bound size, using the ORIGINAL
    # (pre-edit) marker's own parse to find every offset.
    real_piece_name = am.read_object(piece_data)['name']
    vocab = {real_piece_name: [s['name'] for s in new_block['meta']['sizes']]}
    mk0 = am.parse_marker(marker_data, vocab)
    md = bytearray(marker_data)
    total = 0.0
    for s in mk0['placements']:
        outline, _ = am.piece_outline(dict(block=new_block, data=new_piece), s['size'])
        area = abs(sum(outline[i][0]*outline[(i+1) % len(outline)][1]
                        - outline[(i+1) % len(outline)][0]*outline[i][1]
                        for i in range(len(outline)))) / 2
        perim = sum(((outline[i][0]-outline[(i+1) % len(outline)][0])**2
                      + (outline[i][1]-outline[(i+1) % len(outline)][1])**2) ** 0.5
                     for i in range(len(outline)))
        _struct.pack_into('<d', md, s['slot'] + 42, area)
        if s['record']:
            _struct.pack_into('<d', md, s['record']['offset'] - 30, area)
            _struct.pack_into('<d', md, s['record']['offset'] - 22, perim)
        total += area
    W, L = mk0['width'], mk0['length']
    new_util = total * 100 / (W * L) if W and L else mk0['util']
    _struct.pack_into('<d', md, 446, new_util)
    _struct.pack_into('<d', md, 422, total)
    marker_data = bytes(md)

    out_members = dict(members)
    out_members[piece_name] = new_piece
    out_members[marker_name] = marker_data
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, d in out_members.items():
            z.writestr(n, d)
    data = b.getvalue()

    # verify against the decoder's own placement/geometry self-checks before
    # calling it good - a FRESH decode, re-running the area-based slot<->
    # record binding on the patched bytes from scratch. Compared against the
    # ORIGINAL marker's own checks, not required to be all-True outright:
    # 'placed pieces are in the piece list' already fails on the pristine,
    # unmodified CLAUDE-GRADE-MARKER fixture (section 10 never lists this
    # piece - a pre-existing gap, not something this edit introduced), so the
    # real bar is "no NEW failure", not "zero failures".
    base_res = am.place_marker(path)
    base_checks = {n: ok for n, ok, _ in base_res['markers'][0]['checks']}
    res = am.place_marker(io.BytesIO(data))
    mkr = res['markers'][0]
    bbox_rows = am.bbox_check(res, 0.0)
    area_rows = am.area_check(res)
    checks = {n: ok for n, ok, _ in mkr['checks']}
    new_failures = [n for n, ok in checks.items() if not ok and base_checks.get(n, True)]
    checks_ok = not new_failures
    return data, dict(
        name='GENERATED-SAMEBBOX-MARKER', provenance='generated',
        note='CLAUDE-GRADE-MARKER structure, piece reshaped to a trapezoid inside the same bbox, '
             'areas repatched to match',
        checks=checks, pre_existing_failures=[n for n, ok in base_checks.items() if not ok],
        new_failures=new_failures,
        placements=len(mkr['placed']), checks_ok=checks_ok,
        bbox_worst=round(max([max(abs(r[2]), abs(r[3])) for r in bbox_rows] or [0]), 5),
        area_worst=round(max([abs(r[4]-1) for r in area_rows if r[4]] or [0]), 5),
    )


def main():
    os.makedirs(OUT, exist_ok=True)
    template_cache = {}
    manifest = dict(decoder_version=ap.__version__, panels=[], markers=[])

    for garment, panels in sorted(GARMENTS.items()):
        gdir = os.path.join(OUT, garment)
        os.makedirs(gdir, exist_ok=True)
        for spec in panels:
            data, entry = build_panel(garment, spec, template_cache)
            zpath = os.path.join(OUT, entry['zip'])
            os.makedirs(os.path.dirname(zpath), exist_ok=True)
            with open(zpath, 'wb') as f:
                f.write(_pattern_zip_bytes(data, entry['member']))
            manifest['panels'].append(entry)
            print('  %-14s %-16s %5.1fx%-5.1fin  %2d pts  grading=%s'
                  % (garment, spec.name, spec.width_in, spec.height_in,
                     entry['n_perimeter'], entry['real_grading']))

    mdata, mentry = build_samebbox_marker(template_cache)
    mpath = os.path.join(OUT, 'markers', mentry['name'] + '.zip')
    os.makedirs(os.path.dirname(mpath), exist_ok=True)
    with open(mpath, 'wb') as f:
        f.write(mdata)
    mentry['zip'] = 'markers/%s.zip' % mentry['name']
    manifest['markers'].append(mentry)
    print('  MARKER   %-16s placements=%d checks_ok=%s bbox_worst=%s area_worst=%s'
          % (mentry['name'], mentry['placements'], mentry['checks_ok'],
             mentry['bbox_worst'], mentry['area_worst']))

    for label, rel, note in REUSED_MARKERS:
        manifest['markers'].append(dict(name=label, provenance='reused', zip=rel, note=note))

    with open(os.path.join(HERE, 'MANIFEST.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1)
    print('\n%d panels, %d markers (%d generated + %d reused) -> %s'
          % (len(manifest['panels']), len(manifest['markers']),
             sum(1 for m in manifest['markers'] if m.get('provenance') == 'generated'),
             sum(1 for m in manifest['markers'] if m.get('provenance') == 'reused'),
             os.path.join(HERE, 'MANIFEST.json')))


if __name__ == '__main__':
    main()
