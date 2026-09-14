def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    packets = []
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    spins = 0
    yields_count = 0
    
    level = 0
    credits = initial_credits
    
    run_index = 0
    count_in_run = 0
    
    def get_next_outcome():
        nonlocal run_index, count_in_run
        
        while run_index < len(outcomes):
            kind, count = outcomes[run_index]
            
            if count_in_run < count:
                count_in_run += 1
                return kind
            else:
                run_index += 1
                count_in_run = 0
        
        return "error"
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(("INVALID", 0, 0, 0))
            invalid += 1
            continue
        
        packet_status = None
        packet_retries = 0
        packet_spins = 0
        packet_yields = 0
        
        while True:
            outcome = get_next_outcome()
            attempts += 1
            
            if outcome == "ok":
                packet_status = "SENT"
                sent += 1
                level = max(0, level - 1)
                credits = min(credit_cap, credits + length)
                break
            elif outcome == "error":
                packet_status = "ERROR"
                errors += 1
                level = 0
                break
            elif outcome == "full":
                old_level = level
                level = min(level + 1, level_cap)
                cost = min(2 ** old_level, spin_limit)
                
                if packet_retries < max_retries and credits >= cost:
                    packet_retries += 1
                    credits -= cost
                    packet_spins += cost
                    spins += cost
                    
                    if 2 ** old_level > spin_limit:
                        packet_yields += 1
                        yields_count += 1
                else:
                    packet_status = "DROPPED"
                    dropped += 1
                    break
        
        packets.append((packet_status, packet_retries, packet_spins, packet_yields))
    
    telemetry = {
        "sent": sent,
        "dropped": dropped,
        "errors": errors,
        "invalid": invalid,
        "attempts": attempts,
        "spins": spins,
        "yields": yields_count,
        "final_level": level,
        "final_credits": credits
    }
    
    return {
        "packets": packets,
        "telemetry": telemetry
    }