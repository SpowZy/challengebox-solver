def utf8_length(codepoint):
    if codepoint <= 0x7F:
        return 1
    elif codepoint <= 0x7FF:
        return 2
    elif codepoint <= 0xFFFF:
        return 3
    else:
        return 4

line = input().split()
N, S, Q, C, H = int(line[0]), int(line[1]), int(line[2]), int(line[3]), int(line[4])

char_tokens = input().split()
characters = [int(ch, 16) for ch in char_tokens]

segment_lengths = list(map(int, input().split()))

segment_boundaries = set()
pos = 0
for length in segment_lengths:
    pos += length
    segment_boundaries.add(pos)

for _ in range(Q):
    L, R, B = map(int, input().split())
    
    payload_bytes = 0
    wire_bytes = 0
    num_characters = 0
    last_position = 0
    chunks = 0
    last_chunk_payload = 0
    cause = "LIMIT"
    
    current_chunk_payload = 0
    pos = L
    
    while pos <= R:
        char_code = characters[pos - 1]
        char_bytes = utf8_length(char_code)
        
        if current_chunk_payload > 0 and current_chunk_payload + char_bytes > C:
            chunks += 1
            last_chunk_payload = current_chunk_payload
            current_chunk_payload = 0
        
        cost = char_bytes
        if current_chunk_payload == 0:
            cost += H
        
        if wire_bytes + cost > B:
            cause = "LIMIT"
            break
        
        payload_bytes += char_bytes
        wire_bytes += cost
        current_chunk_payload += char_bytes
        num_characters += 1
        last_position = pos
        
        if pos in segment_boundaries:
            chunks += 1
            last_chunk_payload = current_chunk_payload
            current_chunk_payload = 0
        
        pos += 1
    
    if current_chunk_payload > 0:
        chunks += 1
        last_chunk_payload = current_chunk_payload
    
    if last_position == R:
        cause = "END"
    
    print(f"{payload_bytes} {wire_bytes} {num_characters} {last_position} {chunks} {last_chunk_payload} {cause}")