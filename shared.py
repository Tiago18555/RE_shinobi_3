def trim_zero_bytes(data: bytearray) -> bytearray:
    non_zero_pos = len(data) - 1
    while non_zero_pos >= 0 and data[non_zero_pos] == 0:
        non_zero_pos -= 1
    
    if non_zero_pos < 0:
        return bytearray()
    
    return data[:non_zero_pos + 1]