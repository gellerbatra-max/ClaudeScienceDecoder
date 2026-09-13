# V3 production no-edit capture

- ASTM DXF: exported from AccuMark V17 DCU on 2026-09-12 from model
  `2303 MOCUP B1 1`; DCU reported 1/1 model, 2/2 pieces, and 1/1 rule
  table converted.
- Native ZIP: checkpoint package assembled from the byte-exact exported
  members in `D:\Claude\Decoder\2303 PATTERN-MODELS.zip`:
  `a1DCF.tmp` (INMO), `a1EB3.tmp` (OUMO), and `a2905.tmp` (model).
- The outer ZIP container is reconstructed. The `.tmp` member bytes are not
  modified.
- Verified with `verify_capture.py --internal-layers`: all 20 native internal
  lists across OUMO and INMO match their named ASTM entities. The eight
  `0x48` lists match layer 11 (internal cutout) with a worst residual of
  0.0001 inch; the ten `0x49` lists match layer 8 exactly; both grain lines
  match layer 7 exactly.
