import json
import os

from extractors.lzss import lzss_extract
from extractors.shinobi import shinobi_extract
from extractors.rle import rle_extract

from debug_tools import debug_print
from nametable import nametable
from create_scene import create_plane
from plane_to_png import create_tile_image

def read_raw_palette_sect(data):
    try:
        if len(data) != 32:
            raise ValueError("Palette sect data is not 32 bytes long")
        
        palette = []
        for i in range(0, 32, 2):
            word = (data[i] << 8) | data[i + 1]
            r = word & 0xF
            g = (word >> 4) & 0xF
            b = (word >> 8) & 0xF
            r_scaled = (r * 255) // 15
            g_scaled = (g * 255) // 15
            b_scaled = (b * 255) // 15
            palette.append([r_scaled, g_scaled, b_scaled])
        

        return palette
    except Exception as e:
        print(f"Erro ao ler paleta: {e}")
        return None

def main(output_root, vertical):
    with open("stage_table.json", "r") as jf:
        stages = json.load(jf)

    input_file = "rom.bin"

    for i, (stage_name, info) in enumerate(stages.items()):
        stage_folder = os.path.join(output_root, stage_name)
        os.makedirs(stage_folder, exist_ok=True)
        
        # ---------------- Tilemap A ----------------        
        full_tilemap = bytearray()
        tilemap_a_file = os.path.join(stage_folder, "tilemap_a.bin")
        nametable_size = 0x20 * 0x30
        
        for i, offset in enumerate(info["tilemaps"]):
            tilemap_sect = rle_extract(input_file, int(offset, 16))

            if i != len(info["tilemaps"]) - 1:
                tilemap_sect = tilemap_sect[:-nametable_size]

            full_tilemap += tilemap_sect
        with open(tilemap_a_file, "wb") as f:
            f.write(full_tilemap)

        # ---------------- Tilemap B ----------------
        decompress_offset_tilemap_b = int(info["tilemap_b"]["offset"], 16)
        tilemap_b_file = os.path.join(stage_folder, "tilemap_b.bin")
        print(f"[{stage_name}] Extracting tilemap at 0x{decompress_offset_tilemap_b:X} to {tilemap_b_file}")
        lzss_extract(input_file, tilemap_b_file, decompress_offset_tilemap_b)

        # ---------------- Tileset A ----------------
        decompress_offset_tileset_a = int(info["tileset_a"]["offset"], 16)
        tileset_a_file = os.path.join(stage_folder, "tileset_a.bin")
        print(f"[{stage_name}] Extracting tileset A at 0x{decompress_offset_tileset_a:X} to {tileset_a_file}")
        shinobi_extract(input_file, decompress_offset_tileset_a, tileset_a_file)

        # ---------------- Tileset B ----------------
        decompress_offset_tileset_b = int(info["tileset_b"]["offset"], 16)
        tileset_b_file = os.path.join(stage_folder, "tileset_b.bin")
        print(f"[{stage_name}] Extracting tileset B at 0x{decompress_offset_tileset_b:X} to {tileset_b_file}")
        shinobi_extract(input_file, decompress_offset_tileset_b, tileset_b_file)

        # ---------------- Full Tileset ----------------
        full_tileset = bytearray(0x10000) # VRAM SIZE
        with open(tileset_b_file, "rb") as f:
            tb = f.read()

        with open(tileset_a_file, "rb") as f:
            ta = f.read()
            
        full_tileset[0x1000: 0x1000 + len(tb)] = tb
        full_tileset[0x30A0: 0x30A0 + len(ta)] = ta
        
        with open(os.path.join(stage_folder, "tileset_a_full.bin"), "wb") as f:
            f.write(full_tileset)


        # ---------------- Nametables ----------------
        mapper = int(info["mapper"]["offset"], 16)
        nametable_a_file = os.path.join(stage_folder, "nametable_a.bin")
        nametable_b_file = os.path.join(stage_folder, "nametable_b.bin")

        print(f"[{stage_name}] Creating nametable")

        nametable(input_file, mapper, tilemap_a_file, nametable_a_file, vertical)
        nametable(input_file, mapper, tilemap_b_file, nametable_b_file, vertical)

        # ----------------- Plane A -----------------
        plane_a_file = os.path.join(stage_folder, "plane_a.bin")
        full_tileset_file = os.path.join(stage_folder, "tileset_a_full.bin")
        full_nametable_file = os.path.join(stage_folder, "nametable_a.bin")

        print(f"[{stage_name}] Creating Plane A")

        plane = create_plane(full_tileset_file, full_nametable_file, plane_a_file)

        # ----------------- Plane B -----------------
        #plane_b_file = os.path.join(stage_folder, "plane_b.bin")
        #full_tileset_file = os.path.join(stage_folder, "tileset_b.bin")
        #full_nametable_file = os.path.join(stage_folder, "nametable_b.bin")

        #print(f"[{stage_name}] Creating Plane B")

        #plane = create_plane(full_tileset_file, full_nametable_file, plane_b_file)

        # ----------------- Add color palette -------
        
        if "a_palettes" not in info or len(info["a_palettes"]) == 0:
            print(f"[{stage_name}] Warning: No color palette found for this stage.")
            continue
        
        
        color_palette_file = os.path.join(stage_folder, "plane_a_with_color.bin")
        img_file = os.path.join(stage_folder, "plane_a.png")
        print(f"[{stage_name}] Adding color palette")

        with open(input_file, "rb") as f:
            f.seek(int(info["a_palettes"][0], 16))        
            color_palette = f.read(0x20)
            
        if vertical:
            create_tile_image(plane, read_raw_palette_sect(color_palette), 64, (len(full_tilemap) // 32) * 2, img_file, 4)
        if not vertical:
            create_tile_image(plane, read_raw_palette_sect(color_palette), (len(full_tilemap) // 32) * 2, 64, img_file, 4)

        final = color_palette + plane
        
        with open(color_palette_file, "wb") as f:
            f.write(final)

if __name__ == "__main__":
    
    print(f"Extracting as horizontal...")
    
    output_root = "H_stages"
    main(output_root, False)

    print(f"Extracting as vertical...")

    output_root = "V_stages"
    main(output_root, True)