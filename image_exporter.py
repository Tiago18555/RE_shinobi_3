from PIL import Image

class ImageExporter:
    @staticmethod
    def parse_raw_palette(data: bytes) -> list:
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

    @staticmethod
    def _tile_to_image(tile_data: bytes, palette: list) -> Image.Image:
        if len(tile_data) != 32:
            raise ValueError("Tile data must be 32 bytes")
            
        img = Image.new('RGB', (8, 8))
        pixels = img.load()
        
        for y in range(8):
            row_start = y * 4
            for x in range(8):
                byte_idx = row_start + (x // 2)
                byte = tile_data[byte_idx]
                pixel = (byte >> 4) & 0xF if x % 2 == 0 else byte & 0xF
                pixels[x, y] = tuple(palette[pixel])
        
        return img

    @classmethod
    def export_plane_to_png(cls, data: bytes, palette: list, tiles_width: int, tiles_height: int, output_path: str, scale: int = 1):
        tile_size = 32
        
        num_tiles = min(len(data) // tile_size, tiles_width * tiles_height)
        output = Image.new('RGB', (tiles_width * 8, tiles_height * 8))
        
        for tile_idx in range(num_tiles):
            tile_start = tile_idx * tile_size
            tile_data = data[tile_start:tile_start + tile_size]
            tile_img = cls._tile_to_image(tile_data, palette)
            
            x = (tile_idx % tiles_width) * 8
            y = (tile_idx // tiles_width) * 8
            output.paste(tile_img, (x, y))
        
        if scale > 1:
            new_width = tiles_width * 8 * scale
            new_height = tiles_height * 8 * scale
            output = output.resize((new_width, new_height), Image.NEAREST)
        
        output.save(output_path, "PNG")
        return output

    @classmethod
    def export_collision_to_png(cls, tilemap: bytes, collision_mapper: bytes, vertical: bool, output_path: str, scale: int = 1):
        from PIL import ImageDraw, ImageFont
        
        quads_x = len(tilemap) // 32
        
        if vertical:
            width_quads = 32
            height_quads = quads_x
        else:
            width_quads = quads_x
            height_quads = 32
            
        block_size = 16 * scale
        img_w = width_quads * block_size
        img_h = height_quads * block_size
        
        img = Image.new('RGB', (img_w, img_h), "#1a1a1e")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default(size=max(8, 8 * scale))

        # Colors indexed by lower nibble (applied when lower nibble NOT in {8,9,A,B,E})
        nibble_colors = {
            0x0: ("#1a1a1e", "#2e2e36", "#aaaaaa"),  # 0x00 — background/void
            0x1: ("#b0b0bc", "#8a8a96", "#111111"),  # 0x01 — solid
            0x2: ("#ff7675", "#cc5a59", "#ffffff"),  # 0x02 — red
            0x3: ("#fd79a8", "#c0547f", "#ffffff"),  # 0x03 — pink
            0x4: ("#55efc4", "#2db58e", "#000000"),  # 0x04 — teal
            0x5: ("#00b894", "#007f65", "#ffffff"),  # 0x05 — green
            0x6: ("#fdcb6e", "#c9962a", "#000000"),  # 0x06 — yellow
            0x7: ("#e17055", "#a84a2f", "#ffffff"),  # 0x07 — orange
            0xC: ("#74b9ff", "#3a8fd1", "#000000"),  # 0x0C — light blue
            0xD: ("#a29bfe", "#6c5ce7", "#ffffff"),  # 0x0D — purple
            0xF: ("#0984e3", "#0660a8", "#ffffff"),  # 0x0F — blue
        }
        # Lower nibbles that receive no special coloring
        uncolored_nibbles = {0x8, 0x9, 0xA, 0xB, 0xE}

        for quad_y in range(height_quads):
            for quad_x in range(width_quads):
                if vertical:
                    tilemap_idx = quad_x + quad_y * 32
                else:
                    tilemap_idx = quad_y + quad_x * 32

                if tilemap_idx >= len(tilemap):
                    continue

                q_idx = tilemap[tilemap_idx]
                coll_val = collision_mapper[q_idx] if q_idx < len(collision_mapper) else 0

                x1 = quad_x * block_size
                y1 = quad_y * block_size
                x2 = x1 + block_size
                y2 = y1 + block_size

                lower = coll_val & 0xF
                label = f"{coll_val:02X}"

                if lower in uncolored_nibbles:
                    draw.rectangle([x1, y1, x2 - 1, y2 - 1], fill="#1a1a1e", outline="#2e2e36")
                else:
                    fill, outline, text_color = nibble_colors[lower]
                    draw.rectangle([x1, y1, x2 - 1, y2 - 1], fill=fill, outline=outline)
                    if block_size >= 8:
                        center_x = x1 + block_size // 2
                        center_y = y1 + block_size // 2
                        draw.text((center_x, center_y), label, fill=text_color, anchor="mm", font=font)

        img.save(output_path, "PNG")
        return img