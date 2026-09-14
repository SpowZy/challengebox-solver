def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    level = 0
    credits = initial_credits
    packets_results = []
    
    outcome_elem_idx = 0
    outcome_count_used = 0
    
    def get_next_outcome():
        nonlocal outcome_elem_idx, outcome_count_used
        
        if outcome_elem_idx >= len(outcomes):
            return "error"
        
        kind, count = outcomes[outcome_elem_idx]
        
        if outcome_count_used >= count:
            outcome_elem_idx += 1
            outcome_count_used = 0
            
            if outcome_elem_idx >= len(outcomes):
                return "error"
            
            kind, count = outcomes[outcome_elem_idx]
        
        result = kind
        outcome_count_used += 1
        
        return result
    
    telemetry = {
        'sent': 0,
        'dropped': 0,
        'errors': 0,
        'invalid': 0,
        'attempts': 0,
        'spins': 0,
        'yields': 0,
    }
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets_results.append(("INVALID", 0, 0, 0))
            telemetry['invalid'] += 1
            continue
        
        status = None
        retries_scheduled = 0
        packet_spins = 0
        packet_yields = 0
        
        while True:
            outcome = get_next_outcome()
            telemetry['attempts'] += 1
            
            if outcome == "ok":
                status = "SENT"
                level = max(0, level - 1)
                credits = min(credit_cap, credits + length)
                telemetry['sent'] += 1
                break
            
            elif outcome == "error":
                status = "ERROR"
                level = 0
                telemetry['errors'] += 1
                break
            
            elif outcome == "full":
                old_level = level
                level = min(level_cap, level + 1)
                cost = min(2**old_level, spin_limit)
                
                if retries_scheduled < max_retries and credits >= cost:
                    retries_scheduled += 1
                    credits -= cost
                    packet_spins += cost
                    telemetry['spins'] += cost
                    
                    if 2**old_level > spin_limit:
                        packet_yields += 1
                        telemetry['yields'] += 1
                else:
                    status = "DROPPED"
                    telemetry['dropped'] += 1
                    break
        
        packets_results.append((status, retries_scheduled, packet_spins, packet_yields))
    
    telemetry['final_level'] = level
    telemetry['final_credits'] = credits
    
    return {
        'packets': packets_results,
        'telemetry': telemetry
    }