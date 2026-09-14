def refresh_references(initial, snapshots, references):
    def build_state(entries):
        state = {}
        for entry in entries:
            key = (entry['namespace'], entry['name'], entry['version'])
            state[key] = entry['hash']
        return state
    
    states = [build_state(initial)]
    
    for batch in snapshots:
        prev_state = states[-1].copy()
        for update in batch:
            key = (update['namespace'], update['name'], update['version'])
            if update.get('hash') is None:
                if key in prev_state:
                    del prev_state[key]
            else:
                prev_state[key] = update['hash']
        states.append(prev_state)
    
    results = []
    
    for ref in references:
        namespace = ref['namespace']
        text = ref['text']
        context = ref.get('context') or ""
        location = ref.get('location')
        hash_val = ref.get('hash')
        start = ref['start']
        
        if not text:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        parts = text.split('.')
        terminal = parts[-1]
        version = None
        
        if '@' in terminal:
            if namespace == "type":
                results.append(("invalid", namespace, location, hash_val))
                continue
            
            at_idx = terminal.rfind('@')
            base_terminal = terminal[:at_idx]
            version_str = terminal[at_idx+1:]
            
            if not base_terminal or not version_str or not version_str.isdigit() or (len(version_str) > 1 and version_str[0] == '0'):
                results.append(("invalid", namespace, location, hash_val))
                continue
            
            version = int(version_str)
            terminal = base_terminal
            parts[-1] = terminal
        
        def is_valid_id(s):
            return s and all(c.isalnum() or c == '_' for c in s)
        
        valid = True
        for mod in parts[:-1]:
            if not is_valid_id(mod) or mod[0] not in 'abcdefghijklmnopqrstuvwxyz':
                valid = False
                break
        
        if valid:
            if not is_valid_id(terminal):
                valid = False
            elif namespace == "type":
                if terminal[0] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    valid = False
            else:
                if terminal[0] not in 'abcdefghijklmnopqrstuvwxyz':
                    valid = False
        
        if not valid:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        qualified_name = '.'.join(parts)
        
        if location is not None:
            key = (namespace, location, version)
            current_hash = hash_val
            
            for snap_idx in range(start, len(states)):
                if key in states[snap_idx]:
                    current_hash = states[snap_idx][key]
            
            results.append(("located", namespace, location, current_hash))
        else:
            context_parts = context.split('.') if context else []
            candidates = []
            
            for i in range(len(context_parts), -1, -1):
                prefix = context_parts[:i]
                candidate = '.'.join(prefix) + '.' + qualified_name if prefix else qualified_name
                candidates.append(candidate)
            
            found = False
            found_location = None
            found_hash = None
            found_namespace = namespace
            
            for snap_idx in range(start, len(states)):
                state = states[snap_idx]
                
                if namespace == "value":
                    for candidate in candidates:
                        key = ("value", candidate, version)
                        if key in state:
                            found = True
                            found_location = candidate
                            found_hash = state[key]
                            found_namespace = "value"
                            break
                    
                    if not found:
                        for candidate in candidates:
                            key = ("function", candidate, version)
                            if key in state:
                                found = True
                                found_location = candidate
                                found_hash = state[key]
                                found_namespace = "function"
                                break
                else:
                    for candidate in candidates:
                        key = (namespace, candidate, version)
                        if key in state:
                            found = True
                            found_location = candidate
                            found_hash = state[key]
                            break
                
                if found:
                    break
            
            if found:
                results.append(("located", found_namespace, found_location, found_hash))
            else:
                results.append(("missing", namespace, None, None))
    
    return results