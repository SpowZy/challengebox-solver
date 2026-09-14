import random

def gen(rng, scale):
    if scale == "edge":
        cases = [
            # Empty input
            ([], [], 0, 0, 1, 0, 0),
            
            # Single valid packet with ok outcome
            ([1], [("ok", 1)], 0, 0, 1, 0, 1),
            
            # Single invalid packet (too small)
            ([0], [("ok", 1)], 0, 0, 1, 0, 0),
            
            # Single invalid packet (too large)
            ([65536], [("ok", 1)], 0, 0, 1, 0, 0),
            
            # Boundary valid packet lengths
            ([1, 65535], [("ok", 2)], 0, 0, 1, 0, 131070),
            
            # Repeated identical packets
            ([100, 100, 100], [("ok", 3)], 0, 0, 1, 0, 300),
            
            # Error outcome
            ([100], [("error", 1)], 0, 0, 1, 0, 0),
            
            # Full outcome reaching max level_cap
            ([1], [("full", 60), ("ok", 1)], 0, 60, 1, 10**30, 10**30),
            
            # Full outcome with extreme spin_limit
            ([1], [("full", 1)], 1, 10, 10**18, 10**30, 10**30),
            
            # Maximum max_retries
            ([1], [("full", 1)], 10**18, 1, 1, 10**30, 10**30),
            
            # Mixed outcomes with invalid packet
            ([10, 0, 20], [("ok", 1), ("full", 1), ("error", 1)], 1, 5, 100, 1000, 10000),
        ]
        
        choice = rng.randint(0, len(cases) - 1)
        case = cases[choice]
        return list(case)
        
    elif scale == "small":
        num_packets = rng.randint(2, 15)
        
        # Mix of valid and invalid packets
        lengths = []
        for _ in range(num_packets):
            if rng.random() < 0.85:
                lengths.append(rng.randint(1, 65535))
            else:
                lengths.append(rng.choice([0, -1, 65536, 100000]))
        
        # Generate outcome runs
        num_outcome_runs = rng.randint(1, 5)
        outcomes = []
        total_outcomes = 0
        
        for i in range(num_outcome_runs):
            kind = rng.choice(["ok", "full", "error"])
            
            if i < num_outcome_runs - 1:
                remaining = max(1, num_packets - total_outcomes)
                count = rng.randint(1, max(1, min(remaining, 10)))
            else:
                remaining = num_packets - total_outcomes
                count = rng.randint(1, max(1, remaining + rng.randint(1, 5)))
            
            outcomes.append((kind, count))
            total_outcomes += count
        
        max_retries = rng.randint(0, 15)
        level_cap = rng.randint(0, 30)
        spin_limit = rng.randint(1, 100000)
        initial_credits = rng.randint(0, 50000)
        credit_cap = rng.randint(initial_credits, 500000)
        
        return [lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap]
        
    else:  # medium
        num_packets = rng.randint(25, 150)
        
        # Mix of valid and invalid packets
        lengths = []
        for _ in range(num_packets):
            if rng.random() < 0.9:
                lengths.append(rng.randint(1, 65535))
            else:
                lengths.append(rng.choice([0, -1, 65536, 100000]))
        
        # Generate outcome runs
        num_outcome_runs = rng.randint(3, 15)
        outcomes = []
        total_outcomes = 0
        
        for i in range(num_outcome_runs):
            kind = rng.choice(["ok", "full", "error"])
            
            if i < num_outcome_runs - 1:
                remaining = num_packets - total_outcomes
                max_count = max(1, min(remaining, rng.randint(10, 40)))
                count = rng.randint(1, max_count)
            else:
                remaining = num_packets - total_outcomes
                count = rng.randint(1, max(1, remaining + rng.randint(1, 20)))
            
            outcomes.append((kind, count))
            total_outcomes += count
        
        max_retries = rng.randint(0, 200)
        level_cap = rng.randint(5, 50)
        spin_limit = rng.randint(1, 10000000)
        initial_credits = rng.randint(0, 5000000)
        credit_cap = rng.randint(initial_credits, 50000000)
        
        return [lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap]