import sys
from PIL import Image
import argparse

def read_file(filename):
    try:
        with open(filename, 'rb') as f:
            return bytearray(f.read())
    except FileNotFoundError:
        print(f"Arquivo {filename} não encontrado.")
        sys.exit(1)
    
def read_gsx_palette(file_path, section=0):
    try:
        with open(file_path, 'rb') as file:
            file.seek(274)
            data = file.read(128)
            if len(data) != 128:
                raise ValueError("Palette data is not 128 bytes long")
            
            palette = []
            for i in range(0, 128, 2):
                word = (data[i + 1] << 8) | data[i]
                r = word & 0xF
                g = (word >> 4) & 0xF
                b = (word >> 8) & 0xF
                r_scaled = (r * 255) // 15
                g_scaled = (g * 255) // 15
                b_scaled = (b * 255) // 15
                palette.append([r_scaled, g_scaled, b_scaled])
            
            section_size = 16
            start = section * section_size
            end = start + section_size
            if start >= len(palette):
                raise ValueError(f"Section {section} out of range (0-3)")
            return palette[start:end]
    except Exception as e:
        print(f"Erro ao ler paleta: {e}")
        return None
    

def tile_to_image(tile_data, palette):
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

def create_tile_image(data, palette, tiles_width, tiles_height, output_path, scale=1):
    tile_size = 32
    expected_size = tiles_width * tiles_height * tile_size
    
    if len(data) < expected_size:
        print(f"Warning: Data size ({len(data)} bytes) is less than expected ({expected_size} bytes)")
    if len(data) % tile_size != 0:
        print("Warning: Data length is not a multiple of 32 bytes")
    
    num_tiles = min(len(data) // tile_size, tiles_width * tiles_height)
    output = Image.new('RGB', (tiles_width * 8, tiles_height * 8))
    
    for tile_idx in range(num_tiles):
        tile_start = tile_idx * tile_size
        tile_data = data[tile_start:tile_start + tile_size]
        tile_img = tile_to_image(tile_data, palette)
        
        x = (tile_idx % tiles_width) * 8
        y = (tile_idx // tiles_width) * 8
        output.paste(tile_img, (x, y))
    
    # Apply scaling if scale factor is greater than 1
    if scale > 1:
        new_width = tiles_width * 8 * scale
        new_height = tiles_height * 8 * scale
        output = output.resize((new_width, new_height), Image.NEAREST)
    
    output.save(output_path, "PNG")
    return output

def main():
    parser = argparse.ArgumentParser(description="Gera uma imagem PNG a partir de tiles Sega Genesis pré-montados.")
    parser.add_argument("tile_file", help="Caminho para o arquivo de tiles pré-montados")
    parser.add_argument("-p", "--palette", required=True, help="Caminho para o arquivo .gsx com a paleta")
    parser.add_argument("-s", "--section", type=int, default=0, choices=[0, 1, 2, 3],
                        help="Seção da paleta a usar (0-3, padrão 0)")
    parser.add_argument("-w", "--width", type=int, required=True, help="Largura em tiles")
    parser.add_argument("-ht", "--height", type=int, required=True, help="Altura em tiles")
    parser.add_argument("-sc", "--scale", type=int, default=1,
                        help="Fator de escala da imagem final (padrão 1, mínimo 1)")
    parser.add_argument("-o", "--output", help="Nome do arquivo de saída", default="output.png")
    args = parser.parse_args()

    if args.width <= 0 or args.height <= 0:
        print("Largura e altura devem ser maiores que zero.")
        sys.exit(1)
    if args.scale < 1:
        print("O fator de escala deve ser maior ou igual a 1.")
        sys.exit(1)
    
    tile_data = read_file(args.tile_file)
    palette = read_gsx_palette(args.palette, args.section)
    
    if not palette:
        print("Erro ao carregar paleta. Abortando.")
        sys.exit(1)
    
    create_tile_image(tile_data, palette, args.width, args.height, args.output, args.scale)

if __name__ == "__main__":
    main()