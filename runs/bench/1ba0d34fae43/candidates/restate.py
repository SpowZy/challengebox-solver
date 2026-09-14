def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    packets = []
    level = 0
    credits = initial_credits
    
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    total_spins = 0
    total_yields = 0
    
    outcome_run_idx = 0
    outcome_count_in_run = 0
    
    def get_next_outcome():
        nonlocal outcome_run_idx, outcome_count_in_run
        
        while outcome_run_idx < len(outcomes):
            kind, count = outcomes[outcome_run_idx]
            if outcome_count_in_run < count:
                outcome = kind
                outcome_count_in_run += 1
                return outcome
            else:
                outcome_run_idx += 1
                outcome_count_in_run = 0
        
        return "error"
    
    for packet_length in lengths:
        if packet_length < 1 or packet_length > 65535:
            packets.append(("INVALID", 0, 0, 0))
            invalid += 1
            continue
        
        retries = 0
        spins_for_packet = 0
        yields_for_packet = 0
        status = None
        
        while True:
            attempts += 1
            outcome = get_next_outcome()
            
            if outcome == "ok":
                status = "SENT"
                level = max(0, level - 1)
                credits = min(credit_cap, credits + packet_length)
                sent += 1
                break
            
            elif outcome == "error":
                status = "ERROR"
                level = 0
                errors += 1
                break
            
            elif outcome == "full":
                old_level = level
                level = min(level_cap, level + 1)
                cost = min(2 ** old_level, spin_limit)
                
                if retries < max_retries and credits >= cost:
                    retries += 1
                    credits -= cost
                    spins_for_packet += cost
                    total_spins += cost
                    
                    if 2 ** old_level > spin_limit:
                        yields_for_packet += 1
                        total_yields += 1
                else:
                    status = "DROPPED"
                    dropped += 1
                    break
        
        packets.append((status, retries, spins_for_packet, yields_for_packet))
    
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