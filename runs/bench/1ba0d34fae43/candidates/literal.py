def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    congestion_level = 0
    credit_balance = initial_credits
    
    outcome_run_idx = 0
    outcome_count_in_run = 0
    
    packet_results = []
    
    sent_count = 0
    dropped_count = 0
    errors_count = 0
    invalid_count = 0
    attempts_count = 0
    total_spins = 0
    total_yields = 0
    
    def get_next_outcome():
        nonlocal outcome_run_idx, outcome_count_in_run
        while outcome_run_idx < len(outcomes):
            kind, count = outcomes[outcome_run_idx]
            if outcome_count_in_run < count:
                outcome_count_in_run += 1
                return kind
            else:
                outcome_run_idx += 1
                outcome_count_in_run = 0
        return "error"
    
    for length in lengths:
        if not (1 <= length <= 65535):
            packet_results.append(("INVALID", 0, 0, 0))
            invalid_count += 1
            continue
        
        retries_scheduled = 0
        packet_spins = 0
        packet_yields = 0
        status = None
        
        while True:
            outcome = get_next_outcome()
            attempts_count += 1
            
            if outcome == "ok":
                congestion_level = max(0, congestion_level - 1)
                credit_balance = min(credit_cap, credit_balance + length)
                status = "SENT"
                sent_count += 1
                break
            
            elif outcome == "error":
                congestion_level = 0
                status = "ERROR"
                errors_count += 1
                break
            
            elif outcome == "full":
                old_level = congestion_level
                congestion_level = min(level_cap, congestion_level + 1)
                
                cost = min(2**old_level, spin_limit)
                
                if retries_scheduled < max_retries and credit_balance >= cost:
                    retries_scheduled += 1
                    credit_balance -= cost
                    packet_spins += cost
                    total_spins += cost
                    
                    if 2**old_level > spin_limit:
                        packet_yields += 1
                        total_yields += 1
                else:
                    status = "DROPPED"
                    dropped_count += 1
                    break
        
        packet_results.append((status, retries_scheduled, packet_spins, packet_yields))
    
    return {
        "packets": packet_results,
        "telemetry": {
            "sent": sent_count,
            "dropped": dropped_count,
            "errors": errors_count,
            "invalid": invalid_count,
            "attempts": attempts_count,
            "spins": total_spins,
            "yields": total_yields,
            "final_level": congestion_level,
            "final_credits": credit_balance
        }
    }