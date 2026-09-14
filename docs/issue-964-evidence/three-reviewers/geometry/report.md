# Independent geometry bug review of PR #968

Reviewer worktree: `KRT-968-review-geometry`, detached original publication
`58c3689f1248a7d582ba695d0ccde66c73ebaa64`, compared with main `5a7fbcb6`.
Read issue #964 and comments, #967, applicable `CLAUDE.md`, full production
diff and earlier evidence. Findings were established independently, including
actual CLI writes and native KiCad 10.0.0 readback.

## Original publication: two new false-clean geometry bugs

1. **Near-cardinal rotations (high priority).** The shared parser folds pad
   angles within 1 degree of cardinal axes into axis-aligned dimensions and
   `rect_rotation=0`. The new edge grader uses those approximate dimensions
   but certifies analytic coverage. On a copy of public `esp_prog`, a 2 x 1 mm
   rectangular pad at absolute angle 0.5 degrees and center (124,104.45) has
   native gap 0.541293 mm to the Y=105.5 Edge.Cuts centerline. Strict placement
   writes it with `legal:true`, `complete:true`, reported gap 0.55 mm, against
   explicit edge requirement 0.55 mm. The written board has the same native
   shortfall. Seven tested near-cardinal angles falsely pass; true 0/90 degree
   positive controls pass at 0.55; 1.0001 degrees correctly refuses before the
   fix because it lies beyond the parser's snap tolerance.
2. **Nonuniform circular pad dimensions (medium priority, unusual input).**
   KiCad's native API accepts, serializes and reloads a circular pad with size
   (2,1) mm. Native `GetEffectiveShape(F_Cu).Format()` gives
   `SHAPE_CIRCLE(VECTOR2I(124000000,104450000),1000000)`, hence exact gap
   105.5 - 104.45 - 1 = 0.05 mm. The new grader instead models it as a 2 x 1
   oval and reports complete 0.55 mm. Actual strict CLI output is falsely
   clean. The native polygon approximation reports 0.054815 mm: this is its
   inscribed approximation error, not the exact gap. Ordinary 2 x 1 oval and
   roundrect controls pass correctly. This is a controlled native-authored
   pad variant; it is not claimed to occur in the unmodified public fixture
   or be creatable by every KiCad GUI dialog.

The source fixture SHA256 is
`165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`.
Its original bytes were never edited. There is no source project sibling;
all experiments explicitly request copper 0.25 and edge 0.55 mm. No brief,
baseline or rule waiver was introduced to obtain the result. The four public
placement poses are reconstructed on copies; one copied pad is modified with
native KiCad to isolate the shape/rotation condition. Mechanics outside this
controlled input construction are not authorized to change.

## Replay and evidence

From this worktree:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 review_geometry.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 extra_geometry.py
```

`review-geometry-evidence/results.json` contains revision, source/input/output
hashes, all ten exact CLI argv vectors, direct child exit codes, complete
summaries, text/live grades, native original/written pad gaps and independent
analytic gap calculations. `extra-results.json` has three additional CLI
shape controls and locked/unlocked internal Edge.Cuts controls, both correctly
incomplete. Raw CLI stdout/stderr files are retained for the ten angle cases.
The existing `tests/test_967_edge_floor.py` passed on the original publication
despite these newly demonstrated bugs.

Both scripts support `--expect-fixed` and write to the separate
`review-geometry-evidence-final` directory. Their assertions require corrected
strict refusal reasons, accepted positive controls, native/text/live boundary
agreement and retained no-worse ordinary writes with `legal:false` for inherited
angle defects. The unequal circle must either be accurately rejected or named
unmeasured; it cannot claim a clean complete result.

## Limits

This geometry lane does not establish whole-board native DRC cleanliness,
routed connectivity, placement quality, exact unsupported curved/custom geometry,
or broader #964 acceptance. Other reviewers own operations and rule coverage.
The original published existing chamfer/padstack/open-edge/custom-rule limitations
were checked against the code but are not claimed as newly discovered bugs.

## Final integrated verification

**PASS on `ad156f2a2cc1b6f58eafc25abfeb0a6c31a811d4`.** Independently inspected
the complete integrated diff from `58c3689f` to this candidate, including
numeric/rule validation, near-search and writer rollback changes. Operations
and rules reviewers own the independent behavior proofs for those other
channels; this report's conclusions are confined to geometry and actual outputs.

```powershell
git checkout --detach ad156f2a2cc1b6f58eafc25abfeb0a6c31a811d4
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 review_geometry.py --expect-fixed
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 extra_geometry.py --expect-fixed
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 final_identity.py
```

All script assertions passed; the geometry scripts exercised **21 actual CLI
calls**, comprising ten strict angle cases, eight ordinary no-worse angle cases
and three strict native-shape cases. They also ran both text and live/native
parser edge graders and checked actual output boards using native KiCad.

| Angle / shape | Native gap (mm) | Original strict verdict | Final strict verdict |
|---|---:|---|---|
| Rectangle 0 / 90 degrees | .550000 | clean | clean |
| Rectangle .5 / 179.5 / 180.5 / 359.5 degrees | .541293 | falsely clean at .55 | refuses measured shortfall |
| Rectangle 1 degree | .532624 | falsely clean at .55 | refuses measured shortfall |
| Rectangle 89.5 / 90.5 degrees | .545675 | falsely clean at .55 | refuses measured shortfall |
| Rectangle 1.0001 degrees | .532622 | refuses shortfall | refuses shortfall |
| Circle (2,1) mm | .050000 exact native shape | falsely clean at .55 | refuses explicitly incomplete geometry |
| Oval / roundrect (2,1) mm | .550000 | clean | clean |

The eight violating angle cases all remain writable through ordinary no-worse
placement, with `no_worse:true` and `legal:false`. Their written native gap
remains the correctly reported gap, so the fix permits continued repair without
claiming the inherited defect disappeared. Strict failures assert the intended
edge refusal reason and absence of output, not just nonzero return status.
Both parsers agree with native rectangle extrema within the declared 1 nm
tolerance. Unequal circles remain partially measured; their approximate numeric
gap is not promoted to a native geometry claim. Locked/unlocked internal edge
segments remain correctly incomplete controls.

`review-geometry-evidence-final/results.json`, `extra-results.json` and
`identity.json` preserve exact argv, results, final revision and input/output
identities. All **12 emitted boards** received independent native readback of
every footprint/pad position, angle, layer, lock, size and shape. Every such
mechanical signature is unchanged from its graded input. Board text outside
equivalent serialization of Y1's requested pose is identical.

A deliberately stronger byte-equality check initially failed because the writer
normalizes Y1 `(at 124.7 103.15 -90)` to `(at 124.700000 103.150000 270)`.
Inspection and native readback established this as numeric formatting of the
same pose. The final identity check permits only that exact equivalent line
change; it does not erase or broadly normalize unrelated changes.

Final checked trees:

- `py_placer`: `d27c92cc0ba7f25babde20df7a67c12c89b72655`
- `py_router`: `c1f94185bbe16eced655a6bb047768549031fdb0`
- `tests`: `9ebc308a766723da5d136843e0affbfdeb59dce4`

Original fixture SHA256 remains the identity above. The before evidence remains
unchanged in its separate directory. There are no unresolved geometry findings
within these exercised cases. Full native DRC, routed outcomes, unsupported
exact geometry and the broader issue acceptance remain outside this review's
behavioral evidence. A later documentation-only publication must retain the
checked production/test tree identities before citing these results.
