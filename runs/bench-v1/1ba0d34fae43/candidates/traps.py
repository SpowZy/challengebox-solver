def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    level = 0
    credits = initial_credits
    
    outcome_run_idx = 0
    outcome_count_idx = 0
    
    packets = []
    telemetry = {
        'sent': 0,
        'dropped': 0,
        'errors': 0,
        'invalid': 0,
        'attempts': 0,
        'spins': 0,
        'yields': 0,
        'final_level': 0,
        'final_credits': 0
    }
    
    def get_next_outcome():
        nonlocal outcome_run_idx, outcome_count_idx
        
        if outcome_run_idx >= len(outcomes):
            return 'error'
        
        kind, count = outcomes[outcome_run_idx]
        if outcome_count_idx >= count:
            outcome_run_idx += 1
            outcome_count_idx = 0
            if outcome_run_idx >= len(outcomes):
                return 'error'
            kind, count = outcomes[outcome_run_idx]
        
        outcome_count_idx += 1
        return kind
    
    for length in lengths:
        if not (1 <= length <= 65535):
            packets.append(('INVALID', 0, 0, 0))
            telemetry['invalid'] += 1
            continue
        
        status = None
        retries = 0
        total_spins = 0
        total_yields = 0
        
        while True:
            outcome = get_next_outcome()
            telemetry['attempts'] += 1
            
            if outcome == 'ok':
                status = 'SENT'
                level = max(0, level - 1)
                credits = min(credits + length, credit_cap)
                telemetry['sent'] += 1
                break
            
            elif outcome == 'error':
                status = 'ERROR'
                level = 0
                telemetry['errors'] += 1
                break
            
            elif outcome == 'full':
                old_level = level
                level = min(level + 1, level_cap)
                
                if old_level >= 60:
                    cost = spin_limit
                else:
                    cost = min(1 << old_level, spin_limit)
                
                can_retry = retries < max_retries and credits >= cost
                
                if can_retry:
                    retries += 1
                    credits -= cost
                    total_spins += cost
                    telemetry['spins'] += cost
                    
                    if old_level >= 60 or (1 << old_level) > spin_limit:
                        total_yields += 1
                        telemetry['yields'] += 1
                
                else:
                    status = 'DROPPED'
                    telemetry['dropped'] += 1
                    break
        
        packets.append((status, retries, total_spins, total_yields))
    
    telemetry['final_level'] = level
    telemetry['final_credits'] = credits
    
    return {
        'packets': packets,
        'telemetry': telemetry
    }