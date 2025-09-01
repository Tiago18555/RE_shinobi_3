from debug_tools import debug_print

SIZE_LIMIT = 0x1FFF

def rle_extract(source, offset):
    
    with open(source, "rb") as f:
        source = f.read()
         
    target = bytearray()
    counter = 0x0
    
    while(True):
        
        try:        
            counter = source[offset]
            offset += 1
            
            if counter == 0xFF:
                counter = source[offset]
                offset += 1
                if counter == 0xFF:
                    break
                counter -= 0x1
                
                # LITERAL COPY #       
                for _ in range(counter + 1):
                    if len(target) - 1 >= SIZE_LIMIT:
                        target = trim_plane(target)
                        return target
                    target.append(source[offset])
                    offset += 1
                continue
                
            else:
                # RUN LENGTH COPY #
                byte = source[offset]
                offset += 1
                for _ in range(counter + 1):
                    if len(target) - 1 >= SIZE_LIMIT:
                        target = trim_plane(target)
                        return target
                    target.append(byte)
                continue
            
        except IndexError:
            print(f"Index out of range: {hex(offset)}")
            break

    target = trim_plane(target)
    return target

def trim_plane(data: bytearray) -> bytearray:
    
    while len(data) >= 0x20 and all(b == 0 for b in data[-0x20:]):
        data = data[:-0x20]

    return data


#debug_print(rle_extract('rom.bin', 'rle.bin', 0x4B846))