def debug_print(source: bytearray, with_string: bool = False, limit: int = 0):
    if limit <= 0 or limit > len(source):
        limit = len(source)

    for i in range(0, limit, 16):
        line_end = min(i + 16, limit)
        line_bytes = source[i:line_end]        
        address = f"{i:08X}"        

        words = []
        for j in range(0, len(line_bytes), 2):
            if j + 1 < len(line_bytes):
                words.append(f"{line_bytes[j]:02X}{line_bytes[j+1]:02X}")
            else:
                words.append(f"{line_bytes[j]:02X}  ")

        utf8_string = line_bytes.decode('utf-8', errors='replace')    
        
        utf8_string = utf8_string.replace('�', '.')
        utf8_string = utf8_string.replace('\n', '.')
        utf8_string = utf8_string.replace('\r', '.')
        utf8_string = utf8_string.replace('\t', '.')
        utf8_string = utf8_string.replace('\a', '.')
        utf8_string = utf8_string.replace(' ', '.')
        
        utf8_string = ''.join(
            (chr(c) if 32 <= c <= 126 else '.') for c in line_bytes
        )

        if with_string:
            print(f"{address}:\t{' '.join(words)}\t\t{utf8_string}")
        else:
            print(f"{address}:\t{' '.join(words)}")
            
def debug_print_at_offset(source: bytearray, offset: int, with_string: bool = False):
    if offset < 0 or offset >= len(source):
        print(f"Offset {offset:#X} está fora dos limites do buffer.")
        return

    line_start = (offset // 16) * 16
    line_end = min(line_start + 16, len(source))
    line_bytes = source[line_start:line_end]
    address = f"{line_start:08X}"

    words = []
    for j in range(0, len(line_bytes), 2):
        if j + 1 < len(line_bytes):
            word = f"{line_bytes[j]:02X}{line_bytes[j+1]:02X}"
        else:
            word = f"{line_bytes[j]:02X}  "
        words.append(word)

    utf8_string = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in line_bytes)

    if with_string:
        print(f"{address}:\t{' '.join(words)}\t\t{utf8_string}")
    else:
        print(f"{address}:\t{' '.join(words)}")