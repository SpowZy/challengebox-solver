def simulate_writes(lengths, outcomes, max_retries, level_cap, spin_limit, initial_credits, credit_cap):
    outcome_list = list(outcomes)
    outcome_run_idx = 0
    outcome_count_in_run = 0
    
    def get_next_outcome():
        nonlocal outcome_run_idx, outcome_count_in_run
        while outcome_run_idx < len(outcome_list):
            kind, count = outcome_list[outcome_run_idx]
            if outcome_count_in_run < count:
                outcome_count_in_run += 1
                return kind
            outcome_run_idx += 1
            outcome_count_in_run = 0
        return "error"
    
    level = 0
    credits = initial_credits
    
    packets = []
    telemetry = {
        "sent": 0,
        "dropped": 0,
        "errors": 0,
        "invalid": 0,
        "attempts": 0,
        "spins": 0,
        "yields": 0
    }
    
    for length in lengths:
        if length < 1 or length > 65535:
            packets.append(("INVALID", 0, 0, 0))
            telemetry["invalid"] += 1
            continue
        
        retries = 0
        total_spins = 0
        total_yields = 0
        status = None
        
        while True:
            telemetry["attempts"] += 1
            outcome = get_next_outcome()
            
            if outcome == "ok":
                level = max(0, level - 1)
                credits = min(credits + length, credit_cap)
                status = "SENT"
                telemetry["sent"] += 1
                break
            
            elif outcome == "error":
                level = 0
                status = "ERROR"
                telemetry["errors"] += 1
                break
            
            elif outcome == "full":
                old_level = level
                level = min(level + 1, level_cap)
                cost = min(2 ** old_level, spin_limit)
                
                if retries < max_retries and credits >= cost:
                    retries += 1
                    credits -= cost
                    total_spins += cost
                    telemetry["spins"] += cost
                    
                    if 2 ** old_level > spin_limit:
                        total_yields += 1
                        telemetry["yields"] += 1
                else:
                    status = "DROPPED"
                    telemetry["dropped"] += 1
                    break
        
        packets.append((status, retries, total_spins, total_yields))
    
    telemetry["final_level"] = level
    telemetry["final_credits"] = credits
    
    return {
        "packets": packets,
        "telemetry": telemetry
    }