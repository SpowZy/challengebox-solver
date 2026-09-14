def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    level = 0
    credits = initial_credits
    
    run_idx = 0
    count_in_run = 0
    
    packets = []
    telemetry = {
        'sent': 0,
        'dropped': 0,
        'errors': 0,
        'invalid': 0,
        'attempts': 0,
        'spins': 0,
        'yields': 0,
    }
    
    def get_next_outcome():
        nonlocal run_idx, count_in_run
        
        while run_idx < len(outcomes):
            kind, count = outcomes[run_idx]
            if count_in_run < count:
                count_in_run += 1
                return kind
            else:
                run_idx += 1
                count_in_run = 0
        
        return 'error'
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(('INVALID', 0, 0, 0))
            telemetry['invalid'] += 1
            continue
        
        retries_scheduled = 0
        packet_spins = 0
        packet_yields = 0
        status = None
        
        while True:
            outcome = get_next_outcome()
            telemetry['attempts'] += 1
            
            if outcome == 'ok':
                level = max(0, level - 1)
                credits = min(credit_cap, credits + length)
                status = 'SENT'
                telemetry['sent'] += 1
                break
            
            elif outcome == 'error':
                level = 0
                status = 'ERROR'
                telemetry['errors'] += 1
                break
            
            elif outcome == 'full':
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
                    status = 'DROPPED'
                    telemetry['dropped'] += 1
                    break
        
        packets.append((status, retries_scheduled, packet_spins, packet_yields))
    
    telemetry['final_level'] = level
    telemetry['final_credits'] = credits
    
    return {
        'packets': packets,
        'telemetry': telemetry
    }