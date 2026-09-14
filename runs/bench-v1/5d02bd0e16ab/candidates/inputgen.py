import random

def gen(rng, scale):
    if scale == "edge":
        cases = [
            "1 1\nR 0 1",
            "1 2\nR 0 1\nW 1 1 E",
            "1 3\nR 0 1\nW 1 1 E\nP 2",
            "1 4\nR 0 1\nD 1 1\nW 2 1 V 42\nP 3",
            "2 4\nR 0 1\nR 1 2\nW 2 1 E\nW 3 2 E",
            "1 2\nR 0 1\nD 1 10",
            "1 4\nR 0 1\nW 1 1 V 5\nP 2\nP 3",
            "2 6\nR 0 1\nR 0 2\nW 1 1 E\nW 2 2 V -100\nP 3\nP 4",
            "3 5\nR 0 1\nR 0 2\nR 0 3\nW 1 1 E\nP 2",
        ]
        return rng.choice(cases)
    
    elif scale == "small":
        n = rng.randint(1, 5)
        q = rng.randint(5, 30)
        
        lines = [f"{n} {q}"]
        versions = {0: {'reserved': set(), 'published': set()}}
        
        for i in range(1, q + 1):
            b = rng.randint(0, i - 1)
            base = versions[b]
            
            unreserved = [p for p in range(1, n + 1) if p not in base['reserved']]
            publishable = [p for p in base['reserved'] if p not in base['published']]
            
            candidates = []
            if unreserved:
                candidates.append('R')
            if publishable:
                candidates.append('W')
            candidates.extend(['D', 'P'])
            
            op = rng.choice(candidates)
            
            if op == 'R':
                prod = rng.choice(unreserved)
                lines.append(f"R {b} {prod}")
                versions[i] = {
                    'reserved': base['reserved'] | {prod},
                    'published': base['published'].copy()
                }
            elif op == 'W':
                prod = rng.choice(publishable)
                if rng.random() < 0.5:
                    lines.append(f"W {b} {prod} E")
                else:
                    val = rng.randint(-1000, 1000)
                    lines.append(f"W {b} {prod} V {val}")
                versions[i] = {
                    'reserved': base['reserved'].copy(),
                    'published': base['published'] | {prod}
                }
            elif op == 'D':
                k = rng.randint(0, min(100, n * 20))
                lines.append(f"D {b} {k}")
                versions[i] = {
                    'reserved': base['reserved'].copy(),
                    'published': base['published'].copy()
                }
            else:
                lines.append(f"P {b}")
                versions[i] = {
                    'reserved': base['reserved'].copy(),
                    'published': base['published'].copy()
                }
        
        return '\n'.join(lines)
    
    elif scale == "medium":
        n = rng.randint(5, 30)
        q = rng.randint(50, 150)
        
        lines = [f"{n} {q}"]
        versions = {0: {'reserved': set(), 'published': set()}}
        
        for i in range(1, q + 1):
            b = rng.randint(0, i - 1)
            base = versions[b]
            
            unreserved = [p for p in range(1, n + 1) if p not in base['reserved']]
            publishable = [p for p in base['reserved'] if p not in base['published']]
            
            candidates = []
            if unreserved:
                candidates.append('R')
            if publishable:
                candidates.append('W')
            candidates.extend(['D'] * 2)
            candidates.append('P')
            
            op = rng.choice(candidates)
            
            if op == 'R':
                prod = rng.choice(unreserved)
                lines.append(f"R {b} {prod}")
                versions[i] = {
                    'reserved': base['reserved'] | {prod},
                    'published': base['published'].copy()
                }
            elif op == 'W':
                prod = rng.choice(publishable)
                if rng.random() < 0.6:
                    lines.append(f"W {b} {prod} E")
                else:
                    val = rng.randint(-100000, 100000)
                    lines.append(f"W {b} {prod} V {val}")
                versions[i] = {
                    'reserved': base['reserved'].copy(),
                    'published': base['published'] | {prod}
                }
            elif op == 'D':
                k = rng.randint(0, min(10000, n * 500))
                lines.append(f"D {b} {k}")
                versions[i] = {
                    'reserved': base['reserved'].copy(),
                    'published': base['published'].copy()
                }
            else:
                lines.append(f"P {b}")
                versions[i] = {
                    'reserved': base['reserved'].copy(),
                    'published': base['published'].copy()
                }
        
        return '\n'.join(lines)
    
    return "1 1\nR 0 1"