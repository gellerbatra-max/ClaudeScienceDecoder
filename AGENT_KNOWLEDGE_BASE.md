# Gerber AccuMark Pattern Design (PDS) — GUI Automation Knowledge Base

Compiled while operating AccuMark V17 Pattern Design (`Work Area 1 - Pattern Design`, PDS MFC
Application) purely through screenshot + mouse/keyboard automation (no API, no scripting hooks).
Written for training/prompting an agent that must drive the same application the same way.

Environment: Windows 11, display 1920x1080, PDS window **maximized**. All pixel coordinates below
assume that exact state. **Coordinates are fragile** — they shift if the window is a different
size, if the ribbon has a different tab selected (groups reflow), or if the canvas has been
scrolled/zoomed. Prefer taking a fresh screenshot and re-locating a control by its label/shape
over trusting a remembered coordinate, especially after any tab switch or dialog close.

## 1. Application shape

- Ribbon UI (like MS Office) with tabs: **Create, Edit, Modify, Advanced, Verify, Grade, Wizard,
  Draft, Images, View, Help**. Each tab shows different tool groups in the ribbon band directly
  below the tab row (~y=44 for tabs, groups roughly y=60-140).
- Below the ribbon: a canvas ("Work Area") on the left/center showing pattern pieces, and a
  **right-hand "User Input" panel** (~x=1670-1920) that is the primary way tools communicate
  state and take input. Almost every tool's behavior is mediated through this panel, not
  standard dialogs — **and its content changes shape per-tool**, sometimes with different pixel
  offsets than the last time the "same" panel appeared. Always screenshot after opening a tool
  before typing/clicking into it.
- Status bar at the very bottom shows the selected piece name (editable-looking field around
  x=497,y=941), a size selector, "Cut"/"Sew" status, and Snap-to / Show toggles (Grid, Seams,
  Notch Shapes, etc.) around y=941.
- Launch via Start Menu shortcut "Pattern Design" (AccuMark V17 folder), or directly via
  `C:\Program Files\Gerber Technology\AccuMark V17\AccuMark\sil2000.exe` (the historical PDS
  binary). Standalone companion tools live in the same folder, notably `RuleTable.exe` (grade
  rule table editor — a *normal* Win32 dialog app, much more automation-friendly than PDS's
  custom-drawn panel; launch it with `Start-Process` from PowerShell/Bash, then
  `App{mode:switch, name:"RuleTable"}` to bring it forward — it opens without a visible window
  handle at first).

## 2. The "User Input" panel / Value Input mechanics (critical, non-obvious)

Most drawing tools (Rectangle, Circle, Point/Drill, etc.) show a **"Value Input"** mini-form with
rows labeled `Beg`/`End`/`Dist` and columns `X`/`Y`/`Ang`. This looks like 6 editable cells but
**it is not a normal set of textboxes**:

- On first activating a tool (e.g. Rectangle), these cells are **blank and not directly
  clickable/typeable** — clicking into them and typing does nothing.
- The values only populate live once you **hover the mouse over the canvas** while the tool is
  mid-operation (e.g. after placing the first corner of a rectangle, hover for the second corner).
  Use a `Click` with `clicks: 0` (hover-only) at a canvas point, then screenshot — the panel will
  show live computed values (e.g. rectangle width in `Beg X`, height in `End Y`, diagonal in
  `Dist`).
- This hover-readout is the **only reliable way to get numeric feedback for precise placement**.
  There is no confirmed way to type an exact target value into these Beg/End/Dist cells for
  shape-creation tools (Rectangle, Circle, Point/Drill) — attempts to click+type into them (even
  after clicking "Cursor" or toggling "Tracking") did not take.
- **Practical technique for precise rectangles**: click a first corner anywhere, then hover near
  the intended second corner, screenshot, read the live `Beg X` / `End Y` values (which for a
  rectangle tool represent width/height, not absolute coordinates — only one of the two doubled
  columns is populated per row: `Beg` row shows the X extent, `End` row shows the Y extent), then
  binary-search adjacent 1px hover positions until the displayed values are within your tolerance
  (sub-pixel precision is not achievable this way; ~0.02-0.1cm residual error is typical at 100%
  zoom — the on-screen scale is roughly **10.8 px/cm** at default zoom, so 1px error ≈ 0.09cm).
  Then click to commit. Grid/snap checkboxes (bottom bar) did **not** appear to force clean
  snapping in testing — don't rely on them for exact values.
- A **single free-form textbox** does exist at the top of the Value Input area, and *is* directly
  typeable — it is reused for whatever the current tool's single scalar input is (seam allowance
  amount, piece name on creation, etc.). Click it, then `Type` with `clear: true`. This one works
  normally.

## 3. Piece creation workflow

1. **Create tab → Piece group → Rectangle** (button location varies slightly by ribbon scroll
   state; look for a "Rectangle" labeled icon, historically around x=793-825,y=74). Click it —
   panel shows "Press to select one corner, press again to select other corner." (this text does
   **not** change between the first and second click — don't rely on it to know which corner
   you're on).
2. Click first corner on canvas.
3. Hover for the second corner using the width/height-readout technique above; click to commit.
4. A "piece name" textbox appears in the panel with a default name (e.g. `P2`) pre-selected —
   `Type` your name into it with `clear: true`.
5. Click **OK** (bottom of panel, position shifts — screenshot first; roughly x=1710,y=629 or
   x=1709,y=781 depending on panel height) to finalize. The tool re-arms for another piece —
   press the panel's **Cancel** button to fully exit the tool (do NOT press Escape — see §6).
6. **Circle**: Create tab → Notch/Piece area → "Circles" split-button → "Center". Click center
   point, click again for radius, name it, OK.
7. **Copy an existing piece** (much faster than redrawing for creating variants): right-click the
   piece on canvas → context menu → **"Copy Piece"** → click the piece again to confirm the
   source → right-click empty canvas → **"Paste Piece"** → click to drop it → OK the naming
   prompt. The pasted copy often lands **far off to the side** (partially or fully off-screen);
   scroll or just work with the visible sliver — clicking a partially-visible piece still selects
   it correctly.

## 4. Saving and naming pieces

- **File tab → Save As** (File menu is a full-screen "backstage" view, not a dropdown — click
  "File" at x≈33,y=44, then "Save As…" in the list, e.g. x≈54,y=262). A dialog appears showing
  the AccuMark piece database folder (`DATA90`) with existing piece names listed; there is a
  filename textbox pre-filled with the current/default name — clear and retype it, click Save.
- This is the primary way to give a pasted-copy piece a permanent distinct name (don't rely on
  renaming via the bottom-status-bar name field or piece-properties dialogs — those did not
  accept typed edits reliably in testing).
- Piece "Cut Quantity" is **not** a PDS/piece-level property. Checked Piece Properties,
  Piece Utility, and Current Pieces dialogs — none expose it. It belongs to the separate
  **Model** or **Order** module (`Model.exe` / `Order.exe`), which is outside PDS's scope.

## 5. Export workflow (DXF and native AccuMark ZIP)

1. **File → Export**. Select the piece on canvas (prompt: "Select piece(s)").
2. A standard Windows Save dialog opens, defaulting to the AccuMark piece storage path mapped to
   a real filesystem location (seen here as `C:\DATA90\...`, but the **"Save in" dropdown lets
   you navigate to any real folder**, e.g. `D:\...`). Filename defaults to the piece name.
3. **"Save as type"** dropdown offers: `ASTM (*.dxf)`, `AAMA (*.dxf)`, `Standard DXF (*.dxf)`,
   `IGES (*.igs)`, `ZIP files (*.zip)`. ZIP is AccuMark's native interchange format (piece +
   metadata, importable by another AccuMark install); DXF is plain geometry.
4. For ZIP, after clicking Save an **"Export Summary"** dialog appears showing From/To paths and
   checkboxes: Include Components, Include Model Notes, Only 1st Level Subfolders, Include
   Images, Include Measure Charts, Include Pieces From Selected Model Options, **Include Grade
   Rule Table** (only enabled/meaningful if the piece actually has a rule table assigned —
   check it for graded pieces), Include 3D Components, Include Vizoo Images, Only selected
   Colorways. Click OK.
5. A benign **"AccuMark Compatibility Warning"** ("...may only be imported into a V9 storage
   area") always appears for ZIP exports — just click OK, it is not an error.
6. A final **"Process Completed"** dialog confirms success — click OK.
7. DXF export (no ZIP) is more direct: after picking the folder/filename and clicking Save, an
   **"Export Results"** window shows a tree (e.g. "ASTM") with 0 errors/warnings on success — close
   it with its own titlebar X (top-right of that sub-window, not the main app).
8. **Every DXF export also silently drops a `<piecename>.RUL` file** next to the DXF in the same
   folder (even for ungraded pieces — it's a stub/empty rule table in that case, ~5.8KB; for a
   genuinely graded piece it's much smaller, e.g. ~476 bytes, and contains the real per-size
   deltas). This is a useful signal: a small `.RUL` size indicates a real custom grade table was
   captured; a large uniform size across exports indicates an empty/default stub.

### File-dialog "New Folder" gotcha

- The Save/Export dialogs have a toolbar "New Folder" icon (≈x=461,y=94 when the dialog is at its
  default size/position). Clicking it creates a folder named literally `New folder` in
  rename-mode.
- **Typing a name immediately and pressing Enter does NOT reliably commit the rename** in this
  dialog — it was observed to sometimes silently fail, leaving the folder as `New folder` while
  the dialog's path bar still shows the *typed* name (a mismatch that looks correct but isn't).
  **Always verify on disk** (e.g. `ls`/`Get-ChildItem`) after creating a folder this way rather
  than trusting the dialog's own display.
- If the rename didn't take, **do not try to `mv`/`Rename-Item` the folder while the PDS Save/
  Export dialog still has it open or was ever navigated into** — the OS reports
  "Device or resource busy" / "used by another process" even after clicking Cancel on the dialog,
  because PDS appears to keep an internal handle/MRU reference to any folder its file dialog has
  browsed into, and this lingers for the rest of the session (retrying later, closing and
  reopening the dialog, and navigating elsewhere first did not release it in testing).
  **Workaround**: `mkdir` a correctly-named folder and `cp` the exported files into it, then
  leave the stray `New folder` alone (harmless) rather than fighting the lock.
- **More robust pattern**: pre-create the destination folder with `mkdir -p` *before* opening the
  Export dialog, then just double-click into that already-correctly-named folder inside the
  dialog. Avoids the rename step entirely.

## 6. Tool-cancellation semantics (Escape is dangerous)

- Pressing **Escape** while a shape tool has a pending first point **discards that in-progress
  point silently** and can leave the tool in a confusing state. Prefer clicking the panel's own
  **Cancel** button to back out of a tool.
- Switching ribbon **tabs does not cancel an active tool** — e.g. leaving the Rectangle tool
  active and clicking to a different tab, the tool stays armed and the next canvas click is
  still interpreted as a corner placement, not a piece selection. Always explicitly click
  **Cancel** in the User Input panel before assuming you're back in a neutral "select" state.
- To select an already-existing piece (for copy/export/right-click menus/etc.), you must be in
  this neutral state — no drawing tool active.

## 7. Right-click context menu (on a piece, no tool active)

Useful items observed: **Piece Properties…** (read-only info list — Device, Storage Area, Model,
Rule Tables, Piece Name, Piece Type, Category, Description, Fabric, … — no cut-quantity, no
editable fields), **Edit Piece Info…**, **Current Pieces…** (piece picker list, no properties
columns), **Copy Piece**, **Paste Piece** (only on empty canvas right-click). Right-clicking
*while a tool is still active* opens that tool's own mini context menu instead (e.g. Export tool
showed "Cancel" here) — another reason to explicitly Cancel tools before right-clicking for the
real piece menu.

## 8. Seam allowance (Advanced tab)

1. **Advanced tab → Seam group → Define**.
2. Click the piece to select it for the seam operation — **click precisely on the intended
   piece's edge/interior**; clicking near another nearby piece will select *that* one instead
   (no confirmation step warns you), so double check the highlighted piece before typing an
   amount.
3. The single free-form Value Input textbox becomes active — type the seam amount (respect the
   unit shown in the bottom status bar, typically `cm`; **1mm = 0.10 cm**), e.g. `0.1` or `1.0`.
4. Click **OK** in the panel. Success is visible as: the piece's outline gains a dashed offset
   line, and the bottom status bar's Cut/Sew indicator flips from **"Cut" to "Sew"** — this is the
   reliable confirmation signal (don't just trust "no error dialog appeared").
5. "Manual - Even" is the default seam type — a uniform allowance around the whole perimeter.
6. To back out without applying to a wrongly-selected piece: click **Cancel** in the panel (not
   OK) — verified this correctly avoids modifying the piece.

## 9. Notches and interior/drill points (Create tab)

- **Notches**: Create tab → Notch group → "Standard" (or the dropdown for other notch types).
  Tool prompts "Indicate notch position." Click a point on/near a piece edge — it snaps to the
  nearest boundary line and drops a small tick-mark notch there. The instructional text does
  **not** change between placing the 1st and 2nd notch — you can just keep clicking additional
  edge points and it keeps placing notches until you Cancel.
- **Interior/drill points**: Create tab → Point group → "Point/Drill". Prompts "Indicate point
  position." Click anywhere inside the piece interior (not on an edge) to drop a point marker.
  Same multi-click-without-reconfirm behavior as notches.
- Both tools' Value Input panel shows the same non-functional Beg/End/Dist grid as shape tools —
  don't expect to type exact offsets there either; place by eye/hover-readout if precision
  matters, or accept approximate placement for a "roughly N cm from a corner" spec.

## 10. Grading workflow (Grade tab) — the hardest, most fragile part

Grading a piece requires, in order: (a) a **Rule Table** file existing on disk with defined
sizes and at least one numbered **Rule** (X/Y delta per size-break), (b) **assigning** that table
to the piece, (c) **assigning a specific rule number** to each point you want graded.

### 10a. Building a Rule Table (use the standalone `RuleTable.exe`, not PDS)

PDS's own **Grade tab → Assign Rule Table** dialog lets you pick an *existing* library (it shows
whatever `.RUL`-family libraries already exist under `DATA90`, e.g. sample libraries like
`A1-LADIES` with sub-tables `ID 1X-4X`, `ID 2-18`, `ID XS-XL`) or type a *new library name* to
create an empty one — but **PDS itself gives no way to define what rule numbers/values exist
inside that new library**. Guessing at pre-existing sample-library rule numbers (tried plain
values like `1`, `1.00`) reliably produced a **"Invalid Grade Rule specification"** error — those
numbers don't exist in the sample table and there's no way from within PDS to discover valid
ones.

**Instead**, launch the separate app directly:
```
Start-Process 'C:\Program Files\Gerber Technology\AccuMark V17\AccuMark\RuleTable.exe'
```
It opens with no visible taskbar entry at first — find it via
`Get-Process | Where-Object ProcessName -like '*Rule*'` then
`App{mode:"switch", name:"RuleTable"}`. This is a genuinely normal Win32 app (real editable
textboxes, real menus) — much easier to automate than PDS.

Two tabs at the bottom: **"Rule Table"** and **"Rules"**.

- **Rule Table tab**: fields `Comments` (2 lines), `Size Names` (dropdown, e.g. "Numeric"),
  `Smallest Size`, `Base Size`, `Size Step`, and a `Next Size Breaks` grid (list of the sizes
  above the base size — fill it manually, one per row, e.g. base=8/step=2/smallest=2 needs rows
  `10,12,14,16,18` typed in — it does **not** auto-populate from Base/Step, verified by testing).
  All of these are normal editable textboxes/grid-cells — click, `Type` with `clear:true` works
  directly (no hover tricks needed here, unlike PDS).
- **Rules tab**: shows `Grade Method: Small-Large Incremental`, a live `Grade Rules in Library`
  counter, and a spreadsheet-like table: header rows `Number:` / `Comment:` / `Point Attribute:`,
  then one row per size-break pair (e.g. `2-10`, `10-12`, `12-14`...) with `X`/`Y` columns.
  Type a **Rule Number** (any integer you choose, e.g. `1`) into the `Number:` cell — as soon as
  you fill in a value anywhere for that rule, the library's "Grade Rules in Library" counter
  increments and a **new blank "Rule" column auto-appears** to its right (ready for Rule 2, if
  you want a second rule with different values, e.g. for different points that should grade
  differently). Fill the X/Y numeric delta for each size-break row (values are the **incremental**
  change per step, e.g. `1.00` in every row = grows 1cm every size step, both axes).
- **Save**: `File → Save As` — normal dialog, `DATA90` storage area, gives it a library name
  (e.g. `TASK5-RULES`) of your choosing. This is the name you'll pick in PDS's
  "Assign Rule Table" list afterward — it appears there immediately once saved.

### 10b. Assign the table to a piece (PDS, Grade tab)

**Grade tab → Assign Rule Table**. Panel prompts "Select piece(s)." — click the piece, then a
dialog (`Assign Rule Table`) lists Device/Path (`C:` / `DATA90`) and a library listbox including
your newly-saved custom table. Click it, click OK, then **click the piece again** (the dialog
reopens to confirm) and OK again — it takes two rounds of piece-click + OK in testing before it
actually commits (the bottom status bar's size-selector changing from blank/`D1` to a real size
number like `8` is a sign it stuck).

### 10c. Assign a rule number to each point (PDS, Grade tab → Rule Number) — fiddly

**Grade tab → Modify group → Rule Number** opens a **"Tracking Information"** floating dialog
(titlebar "Tracking Information", not part of the right-hand panel) with tabs Piece/Line/Point/
Notch/Filter. On the **Point** tab: `Point Id:`, `Grade Rule: D1/D2/D3/D4` (four numeric cells —
in testing only `D1` was needed/used for a simple 2-axis rule; D2-D4 appear to be for
multi-directional/complex grading not exercised here), `Attributes:`, and buttons
**Enable / (arrow) / Track-or-Stop (toggles label) / (arrow)**, then OK/Cancel/Apply.

Observed, somewhat non-obvious behavior:
- Clicking a point on canvas while this dialog is open updates `Point Id:` to that point's ID —
  but **only when the toggle button (which reads "Track" or "Stop" depending on state) is in
  "Track" mode**. If it currently reads "Stop", canvas clicks don't change which point is
  selected.
- **Typing into the `D1` field only works when the toggle is in "Stop" mode** (i.e. you must
  click the toggle to switch it to "Stop" — its label will now read "Stop" — *then* click into
  D1 and type). If you type while still in "Track" mode, the text does not appear.
- **The D1 field is not auto-cleared between entries.** If you type `1` on top of a previous `1`
  that wasn't cleared, you get `11` — which produced the same "Invalid Grade Rule specification"
  error as an unrecognized rule number. Always click into the field, `End` then `Shift+Home` then
  `Delete` (or equivalent select-all-and-delete) before typing a fresh value, and verify via
  screenshot that the field shows exactly what you intended before clicking Apply.
- **Recommended per-point loop**: click **Track** toggle (ensure it reads "Track") → click the
  point on canvas (Point Id updates) → click the toggle again (now reads "Stop") → click into D1
  → clear it → type the rule number → click **Apply** in the dialog. Repeat for each point. Watch
  for the **"Invalid Grade Rule specification"** popup — it means the rule number you typed
  doesn't exist in the assigned table; dismiss with its OK button and fix the value.
- The dialog does not visibly confirm success beyond the absence of an error and the field
  keeping your typed value after Apply — there is no green-check or similar.
- Verification: **Grade tab → All Sizes** (View group), then click the piece — this triggers a
  **"Show Nest All"** tool whose panel prompts "Select piece(s) to display nest." Click the
  piece: if grading was applied correctly, the canvas overlays **nested outline copies in
  cyan/teal**, one per size, fanning out from the base size — this is the definitive visual
  confirmation that per-point rules took effect. If ungraded, only the single base-size outline
  shows.
- After confirming via the nest view, remember to **Save As** the piece again (grading changes,
  like other edits, aren't auto-persisted) before exporting.

## 11. Curve grading (multiple points, each with its own rule) — additional findings

Building on §10, a curved piece (tested with a plain Circle — Create tab → Line group → "Circles"
dropdown → "Center", click center then a second point for radius) with many distinct grade points
surfaced two more critical, non-obvious issues:

- **The "Tracking Information" dialog is a real floating top-level window, not embedded in the
  main app** — `Snapshot` shows it as its own top-level window (title "Tracking Information") with
  its own coordinate space, sitting *on top of* the canvas at a fixed screen position (roughly
  x:764-1060, y:290-660 at default position). **If the piece you're tracking points on is located
  underneath that dialog's rectangle, every "canvas click" you attempt actually lands on the
  dialog's blank background instead of the canvas**, and Point Id / D1 silently never populate —
  with no error, making it look like the whole tool is broken. Always check whether the piece's
  on-screen position overlaps the dialog before assuming clicks aren't registering.
  **Fix**: drag the dialog out of the way first — `Move{loc: <titlebar>}` (plain hover) then
  `Move{loc: <destination>, drag: true}` (Windows-MCP's `Click` tool has no drag; use `Move` with
  `drag:true`, which presses at the current cursor position and releases at the target). Grabbing
  the dialog's titlebar text (e.g. "Tracking Information" label) works as the drag handle.
- Once the dialog is clear of the piece, the same click-canvas → click-D1 → clear
  (End, Shift+Home, Delete) → type → Apply loop from §10c works, but **exactly which point gets
  selected by a given canvas click is not reliably "the point nearest the click"** — on a
  many-point curve, clicks sometimes select a visually distant point (observed jumps like
  clicking near the top of a circle but the tool highlighting/reporting a point near the bottom).
  The `Beg X` / `End Y` / `Dist` readout in the main right-hand panel *does* change to genuinely
  different values on each successful Apply, confirming distinct points are being hit even when
  you can't predict in advance which one — so **don't try to map specific screen coordinates to
  specific intended point IDs**; instead just fire the click→type→Apply sequence once per point you
  need to touch (matching the total count of points you created), watch for the absence of an
  "Invalid Grade Rule specification" popup as your only per-step success signal, and verify the
  aggregate result afterward rather than trusting any single step's target.
- **Best verification available is file size, not the in-app nest view.** The Grade tab's
  "All Sizes" → click piece → OK/Apply ("Show Nest All") panel, which worked immediately for a
  simple rectangle with one rule applied to every point (§10c), did **not** reliably render visible
  nested outlines for a many-point curve with per-point distinct rules in this session (repeated
  attempts showed only the flat base-size outline, no fan of graded copies) — likely a display
  edge case with many low-magnitude, non-uniform per-point deltas rather than a real failure of
  the underlying data. Don't treat a blank nest view as proof grading didn't take.
  **Reliable alternative**: export the piece (DXF and/or ZIP with "Include Grade Rule Table"
  checked) and compare the resulting `<piece>.RUL` file size against known references — an empty/
  default rule table stub is a fixed size (~5.8KB in this environment), a single real rule with
  values across all size-breaks lands far smaller (~476 bytes here), and N applied rules scale
  roughly linearly (~476×N bytes) — e.g. 11 rules produced a ~2.5KB `.RUL`. A `.RUL` size in that
  scaled-up range (not equal to the empty-stub size) is strong evidence the per-point rule
  assignments were actually captured in the export, even when the visual nest check is
  inconclusive.
- Building a large rule table (many rule columns) in the standalone `RuleTable.exe` is fast once
  you know the layout: filling one rule's Number+X+Y auto-spawns the next blank "Rule" column
  immediately to the right, at a fixed ~120px column pitch (Number at column_left+60, X at
  column_left+29, Y at column_left+89, all on the same fixed row y-coordinates for every column) —
  so coordinates for column *i* can be computed directly (`col_left = 195 + (i-1)*120`) rather than
  re-locating each field visually, confirmed accurate through at least 11 columns without any
  reflow/scrolling surprises.

## 12. General automation hygiene learned this session

- **Screenshot after almost every click** — this app's panel content, button positions, and even
  which tool is "active" are not reliably inferable from the previous state; several actions
  silently no-op (e.g. typing into a non-live field) with no error, so the only way to know
  something worked is to look.
- When a `Screenshot`/`Click` call returns a classifier timeout error, simply retry the same call
  — it is a transient tool-availability issue, not a signal that the action was unsafe.
- If the PDS window unexpectedly shows unrelated content (another app, a different desktop state)
  after a `switch`, don't assume something broke — this host machine has many other windows and
  can experience focus-stealing; re-issue `App{mode:"switch", name:"Pattern Design"}` (or
  `RuleTable`) and re-screenshot before continuing. Never interact with unrelated windows that
  happen to surface this way.
- Multiple PDS `Work Area 1 - Pattern Design` windows can be open simultaneously (e.g. one
  leftover from an earlier launch) — check `Get-Process`/window titles if pieces you expect to
  see aren't on screen; you may be looking at the wrong instance's blank canvas.
- For any task requiring an exported file at a specific path, **pre-create the destination folder
  with `mkdir -p` before opening PDS's Save/Export dialog**, and **verify the resulting file(s)
  on disk with `ls`/`Get-ChildItem` afterward** rather than trusting the in-app "success" dialogs
  alone (they confirm the *operation* completed, not that the file landed exactly where/how you
  expected, especially given the folder-rename gotcha in §5).

## 13. Round-2 addenda (2026-09-07, Claude Code session)

Observed on the same machine/build while producing the `CAP-*` captures. Where these
contradict §§2-12, trust this section.

- **File menu is a plain dropdown** here (not a full-screen backstage): Save As at
  (54,262), Open at (48,128), Export at (50,672) after clicking File at (34,43).
- **Export dialog accepts a full path in the File name box** — type
  `D:\...\FOLDER\NAME` (no extension) and click Save; no folder navigation, no
  "New folder" rename problem. PDS appends `.DXF` itself; if you type `NAME.dxf` you
  get `NAME.dxf.DXF` and the rule file becomes `NAME.RUL.DXF`. The dialog remembers
  the last "Save as type" (ASTM at (281,472), ZIP at (281,536) in the opened list at
  (281,451)).
- Export ZIP dialogs land at fixed spots: Export Summary OK (911,825) →
  Compatibility warning OK (1161,624) → Process Completed OK (985,605). The ASTM
  "Export Results" window close button is at (1281,19) but the window can lag the
  screenshot by a second or two — check the window list before assuming it failed.
  The panel's Cancel button moves between y=629 and y=705 depending on the tool.
- **Rectangle hover readout**: width is in the X column of the Beg row and height
  (negative, downward) in the Y column of the End row. Canvas zoom is not fixed:
  6.66 px/cm at the start of this session, ~4.5 px/cm after an Open re-zoomed the
  view — always re-measure from a known piece.
- **Point/Drill**: the click places a pending mark; click **OK** in the panel to commit
  (leaving via Cancel is almost certainly how TASK4 lost its drill point).
- **Define Seam**: the tool re-opens with the *previous* Seam Type radio selected —
  click Manual-Even/Uneven explicitly. Manual-Uneven is per *point*: click a corner,
  type the amount, **OK** (Apply is disabled); the tool loops back to "Select
  point(s)". A final OK with nothing selected ends the tool and keeps the seam. A
  corner value sets the allowance at the end of the segment that ends at that
  corner; the next segment starts at 0 unless its own end corner is set.
- **File → Open** puts the piece in the icon strip above the canvas; click the icon,
  the piece rides on the cursor centred on it, click the canvas to drop. Dropping can
  re-zoom the whole view to fit every piece — re-map positions afterwards. Opening a
  piece that is already in the icon menu shows "already exist in the icon menu" and
  does nothing; drag the existing icon. Untick "Open Separate Work Areas" or it opens
  a new work area. **Hover a piece to read its name in the status bar** before acting
  on it — the wrong piece got the first uneven seam this way.
- **Delete Piece from Work Area** (toolbar (752,189)): click the piece, no confirmation.
- **Assign Rule Table**: exactly as §10b; the status-bar size changing to the table's
  base size confirms it. `Include Grade Rule Table` in the ZIP Export Summary stayed
  greyed out even with a custom table assigned — the DXF export's `.RUL` is what
  carries the table.
- **RuleTable.exe**: rows come from the Next Size Breaks list starting at the smallest
  size — breaks `10,12,14,16,18` give "2-10, 10-12, …" (5 rows, no 8-10 row, which is
  why TASK5's `.RUL` has a zero step at 8→10); breaks `4,6,8,10,12,14,16,18` give the
  eight rows 2-4 … 16-18. Grid cells: **double-click, then type without `clear`** —
  Windows-MCP `Type` with `clear:true` opens the "Go To" dialog and every keystroke
  lands there. Number cell (255,188), X (225,y) Y (285,y), rows y = 263 + 19·i;
  column 2 at x+120. Save via toolbar (112,69) / Save As (135,69).
- **Tracking Information (Rule Number) — corrected**: all fields are disabled until a
  point is tracked. A canvas click fills Point Id (which corner you get is not
  reliably the one you clicked) and flips the toggle label to **"Stop"**; while it
  reads "Stop" the D1 field ignores typing. Press the toggle (label → "Track"): typing
  now works, but the displayed Point Id may change — **read it before typing**. Clear
  D1 (End, Shift+Home, Delete) — it keeps the previous point's value. Apply, then
  repeat. **Never type into the Point Id box**: it renumbers the point ("Point number
  is not unique") and corrupts the piece; if that happens, delete the piece from the
  work area and re-open the saved copy.
- **Split line gives no positive confirmation.** The panel's message ("Select point to
  split line.") is identical before and after every click, and a click that lands
  slightly off the line can silently no-op with nothing else changing on screen either.
  Both failure modes look the same to a screenshot taken too late: **screenshot
  immediately after every Split click and count the new corner marker before clicking
  again.** Retrying a click that "seemed to do nothing" is the likely way to end up
  with duplicate near-coincident split points and a piece with more sides than intended
  (round 2: three retried clicks on one edge silently produced three real splits,
  yielding an 8-sided piece where a pentagon/hexagon was intended). If a piece's point
  count looks wrong after the fact, delete it from the work area (Modify→Piece
  Actions→Delete Piece from Work Area, click the piece) and rebuild rather than trying
  to prune the extra points.
