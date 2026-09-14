def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    class OutcomeIterator:
        def __init__(self, outcomes):
            self.outcomes = outcomes
            self.run_idx = 0
            self.consumed_from_run = 0
        
        def next(self):
            if self.run_idx >= len(self.outcomes):
                return 'error'
            
            kind, count = self.outcomes[self.run_idx]
            
            if self.consumed_from_run >= count:
                self.run_idx += 1
                self.consumed_from_run = 0
                if self.run_idx >= len(self.outcomes):
                    return 'error'
                kind, count = self.outcomes[self.run_idx]
            
            self.consumed_from_run += 1
            return kind
    
    outcome_iter = OutcomeIterator(outcomes)
    
    level = 0
    credits = initial_credits
    
    results = []
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
            results.append(('INVALID', 0, 0, 0))
            telemetry['invalid'] += 1
            continue
        
        status = None
        retries = 0
        spins = 0
        yields = 0
        
        while True:
            outcome_kind = outcome_iter.next()
            telemetry['attempts'] += 1
            
            if outcome_kind == 'ok':
                status = 'SENT'
                level = max(0, level - 1)
                credits = min(credit_cap, credits + length)
                break
            
            elif outcome_kind == 'error':
                status = 'ERROR'
                level = 0
                break
            
            elif outcome_kind == 'full':
                old_level = level
                level = min(level_cap, level + 1)
                cost = min(2 ** old_level, spin_limit)
                
                if retries < max_retries and credits >= cost:
                    retries += 1
                    credits -= cost
                    spins += cost
                    telemetry['spins'] += cost
                    
                    if 2 ** old_level > spin_limit:
                        yields += 1
                        telemetry['yields'] += 1
                else:
                    status = 'DROPPED'
                    break
        
        results.append((status, retries, spins, yields))
        
        if status == 'SENT':
            telemetry['sent'] += 1
        elif status == 'DROPPED':
            telemetry['dropped'] += 1
        elif status == 'ERROR':
            telemetry['errors'] += 1
    
    telemetry['final_level'] = level
    telemetry['final_credits'] = credits
    
    return {
        'packets': results,
        'telemetry': telemetry
    }