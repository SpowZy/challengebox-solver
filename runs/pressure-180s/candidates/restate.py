def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    packets = []
    
    level = 0
    credits = initial_credits
    
    telemetry = {
        'sent': 0,
        'dropped': 0,
        'errors': 0,
        'invalid': 0,
        'attempts': 0,
        'spins': 0,
        'yields': 0,
        'final_level': level,
        'final_credits': credits
    }
    
    outcome_runs = iter(outcomes)
    current_kind = None
    current_count = 0
    
    def get_next_outcome():
        nonlocal current_kind, current_count, outcome_runs
        
        if current_count > 0:
            current_count -= 1
            return current_kind
        
        try:
            current_kind, current_count = next(outcome_runs)
            current_count -= 1
            return current_kind
        except StopIteration:
            return 'error'
    
    for packet_length in lengths:
        if not (1 <= packet_length <= 65535):
            packets.append(('INVALID', 0, 0, 0))
            telemetry['invalid'] += 1
            continue
        
        retries = 0
        spins = 0
        yields = 0
        status = None
        
        while True:
            outcome = get_next_outcome()
            telemetry['attempts'] += 1
            
            if outcome == 'ok':
                status = 'SENT'
                telemetry['sent'] += 1
                level = max(0, level - 1)
                credits = min(credits + packet_length, credit_cap)
                break
            
            elif outcome == 'error':
                status = 'ERROR'
                telemetry['errors'] += 1
                level = 0
                break
            
            elif outcome == 'full':
                old_level = level
                level = min(level + 1, level_cap)
                
                cost = min(2**old_level, spin_limit)
                
                if retries < max_retries and credits >= cost:
                    retries += 1
                    credits -= cost
                    spins += cost
                    if 2**old_level > spin_limit:
                        yields += 1
                else:
                    status = 'DROPPED'
                    telemetry['dropped'] += 1
                    break
        
        packets.append((status, retries, spins, yields))
    
    telemetry['final_level'] = level
    telemetry['final_credits'] = credits
    
    return {
        'packets': packets,
        'telemetry': telemetry
    }