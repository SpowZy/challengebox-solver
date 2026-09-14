def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    def outcome_generator(outcomes):
        for kind, count in outcomes:
            for _ in range(count):
                yield kind
    
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
        'final_credits': initial_credits
    }
    
    level = 0
    credits = initial_credits
    outcome_iter = outcome_generator(outcomes)
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(('INVALID', 0, 0, 0))
            telemetry['invalid'] += 1
            continue
        
        status = None
        retries_scheduled = 0
        total_spins = 0
        total_yields = 0
        
        while True:
            telemetry['attempts'] += 1
            outcome = next(outcome_iter, 'error')
            
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
                cost = min(2 ** old_level, spin_limit)
                
                if retries_scheduled < max_retries and credits >= cost:
                    retries_scheduled += 1
                    credits -= cost
                    total_spins += cost
                    telemetry['spins'] += cost
                    if 2 ** old_level > spin_limit:
                        total_yields += 1
                        telemetry['yields'] += 1
                else:
                    status = 'DROPPED'
                    telemetry['dropped'] += 1
                    break
        
        packets.append((status, retries_scheduled, total_spins, total_yields))
    
    telemetry['final_level'] = level
    telemetry['final_credits'] = credits
    
    return {
        'packets': packets,
        'telemetry': telemetry
    }