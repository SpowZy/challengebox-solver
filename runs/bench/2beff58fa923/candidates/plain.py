def refresh_references(initial, snapshots, references):
    results = []
    
    for ref in references:
        namespace = ref['namespace']
        text = ref['text']
        context = ref['context']
        location = ref['location']
        hash_val = ref['hash']
        start = ref['start']
        
        # Parse text
        is_valid, parsed_name, version = parse_text(text, namespace)
        
        if not is_valid:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        # Build initial index
        current_index = {}
        for entry in initial:
            key = (entry['namespace'], entry['name'], entry['version'])
            current_index[key] = entry
        
        if location is not None:
            # Location-authoritative
            current_hash = hash_val
            for snapshot_idx in range(start, len(snapshots) + 1):
                if snapshot_idx > 0:
                    batch = snapshots[snapshot_idx - 1]
                    for update in batch:
                        key = (update['namespace'], update['name'], update['version'])
                        if update['hash'] is None:
                            current_index.pop(key, None)
                        else:
                            current_index[key] = update
                
                ref_key = (namespace, parsed_name, version)
                if ref_key in current_index:
                    current_hash = current_index[ref_key]['hash']
            
            results.append(("located", namespace, location, current_hash))
        else:
            # Location-less
            context_parts = context.split('.') if context else []
            candidates = generate_candidates(context_parts, parsed_name)
            
            found_candidate = None
            found_namespace = namespace
            found_hash = None
            
            for snapshot_idx in range(start, len(snapshots) + 1):
                if snapshot_idx > 0:
                    batch = snapshots[snapshot_idx - 1]
                    for update in batch:
                        key = (update['namespace'], update['name'], update['version'])
                        if update['hash'] is None:
                            current_index.pop(key, None)
                        else:
                            current_index[key] = update
                
                if found_candidate is None:
                    # Search for match
                    if namespace == "value":
                        # Try value candidates
                        for candidate in candidates:
                            ref_key = ("value", candidate, version)
                            if ref_key in current_index:
                                found_candidate = candidate
                                found_namespace = "value"
                                found_hash = current_index[ref_key]['hash']
                                break
                        
                        # Try function candidates
                        if found_candidate is None:
                            for candidate in candidates:
                                ref_key = ("function", candidate, version)
                                if ref_key in current_index:
                                    found_candidate = candidate
                                    found_namespace = "function"
                                    found_hash = current_index[ref_key]['hash']
                                    break
                    else:
                        # Type or function
                        for candidate in candidates:
                            ref_key = (namespace, candidate, version)
                            if ref_key in current_index:
                                found_candidate = candidate
                                found_hash = current_index[ref_key]['hash']
                                break
                else:
                    # Already found, update hash if key still exists
                    ref_key = (found_namespace, found_candidate, version)
                    if ref_key in current_index:
                        found_hash = current_index[ref_key]['hash']
            
            if found_candidate is not None:
                results.append(("located", found_namespace, found_candidate, found_hash))
            else:
                results.append(("missing", namespace, None, None))
    
    return results


def parse_text(text, namespace):
    if not text:
        return False, None, None
    
    parts = text.split('.')
    version = None
    
    terminal = parts[-1]
    if '@' in terminal:
        if namespace == "type":
            return False, None, None
        
        parts_of_terminal = terminal.rsplit('@', 1)
        version_str = parts_of_terminal[1]
        
        if not version_str or not version_str.isdigit():
            return False, None, None
        if len(version_str) > 1 and version_str[0] == '0':
            return False, None, None
        version = int(version_str)
        
        parts[-1] = parts_of_terminal[0]
        terminal = parts[-1]
    
    if not terminal:
        return False, None, None
    
    for i, part in enumerate(parts):
        if not part:
            return False, None, None
        if not all(c.isalnum() or c == '_' for c in part):
            return False, None, None
        
        first_char = part[0]
        if i == len(parts) - 1:
            if namespace == "type":
                if not first_char.isupper():
                    return False, None, None
            else:
                if not first_char.islower():
                    return False, None, None
        else:
            if not first_char.islower():
                return False, None, None
    
    return True, '.'.join(parts), version


def generate_candidates(context_parts, parsed_name):
    candidates = []
    for i in range(len(context_parts), 0, -1):
        prefix = '.'.join(context_parts[-i:])
        candidates.append(prefix + '.' + parsed_name)
    candidates.append(parsed_name)
    return candidates