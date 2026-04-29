import json
import os
import sys
import argparse

# Refactored OOP classes
from extractors import Extractors
from nametable_builder import NametableBuilder
from scene_builder import SceneBuilder
from image_exporter import ImageExporter
from bg_strategies import BackgroundStrategy

def main(output_root, args):
    # Base dir is now local (class_version)
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # JSON is now loaded locally
    with open(os.path.join(base_dir, "stage_table.json"), "r") as jf:
        stages = json.load(jf)

    # ROM is now loaded locally
    rom_path = os.path.join(base_dir, "rom.bin")
    with open(rom_path, "rb") as f:
        rom = f.read()

    bg_strat = BackgroundStrategy(rom, os.path.join(base_dir, "stage_table.json"))

    for stage_name, info in stages.items():
        stage_folder = os.path.join(output_root, stage_name)
        os.makedirs(stage_folder, exist_ok=True)

        colored_v_plane_a = os.path.join(stage_folder, "v_plane_a.bin")
        colored_h_plane_a = os.path.join(stage_folder, "h_plane_a.bin")
        colored_plane_b = os.path.join(stage_folder, "plane_b.bin")

        img_v_plane_a = os.path.join(stage_folder, f"[{stage_name}] v_plane_a.png")
        img_h_plane_a = os.path.join(stage_folder, f"[{stage_name}] h_plane_a.png")

        img_plane_b = os.path.join(stage_folder, f"[{stage_name}] plane_b.png")

        img_v_plane_b = os.path.join(stage_folder, f"[{stage_name}] v_plane_b.png")
        img_h_plane_b = os.path.join(stage_folder, f"[{stage_name}] h_plane_b.png")
        colored_h_plane_b = os.path.join(stage_folder, "h_plane_b.bin")
        colored_v_plane_b = os.path.join(stage_folder, "v_plane_b.bin")

        img_plane_b_1 = os.path.join(stage_folder, f"[{stage_name}] plane_b_1.png")
        img_plane_b_2 = os.path.join(stage_folder, f"[{stage_name}] plane_b_2.png")
        img_plane_b_3 = os.path.join(stage_folder, f"[{stage_name}] plane_b_3.png")

        # --------------- Infos -----------------------
        decompress_offset_a = int(info["tileset_a"]["offset"], 16)
        decompress_offset_b = int(info["tileset_b"]["offset"], 16)

        ba_mapper = int(info["mapper"]["offset"], 16)
        bg_x = int(info["tilemap_b"]["x_size"], 16)
        bg_y = int(info["tilemap_b"]["y_size"], 16)

        vram_base_offset = int(info["tileset_b"]["vram_base_offset"], 16)

        # ---------------- Tilemap A ----------------
        tilemap_a = bytearray()
        nametable_size = 0x20 * 0x30

        for i, offset in enumerate(info["tilemaps"]):
            tilemap_sect = Extractors.rle_decomp(rom[int(offset, 16):])

            if i != len(info["tilemaps"]) - 1:
                tilemap_sect = tilemap_sect[:-nametable_size]

            tilemap_a += tilemap_sect

        # ---------------- Tileset   ----------------
        print(f'[{stage_name}] Extracting tileset...')

        tileset_a = Extractors.shinobi_decomp(rom[decompress_offset_a:])
        tileset_b = Extractors.shinobi_decomp(rom[decompress_offset_b:])

        full_tileset = bytearray(0x10000)  # VRAM SIZE

        full_tileset[vram_base_offset: vram_base_offset + len(tileset_a)] = tileset_a
        full_tileset[0x1000: 0x1000 + len(tileset_b)] = tileset_b

        if args.debug:
            with open(os.path.join(stage_folder, "tileset.bin"), "wb") as f:
                f.write(full_tileset)

        # ---------------- Nametables ----------------
        print(f"[{stage_name}] Creating entire nametable")

        h_nametable_b, v_nametable_b = (None, None)
        nametable_b_1, nametable_b_2, nametable_b_3 = (None, None, None)

        bg_strategy = bg_strat.get_strategy(stage_name)

        if stage_name == "stage 2-2":
            h_nametable_b, v_nametable_b = bg_strategy
        elif stage_name == "stage 7-1":
            nametable_b_1, nametable_b_2, nametable_b_3 = bg_strategy
        else:
            (nametable_b, ) = bg_strategy

        nt_builder = NametableBuilder(rom, ba_mapper)
        scene_builder = SceneBuilder(full_tileset)
        
        v_plane_a = None
        h_plane_a = None

        if "V" in info["orientations"]:
            v_nametable_a = nt_builder.build(tilemap_a, vertical=True)
            if args.debug:
                with open(os.path.join(stage_folder, "raw_v_nametable_a.bin"), "wb") as f: f.write(v_nametable_a)
            v_plane_a = scene_builder.build_plane(v_nametable_a)

        if "H" in info["orientations"]:
            h_nametable_a = nt_builder.build(tilemap_a, vertical=False)
            if args.debug:
                with open(os.path.join(stage_folder, "raw_h_nametable_a.bin"), "wb") as f: f.write(h_nametable_a)
            h_plane_a = scene_builder.build_plane(h_nametable_a)

        # ----------------- Plane B -----------------
        print(f"[{stage_name}] Creating Plane B")

        if stage_name == "stage 2-2":
            if args.debug:
                with open(os.path.join(stage_folder, "raw_v_nametable_b.bin"), "wb") as f: f.write(v_nametable_b)
                with open(os.path.join(stage_folder, "raw_h_nametable_b.bin"), "wb") as f: f.write(h_nametable_b)
            v_plane_b = scene_builder.build_plane(v_nametable_b)
            h_plane_b = scene_builder.build_plane(h_nametable_b)
        elif stage_name == "stage 7-1":
            if args.debug:
                with open(os.path.join(stage_folder, "raw_nametable_b_1.bin"), "wb") as f: f.write(nametable_b_1)
                with open(os.path.join(stage_folder, "raw_nametable_b_2.bin"), "wb") as f: f.write(nametable_b_2)
                with open(os.path.join(stage_folder, "raw_nametable_b_3.bin"), "wb") as f: f.write(nametable_b_3)
            plane_b_1 = scene_builder.build_plane(nametable_b_1)
            plane_b_2 = scene_builder.build_plane(nametable_b_2)
            plane_b_3 = scene_builder.build_plane(nametable_b_3)
        else:
            if args.debug:
                with open(os.path.join(stage_folder, "raw_nametable_b.bin"), "wb") as f: f.write(nametable_b)
            plane_b = scene_builder.build_plane(nametable_b)

        # ----------------- Add color palette -------
        if "a_palettes" not in info or len(info["a_palettes"]) == 0:
            print(f"[{stage_name}] Warning: No color palette found for this stage.")
            continue

        print(f"[{stage_name}] Adding color palette")

        palette_offset_a = int(info["a_palettes"][0], 16)
        color_palette_a = rom[palette_offset_a:palette_offset_a + 0x20]
        parsed_palette_a = ImageExporter.parse_raw_palette(color_palette_a)

        if v_plane_a is not None:
            ImageExporter.export_plane_to_png(v_plane_a, parsed_palette_a, 64, (len(tilemap_a) // 32) * 2, img_v_plane_a, 4)
            if args.debug:
                with open(colored_v_plane_a, "wb") as f:
                    f.write(color_palette_a + v_plane_a)

        if h_plane_a is not None:
            ImageExporter.export_plane_to_png(h_plane_a, parsed_palette_a, (len(tilemap_a) // 32) * 2, 64, img_h_plane_a, 4)
            if args.debug:
                with open(colored_h_plane_a, "wb") as f:
                    f.write(color_palette_a + h_plane_a)

        palette_offset_b = int(info["tilemap_b"]["palette"], 16)
        color_palette_b = rom[palette_offset_b:palette_offset_b + 0x20]
        parsed_palette_b = ImageExporter.parse_raw_palette(color_palette_b)

        if stage_name == "stage 2-2":
            ImageExporter.export_plane_to_png(v_plane_b, parsed_palette_b, 0x14 * 2, 0x1F, img_v_plane_b, 4)
            ImageExporter.export_plane_to_png(h_plane_b, parsed_palette_b, 0x20 * 2, 0x1F, img_h_plane_b, 4)

            if args.debug:
                with open(colored_h_plane_b, "wb") as f:
                    f.write(color_palette_b + h_plane_b)
                with open(colored_v_plane_b, "wb") as f:
                    f.write(color_palette_b + v_plane_b)

        elif stage_name == "stage 7-1":
            ImageExporter.export_plane_to_png(plane_b_1, parsed_palette_b, 0x10 * 2, 0x11, img_plane_b_1, 4)
            ImageExporter.export_plane_to_png(plane_b_2, parsed_palette_b, 0x10 * 2, 0xB, img_plane_b_2, 4)
            ImageExporter.export_plane_to_png(plane_b_3, parsed_palette_b, 0x10 * 2, 0x11, img_plane_b_3, 4)
        else:
            ImageExporter.export_plane_to_png(plane_b, parsed_palette_b, (bg_x + 1) * 2, bg_y, img_plane_b, 4)
            
            if args.debug:
                with open(colored_plane_b, "wb") as f:
                    f.write(color_palette_b + plane_b)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Export binary files for debugging")
    args = parser.parse_args()

    print("Extracting...")
    output_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stages")
    main(output_root, args)
