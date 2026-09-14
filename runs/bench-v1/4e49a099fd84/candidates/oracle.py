import sys

def is_attachment(cp):
    ranges = [
        (0x0300, 0x036F),
        (0x1AB0, 0x1AFF),
        (0x1DC0, 0x1DFF),
        (0x20D0, 0x20FF),
        (0xFE00, 0xFE0F),
        (0xFE20, 0xFE2F),
        (0x1F3FB, 0x1F3FF),
        (0xE0100, 0xE01EF),
    ]
    return any(start <= cp <= end for start, end in ranges)

def is_emoji(cp):
    return (0x2600 <= cp <= 0x27BF) or (0x1F000 <= cp <= 0x1FAFF)

def is_regional_indicator(cp):
    return 0x1F1E6 <= cp <= 0x1F1FF

def is_control(cp):
    return (0x0000 <= cp <= 0x001F) or (0x007F <= cp <= 0x009F)

def parse_utf8_bytes(data):
    scalars = []
    i = 0
    while i < len(data):
        b = data[i]
        if b < 0x80:
            scalars.append(b)
            i += 1
        elif b < 0xE0:
            cp = ((b & 0x1F) << 6) | (data[i+1] & 0x3F)
            scalars.append(cp)
            i += 2
        elif b < 0xF0:
            cp = ((b & 0x0F) << 12) | ((data[i+1] & 0x3F) << 6) | (data[i+2] & 0x3F)
            scalars.append(cp)
            i += 3
        else:
            cp = ((b & 0x07) << 18) | ((data[i+1] & 0x3F) << 12) | ((data[i+2] & 0x3F) << 6) | (data[i+3] & 0x3F)
            scalars.append(cp)
            i += 4
    return scalars

def find_graphemes(scalars):
    if not scalars:
        return []
    
    graphemes = [[scalars[0]]]
    
    for i in range(len(scalars) - 1):
        left_cp = scalars[i]
        right_cp = scalars[i+1]
        
        rule4_met = False
        if left_cp == 0x200D and is_emoji(right_cp):
            j = i - 1
            while j >= 0 and is_attachment(scalars[j]):
                j -= 1
            if j >= 0 and is_emoji(scalars[j]):
                rule4_met = True
        
        if left_cp == 0x000D and right_cp == 0x000A:
            has_boundary = False
        elif is_control(left_cp) or is_control(right_cp):
            has_boundary = True
        elif is_attachment(right_cp) or right_cp == 0x200D:
            has_boundary = False
        elif rule4_met:
            has_boundary = False
        elif is_regional_indicator(left_cp) and is_regional_indicator(right_cp):
            count = 1
            j = i - 1
            while j >= 0 and is_regional_indicator(scalars[j]):
                count += 1
                j -= 1
            has_boundary = (count % 2 == 0)
        else:
            has_boundary = True
        
        if has_boundary:
            graphemes.append([right_cp])
        else:
            graphemes[-1].append(right_cp)
    
    return graphemes

def compute_utf16_offsets(graphemes):
    offsets = [0]
    current_offset = 0
    
    for grapheme in graphemes:
        for cp in grapheme:
            if cp > 0xFFFF:
                current_offset += 2
            else:
                current_offset += 1
        offsets.append(current_offset)
    
    return offsets

def resolve_index(x, num_graphemes):
    if x >= 0:
        return min(x, num_graphemes)
    else:
        return max(0, num_graphemes + x)

input_str = sys.stdin.read()
tokens = input_str.split()
S_str = tokens[0]
Q = int(tokens[1])

S_bytes = S_str.encode('utf-8')

scalars = parse_utf8_bytes(S_bytes)
graphemes = find_graphemes(scalars)
num_graphemes = len(graphemes)
offsets = compute_utf16_offsets(graphemes)

idx = 2
for _ in range(Q):
    query_type = int(tokens[idx])
    a = int(tokens[idx + 1])
    b = int(tokens[idx + 2])
    idx += 3
    
    i = resolve_index(a, num_graphemes)
    j = resolve_index(b, num_graphemes)
    
    if query_type == 1:
        if j >= i:
            print(offsets[i], offsets[j])
        else:
            print(offsets[i], offsets[i])
    else:
        L = 0
        while i + L < num_graphemes and j + L < num_graphemes:
            if graphemes[i + L] == graphemes[j + L]:
                L += 1
            else:
                break
        byte_count = offsets[i + L] - offsets[i]
        print(L, byte_count)