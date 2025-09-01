import sys
import argparse
from debug_tools import print_tile

def get_tile(tileset: bytearray, pattern, pos):
    tile = bytearray()
    TILE_SIZE = 0x20
    TILE_MASK = 0x7FF

    
    h_flip = (pattern & 0x0800) != 0 
    v_flip = (pattern & 0x1000) != 0  
    tile_index = pattern & TILE_MASK
    
    offset = tile_index << 5    
    try:
        for i in range(TILE_SIZE):
            tile.append(tileset[offset + i])
    except IndexError:
        print(f"Index out of range: {hex(offset)} at pos {pos}; pattern: {hex(tile_index)}")
        sys.exit(1)
    
    if h_flip or v_flip:
        flipped = bytearray(TILE_SIZE)
        bytes_per_row = 4 
        
        for row in range(8): 
            row_start = row * bytes_per_row
            new_row = row
                       
            if v_flip:
                new_row = 7 - row
                
            dest_start = new_row * bytes_per_row
            src_start = row * bytes_per_row
            
            if h_flip:
                flipped[dest_start] = tile[src_start + 3]
                flipped[dest_start + 1] = tile[src_start + 2]
                flipped[dest_start + 2] = tile[src_start + 1]
                flipped[dest_start + 3] = tile[src_start]
            else:
                flipped[dest_start:dest_start + 4] = tile[src_start:src_start + 4]
        
        tile = flipped

    return tile

def create(tilemap: bytearray, tileset):
    output = bytearray()
    
    try:
        for i in range(0, len(tilemap) - 1, 2):
            pattern =  ( tilemap[i] << 8 | (tilemap[i + 1])) 
            debug_info = f"offset 0x{i:04X}"        
            tile_data = get_tile(tileset, pattern, debug_info)
            output += tile_data        
    except IndexError:
        print(f"Index out of range: {hex(i)}; pattern: {hex(pattern)}")
        sys.exit(1)
    
    
    return output

def unpack_tile(data):
    pixels = [[0]*8 for _ in range(8)]
    for y in range(8):
        row = data[y*4:(y+1)*4]  # 4 bytes = 8 pixels
        for x in range(8):
            byte_index = x // 2
            if x % 2 == 0:
                px = (row[byte_index] >> 4) & 0xF  # high nibble
            else:
                px = row[byte_index] & 0xF         # low nibble
            pixels[y][x] = px
    return pixels

def pack_tile(pixels):
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

def rotate_tile(pixels, clockwise=False):
    if clockwise:
        return [[pixels[7 - x][y] for x in range(8)] for y in range(8)]
    else:
        return [[pixels[x][7 - y] for x in range(8)] for y in range(8)]

def create_plane(tileset, tilemap, output):
    tileset = read_file(tileset)
    tilemap = read_file(tilemap)

    data = create(tilemap, tileset)
    write_file(output, data)
    
    return data

def read_file(filename):
    try:
        with open(filename, 'rb') as f:
            return bytearray(f.read())
    except FileNotFoundError:
        print(f"File {filename} not found.")
        sys.exit(1)
        
def write_file(filename, data):
    with open(filename, 'wb') as f:
        f.write(data)
    stage = filename.split('\\')[1]
    print(f"[{stage}] File {filename} generated successfully.")

def main():
    parser = argparse.ArgumentParser(description="Processa um tileset e tilemap com suporte a H/V flips.")
    parser.add_argument("tileset_file", help="Caminho para o arquivo de tileset")
    parser.add_argument("tilemap_file", help="Caminho para o arquivo de tilemap")
    parser.add_argument("-o", "--output", help="Nome do arquivo de saída", default="plane.bin")
    args = parser.parse_args()
    
    create_plane(args.tileset_file, args.tilemap_file, args.output)

if __name__ == "__main__":
    main()