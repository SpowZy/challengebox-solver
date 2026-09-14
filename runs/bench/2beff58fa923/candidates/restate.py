def refresh_references(initial, snapshots, references):
    # Build snapshots state
    snapshots_state = []
    
    # Initial state
    current_state = {}
    for entry in initial:
        key = (entry['namespace'], entry['name'], entry['version'])
        current_state[key] = entry['hash']
    
    snapshots_state.append(current_state.copy())
    
    # Apply each batch
    for batch in snapshots:
        current_state = current_state.copy()
        for update in batch:
            key = (update['namespace'], update['name'], update['version'])
            if update['hash'] is None:
                if key in current_state:
                    del current_state[key]
            else:
                current_state[key] = update['hash']
        snapshots_state.append(current_state.copy())
    
    # Process references
    results = []
    
    for ref in references:
        ref_namespace = ref['namespace']
        ref_text = ref['text']
        ref_context = ref['context']
        ref_location = ref['location']
        ref_hash = ref['hash']
        ref_start = ref['start']
        
        # Validate text format
        if not ref_text:
            results.append(("invalid", ref_namespace, ref_location, ref_hash))
            continue
        
        parts = ref_text.split('.')
        if not all(parts):
            results.append(("invalid", ref_namespace, ref_location, ref_hash))
            continue
        
        valid = True
        for part in parts:
            if not part or not all(c.isalnum() or c == '_' for c in part):
                valid = False
                break
        
        if not valid:
            results.append(("invalid", ref_namespace, ref_location, ref_hash))
            continue
        
        # Extract terminal and modules
        terminal = parts[-1]
        modules = parts[:-1]
        
        # Validate module identifiers start with lowercase
        for mod in modules:
            if not mod[0].islower():
                results.append(("invalid", ref_namespace, ref_location, ref_hash))
                valid = False
                break
        
        if not valid:
            continue
        
        # Parse terminal for version suffix
        version_suffix = None
        terminal_name = terminal
        
        if ref_namespace != 'type':
            if '@' in terminal:
                parts_split = terminal.rsplit('@', 1)
                base, suffix = parts_split
                if suffix and suffix.isdigit() and (suffix == '0' or not suffix.startswith('0')):
                    terminal_name = base
                    version_suffix = int(suffix)
                else:
                    results.append(("invalid", ref_namespace, ref_location, ref_hash))
                    continue
        else:
            if '@' in terminal:
                results.append(("invalid", ref_namespace, ref_location, ref_hash))
                continue
        
        if not terminal_name:
            results.append(("invalid", ref_namespace, ref_location, ref_hash))
            continue
        
        if ref_namespace == 'type':
            if not terminal_name[0].isupper():
                results.append(("invalid", ref_namespace, ref_location, ref_hash))
                continue
        else:
            if not terminal_name[0].islower():
                results.append(("invalid", ref_namespace, ref_location, ref_hash))
                continue
        
        # Validate context
        context_parts = []
        if ref_context:
            context_parts = ref_context.split('.')
            if not all(context_parts):
                results.append(("invalid", ref_namespace, ref_location, ref_hash))
                continue
            for ctx_part in context_parts:
                if not ctx_part[0].islower():
                    results.append(("invalid", ref_namespace, ref_location, ref_hash))
                    valid = False
                    break
            if not valid:
                continue
        
        # If location is provided, it's location-authoritative
        if ref_location is not None:
            current_hash = ref_hash
            for snapshot_idx in range(ref_start, len(snapshots_state)):
                state = snapshots_state[snapshot_idx]
                ver = version_suffix if ref_namespace != 'type' else None
                key = (ref_namespace, ref_location, ver)
                if key in state:
                    current_hash = state[key]
            
            results.append(("located", ref_namespace, ref_location, current_hash))
            continue
        
        # For location-less reference, form candidates
        qualified_name = '.'.join(modules + [terminal_name])
        
        candidates = []
        for i in range(len(context_parts), -1, -1):
            if i == 0:
                candidate = qualified_name
            else:
                prefix = '.'.join(context_parts[:i])
                candidate = prefix + '.' + qualified_name
            candidates.append(candidate)
        
        # Search for match across snapshots
        matched_namespace = ref_namespace
        matched_location = None
        matched_hash = None
        
        for snapshot_idx in range(ref_start, len(snapshots_state)):
            state = snapshots_state[snapshot_idx]
            
            if ref_namespace in ('type', 'function'):
                for candidate in candidates:
                    ver = version_suffix if ref_namespace != 'type' else None
                    key = (ref_namespace, candidate, ver)
                    if key in state:
                        matched_location = candidate
                        matched_hash = state[key]
                        break
            else:
                for candidate in candidates:
                    key = ('value', candidate, version_suffix)
                    if key in state:
                        matched_namespace = 'value'
                        matched_location = candidate
                        matched_hash = state[key]
                        break
                
                if matched_location is None:
                    for candidate in candidates:
                        key = ('function', candidate, version_suffix)
                        if key in state:
                            matched_namespace = 'function'
                            matched_location = candidate
                            matched_hash = state[key]
                            break
            
            if matched_location is not None:
                break
        
        if matched_location is not None:
            results.append(("located", matched_namespace, matched_location, matched_hash))
        else:
            results.append(("missing", ref_namespace, None, None))
    
    return results