"""#958's equal-length tie-break does not rearrange copper in a fine-pitch field.

`smooth_octolinear_chains` phase 2 (#958) accepts a connector of EQUAL length
when it emits strictly fewer legs. Straightening does not ADD copper -- it MOVES
it: a staircase hugs its own corner, and the diagonal that replaces it cuts
across, sweeping through the space the steps left open. Between 0.5mm-pitch pads
that space is the escape corridor for a pad that still needs one, and BOTH
variants are DRC-legal, so `clears()` cannot choose between them. A tie buys one
fewer leg; it must not buy it there.

MEASURED on ft2232h_jtag, `+1V8` under U4 -- 3.8728mm either way, 3 legs vs 2:

    3 legs   (129.000,103.500)-(128.400,102.900)
             (128.400,102.900)-(125.800,102.900)
             (125.800,102.900)-(125.500,102.600)
    2 legs   (129.000,103.500)-(128.100,102.600)
             (128.100,102.600)-(125.500,102.600)

The run drops from y=102.900 to y=102.600 -- 0.15mm from where /OSCI's #666
bare-ball escape drops its via. The dogbone failed, the rescue failed, and /OSCI
shipped in two pieces.

WHY PITCH AND NOT THE PACKAGE NAME. `find_components_by_type('BGA')` is the
obvious reuse and is the WRONG set: ft2232h_jtag's U4 -- the part this fix
exists for -- is `Package_QFP:LQFP-64_10x10mm_P0.5mm`, so `detect_package_type`
calls it QFP and the BGA filter returns nothing. (Its log line "BGA Grid
Analysis for U4" is the FANOUT's grid analyser, which runs on any candidate and
finds a pitch in a QFP's peripheral rows.) What makes the space a corridor is
the pitch, so a 0.5mm QFP, a 0.65mm BGA and a 0.2mm QFN all qualify. The region
is built from `detect_bga_pitch` + `get_footprint_bounds`, the two helpers
`auto_detect_bga_exclusion_zones` is itself made of.

WHY A STATIC REGION AND NOT "PADS THAT LACK COPPER". That set changes on every
route pass, so a guard keyed on it fires differently each lap. An earlier cut
did exactly that and was REVERTED (549f16b5): it fixed ft2232h_jtag and took
ottercast_audio from 2 to 4 nets incomplete across its five-pass chain. A
package does not move between passes.

    board          v0.22.0   HEAD   waiting-pad cut   THIS
    ft2232h_jtag      0/34   1/34              0/34   0/34
    ottercast        0/158  2/158             4/158  2/158

One improved, one unchanged, none regressed. The cost is real and recorded:
ft2232h_jtag's smoothing goes 46 -> 39 spans (pre-#958 was 27), so #958 still
nets +12 spans there.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py_router'))

FAILS = []


def check(name, cond, detail=''):
    print(f"--- {name}")
    if cond:
        print(f"  PASS{': ' + detail if detail else ''}")
    else:
        print(f"  FAIL: {detail}")
        FAILS.append(name)


def _threshold(row):
    try:
        from pcb_modification import _SMOOTH_DENSE_PITCH_MM
        return _SMOOTH_DENSE_PITCH_MM
    except ImportError:
        check(row, False,
              'pcb_modification exports no _SMOOTH_DENSE_PITCH_MM -- the '
              'equal-length tie-break is not protecting fine-pitch fields, '
              'because there is no guard to do it')
        return None


def _fn_body(fname):
    import ast
    src = open(os.path.join(os.path.dirname(__file__), '..',
                            'py_router', 'pcb_modification.py')).read()
    lines = src.splitlines()
    for fn in ast.walk(ast.parse(src)):
        if isinstance(fn, ast.FunctionDef) and fn.name == fname:
            return "\n".join(lines[fn.lineno - 1:getattr(fn, 'end_lineno', fn.lineno)])
    return None


def t_the_threshold_admits_the_packages_that_matter():
    """0.5mm QFP, 0.65mm BGA and 0.2mm QFN all count; a coarse part does not."""
    thr = _threshold('t_the_threshold_admits_the_packages_that_matter')
    if thr is None:
        return
    measured = {'ft2232h U4 (QFP)': 0.5, 'ottercast U1 (BGA)': 0.65,
                'ottercast U3 (QFN)': 0.2, 'ottercast J3 (QFN)': 0.31}
    missed = {k: v for k, v in measured.items() if v > thr}
    check('t_the_threshold_admits_the_packages_that_matter',
          not missed,
          f'threshold {thr}mm admits {sorted(measured.values())}')
    check('t_the_threshold_is_not_unbounded',
          thr <= 1.0,
          f'{thr}mm keeps ordinary coarse-pitch parts out of the guard')


def t_the_region_comes_from_the_boards_own_helpers():
    """Reuse, not a re-derivation: pitch and bounds are the shared helpers."""
    body = _fn_body('smooth_octolinear_chains')
    check('t_the_region_comes_from_the_boards_own_helpers',
          body is not None and 'detect_bga_pitch' in body
          and 'get_footprint_bounds' in body,
          'built from detect_bga_pitch + get_footprint_bounds')
    # ...and NOT from the BGA-only component filter, which misses U4. Asked of
    # the AST: the name appears in a comment explaining exactly this, so a
    # substring test would read that comment as the defect it warns about.
    import ast
    src = open(os.path.join(os.path.dirname(__file__), '..',
                            'py_router', 'pcb_modification.py')).read()
    called = set()
    for fn in ast.walk(ast.parse(src)):
        if isinstance(fn, ast.FunctionDef) and fn.name == 'smooth_octolinear_chains':
            for node in ast.walk(fn):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    called.add(node.func.id)
    check('t_it_does_not_key_on_the_bga_only_filter',
          'find_components_by_type' not in called,
          "not keyed on find_components_by_type('BGA') -- ft2232h_jtag's U4 is "
          "a QFP and would be missed")
    check('t_it_calls_the_pitch_and_bounds_helpers',
          {'detect_bga_pitch', 'get_footprint_bounds'} <= called,
          f'calls {sorted({"detect_bga_pitch", "get_footprint_bounds"} & called)}')


def t_the_measured_geometry_is_decided_correctly():
    """The ft2232h_jtag case as numbers: same length, and the loser goes low."""
    old = [(129.000, 103.500), (128.400, 102.900),
           (125.800, 102.900), (125.500, 102.600)]
    bad = [(129.000, 103.500), (128.100, 102.600), (125.500, 102.600)]

    def length(pts):
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    check('t_the_variants_are_the_same_length',
          abs(length(bad) - length(old)) < 1e-9,
          f'{length(old):.4f}mm both -- a TIE, the only case this guard touches')
    # U4's pad-bounds box, measured: X[118.05,130.95] Y[100.55,113.45].
    bx0, by0, bx1, by1 = 118.05, 100.55, 130.95, 113.45

    def inside(pts):
        return any(min(a[0], b[0]) <= bx1 and max(a[0], b[0]) >= bx0
                   and min(a[1], b[1]) <= by1 and max(a[1], b[1]) >= by0
                   for a, b in zip(pts, pts[1:]))
    check('t_the_losing_collapse_lies_in_the_field',
          inside(bad), 'the 2-leg variant crosses U4\'s pad field, so the '
                       'guard refuses it')


def t_the_guard_is_scoped_to_ties_and_cheap():
    """Wiring and cost: ties only, after the memoised clearance test."""
    body = _fn_body('smooth_octolinear_chains')
    if body is None:
        check('t_the_guard_is_scoped_to_ties_and_cheap', False,
              'smooth_octolinear_chains not found')
        return
    check('t_the_guard_only_touches_ties',
          '_is_tie and _dense_boxes' in body,
          'gated on _is_tie, so strictly-shorter collapses are untouched '
          'inside the field as well')
    # COST: the guard must be a bbox test, not a geometry query. That is what
    # makes its position in the ladder irrelevant -- unlike the reverted
    # waiting-pad cut, whose per-candidate distance query had to sit behind the
    # memoised clears_m to stay off the hot path.
    import ast
    src = open(os.path.join(os.path.dirname(__file__), '..',
                            'py_router', 'pcb_modification.py')).read()
    guard_fn = None
    for fn in ast.walk(ast.parse(src)):
        if isinstance(fn, ast.FunctionDef) and fn.name == '_in_dense_field':
            guard_fn = fn
    names = set()
    if guard_fn is not None:
        for node in ast.walk(guard_fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                names.add(node.func.id)
    check('t_the_query_does_no_geometry',
          guard_fn is not None and not (names - {'min', 'max'}),
          f'_in_dense_field calls only {sorted(names)} -- bbox compares, so it '
          f'is cheap wherever it sits in the ladder')
    # And the region itself is built ONCE per call, not per candidate: its
    # construction must live outside the collapse loop.
    outer = [fn for fn in ast.walk(ast.parse(src))
             if isinstance(fn, ast.FunctionDef) and fn.name == 'collapse']
    inner = "\n".join(
        src.splitlines()[outer[0].lineno - 1:outer[0].end_lineno]) if outer else ''
    check('t_the_region_is_built_once',
          'get_footprint_bounds' not in inner,
          'the box list is built outside the greedy collapse loop')


def main():
    t_the_threshold_admits_the_packages_that_matter()
    t_the_region_comes_from_the_boards_own_helpers()
    t_the_measured_geometry_is_decided_correctly()
    t_the_guard_is_scoped_to_ties_and_cheap()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURE(S): {', '.join(FAILS)}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == '__main__':
    sys.exit(main())
