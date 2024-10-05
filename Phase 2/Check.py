def check(hex_str):
    integer_value = int(hex_str, 16)
    binary_str = bin(integer_value)[2:]
    required_length = len(hex_str) * 4
    padded_binary = binary_str.zfill(required_length)
    split_binary = list(padded_binary)
    # print(split_binary)
    op = ''.join(split_binary[:6])
    n=split_binary[6]
    i = split_binary[7]
    x = split_binary[8]
    b = split_binary[9]
    p = split_binary[10]
    e = split_binary[11]
    disp_bits = ''.join(split_binary[12:])
    print(f"{'op':<10} {'n':<3} {'i':<3} {'x':<3} {'b':<3} {'p':<3} {'e':<3} {'   disp'}")  
    print(f"{op:<10} {n:<3} {i:<3} {x:<3} {b:<3} {p:<3} {e:<3} {disp_bits}")  


check('03100008')

'''
prog start 0x0 
    base xx
    +add xx           0
    add zz            4
    sta xx, x         7
xx  word 5            A
yy  resb 2            D
zz  word 4            F
    end prog          12


'''