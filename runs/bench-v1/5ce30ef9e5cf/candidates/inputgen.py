def gen(rng, scale):
    if scale == "edge":
        # Minimal: 1 object, 1 cell, 1 query
        return "1 1 1\n1 1 I 0\nSTACK"
    
    if scale == "small":
        n = rng.randint(2, 8)
        k = rng.randint(n, min(20, n * 2))
        q = rng.randint(3, 15)
    else:  # medium
        n = rng.randint(8, 60)
        k = rng.randint(n, min(180, n * 2))
        q = rng.randint(10, 60)
    
    lines = [f"{n} {k} {q}"]
    
    used = set()
    
    # Build a chain of object references: 1 -> 2 -> 3 -> ... -> n
    # This ensures all paths of length 2 are resolvable
    for i in range(1, n):
        lines.append(f"{i} {i} O {i+1}")
        used.add((i, i))
    
    # Last object has an integer terminal cell
    lines.append(f"{n} {n} I 0")
    used.add((n, n))
    
    # Fill remaining K cells with integers using high attribute numbers
    while len(used) < k:
        obj = rng.randint(1, n)
        attr = rng.randint(1001, 9999)
        if (obj, attr) not in used:
            value = rng.randint(-10000, 10000)
            lines.append(f"{obj} {attr} I {value}")
            used.add((obj, attr))
    
    active_acts = []
    used_ids = set()
    
    # Generate Q commands
    for _ in range(q):
        can_start = len(used_ids) < q
        can_stop = bool(active_acts)
        
        # Weighted command selection
        if can_start and rng.random() < 0.3:
            # START: new activation
            for aid in range(1, q + 1):
                if aid not in used_ids:
                    act_id = aid
                    break
            used_ids.add(act_id)
            active_acts.append(act_id)
            
            m = rng.randint(1, min(3, k))
            cmd = f"START {act_id} {m}"
            
            # Add M replacements with path length 1 (direct access)
            for _ in range(m):
                obj = rng.randint(1, n)
                attr = rng.randint(1001, 9999)
                value = rng.randint(-1000, 1000)
                cmd += f" {obj} 1 {attr} I {value}"
            
            lines.append(cmd)
        
        elif rng.random() < 0.5:
            # GET: read a cell
            obj = rng.randint(1, n)
            attr = rng.randint(1, 9999)
            lines.append(f"GET {obj} 1 {attr}")
        
        elif can_stop and rng.random() < 0.7:
            # STOP: restore one activation
            idx = rng.randint(0, len(active_acts) - 1)
            lines.append(f"STOP {active_acts.pop(idx)}")
        
        elif can_stop and rng.random() < 0.9:
            # STOPALL: restore all
            lines.append("STOPALL")
            active_acts.clear()
        
        else:
            # STACK: query activation stack
            lines.append("STACK")
    
    return "\n".join(lines)