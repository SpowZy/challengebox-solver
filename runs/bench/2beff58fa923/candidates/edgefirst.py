def refresh_references(initial, snapshots, references):
    import re
    
    def validate_text(text, namespace):
        if not text:
            return None
        parts = text.split('.')
        for p in parts[:-1]:
            if not re.match(r'^[a-z][a-zA-Z0-9_]*$', p):
                return None
        terminal = parts[-1]
        if namespace == "type":
            if not re.match(r'^[A-Z][a-zA-Z0-9_]*$', terminal):
                return None
            return {'name': '.'.join(parts), 'version': None}
        elif namespace in ["function", "value"]:
            match = re.match(r'^([a-z][a-zA-Z0-9_]*)(?:@(0|[1-9]\d*))?$', terminal)
            if not match:
                return None
            base, ver = match.group(1), match.group(2)
            name = '.'.join(parts[:-1] + [base])
            return {'name': name, 'version': int(ver) if ver else None}
        return None
    
    # Build state snapshots
    state = {}
    for entry in initial:
        key = (entry['namespace'], entry['name'], entry['version'])
        state[key] = entry['hash']
    
    states = [state.copy()]
    
    for batch in snapshots:
        for update in batch:
            key = (update['namespace'], update['name'], update['version'])
            if update['hash'] is None:
                state.pop(key, None)
            else:
                state[key] = update['hash']
        states.append(state.copy())
    
    # Process references
    results = []
    for ref in references:
        ns, text, ctx, loc, h, start = ref['namespace'], ref['text'], ref['context'], ref['location'], ref['hash'], ref['start']
        
        parsed = validate_text(text, ns)
        if parsed is None:
            results.append(("invalid", ns, loc, h))
            continue
        
        name, version = parsed['name'], parsed['version']
        
        if loc is not None:
            # Location-authoritative
            current_hash = h
            key = (ns, name, version)
            for i in range(start, len(states)):
                if key in states[i]:
                    current_hash = states[i][key]
            results.append(("located", ns, loc, current_hash))
        else:
            # Location-less
            context_parts = ctx.split('.') if ctx else []
            candidates = []
            for i in range(len(context_parts), -1, -1):
                if i > 0:
                    candidates.append('.'.join(context_parts[:i]) + '.' + name)
                else:
                    candidates.append(name)
            
            matched = False
            matched_location = None
            matched_ns = ns
            current_hash = None
            
            for snap_idx in range(start, len(states)):
                if ns == "type":
                    for cand in candidates:
                        if ("type", cand, None) in states[snap_idx]:
                            matched = True
                            matched_location = cand
                            current_hash = states[snap_idx][("type", cand, None)]
                            break
                elif ns == "function":
                    for cand in candidates:
                        if ("function", cand, version) in states[snap_idx]:
                            matched = True
                            matched_location = cand
                            current_hash = states[snap_idx][("function", cand, version)]
                            break
                else:  # value
                    for cand in candidates:
                        if ("value", cand, version) in states[snap_idx]:
                            matched = True
                            matched_location = cand
                            current_hash = states[snap_idx][("value", cand, version)]
                            break
                    if not matched:
                        for cand in candidates:
                            if ("function", cand, version) in states[snap_idx]:
                                matched = True
                                matched_location = cand
                                matched_ns = "function"
                                current_hash = states[snap_idx][("function", cand, version)]
                                break
                
                if matched:
                    # Location-authoritative from this point on
                    for j in range(snap_idx + 1, len(states)):
                        k = (matched_ns, matched_location, None if matched_ns == "type" else version)
                        if k in states[j]:
                            current_hash = states[j][k]
                    break
            
            if matched:
                results.append(("located", matched_ns, matched_location, current_hash))
            else:
                results.append(("missing", ns, None, None))
    
    return results