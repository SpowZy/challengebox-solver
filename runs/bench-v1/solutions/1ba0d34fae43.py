def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    packets = []
    level = 0
    credits = initial_credits
    
    sent = 0
    dropped = 0
    errors = 0
    invalid = 0
    attempts = 0
    spins = 0
    yields = 0
    
    outcome_run_idx = 0
    outcome_count_idx = 0
    
    def get_next_outcome():
        nonlocal outcome_run_idx, outcome_count_idx
        
        while outcome_run_idx < len(outcomes):
            kind, count = outcomes[outcome_run_idx]
            if outcome_count_idx < count:
                outcome_count_idx += 1
                return kind
            else:
                outcome_run_idx += 1
                outcome_count_idx = 0
        
        return 'error'
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(('INVALID', 0, 0, 0))
            invalid += 1
            continue
        
        retries_scheduled = 0
        packet_spins = 0
        packet_yields = 0
        packet_status = None
        
        while True:
            outcome = get_next_outcome()
            attempts += 1
            
            if outcome == 'ok':
                packet_status = 'SENT'
                level = max(0, level - 1)
                credits = min(credits + length, credit_cap)
                sent += 1
                break
            
            elif outcome == 'error':
                packet_status = 'ERROR'
                errors += 1
                level = 0
                break
            
            elif outcome == 'full':
                old_level = level
                level = min(level + 1, level_cap)
                
                cost = min(2**old_level, spin_limit)
                
                if retries_scheduled < max_retries and credits >= cost:
                    retries_scheduled += 1
                    credits -= cost
                    packet_spins += cost
                    spins += cost
                    
                    if 2**old_level > spin_limit:
                        packet_yields += 1
                        yields += 1
                else:
                    packet_status = 'DROPPED'
                    dropped += 1
                    break
        
        packets.append((packet_status, retries_scheduled, packet_spins, packet_yields))
    
    telemetry = {
        'sent': sent,
        'dropped': dropped,
        'errors': errors,
        'invalid': invalid,
        'attempts': attempts,
        'spins': spins,
        'yields': yields,
        'final_level': level,
        'final_credits': credits
    }
    
    return {
        'packets': packets,
        'telemetry': telemetry
    }