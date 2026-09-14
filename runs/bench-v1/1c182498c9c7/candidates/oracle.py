def utf8_bytes(codepoint):
    """Return number of UTF-8 bytes needed for a Unicode codepoint"""
    if codepoint <= 0x7F:
        return 1
    elif codepoint <= 0x7FF:
        return 2
    elif codepoint <= 0xFFFF:
        return 3
    else:
        return 4

def read_tokens(count):
    """Read exactly `count` tokens from input, handling line breaks"""
    tokens = []
    while len(tokens) < count:
        tokens.extend(input().split())
    return tokens[:count]

def main():
    line = input().split()
    N, S, Q, C, H = int(line[0]), int(line[1]), int(line[2]), int(line[3]), int(line[4])
    
    # Read characters
    char_tokens = read_tokens(N)
    characters = [int(token, 16) for token in char_tokens]
    
    # Read segment lengths
    segment_tokens = read_tokens(S)
    segment_lengths = [int(token) for token in segment_tokens]
    
    # Calculate segment boundaries (first character of each segment after the first)
    segment_boundaries = set()
    pos = 0
    for length in segment_lengths[:-1]:
        pos += length
        segment_boundaries.add(pos)
    
    # Process requests
    for _ in range(Q):
        parts = input().split()
        L, R, B = int(parts[0]), int(parts[1]), int(parts[2])
        L -= 1  # Convert to 0-indexed
        R -= 1  # Convert to 0-indexed
        
        payload_bytes = 0
        wire_bytes = 0
        chars_transmitted = 0
        last_position = 0
        chunk_count = 0
        last_chunk_payload = 0
        cause = "LIMIT"
        
        current_chunk_payload = 0
        
        for char_idx in range(L, R + 1):
            char_bytes = utf8_bytes(characters[char_idx])
            
            # Determine if we need a new chunk
            need_new_chunk = False
            
            if char_idx in segment_boundaries:
                need_new_chunk = True
            elif current_chunk_payload == 0:
                need_new_chunk = True
            elif current_chunk_payload + char_bytes > C:
                need_new_chunk = True
            
            # Calculate wire bytes needed
            header_cost = H if need_new_chunk else 0
            total_cost = char_bytes + header_cost
            
            if wire_bytes + total_cost > B:
                cause = "LIMIT"
                break
            
            # Add this character to the transmission
            wire_bytes += total_cost
            payload_bytes += char_bytes
            chars_transmitted += 1
            last_position = char_idx + 1  # Convert back to 1-indexed
            
            if need_new_chunk:
                chunk_count += 1
                current_chunk_payload = char_bytes
                last_chunk_payload = char_bytes
            else:
                current_chunk_payload += char_bytes
                last_chunk_payload += char_bytes
        else:
            # Loop completed without break
            cause = "END"
        
        print(f"{payload_bytes} {wire_bytes} {chars_transmitted} {last_position} {chunk_count} {last_chunk_payload} {cause}")

if __name__ == "__main__":
    main()