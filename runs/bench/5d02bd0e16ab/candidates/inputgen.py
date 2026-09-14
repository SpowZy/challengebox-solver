def gen(rng, scale):
    if scale == "edge":
        case = rng.randint(0, 2)
        
        if case == 0:
            # Single producer, basic flow
            n = 1
            lines = [f"{n} 3"]
            lines.append("R 0 1")
            lines.append("W 1 1 E")
            lines.append("P 2")
        
        elif case == 1:
            # Empty drain with no publications
            n = 1
            lines = [f"{n} 1"]
            lines.append("P 0")
        
        else:
            # Multiple producers, all completions
            n = 2
            lines = [f"{n} 6"]
            lines.append("R 0 1")
            lines.append("R 1 2")
            lines.append("W 2 1 E")
            lines.append("W 3 2 E")
            lines.append("D 4 0")
            lines.append("P 5")
        
        return "\n".join(lines)
    
    elif scale == "small":
        n = rng.randint(1, 5)
        operations = []
        
        reserved = [False] * (n + 1)
        published = [False] * (n + 1)
        p = 0
        version = 0
        
        for _ in range(rng.randint(5, 30)):
            choices = []
            
            if p < n:
                unreserved = [i for i in range(1, n + 1) if not reserved[i]]
                if unreserved:
                    choices.append(('R', unreserved))
            
            publishable = [i for i in range(1, n + 1) if reserved[i] and not published[i]]
            if publishable:
                choices.append(('W', publishable))
            
            choices.extend([('D', None), ('P', None)])
            
            op_type, targets = rng.choice(choices)
            
            if op_type == 'R':
                s = rng.choice(targets)
                operations.append(f"R {version} {s}")
                reserved[s] = True
                p += 1
            
            elif op_type == 'W':
                s = rng.choice(targets)
                if rng.random() < 0.5:
                    operations.append(f"W {version} {s} E")
                else:
                    x = rng.randint(-100000, 100000)
                    operations.append(f"W {version} {s} V {x}")
                published[s] = True
            
            elif op_type == 'D':
                k = rng.randint(0, 1000)
                operations.append(f"D {version} {k}")
            
            elif op_type == 'P':
                operations.append(f"P {version}")
            
            version += 1
        
        lines = [f"{n} {len(operations)}"]
        lines.extend(operations)
        return "\n".join(lines)
    
    else:  # medium
        n = rng.randint(10, 150)
        
        reserved = [False] * (n + 1)
        published = [False] * (n + 1)
        p = 0
        operations = []
        version = 0
        
        for _ in range(rng.randint(100, 400)):
            choices = []
            
            if p < n:
                unreserved = [i for i in range(1, n + 1) if not reserved[i]]
                if unreserved:
                    choices.append(('R', unreserved))
            
            publishable = [i for i in range(1, n + 1) if reserved[i] and not published[i]]
            if publishable:
                choices.append(('W', publishable))
            
            choices.extend([('D', None), ('P', None)])
            
            op_type, targets = rng.choice(choices)
            
            if op_type == 'R':
                s = rng.choice(targets)
                operations.append(f"R {version} {s}")
                reserved[s] = True
                p += 1
            
            elif op_type == 'W':
                s = rng.choice(targets)
                if rng.random() < 0.5:
                    operations.append(f"W {version} {s} E")
                else:
                    x = rng.randint(-10**9, 10**9)
                    operations.append(f"W {version} {s} V {x}")
                published[s] = True
            
            elif op_type == 'D':
                k = rng.randint(0, 10000)
                operations.append(f"D {version} {k}")
            
            elif op_type == 'P':
                operations.append(f"P {version}")
            
            version += 1
        
        lines = [f"{n} {len(operations)}"]
        lines.extend(operations)
        return "\n".join(lines)