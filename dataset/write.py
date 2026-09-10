"""dataset/write.py - byte-level editing of a real AccuMark piece object:
reshape its perimeter and rename it, without changing its length or any
record structure.

Both operations only ever overwrite bytes accumark_pds's own parse already
identified (coord_offsets) or bytes that are an exact, same-length copy of
a string the parse already identified (the piece name) - see
dataset/templates.py's module docstring for why offset-based patching is
required instead of a blind byte search.

Every write here is verified before being returned: re-decoded, checked
against the intended geometry, and gated on accumark_pds's own
`line_table_consistent` cross-check (see verify_capture.facts) - the
decoder's independent proof that the line table agrees with the perimeter.
A retarget that breaks that check raises rather than silently producing an
invalid piece; this is what this session's probing found necessary (an
arbitrary reshape of a curved template can flip line_table_consistent to
'no' even though the geometry itself decodes fine - see CHANGELOG.md).
"""
import struct
import accumark_pds as ap
import verify_capture as vc
from dataset.templates import coord_offsets


class RetargetError(Exception):
    """A retarget produced a piece that failed its own consistency gate."""


def affine_map(points, sx=1.0, sy=1.0, dx=0, dy=0, mirror=False):
    """{old (x,y): new (x,y)} for every point in `points` (ints, 1e-4 in),
    scaled/translated and optionally mirrored about the point set's own
    minimum X. All distinct input points must stay distinct after the
    transform (checked by the caller via retarget's dedupe requirement)."""
    if mirror:
        x0 = min(p[0] for p in points)
        points_mirrored = [(2 * x0 - x, y) for x, y in points]
    else:
        points_mirrored = points
    out = {}
    for (ox, oy), (mx, my) in zip(points, points_mirrored):
        out[(ox, oy)] = (int(round(mx * sx)) + dx, int(round(my * sy)) + dy)
    return out


def retarget(data, block, old_to_new, source_label=''):
    """Patch every known byte occurrence of every mapped coordinate pair in
    `data`, in place (length-preserving), and verify the result before
    returning it. Raises RetargetError instead of returning a piece that
    fails its own consistency check."""
    old_pts = [(p['x'], p['y']) for p in block['perimeter']]
    if len(set(old_pts)) != len(old_pts):
        raise RetargetError('%s: template perimeter has duplicate coordinates; '
                             'offset-based retargeting requires distinct points' % source_label)
    offs = coord_offsets(data, block)
    d = bytearray(data)
    for (ox, oy), (nx, ny) in old_to_new.items():
        for xo, yo in offs.get((ox, oy), []):
            struct.pack_into('<i', d, xo, nx)
            struct.pack_into('<i', d, yo, ny)
    d = bytes(d)

    # verify: re-decode, check the intended perimeter landed exactly, and
    # gate on the decoder's own independent line-table cross-check.
    b1 = ap.decode(d)['blocks'][0]
    got = [(p['x'], p['y']) for p in b1['perimeter']]
    want = [old_to_new.get(p, p) for p in old_pts]
    if got != want:
        raise RetargetError('%s: perimeter did not round-trip (got %r, want %r)'
                             % (source_label, got, want))
    f, _ = vc.facts(dict(folder='.', zip='mem', data=d, dxf=None, rul=None))
    if f['line_table_consistent'] != 'yes':
        raise RetargetError('%s: line_table_consistent=%r after retarget - reject '
                             'rather than emit an invalid piece'
                             % (source_label, f['line_table_consistent']))
    return d


def rename(data, old_name_bytes, new_name):
    """Rename a piece by swapping every exact occurrence of its old name for
    a new one of IDENTICAL byte length (the header slot, the piece-record
    name field, and Region C's raw name echo are all literal copies of the
    same string - see FORMAT_SPEC.md section 1/2 - so a same-length ASCII
    swap needs no length-field or offset adjustment anywhere)."""
    new_bytes = new_name.encode('latin1')
    if len(new_bytes) != len(old_name_bytes):
        raise RetargetError('rename requires an identical byte length: %r (%d) -> %r (%d)'
                             % (old_name_bytes, len(old_name_bytes), new_name, len(new_bytes)))
    n = data.count(old_name_bytes)
    if n == 0:
        raise RetargetError('old name %r not found in object' % old_name_bytes)
    return data.replace(old_name_bytes, new_bytes)
