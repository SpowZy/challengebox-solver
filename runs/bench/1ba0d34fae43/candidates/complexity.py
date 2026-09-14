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
        'final_level': 0,
        'final_credits': 0
    }
    
    run_idx = 0
    count_in_run = 0
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(('INVALID', 0, 0, 0))
            telemetry['invalid'] += 1
            continue
        
        retries = 0
        spins = 0
        yields = 0
        status = None
        
        while True:
            if run_idx >= len(outcomes):
                telemetry['attempts'] += 1
                telemetry['errors'] += 1
                status = 'ERROR'
                break
            
            kind, total_count = outcomes[run_idx]
            
            if count_in_run >= total_count:
                run_idx += 1
                count_in_run = 0
                
                if run_idx >= len(outcomes):
                    telemetry['attempts'] += 1
                    telemetry['errors'] += 1
                    status = 'ERROR'
                    break
                
                kind, total_count = outcomes[run_idx]
            
            count_in_run += 1
            telemetry['attempts'] += 1
            
            if kind == 'ok':
                level = max(0, level - 1)
                credits = min(credits + length, credit_cap)
                telemetry['sent'] += 1
                status = 'SENT'
                break
            
            elif kind == 'error':
                level = 0
                telemetry['errors'] += 1
                status = 'ERROR'
                break
            
            elif kind == 'full':
                old_level = level
                level = min(level + 1, level_cap)
                cost = min(2**old_level, spin_limit)
                
                if retries < max_retries and credits >= cost:
                    retries += 1
                    credits -= cost
                    spins += cost
                    if 2**old_level > spin_limit:
                        yields += 1
                        telemetry['yields'] += 1
                else:
                    telemetry['dropped'] += 1
                    status = 'DROPPED'
                    break
        
        packets.append((status, retries, spins, yields))
        telemetry['spins'] += spins
    
    telemetry['final_level'] = level
    telemetry['final_credits'] = credits
    
    return {
        'packets': packets,
        'telemetry': telemetry
    }