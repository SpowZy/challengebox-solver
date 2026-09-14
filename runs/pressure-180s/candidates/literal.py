def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    class OutcomeIterator:
        def __init__(self, outcomes):
            self.outcomes = outcomes
            self.run_idx = 0
            self.offset_in_run = 0
        
        def next(self):
            while self.run_idx < len(self.outcomes):
                kind, count = self.outcomes[self.run_idx]
                if self.offset_in_run < count:
                    self.offset_in_run += 1
                    return kind
                else:
                    self.run_idx += 1
                    self.offset_in_run = 0
            return "error"
    
    outcome_iter = OutcomeIterator(outcomes)
    
    level = 0
    credits = initial_credits
    
    packets = []
    sent_count = 0
    dropped_count = 0
    errors_count = 0
    invalid_count = 0
    attempts_count = 0
    spins_count = 0
    yields_count = 0
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(("INVALID", 0, 0, 0))
            invalid_count += 1
            continue
        
        retries_scheduled = 0
        total_spins = 0
        total_yields = 0
        status = None
        
        while True:
            outcome = outcome_iter.next()
            attempts_count += 1
            
            if outcome == "ok":
                level = max(0, level - 1)
                credits = min(credit_cap, credits + length)
                status = "SENT"
                sent_count += 1
                break
            
            elif outcome == "error":
                level = 0
                status = "ERROR"
                errors_count += 1
                break
            
            elif outcome == "full":
                old_level = level
                level = min(level + 1, level_cap)
                cost = min(2**old_level, spin_limit)
                
                if retries_scheduled < max_retries and credits >= cost:
                    retries_scheduled += 1
                    credits -= cost
                    total_spins += cost
                    spins_count += cost
                    
                    if 2**old_level > spin_limit:
                        total_yields += 1
                        yields_count += 1
                else:
                    status = "DROPPED"
                    dropped_count += 1
                    break
        
        packets.append((status, retries_scheduled, total_spins, total_yields))
    
    telemetry = {
        "sent": sent_count,
        "dropped": dropped_count,
        "errors": errors_count,
        "invalid": invalid_count,
        "attempts": attempts_count,
        "spins": spins_count,
        "yields": yields_count,
        "final_level": level,
        "final_credits": credits
    }
    
    return {
        "packets": packets,
        "telemetry": telemetry
    }