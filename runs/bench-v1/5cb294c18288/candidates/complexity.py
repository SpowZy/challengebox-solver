def validate_build(schemas, root, operations):
    import math
    
    field_count_cache = {}
    all_primitive_cache = {}
    first_nonprim_cache = {}
    
    def get_field_count(schema_idx):
        if schema_idx in field_count_cache:
            return field_count_cache[schema_idx]
        schema = schemas[schema_idx]
        total = 0
        for term in schema:
            if term[0] == "field":
                total += 1
            elif term[0] == "repeat":
                base_count = get_field_count(term[1])
                total += base_count * term[2]
        field_count_cache[schema_idx] = total
        return total
    
    def all_primitive(schema_idx):
        if schema_idx in all_primitive_cache:
            return all_primitive_cache[schema_idx]
        schema = schemas[schema_idx]
        for term in schema:
            if term[0] == "field":
                if term[2] not in ("int", "text"):
                    all_primitive_cache[schema_idx] = False
                    return False
            elif term[0] == "repeat":
                if not all_primitive(term[1]):
                    all_primitive_cache[schema_idx] = False
                    return False
        all_primitive_cache[schema_idx] = True
        return True
    
    def find_first_nonprimitive(schema_idx):
        if schema_idx in first_nonprim_cache:
            return first_nonprim_cache[schema_idx]
        if all_primitive(schema_idx):
            first_nonprim_cache[schema_idx] = None
            return None
        schema = schemas[schema_idx]
        current_pos = 0
        for term in schema:
            if term[0] == "field":
                if term[2] not in ("int", "text"):
                    first_nonprim_cache[schema_idx] = current_pos
                    return current_pos
                current_pos += 1
            elif term[0] == "repeat":
                base_count = get_field_count(term[1])
                first = find_first_nonprimitive(term[1])
                if first is not None:
                    first_nonprim_cache[schema_idx] = current_pos + first
                    return current_pos + first
                current_pos += base_count * term[2]
        first_nonprim_cache[schema_idx] = None
        return None
    
    def descriptors_equal(d1, d2):
        if d1 == d2:
            return True
        if not isinstance(d1, tuple) or not isinstance(d2, tuple):
            return False
        if d1[0] != d2[0]:
            return False
        if d1[0] == "record":
            return d1[1] == d2[1]
        elif d1[0] == "array":
            return descriptors_equal(d1[1], d2[1]) and d1[2] == d2[2]
        return False
    
    def get_field_at(schema_idx, position):
        schema = schemas[schema_idx]
        current_pos = 0
        for term in schema:
            if term[0] == "field":
                if current_pos == position:
                    return (term[1], term[2])
                current_pos += 1
            elif term[0] == "repeat":
                base_count = get_field_count(term[1])
                chunk_size = base_count * term[2]
                if current_pos + chunk_size > position:
                    rel_pos = (position - current_pos) % base_count
                    return get_field_at(term[1], rel_pos)
                current_pos += chunk_size
        raise ValueError()
    
    def check_all_primitive_in_range(schema_idx, start_pos, count):
        schema = schemas[schema_idx]
        current_pos = 0
        checked = 0
        for term in schema:
            if checked == count:
                return True
            if term[0] == "field":
                if current_pos >= start_pos:
                    if term[2] not in ("int", "text"):
                        return False
                    checked += 1
                current_pos += 1
            elif term[0] == "repeat":
                base_count = get_field_count(term[1])
                chunk_size = base_count * term[2]
                chunk_end = current_pos + chunk_size
                if chunk_end <= start_pos:
                    current_pos = chunk_end
                    continue
                if all_primitive(term[1]):
                    overlap_start = max(current_pos, start_pos)
                    overlap_end = min(chunk_end, start_pos + count)
                    checked += overlap_end - overlap_start
                else:
                    first_nonprim = find_first_nonprimitive(term[1])
                    a = start_pos - current_pos - first_nonprim
                    b = start_pos + count - current_pos - first_nonprim
                    min_rep = max(0, -(-max(0, a) // base_count))
                    max_rep = min(term[2] - 1, (b - 1) // base_count) if b > 0 else -1
                    if min_rep <= max_rep:
                        return False
                    overlap_start = max(current_pos, start_pos)
                    overlap_end = min(chunk_end, start_pos + count)
                    checked += overlap_end - overlap_start
                current_pos = chunk_end
        return checked == count
    
    stack = [("record", (root, 0, get_field_count(root)))]
    
    for i, op in enumerate(operations, 1):
        if not stack:
            return i
        container_type, container_data = stack[-1]
        
        if op[0] == "put":
            name, p = op[1], op[2]
            if container_type == "record":
                schema_idx, position, total = container_data
                if position >= total:
                    return i
                try:
                    exp_name, exp_desc = get_field_at(schema_idx, position)
                except:
                    return i
                if exp_name != name or exp_desc != p:
                    return i
                stack[-1] = ("record", (schema_idx, position + 1, total))
            else:
                element_desc, current_length, capacity = container_data
                if name is not None or current_length >= capacity or element_desc != p:
                    return i
                stack[-1] = ("array", (element_desc, current_length + 1, capacity))
        
        elif op[0] == "open":
            name, d = op[1], op[2]
            if container_type == "record":
                schema_idx, position, total = container_data
                if position >= total:
                    return i
                try:
                    exp_name, exp_desc = get_field_at(schema_idx, position)
                except:
                    return i
                if exp_name != name or not descriptors_equal(exp_desc, d):
                    return i
                if d[0] == "record":
                    stack.append(("record", (d[1], 0, get_field_count(d[1]))))
                else:
                    stack.append(("array", (d[1], 0, d[2])))
                stack[-2] = ("record", (schema_idx, position + 1, total))
            else:
                element_desc, current_length, capacity = container_data
                if name is not None or current_length >= capacity or not descriptors_equal(element_desc, d):
                    return i
                if d[0] == "record":
                    stack.append(("record", (d[1], 0, get_field_count(d[1]))))
                else:
                    stack.append(("array", (d[1], 0, d[2])))
                stack[-2] = ("array", (element_desc, current_length + 1, capacity))
        
        elif op[0] == "default":
            k = op[1]
            if container_type == "record":
                schema_idx, position, total = container_data
                if position + k > total:
                    return i
                if not check_all_primitive_in_range(schema_idx, position, k):
                    return i
                stack[-1] = ("record", (schema_idx, position + k, total))
            else:
                element_desc, current_length, capacity = container_data
                if element_desc not in ("int", "text") or current_length + k > capacity:
                    return i
                stack[-1] = ("array", (element_desc, current_length + k, capacity))
        
        elif op[0] == "close":
            if container_type == "record":
                schema_idx, position, total = container_data
                if position != total:
                    return i
            stack.pop()
            if not stack and i < len(operations):
                return i + 1
    
    return len(operations) + 1 if stack else 0