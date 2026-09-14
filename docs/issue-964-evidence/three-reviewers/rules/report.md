# Independent rules and consumer review of PR 968

**Final production revision verified: `ad156f2a2cc1b6f58eafc25abfeb0a6c31a811d4`.** This reviewer independently reproduced the rule failures on `58c3689f1248a7d582ba695d0ccde66c73ebaa64`, reviewed the complete integrated production/test diff, and verified the final candidate through **28 actual CLI commands and four direct API refusal checks**. All asserted final outcomes passed. The before evidence demonstrates false certifications even though the former regression file passed.

The isolated worktree was `C:/Users/rob/Documents/prive/git/KRT-968-review-rules`. I read issue 964 and all comments, issue 967 (no comments), PR 968, applicable CLAUDE.md instructions, all changed production paths and new tests. This review made no GitHub writes and changed no production files or original fixtures.

## Reproduction and acceptance evidence

Public fixture: tracked `kicad_files/esp_prog.kicad_pcb`, SHA256 `165302e6a4f7aacdd64b3174df27ed8ddb19fd5f1f7effadd8d92205e25a120e`. The harness copies the board, places the documented four-part oscillator arrangement, and locks the other 17 footprint blocks. The bad arrangement has Y1 at `(124.7,103.2,270)` and a .50-mm copper gap; the nearby control is Y1 at `(124.7,103.1,270)`, giving .60 mm. Those geometry variants are controlled test inputs, not changes to original fixtures or approved mechanical requirements. All other poses and Edge.Cuts remain fixed. Copper clearance is explicitly .25 mm throughout. Declared project/rule variants are kept separate from scalar CLI edge values.

The primary 18-row matrix is in `rules-before.json` and `rules-final.json`, with exact argv, return codes, full emitted summaries, per-case input hashes, native output gaps and preservation results. `rules-supplemental.json` records ten additional CLI commands and the four direct API checks. Each row's input board is its genuine no-worse baseline; no later candidate is substituted as that baseline. The tracked source identity above remains unchanged.

| Case | Before | Final expected and verified behavior |
|---|---|---|
| .50 gap, explicit edge .55 | Strict exit 4, no write, two .05 shortfalls | Same; findings specifically Y1.2 and Y1.3 |
| .50 gap, explicit edge .50 | Strict exit 0, legal and complete | Same; native written gap .50 |
| Explicit zero edge floor on .60 control | Strict exit 0, legal and complete | Same; zero remains a supported finite request |
| Explicit NaN edge floor | Strict exit 0, output written, `legal:true`, `required_mm:NaN`, complete, no findings | Exit 2, actionable finite/nonnegative refusal, no output |
| Explicit negative -1 edge floor | Strict exit 0, legal and complete | Exit 2, same input-validation refusal, no output |
| Explicit positive infinity | Strict exit 4 with infinite requirement propagated | Exit 2 before grading/promotion, no output |
| Project NaN or -1, CLI edge omitted | Scalar silently falls back to .55; strict fails on .50 gap but reports complete coverage | Scalar .55 remains distinct from invalid source declaration; project requirement appears in `rules_unmeasured`, coverage incomplete, strict exit 4 |
| Project positive infinity, CLI edge omitted | Infinite requirement reaches grade, strict exit 4 | Exit 2 finite/nonnegative refusal, no output |
| Well-formed unconditional/conditional .75 edge rule | Strict exit 4, custom rule unmeasured | Same; rule name and declared .75 retained separately from scalar .55 |
| Copper-only .25 custom rule | Strict exit 0, legal and complete | Same; native .60 gap, custom sibling retained |
| Comment or quoted name containing parentheses | Copper-only control accepted | Same; comments/quoted text are not treated as physical parentheses |
| Missing final parenthesis, extra parenthesis, unterminated quote | Strict write falsely reports legal and complete, missing rules empty | Strict exit 4, no output, unreadable rule specification explicitly unmeasured |
| Balanced wrapper around valid top-level forms | Strict write falsely reports legal and complete | Strict exit 4; unsupported top-level structure unmeasured |
| Valid quoted rule name `")"` | Legacy parser loses quote identity and drops edge rule; strict write falsely legal | Strict exit 4, conservatively unmeasured because legacy parser cannot preserve this container; no claim that the rule itself is invalid |

Five additional ordinary no-worse writes cover valid .75 rules, truncated rules, wrapped forms, the quoted `")"` name, and invalid project NaN with explicit finite .55. All exit 0, write outputs, and report `no_worse:true`, `legal:false`, incomplete coverage and named missing checks. Their paired in-place strict calls each exit 4 without changing the input board or requirement siblings. This establishes that incomplete specifications do not turn ordinary placement progress into an unconditional ban, and strict refusal stays atomic on these paths.

The direct shared edge grader rejects NaN, positive/negative infinity and -1 with the finite/nonnegative reason. No unsupported value is accepted merely because an arithmetic comparison is false.

## Commands and output verification

Using KiCad 10.0.0 bundled Python 3.11.5:

```powershell
$py = 'C:/Program Files/KiCad/10.0/bin/python.exe'
# At original candidate 58c3689f, fresh directory:
& $py -X utf8 review_rules.py review-rules-evidence-expanded
& $py -X utf8 verify_rules_results.py review-rules-evidence-expanded before
# At final candidate ad156f2a, fresh directory:
& $py -X utf8 review_rules.py review-rules-final-ad156f2a
& $py -X utf8 verify_rules_results.py review-rules-final-ad156f2a after
& $py -X utf8 review_rules_supplemental.py
```

The asserted completed results are `PASS before 18 CLI rows`, `PASS after 18 CLI rows`, and `PASS10ordinary/inplaceCLIcases+4directAPIinvalidfloors`. The initial 13-case before run is also retained locally. Every refusal was checked for an emitted reason and no output rather than merely a nonzero exit. Every successful matrix output was reopened with native KiCad and checked for the expected .50/.60 gap from Y1's axis-aligned pad bounds to the unchanged Edge.Cuts centreline Y=105.5 mm. All 18 input hashes stayed unchanged, all successful outputs preserved 17 serialized fixed footprint blocks, and all applicable brief/project/custom-rule siblings matched their input bytes. Supplemental ordinary outputs retained their requirement siblings; strict in-place calls retained both boards and siblings.

Final production/test tree identities:

- `py_placer`: `d27c92cc0ba7f25babde20df7a67c12c89b72655`
- `py_router`: `c1f94185bbe16eced655a6bb047768549031fdb0`
- `tests`: `9ebc308a766723da5d136843e0affbfdeb59dce4`

The repository `tests/test_967_edge_floor.py` passed independently on the original head but missed the newly reproduced cases. The primary agent's broader final regression runs are separate evidence; I do not count their commands in my 28 independent CLI checks.

## Call-site review and limits

All production calls to `grade_pad_legality` were examined. Pose before/after, trial/snap and restored-candidate grading receive the resolved edge value. Seed, optimize and reconstruct retain the edge report with their preexisting scoped completion/exit policies. Diagnosis, floorplan suspect-pair detection and lock advisor consume pad-pair findings; those are not claims of complete edge compliance. Assembly's buildable result is scoped separately. The full integrated patch, including the other reviewers' near-cardinal/unequal-circle corrections and output/snap changes, was inspected; their behavioral verification belongs to their independent reports.

No remaining discrepancy was established within this reviewed bounded scope. The new rule helper checks balanced containers and supported top-level/clause shapes; it is **not** a complete KiCad grammar parser. The quoted `")"` rule-name case is conservatively unmeasured because the existing shared parser loses that token's quote identity. Exact effective custom-rule evaluation, the existing placement/final-DRC policy mismatch, general project grammar validation and complex geometry certification remain outside this slice. No full native board DRC, routed connectivity, placement-quality improvement or exhaustive engine search was measured by this reviewer.

One low-priority provenance limitation remains: `pad_edge_after.rules_unmeasured[].source` points to the temporary candidate sibling, deleted after promotion. The before report names the actual input source and written outputs retain the declaration, so the evidence still binds the declaration through input identity/sibling preservation, but a stable final source field would be clearer.

Harness-only problems were corrected before completed assertions: an indentation error while adding fixed-block checks stopped an expanded attempt before any CLI command; a premature read of final results occurred while the matrix was still running. Neither is counted as a passing refusal. Windows PowerShell also wraps benign native KiCad image-handler stderr as NativeCommandError; the recorded child subprocess return codes, emitted summaries, output checks and subsequent explicit assertion runs establish command outcomes.
