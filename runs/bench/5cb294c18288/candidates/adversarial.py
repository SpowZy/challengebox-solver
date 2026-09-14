def validate_build(schemas, root, operations):
    def get_schema_size(s, cache):
        if s in cache:
            return cache[s]
        total = 0
        for term in schemas[s]:
            if term[0] == "field":
                total += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                sub_size = get_schema_size(t, cache)
                total += sub_size * r
        cache[s] = total
        return total
    
    def get_field_at_position(s, pos, cache):
        current_pos = 0
        for term in schemas[s]:
            if term[0] == "field":
                if current_pos == pos:
                    return term[1], term[2]
                current_pos += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                sub_size = get_schema_size(t, cache)
                total_size = sub_size * r
                if current_pos + total_size > pos:
                    offset = pos - current_pos
                    sub_pos = offset % sub_size
                    return get_field_at_position(t, sub_pos, cache)
                current_pos += total_size
        return None
    
    def descriptors_equal(d1, d2):
        if type(d1) != type(d2):
            return False
        if isinstance(d1, str):
            return d1 == d2
        if isinstance(d1, tuple):
            if len(d1) >= 2 and len(d2) >= 2:
                if d1[0] == d2[0] == "record":
                    return d1[1] == d2[1]
                if d1[0] == d2[0] == "array" and len(d1) >= 3 and len(d2) >= 3:
                    return descriptors_equal(d1[1], d2[1]) and d1[2] == d2[2]
        return False
    
    cache = {}
    stack = [("record", root, 0)]
    
    for op_idx, op in enumerate(operations, 1):
        if not stack:
            return op_idx
        
        top = stack[-1]
        
        if top[0] == "record":
            _, s, position = top
            total_size = get_schema_size(s, cache)
            
            if op[0] == "put":
                name, p = op[1], op[2]
                if position >= total_size:
                    return op_idx
                field_name, field_desc = get_field_at_position(s, position, cache)
                if field_name != name or not descriptors_equal(field_desc, p):
                    return op_idx
                stack[-1] = ("record", s, position + 1)
            
            elif op[0] == "open":
                name, d = op[1], op[2]
                if position >= total_size:
                    return op_idx
                field_name, field_desc = get_field_at_position(s, position, cache)
                if field_name != name or not descriptors_equal(field_desc, d):
                    return op_idx
                if isinstance(d, tuple) and len(d) >= 2:
                    if d[0] == "record":
                        stack.append(("record", d[1], 0))
                    elif d[0] == "array" and len(d) >= 3:
                        stack.append(("array", d[1], 0, d[2]))
                    else:
                        return op_idx
                else:
                    return op_idx
                stack[-2] = ("record", s, position + 1)
            
            elif op[0] == "default":
                k = op[1]
                if total_size - position < k:
                    return op_idx
                for i in range(k):
                    _, field_desc = get_field_at_position(s, position + i, cache)
                    if field_desc not in ("int", "text"):
                        return op_idx
                stack[-1] = ("record", s, position + k)
            
            elif op[0] == "close":
                if position != total_size:
                    return op_idx
                stack.pop()
        
        elif top[0] == "array":
            _, element_desc, position, capacity = top
            
            if op[0] == "put":
                name, p = op[1], op[2]
                if position >= capacity or name is not None or not descriptors_equal(element_desc, p):
                    return op_idx
                stack[-1] = ("array", element_desc, position + 1, capacity)
            
            elif op[0] == "open":
                name, d = op[1], op[2]
                if position >= capacity or name is not None or not descriptors_equal(element_desc, d):
                    return op_idx
                if isinstance(d, tuple) and len(d) >= 2:
                    if d[0] == "record":
                        stack.append(("record", d[1], 0))
                    elif d[0] == "array" and len(d) >= 3:
                        stack.append(("array", d[1], 0, d[2]))
                    else:
                        return op_idx
                else:
                    return op_idx
                stack[-2] = ("array", element_desc, position + 1, capacity)
            
            elif op[0] == "default":
                k = op[1]
                if element_desc not in ("int", "text") or position + k > capacity:
                    return op_idx
                stack[-1] = ("array", element_desc, position + k, capacity)
            
            elif op[0] == "close":
                stack.pop()
    
    return 0 if len(stack) == 0 else len(operations) + 1