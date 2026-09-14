def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    outcome_runs = outcomes
    outcome_run_idx = 0
    outcome_count_in_run = 0
    
    def get_next_outcome():
        nonlocal outcome_run_idx, outcome_count_in_run
        
        if outcome_run_idx >= len(outcome_runs):
            return "error"
        
        kind, count = outcome_runs[outcome_run_idx]
        outcome_count_in_run += 1
        
        if outcome_count_in_run >= count:
            outcome_run_idx += 1
            outcome_count_in_run = 0
        
        return kind
    
    level = 0
    credits = initial_credits
    
    packets = []
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    spins = 0
    yields = 0
    
    for length in lengths:
        if not (1 <= length <= 65535):
            packets.append(("INVALID", 0, 0, 0))
            invalid += 1
            continue
        
        retries = 0
        packet_spins = 0
        packet_yields = 0
        status = None
        
        while True:
            outcome = get_next_outcome()
            attempts += 1
            
            if outcome == "ok":
                status = "SENT"
                level = max(0, level - 1)
                credits = min(credits + length, credit_cap)
                break
            elif outcome == "error":
                status = "ERROR"
                level = 0
                break
            elif outcome == "full":
                old_level = level
                level = min(level + 1, level_cap)
                cost = min(2**old_level, spin_limit)
                
                if retries < max_retries and credits >= cost:
                    retries += 1
                    credits -= cost
                    packet_spins += cost
                    if 2**old_level > spin_limit:
                        packet_yields += 1
                else:
                    status = "DROPPED"
                    break
        
        packets.append((status, retries, packet_spins, packet_yields))
        sent += status == "SENT"
        dropped += status == "DROPPED"
        errors += status == "ERROR"
        spins += packet_spins
        yields += packet_yields
    
    return {
        "packets": packets,
        "telemetry": {
            "sent": sent,
            "dropped": dropped,
            "errors": errors,
            "invalid": invalid,
            "attempts": attempts,
            "spins": spins,
            "yields": yields,
            "final_level": level,
            "final_credits": credits
        }
    }