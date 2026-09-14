def validate_build(schemas, root, operations):
    flattened_counts = {}
    
    def get_flattened_count(schema_idx):
        if schema_idx in flattened_counts:
            return flattened_counts[schema_idx]
        schema = schemas[schema_idx]
        count = 0
        for term in schema:
            if term[0] == "field":
                count += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                count += get_flattened_count(t) * r
        flattened_counts[schema_idx] = count
        return count
    
    def get_field_at(schema_idx, pos):
        schema = schemas[schema_idx]
        current_pos = 0
        for term in schema:
            if term[0] == "field":
                if current_pos == pos:
                    return term[1], term[2]
                current_pos += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                t_count = get_flattened_count(t)
                total_count = t_count * r
                if current_pos + total_count > pos:
                    offset = pos - current_pos
                    rep_pos = offset % t_count
                    return get_field_at(t, rep_pos)
                current_pos += total_count
        return None, None
    
    def desc_equal(d1, d2):
        if isinstance(d1, str) and isinstance(d2, str):
            return d1 == d2
        if isinstance(d1, tuple) and isinstance(d2, tuple):
            if len(d1) != len(d2) or d1[0] != d2[0]:
                return False
            if d1[0] == "record":
                return d1[1] == d2[1]
            elif d1[0] == "array":
                return desc_equal(d1[1], d2[1]) and d1[2] == d2[2]
        return False
    
    stack = [("record", 0, get_flattened_count(root), root)]
    
    for op_idx, op in enumerate(operations, 1):
        if not stack:
            return op_idx
        
        container_type, pos, total, container_data = stack[-1]
        
        if op[0] == "put":
            _, name, p = op
            if container_type == "record":
                if pos >= total:
                    return op_idx
                field_name, field_desc = get_field_at(container_data, pos)
                if field_name is None or field_name != name or not desc_equal(field_desc, p):
                    return op_idx
                stack[-1] = (container_type, pos + 1, total, container_data)
            else:
                if pos >= total:
                    return op_idx
                if not desc_equal(container_data, p):
                    return op_idx
                stack[-1] = (container_type, pos + 1, total, container_data)
        
        elif op[0] == "open":
            _, name, d = op
            if container_type == "record":
                if pos >= total:
                    return op_idx
                field_name, field_desc = get_field_at(container_data, pos)
                if field_name is None or field_name != name or not desc_equal(field_desc, d):
                    return op_idx
                stack[-1] = (container_type, pos + 1, total, container_data)
                if isinstance(d, tuple):
                    if d[0] == "record":
                        stack.append(("record", 0, get_flattened_count(d[1]), d[1]))
                    elif d[0] == "array":
                        stack.append(("array", 0, d[2], d[1]))
            else:
                if name is not None:
                    return op_idx
                if pos >= total:
                    return op_idx
                if not desc_equal(container_data, d):
                    return op_idx
                stack[-1] = (container_type, pos + 1, total, container_data)
                if isinstance(d, tuple):
                    if d[0] == "record":
                        stack.append(("record", 0, get_flattened_count(d[1]), d[1]))
                    elif d[0] == "array":
                        stack.append(("array", 0, d[2], d[1]))
        
        elif op[0] == "default":
            _, k = op
            if container_type == "record":
                if pos + k > total:
                    return op_idx
                for i in range(pos, pos + k):
                    _, field_desc = get_field_at(container_data, i)
                    if not (isinstance(field_desc, str) and field_desc in ["int", "text"]):
                        return op_idx
                stack[-1] = (container_type, pos + k, total, container_data)
            else:
                if pos + k > total:
                    return op_idx
                if not (isinstance(container_data, str) and container_data in ["int", "text"]):
                    return op_idx
                stack[-1] = (container_type, pos + k, total, container_data)
        
        elif op[0] == "close":
            if container_type == "record":
                if pos != total:
                    return op_idx
            stack.pop()
    
    if len(stack) > 0:
        return len(operations) + 1
    return 0