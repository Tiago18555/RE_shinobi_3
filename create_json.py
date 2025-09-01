import json

def get_addrs(input_file, offset):
    addrs = []
    with open(input_file, "rb") as f:
        f.seek(offset)
        for _ in range(7):
            a = int.from_bytes(f.read(4))
            addrs.append(a)
            
            b = int.from_bytes(f.read(4))
            addrs.append(b)
            
            c = int.from_bytes(f.read(4))
            addrs.append(c)
            
            _ = int.from_bytes(f.read(4)) 
            
    return addrs

def get_mapper(input_file, offset):
    base_addrs = []
    addrs = []
    with open(input_file, "rb") as f:
        f.seek(offset)
        for _ in range(7):
            a = int.from_bytes(f.read(4))
            base_addrs.append(a)
            
            b = int.from_bytes(f.read(4))
            base_addrs.append(b)
            
            c = int.from_bytes(f.read(4))
            base_addrs.append(c)

            _ = int.from_bytes(f.read(4))
            
        for addr in base_addrs:
            f.seek(addr)
            addrs.append(int.from_bytes(f.read(4)))
            
    return addrs

def get_pal_addrs():
    
    pass

def merge_stage_data(stage_table, tilemaps):
    merged_data = {}
    
    
    for stage_name, stage_info in stage_table.items():
        tileset_key = stage_name.replace(" ", "_").lower() 

        if tileset_key in tilemaps:
            stage_info["tilemaps"] = tilemaps[tileset_key]
        else:
            stage_info["tilemaps"] = [] 

        merged_data[stage_name] = stage_info
    
    return merged_data

def create_json(input_file="rom.bin"):
    
    c_data = 0x43042
    palettes = 0x42062
    
    stage_names = [f"stage {i}-{j}" for i in range(1, 8) for j in range(1, 4)]
    
    mapper = get_mapper(input_file, 0xFF23E)
    tilemap_b_addrs = get_addrs(input_file, 0x3E1C8)
    tileset_a_addrs = get_addrs(input_file, 0xE2ED8)
    tileset_b_addrs = get_addrs(input_file, 0xD8DB2)

    with open(input_file, "rb") as f:
        data = f.read()

    stages = {}
    sect_counts = [3, 3, 1, 1, 3, 1, 3, 1, 1, 1, 3, 1, 4, 4, 1, 2, 8, 1, 5, 5, 1]
    vertical = []
    for name, tm_b, ts_a, ts_b, mapper, sects in zip(stage_names, tilemap_b_addrs, tileset_a_addrs, tileset_b_addrs, mapper, sect_counts):
        counter = data[tm_b + 5]
        tm_b_decomp = tm_b + 6 + ((counter + 1) * 6)
            
        pal_offsets = []
        
        for sect in range(0, sects - 1):

            stage_part = int(name[-1]) - 1
            stage_number = int(name[-3]) - 1

            base_offset = c_data + ((stage_number * 16 + stage_part * 8 + sect) * 4) + 3
            print(f'STAGE:{stage_number}-{stage_part} BYTE: {hex(data[base_offset])} OFFSET:{hex(base_offset)}')
            skip = data[base_offset] * 32
            pal_offset = palettes + skip
            pal_offsets.append(pal_offset)

        stages[name] = {
            "tilemap_b": {
                "base_offset": f"0x{tm_b:08X}",
                "offset": f"0x{tm_b_decomp:08X}",
                "counter": counter,
            },
            "mapper": { 
                "offset": f"0x{mapper:08X}"
            },
            "tileset_a": {
                "base_offset": f"0x{ts_a:08X}",
                "offset": f"0x{ts_a + 0x4:08X}"
            },
            "tileset_b": {
                "base_offset": f"0x{ts_b:08X}",
                "offset": f"0x{ts_b + 0x4:08X}"
            },
            "a_palettes": [
                f"0x{addr:08X}" for addr in pal_offsets
            ],            
            "sects": sects
        }

    with open('tilemaps.json', 'r') as f:
        tilemaps_data = json.load(f)
    merged_stages = merge_stage_data(stages, tilemaps_data)
    with open("stage_table.json", "w") as out:
        json.dump(merged_stages, out, indent=4)

    return merged_stages

create_json()
