# Marker decode plan — AccuMark native marker export

> ## STATUS 2026-09-10 (evening, live session) — the 8 status-bar codes: offline route now genuinely exhausted, not just believed so
>
> Live on the AccuMark machine, `2303-BD 137 PLACED` already open in Easy
> Marking. Two things done, one safe result, one stopped early for safety.
>
> **Extended the offline-manual search to two PE editions nobody had
> checked** - `MarkerMaking_Users_PE.pdf` (2.3 MB, vs. the 860 KB `_AE`
> edition already searched) and `OrderEntry_Users_PE.pdf` (4.5 MB vs.
> 2.4 MB `_AE`), plus `ms2000 order entry.pdf`, none of them in the prior
> session's search list. Extracted with `pdftotext -layout` and grepped for
> all 8 codes (`PA TI TT FC FW CB MW BD`) as substrings, not just word
> boundaries. **`PA`, `FC`, `FW`, `CB`, `MW` do not occur anywhere in any
> of the three documents - not one hit, not even as part of another
> word.** `TI`/`TT`/`BD` do occur, but only as substrings of unrelated
> terms already identified elsewhere in this plan (`BD1-3` in the same
> `SZ1-6,BD1-3` annotation-code notation already decoded; nothing new).
> `MarkerMaking_Users_PE.pdf` does have a real "Marker Info" field-by-field
> table (`Field / Explanation`, pp. 87-88) - it documents `MD, PN, SZ, SA,
> PL/ST, WI, TL, OL, FB, 1/1, CT, CU/TU, LN, TB` (confirming `TL` = tilt
> increment and `OL` = overlap amount, both already known) but simply does
> not include the 8 target fields at all - the live UI has more fields
> than this table lists, on either edition. This is the same conclusion
> the prior session reached from the `_AE` manuals alone, now confirmed
> independently on documents twice-to-five-times their size that nobody
> had actually opened - a real negative result, not an assumption.
>
> **Live UI exploration in Easy Marking, also negative:** no tooltip on
> hover over any of the 8 fields; right-click on the Marker Info panel
> only offers panel-docking options (Float/Show/Dock/Auto Hide/Hide), no
> field menu; the ribbon's "Marker Properties" button opens an unrelated
> Order Number/Marker Description dialog; "Report Results" produced no
> new window; clicking directly into a field's value box does not expand
> or relabel it. Every reasonably-safe, read-only avenue for these 8
> codes is now exhausted on this install; closing them needs either
> internet access (unavailable here) or a support contact, not more
> looking.
>
> **Stopped before attempting a live marker-rearrangement test** (the
> other lead from the STATUS block below, aimed at telling whether the
> type-10 gap tracks placement layout). Windows-MCP's window-focus
> tracking silently drifted off Easy Marking mid-session (several
> `Snapshot` calls in a row reported "No active window found" with no
> error), and the next click landed on this Claude session's own chat
> sidebar instead, one menu item away from `Delete` on an unrelated
> session. No harm done - caught and dismissed immediately - but a
> multi-step Save As/Export sequence is exactly the wrong place to
> discover focus is unreliable, so that test was not attempted this pass.
> Left for a session that re-verifies focus before every click (or
> re-checks after each step rather than chaining several blind).
>
> `python selftest.py` → not re-run this pass (no decoder files touched).
>
> ## STATUS 2026-09-10 (later still, part 2) — the id53→id54 gap: the point-attribute lead does NOT hold up; bounded and characterized instead
>
> Follow-up to the STATUS block directly below, same session, still offline.
> That block flagged the ~48 KB gap between id 53 and id 54 on
> `2303-BD 137 PLACED` as a lead because its byte histogram was rich in
> 9s and 10s (`accumark_pds.POINT_TURN`/`POINT_CURVE`). Checked directly
> and it does not survive: **every one of the style's 1,366 perimeter
> points has `attr == 9`; none has `attr == 10`.** The gap's 1,042
> tens therefore correspond to nothing in the piece data at all, and its
> 931 nines are not a clean multiple or fraction of 1,366 either. Retracted
> - do not re-chase this specific coincidence.
>
> **Precisely bounded instead of globally characterized.** The gap is not
> one undifferentiated blob: its first **138 bytes** are a plain `01 00`
> repeating cycle (a *different* filler motif than the `00 00 01 01 02`
> cycle documented elsewhere in this section), and its last **47 bytes**
> are zero padding. The **47,915-byte middle residual** - 11,978 u16-LE
> pairs at a strict 4-byte stride - is genuinely denser (its own period-4
> self-match is 94-98% in three of four quarters, dropping to 83% in the
> last), so it is not pure filler either, but tallying its values against
> every countable quantity already decoded for this marker (the 8 models,
> the 53 section-12 size rows and their model-index field, the per-piece
> section-14 record counts, the 97 placements, the 66 records) finds no
> clean match to any of them - ruled out this pass, not just untested.
>
> Net effect on the open question: narrower and more precisely described,
> not closed. A future pass should stop treating this as "a 48 KB
> unstructured gap" and start from "a 138-byte filler run, a 47.9 KB
> region of ~12,000 quasi-periodic u16 pairs that resembles a nesting/
> packing algorithm's own working buffer more than it resembles stored
> per-item data, and 47 bytes of padding" - and, given the length is
> identical regardless of laid state (established in the STATUS block
> below), a live comparison across two markers with the SAME piece set
> placed in genuinely different layouts (not just laid vs. unlaid) is the
> most direct way to tell "meaningful, marker-specific" from "algorithm
> scratch space that never varies with what's actually placed" apart -
> offline analysis of the one marker instance already committed cannot
> settle that distinction by itself.
>
> `python selftest.py` → **SELFTEST PASS** (analysis only; no decoder code
> changed this pass).
>
> ## STATUS 2026-09-10 (later still) — slot 39 is not uniform filler: a small tagged-field table found inside it, byte-exact across the whole corpus
>
> Offline analysis only (no live AccuMark this pass) against the markers
> already committed in `markers/`. Re-derived the type-10 object's own
> envelope and directory independently (its magic sits 26-58 bytes into
> the marker's slot 30, not at the section's own start - the object's own
> `directory()`/`_section()` apply from there) and got the same slot set
> {33,35,36,37,39,41} already logged below, which cross-checks that
> earlier pass.
>
> **Slot 39's low entropy is two DIFFERENT repeating placeholder cycles
> (`00 00 01 01 02` and `01 00`), not one, and they don't cover the whole
> section.** Scanning for the byte signature `00 00 <id> <7 zero bytes>
> <u32 value> <u16 tail>` (16 bytes) finds a genuine sparse table sitting
> in slot 39's first 20-90 KB, present in every marker tested:
> `2303-BD 137` (laid + unlaid), all four `2303-CP150-JULY` corner probes,
> `CLAUDE-GRADE-MARKER`, `CLAUDE-QTY-TEST`, `AD1234 TEST 134`,
> `LADIES-BLOUSE TEST-2` - 10 markers, two styles, 0-97 placements, both
> export vintages, added to `accumark_marker.type10_tagged_fields()`.
>
> **Two fields are universal format constants, exact on all 10 markers:**
> id `45` -> `(value=4, tail=0)`; id `46` -> `(value=102, tail=98)`.
>
> **Three fields move together and split cleanly by STYLE, not by marker
> instance:** id `44`'s value is always exactly 2x id `47`'s value, which
> always equals id `51`'s value. Every `2303` marker reads `88/44/44`;
> every marker built from one of the small single-test-piece styles
> (`CLAUDE-GRADE-TEST`, `CLAUDE-QTY-TEST`, `AD1234`, `LADIES-BLOUSE`) reads
> `8/4/4` - unaffected by laid state, placement count (0 through 97), or
> marker length/width, and the two `2303` samples agree even though one
> zip bundles only the 18 pieces this marker places and the other bundles
> that style's whole ~120-piece catalog. So this is keyed to the STYLE's
> piece set, not the specific export. What it counts is not identified.
>
> **id `53` is optional** - present with a value on `2303-BD 137` and every
> single-test-piece marker, absent (skipped entirely) on all four CP150
> markers, which are a different export of a piece set that otherwise
> matches BD137's id-44/47/51 values exactly.
>
> **Not all of slot 39's remaining bytes are filler either, and this is
> the open lead, not a finding.** The ~48 KB gap between id 53 and id 54 on
> `2303-BD 137 PLACED` has a rich byte histogram - 0, 1, 2, 6, 7, 8, 9, 10
> all in the hundreds-to-thousands - unlike the simple 2- and 5-byte
> cycles filling the rest of the section. 9 and 10 are exactly
> `accumark_pds.POINT_TURN`/`POINT_CURVE`, the piece format's own
> perimeter-point attr bytes. This does not show the gap re-encodes point
> attributes - only that the byte distribution is consistent with it and
> worth checking directly (e.g. against the total perimeter-point count of
> the style's own catalog) before assuming it's more filler.
>
> This narrows, but does not close, the "no working hypothesis" verdict on
> slot 39 from the STATUS block below: a small constant/style-keyed table
> is now decoded at the byte level (framing solid, meaning mostly open),
> and the true bulk of the section is now known to have at least one
> non-filler region still unaccounted for, rather than being uniformly
> reserved space.
>
> `python selftest.py` → **SELFTEST PASS** (added
> `accumark_marker.type10_object()` / `.type10_directory()` /
> `.type10_tagged_fields()` - research helpers, not wired into
> `place_marker`/`check_marker`/any correctness path; no existing decode
> logic changed).
>
> ## STATUS 2026-09-10 (final, part 2) — M-MARKER's label codes closed: official PDF manuals shipped with the install decode the whole table
>
> New technique this pass, not used before in this project: the AccuMark V17
> install directory (`C:\Program Files\Gerber Technology\AccuMark V17\AccuMark`)
> ships its own offline PDF manuals (`MarkerMaking_Users_AE.pdf`,
> `OrderEntry_Users_AE.pdf`, `MS2000 Marking.pdf`, `WhatsNew_ae.pdf`, and
> others) - the online "Learn & Support" help inside AccuMark Explorer needs
> internet access this machine doesn't have, but these local copies don't.
> `OrderEntry_Users_AE.pdf`'s Annotation Form section (§"Annotation Type/Code/
> Explanation") turned out to be the exact legend for the `M-MARKER`/`A`
> object's numeric codes this plan has been chasing since the "M-MARKER/3MM/
> lay-limit/notch table payloads" pass.
>
> **The `MARKER` sub-block is a flat list of marker-level annotation type
> codes, confirmed byte-for-byte.** The manual documents the MicroMark-import
> default for this exact sub-block as literally `MARKER MSQ,/,AP,/,WI,L,U,PS`
> - and `2303-BD 137`'s own `M-MARKER` object stores precisely that 8-token
> sequence as 8 one-byte codes, matching in order and value:
>
> | token | byte | decimal |
> |---|---|---|
> | MSQ (Model/Size/Quantity) | `0x14` | 20 |
> | / (new line) | `0x0b` | 11 |
> | AP (Add PC/Bundle) | `0x18` | 24 |
> | / (new line) | `0x0b` | 11 |
> | WI (Marker Width) | `0x17` | 23 |
> | L (Length) | `0x15` | 21 |
> | U (Utilization) | `0x16` | 22 |
> | PS (Plaid/Stripe) | `0x1c` | 28 |
>
> The repeated `/` token reproducing the identical byte (`0x0b`) both times
> it appears is the strongest internal check - a coincidence would need to
> reproduce that agreement by chance. Bonus: L, U, WI, AP land on four
> **consecutive** integers (21-24) in exactly the textual order the manual
> lists them (Length, Utilization, Marker Width, Add PC/Bundle) - not
> coincidental either.
>
> **The `DEFAULT`/`LABELD` sub-block's 3-byte triples are `[type code,
> range start, range end]` - the manual's own `SZ1-6`/`BD1-3` notation,
> literally.** `LADIES-BLOUSE TEST-2`'s annotation object is named
> `SIZE-AND-BUNDLE` and its two `DEFAULT` triples are `(07,01,06)` and
> `(09,01,03)`. The manual documents the MicroMark-import default annotation
> as `DEFAULT SZ1-6,BD1-3` - Size truncated to 6 characters, Bundle to 3.
> `(07,01,06)` decodes as **SZ (Size), range 1-6** and `(09,01,03)` decodes
> as **BD (Bundle), range 1-3** - both the type code AND the two range bytes
> match the doc's own notation exactly, digit for digit. This retires the
> earlier "tentative: code 07 = SIZE" note - it's now confirmed, not
> guessed, and a second code (09 = Bundle) is confirmed alongside it.
>
> Not confirmed to the same standard: the generic `2303-BD 137`-side `A`
> object's first triple `(06,01,14)` - plausibly **PN (Piece Name)
> truncated to 14 characters** (Name-then-Size is the obvious pairing for a
> generic per-piece label, and its second triple is the confirmed
> `(07,01,06)` = SZ), but no doc default exists at exactly `PN1-14` to check
> against, so this stays a plausible reading rather than a proven one.
>
> **Bonus, same manuals: `COSTINGS`'s ply-count byte matches the documented
> Fabric Spread enum order.** `OrderEntry_Users_AE.pdf`'s Lay Limits Form
> section lists the Fabric Spread options in the fixed order "Single Ply,
> Tubular, Bookfold, Face-To-Face". The one byte already identified in this
> plan (`1` on the `SINGLE-PLY`-named lay-limits object, `2` on generic
> ones) is consistent with a 1-indexed enum over that exact list -
> Single Ply first. Still only one value confirmed by name; 2/3/4 for
> Tubular/Bookfold/Face-To-Face are inferred from list order, not observed
> directly on a sample named for them.
>
> **Checked and NOT found in any shipped manual:** the Easy Marking status
> bar's `TI`, `PA`, `TT`, `FC`, `FW`, `CB`, `MW`, `PR` fields from the
> "length allowance" live-check pass. Searched `MarkerMaking_Users_AE.pdf`,
> `OrderEntry_Users_AE.pdf`, `MS2000 Marking.pdf`, and `WhatsNew_ae.pdf` -
> none define these tokens. The `Marker Info` dialog box *is* documented in
> `MarkerMaking_Users_AE.pdf` (confirms `MD`/`PN`/`SZ`/`SA`/`WI`/`TL`/`OL`/
> `FB`/`CT`/`CU`/`TU`/`LN`/`TB`, including a full-sentence match for `OL` -
> "Displays the amount of overlap allowed when placing pieces" - and `TL` -
> "Tilt amount increments" - neither previously identified), but that table
> is legacy-vintage and the 8 still-unknown codes aren't in it. They most
> likely belong to a newer Easy Marking status-bar row this older manual set
> predates, and closing them needs either a working internet connection (for
> AccuMark's own online help) or targeted live UI probing (right-click /
> customize menus on the status bar, if any exist), not more offline-doc
> searching - the offline route has been exhausted for these 8 codes.
>
> `python selftest.py` → **SELFTEST PASS** (analysis only; no decoder code
> changed this pass).
>
> ## STATUS 2026-09-10 (last, part 2) — section 14's X coordinate found: closes the ruled point's full position
>
> Re-verified the diff between `CLAUDE-GRADE-TEST`'s two size records
> byte-for-byte across the *entire* 65-byte stream (not just the header)
> and confirmed only 6 bytes ever differ: offsets 3-7 and the already-known
> trailing counter at 63. Offset 5-6 was already identified as the ruled
> point's `Y` (§ above). That leaves exactly 2 unaccounted bytes - offsets
> 3-4 - immediately before it.
>
> **They're `X`, truncated to its low 16 bits.** `u16` at offset 3 reads
> `56227` on size "2" and `4860` on size "18" - and `318371 mod 65536 =
> 56227`, `332540 mod 65536 = 4860` **exactly**, where 318371/332540 are
> the same independently-computed graded X coordinates (1e-4 in) used to
> confirm Y. Zero error, on both samples. So the header's bytes 3-6 are a
> packed `(X mod 65536, Y)` pair for the ruled point - Y fits a plain
> `u16` in every sample seen so far, X only needed truncating because this
> test piece is unusually wide (48 in); on an ordinary piece under 6.5536
> in this field would just read as the true X with no wraparound, so the
> rule "`u16` = coordinate mod 65536" is the general statement, not a
> special case for this piece.
>
> **This closes section 14's ruled-point coordinate storage completely**
> (both X and Y now confirmed, not just Y). What's left of section 14 is
> unchanged: this exact 8-byte-header framing hasn't been confirmed to
> generalize to a piece with more than one genuinely graded point, since
> the only production piece available (5 graded points) has all-
> placeholder deltas and produces zero byte variation to test against.
>
> `python selftest.py` → **SELFTEST PASS** (analysis only).
>
> ## STATUS 2026-09-10 (last) — M-MARKER's label codes and COSTINGS's ply byte, both narrowed with real evidence
>
> Compared annotation and lay-limit objects **across every captured
> marker at once** instead of reading one payload in isolation - the
> corpus already had differently-named instances of both, which is what
> made this tractable without a new capture.
>
> **`M-MARKER`/`A` (annotation) - framing confirmed, one code tentatively
> identified.** Every sample repeats `[u16 tag][20-byte padded name]
> [00 00][u16 count][code bytes]` for up to three named sub-blocks
> (`DEFAULT`, `MARKER`, `LABELD`). The `MARKER` sub-block's 8 code bytes
> are **byte-identical across all three independent samples**
> (`14 0b 18 0b 17 15 16 1c`) - a real, reproducible constant, meaning
> in this vintage. The `DEFAULT` sub-block's codes differ, and comparing
> them is what breaks in: `LADIES-BLOUSE TEST-2`'s annotation object is
> descriptively named **`SIZE-AND-BUNDLE`** and its `DEFAULT` codes are
> two 3-byte triples, `(07,01,06)` and `(09,01,03)` - `2303-BD 137`'s
> generic `A` object's first triple is `(06,01,14)` and its **second is
> the identical `(07,01,06)`**. Tentatively: **code `07` = SIZE** (it's
> the one recurring value, and it sits in the object literally named for
> showing size). `LABELD` is a real third slot, populated with its own
> count+codes only in the fuller `M-MARKER` sample - empty/truncated in
> the simpler `A` objects, so it's an optional preset, not always used.
>
> **`COSTINGS`/`L`/`SINGLE-PLY` (lay limits) - one byte identified.** The
> byte right before each object's own `DEFAULT` name reads `2` on every
> generic `L` object and `1` on the one named **`SINGLE-PLY`** - matching
> its own name exactly. Tentatively: **this byte is the configured ply
> count** (or a lay-type code where 1 = single ply). A second, smaller
> flag two bytes past the name differs between `COSTINGS` (`01`) and the
> generic objects (`00`) - unidentified, but distinct and reproducible.
>
> `python selftest.py` → **SELFTEST PASS** (analysis only).
>
> ## STATUS 2026-09-10 (final) — M-MARKER/3MM/lay-limit/notch table payloads: mostly closed, one real prior mystery resolved
>
> These four object kinds (types 2/3/6/17) turned out to already be sitting
> in the corpus - `2303-CP150-JULY/2303-CP 150 CPL.zip` has all four, no new
> capture needed (the other zips only ever carry the piece-annotation
> variant `A`/`DEFAULT`, never `M-MARKER`/`3MM`/`COSTINGS`).
>
> - **`3MM` (block buffer, type 3) - decoded cleanly.** Payload is a
>   creator name + date string (`DILUK`, `20/07/05`), then a count, then
>   the buffer distance itself as `i32` (1e-4 in), repeated 4 times (one
>   per marker edge): `1181`... no - **`591`**, which is exactly **1.5 mm**
>   (0.0591 in x 25.4 = 1.50 mm). Confirms, with the actual stored number
>   rather than just the object's own name, the "1.5 mm block buffer" this
>   plan already referenced from the piece side.
> - **`P-NOTCH` and `V-NOTCH-ALL CUSTOMERS` (notch table, type 17) - this
>   is the "system-wide notch-shape table" FORMAT_SPEC.md §4 predicted but
>   never located.** `P-NOTCH` stores one depth value, `i32` 1574 (1e-4 in)
>   = **exactly 0.40 cm** - matching, digit for digit, the "Type 1 default
>   Depth 0.40" the UI showed during `CAP-C41-NOTCH-WIDTH` (FORMAT_SPEC.md
>   §4: "Depth is therefore fixed per Type, looked up from a system-wide
>   notch-shape table, not settable per placement" - this is that table).
>   `V-NOTCH-ALL CUSTOMERS` stores the same `[depth, 0, width]` triple
>   (1181, 0, -787 -> 0.30 cm / 0.20 cm) 25 times - a header count (`25`)
>   followed by 5 untagged records then 20 more each prefixed with a small
>   type tag - all 25 slots share one value, consistent with a factory-
>   default table where every notch type still uses the same shape until
>   customized.
> - **`M-MARKER` (annotation, type 2) - structure mapped, label codes not
>   decoded.** Creator name + date (`THUSHARA`, `02/02/06`), then two
>   named sub-blocks (`DEFAULT`→`LABELD`, and a second tagged `MARKER`)
>   each holding a short run of small integers - plausibly which text
>   fields print in a piece's on-marker label (size, cut number, ...), not
>   decoded further.
> - **`COSTINGS` (lay limits, type 6) - structure only.** Mostly zero
>   padding, a `DEFAULT` name, and a trailing 2-byte value with no
>   confirmed meaning yet.
> - **Bonus, unplanned:** found and identified a fifth object kind while
>   surveying the corpus - **type 23 = rule table** (`CAP-RULES-A`, `ID
>   XS-XL`, `A1-LADIES` all carry it). Confirmed by content, not just name:
>   its payload contains the exact same cumulative deltas already known
>   from `CAP-RULES-A`'s embedded piece-side copy (393,-196 / 787,-393 /
>   1181...). Added to `accumark_marker.OBJECT_TYPES`.
>
> `python selftest.py` → **SELFTEST PASS** (one small, safe code change -
> the type-23 mapping - plus analysis, no other decoder logic touched).
>
> ## STATUS 2026-09-10 (night, live check) — the length allowance: no discrepancy on this marker
>
> Opened `2303-BD 137 PLACED` directly in Easy Marking (live, on the
> AccuMark machine) and read its own "Marker Info" status bar rather than
> guessing from stored bytes. **`LN` (Length) reads `3m 77.68cm` — an exact
> match to the decoded `length_cm` value, zero allowance added.** The
> `dxfparser`-reported +4.00/+5.96 cm discrepancy on other styles does not
> reproduce here; whatever produces it (a fabric-specific trim/roll-end
> setting, most likely) is evidently not configured on this marker, or is
> zero for it. Checked `Fabric → Fabric/Trim` too, in case a configured
> fabric background carries its own allowance value - the dialog was empty
> for this marker (no fabric background set), a dead end here but the right
> place to look on a marker that does show a length discrepancy.
>
> **Bonus, not previously logged:** the same status bar exposes several
> other abbreviated fields with no accessible tooltip found yet - `OL`
> (0.32), `TI` (0.13cm), `PA` (13.49), `TT` (0.00), `BD` (0.06), `FC`/`FW`/
> `CB`/`MW` (all 0.00 here), `PR` (243.14). None identified; flagging for
> whoever tackles them next, since `BD` in particular is suggestively
> small and might be the same "block buffer" concept `CAP-C60-CUTOUT`'s
> era already named elsewhere in this format.
>
> `python selftest.py` → **SELFTEST PASS** (no decoder code changed; this
> was a live AccuMark check, not a file-format decode).
>
> ## STATUS 2026-09-10 (later night) — the model's fabric-type byte closed out
>
> Cross-referenced `parse_model`'s already-extracted 14-byte per-piece
> "flags" blob against `parse_pieces_section`'s already-decoded section-10
> `flag` field (both existed in code; nobody had checked whether they're
> the same value). They are, exactly: every `OUMO` piece in `2303-BD 137
> PLACED` reads `0x41`/`'A'` in both the model object and section 10, every
> `INMO` piece reads `0x44`/`'D'` in both. Checking across fabric codes
> shows the letter tracks AccuMark's own **Fabric Type** role (self vs.
> lining), not the specific fabric roll string — `OUCF` and `SA60151TH`
> are different fabric identifiers but both read `'A'`, matching the
> "Fabric Type" column seen directly in Easy Order's UI earlier this
> session, not a per-fabric-string hash. Full detail in §5.
>
> `python selftest.py` → **SELFTEST PASS** (analysis only).
>
> ## STATUS 2026-09-10 (night) — section 14: first confirmed semantic content, plus a clean per-point record framing that only holds for the simplest case
>
> Went back to `CLAUDE-GRADE-TEST`'s two records (`RECTANGLE2G`/`RECTANGLE18G`,
> 65 bytes each - the smallest streams in the corpus and the only genuinely-
> graded ones available) and mapped them byte-for-byte instead of just
> diffing whole streams.
>
> **Record framing (this piece only):** an 8-byte header, then one 8-byte
> record per NUMBERED perimeter point, each starting with a literal `u16`
> point id (`01 00`, `02 00`, `03 00`, `04 00` - this piece's real ids,
> found at exactly the expected 8-byte stride), except the *last*-listed
> point's record, which continues on to the end of the stream (33 bytes
> here) rather than stopping at 8.
>
> **The point records for ids 2/3/4 (unruled - no `rule_ref` on this
> piece) are byte-identical between the two sizes**, confirming they are
> not storing per-size coordinates - consistent with AccuMark computing
> their positions the same way this project's own `graded_outline()` chain-
> interpolation does, rather than storing them.
>
> **First real crack in section 14: found what the header actually holds.**
> Point 1 (the piece's only ruled point, rule 1) is graded to Y = 58369
> (size "2") and Y = 51287 (size "18") in 1e-4 in - values computed
> independently via `graded_outline()` (base Y 57190, plus the rule's
> cumulative delta). The `u16` at header offset 5 reads exactly `58369` on
> the size-2 record and exactly `51287` on the size-18 record - a precise
> match, not an approximation, confirmed on two independent, genuinely
> different values. **This is the first concrete semantic field ever
> identified in section 14.** The matching X coordinate (318371 / 332540 -
> too large for a `u16`) was not found anywhere in the header or the long
> trailing record under `i32`/`u32`/`float32` at any byte offset - still
> unlocated.
>
> **The clean 8-byte-per-point framing does not generalize as-is.** Tried
> the identical stride search on a real production piece with 5 genuinely
> graded (if placeholder-valued) points (`2303-B1-A1- OUCF-SP24`, 272-byte
> stream): the expected id sequence at 8-byte stride from a plausible
> header length was not found at any tested header length (2-12 bytes),
> and the piece's own rule id (`10001`) does not appear literally anywhere
> in the stream either. Record length most likely scales with each point's
> own attribute complexity (as the piece's own perimeter-point records do
> elsewhere in this format) rather than being a fixed 8 bytes in general.
>
> **Independent confirmation that placeholder-graded pieces produce zero
> stream variation:** diffed all 10 same-piece, different-size records of
> that same OUCF piece (32A through 38A) - **zero differing bytes across
> every pair**, matching the already-established fact that style 2303's
> grading is all-zero placeholder. This is expected, not a gap: a piece
> whose shape genuinely never changes should have a genuinely unchanging
> stream, and now it's been checked pairwise across all 10 of its real
> size records rather than assumed.
>
> `python selftest.py` → **SELFTEST PASS** (analysis only; no decoder code
> changed this pass).
>
> ## STATUS 2026-09-10 (evening) — the type-10 object's structure is now mapped, even though its bulk content isn't
>
> New angle, not another encoding sweep: every AccuMark object shares one
> envelope (magic, name, type at 0x7a) - the *marker* object additionally
> carries its own 42-slot section directory at 0x8a. Nobody had checked
> whether the embedded type-10 blob, which starts with the same `XGGT
> IXPORT` magic and its own name, *also* has a directory at that same
> offset. It does.
>
> **Confirmed identically across three independent markers** (`2303-BD 137
> PLACED`/`unlaid` production pair, `CLAUDE-GRADE-MARKER`, `AD1234 TEST
> 134` - 2, 13 and 97 placements respectively):
>
> - Directory slots used: **33, 35, 36, 37, 39, 41** (of 42) - the same set
>   every time.
> - Slots 35 (88 B), 36 (44 B), 37 (4 B) are small, fixed, and **byte-for-
>   byte identical** whether the marker is laid or not.
> - **Slot 33 exists only when laid** and is exactly `22-byte header + N ×
>   72-byte records` where `N` = the marker's own placement count (2, 13,
>   97 all confirmed exactly). Every single record in every sample is
>   `ff ff ff ff` + 68 zero bytes, uniformly - a per-placement array that
>   gets allocated to the right size but is never populated with real
>   content in anything captured so far. This is what accounts for the
>   "168 → 175 KB when laid" growth previously logged: it's exactly this
>   array's size (7008 B for 97 placements), not per-placement geometry.
> - **Slot 39 is 95%+ of the object's bytes** (167,602 of 175,050 on
>   `PLACED`) and is the same *length* whether laid or not, differing by
>   only **19 bytes total**, every one of them inside its own trailing
>   object trailer (§ below) - not scattered through the bulk. This rules
>   out per-placement position/rotation data living anywhere in type-10:
>   97 real placements cannot be encoded in 19 changed bytes.
> - That 19-byte trailer diff is fully explained, and confirms type-10 uses
>   the **same trailer format as every other object** (name, two identical
>   Unix timestamps, `u32` constant `5`, repeated `MSI` author slots) - the
>   only new field is a `u16` right after the `5` that reads `0x0000`
>   unlaid and `0x0002` laid: a genuine, if minor, laid-state flag.
> - Slot 39's own content: **low entropy** (1.6-1.9 bits/byte vs ~8 for
>   compressed/random data, on all three markers) and **85-95%+ of its
>   bytes are the raw values 0, 1 or 2**. This rules out both a
>   straightforward coordinate encoding (already tried pre-2026-09-10:
>   int32/int16/float32/float64, 8 orientations, absolute or delta - all
>   negative, now explained *why*: real coordinates don't look like this)
>   and a compressed encoding. Its size doesn't divide cleanly by
>   placement count, section-14 record count, size count, or model count in
>   any sample tried. Still the one piece of this object with no working
>   hypothesis.
>
> **Net effect:** the type-10 object is no longer "an opaque 168-175 KB
> blob with no geometry found anywhere" - it's a mapped envelope + directory
> + one fully-characterized placeholder array + a fully-explained trailer,
> with exactly one remaining unknown (slot 39's low-entropy bulk), which is
> now a much narrower, well-described target than "the whole object" was.
>
> `python selftest.py` → **SELFTEST PASS** (analysis only this pass; no
> decoder code changed).
>
> ## STATUS 2026-09-10 (later) — `@454` closed on independent data; section 14 narrowed further
>
> **`@454` — now confirmed, not just "understood in the simple case."** The
> gap left by the previous pass was that both controlled tests happened to
> place the *same* piece repeatedly, so `Σ(quantity × perimeter)` couldn't be
> told apart from `n_placements × (one piece's perimeter)`. Found two
> pre-existing markers already sitting in `DATA90` (`AD1234 TEST 134`,
> `LADIES-BLOUSE TEST-2`) and exported both. `AD1234 TEST 134` is a genuine
> third, independent data point - not something built for this investigation -
> with 13 placements of `ID1005 - RUFFLE` (a 142-point gathered/curved
> piece, nothing like the rectangles used before): predicted `13 ×
> perimeter(RUFFLE) = 764.06`, actual `@454 = 764.32` - 0.03% off, on the
> same order as the curve-tessellation residuals already accepted elsewhere
> in this project. `LADIES-BLOUSE TEST-2` hit the known "Include Components
> silently drops pieces" limitation (0 of 5 needed pieces came through) and
> also exposed a real bug fixed along the way: `accumark_marker.parse_marker`
> raised `KeyError: 'size'` when a slot's best-area-match record's own text
> didn't match any declared piece name (that record never got a `'size'` key
> set at all) - now defaulted to `None` up front so binding never crashes on
> an unmatched record. `selftest.py` still passes after the fix.
>
> **Section 14's per-point stream — two more hypotheses tested, one ruled
> out, one narrowed:**
> - **Not a literal copy of the piece's own raw bytes.** Searched the piece's
>   full raw `.tmp` data for the stream's own bytes at 200/100/50/20/10-byte
>   granularity: zero matches at every size, on `2303-B1-OUMO-5-SP24`'s
>   2634-byte stream. Whatever derives this stream from the piece, it isn't
>   a direct embed.
> - **Total length tracks piece complexity, clustered by piece *family*, not
>   a single global ratio.** `stream_len / raw_piece_size` clusters tightly
>   within a style: OUCF fold pieces (4 samples) land at 0.0414-0.0436;
>   OUMO/INMO cup pieces (6 of 8 samples) land at 0.0853-0.0892 - a
>   different, family-specific proportionality, not one constant across the
>   whole format. (Two OUMO outliers, `-2`/`-4`, sit at ~0.10 - unexplained.)
> - **The stream opens with a short run of small values, then goes opaque.**
>   The first 22 bytes of `OUMO-5`'s stream are 11 `u16` pairs, every value
>   ≤ 73 (well inside its 117-point perimeter's index range - plausibly
>   point ordinals or a small record count) before the remaining ~2600 bytes
>   stop looking like anything structured at the `u16` level. Byte-level
>   layout past that header is still open.
>
> `python selftest.py` → **SELFTEST PASS** (one real fix landed this pass -
> the `KeyError` above - plus two new marker fixtures added to `markers/
> misc-test-markers/` as read-only reference data, not yet wired into
> `selftest.py`'s fixture list since `LADIES-BLOUSE TEST-2` can't fully
> decode without its missing piece components).
>
> ## STATUS 2026-09-10 — a pass at §5's "still open" list: two solved, one reframed, one narrowed
>
> Worked the long-tail unexplained-byte list (piece-side §10.3/§12 and
> marker-side §5) end to end — pure re-analysis of existing captures first,
> then two small new AccuMark objects (`CLAUDE-QTY-TEST` order+marker) built
> specifically to isolate one field each. Full detail is in `FORMAT_SPEC.md`
> §10.1/§12 for the piece-side items; summary for the marker side:
>
> - **Order quantity field — found.** Each per-model-size row in an Order
>   object is `[model name]\0 [u16 flag] [u16 QUANTITY] [~26-30 zero bytes]
>   [ASCII size name] …`; confirmed by building `CLAUDE-QTY-TEST` (quantity 3
>   for size "8" of `CLAUDE-GRADE-MODEL`, every other size left at 0) via
>   Easy Order and finding `u16 = 3` at exactly that position, against `u16 =
>   1` at the analogous position in every one of `2303 MOCUP`'s real
>   quantity-1 rows.
> - **Section 13 — already solved, this doc was stale.** `accumark_marker.
>   parse_marker()` already computes it as `record_index`: cumulative byte
>   offsets into section 14's per-piece records (66 values for 66 records on
>   `PLACED`, monotonically increasing, diffs are the records' own byte
>   lengths). The "36 u16 pairs" description in the old version of this list
>   was never updated after the code caught up.
> - **`@454` — proven not constant.** It read 19.5158 on every sample so far
>   because every sample so far was an export of the *same* two marker
>   sessions (`2303-BD 137` unlaid/laid; the four July corner probes share
>   one session too). Across five genuinely different markers it ranges
>   19.5–134.5. It matches `Σ(quantity × that placement's own perimeter
>   length, inches)` exactly on both `CLAUDE-GRADE-MARKER` (2 placements,
>   89.6476 = 2 × 44.8238) and `CLAUDE-QTY-TEST` (3 placements of the same
>   piece, 134.4714 = 3 × 44.8238 — the piece's real perimeter, computed
>   independently from its own geometry). Does not resolve against `PLACED`
>   with only that fabric group's pieces on hand (its models list other
>   sizes whose piece objects aren't in this particular export) — the
>   formula is confirmed on controlled data, not yet on a fully-self-
>   contained production marker.
> - **Section 14's per-point stream — hypothesis from this list ruled out.**
>   It is not the piece line table's TLV grammar (searched a 65-byte and a
>   2634-byte sample for the `0a 00` record header used everywhere in that
>   grammar: zero hits in either). Confirmed piece-level rather than
>   per-placement: two records of the same piece at very different sizes are
>   byte-identical apart from one heap-pointer-shaped value and a trailing
>   1-byte counter. Its own internal structure past that is still open.
>
> `python selftest.py` → **SELFTEST PASS** throughout (no decoder code
> changed this pass — this was documentation/analysis plus two new,
> clearly-named test objects in `DATA90`, not a fix to `accumark_marker.py`
> or `accumark_pds.py`).
>
> ## STATUS 2026-09-09 (later night) — M3 (graded placements) closed with a controlled test
>
> The one real gap left after §4's captures: style 2303 has no genuine
> grading, so `graded_outline()` had never been proven against a placement
> that actually moves. Rather than wait for a genuinely-graded production
> style, built the minimal controlled test directly in AccuMark: a fresh
> rectangle (`CLAUDE-GRADE-TEST`, `C:\DATA90`), assigned the existing
> `CAP-RULES-A` rule table (real, non-uniform per-size-break deltas, already
> validated on the piece side by `CAP-C20-RULE-DISTINCT`), rule 1 applied to
> only 2 of its 4 corners (Grade tab → Rule Number — the Track/Stop toggle
> from `AGENT_KNOWLEDGE_BASE.md` §10c is exactly right: canvas clicks only
> move the selection in Track mode, typing into D1 only registers in Stop
> mode) so the other 2 corners exercise `graded_outline()`'s chain-
> interpolation branch, not just the explicitly-ruled points. Bundled it into
> a model (`CLAUDE-GRADE-MODEL`, since the Marker Wizard requires a model, not
> a bare piece) and placed it twice in its own marker — size 2 and size 18,
> the two ends of the table, both far from base size 8 — via manual
> drag-to-canvas placement in Easy Marking (AutoMark reported "Success" but
> silently placed 0 of 2 pieces; not investigated further since manual
> placement is trivial for 2 pieces).
>
> Result, against AccuMark's own drawn DXF of that marker
> (`markers/CLAUDE-GRADE-MARKER/`): **both placements' graded outlines
> match to dxf_outline_max = 0.001 in**, centres to 0.0007 in, `bbox_ok 2/2`.
> This proves `graded_outline()` correctly reconstructs a genuinely different
> per-size shape — including the two interpolated corners — not just the
> two explicitly-ruled ones. Now a permanent `selftest.py` fixture.
>
> One decoder-adjacent snag worth recording: `accumark_marker.place_marker()`
> only looks for a piece object inside the *same* zip as the marker. PDS's
> own marker export (with "Include Components" checked) hit "Error: not all
> components exist" and silently dropped the piece from the zip — fixed for
> this fixture by exporting the piece separately and merging its `.tmp`
> member into the marker zip (`list_zip` classifies by content, not member
> name, so this is a legitimate zip, not a hack around the format).
>
> ## STATUS 2026-09-09 (night) — §4's three inputs captured and validated, live on the AccuMark machine
>
> Captured directly from AccuMark (Easy Marking → Marker Plot for the drawn
> DXF; PDS File → Export for the two piece DXF+ZIP pairs) rather than waiting
> on the user — style 2303's `Test` storage area on `C:` already had
> everything named in §4.
>
> | file | result |
> |---|---|
> | drawn-marker DXF of `2303-BD 137 PLACED` (`markers/2303-BD137-PLACED/2303-BD 137 PLACED.DXF`) | **97/97 placements matched**, centres worst 0.0012 in, outline Hausdorff worst 0.0205 in — closes §4a, the acceptance test for the whole placement/transform pipeline across every rotation, mirror, flip-H and fold piece in the marker (previously only exercised by the July set's 4 markers × 1 placement each) |
> | ASTM DXF of `2303-B1-38B-IN WG-SP24` (wing piece, 15-byte curve records, `captures/2303-B1-38B-IN WG-SP24/`) | **dxf max\|delta\| = 0.000000 in** — closes §4b for Fix 2: the variable-width point record is exactly right on real production curve data, not just `CAP-*` synthetic pieces |
> | ASTM DXF of `2303-B1-A1- OUCF-SP24` (fold piece, `captures/2303-B1-A1- OUCF-SP24/`) | **dxf max\|delta\| = 0.0001 in** (print rounding) — closes §4b for Fix 5: fold unfolding is exact on a real production fold piece |
>
> **New finding along the way, now fixed:** the drawn-marker DXF's raw
> polyline vertices are in whatever unit the AccuMark session was set to —
> `$INSUNITS 1` (inches) on the July markers, `$INSUNITS 5` (centimeters) on
> this one (`2303-BD-137-PLACED.DXF`'s own bbox was exactly 377.68 × 137.0,
> the marker's `length_cm`/`width_cm` to the decimal — the tell). `verify_
> marker.dxf_marker()` was comparing raw cm values against inch-based
> placements with no conversion, off by ~2.54× (worst case ~111 in before the
> fix, 0.0012 in after). Fixed by reading `$INSUNITS` and scaling to inches;
> also fixed a latent bug the same investigation exposed — `dxf_facts`'s
> glob for `*.dxf`/`*.DXF` double-counts a single file on a case-insensitive
> filesystem, defeating its "only one DXF in this folder" shortcut. Neither
> fix changes the July markers' own numbers (still ≤0.0008 in / ≤0.078 in;
> `selftest.py`'s per-marker tolerance for `dxf_centre_worst` is now 0.0015
> in generally, not 0.001, to allow for the cm→inch round-trip's slightly
> coarser precision on this vintage — still an order of magnitude tighter
> than the outline-tessellation budget).
>
> `python selftest.py` → **SELFTEST PASS**, now on 7 marker fixtures (the
> `2303-BD137-PLACED` entry gained its `--dxf` check).
>
> **What's left of §4, and the one real gap:** §4c (tilted piece, group/block
> placement, alpha-size style) is untouched. More importantly, **M3 (graded
> placements) is still unproven** — style 2303 has no real grading (every
> rule reference is the placeholder `10001`, confirmed again on both new
> piece captures), so `graded_outline()` has never moved a point on real
> data. That is the next input worth asking for, not another §4-style capture
> this machine can already supply.
>
> ## STATUS 2026-09-09 (evening) — decoder work of §3 done through M4
>
> `python selftest.py` → **SELFTEST PASS** on the 21 piece captures **and**
> the six markers now in `markers/` (2303-BD 137 unlaid, laid, and the four
> July corner probes with their drawn DXFs).
>
> | item | state | evidence |
> |---|---|---|
> | Fix 1 point-table locator | **done** | 162/162 production pieces; C61's "missing 4th corner" was this bug (spec §4 corrected, selftest expectation updated) |
> | Fix 2 variable-width records | **done** — the real cause was narrower than dxfparser's grammar: the `rule_ref` group follows whenever `f1`'s low byte is 0 (a corner carrying a notch, `f1 = 0x0N00`) | the 8 failing wing pieces now read `n_perimeter − 1` points with sane bboxes |
> | Fix 3 header residue | **done** — field-block search from 0x80, type from 0x7a | 122 July-vintage pieces decode |
> | Fix 4 refuse non-piece objects | **done** — `decode()` raises on type ≠ 20; `accumark_marker.read_object` reads every type | |
> | Fix 5 fold halves | **done** — `accumark_pds.mirror_lines()` / `unfold()`; `accumark_marker.piece_outline()` unfolds about the two perimeter points the `M` block names | the four OUCF pieces reach declared area to ≤0.7 % and pass the home×2 bbox test |
> | Fix 6 `summarize()` speed | **done** — 58 s → 0.01 s (pre-filter + `n_sizes` cap in the offset scan) | |
> | M1 `accumark_marker.py` | **done** | 97/97 slots bound; Σ areas = W·L·U exact; piece list with fabric codes, models, size rows, record index all parse on both vintages |
> | M2 `verify_marker.py` | **done** — report, `--expect`, `--dxf` (placement centres + outline Hausdorff), `--baseline` section-aware diff | July markers: centres ≤0.0008 in, outlines ≤0.078 in |
> | M3 graded placements | **engine written, only trivially exercised** — every rule reference in style 2303 is the all-zero placeholder 10001 and sister sizes share one geometry, so `graded_outline()` moves nothing here. Needs a genuinely graded style + drawn DXF | bbox test 97/97 at 0.02 in |
> | M4 fixtures in `selftest.py` | **done** | |
>
> **What the laid-vs-unlaid diff says (section diff in `verify_marker.py
> --baseline`):** laying changes only section 1 (header scalars), section 2
> (+7 bytes: the name), the slot table (section 21) and the embedded type-10
> object (168 → 175 KB); every list section is byte-identical, just shifted.
>
> **Still open (unchanged from §5):** @454, the type-10 object, section 12's
> `f0` field, the Order's quantity fields, the small parameter tables, and a
> *real* grading test. The three exports in §4 remain the next inputs.

Rewritten 2026-09-09 after analysing four files: `2303-BD 137 marker.zip`
(unlaid), `2303-BD 137 PLACED.zip` (the same marker laid, 97 placements),
`2303 PATTERN-MODELS.zip` (the whole style, 179 objects, July vintage) and
the July `2303-CP 150 CPL …` set (4 laid corner-probe markers **with their
drawn-marker DXFs**), plus the user's earlier repo
`github.com/gellerbatra-max/dxfparser` (`docs/accumark-decoded-so-far.md`
§6 is the marker ledger; `tools/accumark_marker.py`, `v2/accumark/binding.py`
are the reference implementation). Conventions as in `FORMAT_SPEC.md`:
**[V]** demonstrated by a file, **[?]** consistent but unproven.

## 0. Where we are, in five lines

1. **The marker placement format is solved and verified** — by dxfparser on
   2,830 production placements, and here on `PLACED` (97/97 slots bound,
   Σ areas = W·L·U to the last digit) and on the four July markers
   (placement centres match the drawn DXFs to ≤0.0008 in).
2. **`accumark_pds` is the better piece decoder** — its outline for the
   placed piece lands within 0.05–0.08 in of the drawn DXF (dxfparser's own
   is 3.8 in off) and matches every checkable declared area to ≤0.06 %.
3. **But `accumark_pds` needs three fixes for production pieces** (§3): a
   one-line point-table locator fix (validated, `selftest.py` still passes),
   the variable-width point record, and header-residue tolerance for the
   July vintage. After fix 1 alone: 154/162 production pieces decode.
4. **Nothing in the marker needs a GUI capture campaign any more.** The
   remaining marker unknowns (§5) are cosmetic; what is needed is one drawn
   DXF of `PLACED` and two piece DXFs (§4).
5. The rest of this plan is decoder work with the acceptance test for each
   item, in order.

---

## 1. Format facts established (all [V] unless marked)

### 1.1 Object envelope — every `.tmp`, every vintage

| offset | field |
|---|---|
| 0x00 | `XGGT IXPORT DB5.1\0` |
| 0x15 | object name, NUL-terminated (fixed slot) |
| 0x60 / 0x68 | object type u32 — **at 0x60 in the 2026-09 V17 export, at 0x68 in the 2026-07 export** |
| **0x7a** | object type u16 — **same offset in both vintages: read the type here** |
| 0x7e | payload length u32; payload starts at 0x80; `file = payload + 396` except markers |
| last 396 | trailer: u32 created, u32 modified (Unix), u32 5, two user-name slots |

Types: **20** piece · **12** model · **13** order · **9** marker · **10**
marker geometry cache (embedded) · **2** annotation / marker settings (`A`,
`M-MARKER`) · **3** block buffer (`3MM`) · **6** lay limits (`L`,
`COSTINGS`) · **17** notch table (`P-NOTCH`, `V-NOTCH-ALL CUSTOMERS`). The
Order names its annotation, lay-limit, buffer and notch tables in adjacent
fixed slots right after its own name — that is how the types were labelled.

Bytes 0x12–0x7d are heap/pointer residue that differs per machine and
vintage; **the July vintage's residue trips `accumark_pds._find_field_block`**
(it scans from 0x60). Neutralising 0x60–0x7f makes every July piece decode
(§3, fix 3).

### 1.2 Marker object (type 9)

- **Section directory at 0x8a: 42 × u32 absolute file offsets**, `0xffffffff`
  = absent. Used slots on both vintages: 1 header scalars · 2/3 options +
  name (grows with the marker name) · 4/5 per-piece label config
  (`-PDSTEXT-`) · 10 placed-piece list with fabric codes · 11 model list ·
  12 size/bundle list · 13 index [?] · 14 (piece,size) records · 15 copy of
  the order's model/size list · **21 placement slot table** · **30 embedded
  type-10 object**. The marker's payload-length field points at slot 30.
- **Header scalars (double, inches):** width @396, length @412,
  **total placed area @422** (= W·L·U/100, exact), utilisation % @446;
  @454 = 19.5158 on both 2303-BD exports, unnamed [?]. On an **unlaid**
  marker length/util are 0 and @422 holds a stale value.
- **Slot table = directory[21] … directory[30], 96-byte slots** (97 here, 72
  on the July markers; empty slots have placed = (0,0) on this vintage,
  (−1000,−1000) on older ones). Layout (dxfparser, confirmed): placed centre
  f64 @+0/+8 · home (bbox) centre f64 @+16/+24 · orientation u16 @+32 —
  bitmask `0x2000` rotate 180, `0x0080` mirror, both = flip H, other bits
  vintage base data · declared area f64 @+42 · bundle u32 @+64 (low word).
  The directory replaces dxfparser's fingerprint/sentinel locators, which
  fail on this vintage (fingerprint byte `01 01` vs its `11 01`).
- **Slot → piece binding:** the slot's area equals (≤0.1 %) the area in one
  of the section-14 records `[f64 area][f64 perimeter][u16][u16][u16 len]
  [8×0] <piece name><cut description><size>G\0`; 66 records here, e.g.
  `2303-B1-OUMO-2-SP24C-234AG` = piece, cut `C-2`, size `34A`. The same
  piece's records differ only in the size label and a trailing counter —
  the ~30 B/point stream after the label is a per-piece attribute table,
  not geometry.
- **Placed outline** = piece outline mirrored/rotated about its own bbox
  centre, translated to the placed centre. Verified on the four July
  markers: centres ≤0.0008 in; outline Hausdorff 0.046/0.078 in against the
  drawn DXF, whose curves are re-tessellated (95 vs our 85 points) — the
  same class of residual `TASK6-CURVE` showed against a *piece* DXF was
  0.0001 in, so treat this as plot smoothing, to be confirmed by a piece
  DXF (§4 b). The 1.5 mm block buffer (`3MM`) is a gap from the marker
  edge, not an enlargement of the piece.
- **The embedded type-10 object is not needed.** It is a complete object of
  its own (magic + name at +0x1a), 168–175 KB, contains no placed-outline
  coordinates in any encoding tried (int32/int16/float32/float64, 8
  orientations, absolute or delta), and changes wholesale when the marker
  is laid. Hypothesis: the unplaced/graded piece cache [?]. Park it.

### 1.3 Order (type 13) and Model (type 12) — readable, numeric flags [?]

Order: name, four table-name slots, then one block per model with the
requested sizes and quantity fields (`03 00 01 00` on ordinary rows). **Cut
quantity lives here**, per model per size — TASK1's null result explained.
Model: `3d 2b 00 00`, u16 len, piece name, flags incl. `0x41`/`0x44` per
piece [?], `Fabric Table.csv`, model name.

### 1.4 What the style bundle says about this product

Bra style 2303: 22 moulded-cup pieces (`INMO/OUMO 1–11`, graded 1–6 sizes
each), 72 wing pieces stored **one object per size** (`32A-OUWG` … , not
graded), 24 small cup-fabric pieces (`OUCF/INCF`) that are **cut on the
fold** — their decoded area is exactly 0.500 of the declared area — and
models per size range. A marker is per fabric group: `2303-BD 137` places
12 of the 18 pieces exported with it (`SA60151TH`, `SI01040A17`, `OUCF`
fabric codes in section 10).

---

## 2. Verification results (2026-09-09)

| check | result |
|---|---|
| `PLACED` slot parse | 97/97 bound, 61 bundles, x 6.1–144.1 in, y within 53.94 in |
| Σ slot areas vs @422 vs W·L·U | 5735.2104 = 5735.2104 = 5735.2104 |
| dxfparser vs directory locator, `PLACED` | identical placements |
| July markers, 4 × 1 placement, vs drawn DXF | centre ≤0.0008 in; outline 0.046/0.078 in (curve tessellation) |
| `accumark_pds` vs declared areas, 14 cup pieces | ratio 0.999–1.000 |
| `accumark_pds` vs declared areas, 4 OUCF pieces | 0.500 (fold halves — correct) |
| `selftest.py` with fix 1 applied | PASS, coverage unchanged |
| production pieces after fix 1 | 154/162 sane; all cup pieces `n = n_perimeter − 1` (closing point counted, harmless) |

---

## 3. Decoder work, in order — each with its acceptance test

**Fix 1 — point-table locator (validated, ready to apply).** Production
perimeters start at any creation-order id (13, 2, 7…), not 1/−1, and the
table begins exactly at the end of the object records; the window scan
therefore skipped real points (42A-OUWG read 24 of 27 silently) or landed
mid-record (17 pieces garbage). Patch in `accumark_pds.find_point_table`:
```python
    pid = i16(d, after)
    if (pid == -1 or 1 <= pid <= 4096) and COORD_LO < i32(d,after+2) < COORD_HI \
       and COORD_LO < i32(d,after+6) < COORD_HI and u16(d,after+10) in (0,1,2,0x101):
        return after
    # ...then the existing window scan
```
Acceptance: `selftest.py` PASS (done); wing pieces decode with sane bboxes
(done, 154/162).

**Fix 2 — variable-width point records.** The 8 remaining wing pieces carry
a 15-byte curve record `ff ff <x> <y> 01 00 01 00 0a` (14-byte form + a
terminator byte), which dxfparser documents as one of six widths (14, 15,
18, 19, 20, 21; terminator ∈ {09, 03, 0a}; `f1` low word `0x0C00` announces
an extra 8-byte payload). Port that grammar into `parse_point` (see
`dxfparser/v2/accumark/records.py`). Acceptance: 162/162 production pieces
with `n == n_perimeter − 1` and bbox < 20 in; `selftest.py` PASS.

**Fix 3 — header residue.** Start `_find_field_block` at 0x80 (payload
start) instead of 0x60, and read the object type at 0x7a. Acceptance: the
122 July pieces decode without neutralising the header; `selftest.py` PASS.

**Fix 4 — `decode()` must refuse non-piece objects** (type ≠ 20) instead of
`IndexError`; expose `read_object()` (type, name, payload, trailer) for all
types.

**Fix 5 — fold pieces.** `CAP-C61-MIRROR` gave the mirror-line grammar;
expose the axis and an `unfolded` outline. Acceptance: OUCF pieces reach
area ratio 1.00 ± 2 % against the declared area.

**Fix 6 — `summarize()` speed** (4–24 s per production piece; `decode()` is
instant). Profile the tail/coverage search; a 97-placement marker calls it
97 times.

**M1 — `accumark_marker.py`** (new): directory, header scalars, sections
10/11/12/14, slot table, binding (port `binding.py`: area match with
relative tolerance and rival band; size resolution across a piece's record
set — the *cut count is constant within a marker* rule), Order/Model
readers, `summarize_marker()` with the identities (Σ areas = @422 = W·L·U;
bundles; placed-piece list = section 10). Acceptance: reproduces §2 on
`marker.zip`, `PLACED.zip` and the four July markers, and reports
laid/unlaid correctly.

**M2 — `verify_marker.py`**: `report`, `--baseline` structural diff (reuse
`verify_capture.py`'s run classifier), `--dxf <drawn marker>` placement +
outline Hausdorff (port `_dxf_marker_polylines`/`_stitch_pieces`), and
`--expect` keys `placements, bundles, pieces_placed, width_cm, length_cm,
util_pct, area_identity=yes, laid=yes|no, geometry_match=yes`.

**M3 — graded placements.** Most placements are non-sample sizes (OUMO-3 is
placed at 36B, sample 32D). `accumark_pds` already decodes the rule table
and per-point rule references; add `graded_outline(piece, size)` (per-step
increments, smallest size first — see FORMAT_SPEC §3 and dxfparser ledger
§5: unruled points interpolate proportionally, a user-settled rule).
Acceptance: `PLACED` vs its drawn DXF (§4 a), all 97 placements within the
curve-tessellation band; then tighten with §4 b.

**M4 — `selftest.py` fixtures**: add `markers/` with the six markers and
the four July DXFs as regressions (counts, identities, Hausdorff budgets).

---

## 4. Files to ask the user for (small, all exports — no GUI experiments)

a. **Drawn-marker DXF of `2303-BD 137 PLACED`** — 97 placements covering
   rot 180, mirror, flip H, graded sizes and fold pieces in one file; the
   acceptance test for M1–M3.
b. **ASTM piece DXF (+ .RUL) of `2303-B1-38B-IN WG-SP24`** (15-byte curve
   records) **and of `2303-B1-A1- OUCF-SP24`** (fold) — settles whether the
   0.05–0.08 in residual is plot smoothing (expected) and validates Fix 2
   and Fix 5 point-exactly.
c. Later, one marker each with: a tilted piece (non-90° rotation — is it
   even stored in the orientation word?), a group/block placement
   (dxfparser's open gap), and a second style with alpha sizes.

## 5. Still open, none blocking

**Solved since this list was last written (2026-09-10, see STATUS blocks):**
section 13 (`record_index`, already implemented in `accumark_marker.py`,
just never promoted out of this list); Order quantity fields (the u16
immediately before each per-model-size row's zero-padding+size-string);
**`@454`** — confirmed `Σ(placement's own perimeter, inches)` on a third,
independent, pre-existing marker (`AD1234 TEST 134`, 13 placements of a
142-point piece, 0.03% off) in addition to the two controlled tests, so this
is no longer "the simple case only." Only loose end: it still doesn't
resolve against the production `PLACED` marker, whose export doesn't bundle
every piece its order references — a bundling gap, not a formula doubt.

**Ruled point's coordinates fully found — section 14's per-point attribute
stream.** On the one genuinely-graded piece available (`CLAUDE-GRADE-
TEST`), the header holds a packed `(X mod 65536, Y)` pair for the ruled
perimeter point at that placement's size — `u16`s at offset 3 (X, low 16
bits) and offset 5 (Y, exact — this piece never overflows it), both
matching `graded_outline()`'s independently-computed values exactly on
two different sizes, zero error. The 8-byte-per-point record framing that
surfaced this (one `u16`-id-prefixed record per numbered perimeter point)
does not generalize as tested to a production piece with several graded
points — record length there likely scales with per-point attribute
complexity rather than being fixed at 8 bytes, the same variable-length
pattern the piece's own point records use elsewhere in this format.
Confirmed *not* the piece line table's TLV vocabulary (zero `0a 00`
record headers), confirmed piece-level not per-placement (unruled points'
records are byte-identical across sizes; a placeholder-graded production
piece's stream is byte-identical across all 10 of its real size records,
checked pairwise), and confirmed *not* a literal copy of any part of the
piece's own raw bytes. Total length tracks piece complexity in a family-
specific way (`stream_len / raw_piece_size` clusters per style: OUCF
≈0.042, OUMO/INMO ≈0.085-0.089). Full internal layout for anything beyond
the ruled point's own coordinates — including non-ruled ordinary points'
own attributes — is still open, and this framing hasn't been proven on a
piece with more than one genuinely graded point.

**Structurally mapped, one bulk section still unexplained:** the type-10
object — has its own object envelope and 42-slot directory (same convention
as the marker object itself), confirmed identically on three independent
markers. Slots 35/36/37 are small and placement-independent. Slot 33
(laid-only) is a fully-characterized but content-empty per-placement
placeholder array (22-byte header + N × 72-byte all-`ffffffff` records).
Slot 39 (95%+ of the object) does not vary with placement at all — ruling
out per-placement geometry anywhere in this object — and its own low-entropy,
0/1/2-dominated content rules out both a coordinate encoding and compression,
but has no working hypothesis for what it *is*. The object's trailer is the
same format as every other AccuMark object, plus one new tiny field: a laid-
state flag (`0x0000`/`0x0002`).

**Solved — the model's `0x41`/`0x44` byte.** It's the same field
`parse_pieces_section` already decodes from section 10 as `flag` (`[V]`
there already, just never connected to this plan-list item): the model
object stores its own redundant copy, at a fixed offset (+12 in each
piece's 14-byte flags blob following the piece name). Confirmed by exact
cross-reference on `2303-BD 137 PLACED` — every `OUMO` piece is `0x41`
('A') in both places, every `INMO` piece is `0x44` ('D') in both places.
**Not tied 1:1 to the specific fabric code/roll string**: `OUCF` and
`SA60151TH` are two different fabric identifiers but both read `'A'`,
while `SI01040A17` reads `'D'`. Better explained as AccuMark's own
**Fabric Type** role slot (A = self/primary, D = lining/secondary here) —
the same "Fabric Type" column seen directly in Easy Order's UI when
building `CLAUDE-QTY-TEST` earlier this session, which is an abstract
per-style role, distinct from the concrete fabric roll assigned to fill
it for a given cutting order/marker. A third marker's single piece
(`ID1005 - RUFFLE`) reads `'C'`, consistent with a small A/B/C/D-style
enum rather than a per-fabric hash. What exactly governs which piece
gets which letter (beyond "self fabric tends to be A") isn't nailed down,
but the byte itself is no longer unexplained.

**Checked live, no discrepancy found here:** the panel's length allowance —
opened `PLACED` in Easy Marking and read its own status bar directly:
`LN` reads `3m 77.68cm`, an exact match to the decoded value, zero
allowance. The `dxfparser`-reported +4.00/+5.96 cm gap on other styles
doesn't reproduce on this marker; needs a marker that *does* show the gap
to find where it's configured (a fabric/trim setting is the leading
guess — `Fabric/Trim` was empty here since no fabric background is set).
Turned up several other unlabeled status-bar fields (`OL`, `TI`, `PA`,
`TT`, `BD`, `FC`, `FW`, `CB`, `MW`, `PR`) with no identified meaning yet —
new leads, not previously logged.

**Mostly closed — `M-MARKER`/`3MM`/lay-limit/notch table payloads.**
`3MM` (block buffer): decoded, stores the buffer distance directly as
`591` (1e-4 in) = exactly 1.5 mm, x4 (one per edge). Notch table
(`P-NOTCH`/`V-NOTCH-ALL CUSTOMERS`): this is the system-wide notch-shape
table FORMAT_SPEC.md §4 predicted but never located — `P-NOTCH`'s stored
depth (1574 = 0.40 cm) matches the UI-observed "Type 1 default Depth
0.40" from `CAP-C41-NOTCH-WIDTH` exactly. `M-MARKER` (annotation):
structure mapped (creator/date + two named label-config sub-blocks) but
the label field codes themselves aren't decoded. `COSTINGS` (lay limits):
structure only, no confirmed numeric meaning yet. Bonus: identified a
fifth object kind (type 23 = rule table) while surveying the corpus,
confirmed by content match against `CAP-RULES-A`'s known deltas.

**Solved — `M-MARKER`'s label codes.** The shipped offline PDF manuals
(`OrderEntry_Users_AE.pdf`'s Annotation Form section) supply the exact
legend. The `MARKER` sub-block's 8-code constant is confirmed, byte for
byte, as the manual's own documented default `MSQ,/,AP,/,WI,L,U,PS`
(codes 20, 11, 24, 11, 23, 21, 22, 28 - the repeated `/` reproducing the
same byte both times is the tell). The `DEFAULT`/`LABELD` triples are
`[type code, range start, range end]`; `SIZE-AND-BUNDLE`'s two triples
decode as `SZ` (code `07`, range 1-6) and `BD`/Bundle (code `09`, range
1-3), matching the manual's `SZ1-6,BD1-3` default exactly - both the codes
and the numeric ranges check out, not just the codes. This retires the old
"code 07 tentatively SIZE" note (now confirmed) and adds Bundle (`09`)
alongside it. One triple stays a plausible-not-proven reading: the generic
`A` object's `(06,01,14)`, likely `PN` (Piece Name) truncated to 14
characters, since no `PN1-14` default exists in the docs to check against.
`COSTINGS`'s ply-count byte (`1`=`SINGLE-PLY`) is now supported by the same
manuals' documented Fabric Spread enum order (Single Ply, Tubular,
Bookfold, Face-To-Face) rather than resting on name-matching alone, though
2/3/4 remain inferred from list order, not observed on named samples.

**Solved — section 14's X coordinate.** Packed with Y as `(X mod 65536,
Y)` at header offset 3-6; see the dedicated STATUS block above. Only
overflows the `u16` on unusually wide pieces (this test piece is 48 in);
an ordinary piece's X would just read directly, no wraparound.

**Untouched, and the offline-doc route is exhausted for it:** the 8
newer Easy Marking status-bar fields (`TI`, `PA`, `TT`, `FC`, `FW`, `CB`,
`MW`, `PR`) - checked against every shipped manual, not present in any of
them; likely belong to a UI generation newer than these manuals, so closing
them needs either live internet access (for AccuMark's own online help,
confirmed unreachable from this machine) or further live UI probing, not
more offline-doc searching. Also still open: generalizing section 14's
record framing to a piece with more than one genuinely graded point (no
suitable sample exists in the corpus).

## 6. Superseded

The Phase M1/M2 GUI capture campaign of the first version of this plan
(MK-00 … MK-20) — the transform, the noise floor and the oracle were all
answered by dxfparser's work plus the four files above. Keep only the idea
of `MK-14-TILT` and `MK-16-QTY2`-style checks as §4 c.
