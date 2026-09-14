def refresh_references(initial, snapshots, references):
    results = []
    for ref in references:
        result = process_reference(ref, initial, snapshots)
        results.append(result)
    return results


def process_reference(ref, initial, snapshots):
    namespace = ref['namespace']
    text = ref['text']
    context = ref['context']
    location = ref['location']
    hash_val = ref['hash']
    start = ref['start']
    
    # Parse text into name and version
    parsed_name, parsed_version = parse_text(text, namespace)
    if parsed_name is None:
        return ("invalid", namespace, location, hash_val)
    
    # Validate location and hash consistency
    if location is not None:
        if hash_val is None:
            return ("invalid", namespace, location, hash_val)
    else:
        if hash_val is not None:
            return ("invalid", namespace, location, hash_val)
    
    # Build initial state
    current_state = build_state(initial)
    current_hash = hash_val
    current_namespace = namespace
    current_location = location
    
    # Process snapshot 0 (initial state)
    if start <= 0:
        if location is not None:
            key = (namespace, location, parsed_version)
            if key in current_state:
                current_hash = current_state[key]
        else:
            found_loc, found_hash, found_ns = find_candidate(
                namespace, context, parsed_name, parsed_version, current_state
            )
            if found_loc is not None:
                current_location = found_loc
                current_hash = found_hash
                current_namespace = found_ns
    
    # Process subsequent snapshots
    for batch_idx in range(len(snapshots)):
        for update in snapshots[batch_idx]:
            apply_update(current_state, update)
        
        snapshot_idx = batch_idx + 1
        if start <= snapshot_idx:
            if current_location is not None:
                key = (current_namespace, current_location, parsed_version)
                if key in current_state:
                    current_hash = current_state[key]
            else:
                found_loc, found_hash, found_ns = find_candidate(
                    namespace, context, parsed_name, parsed_version, current_state
                )
                if found_loc is not None:
                    current_location = found_loc
                    current_hash = found_hash
                    current_namespace = found_ns
    
    if current_location is not None:
        return ("located", current_namespace, current_location, current_hash)
    else:
        return ("missing", namespace, None, None)


def parse_text(text, namespace):
    if not text:
        return None, None
    
    parts = text.split('.')
    if not parts[-1]:
        return None, None
    
    # All parts except the last must be valid module identifiers
    for i in range(len(parts) - 1):
        if not is_valid_module_id(parts[i]):
            return None, None
    
    terminal = parts[-1]
    
    if namespace == "type":
        if not is_valid_type_terminal(terminal):
            return None, None
        return terminal, None
    else:  # function or value
        return parse_func_val_terminal(terminal)


def is_ascii_alnum_underscore(c):
    return ('a' <= c <= 'z') or ('A' <= c <= 'Z') or ('0' <= c <= '9') or c == '_'


def is_valid_module_id(s):
    if not s or s[0] not in 'abcdefghijklmnopqrstuvwxyz':
        return False
    for c in s:
        if not is_ascii_alnum_underscore(c):
            return False
    return True


def is_valid_type_terminal(s):
    if not s or s[0] not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        return False
    for c in s:
        if not is_ascii_alnum_underscore(c):
            return False
    return True


def is_valid_func_val_terminal(s):
    if not s or s[0] not in 'abcdefghijklmnopqrstuvwxyz':
        return False
    
    if '@' in s:
        idx = s.rfind('@')
        name_part = s[:idx]
        version_part = s[idx+1:]
        
        if not name_part or not version_part:
            return False
        
        for c in name_part:
            if not is_ascii_alnum_underscore(c):
                return False
        
        if not version_part.isdigit():
            return False
        if version_part[0] == '0' and len(version_part) > 1:
            return False
        return True
    else:
        for c in s:
            if not is_ascii_alnum_underscore(c):
                return False
        return True


def parse_func_val_terminal(s):
    if not is_valid_func_val_terminal(s):
        return None, None
    
    if '@' in s:
        idx = s.rfind('@')
        name_part = s[:idx]
        version_str = s[idx+1:]
        return name_part, int(version_str)
    else:
        return s, None


def find_candidate(namespace, context, parsed_name, parsed_version, state):
    context_parts = context.split('.') if context else []
    candidates = []
    
    for i in range(len(context_parts), -1, -1):
        if i > 0:
            prefix = '.'.join(context_parts[:i])
            candidate = prefix + '.' + parsed_name
        else:
            candidate = parsed_name
        candidates.append(candidate)
    
    if namespace == "type":
        for candidate in candidates:
            key = ("type", candidate, None)
            if key in state:
                return candidate, state[key], "type"
    elif namespace == "function":
        for candidate in candidates:
            key = ("function", candidate, parsed_version)
            if key in state:
                return candidate, state[key], "function"
    else:  # "value"
        for candidate in candidates:
            key = ("value", candidate, parsed_version)
            if key in state:
                return candidate, state[key], "value"
        for candidate in candidates:
            key = ("function", candidate, parsed_version)
            if key in state:
                return candidate, state[key], "function"
    
    return None, None, namespace


def build_state(initial):
    state = {}
    for entry in initial:
        key = (entry['namespace'], entry['name'], entry['version'])
        state[key] = entry['hash']
    return state


def apply_update(state, update):
    key = (update['namespace'], update['name'], update['version'])
    if update['hash'] is None:
        state.pop(key, None)
    else:
        state[key] = update['hash']