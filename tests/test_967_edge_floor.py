"""Resolved placement edge floor on the published esp_prog poses (#967).

Reconstruct geometry from the existing repository board, never edit it.
Frozen public board/brief identities and independent native evidence are in
docs/issue-967-verification.md. These tests need no KiCad installation.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / p) for p in ('py_router', 'py_placer', 'tests')]
from copy_board import copy_board
from kicad_parser import parse_kicad_pcb
from placement.legality import grade_pad_legality, grade_pad_edge_clearance
from placement.writer import write_placed_output
from placement.seeder import stamp_locked

BOARD = ROOT / 'kicad_files/esp_prog.kicad_pcb'
POSES = {
    'bad': {'C2': (126.9, 103.5, 90), 'C4': (122.4, 102.2, 90),
            'U1': (126.6, 97.75, 270), 'Y1': (124.7, 103.2, 270)},
    'control': {'C2': (125.4, 93.4, 90), 'C4': (122.7, 95.6, 180),
                'U1': (127.6, 99.7, 180), 'Y1': (123, 93.4, 0)},
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class EdgeFloor(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='krt967_')
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.source_hash = digest(BOARD)
        self.addCleanup(lambda: self.assertEqual(digest(BOARD), self.source_hash))

    def fixture(self, case='bad'):
        out = self.work / (case + '.kicad_pcb')
        copy_board(str(BOARD), str(out))
        rows = [dict(reference=r, new_x=p[0], new_y=p[1], new_rotation=p[2])
                for r, p in POSES[case].items()]
        write_placed_output(str(out), str(out), rows)
        pcb = parse_kicad_pcb(str(out))
        stamp_locked(str(out), set(pcb.footprints) - set(POSES[case]))
        return out

    def cli(self, board, *verbs, floor='.55', expected=0, extra=(), output=None):
        out = output or self.work / 'out.kicad_pcb'
        args = [sys.executable, '-X', 'utf8', str(ROOT/'py_placer/place_pose.py'),
                str(board), str(out), '--clearance', '.25']
        if floor is not None:
            args += ['--board-edge-clearance', floor]
        args += list(extra) + list(verbs)
        result = subprocess.run(args, cwd=ROOT, capture_output=True,
                                text=True, encoding='utf-8', timeout=90)
        self.assertNotIn('Traceback', result.stdout + result.stderr)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        summaries = [json.loads(s.split(': ', 1)[1]) for s in result.stdout.splitlines()
                     if s.startswith('JSON_SUMMARY: ')]
        self.assertEqual(len(summaries), 1, result.stdout)
        if expected == 4:
            self.assertTrue(summaries[0]['refused'])
            self.assertIsNone(summaries[0]['output'])
        return summaries[0], out

    def test_frozen_bad_and_positive_control(self):
        board = self.fixture()
        for floor, count in (('.50', 0), ('.55', 2), ('.60', 2)):
            s, out = self.cli(board, 'set', 'Y1', '124.7', '103.2', '--rot', '270', floor=floor)
            self.assertEqual(s['legal'], count == 0)
            self.assertTrue(s['no_worse'])
            self.assertEqual(s['pad_edge_conflicts_after'], count)
            self.assertEqual(s['oob_pad_copper_count_after'], 0)
            self.assertEqual(s['pad_conflicts_after'], 0)
            if count:
                rows = s['pad_edge_after']['findings']
                self.assertEqual({r['pad_ref'] for r in rows}, {'Y1.2', 'Y1.3'})
                self.assertEqual(len({r['pad_index'] for r in rows}), 2)
                for r in rows:
                    self.assertAlmostEqual(r['gap_mm'], .50)
                    self.assertAlmostEqual(r['shortfall_mm'], float(floor)-.50)
        control = self.fixture('control')
        s, out = self.cli(control, 'set', 'Y1', '123', '93.4', '--rot', '0',
                          extra=('--strict-legal',))
        self.assertTrue(s['legal'])
        self.assertTrue(s['pad_edge_after']['complete'])
        self.assertEqual(parse_kicad_pcb(str(out)).footprints['Y1'].x, 123)

    def test_boundary_improving_and_worsening(self):
        board = self.fixture()
        for y, clean in (('103.18', False), ('103.15', True), ('103.10', True)):
            s, _ = self.cli(board, 'set', 'Y1', '124.7', y, '--rot', '270')
            self.assertTrue(s['no_worse'])
            self.assertEqual(s['legal'], clean)
        before = digest(board)
        s, _ = self.cli(board, 'set', 'Y1', '124.7', '103.21', '--rot', '270',
                        expected=4, output=board)
        self.assertIn('pad_edge_shortfall', s['refused'])
        self.assertEqual(digest(board), before)
        s, _ = self.cli(board, 'set', 'Y1', '124.7', '103.2', '--rot', '270',
                        expected=4, extra=('--strict-legal',), output=board)
        self.assertFalse(s['legal'])
        self.assertEqual(digest(board), before)

    def test_atomic_multi_near_and_dry_run(self):
        board = self.fixture()
        _, clean = self.cli(board, 'set', 'Y1', '124.7', '103.1', '--rot', '270')
        # A coordinated request must refuse as a whole when just one member
        # introduces an edge shortfall. Preserve sibling requirements as well.
        brief = clean.with_suffix('.design-brief.json')
        brief.write_text('{"version": 1, "purpose": "fixed test requirement"}')
        before, sibling = digest(clean), digest(brief)
        s, _ = self.cli(clean, 'set', 'Y1', '124.7', '103.2', '--rot', '270',
                        'set', 'C2', '126.9', '103.5', '--rot', '90',
                        expected=4, output=clean)
        self.assertIn('pad_edge_conflicts', s['refused'])
        self.assertEqual((digest(clean), digest(brief)), (before, sibling))
        s, out = self.cli(clean, 'set', 'Y1', '--near', '124.7', '103.2', '--rot', '270',
                          extra=('--radius', '.5', '--snap-step', '.05', '--snap-tries', '24'),
                          output=self.work/'snapped.kicad_pcb')
        self.assertTrue(s['snapped'])
        written = grade_pad_legality(parse_kicad_pcb(str(out)), .25, edge_margin=.55,
                                     pcb_file=str(out))
        self.assertEqual(written['pad_edge_conflicts'], 0)
        self.assertEqual(digest(out.with_suffix('.design-brief.json')), sibling)
        s, out = self.cli(board, 'set', 'Y1', '124.7', '103.15', '--rot', '270',
                          'set', 'C2', '126.9', '103.5', '--rot', '90',
                          extra=('--dry-run',), output=self.work/'dry.kicad_pcb')
        self.assertTrue(s['legal'])
        self.assertFalse(out.exists())

    def test_rule_sources_and_local_copper_override(self):
        board = self.fixture()
        s, _ = self.cli(board, 'set', 'Y1', '124.7', '103.2', '--rot', '270', floor=None)
        self.assertEqual(s['knobs']['board_edge_clearance']['requested'], None)
        self.assertEqual(s['pad_edge_after']['source'], 'fixed default')
        pro = board.with_suffix('.kicad_pro')
        pro.write_text(json.dumps({'board': {'design_settings': {'rules': {
            'min_copper_edge_clearance': .60}}},
            'net_settings': {'classes': [{'name': 'Default', 'clearance': .25}]}}))
        s, out = self.cli(board, 'set', 'Y1', '124.7', '103.2', '--rot', '270', floor=None)
        self.assertEqual(s['board_edge_clearance'], .60)
        self.assertEqual(s['pad_edge_after']['source'], 'board constraint')
        self.assertIsNone(s['pad_edge_after']['requested_mm'])
        self.assertEqual(digest(pro), digest(out.with_suffix('.kicad_pro')))
        s, _ = self.cli(board, 'set', 'Y1', '124.7', '103.2', '--rot', '270', floor='.50')
        self.assertEqual(s['pad_edge_after']['source'], 'cli')
        self.assertEqual(s['pad_edge_after']['requested_mm'], .50)
        self.assertTrue(s['legal'])  # placement's existing explicit override precedence
        pcb = parse_kicad_pcb(str(board))
        pcb.footprints['Y1'].pads[0].local_clearance = 3
        a = grade_pad_legality(pcb, .25, edge_margin=.50, pcb_file=str(board))
        b = grade_pad_legality(pcb, .25, edge_margin=.60, pcb_file=str(board))
        self.assertTrue(a['required'])
        for key in ('required', 'pad_conflicts', 'pad_shortfall', 'oob_pad_copper_refs'):
            self.assertEqual(a[key], b[key])

    def test_rotated_support_tolerance_and_unsupported(self):
        board = self.fixture()
        pcb = parse_kicad_pcb(str(board))
        fp = copy.deepcopy(pcb.footprints['Y1'])
        pad = fp.pads[0]
        fp.pads = [pad]
        pcb.footprints = {'Y1': fp}
        pad.shape, pad.size_x, pad.size_y, pad.rect_rotation = 'rect', 2, 1, 33
        pad.polygons = None
        pad.global_x = 130
        # Independent rectangle corner transform, not production support formula.
        angle = math.radians(33)
        support = max(x*math.sin(angle)+y*math.cos(angle)
                      for x in (-1, 1) for y in (-.5, .5))
        for gap, count in ((.50, 1), (.55, 0), (.60, 0), (.55-5e-7, 0), (.55-2e-6, 1)):
            pad.global_y = 105.5-support-gap
            report = grade_pad_edge_clearance(pcb, .55, str(board))
            self.assertEqual(len(report['findings']), count)
            self.assertAlmostEqual(report['minimum_gap_mm'], gap)
        # Rounded shapes rotated away from cardinal axes must not acquire
        # the sharp AABB corners of their outer rectangle.
        pad.shape, pad.size_x, pad.size_y = 'circle', 1, 1
        pad.global_y = 105.5-.5-.55
        self.assertEqual(grade_pad_edge_clearance(pcb, .55, str(board))['findings'], [])
        pad.shape = 'custom'
        report = grade_pad_edge_clearance(pcb, .55, str(board))
        self.assertFalse(report['complete'])
        self.assertIn('unsupported', report['unmeasured'][0]['reason'])
        # Existing custom-circle polygonization is inscribed (32 vertices).
        # At half a sample step it understates the radius by 0.0024076 mm:
        # a true .548 gap can look >= .55, so this cannot certify native copper.
        centre_y = 105.5-.5-.548
        pad.polygons = [[(130+.5*math.cos(math.radians(5.625+i*11.25)),
                          centre_y+.5*math.sin(math.radians(5.625+i*11.25)))
                         for i in range(32)]]
        report = grade_pad_edge_clearance(pcb, .55, str(board))
        self.assertGreater(report['minimum_gap_mm'], .55)
        self.assertFalse(report['complete'])
        self.assertIn('parsed polygons', report['unmeasured'][0]['reason'])
        pad.shape = 'rect'
        pad.polygons = None
        # A bounding box without a source/ring is not evidence of a closed board.
        pcb.source_path = None
        report = grade_pad_edge_clearance(pcb, .55)
        self.assertFalse(report['complete'])


if __name__ == '__main__':
    unittest.main()
