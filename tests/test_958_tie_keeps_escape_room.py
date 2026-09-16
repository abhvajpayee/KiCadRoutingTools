"""#958's equal-length tie-break must not crowd a pad still awaiting an escape.

`smooth_octolinear_chains` phase 2 (#958) accepts a connector of EQUAL length
when it emits strictly fewer legs. Straightening does not ADD copper -- it MOVES
it: a staircase hugs its own corner, and the diagonal that replaces it cuts
across, sweeping through the space the steps left open. When a pad with no
copper of its own sits in that space, the collapse has taken the room its escape
via needs. Both variants are DRC-legal, so `clears()` cannot choose between
them; at equal length the one that leaves a waiting pad alone is the right one.

MEASURED on ft2232h_jtag, `+1V8` under U4's 0.5mm-pitch BGA -- 3.8728mm either
way:

    3 legs   (129.000,103.500)-(128.400,102.900)
             (128.400,102.900)-(125.800,102.900)
             (125.800,102.900)-(125.500,102.600)
    2 legs   (129.000,103.500)-(128.100,102.600)
             (128.100,102.600)-(125.500,102.600)

/OSCI's bare ball U4.2 sits at (127.75,101.33). The horizontal run drops from
y=102.900 to y=102.600 -- from 1.57mm to 1.27mm of that pad, inside the 1.5mm
the #666 dogbone searches for a via site. The dogbone failed, the rescue failed,
and /OSCI shipped in two pieces: 1/34 nets incomplete where v0.22.0 had 0.

With the guard the board is whole again AND #958 keeps everything: 46 spans on
22 nets collapsed either way, -14.03mm of copper either way. Phase 2 simply
takes a different equal-length two-leg variant that descends late
((129.000,103.500)-(126.400,103.500) then down), clear of the pad.

TWO DEAD ENDS ARE RECORDED HERE because each looks right and is not:

  * a pad-CLEARANCE test ("did this get closer to any foreign pad?") does NOT
    catch it. The copper moves into the channel BETWEEN balls, no closer to any
    pad's keep-out. Tried, measured, still lost the net. What matters is the
    room left for pads that have NO copper yet, not clearance to the ones that
    do.
  * a via-WIDTH keep-out (via/2 + clearance + w/2 = 0.5mm here) does not fire
    at 1.27mm. The escape via lands 1.21mm from its pad, so the radius has to be
    the escape SEARCH radius; this file pins that the two agree.
"""
import ast
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py_router'))

FAILS = []


def _room_mm(row):
    """The guard's radius, or None with the row already failed.

    A bare import raises ImportError on a tree without the guard, and an
    ImportError is a BROKEN TEST, not a detected regression -- the two exit the
    same way and only one is evidence. Absence IS the finding, so say so.
    """
    try:
        from pcb_modification import _SMOOTH_ESCAPE_ROOM_MM
        return _SMOOTH_ESCAPE_ROOM_MM
    except ImportError:
        check(row, False,
              'pcb_modification exports no _SMOOTH_ESCAPE_ROOM_MM -- the '
              'equal-length tie-break is not protecting a waiting pad\'s '
              'escape room, because there is no guard to do it')
        return None


def check(name, cond, detail=''):
    print(f"--- {name}")
    if cond:
        print(f"  PASS{': ' + detail if detail else ''}")
    else:
        print(f"  FAIL: {detail}")
        FAILS.append(name)


def _src(name):
    with open(os.path.join(os.path.dirname(__file__), '..', 'py_router', name)) as f:
        return f.read()


def _fn_body(src, fname):
    tree = ast.parse(src)
    lines = src.splitlines()
    for fn in ast.walk(tree):
        if isinstance(fn, ast.FunctionDef) and fn.name == fname:
            return "\n".join(lines[fn.lineno - 1:getattr(fn, 'end_lineno', fn.lineno)])
    return None


def t_the_radius_is_the_escape_search_radius():
    """The smoother's keep-out must equal what the rescue actually searches.

    If net_rescue widens its search and this constant stays put, the guard
    silently stops covering the escapes it exists for -- so pin them together
    rather than pinning a number.
    """
    _SMOOTH_ESCAPE_ROOM_MM = _room_mm('t_the_radius_is_the_escape_search_radius')
    if _SMOOTH_ESCAPE_ROOM_MM is None:
        return
    body = _fn_body(_src('net_rescue.py'), 'rescue_failed_nets') or _src('net_rescue.py')
    radii = [n.value for n in ast.walk(ast.parse(_src('net_rescue.py')))
             if isinstance(n, ast.keyword) and n.arg == 'max_search_radius'
             and isinstance(n.value, ast.Constant)]
    vals = {r.value for r in radii}
    check('t_the_radius_is_the_escape_search_radius',
          bool(vals) and _SMOOTH_ESCAPE_ROOM_MM in vals,
          f'_SMOOTH_ESCAPE_ROOM_MM={_SMOOTH_ESCAPE_ROOM_MM}, '
          f'net_rescue max_search_radius={sorted(vals)}')
    # ...and it must exceed a via keep-out, or it would not have fired at all.
    check('t_a_via_width_keepout_would_not_have_been_enough',
          _SMOOTH_ESCAPE_ROOM_MM > 0.6,
          f'{_SMOOTH_ESCAPE_ROOM_MM}mm > a via keep-out (~0.5mm at the measured '
          f'geometry), where the escape via sat 1.21mm out')


def t_the_measured_geometry_is_decided_correctly():
    """The ft2232h_jtag case, as numbers: reject the low run, keep the high one.

    Exercises the real distance function rather than restating the story.
    """
    from pcb_modification import _pt_seg_dist
    _SMOOTH_ESCAPE_ROOM_MM = _room_mm('t_the_collapse_that_lost_the_net_is_refused')
    if _SMOOTH_ESCAPE_ROOM_MM is None:
        return
    PAD = (127.75, 101.33)                      # /OSCI's bare ball U4.2
    old = [(129.000, 103.500), (128.400, 102.900),
           (125.800, 102.900), (125.500, 102.600)]
    bad = [(129.000, 103.500), (128.100, 102.600), (125.500, 102.600)]
    good = [(129.000, 103.500), (126.400, 103.500), (125.500, 102.600)]

    def room(pts):
        return min(_pt_seg_dist(PAD[0], PAD[1], a[0], a[1], b[0], b[1])
                   for a, b in zip(pts, pts[1:]))

    d_old, d_bad, d_good = room(old), room(bad), room(good)
    check('t_the_collapse_that_lost_the_net_is_refused',
          d_bad < d_old and d_bad < _SMOOTH_ESCAPE_ROOM_MM,
          f'{d_bad:.3f}mm vs {d_old:.3f}mm before, inside the '
          f'{_SMOOTH_ESCAPE_ROOM_MM}mm escape radius')
    check('t_the_equal_length_alternative_is_allowed',
          not (d_good < d_old - 1e-9),
          f'the late-descent variant keeps {d_good:.3f}mm (>= {d_old:.3f}mm), '
          f'so #958 still gets its two-leg collapse')
    # Non-vacuity: both candidates really are the same length as the original,
    # or this is not the tie-break's decision to make.
    import math

    def length(pts):
        return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
    check('t_all_three_variants_are_the_same_length',
          abs(length(bad) - length(old)) < 1e-9 and abs(length(good) - length(old)) < 1e-9,
          f'{length(old):.4f}mm for all three -- a TIE, which is the only case '
          f'this guard touches')


def t_a_pad_clearance_test_would_not_have_caught_it():
    """The dead end, pinned: the losing move is no closer to any FOREIGN pad.

    Recorded as a row so nobody re-derives the cheaper-looking guard, ships it,
    and measures nothing.
    """
    from pcb_modification import _pt_seg_dist
    # The nearest BGA balls flanking the corridor, from ft2232h_jtag's U4 grid
    # (0.5mm pitch, boundary X[118.58,130.43] Y[101.08,112.92]).
    flanking = [(128.08, 103.08), (128.58, 103.08), (127.58, 103.08)]
    old = [(129.000, 103.500), (128.400, 102.900),
           (125.800, 102.900), (125.500, 102.600)]
    bad = [(129.000, 103.500), (128.100, 102.600), (125.500, 102.600)]

    def room(pts, pad):
        return min(_pt_seg_dist(pad[0], pad[1], a[0], a[1], b[0], b[1])
                   for a, b in zip(pts, pts[1:]))
    worse = [p for p in flanking if room(bad, p) < room(old, p) - 1e-9]
    check('t_a_pad_clearance_test_would_not_have_caught_it',
          not worse,
          'the losing collapse moves AWAY from the flanking balls '
          + ', '.join(f'{room(old, p):.3f}->{room(bad, p):.3f}mm' for p in flanking))


def t_the_guard_is_wired_and_scoped_to_ties():
    """Wiring, off the AST: inside the smoother, on the tie branch only."""
    body = _fn_body(_src('pcb_modification.py'), 'smooth_octolinear_chains')
    check('t_the_guard_is_in_the_smoother',
          body is not None and '_escape_room_lost' in body
          and '_escape_pads' in body,
          'smooth_octolinear_chains builds the waiting-pad set and consults it')
    if not body:
        return
    seg = body[body.find('_is_tie and _escape_pads'):][:200]
    check('t_the_guard_only_touches_ties',
          '_is_tie and _escape_pads' in body,
          'gated on _is_tie, so strictly-shorter collapses are untouched')
    # Cost: it must sit AFTER the memoised clearance test, not before it.
    i_clears = body.find('if not all(clears_m(')
    i_guard = body.find('_is_tie and _escape_pads')
    check('t_the_guard_runs_after_the_memoised_clearance_test',
          0 < i_clears < i_guard,
          'clears_m (memoised, warm from phase 1) rejects first; the distance '
          'query only sees candidates that are otherwise accepted')
    check('t_the_waiting_pads_are_indexed_not_scanned',
          '_escape_xs' in body and 'bisect' in body,
          'queried through a sorted x-band -- O(waiting pads) per candidate was '
          '104 pads on ottercast_audio')


def main():
    t_the_radius_is_the_escape_search_radius()
    t_the_measured_geometry_is_decided_correctly()
    t_a_pad_clearance_test_would_not_have_caught_it()
    t_the_guard_is_wired_and_scoped_to_ties()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURE(S): {', '.join(FAILS)}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == '__main__':
    sys.exit(main())
