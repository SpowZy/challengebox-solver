def gen(rng, scale):
    # ASCII letters and digits (no whitespace bytes)
    ascii_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    
    # Unicode characters for variety
    emoji_list = [chr(0x1F600), chr(0x1F601), chr(0x1F602), chr(0x2600), chr(0x2601)]
    combining_list = [chr(0x0301), chr(0x0302), chr(0x0303), chr(0x20D0), chr(0x20D1)]
    regional_list = [chr(0x1F1E6), chr(0x1F1E7), chr(0x1F1E8)]
    
    if scale == "edge":
        # Degenerate and boundary cases
        options = [
            'A',
            'AA',
            'ABC',
            chr(0x1F600),
            chr(0x1F600) + chr(0x1F601),
            chr(0x1F600) + chr(0x0301),
            'A' + chr(0x0301),
            'A' + chr(0x0301) + 'B',
            'ABCD',
        ]
        s = rng.choice(options)
        
        q = rng.randint(1, 5)
        queries = []
        for _ in range(q):
            query_type = rng.choice([1, 2])
            # Negative indices, reversed ranges, boundary values
            a = rng.randint(-12, 12)
            b = rng.randint(-12, 12)
            queries.append(f"{query_type} {a} {b}")
    
    elif scale == "small":
        # Small string with few elements
        s_parts = []
        num_parts = rng.randint(3, 10)
        for _ in range(num_parts):
            char_type = rng.randint(0, 9)
            if char_type < 6:
                # ASCII
                s_parts.append(rng.choice(ascii_chars))
            elif char_type < 8:
                # Emoji
                s_parts.append(rng.choice(emoji_list))
            else:
                # Base + combining mark
                base_choice = rng.randint(0, 4)
                if base_choice < 3:
                    base = rng.choice(ascii_chars)
                else:
                    base = rng.choice(emoji_list)
                combining = rng.choice(combining_list)
                s_parts.append(base + combining)
        
        s = ''.join(s_parts)
        
        q = rng.randint(3, 10)
        queries = []
        for _ in range(q):
            query_type = rng.choice([1, 2])
            a = rng.randint(-25, 25)
            b = rng.randint(-25, 25)
            queries.append(f"{query_type} {a} {b}")
    
    else:  # medium
        # Medium string with tens of elements
        s_parts = []
        num_parts = rng.randint(15, 35)
        for _ in range(num_parts):
            char_type = rng.randint(0, 9)
            if char_type < 6:
                # ASCII
                s_parts.append(rng.choice(ascii_chars))
            elif char_type < 8:
                # Emoji or regional indicator
                if rng.random() < 0.8:
                    s_parts.append(rng.choice(emoji_list))
                else:
                    s_parts.append(rng.choice(regional_list))
            else:
                # Base + combining mark
                base_choice = rng.randint(0, 4)
                if base_choice < 3:
                    base = rng.choice(ascii_chars)
                else:
                    base = rng.choice(emoji_list)
                combining = rng.choice(combining_list)
                s_parts.append(base + combining)
        
        s = ''.join(s_parts)
        
        q = rng.randint(10, 30)
        queries = []
        for _ in range(q):
            query_type = rng.choice([1, 2])
            a = rng.randint(-60, 60)
            b = rng.randint(-60, 60)
            queries.append(f"{query_type} {a} {b}")
    
    # Format output: S, Q, then Q queries
    lines = [s, str(q)]
    lines.extend(queries)
    return '\n'.join(lines)