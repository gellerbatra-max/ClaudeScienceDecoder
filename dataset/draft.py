"""dataset/draft.py - garment panel specifications: which corpus template
each panel reuses, and the affine transform (scale/translate/mirror) that
takes the template's native shape to the panel's assumed target dimensions.

ASSUMED MEASUREMENTS (base size, before grading - the grading itself comes
unmodified from each template's own grade rule table, see build.py): a
women's size-12 block, bust 38in / waist 30in / hip 40in / back length
15.5in / sleeve length 24in / trouser outseam 41in / trouser inseam 30in,
with 1-2in flat-pattern ease per panel. These are reasonable drafting
figures, not measurements taken from a real customer.

Every panel below names: the template (dataset/templates.py) it reshapes,
its target flat width/height in inches, and whether it is mirrored (for a
genuine left/right pair built from one template). build.py turns each
PanelSpec into an affine_map() and a dataset.write.retarget() call.

Scope note: a template's POINT COUNT, notch/dart placement and grading
table are inherited from the corpus fixture - see templates.py's own
docstring on why (byte-structure edits are restricted to coordinate VALUES,
never record layout). "Complex" therefore means complex shapes, sizes,
proportions and marker layouts, not novel per-piece record structures.
"""
from collections import namedtuple

PanelSpec = namedtuple('PanelSpec', 'name template width_in height_in mirror')

# garment name -> [PanelSpec, ...]
GARMENTS = {
    'A-LINE-SKIRT': [
        PanelSpec('SKIRT-FRONT', 'rect4g', 13.5, 22.0, False),
        PanelSpec('SKIRT-BACK',  'rect4g', 13.5, 22.0, True),
        PanelSpec('SKIRT-WAISTB', 'rect4', 32.0, 1.75, False),
    ],
    'TROUSER': [
        PanelSpec('TROUSER-FRONT', 'dart7', 11.5, 26.0, False),
        PanelSpec('TROUSER-BACK',  'dart7', 12.5, 27.0, True),
        PanelSpec('TROUSER-WAISTB', 'rect4', 31.5, 1.75, False),
        PanelSpec('TROUSER-POCKET', 'pent5', 7.0, 8.5, False),
    ],
    'SHIRT': [
        PanelSpec('SHIRT-FRONT-L', 'notch8', 11.5, 27.0, False),
        PanelSpec('SHIRT-FRONT-R', 'notch8', 11.5, 27.0, True),
        PanelSpec('SHIRT-BACK',    'notch8', 20.5, 27.5, False),
        PanelSpec('SHIRT-YOKE',    'pent5', 20.5, 3.5, False),
        PanelSpec('SHIRT-SLEEVE-L', 'curve34', 14.5, 24.0, False),
        PanelSpec('SHIRT-SLEEVE-R', 'curve34', 14.5, 24.0, True),
        PanelSpec('SHIRT-COLLAR',  'hex6', 16.5, 2.75, False),
        PanelSpec('SHIRT-CUFF-L',  'rect4', 9.0, 2.5, False),
        PanelSpec('SHIRT-CUFF-R',  'rect4', 9.0, 2.5, True),
    ],
    'BLAZER': [
        PanelSpec('BLAZER-FRONT', 'dart7', 13.5, 28.0, False),
        PanelSpec('BLAZER-SIDE',  'pent5', 6.5, 27.0, False),
        PanelSpec('BLAZER-BACK',  'notch8', 20.0, 28.5, False),
        PanelSpec('BLAZER-SLV-UP-L', 'curve34', 15.5, 25.0, False),
        PanelSpec('BLAZER-SLV-UP-R', 'curve34', 15.5, 25.0, True),
        PanelSpec('BLAZER-SLV-UN-L', 'curve34', 10.0, 23.0, False),
        PanelSpec('BLAZER-SLV-UN-R', 'curve34', 10.0, 23.0, True),
        PanelSpec('BLAZER-COLLAR', 'hex6', 17.0, 3.25, False),
        PanelSpec('BLAZER-LAPEL',  'pent5', 5.5, 11.0, False),
        PanelSpec('BLAZER-POCKET', 'rect4', 6.0, 1.5, False),
    ],
    'DRESS': [
        PanelSpec('DRESS-BODICE-F', 'dart7', 13.0, 15.5, False),
        PanelSpec('DRESS-BODICE-B', 'notch8', 20.0, 16.0, False),
        PanelSpec('DRESS-SKIRT-F', 'rect4g', 21.0, 26.0, False),
        PanelSpec('DRESS-SKIRT-B', 'rect4g', 21.0, 26.0, True),
        PanelSpec('DRESS-SLEEVE', 'curve34', 13.0, 6.5, False),
    ],
}
