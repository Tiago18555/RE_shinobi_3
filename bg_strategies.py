import json
import os
from bg_transform import (
    transform_bytes_single_line, 
    transform_bytes_dual_lines, 
    transform_bytes_quad_lines, 
    transform_bytes_group_lines
)
from extractors import Extractors

class BackgroundStrategy:
    def __init__(self, rom_data: bytes, stage_table_path: str):
        self.rom_data = rom_data
        with open(stage_table_path, "r") as f:
            self.stage_data = json.load(f)

    def get_strategy(self, stage_name: str):
        switch = {
            "stage 1-1": self._default, "stage 1-2": self._default, "stage 1-3": self._default,
            "stage 2-1": self._idaten, "stage 2-2": self._ninja_soul, "stage 2-3": self._default,
            "stage 3-1": self._default, "stage 3-2": self._trap_body, "stage 3-3": self._my_dear_d,
            "stage 4-1": self._default, "stage 4-2": self._default, "stage 4-3": self._default,
            "stage 5-1": self._default, "stage 5-2": self._rush_and_beat, "stage 5-3": self._electric_demon,
            "stage 6-1": self._fall, "stage 6-2": self._default, "stage 6-3": self._electric_demon,
            "stage 7-1": self._solitary, "stage 7-2": self._default, "stage 7-3": self._default
        }
        
        strategy_func = switch.get(stage_name, self._default)
        return strategy_func(stage_name)

    def _default(self, stage: str):
        data = self.stage_data.get(stage).get("tilemap_b")
        
        bg_x = int(data.get("x_size"), 16)
        bg_y = int(data.get("y_size"), 16)
        offset = int(data.get("offset"), 16)        
        bg_skip = int(data.get("skip_word"), 16)
            
        tilemap_data = Extractors.lzss_decomp(self.rom_data[offset:]) 
        nametable = transform_bytes_dual_lines(tilemap_data, bg_skip, bg_x, bg_y)
        return (nametable,)

    def _idaten(self, stage: str):
        offsets = [0x3E7D4, 0x3E8DE]
        skips = [0x4180, 0xE180]
        bg_x = [0xF, 0xF]
        bg_y = [0x10, 0x7]

        border_data = Extractors.lzss_decomp(self.rom_data[offsets[0]:])
        lower_data = Extractors.lzss_decomp(self.rom_data[offsets[1]:])    
            
        upper_nt = transform_bytes_quad_lines(border_data, skips[0], bg_x[0], bg_y[0])
        lower_nt = transform_bytes_quad_lines(lower_data, skips[1], bg_x[1], bg_y[1])
        
        return (upper_nt + lower_nt,)

    def _ninja_soul(self, stage: str):
        offsets = [0x3E920, 0x3EB66]
        skips = [0x41D7, 0x41D7]
        bg_x = [0x1F, 0x13]
        bg_y = [0x1F, 0x1F]
        
        h_tilemap = Extractors.lzss_decomp(self.rom_data[offsets[0]:])
        v_tilemap = Extractors.lzss_decomp(self.rom_data[offsets[1]:])
        
        h_nt = transform_bytes_dual_lines(h_tilemap, skips[0], bg_x[0], bg_y[0])
        v_nt = transform_bytes_dual_lines(v_tilemap, skips[1], bg_x[1], bg_y[1])
        
        return (h_nt, v_nt)

    def _my_dear_d(self, stage: str):
        return self._trap_body(stage)

    def _trap_body(self, stage: str):
        offsets = [0x3EED8, 0x3EF32]
        skips = [0x4180, 0x4180]
        bg_x = [0x7, 0x1F]
        bg_y = [0x8, 0x7]
        layer_a_size = 0x48
        flip_states = [0x0]*8 + [0x1800]*8
        
        result = self._copy_with_h_mirror_effect(offsets, skips, bg_x, bg_y, layer_a_size, flip_states)
        return (result,)

    def _rush_and_beat(self, stage: str):
        offsets = [0x3FF12, 0x3F68E]
        skips = [0x6180, 0x4180]
        bg_x = [0x7, 0x3F]
        bg_y = [0x2, 0x3C]
        layer_a_size = 0x84E
        flip_states = [0x0] * 8
        
        result = self._copy_with_h_mirror_effect(offsets, skips, bg_x, bg_y, layer_a_size, flip_states)
        return (result,)

    def _electric_demon(self, stage: str):
        return (bytearray(0x500),)

    def _fall(self, stage: str):
        offsets = [0x3FF48, 0x40194]
        skips = [0x4180, 0x4180]
        bg_x = [0x11, 0X3]
        bg_y = [0x1F, 0X3F]
        layer_a_size = 0x240
        
        result = self._copy_with_v_mirror_effect(offsets, skips, bg_x, bg_y, layer_a_size)
        return (result,)

    def _solitary(self, stage: str):
        offsets = [0x40434, 0x40398, 0x40434]
        skips = [0xC1E0, 0xC1E0, 0xC1E0]
        bg_x = [0xF, 0xF, 0xF]
        bg_y = [0x11, 0xA, 0x11]
        
        data_1 = Extractors.lzss_decomp(self.rom_data[offsets[0]:])
        data_2 = Extractors.lzss_decomp(self.rom_data[offsets[1]:])
        
        fs_1 = [0x0]*4
        fs_2 = [0x0]*4 + [0x1800]*4
        fs_3 = [0x1800]*4
        
        nt1 = transform_bytes_group_lines(data_1, skips[0], bg_x[0], bg_y[0], fs_1)
        nt2 = transform_bytes_group_lines(data_2, skips[1], bg_x[1], bg_y[1], fs_2)
        nt3 = transform_bytes_group_lines(data_1, skips[2], bg_x[2], bg_y[2], fs_3)
        
        return (nt1, nt2, nt3)

    def _copy_with_h_mirror_effect(self, offsets, skips, bg_x, bg_y, layer_a_size, flip_states):
        center_tilemap = Extractors.lzss_decomp(self.rom_data[offsets[1]:])
        border_tilemap = self.rom_data[offsets[0]:offsets[0]+layer_a_size]
        
        u = transform_bytes_group_lines(border_tilemap, skips[0], bg_x[0], bg_y[0], flip_states)
        c = transform_bytes_dual_lines(center_tilemap, skips[1], bg_x[1], bg_y[1])
        l = transform_bytes_group_lines(border_tilemap, skips[0], bg_x[0], bg_y[0], flip_states, True)
        return u + c + l

    def _copy_with_v_mirror_effect(self, offsets, skips, bg_x, bg_y, layer_a_size):
        center_tilemap = Extractors.lzss_decomp(self.rom_data[offsets[1]:])
        border_tilemap = self.rom_data[offsets[0]:offsets[0]+layer_a_size]
        
        left = transform_bytes_single_line(border_tilemap, skips[0], bg_x[0], bg_y[0])
        mid = transform_bytes_single_line(center_tilemap, skips[1], bg_x[1], bg_y[1])
        right = transform_bytes_single_line(border_tilemap, skips[0], bg_x[0], bg_y[0], True)
        
        entire = bytearray()
        b_size = (bg_x[0] + 1) * 2
        c_size = (bg_x[1] + 1) * 2
        for line in range(bg_y[1]):
            base_b = b_size * line
            base_c = c_size * line
            entire += left[base_b:base_b+b_size] + mid[base_c:base_c+c_size] + right[base_b:base_b+b_size]
        return entire