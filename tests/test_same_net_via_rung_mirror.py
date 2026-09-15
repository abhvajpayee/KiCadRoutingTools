"""A same-net via keep-out must reach the SMALL fab rung too.

`add_same_net_via_clearance` stamps a ring around every existing same-net via
so a new one cannot land on top of it. The ring went into `blocked_vias` only.
A rung-1 search -- the escalated small-via geometry (#568/#530) -- consults
`blocked_vias_small` / the per-net rung maps for dynamic copper, so it never
saw the ring and could place a small via inside it.

The #581 pad keep-out ten lines above already mirrors, with a comment giving
exactly this reasoning ("a rung-1 search consults ONLY blocked_vias_small ...
it drops a small fab-rung via straight into the pad this keep-out exists to
protect"). The via-via ring was simply left out.

MEASURED: mod_bme280 shipped two same-net vias 0.180mm apart -- drill 0.3
beside drill 0.15 -- whose HOLES overlap by 0.045mm against the run's own
0.25mm hole-to-hole rule. A drill overlap is a fab defect, not a clearance
opinion, and no waiver covers it. The ring radius there was
via_size + clearance = 0.65mm, so the site was refused outright at rung 0 and
allowed at rung 1.

WHY IT SURFACED WHEN IT DID, since the mirror has been missing since #568: it
takes a run that places a SHRUNK via near an existing same-net one. #900 (the
pad-override cap no longer contaminating the net classes) made mod_bme280 route
at its real 0.2mm clearance instead of a phantom 0.0508mm, which needs more
vias and pushes the fab tier to escalate -- so the latent hole finally had the
geometry to bite. The trigger was a CORRECTION; the defect is older.
"""
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


def _map_with_ring():
    """A map carrying one same-net via and its keep-out ring, both rungs armed."""
    import numpy as np
    from routing_config import GridRouteConfig, GridCoord
    from kicad_parser import PCBData, Via, BoardInfo
    import obstacle_map as OM

    cfg = GridRouteConfig(layers=['F.Cu', 'B.Cu'])
    cfg.via_size = 0.45
    cfg.clearance = 0.2
    via = Via(x=10.0, y=10.0, size=0.45, drill=0.3,
              layers=['F.Cu', 'B.Cu'], net_id=7)
    pcb = PCBData(
        board_info=BoardInfo(layers={0: 'F.Cu', 2: 'B.Cu'},
                             copper_layers=['F.Cu', 'B.Cu'],
                             board_bounds=(0.0, 0.0, 20.0, 20.0),
                             stackup=[]),
        nets={}, footprints={}, vias=[via], segments=[], pads_by_net={})

    real = OM.GridObstacleMap(2)
    # POPULATE rung 1, the way #530 does when a net has its own via geometry.
    # This is load-bearing for the test, not setup noise: an UNPOPULATED rung
    # falls back to rung 0 ("a smaller via is never legal where the caller
    # hasn't proven it"), so a rung-1 query would answer rung 0's blocked and
    # the check would pass whether or not the ring was ever mirrored. The first
    # version of this test did exactly that and passed on the unfixed tree.
    # One far-away cell is enough to make the rung real without touching the
    # cells under test.
    real.add_blocked_vias_rung_batch(1, np.array([[0, 0]], dtype=np.int32))
    OM.add_same_net_via_clearance(real, pcb, 7, cfg)
    coord = GridCoord(cfg.grid_step)
    return real, coord.to_grid(10.0, 10.0), cfg, coord


def t_the_ring_blocks_the_nominal_rung():
    """Non-vacuity: the keep-out must exist at all before asking about rung 1."""
    real, (gx, gy), cfg, coord = _map_with_ring()
    # 0.18mm away -- the spacing mod_bme280 actually shipped.
    d = max(1, int(round(0.18 / cfg.grid_step)))
    check('t_the_ring_blocks_the_nominal_rung',
          real.is_via_blocked(gx + d, gy),
          f'cell {d} step(s) ({d * cfg.grid_step:.2f}mm) from the via is refused at rung 0')
    far = int(round(1.2 / cfg.grid_step))
    check('t_the_ring_is_not_everything',
          not real.is_via_blocked(gx + far, gy),
          f'a cell {far * cfg.grid_step:.2f}mm away is still free '
          f'(ring radius is via_size + clearance = {cfg.via_size + cfg.clearance}mm)')


def t_the_ring_reaches_the_small_rung():
    """THE regression: an escalated small via must not land inside the ring."""
    real, (gx, gy), cfg, coord = _map_with_ring()
    d = max(1, int(round(0.18 / cfg.grid_step)))
    blocked_small = real.is_via_blocked_rung(gx + d, gy, 1)
    check('t_the_ring_reaches_the_small_rung',
          blocked_small,
          f'a SMALL-rung via {d * cfg.grid_step:.2f}mm from a same-net via is refused')
    # And the far cell stays legal at rung 1 too, or "blocked" could just be
    # rung 1 falling back to a fully blocked map.
    far = int(round(1.2 / cfg.grid_step))
    check('t_the_small_rung_is_not_blanket_blocked',
          not real.is_via_blocked_rung(gx + far, gy, 1),
          'a distant cell is still legal at rung 1')


def main():
    t_the_ring_blocks_the_nominal_rung()
    t_the_ring_reaches_the_small_rung()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURE(S): {', '.join(FAILS)}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == '__main__':
    sys.exit(main())
