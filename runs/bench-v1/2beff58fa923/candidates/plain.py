def refresh_references(initial, snapshots, references):
    def is_valid_identifier(s, start_case='lowercase'):
        if not s:
            return False
        if start_case == 'lowercase' and not s[0].islower():
            return False
        if start_case == 'uppercase' and not s[0].isupper():
            return False
        return all(c.isalnum() or c == '_' for c in s)
    
    # Build snapshots_states
    current_state = {}
    for entry in initial:
        namespace, name, version, hash_val = entry
        key = (namespace, name, version)
        current_state[key] = hash_val
    
    snapshots_states = [dict(current_state)]
    
    for batch in snapshots:
        for update in batch:
            namespace, name, version, hash_val = update
            key = (namespace, name, version)
            if hash_val is None:
                current_state.pop(key, None)
            else:
                current_state[key] = hash_val
        snapshots_states.append(dict(current_state))
    
    results = []
    
    for ref in references:
        namespace, text, context, location, hash_val, start = ref
        
        # Parse and validate text
        is_valid = True
        parsed_name = None
        parsed_version = None
        
        if not text:
            is_valid = False
        else:
            parts = text.split('.')
            
            if any(not p for p in parts):
                is_valid = False
            else:
                for i in range(len(parts) - 1):
                    if not is_valid_identifier(parts[i], 'lowercase'):
                        is_valid = False
                        break
                
                if is_valid:
                    terminal = parts[-1]
                    
                    if namespace == "type":
                        if '@' in terminal:
                            is_valid = False
                        elif not is_valid_identifier(terminal, 'uppercase'):
                            is_valid = False
                        else:
                            parsed_name = text
                            parsed_version = None
                    else:
                        if '@' in terminal:
                            at_pos = terminal.rfind('@')
                            name_part = terminal[:at_pos]
                            version_part = terminal[at_pos+1:]
                            
                            if not name_part or not is_valid_identifier(name_part, 'lowercase'):
                                is_valid = False
                            elif not version_part or not version_part.isdigit() or version_part != str(int(version_part)):
                                is_valid = False
                            else:
                                parsed_version = int(version_part)
                                parts[-1] = name_part
                                parsed_name = '.'.join(parts)
                        else:
                            if not is_valid_identifier(terminal, 'lowercase'):
                                is_valid = False
                            else:
                                parsed_name = text
                                parsed_version = None
        
        if not is_valid:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        if location is not None:
            key = (namespace, location, parsed_version)
            retained_hash = hash_val
            for snapshot_idx in range(start, len(snapshots_states)):
                state = snapshots_states[snapshot_idx]
                if key in state:
                    retained_hash = state[key]
            
            results.append(("located", namespace, location, retained_hash))
        else:
            context_parts = context.split('.') if context else []
            
            candidates = []
            for i in range(len(context_parts), -1, -1):
                prefix = '.'.join(context_parts[:i]) if i > 0 else ''
                candidate = (prefix + '.' + parsed_name) if prefix else parsed_name
                candidates.append(candidate)
            
            found_location = None
            found_namespace = namespace
            found_hash = None
            
            for snapshot_idx in range(start, len(snapshots_states)):
                if found_location is not None:
                    state = snapshots_states[snapshot_idx]
                    key = (found_namespace, found_location, parsed_version)
                    if key in state:
                        found_hash = state[key]
                else:
                    state = snapshots_states[snapshot_idx]
                    
                    if namespace == "value":
                        for candidate in candidates:
                            key = ("value", candidate, parsed_version)
                            if key in state:
                                found_location = candidate
                                found_namespace = "value"
                                found_hash = state[key]
                                break
                        
                        if found_location is None:
                            for candidate in candidates:
                                key = ("function", candidate, parsed_version)
                                if key in state:
                                    found_location = candidate
                                    found_namespace = "function"
                                    found_hash = state[key]
                                    break
                    else:
                        for candidate in candidates:
                            key = (namespace, candidate, parsed_version)
                            if key in state:
                                found_location = candidate
                                found_hash = state[key]
                                break
            
            if found_location is None:
                results.append(("missing", namespace, None, None))
            else:
                results.append(("located", found_namespace, found_location, found_hash))
    
    return results