def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    packets = []
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    spins = 0
    yields = 0
    
    level = 0
    credits = initial_credits
    
    outcome_runs = list(outcomes)
    run_idx = 0
    run_pos = 0
    
    def get_next_outcome():
        nonlocal run_idx, run_pos
        while run_idx < len(outcome_runs):
            kind, count = outcome_runs[run_idx]
            if run_pos < count:
                run_pos += 1
                return kind
            else:
                run_idx += 1
                run_pos = 0
        return "error"
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(("INVALID", 0, 0, 0))
            invalid += 1
            continue
        
        retries = 0
        total_spins = 0
        total_yields = 0
        status = None
        
        while True:
            attempts += 1
            outcome = get_next_outcome()
            
            if outcome == "ok":
                level = max(0, level - 1)
                credits = min(credits + length, credit_cap)
                status = "SENT"
                sent += 1
                break
            elif outcome == "error":
                level = 0
                status = "ERROR"
                errors += 1
                break
            elif outcome == "full":
                old_level = level
                level = min(level + 1, level_cap)
                cost = min(2**old_level, spin_limit)
                if retries < max_retries and credits >= cost:
                    retries += 1
                    credits -= cost
                    total_spins += cost
                    spins += cost
                    if 2**old_level > spin_limit:
                        total_yields += 1
                        yields += 1
                else:
                    status = "DROPPED"
                    dropped += 1
                    break
        
        packets.append((status, retries, total_spins, total_yields))
    
    telemetry = {
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
    
    return {
        "packets": packets,
        "telemetry": telemetry
    }