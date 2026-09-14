def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    level = 0
    credits = initial_credits
    
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    total_spins = 0
    total_yields = 0
    
    packets = []
    
    outcome_idx = 0
    run_count = 0
    
    def get_next_outcome():
        nonlocal outcome_idx, run_count
        
        while outcome_idx < len(outcomes):
            kind, count = outcomes[outcome_idx]
            if run_count < count:
                run_count += 1
                return kind
            else:
                outcome_idx += 1
                run_count = 0
        
        return "error"
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(("INVALID", 0, 0, 0))
            invalid += 1
            continue
        
        status = None
        retry_count = 0
        packet_spins = 0
        packet_yields = 0
        
        while True:
            outcome = get_next_outcome()
            attempts += 1
            
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
                
                if retry_count < max_retries and credits >= cost:
                    retry_count += 1
                    credits -= cost
                    packet_spins += cost
                    total_spins += cost
                    
                    if 2**old_level > spin_limit:
                        packet_yields += 1
                        total_yields += 1
                else:
                    status = "DROPPED"
                    dropped += 1
                    break
        
        packets.append((status, retry_count, packet_spins, packet_yields))
    
    telemetry = {
        "sent": sent,
        "dropped": dropped,
        "errors": errors,
        "invalid": invalid,
        "attempts": attempts,
        "spins": total_spins,
        "yields": total_yields,
        "final_level": level,
        "final_credits": credits
    }
    
    return {
        "packets": packets,
        "telemetry": telemetry
    }