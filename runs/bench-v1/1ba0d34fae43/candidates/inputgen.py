def gen(rng, scale):
    if scale == "edge":
        cases = [
            # Empty inputs
            [[], [], 0, 0, 1, 0, 0],
            
            # Single packet, single outcome
            [[1], [("ok", 1)], 0, 0, 1, 0, 1],
            [[65535], [("ok", 1)], 0, 0, 1, 0, 65535],
            
            # Invalid packets (outside [1, 65535])
            [[0], [("ok", 1)], 0, 0, 1, 0, 1],
            [[65536], [("ok", 1)], 0, 0, 1, 0, 1],
            [[-1], [("ok", 1)], 0, 0, 1, 0, 1],
            
            # Outcomes exhausted before all packets processed
            [[1, 2, 3], [("ok", 1)], 0, 10, 1, 0, 100],
            
            # All error outcomes
            [[1, 2], [("error", 2)], 0, 10, 1, 0, 100],
            
            # level_cap = 0 (no congestion level increase)
            [[1], [("full", 1), ("ok", 1)], 5, 0, 1, 10, 10],
            
            # credit_cap = 0 (no credits available for retries)
            [[1], [("full", 1), ("ok", 1)], 5, 10, 1, 0, 0],
            
            # spin_limit = 1 (minimum spinning)
            [[1, 2], [("full", 1), ("ok", 1), ("full", 1), ("ok", 1)], 5, 10, 1, 10, 10],
            
            # max_retries = 0 (no retries possible)
            [[1], [("full", 1), ("ok", 1)], 0, 10, 100, 100, 100],
            
            # Mixed valid and invalid packets
            [[1, 0, 65535, 65536, 100], [("ok", 5)], 0, 10, 1, 0, 100],
        ]
        return cases[rng.randint(0, len(cases) - 1)]
    
    elif scale == "small":
        num_packets = rng.randint(2, 6)
        
        # Generate packet lengths with some invalid ones
        lengths = []
        num_invalid = min(rng.randint(0, 2), num_packets)
        invalid_positions = set(rng.sample(range(num_packets), num_invalid)) if num_invalid > 0 else set()
        
        for i in range(num_packets):
            if i in invalid_positions:
                lengths.append(rng.choice([0, 65536, -1]))
            else:
                lengths.append(rng.randint(1, 65535))
        
        num_valid = num_packets - len(invalid_positions)
        
        # Generate outcomes
        total_attempts = num_valid + rng.randint(0, num_valid + 2)
        outcomes = []
        remaining = total_attempts
        
        while remaining > 0:
            kind = rng.choice(["ok", "error", "full"])
            count = min(rng.randint(1, max(1, min(3, remaining))), remaining)
            outcomes.append((kind, count))
            remaining -= count
        
        max_retries = rng.randint(0, 4)
        level_cap = rng.randint(0, 10)
        spin_limit = rng.randint(1, 100)
        credit_cap = rng.randint(10, 500)
        initial_credits = rng.randint(0, credit_cap)
        
        return [lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap]
    
    else:  # medium
        num_packets = rng.randint(20, 50)
        
        # Generate packet lengths
        lengths = []
        num_invalid = min(rng.randint(0, max(1, num_packets // 10)), num_packets)
        invalid_positions = set(rng.sample(range(num_packets), num_invalid)) if num_invalid > 0 else set()
        
        for i in range(num_packets):
            if i in invalid_positions:
                lengths.append(rng.choice([0, 65536]))
            else:
                lengths.append(rng.randint(1, 65535))
        
        num_valid = num_packets - len(invalid_positions)
        
        # Generate outcomes with variation in coverage
        total_attempts = num_valid + rng.randint(num_valid // 2, num_valid * 2)
        outcomes = []
        remaining = total_attempts
        
        while remaining > 0:
            kind = rng.choice(["ok", "error", "full"])
            count = min(rng.randint(1, max(1, min(8, remaining))), remaining)
            outcomes.append((kind, count))
            remaining -= count
        
        max_retries = rng.randint(1, 15)
        level_cap = rng.randint(2, 30)
        spin_limit = rng.randint(1, 5000)
        credit_cap = rng.randint(1000, 50000)
        initial_credits = rng.randint(0, credit_cap)
        
        return [lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap]