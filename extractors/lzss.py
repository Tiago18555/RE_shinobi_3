def lzss_extract(input_file, output_file, offset):

    with open(input_file, "rb") as f:
        data = f.read()

    src = offset
    target = bytearray(0x1000)
    
    header = data[src:src + 2]
    word = (header[0] << 8) | header[1]
 
    decomp_size = word & 0x3FFF
    decomp_mask = (word & 0xC000) >> 0xE
    recopy_shifts = 4 - decomp_mask
    recopy_mask = 1 << recopy_shifts
    recopy_mask -= 1

    src += 2

    for i in range(decomp_size + 1):
        control = data[src]
        src += 1

        for bit in range(8):

            if control & 0x80:
                header = data[src]
                src += 1
                
                offset_back = header >> recopy_shifts                
                length = header & recopy_mask
                length += 1

                cp_offset = len(target) - 1 - offset_back
                
                for _ in range(length + 1):
                    target.append(target[cp_offset])
                    cp_offset += 1                    
                
            else:
                target.append(data[src])
                src += 1

            control <<= 1        

    with open(output_file, "wb") as f:
        f.write(target)
        
    return target