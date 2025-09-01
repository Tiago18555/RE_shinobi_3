import struct
import sys
from debug_tools import debug_print

def get_quadrants(index, mapper, vertical):   
    start_offset = index * 8
    words = mapper[start_offset:start_offset + 8]
    if len(words) < 8:
        raise ValueError(f"Índice de quadrante inválido ou mapper corrompido: {index}")
    
    tile1 = (words[0] << 8) | words[1]  # top-left
    tile2 = (words[2] << 8) | words[3]  # bottom-left
    tile3 = (words[4] << 8) | words[5]  # top-right
    tile4 = (words[6] << 8) | words[7]  # bottom-right
    
    if vertical:
        return (tile1, tile2, tile3, tile4)
    else:
        return (tile1, tile2, tile3, tile4)

def create_full_nametable(mapper: bytearray, tilemap: bytes, vertical: bool):    
    try:
        
        #LINE SIZE IN QUADS
        QUADS_X = len(tilemap) // 32

        nametable = bytearray(len(tilemap) * 8) # 1 byte => 8 bytes of quads
        quad_x_size = 0x4 # size of quadrant in bytes (only X)
        
        if vertical:
            ln_size = 32 * 4 #line size in bytes if vertical
        else:
            ln_size = quad_x_size * QUADS_X #line size in bytes if horizontal

        for col in range(0, QUADS_X):        
            for row in range(0, 64, 2): # 2 rows at once
                
                index = tilemap[(row // 2) + (col * 32)]              
                t1, t2, t3, t4 = get_quadrants(index, mapper, vertical)  
                
                if vertical:
                    base = ((col * 2) * ln_size) + (row * 2)
                else:
                    base = (row * ln_size) + (col * 4)
                    
                #print(hex(base))

                nametable[base                  :base +           2] = struct.pack(">H", t1)
                nametable[base           + 2    :base +           4] = struct.pack(">H", t2)
                nametable[base + ln_size        :base + ln_size + 2] = struct.pack(">H", t3)
                nametable[base + ln_size + 2    :base + ln_size + 4] = struct.pack(">H", t4)

    except Exception as e:
        print(f"Erro ao gerar nametable: {e}")
        return None
    
    return nametable

def save_nametable(output_data: bytes, output_file: str):
    try:
        with open(output_file, "wb") as f:
            f.write(output_data)
    except Exception as e:
        print(f"Erro ao salvar nametable '{output_file}': {e}")

def extract_mapper_from_rom(rom_path: str, mapper_offset: int):
    try:
        with open(rom_path, "rb") as f:

            f.seek(mapper_offset)
            mapper = f.read(0x100 * 0x8)  # 256 quadrantes, 8 bytes cada
            return mapper
    except Exception as e:
        print(f"Erro ao ler mapper da ROM: {e}")
        return None

def nametable(rom_path, mapper_offset_hex, tilemap_path, output_path, vertical):
    mapper_offset = int(mapper_offset_hex, 16) if isinstance(mapper_offset_hex, str) else mapper_offset_hex
    mapper = extract_mapper_from_rom(rom_path, mapper_offset)
    if not mapper:
        print("Falha ao extrair o mapper da ROM.")
        return
    try:
        with open(tilemap_path, "rb") as f:
            tilemap = f.read()
    except Exception as e:
        print(f"Erro ao ler tilemap: {e}")
        return
    
    output_data = create_full_nametable(mapper, tilemap, vertical)
    if output_data is None:
        print("Erro ao criar nametable.")
        return

    save_nametable(output_data, output_path)
    return output_data

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Uso: python gerar_nametable.py <rom.bin> <offset_mapper_hex> <tilemap.bin> <output.bin>")
        print("Exemplo: python gerar_nametable.py jogo.bin 0x123456 tilemap.bin saida.bin")
    else:
        rom_path = sys.argv[1]
        mapper_offset = sys.argv[2]
        tilemap_path = sys.argv[3]
        output_path = sys.argv[4]

        nametable(rom_path, mapper_offset, tilemap_path, output_path, line_size=64, max_height=64)
  