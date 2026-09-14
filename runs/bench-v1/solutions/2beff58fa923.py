def refresh_references(initial, snapshots, references):
    db_snapshots = [{}]
    
    for entry in initial:
        namespace, name, version, hash_val = entry['namespace'], entry['name'], entry['version'], entry['hash']
        key = (namespace, name, version)
        if namespace not in db_snapshots[0]:
            db_snapshots[0][namespace] = {}
        db_snapshots[0][namespace][key] = hash_val
    
    for batch in snapshots:
        prev_snapshot = db_snapshots[-1]
        new_snapshot = {}
        
        for namespace in prev_snapshot:
            new_snapshot[namespace] = dict(prev_snapshot[namespace])
        
        for update in batch:
            namespace, name, version, hash_val = update['namespace'], update['name'], update['version'], update['hash']
            if namespace not in new_snapshot:
                new_snapshot[namespace] = {}
            
            key = (namespace, name, version)
            if hash_val is None:
                if key in new_snapshot[namespace]:
                    del new_snapshot[namespace][key]
            else:
                new_snapshot[namespace][key] = hash_val
        
        db_snapshots.append(new_snapshot)
    
    results = []
    
    for ref in references:
        namespace = ref['namespace']
        text = ref['text']
        context = ref.get('context', '')
        location = ref.get('location')
        hash_val = ref.get('hash')
        start = ref.get('start', 0)
        
        parts = text.split('.') if text else []
        is_invalid = False
        terminal = None
        terminal_version = None
        
        if len(parts) == 0:
            is_invalid = True
        else:
            last_part = parts[-1]
            if '@' in last_part:
                if namespace == 'type':
                    is_invalid = True
                else:
                    suffix_parts = last_part.rsplit('@', 1)
                    if len(suffix_parts) == 2:
                        name_part, version_str = suffix_parts
                        if name_part and version_str and (version_str[0] != '0' or len(version_str) == 1) and version_str.isdigit():
                            terminal = name_part
                            terminal_version = int(version_str)
                            parts[-1] = terminal
                        else:
                            is_invalid = True
                    else:
                        is_invalid = True
            else:
                terminal = last_part
        
        if not is_invalid:
            for i, part in enumerate(parts):
                if not part or not all(c.isalnum() or c == '_' for c in part):
                    is_invalid = True
                    break
                if i == len(parts) - 1:
                    if namespace == 'type' and not part[0].isupper():
                        is_invalid = True
                    elif namespace != 'type' and not part[0].islower():
                        is_invalid = True
                elif not part[0].islower():
                    is_invalid = True
        
        if is_invalid:
            results.append(("invalid", ref['namespace'], ref.get('location'), ref.get('hash')))
            continue
        
        qualified_name = '.'.join(parts)
        
        if location is not None:
            current_hash = hash_val
            for snap_idx in range(start, len(db_snapshots)):
                snapshot = db_snapshots[snap_idx]
                key = (namespace, location, terminal_version)
                if namespace in snapshot and key in snapshot[namespace]:
                    current_hash = snapshot[namespace][key]
            results.append(("located", namespace, location, current_hash))
        else:
            context_parts = context.split('.') if context else []
            candidates = []
            for i in range(len(context_parts), -1, -1):
                if i == 0:
                    candidates.append(qualified_name)
                else:
                    candidates.append('.'.join(context_parts[:i]) + '.' + qualified_name)
            
            matched = False
            matched_location = None
            matched_hash = None
            matched_namespace = namespace
            match_snapshot_idx = None
            
            for snap_idx in range(start, len(db_snapshots)):
                snapshot = db_snapshots[snap_idx]
                
                if namespace == 'value':
                    for candidate in candidates:
                        if 'value' in snapshot and ('value', candidate, terminal_version) in snapshot['value']:
                            matched, matched_location, matched_hash = True, candidate, snapshot['value'][('value', candidate, terminal_version)]
                            matched_namespace = 'value'
                            match_snapshot_idx = snap_idx
                            break
                    if not matched:
                        for candidate in candidates:
                            if 'function' in snapshot and ('function', candidate, terminal_version) in snapshot['function']:
                                matched, matched_location, matched_hash = True, candidate, snapshot['function'][('function', candidate, terminal_version)]
                                matched_namespace = 'function'
                                match_snapshot_idx = snap_idx
                                break
                else:
                    for candidate in candidates:
                        if namespace in snapshot and (namespace, candidate, terminal_version) in snapshot[namespace]:
                            matched, matched_location, matched_hash = True, candidate, snapshot[namespace][(namespace, candidate, terminal_version)]
                            match_snapshot_idx = snap_idx
                            break
                
                if matched:
                    break
            
            if matched:
                for snap_idx in range(match_snapshot_idx + 1, len(db_snapshots)):
                    snapshot = db_snapshots[snap_idx]
                    if matched_namespace in snapshot and (matched_namespace, matched_location, terminal_version) in snapshot[matched_namespace]:
                        matched_hash = snapshot[matched_namespace][(matched_namespace, matched_location, terminal_version)]
                results.append(("located", matched_namespace, matched_location, matched_hash))
            else:
                results.append(("missing", namespace, None, None))
    
    return results