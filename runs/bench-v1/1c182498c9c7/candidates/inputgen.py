def gen(rng, scale):
    def utf8_size(c):
        if c <= 0x7F:
            return 1
        elif c <= 0x7FF:
            return 2
        elif c <= 0xFFFF:
            return 3
        else:
            return 4
    
    def random_char(rng):
        """Generate a valid Unicode scalar value (not a surrogate)."""
        choice = rng.random()
        if choice < 0.4:
            return rng.randint(0, 0x7F)
        elif choice < 0.7:
            return rng.randint(0x80, 0x7FF)
        elif choice < 0.9:
            # Avoid surrogates D800..DFFF
            if rng.random() < 0.5:
                return rng.randint(0x800, 0xD7FF)
            else:
                return rng.randint(0xE000, 0xFFFF)
        else:
            return rng.randint(0x10000, 0x10FFFF)
    
    if scale == "edge":
        cases = [
            {'N': 1, 'S': 1, 'Q': 1, 'C': 10, 'H': 0,
             'chars': [0x41], 'segments': [1], 'requests': [(1, 1, 10)]},
            {'N': 1, 'S': 1, 'Q': 1, 'C': 10, 'H': 0,
             'chars': [0x41], 'segments': [1], 'requests': [(1, 1, 0)]},
            {'N': 1, 'S': 1, 'Q': 1, 'C': 100, 'H': 10,
             'chars': [0x41], 'segments': [1], 'requests': [(1, 1, 5)]},
            {'N': 1, 'S': 1, 'Q': 1, 'C': 10, 'H': 0,
             'chars': [0x10FFFF], 'segments': [1], 'requests': [(1, 1, 10)]},
            {'N': 4, 'S': 2, 'Q': 1, 'C': 100, 'H': 1,
             'chars': [0x41, 0x42, 0x43, 0x44], 'segments': [2, 2], 'requests': [(1, 4, 1000)]},
            {'N': 2, 'S': 1, 'Q': 1, 'C': 1000000000000, 'H': 1000000000000,
             'chars': [0x41, 0x42], 'segments': [2], 'requests': [(1, 2, 2000000000000)]},
            {'N': 2, 'S': 1, 'Q': 1, 'C': 100, 'H': 2,
             'chars': [0x41, 0x42], 'segments': [2], 'requests': [(1, 2, 3)]},
            {'N': 5, 'S': 5, 'Q': 1, 'C': 100, 'H': 1,
             'chars': [0x41, 0x42, 0x43, 0x44, 0x45], 'segments': [1, 1, 1, 1, 1], 'requests': [(1, 5, 1000)]},
            {'N': 3, 'S': 1, 'Q': 1, 'C': 100, 'H': 0,
             'chars': [0x100, 0x800, 0x10000], 'segments': [3], 'requests': [(1, 3, 15)]},
            {'N': 1, 'S': 1, 'Q': 3, 'C': 10, 'H': 0,
             'chars': [0x41], 'segments': [1], 'requests': [(1, 1, 100), (1, 1, 0), (1, 1, 1)]},
        ]
        case_data = rng.choice(cases)
    
    elif scale == "small":
        N = rng.randint(2, 40)
        S = rng.randint(1, min(N, 15))
        Q = rng.randint(1, 10)
        C = rng.randint(4, 10000)
        H = rng.randint(0, 200)
        
        chars = [random_char(rng) for _ in range(N)]
        
        segments = []
        remaining = N
        for i in range(S - 1):
            seg = rng.randint(1, remaining)
            segments.append(seg)
            remaining -= seg
        segments.append(remaining)
        
        requests = []
        for _ in range(Q):
            l = rng.randint(1, N)
            r = rng.randint(l, N)
            max_payload = sum(utf8_size(chars[i - 1]) for i in range(l, r + 1))
            max_wire = max_payload + H * (r - l + 1)
            b = rng.randint(0, max_wire + 1000)
            requests.append((l, r, b))
        
        case_data = {'N': N, 'S': S, 'Q': Q, 'C': C, 'H': H,
                     'chars': chars, 'segments': segments, 'requests': requests}
    
    elif scale == "medium":
        N = rng.randint(60, 400)
        S = rng.randint(2, min(N // 3, 50))
        Q = rng.randint(5, 50)
        C = rng.randint(4, 1000000)
        H = rng.randint(0, 10000)
        
        chars = [random_char(rng) for _ in range(N)]
        
        segments = []
        remaining = N
        for i in range(S - 1):
            seg = rng.randint(1, remaining)
            segments.append(seg)
            remaining -= seg
        segments.append(remaining)
        
        requests = []
        for _ in range(Q):
            l = rng.randint(1, N)
            r = rng.randint(l, N)
            max_payload = sum(utf8_size(chars[i - 1]) for i in range(l, r + 1))
            max_wire = max_payload + H * (r - l + 1)
            b = rng.randint(0, max_wire + 10000)
            requests.append((l, r, b))
        
        case_data = {'N': N, 'S': S, 'Q': Q, 'C': C, 'H': H,
                     'chars': chars, 'segments': segments, 'requests': requests}
    
    lines = []
    lines.append(f"{case_data['N']} {case_data['S']} {case_data['Q']} {case_data['C']} {case_data['H']}")
    lines.append(' '.join(f"{c:X}" for c in case_data['chars']))
    lines.append(' '.join(str(s) for s in case_data['segments']))
    for l, r, b in case_data['requests']:
        lines.append(f"{l} {r} {b}")
    
    return '\n'.join(lines)