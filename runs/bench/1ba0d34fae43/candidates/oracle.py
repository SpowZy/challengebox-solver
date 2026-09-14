def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    # Expand outcomes from run-length encoding
    expanded_outcomes = []
    for kind, count in outcomes:
        expanded_outcomes.extend([kind] * count)
    
    level = 0
    credits = initial_credits
    outcome_index = 0
    
    packets = []
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    total_spins = 0
    total_yields = 0
    
    def get_next_outcome():
        nonlocal outcome_index, attempts
        if outcome_index < len(expanded_outcomes):
            outcome = expanded_outcomes[outcome_index]
            outcome_index += 1
        else:
            outcome = "error"
        attempts += 1
        return outcome
    
    for length in lengths:
        # Check if packet is valid
        if length < 1 or length > 65535:
            packets.append(("INVALID", 0, 0, 0))
            invalid += 1
            continue
        
        # Process valid packet
        retries = 0
        packet_spins = 0
        packet_yields = 0
        status = None
        
        while True:
            outcome = get_next_outcome()
            
            if outcome == "ok":
                # Send packet
                level = max(0, level - 1)
                credits = min(credits + length, credit_cap)
                status = "SENT"
                sent += 1
                break
            elif outcome == "error":
                # Error outcome
                level = 0
                status = "ERROR"
                errors += 1
                break
            elif outcome == "full":
                # Full outcome
                old_level = level
                level = min(level + 1, level_cap)
                cost = min(2 ** old_level, spin_limit)
                
                if retries < max_retries and credits >= cost:
                    # Schedule retry
                    credits -= cost
                    packet_spins += cost
                    total_spins += cost
                    if 2 ** old_level > spin_limit:
                        packet_yields += 1
                        total_yields += 1
                    retries += 1
                    # Continue loop to process retry
                else:
                    # Cannot retry - drop packet
                    status = "DROPPED"
                    dropped += 1
                    break
        
        packets.append((status, retries, packet_spins, packet_yields))
    
    telemetry = {
        "sent": sent,
        "dropped": dropped,
        "errors": errors,
        "invalid": invalid,
        "attempts": attempts,
        "spins": total_spins,
        "yields": total_yields,
        "final_level": level,
        "final_credits": credits,
    }
    
    return {
        "packets": packets,
        "telemetry": telemetry,
    }