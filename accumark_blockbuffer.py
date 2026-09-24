#!/usr/bin/env python3
"""accumark_blockbuffer - read an AccuMark BLOCK / BUFFER table (`3MM`, `ZZBB-1`, `.GT_block`) (v4.12).

    python accumark_blockbuffer.py "<export>.zip" [--json]
    python accumark_blockbuffer.py C:\\userroot\\storage\\AREA\\block\\NAME.GT_block

A block / buffer table holds numbered RULES. A rule is a BUFFER (empty space around a piece, not drawn in marker making - what keeps the cutter blade off the next piece) or a BLOCK (a visible area
added to the piece: die-cut and matched pieces), with amounts for the Left, Top, Right and Bottom of the piece and for a Segment (a stretch of the perimeter marked with B / Q attributes), each once
STATIC (applied when the order is processed) and once DYNAMIC (applied or removed while marking). Amounts need not be equal; an amount is a length or a percentage of the plaid / stripe repeat.
A Lay Limits row names a rule by its number (`buffer_rule`; 0 = none); the marker keeps the rules its pieces use as its own section-6 entries.

Byte format, VERIFIED against the Block Buffer editor (BlockBuff.exe): `ZZBB-USER` (rules 1-8, unequal sides in rule 4, a Block rule, static + dynamic amounts) and `ZZBB-X1`, `ZZBB-X2`
(a rule with nine distinct amounts, percentages, a two-line comment; saved from the editor under new names), plus the real `3MM`, `3MM-N`:

    table (a `.GT_block` file has these bytes from 0x90; an export ZIP object from 0x8a, `payload_len` of them)
      V17 layout:   u16 line1_len, u16 line2_len, u16 n_rules, comment text (line1 + line2 characters), n_rules x entry, [ u32 0 ]
      older layout: 40 comment characters, u16 n_rules, n_rules x entry                  (the AccuMark 9 `3MM`)
      entry (70 bytes): u16 rule number, u16 type (0 buffer, 1 block), 11 x slot
      slot (6 bytes): i32 amount x 10000, u16 unit - the slots are: static Left, Top, Right, Bottom, Segment, dynamic Left, Top, Right, Bottom, Segment, and one more that is 0 in every table
      amount: a length in INCHES (0.30 cm = 1181), or a percentage of the repeat (50% = 500000, unit 2); unit 0 = a length. The older layout leaves stray bytes in the unit's high byte.

A table whose length is not exactly what its header and entries add up to, whose entry has an unknown type or a rule number that repeats is refused.
"""
import json, os, struct, sys

__version__ = '1.0'

SIDES = ('left', 'top', 'right', 'bottom', 'segment')
_FILE_OFF, _EXPORT_OFF, ENTRY = 0x90, 0x8a, 70


class BlockBufferError(ValueError):
    pass


def _slot(t, o, strict):
    v, u = struct.unpack_from('<iH', t, o)
    unit = u if strict else (u & 0xff)
    if unit == 0: return dict(value=v / 1e4, unit='length', inches=v / 1e4)
    if unit == 2: return dict(value=v / 1e4, unit='percent', inches=None)
    return dict(value=v / 1e4, unit=f'unknown({unit})', inches=None)


def _entries(t, pos, n, strict):
    rules = []
    for _ in range(n):
        if pos + ENTRY > len(t): raise BlockBufferError('entries run past the end of the table')
        num, ty = struct.unpack_from('<HH', t, pos)
        if ty not in (0, 1): raise BlockBufferError(f'rule {num}: unknown type {ty}')
        slots = [_slot(t, pos + 4 + 6 * i, strict) for i in range(11)]
        rules.append(dict(number=num, kind='block' if ty else 'buffer', static=dict(zip(SIDES, slots[:5])), dynamic=dict(zip(SIDES, slots[5:10])), reserved=slots[10]['value'],
                          warnings=[f'{w}: unit {s["unit"]}' for w, s in zip(('static ' + x for x in SIDES), slots[:5]) if s['unit'].startswith('unknown')]
                          + [f'dynamic {x}: unit {s["unit"]}' for x, s in zip(SIDES, slots[5:10]) if s['unit'].startswith('unknown')]))
        pos += ENTRY
    return rules, pos


def _parse_v5(t):
    if len(t) < 6: raise BlockBufferError('table shorter than its header')
    l1, l2, n = struct.unpack_from('<HHH', t, 0)
    if l1 > 40 or l2 > 40 or n > 99: raise BlockBufferError('header does not look like a V17 block buffer table')
    text = t[6:6 + l1 + l2]
    if not all(32 <= c < 127 for c in text): raise BlockBufferError('comment is not text')
    rules, end = _entries(t, 6 + l1 + l2, n, True)
    if len(t) not in (end, end + 4) or (len(t) == end + 4 and any(t[end:])): raise BlockBufferError(f'length {len(t)} does not close ({end} or {end + 4} expected)')
    return 'v5', text.decode('latin1'), rules, len(t) == end + 4


def _parse_v4(t):
    if len(t) < 42: raise BlockBufferError('table shorter than its header')
    text = t[:40]
    if not all(c == 0 or 32 <= c < 127 for c in text): raise BlockBufferError('comment is not text')
    n = struct.unpack_from('<H', t, 40)[0]
    if n > 99: raise BlockBufferError(f'{n} rules')
    rules, end = _entries(t, 42, n, False)
    if len(t) != end: raise BlockBufferError(f'length {len(t)} does not close ({end} expected)')
    return 'v4', text.replace(b'\x00', b' ').decode('latin1'), rules, False


def parse_block_buffer(source, name=None):
    """-> dict(name, vintage, comment, rules, by_number, trailer). `source`: an object dict from accumark_marker.list_zip, raw table bytes or a `.GT_block` path.
    Each rule: number, kind ('buffer' / 'block'), static / dynamic = {left, top, right, bottom, segment: {value, unit 'length' | 'percent', inches}}. Raises BlockBufferError when the bytes do not close."""
    if isinstance(source, str):
        d = open(source, 'rb').read(); t = d[_FILE_OFF:]; name = name or os.path.splitext(os.path.basename(source))[0]
    elif isinstance(source, dict):
        d = source['data']; t = bytes(d[_EXPORT_OFF:_EXPORT_OFF + source['payload_len']]); name = name or source.get('name')
        if len(t) != source['payload_len']: raise BlockBufferError('object shorter than its own payload length')
    else: t = bytes(source)
    errs = []
    for fn in (_parse_v5, _parse_v4):
        try: vint, comment, rules, trailer = fn(t); break
        except (BlockBufferError, struct.error) as e: errs.append(f'{fn.__name__[1:]}: {e}')
    else: raise BlockBufferError('unrecognised block buffer table (' + '; '.join(errs) + ')')
    nums = [r['number'] for r in rules]
    if len(set(nums)) != len(nums): raise BlockBufferError('a rule number repeats')
    return dict(name=name, vintage=vint, comment=comment.strip(), rules=rules, by_number={r['number']: r for r in rules}, trailer=trailer,
                basis='decoded: every field verified against the Block Buffer editor')


def load_zip_block_buffers(path, listing=None):
    """{name: parsed table} for every block-buffer object of an export ZIP (unreadable ones in `_errors`)."""
    import accumark_marker as am
    out = {}; errs = []
    for o in (listing if listing is not None else am.list_zip(path)).get('block_buffer', []):
        try: out[o['name']] = parse_block_buffer(o)
        except BlockBufferError as e: errs.append((o['name'], str(e)))
    if errs: out['_errors'] = errs
    return out


def rule_sides_in(rule, which='static'):
    """(left, top, right, bottom) of a rule in inches, None for an amount that is a percentage of the repeat."""
    s = rule[which]
    return tuple(s[k]['inches'] for k in ('left', 'top', 'right', 'bottom'))


def describe(t):
    L = [f"{t.get('name')}  [{t['vintage']}]  {len(t['rules'])} rule(s)" + (f"  comment: {t['comment']}" if t['comment'] else '')]
    def fmt(s): return ' '.join(f"{k[0].upper()}={v['value'] * 2.54:.2f}cm" if v['unit'] == 'length' else f"{k[0].upper()}={v['value']:.1f}%" for k, v in s.items() if v['value'])
    for r in t['rules']:
        L.append(f"  rule {r['number']:>2} {r['kind']:<6} static {fmt(r['static']) or '-':<40} dynamic {fmt(r['dynamic']) or '-'}")
    return '\n'.join(L)


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv); as_json = '--json' in a; a = [x for x in a if x != '--json']
    if not a: print(__doc__); return 2
    tabs = {}
    for f in a:
        if f.lower().endswith('.zip'): tabs.update({f'{os.path.basename(f)}:{k}': v for k, v in load_zip_block_buffers(f).items() if k != '_errors'})
        else: tabs[f] = parse_block_buffer(f)
    if as_json: print(json.dumps(tabs, indent=1, default=str))
    else:
        for v in tabs.values(): print(describe(v))
    return 0


if __name__ == '__main__':
    sys.exit(main())
