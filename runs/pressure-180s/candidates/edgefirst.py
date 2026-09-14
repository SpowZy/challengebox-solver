def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    level = 0
    credits = initial_credits
    
    packets = []
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    total_spins = 0
    total_yields = 0
    
    outcome_run_idx = 0
    consumed_from_current_run = 0
    
    def get_next_outcome():
        nonlocal outcome_run_idx, consumed_from_current_run
        
        while outcome_run_idx < len(outcomes):
            kind, count = outcomes[outcome_run_idx]
            
            if consumed_from_current_run < count:
                consumed_from_current_run += 1
                return kind
            else:
                outcome_run_idx += 1
                consumed_from_current_run = 0
        
        return "error"
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(("INVALID", 0, 0, 0))
            invalid += 1
            continue
        
        status = None
        retries = 0
        packet_spins = 0
        packet_yields = 0
        
        while True:
            outcome = get_next_outcome()
            attempts += 1
            
            if outcome == "ok":
                level = max(0, level - 1)
                credits = min(credit_cap, credits + length)
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
                level = min(level_cap, level + 1)
                cost = min(2**old_level, spin_limit)
                
                if retries < max_retries and credits >= cost:
                    retries += 1
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
        
        packets.append((status, retries, packet_spins, packet_yields))
    
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