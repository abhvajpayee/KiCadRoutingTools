"""Half a pair is not a protected pair (#521/#906).

#521 protects coupled-pair copper because a later chain step cannot reproduce
it -- P/N geometry, gap, polarity. That reasoning needs BOTH members: if one
failed or ended disconnected, the survivor's copper is ordinary single-ended
routing the next step can redo, and freezing it only takes a rip candidate away
from whatever still has to get through.

`protection_candidates` decided per NET, off each member's own result dict. Its
docstring asserts the hybrid is "admitted only when both members connect
terminal to terminal" -- but that is a property of the CONSTRUCTOR, never
checked here, and the `is_diff_pair` path never looked at the partner at all.
So a pair reported 'coupled' whose MEMBER AUDIT then finds disconnected pads
(ecp5_mini's /PA26 and /PH15 ship exactly that shape) had its survivor
protected.

The decision is now per PAIR, using `_member_connected` -- the SAME predicate
the post-route cleanup scope uses to decide a pair's copper is safe to sweep, so
the two agree about what "this pair landed" means.

SCOPE, measured: this is a strict NARROWING of protection and it is inert where
both members land. On picodvi -- the board that raised the question, where
protecting /uC_DVI_CK boxes /uC_DVI_D1+ out entirely -- all three protected
pairs are fully connected, so the protected set is IDENTICAL with and without
this check and the board still grades 1/37 incomplete. That board's loss is a
consequence of protecting a pair that DID land, which is #906 working as
designed; it is not this bug.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'py_router'))

FAILS = []


def _candidates(row, results, pcb, pairs):
    """Call with the pair list, or fail the row with the reason.

    A build without the pair argument raises TypeError, which is a BROKEN TEST,
    not a detected regression -- they exit the same way and only one is
    evidence. Absence of the parameter IS the finding.
    """
    from route_diff import protection_candidates
    try:
        return protection_candidates(results, pcb, pairs=pairs)
    except TypeError:
        check(row, False,
              'protection_candidates takes no `pairs` argument -- protection is '
              'still decided per NET, so half a pair can be protected on the '
              'survivor\'s own result')
        return None


def check(name, cond, detail=''):
    print(f"--- {name}")
    if cond:
        print(f"  PASS{': ' + detail if detail else ''}")
    else:
        print(f"  FAIL: {detail}")
        FAILS.append(name)


class _Pair:
    def __init__(self, p, n):
        self.p_net_id, self.n_net_id = p, n


def _pcb(connected_nets):
    """Two nets, each with two pads; `connected_nets` get a segment joining
    theirs, the others do not -- so _member_connected can tell them apart."""
    from kicad_parser import PCBData, BoardInfo, Net, Pad, Segment
    pads, segs = {}, []
    for nid, (x0, name) in enumerate([(0.0, '/D+'), (5.0, '/D-')], start=1):
        a = Pad(pad_number='1', net_id=nid, net_name=name, global_x=x0 + 1.0,
                global_y=1.0, local_x=0.0, local_y=0.0, size_x=0.5, size_y=0.5,
                shape='circle', layers=['F.Cu'], drill=0, pad_type='smd',
                component_ref=f'U{nid}')
        b = Pad(pad_number='2', net_id=nid, net_name=name, global_x=x0 + 3.0,
                global_y=1.0, local_x=0.0, local_y=0.0, size_x=0.5, size_y=0.5,
                shape='circle', layers=['F.Cu'], drill=0, pad_type='smd',
                component_ref=f'U{nid}')
        pads[nid] = [a, b]
        if nid in connected_nets:
            segs.append(Segment(start_x=a.global_x, start_y=a.global_y,
                                end_x=b.global_x, end_y=b.global_y,
                                width=0.2, layer='F.Cu', net_id=nid))
    return PCBData(
        board_info=BoardInfo(layers={0: 'F.Cu'}, copper_layers=['F.Cu'],
                             board_bounds=(0.0, 0.0, 20.0, 10.0), stackup=[]),
        nets={1: Net(net_id=1, name='/D+', pads=pads[1]),
              2: Net(net_id=2, name='/D-', pads=pads[2])},
        footprints={}, vias=[], segments=segs, pads_by_net=pads)


COUPLED = {'is_diff_pair': True, 'new_segments': [1], 'new_vias': []}


def t_a_landed_pair_is_protected():
    """Non-vacuity: the rule must still protect what #521 is FOR."""
    got = _candidates('t_a_landed_pair_is_protected',
                      {1: COUPLED, 2: COUPLED}, _pcb({1, 2}),
                      [('/D', _Pair(1, 2))])
    if got is None:
        return
    check('t_a_landed_pair_is_protected',
          got == {'/D+': 'diff-pair', '/D-': 'diff-pair'},
          f'both members protected: {sorted(got)}')


def t_a_pair_with_a_disconnected_member_is_not_protected():
    """THE regression this closes: 'coupled' but the audit finds open pads."""
    got = _candidates('t_a_pair_with_a_disconnected_member_is_not_protected',
                      {1: COUPLED, 2: COUPLED}, _pcb({1}),
                      [('/D', _Pair(1, 2))])
    if got is None:
        return
    check('t_a_pair_with_a_disconnected_member_is_not_protected',
          got == {},
          f'nothing protected when /D- never landed (got {sorted(got)})')


def t_a_pair_whose_partner_failed_is_not_protected():
    """The other half: the partner's result says failed."""
    got = _candidates('t_a_pair_whose_partner_failed_is_not_protected',
                      {1: COUPLED, 2: dict(COUPLED, failed=True)},
                      _pcb({1, 2}), [('/D', _Pair(1, 2))])
    if got is None:
        return
    check('t_a_pair_whose_partner_failed_is_not_protected',
          got == {}, f'nothing protected (got {sorted(got)})')
    # ...and a partner with no result at all.
    got2 = _candidates('t_a_pair_whose_partner_has_no_result_is_not_protected',
                       {1: COUPLED}, _pcb({1, 2}), [('/D', _Pair(1, 2))])
    if got2 is None:
        return
    check('t_a_pair_whose_partner_has_no_result_is_not_protected',
          got2 == {}, f'nothing protected (got {sorted(got2)})')


def t_the_survivor_alone_would_have_been_protected_before():
    """The change detector, as behaviour rather than as source shape.

    Without the pair list the function keeps its old per-net decision, so this
    row shows exactly what the pair check now prevents -- and it is also the
    compatibility contract for a caller that has no pair list.
    """
    from route_diff import protection_candidates
    legacy = protection_candidates({1: COUPLED, 2: COUPLED}, _pcb({1}))
    check('t_the_survivor_alone_would_have_been_protected_before',
          legacy == {'/D+': 'diff-pair', '/D-': 'diff-pair'},
          'per-net decision protects both even though /D- never landed -- '
          'which is what the pair check overrides')


def t_the_caller_passes_the_pair_list():
    """Wiring: route_diff must actually hand the pairs in, or this is inert."""
    import ast
    src = open(os.path.join(os.path.dirname(__file__), '..',
                            'py_router', 'route_diff.py')).read()
    tree = ast.parse(src)
    ok = False
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == 'protection_candidates'):
            if any(kw.arg == 'pairs' for kw in node.keywords):
                ok = True
    check('t_the_caller_passes_the_pair_list', ok,
          'batch_route_diff_pairs calls protection_candidates(pairs=...)')


def t_it_uses_the_cleanup_scope_predicate():
    """Detection and repair must agree on 'this pair landed'."""
    import ast
    src = open(os.path.join(os.path.dirname(__file__), '..',
                            'py_router', 'route_diff.py')).read()
    lines = src.splitlines()
    body = None
    for fn in ast.walk(ast.parse(src)):
        if isinstance(fn, ast.FunctionDef) and fn.name == 'protection_candidates':
            body = "\n".join(lines[fn.lineno - 1:getattr(fn, 'end_lineno', fn.lineno)])
    check('t_it_uses_the_cleanup_scope_predicate',
          body is not None and '_member_connected' in body,
          'protection_candidates consults _member_connected, the same predicate '
          'the post-route cleanup scope uses')


def main():
    t_a_landed_pair_is_protected()
    t_a_pair_with_a_disconnected_member_is_not_protected()
    t_a_pair_whose_partner_failed_is_not_protected()
    t_the_survivor_alone_would_have_been_protected_before()
    t_the_caller_passes_the_pair_list()
    t_it_uses_the_cleanup_scope_predicate()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURE(S): {', '.join(FAILS)}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == '__main__':
    sys.exit(main())
