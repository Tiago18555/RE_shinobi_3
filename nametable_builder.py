import struct

class NametableBuilder:
    def __init__(self, rom_data: bytes, mapper_offset: int):
        self.rom_data = rom_data
        self.mapper_offset = mapper_offset
        self.mapper = self._extract_mapper()

    def _extract_mapper(self) -> bytes:
        end_offset = self.mapper_offset + (0x100 * 0x8) # 256 quadrantes, 8 bytes cada
        return self.rom_data[self.mapper_offset:end_offset]

    def _get_quadrants(self, index: int, vertical: bool) -> tuple:
        start_offset = index * 8
        words = self.mapper[start_offset:start_offset + 8]
        if len(words) < 8:
            raise ValueError(f"Índice de quadrante inválido ou mapper corrompido: {index}")
        
        tile1 = (words[0] << 8) | words[1]  # top-left
        tile2 = (words[2] << 8) | words[3]  # bottom-left
        tile3 = (words[4] << 8) | words[5]  # top-right
        tile4 = (words[6] << 8) | words[7]  # bottom-right
        
        # Como o Mega Drive renderiza Row-Major, transpomos o Column-Major
        return (tile1, tile2, tile3, tile4)

    def build(self, tilemap: bytes, vertical: bool) -> bytearray:
        try:
            QUADS_X = len(tilemap) // 32
            nametable = bytearray(len(tilemap) * 8)
            quad_x_size = 0x4
            
            if vertical:
                ln_size = 32 * 4 #line size in bytes if vertical
            else:
                ln_size = quad_x_size * QUADS_X #line size in bytes if horizontal

            for col in range(0, QUADS_X):        
                for row in range(0, 64, 2):
                    index = tilemap[(row // 2) + (col * 32)]              
                    t1, t3, t2, t4 = self._get_quadrants(index, vertical)  
                    
                    if vertical:
                        base = ((col * 2) * ln_size) + (row * 2)
                    else:
                        base = (row * ln_size) + (col * 4)

                    nametable[base:base + 2] = struct.pack(">H", t1)
                    nametable[base + 2:base + 4] = struct.pack(">H", t3)
                    nametable[base + ln_size:base + ln_size + 2] = struct.pack(">H", t2)
                    nametable[base + ln_size + 2:base + ln_size + 4] = struct.pack(">H", t4)

            return nametable
        except Exception as e:
            print(f"Erro ao gerar nametable: {e}")
            return bytearray()