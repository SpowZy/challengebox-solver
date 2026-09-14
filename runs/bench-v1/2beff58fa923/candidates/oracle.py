import re

def refresh_references(initial, snapshots, references):
    indices = []
    current_index = {}
    
    for entry in initial:
        key = (entry["namespace"], entry["name"], entry["version"])
        current_index[key] = entry["hash"]
    indices.append(dict(current_index))
    
    for snapshot in snapshots:
        for update in snapshot:
            key = (update["namespace"], update["name"], update["version"])
            if update["hash"] is None:
                current_index.pop(key, None)
            else:
                current_index[key] = update["hash"]
        indices.append(dict(current_index))
    
    results = []
    
    for ref in references:
        if not validate_context(ref.get("context", "")):
            results.append(("invalid", ref["namespace"], ref["location"], ref["hash"]))
            continue
        
        parsed = parse_reference_text(ref.get("text", ""), ref.get("namespace"))
        if parsed is None:
            results.append(("invalid", ref["namespace"], ref["location"], ref["hash"]))
            continue
        
        parsed_name, parsed_version = parsed
        
        if ref.get("location") is not None:
            key = (ref["namespace"], parsed_name, parsed_version)
            hash_value = ref["hash"]
            
            for snap_idx in range(ref["start"], len(indices)):
                if key in indices[snap_idx]:
                    hash_value = indices[snap_idx][key]
            
            results.append(("located", ref["namespace"], ref["location"], hash_value))
        else:
            candidates = generate_candidates(ref.get("context", ""), parsed_name, parsed_version)
            
            matched_namespace = None
            matched_name = None
            matched_version = parsed_version
            matched_hash = None
            
            for snap_idx in range(ref["start"], len(indices)):
                index = indices[snap_idx]
                
                if matched_namespace is not None:
                    key = (matched_namespace, matched_name, matched_version)
                    if key in index:
                        matched_hash = index[key]
                else:
                    if ref["namespace"] == "type":
                        for cand_name, cand_version in candidates:
                            key = ("type", cand_name, cand_version)
                            if key in index:
                                matched_namespace = "type"
                                matched_name = cand_name
                                matched_version = cand_version
                                matched_hash = index[key]
                                break
                    elif ref["namespace"] == "function":
                        for cand_name, cand_version in candidates:
                            key = ("function", cand_name, cand_version)
                            if key in index:
                                matched_namespace = "function"
                                matched_name = cand_name
                                matched_version = cand_version
                                matched_hash = index[key]
                                break
                    elif ref["namespace"] == "value":
                        for cand_name, cand_version in candidates:
                            key = ("value", cand_name, cand_version)
                            if key in index:
                                matched_namespace = "value"
                                matched_name = cand_name
                                matched_version = cand_version
                                matched_hash = index[key]
                                break
                        
                        if matched_namespace is None:
                            for cand_name, cand_version in candidates:
                                key = ("function", cand_name, cand_version)
                                if key in index:
                                    matched_namespace = "function"
                                    matched_name = cand_name
                                    matched_version = cand_version
                                    matched_hash = index[key]
                                    break
            
            if matched_namespace is not None:
                if matched_version is None:
                    location = f"{matched_namespace}:{matched_name}"
                else:
                    location = f"{matched_namespace}:{matched_name}@{matched_version}"
                results.append(("located", matched_namespace, location, matched_hash))
            else:
                results.append(("missing", ref["namespace"], None, None))
    
    return results


def validate_context(context):
    if not context:
        return True
    parts = context.split('.')
    if not all(parts):
        return False
    return all(re.match(r'^[a-z_][a-z0-9_]*$', part) for part in parts)


def parse_reference_text(text, namespace):
    if not text:
        return None
    
    parts = text.split('.')
    if not parts or not all(parts):
        return None
    
    for part in parts:
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', part):
            return None
    
    terminal = parts[-1]
    version = None
    
    if namespace in ["function", "value"]:
        match = re.match(r'^([a-z_][a-z0-9_]*)@(0|[1-9]\d*)$', terminal)
        if match:
            terminal = match.group(1)
            version = int(match.group(2))
            parts[-1] = terminal
    elif namespace == "type":
        if '@' in terminal:
            return None
    else:
        return None
    
    if namespace == "type":
        if not terminal or not terminal[0].isupper():
            return None
    elif namespace in ["function", "value"]:
        if not terminal or not terminal[0].islower():
            return None
    
    for part in parts[:-1]:
        if not part or not part[0].islower():
            return None
    
    name = '.'.join(parts)
    return name, version


def generate_candidates(context, name, version):
    candidates = []
    context_parts = context.split('.') if context else []
    name_parts = name.split('.')
    
    for i in range(len(context_parts), -1, -1):
        prefix_parts = context_parts[:i]
        full_parts = prefix_parts + name_parts
        full_name = '.'.join(full_parts)
        candidates.append((full_name, version))
    
    return candidates