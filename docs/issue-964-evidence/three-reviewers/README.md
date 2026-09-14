# Three independent bug reviews of PR #968

Both issues are linked without premature closure: **Refs #964; Refs #967**.
The issue timelines also link back to this bounded PR:
[964](https://github.com/drandyhaas/KiCadRoutingTools/issues/964#issuecomment-5661095826),
[967](https://github.com/drandyhaas/KiCadRoutingTools/issues/967#issuecomment-5661096030).

Initial reviewed publication: `58c3689f1248a7d582ba695d0ccde66c73ebaa64`.
Corrected production candidate: `ad156f2a2cc1b6f58eafc25abfeb0a6c31a811d4`.
The final PR head adds evidence only; the PR description records its identity
after all three reviewers compare its production/test trees to this candidate.

| Tree | Verified candidate identity |
|---|---|
| `py_placer` | `d27c92cc0ba7f25babde20df7a67c12c89b72655` |
| `py_router` | `c1f94185bbe16eced655a6bb047768549031fdb0` |
| `py_tools` | `1bae2317936d27c73f64bd903d0f32cb58e62853` |
| `tests` | `9ebc308a766723da5d136843e0affbfdeb59dce4` |

Each reviewer used an isolated worktree and independently reproduced bugs,
derived expectations, checked the integrated patch, and ran real placement CLI
commands with native KiCad output readbacks. The primary agent owns all six
implementation/test file changes. No skill or model instructions changed.

| Independent lane | Final behavioral evidence |
|---|---|
| [Geometry report](geometry/report.md) | 21 placement CLI calls; native readback of all 12 emitted boards; [angles](geometry/final-angles.json), [shapes](geometry/final-shapes.json), [mechanical identities](geometry/final-identities.json) |
| [Operations report](operations/report.md) | 12 placement CLI calls, 4 matching independent DRC commands, 133 pose regression assertions; [before/after evidence](operations/evidence.json) |
| [Rules report](rules/report.md) | 28 placement CLI calls and 4 direct API invalid-floor checks; [final matrix](rules/final.json), [ordinary/in-place controls](rules/supplemental.json) |

These are **61 placement CLI calls plus 4 independent DRC commands**, separate
from the primary regression run. All asserted outcomes passed on the corrected
candidate. Before records are [geometry angles](geometry/before-angles.json),
[geometry shapes](geometry/before-shapes.json), [rules](rules/before.json), and
the combined operations evidence above. Reports retain the original local
artifact names; this index maps them to the archived JSON. Command evidence
records include exact executed argv, summaries and fixture identities. Transient scripts,
raw logs and generated boards named in reports remain in the reviewer
worktrees; the committed regression scripts reproduce the guarded behaviors.

## Findings and dispositions

| Reviewer | Before on `58c3689f` | After on `ad156f2a` |
|---|---|---|
| Geometry | A 2 x 1 mm pad at 0.5 degrees reports .55 mm and strict legal; native gap is .541293 mm | Recovers exact residual tilt from the retained pad angle; strict refuses the shortfall. Ordinary inherited dirty poses still write with `no_worse:true, legal:false` |
| Geometry | Native unequal-axis circle has exact .05 mm edge gap but reports .55 mm, complete | Names unsupported native geometry; complete is false and strict refuses. Ordinary oval/roundrect and cardinal controls remain accepted |
| Rules | Explicit NaN and negative floors certify strict legality; invalid project values silently fall back or propagate infinity | Explicit/resolved nonfinite or negative edge floors refuse. Invalid source project declarations remain named unmeasured, even when resolution falls back |
| Rules | Truncated, extra-close, wrapped-root and unterminated-string custom rules can disappear; legacy parsing also loses the valid quoted name `")"` | Container validation discloses unreadable/unsupported coverage and strict refuses; regular copper-only rules, quoted text/comments, finite zero and positive controls remain accepted |
| Operations | Output-only `.kicad_dru` declarations can join a board graded without them | Refuses output-only project/rule/brief requirements before mutation. Existing local `.kicad_prl` UI state remains supported |
| Operations | A real Windows read-only output board fails after replacing its brief, while claiming nothing changed | Backs up previous files and restores completed replacements on failure. If restoration also fails, reports partial mutation and retains recovery backups |
| Operations | Strict near search chooses an unclean no-worse candidate, or skips search for an unchanged dirty request, despite a nearby clean pose | Strict search requires clean candidates and searches dirty requests; direct and atomic coordinated poses remain supported |

The new shared `validate_dru_structure` helper guards placement coverage;
legacy `parse_dru` behavior for other consumers is unchanged. This is not a
complete KiCad grammar parser or custom-rule evaluator. The exact edge grader
recovers near-cardinal tilt locally; shared routing broad-phase tolerance and
model-authored rotations are unchanged. Promotion now has recovery for ordinary
filesystem errors, not a claim of crash-safe, concurrent multi-file transactions.

## Fixture and measurement contract

All three reviewers use copies of tracked `kicad_files/esp_prog.kicad_pcb`,
SHA256 `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`.
The source has no project sibling. The four public oscillator poses are
reconstructed in copies; geometry cases additionally modify one copied pad
using native KiCad. Project/custom-rule/brief cases explicitly create separate
declarations. Effective copper clearance is .25 mm and edge clearance .55 mm
unless a recorded rule-boundary case explicitly varies it. Matching independent
DRC checks use zero clearance margin and pad-edge checking.

Geometry is measured against Edge.Cuts centreline Y=105.5 mm. For the tilted
2 x 1 mm rectangle, the high-Y extent is
`abs(sin(angle))*1 + abs(cos(angle))*.5` mm. Native polygons corroborate the
analytic result to 1 nm for the tested rectangular angles. The unequal-circle
effective native shape has radius 1 mm, giving .05 mm exact gap; its inscribed
polygon's .054815 mm result is an approximation, not the exact boundary.

Board hashes identify inputs/outputs; they are not geometry or quality proofs.
Operations/rules checks preserve the 17 fixed serialized footprint blocks and
applicable declaration siblings. Geometry checks compare all native footprint
and pad poses, rotations, layers, locks, dimensions and shapes for every emitted
board. The equivalent Y1 angle serialization `-90` to `270` is separately
accounted for; other board text is unchanged. Original public fixture and
baseline evidence remain in the [earlier reproduction](../reproduction.md).

## Regression checks on the corrected candidate

Run from the repository root with KiCad 10.0.0 / bundled Python 3.11.5:

```powershell
$py = 'C:/Program Files/KiCad/10.0/bin/python.exe'
& $py -X utf8 tests/run_all.py 967 937_off_outline 628_milled 697_placement 761_legality 900_class 411_placement_siblings run27_seed_gate 892 placement_pad_legality rotated_footprint_frame design_rules --jobs 3
& $py -X utf8 tests/gui_parity/test_967_pad_geometry_coverage.py
& $py -X utf8 tests/gui_parity/test_manifest_plan_parity.py
& $py -X utf8 tests/gui_parity/test_cli_postpass_coverage.py
```

The runner passed 14 files, zero failures/timeouts, in 108.4 seconds. The optional
untracked perturbed-tigard subtest remains absent, despite the runner reporting
no file-level skips. The focused edge file passed all 11 tests, including actual
CLI boundaries, strict search, real Windows read-only failure and injected
rollback failure assertions. Native text/live parity passed chamfer/padstack,
ten-angle and unequal-circle cases. Both routing parity gates passed.

`C:/Python313/python.exe -X utf8 tests/test_718_static_test_hygiene.py` passed all
nine checks and 1108 mutation anchors. An isolated Python 3.13 / NumPy 2.5.3
environment ran `tests/run_doc_examples.py`: 32 runnable blocks passed, 78
signature/fragments skipped. These are focused results, not a full-suite claim.

## Remaining work and limits

- Unify placement/final-DRC effective-rule policy, including defaults and
  explicit overrides below project floors. This PR does not change the baseline
  or weaken project/custom requirements to make a board pass.
- Evaluate custom edge-rule conditions/layers/severity/precedence and exact
  complex/custom/chamfer/padstack/curved geometry. Unsupported checks are named;
  no-worse writes do not certify those requirements or a clean final board.
- The legacy parser cannot faithfully represent a quoted rule name consisting
  solely of a parenthesis. Such valid input conservatively remains incomplete.
  Rule-source paths in staged after-reports can point to temporary paths; the
  before-report input path and preserved output siblings retain provenance.
- General crash recovery, concurrent writers, and failure recovery on every
  operating system/filesystem are not established by the promotion checks.
- Other #964 channels, whole-board native DRC, routed connectivity/quality,
  body/height certification and model-performance comparisons remain outside
  this bounded slice. Neither issue is closed and the PR is not merged.
