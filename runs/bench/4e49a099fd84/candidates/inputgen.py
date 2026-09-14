import random

def gen(rng, scale):
    if scale == "edge":
        # Degenerate cases: single char, minimal queries, boundary indices
        cases = [
            ("A", [(1, 0, 0), (2, 0, 0)]),
            ("AB", [(1, 0, 1), (1, 1, 1), (1, 0, 0), (2, 0, 1)]),
            ("ABC", [(1, 0, 2), (1, 1, 1), (1, -1, 0), (2, 0, 1)]),
            ("ABCD", [(1, 0, 3), (1, -2, -1), (1, -1, -1), (2, 1, 2)]),
            ("ABCDE", [(1, 0, 4), (1, -3, 2), (2, 0, 1), (2, -1, -2)]),
        ]
        
        s, all_queries = rng.choice(cases)
        
        num_q = rng.randint(1, min(3, len(all_queries)))
        queries = rng.sample(all_queries, num_q)
        
        result = [s, str(num_q)]
        for qtype, a, b in queries:
            result.append(f"{qtype} {a} {b}")
        
        return "\n".join(result)
    
    elif scale == "small":
        # Small: 3-10 characters, simple ASCII
        length = rng.randint(3, 10)
        s = "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(length))
        
        num_q = rng.randint(2, 10)
        result = [s, str(num_q)]
        
        for _ in range(num_q):
            qtype = rng.randint(1, 2)
            # Include out-of-range indices to test resolution and clamping
            a = rng.randint(-length - 2, length + 2)
            b = rng.randint(-length - 2, length + 2)
            result.append(f"{qtype} {a} {b}")
        
        return "\n".join(result)
    
    else:  # medium
        # Medium: 20-50 characters, mix ASCII and accented
        length = rng.randint(20, 50)
        charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789àáâãäåèéêëìíîïòóôõöùúûüý"
        s = "".join(rng.choice(charset) for _ in range(length))
        
        num_q = rng.randint(15, 30)
        result = [s, str(num_q)]
        
        for _ in range(num_q):
            qtype = rng.randint(1, 2)
            a = rng.randint(-length - 3, length + 3)
            b = rng.randint(-length - 3, length + 3)
            result.append(f"{qtype} {a} {b}")
        
        return "\n".join(result)