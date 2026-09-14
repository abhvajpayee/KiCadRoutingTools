# Fresh verification of the placement edge slice of #964 / #967

This updates existing PR #968, based on current upstream main
`5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`. It is a bounded slice: **Refs #964,
Refs #967**, with no automatic closure. No placement strategy or skill changed.
The model can still author direct poses, rotations and coordinated moves.

Production candidate: `64c6368b3d8a335e12a8b20bb4c39d4b9576f856`.
Its `py_placer` tree is `dd3ef33a4a810dd23864e26e373f6057bceaaa1a` and
`py_router` tree is `d90c5c21f80857c6e8d7ef8cbf05b3a8281e296c`.
The [independent final report](final-verifier.md) and
[53-command evidence](final-verifier.json) verify that candidate. The PR
description pins the final documentation-only publication head after an
independent check that its production and test trees match these identities.

## Independent reproduction

The [reproduction verifier's report](reproduction.md) and exact command/native
records for [current main](reproduction-main.json) and the
[original PR head](reproduction-original-pr.json) establish the before/after.
Their local absolute paths identify the isolated runs; substitute your own
scratch directory when replaying the recorded argument vectors. The JSON
contains captured summaries and native readbacks; separate raw stdout files
mentioned by the original report remain local to the verifier worktree.

The immutable public fixtures are at evidence commit
[`e65e33da`](https://github.com/edgehero/KiCadRoutingTools/tree/e65e33da58ecbefb346534f2cad36b1803bfb55b/wk/astra-evidence/pilot/arms).
Original public inputs have no project sibling. Existing briefs were copied
unchanged; explicitly created project/custom-rule controls are separate cases.
Board, baseline, brief and output hashes are recorded as identities, not as
geometry proofs. Native measurements use the Edge.Cuts centreline, not its
stroke-inclusive bounding box.

The original four-command replay reproduces the frozen affected board exactly.
At .25 mm copper / .55 mm edge / zero DRC margin, native Y1 pad gaps are .50 mm:
two .05 mm edge shortfalls despite the original actor's `legal:true`.
The published positive control passes the identical explicit-floor DRC.
The original PR already corrects this scalar-floor failure. Its .52 mm repair
remains accepted with `no_worse:true, legal:false`; .55 and .60 mm outputs are
clean in the measured channels. Native arbitrary-angle output at 33 degrees
also passes. These are tool measurements, not a model performance benchmark.

The final verifier reran **53 actual CLI commands on `64c6368b`**, including
native readbacks, all four added counterexamples, alternate engine output
grades and a subdivided-rectangle strict write. Every asserted outcome passed.
All 17 fixed serialized footprint blocks, other board text, applicable
declaration siblings and the public baseline retain their identities. This
is independent evidence on the integrated implementation, separate from
the reproduction verifier's earlier original-PR checks.

## Discrepancies discovered and changes

The final verifier independently challenged the original PR's coverage claim:

| Case on a copy of esp_prog | Native requirement/geometry | Original PR claim | Follow-up behavior |
|---|---|---|---|
| Chamfered 2 x 1 mm pad at 33 degrees | Gap .523258 mm, below .55 | Simplified roundrect gap .591853 mm, complete | Chamfer approximation named; incomplete |
| Oval front / rectangular back padstack at 33 degrees | Back gap .496026 mm, below .55 | Simplified oval gap .687680 mm, complete | Per-layer approximation named; incomplete |
| Extra open internal Edge.Cuts | .20 mm pad gap to extra segment | Parsed rectangle hides line, complete | All-source-edge proof fails; incomplete |
| `.kicad_dru` edge floor .75 on scalar .55 boundary | Declared .75 remains unevaluated | Legal and complete at .55 | Rule/value/source explicitly unmeasured; incomplete |
| Project .60 plus explicit .50 | Placement uses .50; DRC clamps to .60 | Different effective rules | Existing precedence retained; remaining work |

The parser now carries `Pad.geometry_approximations` through both text and
native-board paths. Only the edge coverage consumer changes behavior; existing
pad shapes, pad-pair checks and placement candidate strategies are preserved.
The new native regression constructs and reloads both pad variants using KiCad
and compares text/live coverage against the native copper polygon.

The rectangular-outline proof checks all extracted source segments, including
open segments the ring builder discards. Subdivided rectangle sides are valid;
gaps, overlaps and internal segments cannot certify complete coverage. Curved
and otherwise unsupported outlines retain sampled findings, explicitly partial.

The scalar edge report keeps requested/resolved .55 separate from the custom
rule's declared .75. It does not invent an effective per-pad rule. Incomplete
coverage makes `legal:false` and strict legality refuses atomically. Ordinary
no-worse operations still progress with incomplete coverage disclosed. They do
not certify compliance with those unmeasured requirements.

## Repeatable regressions

From the candidate checkout on Windows, using KiCad 10.0.0 / Python 3.11.5:

```powershell
$py = 'C:/Program Files/KiCad/10.0/bin/python.exe'
& $py -X utf8 tests/run_all.py 967 937_off_outline 628_milled 697_placement 761_legality 900_class 411_placement_siblings run27_seed_gate 892 placement_pad_legality rotated_footprint_frame --jobs 3
& $py -X utf8 tests/gui_parity/test_967_pad_geometry_coverage.py
& $py -X utf8 tests/gui_parity/test_manifest_plan_parity.py
& $py -X utf8 tests/gui_parity/test_cli_postpass_coverage.py
```

`tests/test_967_edge_floor.py` uses copies of the tracked esp_prog board and
actual CLI output boards. It covers scalar boundaries, tolerance, rotated
support, control, improving dirty moves, atomic refusal, snap, multi-pose,
dry-run, project/fallback resolution, siblings and the new coverage cases.
The numerical tolerance is 1e-6 mm; it is not a fabrication waiver.

Static hygiene runs with Python 3.13 because existing unrelated tests require
its syntax. Documentation examples run in an isolated Python 3.13 environment
with NumPy. Native geometry tests require pcbnew and explicitly skip with code
77 when it is unavailable; a skip is not a pass.

On `64c6368b`, the focused runner reports **13 files passed**, zero failed or
timed out, in 98.4 seconds. This is a file-level result: the optional untracked
perturbed-tigard corroboration inside `test_placement_pad_legality.py` skips
when absent, even though its remaining unit/real-board assertions pass.
The required native test ran and passed both parsers, not skipped. Both
CLI/GUI routing parity gates passed. Python 3.13 static hygiene passed all
nine checks, including 1108 mutation anchors; it also disclosed the unrelated
optional corpus tests whose inputs are absent. Documentation examples passed
32 runnable blocks, with 78 signature/fragments skipped, using NumPy 2.5.3.

## Explicit remaining acceptance work

- Unify placement and final DRC effective-rule contracts, including differing
  no-project defaults and explicit overrides below project floors. Matching
  flags alone currently does not ensure matching effective rules.
- Evaluate custom edge-rule conditions, layers, severity and precedence, and
  verify exact native chamfer/padstack/custom/curved geometry. This slice names
  their missing coverage; it does not certify those requirements.
- #964's other channels: routing-writer requirement siblings, score aggregation
  and baseline coverage, stale withheld-budget recovery, mechanical requirement
  compilation/conflicts, and complete artifact authorship manifests.
- Full native board DRC, routed connectivity/quality, body/height certification,
  full-suite results and model/instruction comparisons are not established by
  these checks. The pilot output boards have zero tracks/zones.

Original fixture files, unrelated user changes, requirement siblings and the
genuine public baseline were preserved. Neither issue is manually closed and
the PR is not merged.
