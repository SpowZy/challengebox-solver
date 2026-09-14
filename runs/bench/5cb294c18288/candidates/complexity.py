def validate_build(schemas, root, operations):
    MAX_SIZE = 10**18
    field_count_cache = {}
    complex_cache = {}
    
    def has_complex_fields(schema_idx):
        if schema_idx in complex_cache:
            return complex_cache[schema_idx]
        result = False
        for term in schemas[schema_idx]:
            if term[0] == "field":
                if term[2] not in ["int", "text"]:
                    result = True
                    break
            elif term[0] == "repeat":
                if has_complex_fields(term[1]):
                    result = True
                    break
        complex_cache[schema_idx] = result
        return result
    
    def get_flattened_field_count(schema_idx):
        if schema_idx in field_count_cache:
            return field_count_cache[schema_idx]
        count = 0
        for term in schemas[schema_idx]:
            if term[0] == "field":
                count += 1
            elif term[0] == "repeat":
                ref_idx, reps = term[1], term[2]
                ref_count = get_flattened_field_count(ref_idx)
                if ref_count > 0 and reps > MAX_SIZE // ref_count:
                    count = MAX_SIZE + 1
                    break
                count += ref_count * reps
                if count > MAX_SIZE:
                    count = MAX_SIZE + 1
                    break
        field_count_cache[schema_idx] = count
        return count
    
    def get_flattened_field(schema_idx, pos):
        current_pos = 0
        for term in schemas[schema_idx]:
            if term[0] == "field":
                if current_pos == pos:
                    return (term[1], term[2])
                current_pos += 1
            elif term[0] == "repeat":
                ref_idx, reps = term[1], term[2]
                ref_count = get_flattened_field_count(ref_idx)
                if ref_count > 0 and reps > MAX_SIZE // ref_count:
                    total_reps_count = MAX_SIZE + 1
                else:
                    total_reps_count = ref_count * reps
                if current_pos + total_reps_count > pos:
                    offset = pos - current_pos
                    ref_pos = offset % ref_count if ref_count > 0 else 0
                    return get_flattened_field(ref_idx, ref_pos)
                current_pos += total_reps_count
                if current_pos > MAX_SIZE:
                    current_pos = MAX_SIZE + 1
        return None
    
    def get_primitive_run_length(schema_idx, start_pos):
        current_pos = 0
        length = 0
        for term in schemas[schema_idx]:
            if term[0] == "field":
                if current_pos >= start_pos:
                    if term[2] not in ["int", "text"]:
                        break
                    length += 1
                current_pos += 1
            elif term[0] == "repeat":
                ref_idx, reps = term[1], term[2]
                if has_complex_fields(ref_idx):
                    if current_pos >= start_pos:
                        break
                    ref_count = get_flattened_field_count(ref_idx)
                    if ref_count > 0 and reps > MAX_SIZE // ref_count:
                        current_pos = MAX_SIZE + 1
                    else:
                        current_pos += ref_count * reps
                else:
                    ref_count = get_flattened_field_count(ref_idx)
                    if ref_count > 0 and reps > MAX_SIZE // ref_count:
                        total_count = MAX_SIZE + 1
                    else:
                        total_count = ref_count * reps
                    if current_pos + total_count <= start_pos:
                        current_pos += total_count
                    elif current_pos >= start_pos:
                        length += total_count
                        current_pos += total_count
                    else:
                        length += current_pos + total_count - start_pos
                        current_pos += total_count
        return length
    
    def descriptors_equal(d1, d2):
        if isinstance(d1, str):
            return d1 == d2
        if isinstance(d1, tuple) and isinstance(d2, tuple):
            if d1[0] != d2[0]:
                return False
            if d1[0] == "record":
                return d1[1] == d2[1]
            elif d1[0] == "array":
                return descriptors_equal(d1[1], d2[1]) and d1[2] == d2[2]
        return False
    
    stack = [(root, 0, None, "record")]
    
    for op_idx, op in enumerate(operations):
        if not stack:
            return op_idx + 1
        info, pos, capacity, cont_type = stack[-1]
        
        if op[0] == "put":
            name, prim = op[1], op[2]
            if cont_type == "record":
                result = get_flattened_field(info, pos)
                if result is None or result[0] != name or result[1] != prim:
                    return op_idx + 1
                stack[-1] = (info, pos + 1, capacity, cont_type)
            else:
                if name is not None or info != prim or pos >= capacity:
                    return op_idx + 1
                stack[-1] = (info, pos + 1, capacity, cont_type)
        
        elif op[0] == "open":
            name, desc = op[1], op[2]
            if cont_type == "record":
                result = get_flattened_field(info, pos)
                if result is None or result[0] != name or not descriptors_equal(result[1], desc):
                    return op_idx + 1
                if desc[0] == "record":
                    new_info, new_capacity, new_type = desc[1], None, "record"
                else:
                    new_info, new_capacity, new_type = desc[1], desc[2], "array"
                stack[-1] = (info, pos + 1, capacity, cont_type)
                stack.append((new_info, 0, new_capacity, new_type))
            else:
                if name is not None or not descriptors_equal(info, desc) or pos >= capacity:
                    return op_idx + 1
                if desc[0] == "record":
                    new_info, new_capacity, new_type = desc[1], None, "record"
                else:
                    new_info, new_capacity, new_type = desc[1], desc[2], "array"
                stack[-1] = (info, pos + 1, capacity, cont_type)
                stack.append((new_info, 0, new_capacity, new_type))
        
        elif op[0] == "default":
            k = op[1]
            if cont_type == "record":
                max_length = get_primitive_run_length(info, pos)
                if max_length < k:
                    return op_idx + 1
                stack[-1] = (info, pos + k, capacity, cont_type)
            else:
                if info not in ["int", "text"] or pos + k > capacity:
                    return op_idx + 1
                stack[-1] = (info, pos + k, capacity, cont_type)
        
        elif op[0] == "close":
            if cont_type == "record":
                total_fields = get_flattened_field_count(info)
                if pos != total_fields:
                    return op_idx + 1
            stack.pop()
    
    return 0 if not stack else len(operations) + 1