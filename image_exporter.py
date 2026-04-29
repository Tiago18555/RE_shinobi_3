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