def refresh_references(initial, snapshots, references):
    def is_valid_identifier(s):
        return s and all(c.isalnum() or c == '_' for c in s)
    
    def is_valid_module_identifier(s):
        return is_valid_identifier(s) and s[0] in 'abcdefghijklmnopqrstuvwxyz'
    
    def is_lowercase_terminal(s):
        return is_valid_identifier(s) and s[0] in 'abcdefghijklmnopqrstuvwxyz'
    
    def is_uppercase_terminal(s):
        return is_valid_identifier(s) and s[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    
    def parse_text(text, namespace):
        if not text:
            return None
        
        parts = text.split('.')
        terminal = parts[-1]
        module_parts = parts[:-1]
        
        version = None
        if '@' in terminal:
            if namespace not in ["function", "value"]:
                return None
            
            term_parts = terminal.rsplit('@', 1)
            terminal_name = term_parts[0]
            version_str = term_parts[1]
            
            if not version_str or (version_str[0] == '0' and len(version_str) > 1):
                return None
            
            try:
                version = int(version_str)
            except ValueError:
                return None
            
            terminal = terminal_name
        
        for part in module_parts:
            if not is_valid_module_identifier(part):
                return None
        
        if not is_valid_identifier(terminal):
            return None
        
        if namespace == "type":
            if not is_uppercase_terminal(terminal):
                return None
        elif namespace in ["function", "value"]:
            if not is_lowercase_terminal(terminal):
                return None
        else:
            return None
        
        return (module_parts, terminal, version)
    
    def parse_context(context):
        if not context:
            return []
        
        parts = context.split('.')
        for part in parts:
            if not is_valid_module_identifier(part):
                return None
        
        return parts
    
    states = [{}]
    
    for entry in initial:
        key = (entry['namespace'], entry['name'], entry['version'])
        states[0][key] = entry['hash']
    
    current_state = dict(states[0])
    for batch in snapshots:
        for update in batch:
            key = (update['namespace'], update['name'], update['version'])
            if update['hash'] is None:
                if key in current_state:
                    del current_state[key]
            else:
                current_state[key] = update['hash']
        states.append(dict(current_state))
    
    results = []
    
    for ref in references:
        ref_namespace = ref['namespace']
        ref_text = ref['text']
        ref_context = ref['context']
        ref_location = ref['location']
        ref_hash = ref['hash']
        ref_start = ref['start']
        
        text_result = parse_text(ref_text, ref_namespace)
        if text_result is None:
            results.append(("invalid", ref_namespace, ref_location, ref_hash))
            continue
        
        module_parts, terminal, version = text_result
        
        context_parts = parse_context(ref_context)
        if context_parts is None:
            results.append(("invalid", ref_namespace, ref_location, ref_hash))
            continue
        
        if ref_location is not None:
            current_hash = ref_hash
            for snapshot_idx in range(ref_start, len(states)):
                key = (ref_namespace, ref_location, version)
                if key in states[snapshot_idx]:
                    current_hash = states[snapshot_idx][key]
            
            results.append(("located", ref_namespace, ref_location, current_hash))
            continue
        
        full_name_parts = module_parts + [terminal]
        
        candidates = []
        for prefix_len in range(len(context_parts), -1, -1):
            prefix = context_parts[:prefix_len]
            full_name = '.'.join(prefix + full_name_parts)
            
            if ref_namespace == "type":
                candidates.append((full_name, "type"))
            elif ref_namespace == "function":
                candidates.append((full_name, "function"))
            elif ref_namespace == "value":
                candidates.append((full_name, "value"))
                candidates.append((full_name, "function"))
        
        matched = False
        matched_namespace = ref_namespace
        matched_location = None
        matched_hash = None
        match_snapshot_idx = -1
        
        for snapshot_idx in range(ref_start, len(states)):
            state = states[snapshot_idx]
            
            for candidate_name, candidate_namespace in candidates:
                key = (candidate_namespace, candidate_name, version)
                if key in state:
                    matched = True
                    matched_namespace = candidate_namespace
                    matched_location = candidate_name
                    matched_hash = state[key]
                    match_snapshot_idx = snapshot_idx
                    break
            
            if matched:
                break
        
        if matched:
            current_hash = matched_hash
            for snapshot_idx in range(match_snapshot_idx + 1, len(states)):
                key = (matched_namespace, matched_location, version)
                if key in states[snapshot_idx]:
                    current_hash = states[snapshot_idx][key]
            
            results.append(("located", matched_namespace, matched_location, current_hash))
        else:
            results.append(("missing", ref_namespace, None, None))
    
    return results