def refresh_references(initial, snapshots, references):
    def is_module_id(s):
        if not s or s[0] not in 'abcdefghijklmnopqrstuvwxyz':
            return False
        return all(c.isalnum() or c == '_' for c in s)
    
    def parse_text(text, ref_namespace):
        if not text:
            return None
        
        parts = text.split('.')
        if not parts or any(not p for p in parts):
            return None
        
        modules = parts[:-1]
        terminal = parts[-1]
        
        for mod in modules:
            if not is_module_id(mod):
                return None
        
        version = None
        name = terminal
        
        if '@' in terminal:
            if ref_namespace == 'type':
                return None
            
            idx = terminal.rfind('@')
            name = terminal[:idx]
            version_str = terminal[idx+1:]
            
            if not name or not version_str:
                return None
            
            if version_str[0] == '0' and len(version_str) > 1:
                return None
            if not version_str.isdigit():
                return None
            
            version = int(version_str)
        
        if not name or not all(c.isalnum() or c == '_' for c in name):
            return None
        
        first = name[0]
        if ref_namespace == 'type':
            if first not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                return None
        else:
            if first not in 'abcdefghijklmnopqrstuvwxyz':
                return None
        
        return {'modules': modules, 'name': name, 'version': version}
    
    current = {}
    if initial:
        for entry in initial:
            key = (entry['namespace'], entry['name'], entry['version'])
            current[key] = entry['hash']
    
    snapshots_list = [dict(current)]
    
    if snapshots:
        for batch in snapshots:
            for update in batch:
                key = (update['namespace'], update['name'], update['version'])
                if update.get('hash') is None:
                    current.pop(key, None)
                else:
                    current[key] = update['hash']
            snapshots_list.append(dict(current))
    
    results = []
    
    for ref in references:
        parsed = parse_text(ref['text'], ref['namespace'])
        
        if parsed is None:
            results.append(("invalid", ref['namespace'], ref['location'], ref['hash']))
            continue
        
        if ref['location'] is not None:
            key = (ref['namespace'], ref['location'], parsed['version'])
            current_hash = ref['hash']
            for snap_idx in range(ref['start'], len(snapshots_list)):
                if key in snapshots_list[snap_idx]:
                    current_hash = snapshots_list[snap_idx][key]
            results.append(("located", ref['namespace'], ref['location'], current_hash))
        else:
            context_str = ref.get('context', '')
            context_parts = context_str.split('.') if context_str else []
            
            candidates = []
            search_namespaces = ['value', 'function'] if ref['namespace'] == 'value' else [ref['namespace']]
            
            for search_ns in search_namespaces:
                for prefix_len in range(len(context_parts), -1, -1):
                    all_parts = context_parts[:prefix_len] + parsed['modules'] + [parsed['name']]
                    qualified = '.'.join(all_parts)
                    candidates.append({'qualified': qualified, 'namespace': search_ns, 'version': parsed['version']})
            
            found = False
            result_ns = ref['namespace']
            result_hash = None
            result_location = None
            
            for snap_idx in range(ref['start'], len(snapshots_list)):
                if not found:
                    for cand in candidates:
                        key = (cand['namespace'], cand['qualified'], cand['version'])
                        if key in snapshots_list[snap_idx]:
                            found = True
                            result_ns = cand['namespace']
                            result_hash = snapshots_list[snap_idx][key]
                            result_location = cand['qualified']
                            break
                else:
                    key = (result_ns, result_location, parsed['version'])
                    if key in snapshots_list[snap_idx]:
                        result_hash = snapshots_list[snap_idx][key]
            
            results.append(("located", result_ns, result_location, result_hash) if found else ("missing", ref['namespace'], None, None))
    
    return results