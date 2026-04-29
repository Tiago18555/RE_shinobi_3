class SceneBuilder:
    def __init__(self, tileset: bytearray):
        self.tileset = tileset
        self.TILE_SIZE = 0x20
        self.TILE_MASK = 0x7FF

    def build_plane(self, full_nametable: bytearray) -> bytearray:
        output = bytearray()
        for i in range(0, len(full_nametable) - 1, 2):
            pattern = (full_nametable[i] << 8) | full_nametable[i + 1]
            output += self._get_tile(pattern)
        return output

    def _get_tile(self, pattern: int) -> bytearray:
        h_flip = (pattern & 0x0800) != 0 
        v_flip = (pattern & 0x1000) != 0  
        tile_index = pattern & self.TILE_MASK
        
        offset = tile_index << 5    
        
        # Read the 32 bytes for the 8x8 4bpp tile
        tile_data = self.tileset[offset:offset + self.TILE_SIZE]
        
        if h_flip or v_flip:
            pixels = self._unpack_tile(tile_data)
            
            if h_flip:
                pixels = self._on_h_flip(pixels)
            if v_flip:
                pixels = self._on_v_flip(pixels)
            
            tile_data = self._pack_tile(pixels)

        return bytearray(tile_data)

    def _on_v_flip(self, pixels):
        return pixels[::-1]

    def _on_h_flip(self, pixels):
        return [row[::-1] for row in pixels]

    def _unpack_tile(self, data):
        pixels = [[0]*8 for _ in range(8)]
        for y in range(8):
            row = data[y*4:(y+1)*4]
            for x in range(8):
                byte_index = x // 2
                if x % 2 == 0:
                    px = (row[byte_index] >> 4) & 0xF
                else:
                    px = row[byte_index] & 0xF
                pixels[y][x] = px
        return pixels

    def _pack_tile(self, pixels):
        data = bytearray(32)
        for y in range(8):
            row = bytearray(4)
            for x in range(8):
                byte_index = x // 2
                if x % 2 == 0:
                    row[byte_index] |= (pixels[y][x] & 0xF) << 4
                else:
                    row[byte_index] |= (pixels[y][x] & 0xF)
            data[y*4:(y+1)*4] = row
        return data