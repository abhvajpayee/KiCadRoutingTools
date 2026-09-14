# PR #968 independent operations bug review

Initial reviewed revision: `58c3689f1248a7d582ba695d0ccde66c73ebaa64`; production patch tree matches `64c6368b3d8a335e12a8b20bb4c39d4b9576f856`. Isolated worktree `KRT-968-review-operations`. Read issue #964 body and all comments, #967 body/comments, applicable CLAUDE.md and complete production diff. No production edits or original fixture edits.

Environment: Windows, KiCad 10.0 bundled Python 3.11.5. All following probes use copies of existing `kicad_files/esp_prog.kicad_pcb`, repository SHA256 `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`. Four publicly documented oscillator poses are set in controlled copies; the 17 other footprints are locked. Explicit copper .25 / edge .55 mm. These are engineering-instrument tests, not PCB quality or model performance trials.

## Concrete bugs independently found

1. **Written output requirements can differ from the strict grade.** `probe.py` places the .60-mm Y1 gap positive control, then invokes a real strict-legal CLI no-op at an output pathname carrying an existing `.kicad_dru` .75-mm edge rule absent from the input. Exit 0 reports legal/complete, but the written output retains the old .75 rule; reading that actual board reports incomplete custom-rule coverage. Native KiCad `GetEffectivePolygon(F_Cu)` reports the expected .60-mm minimum Y1 gap. The staged candidate's declarations and output's declarations are different. Existing promotion behavior, materially contradicting final-output coverage claims. Exact argv, input identity, native measurements and both grade documents: `artifacts/bugs.json` (stale_dru).

2. **Late write failure overwrites requirement siblings while claiming nothing changed.** `readonly.py` uses a real existing output board with Windows readonly file attribute, and different input/output brief contents. Promotion replaces the brief then fails replacing the readonly board. Exit 2 says `Nothing was written` / previous output untouched; board hash stays the same but output brief hash changes to input brief. This is a real Windows filesystem failure without mocked functions. `probe.py` independently demonstrates the same ordering bug with an existing directory at the board pathname. Exact argv, hashes and refusal: `artifacts/readonly_bug.json` and `artifacts/bugs.json` (partial_promotion).

3. **Strict near search selects an unclean candidate and then refuses despite a clean nearby candidate.** Starting from the .50-gap board, `--strict-legal --radius .5 --snap-step .05 --snap-tries 24 set Y1 --near 124.7 103.21 --rot 270` exits 4 after choosing `[124.8,103.16,270]`, no_worse true, legal false, edge shortfall .02 mm. Direct strict `[124.7,103.15,270]` only .06 mm from request exits 0 and is clean. Search acceptance only checks relative no-worse, ignoring requested strict cleanliness; strict unclean but no-worse requests also do not enter snap search. Exact argv/results: `artifacts/near_strict.json`.

Run using `C:/Program Files/KiCad/10.0/bin/python.exe -X utf8 review_operations/{probe,readonly,near_strict}.py` (individual script filename, not shell brace expansion). Raw stdout/stderr are retained alongside JSON. Each bug probe asserted its claimed observation; a first readonly harness BOM SyntaxError was corrected before measurement and was not counted as evidence.

## Initial focused regressions

`tests/test_967_edge_floor.py`: 8 tests PASS at initial head (26.289s). This includes bad/positive/edge boundaries, rotated support, unsupported geometry, same-input atomic multi-op refusal, near writes, project fallback and requirement siblings. The two promotion failures were found despite this green suite. `tests/test_892_place_pose.py`: 133 assertions passed, 0 failed (full log `test_892.log`).

Final candidate verification and disposition of findings will be added after primary integration. No claim of clean whole-board native DRC, routed connectivity, body/height coverage, full repository-suite coverage or completed #964/#967 acceptance is made by this review.


## Final independent verification: all three operations findings resolved

Final behavior-tested production revision: **`ad156f2a2cc1b6f58eafc25abfeb0a6c31a811d4`**, checked out detached in this review worktree. Independently read the entire `58c3689f..ad156f2a` production/test diff, including shared geometry/rule changes and candidate/promotion call sites. Final production file hashes and fixture identity are recorded in `operations-evidence.json` → `final_identity`.

**12 actual placement CLI runs plus 4 independent `check_drc.py` runs passed their asserted outcomes.** Ten ordinary CLI runs came from `final_check.py`; two explicit force/failure controls came from `force_check.py`. The final `tests/test_892_place_pose.py` regression also passed all 133 assertions. No successful exit alone was treated as a behavior assertion.

| Finding / control | Initial head `58c3689f` | Final `ad156f2a` |
|---|---|---|
| Output-only custom edge rule .75 mm, source control gap .60 at scalar .55 | Strict CLI wrote legal/complete despite destination declaration; native gap .60 | Exit 2 before publication; destination rule bytes preserved. Separately verified output-only project and brief refusal. |
| Readonly existing board, different prior brief | Exit 2 claimed untouched while overwriting brief | Real Windows readonly board failure exits 2 with `output_state:unchanged`, no rollback errors; original board plus all three project/rule/brief byte identities preserved. |
| Strict near from .50-gap board, request Y103.21 | Chose Y103.16 / .54 gap then refused; direct Y103.15 / .55 gap was accepted | Writes chosen Y103.06 / native .64 gap, .15-mm move from request, final DRC 0 at .25/.55/margin0. |
| Strict near at unchanged dirty Y103.2 | Initial code did not enter search for strict-only failure | Writes Y103.05 / native .65 gap, final DRC 0. |
| Improving dirty move Y103.2 → Y103.18 | Existing intended no-worse operation | Still accepted: `no_worse:true, legal:false`; native .52 gap; exactly two independent pad-edge DRC findings (.03 mm each). |
| Atomic direct multi pose at Y103.15 | Supported operation | Accepted at native .55 boundary; independent DRC 0. All 17 fixed serialized footprint blocks preserved. |
| In-place direct multi request introduces .50 gap | Relevant refusal control | Exit 4 for `pad_edge` worsening; board and brief hashes unchanged. |
| Destination-only `.kicad_prl` | UI-local state, no engineering requirement | Strict positive no-op remains accepted. |

All four placement outputs in the geometry matrix preserve the original 17 fixed serialized footprint blocks and the source project, custom copper-rule and brief hashes. The source board fixture SHA256 remains `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`. Input, baseline fixture, output and requirement-sibling identities are recorded separately in JSON; rules were not weakened and the baseline was not substituted. All written positions are independently inspected using native KiCad effective F.Cu polygons, and snapped coordinates are checked against parsed written footprints. Explicit DRC parameters are copper .25 / edge .55 / clearance margin0, with pad-edge checking enabled.

### Force and restoration failure disclosure

A forced edge-worsening move followed by stale destination-brief refusal exits 2 and preserves both the original pad-edge finding and the publication failure in its JSON. It does not publish the board or change the destination brief. This is a test of the existing explicit force option, not a workaround used in any positive-control acceptance result.

A separate CLI entry-point run uses a **real Windows readonly-board replacement failure**, plus a controlled injected denial of the subsequent brief-backup restoration rename. It exits 2 with `output_state:partial`, identifies the one failed rollback path, retains a backup whose bytes match the original brief, and prints `REFUSED, output partially changed` without claiming nothing was written. The unchanged old board and changed brief are asserted on disk. Only this restoration denial is injected; the normal rollback control is wholly real filesystem behavior. This verifies truthful disclosure and recovery evidence when rollback itself cannot complete, not crash-proof multi-file transactions.

### Evidence and exact commands

`operations-evidence.json` contains the complete original failure observations, final argv/exit/JSON summaries, four independent DRC documents, native gaps, input/sibling identities, production file hashes and force/partial-failure evidence. Original raw before/after boards, logs and verifier scripts remain in this isolated worktree. Local reproduction commands:

```powershell
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 review_operations/final_check.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 review_operations/force_check.py
& 'C:/Program Files/KiCad/10.0/bin/python.exe' -X utf8 tests/test_892_place_pose.py
```

The first script creates a unique `final_<id>` directory; the force script was pinned to the recorded `final_0cd2a41d` artifacts for this run. Public repository regressions covering the fixes are `tests/test_967_edge_floor.py` and `tests/test_892_place_pose.py`; the report does not imply the transient scripts are installed tools.

**No unresolved operations discrepancy remains in this exercised scope.** This review does not certify arbitrary-outline/custom-pad edge geometry, conditional custom edge-rule evaluation, whole-board native DRC, bodies/heights, routed connectivity, full repository suite, model performance, or acceptance of every optimization candidate. The reported independent DRC is the repository `check_drc.py` at explicit matching parameters; native KiCad was used separately for actual copper geometry. Existing broader #964/#967 work remains bounded and open. Documentation-only publication-head identity review remains necessary after integrating this evidence.
