# Independent reproduction and acceptance probe for #964 / #967

This is fresh evidence from 2026-09-14, independently measured in `C:/Users/rob/Documents/prive/git/KRT-964-reproduction`. It is not a rephrasing of PR #968's previous verification. Production was not edited. The public fixtures were restored from immutable evidence commit `e65e33da58ecbefb346534f2cad36b1803bfb55b`; original repository boards and pilot fixtures were never mutated.

Archived command/native records: [current main](reproduction-main.json),
[original PR](reproduction-original-pr.json). Paths below retain the verifier's
original local run names; the [follow-up index](README.md) identifies the final
candidate verification and the scope of the published evidence.

## Commands and identities

Interpreter: `C:/Program Files/KiCad/10.0/bin/python.exe -X utf8` (native pcbnew installed).

Original reproduction: detached main `5a7fbcb6ee4deebd1d9ec1d5bd094d8681f502f3`, command `... evidence_reproduction/reproduce.py`. Exact 12 subprocess argument vectors, exits, summaries and native readbacks: `before/results.json`; per-command stdout/stderr sit beside it.

Existing-PR acceptance: detached `9df83aafcbf187dd8fe607f9c01863ad43f57673`, command `... evidence_reproduction/acceptance.py --output evidence_reproduction/existing_pr_verified`. Exact 23 subprocess argument vectors, exits, summaries, native readbacks and production-tree IDs: `existing_pr_verified/results.json`. This revision is the PRE-UPDATE PR; final integrated revision verification remains the final verifier's responsibility.

- Repository esp_prog SHA256: `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`.
- Public initial board/baseline: `662b58af79fbd02a05cd5806f2d502c0081de8e32496611742dd5060a0cd41a2`.
- Public affected frozen board, also obtained byte-for-byte by replay: `509e1f95e7c492410eb913d6ceb4e3458d52a74b135392ae37b4c2ecea3a8325`.
- Positive-control final: `ae4194a6879bd986d1c769e0c8f35ae0da8047efe7877b72256a7405f7260e7c`.
- Preserved public brief: `72c0ca2c020cc6a73e7eeb169c433ac7d51bff0818d74c18fdf9397ce54bbf67`.
- Original public inputs have no `.kicad_pro`; the explicit project control declares Default copper .25 and min copper edge .60 in a newly created sibling of an isolated canonical copy.

## Measured before/after

On main, all four commands in the published current-skill RETURN.md succeeded, including in-place coordinated final placement. The final SHA equals the published frozen candidate. A no-op `set Y1 124.7 103.2 --rot 270 --clearance .25 --board-edge-clearance .55` also returned `legal:true`. Independent `check_drc.py BOARD --clearance .25 --board-edge-clearance .55 --clearance-margin 0 --check-pad-edge --json REPORT` returned two pad-board-edge findings, each .05 mm, exit 1. Thus the original failure is reproduced as behavior, not merely source inspection.

Native KiCad gives straight Edge.Cuts centerline bounds `[114,91,145.75,105.5]`. Y1.2 and the lower of the two pads both numbered Y1.3 have maximum copper Y=105.0, hence .500 mm gap. They are inside the outline. Native KiCad sees zero tracks and zero zones. The positive-control frozen board returns zero DRC findings under the identical explicit .25/.55/0 flags.

On existing PR `9df83aaf`, the same affected no-op returns `no_worse:true`, `legal:false`, two .05 edge shortfalls and zero physical off-outline copper. The positive-control no-op remains `legal:true`, and output DRC remains zero. Rule-only sweeps .50/.55/.60 yield edge counts 0/2/2 while copper-pair conflict count and physical off-outline count remain zero.

Y1 Y=103.18 yields native gap .52, accepted improving inherited damage with `no_worse:true`, `legal:false`; explicit output DRC reports two .03 shortfalls. Y=103.15 yields native .55 and Y=103.10 yields .60; both accepted clean and output DRC zero. Implementation tolerance is 1e-6 mm (1 nm); the geometric equality controls pass. This probe does not independently test the ±1 nm tolerance transition.

A coordinated Y1/C2 in-place request reintroducing .50 gap from clean .60 is refused specifically for increasing `pad_edge_conflicts`; board and brief hashes remain unchanged. `--near 124.7 103.2 --rot 270 --radius .5 --snap-step .05 --snap-tries 24` succeeds with `snapped` populated, native written output gap at least .55, and zero output DRC findings.

An authored arbitrary-angle pose `set Y1 133.7 102.7 --rot 33` succeeds. Native output pad bounds measure minimum .645511 mm; the analytic edge report agrees within 2e-6 mm and output DRC is zero. Preliminary proposed x=138 and x=130 poses were correctly refused for distinct copper-pair collisions. Those failed controls were not presented as an edge defect; retained logs identify the physical collisions. Native geometry chose the final valid control.

All ten inspected written outputs preserve every one of the 17 fixed footprint poses/layers/locks, indexed by UUID to retain duplicated/blank references, outline bounds, zero tracks/zones, and brief SHA. Native assertion scope is those facts, not all serialized footprint graphics; the final verifier should additionally inspect exact fixed blocks and complete mechanical drawing identity.

## Discrepancy and acceptance scope

The project .60 control resolves/measures .60 in placement and explicit .60 DRC, with project bytes preserved. A separate explicit-lower control is intentionally retained as a discrepancy: placement `.50` overrides the project, says `legal:true`; DRC given `.50` clamps to `.60`, exits 1 and reports two .10 shortfalls. Matching flags therefore does not establish matching effective rules. These are different existing rule-precedence policies, not a newly introduced regression. A PR must not claim a completed common-rule contract without addressing or explicitly retaining this work under `Refs #967`.

Required final acceptance: freshly verify integrated revision, every changed call path, exact fixed blocks/mechanical drawings and sibling/baseline identity; test unsupported and nonrectangular coverage independently; rerun affected checks after changes. No full native KiCad DRC, routing connectivity/quality, body/fabrication certification, performance trial, or full repository test-suite claim follows from this probe. No skill/instruction change was made.
