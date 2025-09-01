from shinobi import roxl_w, get_next_word, to_signed_number

def test_roxl_w():
    global D3, C
    D3 = 0x1234
    C = 0x1
    roxl_w()
    assert D3 == 0x2469
    assert C == 0x0
    
def test_roxl_w_II():
    global D3, C
    D3 = 0x91A0
    C = 0x0
    roxl_w()
    assert D3 == 0x2340
    assert C == 0x1

def test_roxl_w_III():
    global D3, C
    D3 = 0xC000
    C = 0x1
    roxl_w()
    assert D3 == 0x8001
    assert C == 0x1

def test_roxl_w_IV():
    global D3, C
    D3 = 0x1000
    C = 0x0
    roxl_w()
    assert D3 == 0x2000
    assert C == 0x0

def test_get_next_word():
    source = bytes([0x12, 0x34, 0xAB, 0xCD])
    
    result1 = get_next_word(source, 0)
    result2 = get_next_word(source, 2)
    
    assert result1 == 0x3412
    assert result2 == 0xCDAB
    
def test_to_signed_number():
    assert to_signed_number(0x0000) == 0
    assert to_signed_number(0x0001) == 1
    assert to_signed_number(0x7FFF) == 32767
    assert to_signed_number(0x8000) == -32768
    assert to_signed_number(0xFFFF) == -1
    assert to_signed_number(0xFFFE) == -2  
    
def test():
    test_roxl_w()
    test_roxl_w_II()
    test_roxl_w_III()
    test_roxl_w_IV()
    test_get_next_word()
    test_to_signed_number()
    
test()