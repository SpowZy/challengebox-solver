def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    level = 0
    credits = initial_credits
    run_idx = 0
    count_in_run = 0
    attempts = 0
    
    packets = []
    
    def get_next_outcome():
        nonlocal run_idx, count_in_run
        
        while run_idx < len(outcomes):
            kind, count = outcomes[run_idx]
            if count_in_run < count:
                count_in_run += 1
                return kind
            run_idx += 1
            count_in_run = 0
        
        return 'error'
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(('INVALID', 0, 0, 0))
            continue
        
        status = None
        retries_scheduled = 0
        total_spins = 0
        total_yields = 0
        
        while True:
            outcome = get_next_outcome()
            attempts += 1
            
            if outcome == 'ok':
                level = max(0, level - 1)
                credits = min(credit_cap, credits + length)
                status = 'SENT'
                break
            
            elif outcome == 'error':
                level = 0
                status = 'ERROR'
                break
            
            elif outcome == 'full':
                old_level = level
                level = min(level_cap, level + 1)
                cost = min(2**old_level, spin_limit)
                
                if retries_scheduled < max_retries and credits >= cost:
                    credits -= cost
                    total_spins += cost
                    if 2**old_level > spin_limit:
                        total_yields += 1
                    retries_scheduled += 1
                else:
                    status = 'DROPPED'
                    break
        
        packets.append((status, retries_scheduled, total_spins, total_yields))
    
    telemetry = {
        'sent': sum(1 for p in packets if p[0] == 'SENT'),
        'dropped': sum(1 for p in packets if p[0] == 'DROPPED'),
        'errors': sum(1 for p in packets if p[0] == 'ERROR'),
        'invalid': sum(1 for p in packets if p[0] == 'INVALID'),
        'attempts': attempts,
        'spins': sum(p[2] for p in packets),
        'yields': sum(p[3] for p in packets),
        'final_level': level,
        'final_credits': credits,
    }
    
    return {
        'packets': packets,
        'telemetry': telemetry
    }