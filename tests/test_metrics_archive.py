#!/usr/bin/env python3
"""The reach archive's two invariants, and the page's two disclosures.

OFFLINE BY CONSTRUCTION. Nothing here touches the network: the collector's API
layer is never called, only the pure merge/rollup functions and the renderer,
which read the committed archive. A test that needed GitHub would fail on every
machine without a token and be deleted within a month.

WHY THESE FOUR. Each one is a claim the page makes that a future edit could
quietly invert while the page still renders and still looks plausible:

1. Merging keeps the MAX per date. A part-elapsed day observed by one run must
   not be frozen at its partial value by a later run seeing the same day, and a
   re-run inside the 14-day window must never REDUCE a banked day. Overwrite
   semantics would pass any "the page renders" check and silently lose counts.
2. PCM installs and router-binary downloads are never summed. They are
   different audiences (a PCM user may never touch git), and a single
   "downloads" headline is the obvious, wrong simplification.
3. The page states that uniques are not additive. The card sums daily uniques
   because that is all GitHub gives, and that sum is NOT a count of people --
   if the caveat goes, the number becomes a lie rather than a proxy.
4. A failed endpoint is DISCLOSED. A silently absent series looks exactly like
   a quiet week, which is the failure mode that makes monitoring worthless.
"""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'py_tools'))
sys.path.insert(0, ROOT)

import repo_metrics as M                                      # noqa: E402

FAILS = []


def check(name, cond, detail=''):
    print(f"--- {name}")
    if cond:
        print(f"  PASS{': ' + detail if detail else ''}")
    else:
        print(f"  FAIL: {detail}")
        FAILS.append(name)


def t_merge_keeps_the_max_per_date():
    """A later run seeing a lower count for a banked day must not reduce it."""
    store = {}
    M._merge_daily(store, 'views', [{'timestamp': '2026-09-01T00:00:00Z',
                                     'count': 281, 'uniques': 107}])
    # The same day re-observed LOWER (a partial re-read, or GitHub revising).
    M._merge_daily(store, 'views', [{'timestamp': '2026-09-01T00:00:00Z',
                                     'count': 12, 'uniques': 3}])
    kept = store['views']['2026-09-01']
    check('t_merge_keeps_the_max_per_date',
          kept == {'count': 281, 'uniques': 107},
          f"re-observed low, kept {kept}")

    # ...and a genuine increase IS taken (the negative control: a max that
    # never rises is just as broken, and would pass the assertion above).
    M._merge_daily(store, 'views', [{'timestamp': '2026-09-01T00:00:00Z',
                                     'count': 400, 'uniques': 150}])
    risen = store['views']['2026-09-01']
    check('t_merge_still_takes_a_real_increase',
          risen == {'count': 400, 'uniques': 150}, f"rose to {risen}")


def t_pcm_and_binaries_are_counted_apart():
    """The two populations must not collapse into one 'downloads' number."""
    snap = {'2026-09-15': {'v0.20.4': {
        'published_at': '2026-08-14T00:00:00Z',
        'assets': {'KiCadRoutingTools-0.20.4.zip': 4164,
                   'grid_router-linux-x86_64.so': 145,
                   'grid_router-windows-x86_64.pyd': 62}}}}
    rows, plat, pcm = M._release_rollup(snap)
    ok = (len(rows) == 1 and rows[0]['pcm'] == 4164
          and sum(plat.values()) == 207 and pcm == {'v0.20.4': 4164})
    check('t_pcm_and_binaries_are_counted_apart', ok,
          f"pcm={rows[0]['pcm']}, binaries={sum(plat.values())}")

    # The deltas differ them too, rather than differencing one blended total.
    two = {'2026-09-08': {'v1': {'published_at': '', 'assets': {
               'KiCadRoutingTools-1.zip': 10, 'grid_router-linux-x86_64.so': 5}}},
           '2026-09-15': {'v1': {'published_at': '', 'assets': {
               'KiCadRoutingTools-1.zip': 18, 'grid_router-linux-x86_64.so': 9}}}}
    d = M._weekly_deltas(two)
    check('t_deltas_separate_the_two_populations',
          d == [{'date': '2026-09-15', 'pcm': 8, 'bin': 4}], f"{d}")


def _render_into(tmp, meta):
    """Render with the module's paths redirected at a scratch dir."""
    data, site = M.DATA, M.SITE
    M.DATA = os.path.join(tmp, 'data')
    M.SITE = os.path.join(tmp, 'site')
    os.makedirs(M.DATA, exist_ok=True)
    try:
        M._save('traffic_daily.json', {'views': {'2026-09-01': {'count': 5, 'uniques': 2}},
                                       'clones': {'2026-09-01': {'count': 3, 'uniques': 1}}})
        M._save('releases.json', {'2026-09-15': {'v1': {
            'published_at': '2026-09-01T00:00:00Z',
            'assets': {'KiCadRoutingTools-1.zip': 7,
                       'grid_router-linux-x86_64.so': 2}}}})
        M._save('referrers.json', {'2026-09-15': [{'referrer': 'Google', 'count': 9}]})
        M._save('meta.json', meta)
        M.render('owner/repo')
        with open(os.path.join(M.SITE, 'index.html')) as f:
            return ' '.join(f.read().split())
    finally:
        M.DATA, M.SITE = data, site


def t_page_discloses_what_the_numbers_are_not():
    with tempfile.TemporaryDirectory() as tmp:
        flat = _render_into(tmp, {'last_collected': 'x', 'errors': {}})
    # Non-vacuity first: the page must actually have rendered its data.
    check('t_page_rendered_at_all', 'owner/repo' in flat and 'v1' in flat,
          f"{len(flat)} chars")
    check('t_page_says_uniques_are_not_additive',
          'not additive' in flat.lower() and 'unique-days' in flat)
    check('t_page_says_the_populations_are_not_summed',
          'never summed' in flat.lower())
    check('t_page_says_a_download_is_not_a_run',
          'a download is not a run' in flat.lower())
    check('t_page_names_its_own_ci_as_a_confound',
          'own ci' in flat.lower())


def t_a_failed_endpoint_is_disclosed_not_hidden():
    with tempfile.TemporaryDirectory() as tmp:
        clean = _render_into(tmp, {'last_collected': 'x', 'errors': {}})
        broken = _render_into(tmp, {'last_collected': 'x',
                                    'errors': {'traffic/views': 'HTTP 403'}})
    check('t_a_failed_endpoint_is_disclosed_not_hidden',
          'HTTP 403' in broken and 'traffic/views' in broken
          and 'Incomplete collection' in broken,
          'the failure and the endpoint are both named')
    # The control: a clean run must NOT print the warning, or the disclosure
    # is decoration that says nothing.
    check('t_a_clean_run_shows_no_warning',
          'Incomplete collection' not in clean)


def main():
    t_merge_keeps_the_max_per_date()
    t_pcm_and_binaries_are_counted_apart()
    t_page_discloses_what_the_numbers_are_not()
    t_a_failed_endpoint_is_disclosed_not_hidden()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILURE(S): {', '.join(FAILS)}")
        return 1
    print("ALL PASS")
    return 0


if __name__ == '__main__':
    sys.exit(main())
