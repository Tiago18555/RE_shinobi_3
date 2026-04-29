class Extractors:

    @staticmethod
    def shinobi_decomp(data: bytes | bytearray) -> bytearray:
        """
        Decompresses data using the Shinobi III (Mega Drive) compression scheme.

        This is a variant of LZSS. The compressed stream uses a 16-bit control word
        whose bits are consumed LSB-first to decide between literal copies and
        back-reference copies.

        Equivalent to the 68k routine at 0x3FE2 in the Shinobi III ROM.
        """
        source = bytearray(data)
        target = bytearray()
        pos = 0

        def read_byte():
            nonlocal pos
            val = source[pos]
            pos += 1
            return val

        def read_control_word():
            nonlocal pos
            lo = source[pos]
            hi = source[pos + 1]
            pos += 2
            return (hi << 8) | lo

        header = read_control_word()
        bits_remaining = 16

        def next_bit():
            nonlocal header, bits_remaining
            bit = header & 1
            header >>= 1
            bits_remaining -= 1
            if bits_remaining == 0:
                header = read_control_word()
                bits_remaining = 16
            return bit

        def copy_back_ref(offset: int, length: int):
            for _ in range(length):
                ref_pos = len(target) + offset
                target.append(target[ref_pos])

        while True:
            # --- main_loop: read 1 bit ---
            bit = next_bit()

            if bit:
                # Literal copy
                target.append(read_byte())
                continue

            # --- loc_a: bit was 0, read second bit ---
            bit_a = next_bit()

            if bit_a:
                # --- bulk_back_ref_copy ---
                d0 = read_byte()
                d1 = read_byte()

                offset_w = 0xFF00 | d1
                offset_w = (offset_w << 5) & 0xFFFF
                offset_w = (offset_w & 0xFF00) | d0
                offset = offset_w - 0x10000  # sign-extend to negative

                length_field = d1 & 0x07

                if length_field == 0:
                    # --- loc_d: extended length / control ---
                    extra = read_byte()
                    if extra == 0:
                        break  # End of stream
                    if extra == 1:
                        continue  # Restart main_loop
                    copy_back_ref(offset, extra + 1)
                else:
                    copy_back_ref(offset, length_field + 2)
            else:
                # --- simple_back_ref_copy: read 2 more bits for length ---
                extend = next_bit()
                b_count = extend

                extend2 = next_bit()
                b_count = (b_count << 1) | extend2

                b_count += 1
                offset_byte = read_byte()
                offset = (0xFF00 | offset_byte) - 0x10000  # -256...-1

                copy_back_ref(offset, b_count + 1)

        return target

    @staticmethod
    def lzss_decomp(data: bytes | bytearray) -> bytearray:
        """
        LZSS decompressor used for tilemap data in Shinobi III.

        Header (2 bytes, big-endian):
          - bits 13..0  : number of control-byte blocks (decomp_size)
          - bits 15..14 : recopy shift selector (decomp_mask)

        Each block starts with a control byte whose bits are consumed MSB-first:
          - bit=0 : literal byte copy
          - bit=1 : back-reference (1 byte encodes both offset and length)
        """
        src = 0
        target = bytearray()

        header = (data[src] << 8) | data[src + 1]
        src += 2

        decomp_size = header & 0x3FFF
        decomp_mask = (header & 0xC000) >> 0xE
        recopy_shifts = (4 - decomp_mask) & 0xFFFF
        recopy_mask = ((1 << recopy_shifts) & 0xFFFF) - 1

        for _ in range(decomp_size + 1):
            control = data[src]
            src += 1

            for _ in range(8):
                if control & 0x80:
                    ref_byte = data[src]
                    src += 1

                    offset_back = ref_byte >> recopy_shifts
                    length = (ref_byte & recopy_mask) + 1

                    cp_offset = len(target) - 1 - offset_back
                    for _ in range(length + 1):
                        target.append(target[cp_offset])
                        cp_offset += 1
                else:
                    target.append(data[src])
                    src += 1

                control = (control << 1) & 0xFF

        return Extractors._trim_zero_bytes(target)

    @staticmethod
    def rle_decomp(data: bytes | bytearray) -> bytearray:
        """
        RLE decompressor used for tilemap/nametable data in Shinobi III.

        Stream format:
          - 0xFF 0xFF         → end of stream
          - 0xFF N <N bytes>  → literal copy of N bytes (after N -= 1 adjustment)
          - CC BB              → repeat byte BB for (CC + 1) times
        """
        SIZE_LIMIT = 0x1FFF
        pos = 0
        target = bytearray()

        while True:
            counter = data[pos]
            pos += 1

            if counter == 0xFF:
                counter = data[pos]
                pos += 1
                if counter == 0xFF:
                    break
                counter -= 1

                for _ in range(counter + 1):
                    if len(target) - 1 >= SIZE_LIMIT:
                        return Extractors._trim_plane(target)
                    target.append(data[pos])
                    pos += 1
            else:
                byte = data[pos]
                pos += 1
                for _ in range(counter + 1):
                    if len(target) - 1 >= SIZE_LIMIT:
                        return Extractors._trim_plane(target)
                    target.append(byte)

        return Extractors._trim_plane(target)

    @staticmethod
    def _trim_zero_bytes(data: bytearray) -> bytearray:
        end = len(data) - 1
        while end >= 0 and data[end] == 0:
            end -= 1
        return data[:end + 1] if end >= 0 else bytearray()

    @staticmethod
    def _trim_plane(data: bytearray) -> bytearray:
        while len(data) >= 0x20 and all(b == 0 for b in data[-0x20:]):
            data = data[:-0x20]
        return data
