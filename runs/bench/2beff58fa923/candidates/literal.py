def refresh_references(initial, snapshots, references):
    # Build initial state
    initial_state = {}
    for entry in initial:
        key = (entry["namespace"], entry["name"], entry["version"])
        initial_state[key] = entry
    
    states = [initial_state]
    
    # Build states for each snapshot
    current_state = dict(initial_state)
    for batch in snapshots:
        for update in batch:
            key = (update["namespace"], update["name"], update["version"])
            if update["hash"] is None:
                current_state.pop(key, None)
            else:
                current_state[key] = update
        states.append(dict(current_state))
    
    # Process references
    results = []
    for ref in references:
        result = process_reference(ref, states)
        results.append(result)
    
    return results

def process_reference(ref, states):
    namespace = ref["namespace"]
    text = ref["text"]
    context = ref["context"]
    location = ref["location"]
    hash_val = ref["hash"]
    start = ref["start"]
    
    # Validate and parse reference
    parsed = parse_text(text, namespace)
    if parsed is None:
        return ("invalid", namespace, location, hash_val)
    
    name, version = parsed
    
    # If location is provided, it's location-authoritative
    if location is not None:
        key = (namespace, location, version)
        current_hash = hash_val
        
        for snapshot_idx in range(start, len(states)):
            if key in states[snapshot_idx]:
                current_hash = states[snapshot_idx][key]["hash"]
        
        return ("located", namespace, location, current_hash)
    
    # Search for candidate match
    matched_location = None
    matched_hash = None
    matched_namespace = namespace
    
    for snapshot_idx in range(start, len(states)):
        state = states[snapshot_idx]
        
        # Generate candidates
        candidates = generate_candidates(name, context, namespace)
        
        # Search candidates
        for cand_name, cand_ns in candidates:
            key = (cand_ns, cand_name, version)
            if key in state:
                matched_location = cand_name
                matched_hash = state[key]["hash"]
                matched_namespace = cand_ns
                break
        
        if matched_location is not None:
            break
    
    if matched_location is None:
        return ("missing", namespace, None, None)
    
    return ("located", matched_namespace, matched_location, matched_hash)

def parse_text(text, namespace):
    if not text:
        return None
    
    parts = text.split('.')
    terminal = parts[-1]
    module_parts = parts[:-1]
    
    # Validate module identifiers
    for part in module_parts:
        if not part or not part[0].islower() or not all(c.isalnum() or c == '_' for c in part):
            return None
    
    # Validate terminal based on namespace
    if namespace == "type":
        if not terminal or not terminal[0].isupper() or '@' in terminal:
            return None
        if not all(c.isalnum() or c == '_' for c in terminal):
            return None
        return (text, None)
    else:  # function or value
        if '@' in terminal:
            at_idx = terminal.find('@')
            name_part = terminal[:at_idx]
            version_str = terminal[at_idx+1:]
            
            if not name_part or not name_part[0].islower():
                return None
            if not all(c.isalnum() or c == '_' for c in name_part):
                return None
            
            if not version_str or not version_str.isdigit():
                return None
            if version_str != "0" and version_str[0] == '0':
                return None
            
            version = int(version_str)
            full_name = '.'.join(module_parts + [name_part])
            return (full_name, version)
        else:
            if not terminal or not terminal[0].islower():
                return None
            if not all(c.isalnum() or c == '_' for c in terminal):
                return None
            return (text, None)

def generate_candidates(name, context, namespace):
    context_parts = context.split('.') if context else []
    candidates = []
    
    if namespace == "value":
        for prefix_len in range(len(context_parts), -1, -1):
            if prefix_len > 0:
                prefix = '.'.join(context_parts[:prefix_len])
                candidate_name = prefix + '.' + name
            else:
                candidate_name = name
            candidates.append((candidate_name, "value"))
        
        for prefix_len in range(len(context_parts), -1, -1):
            if prefix_len > 0:
                prefix = '.'.join(context_parts[:prefix_len])
                candidate_name = prefix + '.' + name
            else:
                candidate_name = name
            candidates.append((candidate_name, "function"))
    else:
        for prefix_len in range(len(context_parts), -1, -1):
            if prefix_len > 0:
                prefix = '.'.join(context_parts[:prefix_len])
                candidate_name = prefix + '.' + name
            else:
                candidate_name = name
            candidates.append((candidate_name, namespace))
    
    return candidates