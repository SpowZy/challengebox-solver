def gen(rng, scale):
    def utf8_width(code):
        """Return UTF-8 byte width of a Unicode scalar."""
        if code <= 0x7F:
            return 1
        elif code <= 0x7FF:
            return 2
        elif code <= 0xFFFF:
            return 3
        else:
            return 4
    
    def random_char():
        """Generate a valid Unicode scalar value (not a surrogate)."""
        choice = rng.choices([1, 2, 3, 4], weights=[65, 20, 10, 5])[0]
        if choice == 1:
            return rng.randint(0x00, 0x7F)
        elif choice == 2:
            return rng.randint(0x80, 0x7FF)
        elif choice == 3:
            code = rng.randint(0x800, 0xFFFF)
            while 0xD800 <= code <= 0xDFFF:
                code = rng.randint(0x800, 0xFFFF)
            return code
        else:
            return rng.randint(0x10000, 0x10FFFF)
    
    if scale == "edge":
        # Degenerate cases: single element, empty budget, segment boundaries
        test_cases = [
            {
                'N': 1, 'S': 1, 'Q': 3, 'C': 20, 'H': 2,
                'chars': [0x41],
                'segments': [1],
                'queries': [(1, 1, 0), (1, 1, 2), (1, 1, 3)]
            },
            {
                'N': 2, 'S': 2, 'Q': 3, 'C': 10, 'H': 1,
                'chars': [0x41, 0x42],
                'segments': [1, 1],
                'queries': [(1, 1, 2), (1, 2, 3), (1, 2, 100)]
            },
            {
                'N': 3, 'S': 3, 'Q': 2, 'C': 5, 'H': 1,
                'chars': [0x41, 0x42, 0x43],
                'segments': [1, 1, 1],
                'queries': [(1, 3, 10), (1, 3, 0)]
            },
            {
                'N': 2, 'S': 1, 'Q': 2, 'C': 100, 'H': 5,
                'chars': [0x1F600, 0x1F601],
                'segments': [2],
                'queries': [(1, 1, 4), (1, 2, 15)]
            },
        ]
        case = rng.choice(test_cases)
        
    elif scale == "small":
        N = rng.randint(3, 25)
        S = rng.randint(1, min(N, 5))
        Q = rng.randint(2, 12)
        C = rng.randint(5, 40)
        H = rng.randint(0, 8)
        
        chars = [random_char() for _ in range(N)]
        
        # Distribute N elements into S segments
        segments = [1] * S
        for _ in range(N - S):
            segments[rng.randint(0, S - 1)] += 1
        rng.shuffle(segments)
        
        queries = []
        for _ in range(Q):
            L = rng.randint(1, N)
            R = rng.randint(L, N)
            B = rng.randint(0, 80)
            queries.append((L, R, B))
        
        case = {
            'N': N, 'S': S, 'Q': Q, 'C': C, 'H': H,
            'chars': chars, 'segments': segments, 'queries': queries
        }
        
    else:  # medium
        N = rng.randint(60, 250)
        S = rng.randint(2, min(N, 25))
        Q = rng.randint(8, 35)
        C = rng.randint(15, 150)
        H = rng.randint(0, 20)
        
        chars = [random_char() for _ in range(N)]
        
        segments = [1] * S
        for _ in range(N - S):
            segments[rng.randint(0, S - 1)] += 1
        rng.shuffle(segments)
        
        queries = []
        for _ in range(Q):
            L = rng.randint(1, N)
            R = rng.randint(L, N)
            B = rng.randint(0, 200)
            queries.append((L, R, B))
        
        case = {
            'N': N, 'S': S, 'Q': Q, 'C': C, 'H': H,
            'chars': chars, 'segments': segments, 'queries': queries
        }
    
    # Format input according to spec
    lines = []
    lines.append(f"{case['N']} {case['S']} {case['Q']} {case['C']} {case['H']}")
    lines.append(' '.join(f'{c:X}' for c in case['chars']))
    lines.append(' '.join(map(str, case['segments'])))
    for L, R, B in case['queries']:
        lines.append(f"{L} {R} {B}")
    
    return '\n'.join(lines)