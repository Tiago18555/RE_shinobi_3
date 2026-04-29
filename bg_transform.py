import struct
from shared import trim_zero_bytes

def transform_bytes_single_line(source: bytearray, word_base: int, x: int, y: int, reverse=False):
    s_pos = 0
    t_pos = 0
    
    if reverse:
        source = source[::-1]
        word_base |= 0x1800

    # Cada byte vira uma Word (2 bytes)
    target = bytearray(len(source) * 2)

    try:
        for i in range(len(source)):
            byte = source[i]
            word = (byte + word_base) & 0xFFFF
            
            target[t_pos] = (word >> 8) & 0xFF
            target[t_pos + 1] = word & 0xFF
            t_pos += 2

    except IndexError as e:
        print(f"Erro no single_line: s_pos: {hex(s_pos)}, len: {len(source)}")
    
    return trim_zero_bytes(target)

def transform_bytes_dual_lines(source: bytearray, word_base: int, x: int, y: int):
    # O target precisa comportar 2 linhas de (x+1) words para cada linha de 'y'
    # Total de words = (x + 1) * 2 * y
    target = bytearray((x + 1) * 2 * y * 2)
    line_width = (x + 1) * 2

    try:
        # Primeira passagem (Linha superior de cada par)
        s_pos = 0
        for i in range(y):
            t_pos = i * (line_width * 2)
            for j in range(x + 1):
                word = (source[s_pos] + word_base) & 0xFFFF
                target[t_pos] = (word >> 8) & 0xFF
                target[t_pos + 1] = word & 0xFF
                s_pos += 1
                t_pos += 2

        # Segunda passagem (Linha inferior de cada par)
        s_pos = 0
        for i in range(y):
            t_pos = (i * (line_width * 2)) + line_width
            for j in range(x + 1):
                word = (source[s_pos] + word_base) & 0xFFFF
                target[t_pos] = (word >> 8) & 0xFF
                target[t_pos + 1] = word & 0xFF
                s_pos += 1
                t_pos += 2

    except IndexError as e:
        print(f"Erro no dual_lines: s_pos: {hex(s_pos)}")

    return trim_zero_bytes(target)

def transform_bytes_quad_lines(source: bytearray, word_base: int, x: int, y: int):
    target = bytearray((x + 1) * 4 * y * 2)
    line_width = (x + 1) * 2

    for pass_idx in range(4):
        s_pos = 0
        for i in range(y):
            t_pos = (i * (line_width * 4)) + (pass_idx * line_width)
            for j in range(x + 1):
                word = (source[s_pos] + word_base) & 0xFFFF
                target[t_pos] = (word >> 8) & 0xFF
                target[t_pos + 1] = word & 0xFF
                s_pos += 1
                t_pos += 2
                
    return trim_zero_bytes(target)

def transform_bytes_group_lines(source: bytearray, word_base: int, x: int, y: int, flip_state=[], reverse=False):
    if reverse:
        source = source[::-1]

    # Assume que y é o número de linhas no grupo e também o número de grupos
    line_width = (x + 1) * 2
    target = bytearray(line_width * y * y)

    try:
        for group in range(y):
            s_pos = 0
            for line in range(y):
                # Aplica o flip_state específico da linha se existir
                current_base = word_base | (flip_state[line] if line < len(flip_state) else 0)
                
                t_pos = (group * line_width) + (line * (line_width * y))
                
                for pattern in range(x + 1):
                    word = (source[s_pos] + current_base) & 0xFFFF
                    target[t_pos] = (word >> 8) & 0xFF
                    target[t_pos + 1] = word & 0xFF
                    s_pos += 1
                    t_pos += 2
                    
    except IndexError as e:
        print(f"Erro no group_lines: s_pos: {hex(s_pos)}, t_pos: {hex(t_pos)}")

    return trim_zero_bytes(target)