# Independent final verification

Verified production candidate **64c6368b3d8a335e12a8b20bb4c39d4b9576f856** in a separate detached worktree. I independently read #964 and its comment, #967 (no comments), PR #968, applicable `CLAUDE.md`, and the integrated changes. Historical PR validation was treated as a hypothesis. The original PR incorrectly used `Closes #967` despite documented remaining acceptance work; this bounded slice must use `Refs #967` and list that work.

**Result: 53 actual CLI commands passed their asserted outcomes**, including actual written-board checks with KiCad 10.0.0 / bundled Python 3.11.5. Exact argv, expected results, effective parameters, native measurements and identities are in [final-verifier.json](final-verifier.json). Successful exits alone were not the acceptance test.

## What was established

- Frozen published candidate: at explicit copper .25 / edge .55 mm, no-op remains allowed as `no_worse:true`, reports `legal:false`, and identifies exactly Y1.2/Y1.3 at gap .50 mm / shortfall .05 mm each. Physical off-outline and unrelated copper-conflict counts stay zero. Independent DRC on the emitted board reports exactly those two edge findings at .25/.55/0.
- Published positive control, .55 boundary, .60 gap, 90-degree pose and direct model-authored 33-degree pose remain accepted. Native effective pad polygons on written outputs measure the expected gaps; the 33-degree example has .645511 mm minimum Y1 gap. Matching independent DRC is clean.
- .50-to-.52 mm improving dirty placement remains allowed and unclean. An increased shortfall at unchanged finding count refuses. In-place coordinated introduction of edge defects refuses atomically, preserving the board and brief. Direct multi-part writes, near/snap, strict mode and dry-run retain their respective behaviors.
- Explicit edge-only changes affect the edge grade while physical containment and copper conflict requirements/counts stay unchanged. No-project fallback and project-derived .55 mm are reported and measured consistently. The project output retains the project declaration.
- Every core emitted board preserves all 17 fixed serialized footprint blocks and other board text; applicable brief/project/custom-rule siblings and the starting baseline retain their identities. Native output checks establish geometry separately from these preservation assertions.
- Fresh optimize(max-passes=0), all-locked seed repair, reconstruct(classify) and assembly(with original baseline) calls retain the two inherited findings. Written optimize/seed/reconstruct outputs independently retain .50 mm gaps and fail explicit-floor DRC with the expected two .05 mm findings. Their existing scoped completion/buildable indicators do not certify edge cleanliness.
- Ordinary live-parser esp_prog geometry retains complete coverage. A native-written rectangle whose side is subdivided remains complete in text/live parsers and is accepted by an actual strict CLI write; native output gap remains .60 mm.

## Discrepancies discovered and resolved

The fresh audit found four additional overclaims in prior PR head `9df83aafcbf187dd8fe607f9c01863ad43f57673`. Each used a copy of an existing repository/public board.

| Controlled input | Native/declared fact | Previous edge result | Final result |
|---|---|---|---|
| Y1 2x1 mm pad, chamfer .05, roundrect ratio .25, 33 degrees, (130,104.04) | Native gap .523258 mm | Approximate .591853 mm, complete, no finding | Chamfer approximation disclosed by both parsers; coverage incomplete |
| Same pad, front oval / back rectangle padstack | Native B.Cu gap .496026 mm | Approximate .687680 mm, complete, no finding | Per-layer padstack approximation disclosed by both parsers; coverage incomplete |
| Extra open Edge.Cuts line at Y105.1 inside existing rectangle | .20 mm from Y1 copper; malformed/open geometry | Existing rectangle ring hid extra edge; complete | All source segments examined; incomplete outline coverage |
| Sibling `.kicad_dru` requires edge .75 mm | Canonical `DesignRules` resolves .75 | Scalar .55, complete, legal | Named rule and .75 declaration in `rules_unmeasured`; scalar .55 remains distinct |

All four final counterexamples were exercised through actual no-op writes and strict refusals. Ordinary no-worse progress remains available with `legal:false`; strict mode refuses. Written no-ops retain geometry and declarations, allowing equivalent numeric/angle formatting. Native-controlled variants are geometric test inputs, not approved mechanical redesigns.

The new shared parser field records approximation reasons; it does not alter copper geometry or remove declaration siblings. The edge grader consumes those reasons, verifies all source rectangle segments, and names unconsumed edge rules. Integrated production and test changes received independent review. No unresolved discrepancy remains within the exercised bounded scope.

## Reproduction commands and limits

The committed repository regression paths reproduce the new geometry/rule controls:

```powershell
$py = 'C:/Program Files/KiCad/10.0/bin/python.exe'
& $py -X utf8 tests/test_967_edge_floor.py
& $py -X utf8 tests/gui_parity/test_967_pad_geometry_coverage.py
```

The JSON retains all actual actor/DRC argv; `$PUBLIC_ARMS` identifies the immutable published pilot artifacts. Source and baseline hashes are separate from project and brief identities. Full local stdout/stderr and verifier scripts remain in the isolated verifier worktree; the JSON records the asserted numerical results rather than treating logs as a complete authorship ledger.

Exact general outlines/custom/chamfer/padstack geometry and conditional/local custom edge-rule evaluation remain unmeasured. Independent DRC still has different fallback, project-floor, fabrication and severity policies; these checks match explicit .25/.55/0 where the policies agree. This is a bounded #967/#964 slice, not completion of either issue. There was no full native KiCad DRC, full repository suite, body/height certification, routed connectivity validation, or model/instruction comparison by this verifier. Alternate engine tests establish parameter forwarding and output reporting for the specified paths, not optimization quality or every search candidate.

Verifier harness corrections were not counted as passes: missing required seed intent, nested reconstruct summary selection, and equivalent serialized pose formatting were corrected before completed runs. Windows PowerShell also wrapped benign KiCad image-handler stderr as `NativeCommandError`; direct child return codes and assertions in the evidence establish actual command outcomes.

Final documentation-only revision identity must be checked after integration of this evidence; the production candidate above is the behavior-tested revision.
