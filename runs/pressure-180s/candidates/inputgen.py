def gen(rng, scale):
    if scale == "edge":
        choice = rng.randint(0, 9)
        
        if choice == 0:
            # Empty inputs
            return ([], [], 0, 0, 1, 0, 0)
        elif choice == 1:
            # Single valid packet, ok outcome
            return ([100], [("ok", 1)], 0, 0, 1, 0, 100)
        elif choice == 2:
            # Single invalid packet (length 0)
            return ([0], [], 0, 0, 1, 0, 0)
        elif choice == 3:
            # Single invalid packet (length 65536)
            return ([65536], [], 0, 0, 1, 0, 0)
        elif choice == 4:
            # Valid packet with error outcome
            return ([100], [("error", 1)], 0, 0, 1, 0, 0)
        elif choice == 5:
            # Valid packet with full, max_retries = 0 blocks retry
            return ([100], [("full", 1)], 0, 60, 1, 0, 0)
        elif choice == 6:
            # Valid packet with full, retries possible
            return ([100], [("full", 1)], 10, 60, 1, 100, 1000)
        elif choice == 7:
            # Level cap = 0 (congestion cannot grow)
            return ([100, 200], [("ok", 1), ("full", 1)], 1, 0, 1, 10, 1000)
        elif choice == 8:
            # Mixed valid and invalid packets
            return ([100, 0, 200], [("ok", 1), ("error", 1)], 0, 10, 1, 0, 1000)
        else:
            # Extreme valid values
            return ([1, 65535], [("ok", 1), ("full", 1)], 10**18, 60, 10**18, 10**30, 10**30)
    
    elif scale == "small":
        # Generate 1-5 valid packets with some invalid ones
        num_valid = rng.randint(1, 5)
        num_invalid = rng.randint(0, 2)
        
        lengths = [rng.randint(1, 65535) for _ in range(num_valid)]
        for _ in range(num_invalid):
            lengths.append(rng.choice([0, 65536]))
        
        rng.shuffle(lengths)
        
        # Generate outcome runs covering all valid packets
        outcomes = []
        remaining = num_valid
        while remaining > 0:
            kind = rng.choice(["ok", "full", "error"])
            count = rng.randint(1, remaining)
            outcomes.append((kind, count))
            remaining -= count
        
        max_retries = rng.choice([0, 1, 5, 10])
        level_cap = rng.choice([0, 1, 5, 10, 30, 60])
        spin_limit = rng.choice([1, 2, 10, 100, 1000])
        credit_cap = rng.choice([0, 10, 100, 1000])
        initial_credits = rng.randint(0, credit_cap)
        
        return (lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap)
    
    else:  # scale == "medium"
        # Generate 10-30 valid packets with some invalid ones
        num_valid = rng.randint(10, 30)
        num_invalid = rng.randint(0, 5)
        
        lengths = [rng.randint(1, 65535) for _ in range(num_valid)]
        for _ in range(num_invalid):
            lengths.append(rng.choice([0, 65536]))
        
        rng.shuffle(lengths)
        
        # Generate multiple outcome runs
        outcomes = []
        remaining = num_valid
        while remaining > 0:
            kind = rng.choice(["ok", "full", "error"])
            count = rng.randint(1, remaining)
            outcomes.append((kind, count))
            remaining -= count
        
        max_retries = rng.choice([0, 1, 5, 10, 100])
        level_cap = rng.choice([1, 5, 10, 30, 60])
        spin_limit = rng.choice([1, 2, 10, 100, 1000])
        credit_cap = rng.choice([0, 100, 1000, 10000])
        initial_credits = rng.randint(0, credit_cap)
        
        return (lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap)