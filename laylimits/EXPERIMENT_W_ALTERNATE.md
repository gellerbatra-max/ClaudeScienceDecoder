# Does a `W` (one-way) row keep the marker's alternating 180-degree preset?  (2026-09-24, AccuNest)

Question left open by v4.8: `ZZLL-1` has FRONT = `MW` and Bundling = Alternate Bundle, Alternate Direction. The marker generated with it (`ZZC-M1`, scratch area) stores 180 degrees on
every other bundle. Does the nest engine keep that preset for a piece that may not rotate, or does `W` reset every piece to 0?

Run (own processes, scratch area only): `amcopy Marker ZZC-M1 -> ZZLL-EXP1` (the original stays as generated), Queue Submit > Nest Markers (Draft, no Overrides ticked), Made after 70 s
(`W=139.70CM L=2M 49.84CM U=79.68%`), MarkPlot > DXF (`EXPERIMENT_W_ALTERNATE.DXF`).

Presets stored by the marker (decoder): LADIES-BLOUSE-FR, category FRONT, options `MW`: four instances, slots 5, 6 (mirrored) in bundle 0 -> preset 0; slots 14, 15 (mirrored) in
bundle 1 -> preset 180.

Read from the plot (each outline matched against the marker's own stream outline of the piece, four orientations): FR (area 2249 vs 2250) appears four times - **two forward, two reversed**.
So AccuNest kept every FRONT piece in its preset direction: a `W` piece is fixed in the direction it is *retrieved* in, and that direction alternates with the bundles. The other pieces show the
same pattern (LADIES-BLOUSE-SL, `MS`: as drawn / mirror X / rotated 180 / mirror Y once each = the four preset x mirror combinations); none of them was turned away from its preset.

Consequence, encoded in `nest_spec.py`: `demand[].allowed_deg_by_slot` = `(180 x preset + allowed_deg) mod 360` per slot - `[0]` or `[180]` for a `W` row, `[0, 180]` for a row that allows the
turn. What is NOT shown: that a row allowing 180 lets the engine turn a piece against its preset (no piece did, in this small draft nest).
