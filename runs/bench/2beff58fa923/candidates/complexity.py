def refresh_references(initial, snapshots, references):
    current_state = {}
    for namespace, name, version, hash_val in initial:
        key = (namespace, name, version)
        current_state[key] = hash_val
    
    states = [dict(current_state)]
    for snapshot in snapshots:
        for namespace, name, version, hash_val in snapshot:
            key = (namespace, name, version)
            if hash_val is None:
                current_state.pop(key, None)
            else:
                current_state[key] = hash_val
        states.append(dict(current_state))
    
    results = []
    
    for ref in references:
        namespace, text, context, location, hash_val, start = ref
        
        # Validate and parse text
        if not text:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        parts = text.split('.')
        if not parts:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        # All parts must be valid identifiers
        valid = all(p and all(c.isalnum() or c == '_' for c in p) for p in parts)
        if not valid:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        # Module parts must start with lowercase
        if not all(p[0] in 'abcdefghijklmnopqrstuvwxyz' for p in parts[:-1]):
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        # Parse terminal
        terminal = parts[-1]
        version_num = None
        
        if '@' in terminal:
            at_parts = terminal.split('@')
            if len(at_parts) != 2 or not at_parts[1]:
                results.append(("invalid", namespace, location, hash_val))
                continue
            
            base, ver_str = at_parts
            if not base or not all(c.isalnum() or c == '_' for c in base):
                results.append(("invalid", namespace, location, hash_val))
                continue
            
            if ver_str[0] == '0' and len(ver_str) > 1:
                results.append(("invalid", namespace, location, hash_val))
                continue
            
            if not ver_str.isdigit():
                results.append(("invalid", namespace, location, hash_val))
                continue
            
            version_num = int(ver_str)
            terminal = base
        
        # Validate terminal
        if namespace == "type":
            if terminal[0] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' or version_num is not None:
                results.append(("invalid", namespace, location, hash_val))
                continue
        else:
            if terminal[0] not in 'abcdefghijklmnopqrstuvwxyz':
                results.append(("invalid", namespace, location, hash_val))
                continue
        
        # Process location-authoritative or location-less
        if location is not None:
            key = (namespace, location, None if namespace == "type" else version_num)
            current_hash = hash_val
            for state in states[start:]:
                if key in state:
                    current_hash = state[key]
            results.append(("located", namespace, location, current_hash))
        else:
            context_parts = context.split('.') if context else []
            candidates = []
            for i in range(len(context_parts), -1, -1):
                prefix = '.'.join(context_parts[:i])
                candidate = (prefix + '.' + terminal) if prefix else terminal
                candidates.append(candidate)
            
            found = False
            result_ns, result_loc, result_hash = namespace, None, None
            
            for state in states[start:]:
                if found:
                    break
                
                search_list = ["value", "function"] if namespace == "value" else [namespace]
                for search_ns in search_list:
                    if found:
                        break
                    for cand in candidates:
                        key = (search_ns, cand, None if search_ns == "type" else version_num)
                        if key in state:
                            found = True
                            result_ns, result_loc, result_hash = search_ns, cand, state[key]
                            break
            
            if found:
                results.append(("located", result_ns, result_loc, result_hash))
            else:
                results.append(("missing", namespace, None, None))
    
    return results