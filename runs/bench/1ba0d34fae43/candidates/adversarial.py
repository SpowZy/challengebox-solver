def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    # Flatten outcomes into a simple list
    outcome_list = []
    for kind, count in outcomes:
        outcome_list.extend([kind] * count)
    
    outcome_index = 0
    level = 0
    credits = initial_credits
    
    packets_result = []
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    total_spins = 0
    total_yields = 0
    
    for length in lengths:
        # Check validity
        if length < 1 or length > 65535:
            packets_result.append(("INVALID", 0, 0, 0))
            invalid += 1
            continue
        
        # Valid packet
        retries_scheduled = 0
        packet_spins = 0
        packet_yields = 0
        status = None
        
        while True:
            # Get next outcome
            if outcome_index < len(outcome_list):
                outcome = outcome_list[outcome_index]
                outcome_index += 1
            else:
                outcome = "error"  # Implicit error
            
            attempts += 1
            
            if outcome == "ok":
                # Send packet
                level = max(0, level - 1)
                credits = min(credit_cap, credits + length)
                status = "SENT"
                sent += 1
                break
            elif outcome == "error":
                # Fail packet
                level = 0
                status = "ERROR"
                errors += 1
                break
            elif outcome == "full":
                # Raise level
                old_level = level
                level = min(level_cap, level + 1)
                cost = min(2**old_level, spin_limit)
                
                # Check if we can schedule a retry
                if retries_scheduled < max_retries and credits >= cost:
                    # Schedule retry
                    retries_scheduled += 1
                    credits -= cost
                    packet_spins += cost
                    total_spins += cost
                    
                    if 2**old_level > spin_limit:
                        packet_yields += 1
                        total_yields += 1
                else:
                    # Drop packet
                    status = "DROPPED"
                    dropped += 1
                    break
        
        packets_result.append((status, retries_scheduled, packet_spins, packet_yields))
    
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
        "packets": packets_result,
        "telemetry": telemetry
    }