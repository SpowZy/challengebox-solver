def refresh_references(initial, snapshots, references):
    results = []
    
    for ref in references:
        namespace = ref['namespace']
        text = ref['text']
        context = ref['context']
        location = ref['location']
        hash_val = ref['hash']
        start = ref['start']
        
        # Parse and validate text
        parts = text.split('.')
        if not parts or not parts[-1]:
            results.append(('invalid', namespace, location, hash_val))
            continue
        
        terminal = parts[-1]
        module_parts = parts[:-1]
        
        # Parse @N suffix
        version = None
        if '@' in terminal:
            split = terminal.rsplit('@', 1)
            if len(split) == 2:
                terminal_name, version_str = split
                if namespace == "type":
                    results.append(('invalid', namespace, location, hash_val))
                    continue
                try:
                    if not version_str or (version_str[0] == '0' and len(version_str) > 1):
                        results.append(('invalid', namespace, location, hash_val))
                        continue
                    version = int(version_str)
                except ValueError:
                    results.append(('invalid', namespace, location, hash_val))
                    continue
                terminal = terminal_name
            else:
                results.append(('invalid', namespace, location, hash_val))
                continue
        
        # Validate terminal
        if not terminal or not terminal[0].isalpha():
            results.append(('invalid', namespace, location, hash_val))
            continue
        
        if namespace == "type" and not terminal[0].isupper():
            results.append(('invalid', namespace, location, hash_val))
            continue
        elif namespace != "type" and not terminal[0].islower():
            results.append(('invalid', namespace, location, hash_val))
            continue
        
        # Validate all identifier parts
        valid = all(part and all(c.isalnum() or c == '_' for c in part) for part in module_parts + [terminal])
        if not valid:
            results.append(('invalid', namespace, location, hash_val))
            continue
        
        # Valid reference - process snapshots
        current_namespace = namespace
        current_location = location
        current_hash = hash_val
        resolved = location is not None
        
        # Initialize state to snapshot start
        state = {}
        for entry in initial:
            key = (entry['namespace'], entry['name'], entry['version'])
            state[key] = entry['hash']
        
        # Apply batches 0 to start-1
        for batch_idx in range(start):
            for update in snapshots[batch_idx]:
                key = (update['namespace'], update['name'], update['version'])
                if update['hash'] is None:
                    state.pop(key, None)
                else:
                    state[key] = update['hash']
        
        context_parts = context.split('.') if context else []
        
        # Process snapshots start through len(snapshots)
        for snap_idx in range(start, len(snapshots) + 1):
            if location is not None:
                key = (current_namespace, terminal, version)
                if key in state:
                    current_hash = state[key]
            else:
                if not resolved:
                    if current_namespace in ["type", "function"]:
                        for prefix_len in range(len(context_parts), -1, -1):
                            if prefix_len > 0:
                                candidate_name = '.'.join(context_parts[:prefix_len]) + '.' + terminal
                            else:
                                candidate_name = terminal
                            key = (current_namespace, candidate_name, version)
                            if key in state:
                                current_location = candidate_name
                                current_hash = state[key]
                                resolved = True
                                break
                    else:
                        found = False
                        for prefix_len in range(len(context_parts), -1, -1):
                            if prefix_len > 0:
                                candidate_name = '.'.join(context_parts[:prefix_len]) + '.' + terminal
                            else:
                                candidate_name = terminal
                            key = ('value', candidate_name, version)
                            if key in state:
                                current_location = candidate_name
                                current_hash = state[key]
                                resolved = True
                                found = True
                                break
                        if not found:
                            for prefix_len in range(len(context_parts), -1, -1):
                                if prefix_len > 0:
                                    candidate_name = '.'.join(context_parts[:prefix_len]) + '.' + terminal
                                else:
                                    candidate_name = terminal
                                key = ('function', candidate_name, version)
                                if key in state:
                                    current_location = candidate_name
                                    current_hash = state[key]
                                    current_namespace = 'function'
                                    resolved = True
                                    break
            
            if snap_idx < len(snapshots):
                for update in snapshots[snap_idx]:
                    key = (update['namespace'], update['name'], update['version'])
                    if update['hash'] is None:
                        state.pop(key, None)
                    else:
                        state[key] = update['hash']
        
        if not resolved and location is None:
            results.append(('missing', current_namespace, None, None))
        else:
            results.append(('located', current_namespace, current_location, current_hash))
    
    return results