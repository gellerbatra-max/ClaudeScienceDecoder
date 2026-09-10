"""robustness/zipfuzz.py - in-memory ZIP structural variants (Oracle A),
malformed containers (Oracle B), and byte-level corruption (Oracle C).
Nothing here touches disk - every variant is a BytesIO, since
accumark_marker.list_zip / accumark_pds.decode_zip both accept a file-like
object in place of a path (verified this session).
"""
import io, os, random, zipfile


def members(path):
    """[(name, bytes), ...] for every member of a real zip, read fresh."""
    with zipfile.ZipFile(path) as z:
        return [(i.filename, z.read(i)) for i in z.infolist()]


def build(items, compression=zipfile.ZIP_DEFLATED, comment=None):
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w', compression) as z:
        for name, data in items:
            z.writestr(name, data)
        if comment is not None:
            z.comment = comment
    b.seek(0)
    return b


# --------------------------------------------------------- Oracle A variants
# each: [(name, bytes)] -> [(name, bytes)] or a build()-ready BytesIO.
# named so a failure is reproducible by name alone.

def v_stored(items): return build(items, zipfile.ZIP_STORED)
def v_deflated(items): return build(items, zipfile.ZIP_DEFLATED)
def v_bzip2(items): return build(items, zipfile.ZIP_BZIP2)
def v_lzma(items): return build(items, zipfile.ZIP_LZMA)


def v_mixed_compression(items):
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        for i, (name, data) in enumerate(items):
            comp = [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED, zipfile.ZIP_BZIP2][i % 3]
            zi = zipfile.ZipInfo(name); zi.compress_type = comp
            z.writestr(zi, data)
    b.seek(0); return b


def v_reversed_order(items): return build(list(reversed(items)))


def v_shuffled_order(items):
    rnd = random.Random(20260911)
    shuffled = list(items); rnd.shuffle(shuffled)
    return build(shuffled)


def v_folder_prefix(items): return build([('export/' + n, d) for n, d in items])
def v_deep_nesting(items): return build([('a/b/c/' + n, d) for n, d in items])
def v_backslash_paths(items): return build([('sub\\' + n, d) for n, d in items])


def v_directory_entries(items):
    return build([('adir/', b'')] + items)


def v_extra_junk(items):
    return build(items + [('README.txt', b'hello'), ('notes.bin', bytes(200)),
                           ('.DS_Store', bytes(50))])


def v_nonascii_name(items):
    return build([('é中文/' + n, d) for n, d in items])


def v_long_name(items):
    return build([('x' * 180 + '_' + n, d) for n, d in items])


def v_upper_tmp(items):
    return build([(n.upper() if n.lower().endswith('.tmp') else n, d) for n, d in items])


def v_renamed_ext(items):
    return build([(n[:-4] + '.dat' if n.lower().endswith('.tmp') else n, d) for n, d in items])


def v_drop_ver5(items):
    return build([(n, d) for n, d in items if n != 'ver.5'])


def v_drop_comments(items):
    return build([(n, d) for n, d in items if n != 'comments.txt'])


def v_no_comment(items): return build(items, comment=b'')
def v_replaced_comment(items): return build(items, comment=b'not the real AccuMark comment')


def v_zeroed_timestamps(items):
    b = io.BytesIO()
    with zipfile.ZipFile(b, 'w') as z:
        for name, data in items:
            zi = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            z.writestr(zi, data)
    b.seek(0); return b


ORACLE_A_VARIANTS = [
    v_stored, v_deflated, v_bzip2, v_lzma, v_mixed_compression,
    v_reversed_order, v_shuffled_order, v_folder_prefix, v_deep_nesting,
    v_backslash_paths, v_directory_entries, v_extra_junk, v_nonascii_name,
    v_long_name, v_upper_tmp, v_renamed_ext, v_drop_ver5, v_drop_comments,
    v_no_comment, v_replaced_comment, v_zeroed_timestamps,
]

# ----------------------------------------------------------- Oracle B inputs
# each: () -> BytesIO | bytes, a malformed/unusual container. Named so a
# failure is reproducible; paired with the exception type(s) considered a
# PASS in cases.py.


def b_empty():
    return io.BytesIO(b'')


def b_random(n=4096, seed=1):
    return io.BytesIO(random.Random(seed).randbytes(n))


def b_truncated(items, frac):
    full = build(items).getvalue()
    return io.BytesIO(full[:int(len(full) * frac)])


def b_zero_members():
    return build([])


def b_only_junk():
    return build([('a.txt', b'hello'), ('b.txt', b'world')])


def b_duplicate_members(items):
    return build(items + items)


def b_nested_zip(inner_items, wrapper_name='inner.zip'):
    inner = build(inner_items).getvalue()
    return build([('folder/.DS_Store', b''), ('folder/' + wrapper_name, inner)])
