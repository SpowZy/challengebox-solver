def refresh_references(initial, snapshots, references):
    # Build snapshots from initial and batch updates
    all_snapshots = [{}]
    for e in initial:
        key = (e['namespace'], e['name'], e['version'])
        all_snapshots[0][key] = e['hash']
    
    current_entries = dict(all_snapshots[0])
    
    for batch in snapshots:
        for update in batch:
            key = (update['namespace'], update['name'], update['version'])
            if update['hash'] is None:
                current_entries.pop(key, None)
            else:
                current_entries[key] = update['hash']
        all_snapshots.append(dict(current_entries))
    
    results = []
    
    for ref in references:
        namespace = ref['namespace']
        text = ref['text']
        context = ref['context']
        location = ref['location']
        hash_val = ref['hash']
        start = ref['start']
        
        # Validate context
        is_valid = True
        if context:
            context_parts = context.split('.')
            for part in context_parts:
                if not part or part[0] not in 'abcdefghijklmnopqrstuvwxyz' or not all(c.isalnum() or c == '_' for c in part):
                    is_valid = False
                    break
        
        if not is_valid:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        # Validate and parse text
        if not text:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        text_parts = text.split('.')
        module_parts = text_parts[:-1]
        terminal = text_parts[-1]
        
        # Validate module parts
        for part in module_parts:
            if not part or part[0] not in 'abcdefghijklmnopqrstuvwxyz' or not all(c.isalnum() or c == '_' for c in part):
                is_valid = False
                break
        
        if not is_valid:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        # Parse terminal and extract version if present
        version = None
        terminal_name = terminal
        
        if '@' in terminal:
            if namespace == "type":
                is_valid = False
            else:
                parts = terminal.rsplit('@', 1)
                terminal_name = parts[0]
                version_str = parts[1]
                
                if not version_str or not version_str.isdigit() or (len(version_str) > 1 and version_str[0] == '0'):
                    is_valid = False
                else:
                    version = int(version_str)
        
        if not is_valid:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        # Validate terminal name
        if not terminal_name:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        if namespace == "type":
            if terminal_name[0] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' or not all(c.isalnum() or c == '_' for c in terminal_name):
                results.append(("invalid", namespace, location, hash_val))
                continue
        else:
            if terminal_name[0] not in 'abcdefghijklmnopqrstuvwxyz' or not all(c.isalnum() or c == '_' for c in terminal_name):
                results.append(("invalid", namespace, location, hash_val))
                continue
        
        # Reference is valid - now determine location and hash
        qualified_name_parts = module_parts + [terminal_name]
        
        if location is not None:
            # Location-authoritative reference
            current_hash = hash_val
            for snapshot_idx in range(start, len(all_snapshots)):
                key = (namespace, location, version)
                if key in all_snapshots[snapshot_idx]:
                    current_hash = all_snapshots[snapshot_idx][key]
            results.append(("located", namespace, location, current_hash))
        else:
            # Location-less reference - search for match
            context_parts = context.split('.') if context else []
            
            # Build candidates by prepending context prefixes
            candidates = []
            for prefix_len in range(len(context_parts), -1, -1):
                prefix = context_parts[:prefix_len]
                candidate_parts = prefix + qualified_name_parts
                candidate = '.'.join(candidate_parts)
                candidates.append(candidate)
            
            found = False
            matched_namespace = namespace
            matched_location = None
            matched_hash = None
            
            # Search through snapshots starting from 'start'
            for snapshot_idx in range(start, len(all_snapshots)):
                if found:
                    break
                snapshot = all_snapshots[snapshot_idx]
                
                if namespace == "value":
                    # Value references search values first, then functions
                    for candidate in candidates:
                        key = ("value", candidate, version)
                        if key in snapshot:
                            matched_location = candidate
                            matched_hash = snapshot[key]
                            matched_namespace = "value"
                            found = True
                            break
                    
                    if not found:
                        for candidate in candidates:
                            key = ("function", candidate, version)
                            if key in snapshot:
                                matched_location = candidate
                                matched_hash = snapshot[key]
                                matched_namespace = "function"
                                found = True
                                break
                else:
                    # Type and function references search only their namespace
                    for candidate in candidates:
                        key = (namespace, candidate, version)
                        if key in snapshot:
                            matched_location = candidate
                            matched_hash = snapshot[key]
                            found = True
                            break
            
            if found:
                results.append(("located", matched_namespace, matched_location, matched_hash))
            else:
                results.append(("missing", namespace, None, None))
    
    return results