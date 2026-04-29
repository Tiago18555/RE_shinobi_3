import unittest
import os
import json
from extractors import Extractors
from nametable_builder import NametableBuilder
from bg_strategies import BackgroundStrategy

class TestReconstruction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.abspath(__file__))
        cls.rom_path = os.path.join(cls.base_dir, "rom.bin")
        cls.json_path = os.path.join(cls.base_dir, "stage_table.json")
        cls.stages_dir = os.path.join(cls.base_dir, "stages")

        with open(cls.rom_path, "rb") as f:
            cls.rom = f.read()
        with open(cls.json_path, "r") as f:
            cls.stages_info = json.load(f)

        cls.bg_strat = BackgroundStrategy(cls.rom, cls.json_path)

    def test_plane_a_reconstruction(self):
        """Test Plane A reconstruction for stage 1-1 (Horizontal)"""
        stage_name = "stage 1-1"
        info = self.stages_info[stage_name]
        
        # Build tilemap A
        tilemap_a = bytearray()
        nametable_size = 0x20 * 0x30
        for i, offset in enumerate(info["tilemaps"]):
            tilemap_sect = Extractors.rle_decomp(self.rom[int(offset, 16):])
            if i != len(info["tilemaps"]) - 1:
                tilemap_sect = tilemap_sect[:-nametable_size]
            tilemap_a += tilemap_sect

        # Build nametable
        ba_mapper = int(info["mapper"]["offset"], 16)
        nt_builder = NametableBuilder(self.rom, ba_mapper)
        h_nametable_a = nt_builder.build(tilemap_a, vertical=False)

        # Compare with expected
        expected_path = os.path.join(self.stages_dir, stage_name, "raw_h_nametable_a.bin")
        with open(expected_path, "rb") as f:
            expected = f.read()
        
        self.assertEqual(h_nametable_a, expected, f"Plane A Horizontal mismatch for {stage_name}")

    def _test_strategy(self, stage_name, expected_files):
        """Helper to test a Plane B strategy"""
        results = self.bg_strat.get_strategy(stage_name)
        
        self.assertEqual(len(results), len(expected_files), f"Tuple length mismatch for {stage_name}")
        
        for i, (res, filename) in enumerate(zip(results, expected_files)):
            expected_path = os.path.join(self.stages_dir, stage_name, filename)
            with open(expected_path, "rb") as f:
                expected = f.read()
            self.assertEqual(res, expected, f"Plane B mismatch for {stage_name} part {i+1} ({filename})")

    def test_strategy_default(self):
        self._test_strategy("stage 1-1", ["raw_nametable_b.bin"])

    def test_strategy_idaten(self):
        self._test_strategy("stage 2-1", ["raw_nametable_b.bin"])

    def test_strategy_ninja_soul(self):
        self._test_strategy("stage 2-2", ["raw_h_nametable_b.bin", "raw_v_nametable_b.bin"])

    def test_strategy_trap_body(self):
        self._test_strategy("stage 3-2", ["raw_nametable_b.bin"])

    def test_strategy_rush_and_beat(self):
        self._test_strategy("stage 5-2", ["raw_nametable_b.bin"])

    def test_strategy_electric_demon(self):
        self._test_strategy("stage 5-3", ["raw_nametable_b.bin"])

    def test_strategy_fall(self):
        self._test_strategy("stage 6-1", ["raw_nametable_b.bin"])

    def test_strategy_solitary(self):
        self._test_strategy("stage 7-1", ["raw_nametable_b_1.bin", "raw_nametable_b_2.bin", "raw_nametable_b_3.bin"])

if __name__ == "__main__":
    unittest.main()
