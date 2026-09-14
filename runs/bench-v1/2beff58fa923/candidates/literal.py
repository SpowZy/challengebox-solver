def refresh_references(initial, snapshots, references):
    # Build snapshots starting from initial
    current_state = {}
    for entry in initial:
        key = (entry['namespace'], entry['name'], entry['version'])
        current_state[key] = entry['hash']
    
    all_snapshots = [dict(current_state)]
    
    for batch in snapshots:
        for update in batch:
            key = (update['namespace'], update['name'], update['version'])
            if update['hash'] is None:
                current_state.pop(key, None)
            else:
                current_state[key] = update['hash']
        all_snapshots.append(dict(current_state))
    
    results = []
    
    for ref in references:
        namespace = ref['namespace']
        text = ref['text']
        context = ref['context']
        location = ref['location']
        ref_hash = ref['hash']
        start = ref['start']
        
        parse_result = _validate_and_parse(text, context, namespace)
        if parse_result is None:
            results.append(("invalid", namespace, location, ref_hash))
            continue
        
        parsed_name, parsed_version = parse_result
        
        if location is not None:
            key = (namespace, parsed_name, parsed_version)
            current_hash = ref_hash
            for snap_idx in range(start, len(all_snapshots)):
                if key in all_snapshots[snap_idx]:
                    current_hash = all_snapshots[snap_idx][key]
            results.append(("located", namespace, location, current_hash))
        else:
            found_namespace = None
            found_name = None
            found_version = None
            found_hash = None
            
            for snap_idx in range(start, len(all_snapshots)):
                result = _find_in_snapshot(all_snapshots[snap_idx], context, parsed_name, parsed_version, namespace)
                if result is not None:
                    found_namespace, found_name, found_version, found_hash = result
                    break
            
            if found_namespace is not None:
                results.append(("located", found_namespace, f"{found_namespace}:{found_name}:{found_version}", found_hash))
            else:
                results.append(("missing", namespace, None, None))
    
    return results

def _validate_and_parse(text, context, namespace):
    if context:
        for part in context.split('.'):
            if not _is_module_id(part):
                return None
    
    parts = text.split('.')
    if not parts:
        return None
    
    for part in parts[:-1]:
        if not _is_module_id(part):
            return None
    
    terminal = parts[-1]
    
    if namespace == "type":
        if '@' in terminal:
            return None
        if not _is_type_id(terminal):
            return None
        return (text, None)
    else:
        if '@' in terminal:
            at_idx = terminal.rfind('@')
            base = terminal[:at_idx]
            suffix = terminal[at_idx+1:]
            
            if not base or not suffix or not _is_module_id(base):
                return None
            if suffix[0] == '0' and len(suffix) > 1:
                return None
            if not all(c.isdigit() for c in suffix):
                return None
            
            parsed_name = '.'.join(parts[:-1] + [base])
            parsed_version = int(suffix)
        else:
            if not _is_module_id(terminal):
                return None
            parsed_name = text
            parsed_version = None
        
        return (parsed_name, parsed_version)

def _is_module_id(s):
    return s and s[0] in 'abcdefghijklmnopqrstuvwxyz' and all(c in 'abcdefghijklmnopqrstuvwxyz0123456789_' for c in s)

def _is_type_id(s):
    return s and s[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_' for c in s)

def _find_in_snapshot(snapshot, context, parsed_name, parsed_version, namespace):
    context_parts = context.split('.') if context else []
    candidates = []
    
    for i in range(len(context_parts), -1, -1):
        prefix_parts = context_parts[:i]
        candidate_name = '.'.join(prefix_parts + [parsed_name]) if prefix_parts else parsed_name
        candidates.append(candidate_name)
    
    if namespace == "value":
        for candidate_name in candidates:
            key = ("value", candidate_name, parsed_version)
            if key in snapshot:
                return ("value", candidate_name, parsed_version, snapshot[key])
        for candidate_name in candidates:
            key = ("function", candidate_name, parsed_version)
            if key in snapshot:
                return ("function", candidate_name, parsed_version, snapshot[key])
    else:
        for candidate_name in candidates:
            key = (namespace, candidate_name, parsed_version)
            if key in snapshot:
                return (namespace, candidate_name, parsed_version, snapshot[key])
    
    return None