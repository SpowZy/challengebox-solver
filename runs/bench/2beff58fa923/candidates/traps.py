def refresh_references(initial, snapshots, references):
    states = [{}]
    current_state = {}
    
    for entry in initial:
        key = (entry['namespace'], entry['name'], entry['version'])
        current_state[key] = entry['hash']
    states[0] = dict(current_state)
    
    for snapshot in snapshots:
        for update in snapshot:
            key = (update['namespace'], update['name'], update['version'])
            if update['hash'] is None:
                current_state.pop(key, None)
            else:
                current_state[key] = update['hash']
        states.append(dict(current_state))
    
    results = []
    
    for reference in references:
        namespace = reference['namespace']
        text = reference['text']
        context = reference['context']
        location = reference['location']
        hash_val = reference['hash']
        start = reference['start']
        
        parts = text.split('.')
        if not text or any(not p for p in parts):
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        terminal = parts[-1]
        version = None
        
        if '@' in terminal and namespace in ['function', 'value']:
            base, suffix = terminal.rsplit('@', 1)
            if suffix and (suffix == '0' or (suffix[0] != '0' and suffix.isdigit())):
                terminal = base
                version = int(suffix)
            else:
                results.append(("invalid", namespace, location, hash_val))
                continue
        
        valid = True
        for part in parts[:-1] + [terminal]:
            if not part or not all(c.isalnum() or c == '_' for c in part):
                valid = False
                break
        
        if not valid:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        for part in parts[:-1]:
            if part[0] not in 'abcdefghijklmnopqrstuvwxyz':
                valid = False
                break
        
        if not valid:
            results.append(("invalid", namespace, location, hash_val))
            continue
        
        if namespace == 'type':
            if terminal[0] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                results.append(("invalid", namespace, location, hash_val))
                continue
        else:
            if terminal[0] not in 'abcdefghijklmnopqrstuvwxyz':
                results.append(("invalid", namespace, location, hash_val))
                continue
        
        fq_name = text.rsplit('@', 1)[0] if '@' in text else text
        
        if location is not None:
            key = (namespace, fq_name, version if namespace != 'type' else None)
            current_hash = hash_val
            for idx in range(start, len(states)):
                if key in states[idx]:
                    current_hash = states[idx][key]
            results.append(("located", namespace, location, current_hash))
            continue
        
        context_parts = context.split('.') if context else []
        candidates = []
        
        for i in range(len(context_parts), -1, -1):
            prefix_parts = context_parts[:i]
            cand_name = '.'.join(prefix_parts + [fq_name]) if prefix_parts else fq_name
            
            if namespace == 'type':
                candidates.append(('type', cand_name, None))
            else:
                candidates.append((namespace, cand_name, version))
        
        if namespace == 'value':
            for i in range(len(context_parts), -1, -1):
                prefix_parts = context_parts[:i]
                cand_name = '.'.join(prefix_parts + [fq_name]) if prefix_parts else fq_name
                candidates.append(('function', cand_name, version))
        
        found = False
        for idx in range(start, len(states)):
            for cand_ns, cand_name, cand_version in candidates:
                key = (cand_ns, cand_name, cand_version)
                if key in states[idx]:
                    results.append(("located", cand_ns, cand_name, states[idx][key]))
                    found = True
                    break
            if found:
                break
        
        if not found:
            results.append(("missing", namespace, None, None))
    
    return results