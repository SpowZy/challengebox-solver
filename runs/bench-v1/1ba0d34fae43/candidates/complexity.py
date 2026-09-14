def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    packets = []
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    total_spins = 0
    total_yields = 0
    
    level = 0
    credits = initial_credits
    
    outcome_index = 0
    outcome_pos = 0
    
    def get_next_outcome():
        nonlocal outcome_index, outcome_pos
        
        while outcome_index < len(outcomes):
            kind, count = outcomes[outcome_index]
            if outcome_pos < count:
                outcome_pos += 1
                return kind
            outcome_index += 1
            outcome_pos = 0
        
        return "error"
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(("INVALID", 0, 0, 0))
            invalid += 1
            continue
        
        retries = 0
        spins = 0
        yields_count = 0
        status = None
        
        while True:
            attempts += 1
            outcome = get_next_outcome()
            
            if outcome == "ok":
                status = "SENT"
                sent += 1
                level = max(0, level - 1)
                credits = min(credits + length, credit_cap)
                break
            elif outcome == "error":
                status = "ERROR"
                errors += 1
                level = 0
                break
            elif outcome == "full":
                old_level = level
                level = min(level + 1, level_cap)
                cost = min(2**old_level, spin_limit)
                
                if retries < max_retries and credits >= cost:
                    retries += 1
                    credits -= cost
                    spins += cost
                    total_spins += cost
                    if 2**old_level > spin_limit:
                        yields_count += 1
                        total_yields += 1
                else:
                    status = "DROPPED"
                    dropped += 1
                    break
        
        packets.append((status, retries, spins, yields_count))
    
    return {
        "packets": packets,
        "telemetry": {
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
    }