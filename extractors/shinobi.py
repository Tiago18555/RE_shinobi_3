import sys
import os

from debug_tools import debug_print_at_offset

sys.setrecursionlimit(10000)

byte = 0x0
temp = 0x0
pointer_step = 0x0
b_count = 0x0
count = 0x0
header = 0x0
ctrl: bool = False
C = False  # Carry flag
S = bytearray() # Source
T = bytearray(0x30A0) # Target
P = 0x0 # Source pos
output_file = ""

def shinobi_extract(source, offset, output):
    global byte, temp, pointer_step, b_count, count, header, ctrl, C, S, T, P, output_file
    
    byte = 0x0
    temp = 0x0
    pointer_step = 0x0
    b_count = 0x0
    count = 0x0
    header = 0x0
    ctrl = False
    C = False
    S = bytearray()
    T = bytearray()
    P = 0x0

    if not (isinstance(source, str)):
        raise ValueError("Source and output must be valid file paths.")

    P = offset
    output_file = output

    with open(source, "rb") as f:
        S = bytearray(f.read())
        
    if not (isinstance(offset, int) and 0 <= offset < len(S)):
        raise ValueError(f"Offset ({hex(offset)}) must be a valid position within the source file.")

    header = get_next_word(S, P)
    P += 2
    count = 0xF
    main_loop()

def main_loop():
    global count, header, ctrl, S, P, T, C

    ctrl = header & 0x1 == 0x1
    C = ctrl
    header >>= 1
    
    if count != 0:
        count -= 1
        
        if not ctrl: #BCC
            loc_a()
        else:        
            T.append(S[P])      #DIRECT COPY
            P += 1
            main_loop()
    else:
        header = get_next_word(S, P)
        P += 2
        count = 0xF
        if not ctrl: #bcc
            loc_a()
        else:        
            T.append(S[P])      #DIRECT COPY
            P += 1
            main_loop()

def loc_a():
    global b_count, count, header, ctrl, C, S, P
    b_count = 0x0
    ctrl = (header & 0x1) == 0x1
    C = ctrl
    header >>= 1
    
    if count != 0:
        count -= 1
        loc_b()
    else:
        header = get_next_word(S, P)
        P += 2
        count = 0xF
        loc_b()
        
def loc_b():
    global byte, temp, pointer_step, b_count, count, header, ctrl, S, P, T, C

    if ctrl: #BCS

        # move.b (A0)+, D0
        byte &= 0xFF00
        byte |= S[P]
        P += 1

        # move.b (A0)+, D1
        temp &= 0xFF00
        temp |= S[P]
        P += 1
        
        pointer_step = 0xFF00 | (temp & 0xFF)
        pointer_step <<= 5
        pointer_step &= 0xFF00
        pointer_step |= (byte & 0xFF) # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
        
        temp &= 0x7
        
        if temp == 0x0:
            temp &= 0x7
            loc_d()
            return
        else:
            b_count |= (temp & 0xFF)
            b_count += 1
                       
            for i in range(b_count + 1):   
                step = to_signed_number(pointer_step) 
                length = len(T)   
                pos = length + step
                byte = T[pos]        
                T.append(byte) # BULK COPY
                
                #debug_print_at_offset(T, len(T) - 1)

            
            main_loop()
            
    else:
        C = (header & 0x1) == 0x1
        header >>= 1
        
        if count != 0:
            count -= 1
            loc_c()
        else:
            header = get_next_word(S, P)
            P += 2
            count = 0xF
            loc_c() 

def loc_c():
    global byte, pointer_step, b_count, count, header, S, P, T, C

    roxl_w()
    
    C = (header & 0x1) == 0x1
    header >>= 1
    
    if count != 0:
        count -= 1
        
        roxl_w()
        b_count += 1
        pointer_step = 0xFF00 | (S[P] & 0xFF)
        P += 1        

        for i in range(b_count + 1):
            step = to_signed_number(pointer_step) 
            length = len(T)   
            pos = length + step
            byte = T[pos]        
            T.append(byte) #SIMPLE COPY                
            
        main_loop()
        
    else:
        header = get_next_word(S, P)
        P += 2
        count = 0xF
        roxl_w()
        b_count += 1
        pointer_step = 0xFF00 | (S[P] & 0xFF)
        P += 1
 
        for i in range(b_count + 1):    
            step = to_signed_number(pointer_step)
            length = len(T) 
            pos = length + step
            byte = T[pos]        
            T.append(byte) #SIMPLE COPY
        
        main_loop()


def loc_d():
    global byte, temp, pointer_step, b_count, S, P, T    
    
    if temp == S[P]:
        
        temp = S[P]
        P += 1
        
        finish()
        return
        
    temp = S[P]
    P += 1
    
    if (temp & 0xFF) == 0x1:
        main_loop()
    
    b_count = temp & 0xFF

    for i in range(b_count + 1): 
        step = to_signed_number(pointer_step)  
        length = len(T)
        pos = length + step
        byte = T[pos]        
        T.append(byte) #FINAL COPY
    
    main_loop()
    
def finish():
    global output_file, T
    
    if not output_file:
        return

    with open(output_file, "wb") as f:
        f.write(T)
    return

def get_next_word(source, offset):
    word = source[offset:offset+2]

    return (word[1] << 8) | word[0]

def to_signed_number(word):
    if word & 0x8000:
        return word - 0x10000
    else:
        return word

def roxl_w():
    global b_count, C
    old_x = 1 if C else 0
    msb = (b_count >> 15) & 1
    b_count = ((b_count << 1) & 0xFFFF) | old_x
    C = bool(msb)