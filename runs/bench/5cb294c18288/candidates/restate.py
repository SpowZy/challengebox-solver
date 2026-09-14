def validate_build(schemas, root, operations):
    memo_field_count = {}
    
    def get_field_count(schema_idx):
        if schema_idx in memo_field_count:
            return memo_field_count[schema_idx]
        schema = schemas[schema_idx]
        count = 0
        for term in schema:
            if term[0] == "field":
                count += 1
            elif term[0] == "repeat":
                _, t, r = term
                base_count = get_field_count(t)
                count += base_count * r
        memo_field_count[schema_idx] = count
        return count
    
    def get_field_at(schema_idx, pos):
        schema = schemas[schema_idx]
        current_pos = 0
        for term in schema:
            if term[0] == "field":
                if current_pos == pos:
                    _, name, descriptor = term
                    return name, descriptor
                current_pos += 1
            elif term[0] == "repeat":
                _, t, r = term
                base_count = get_field_count(t)
                total = base_count * r
                if current_pos + total > pos:
                    offset = pos - current_pos
                    field_in_repeat = offset % base_count
                    return get_field_at(t, field_in_repeat)
                current_pos += total
    
    memo_all_primitive = {}
    
    def all_fields_primitive(schema_idx):
        if schema_idx in memo_all_primitive:
            return memo_all_primitive[schema_idx]
        schema = schemas[schema_idx]
        for term in schema:
            if term[0] == "field":
                _, name, descriptor = term
                if descriptor not in ["int", "text"]:
                    memo_all_primitive[schema_idx] = False
                    return False
            elif term[0] == "repeat":
                _, t, r = term
                if not all_fields_primitive(t):
                    memo_all_primitive[schema_idx] = False
                    return False
        memo_all_primitive[schema_idx] = True
        return True
    
    def check_all_primitive(schema_idx, start_pos, check_count):
        schema = schemas[schema_idx]
        current_pos = 0
        remaining = check_count
        
        for term in schema:
            if remaining == 0:
                break
            
            if term[0] == "field":
                if current_pos >= start_pos:
                    _, name, descriptor = term
                    if descriptor not in ["int", "text"]:
                        return False
                    remaining -= 1
                current_pos += 1
            
            elif term[0] == "repeat":
                _, t, r = term
                base_count = get_field_count(t)
                total = base_count * r
                
                if current_pos + total > start_pos and remaining > 0:
                    if all_fields_primitive(t):
                        repeat_start = max(0, start_pos - current_pos)
                        skip_count = min(total - repeat_start, remaining)
                        remaining -= skip_count
                    else:
                        repeat_start = max(0, start_pos - current_pos)
                        repeat_count = min(total - repeat_start, remaining)
                        
                        for i in range(min(repeat_count, base_count)):
                            field_idx = (repeat_start + i) % base_count
                            _, desc = get_field_at(t, field_idx)
                            if desc not in ["int", "text"]:
                                return False
                        
                        remaining -= repeat_count
                
                current_pos += total
        
        return remaining == 0
    
    root_field_count = get_field_count(root)
    container_stack = [("record", root, root_field_count, 0)]
    
    for op_idx, operation in enumerate(operations, 1):
        if not container_stack:
            return op_idx
        
        op_type = operation[0]
        
        if op_type == "put":
            _, name, p = operation
            current = container_stack[-1]
            
            if current[0] == "record":
                _, schema_idx, field_count, pos = current
                if pos >= field_count:
                    return op_idx
                field_name, field_desc = get_field_at(schema_idx, pos)
                if name != field_name or field_desc != p:
                    return op_idx
                container_stack[-1] = ("record", schema_idx, field_count, pos + 1)
            
            elif current[0] == "array":
                _, element_desc, capacity, array_count = current
                if name is not None:
                    return op_idx
                if array_count >= capacity:
                    return op_idx
                if element_desc != p:
                    return op_idx
                container_stack[-1] = ("array", element_desc, capacity, array_count + 1)
        
        elif op_type == "open":
            _, name, descriptor = operation
            current = container_stack[-1]
            
            if current[0] == "record":
                _, schema_idx, field_count, pos = current
                if pos >= field_count:
                    return op_idx
                field_name, field_desc = get_field_at(schema_idx, pos)
                if name != field_name or field_desc != descriptor:
                    return op_idx
                
                container_stack[-1] = ("record", schema_idx, field_count, pos + 1)
                
                if descriptor[0] == "record":
                    new_field_count = get_field_count(descriptor[1])
                    container_stack.append(("record", descriptor[1], new_field_count, 0))
                elif descriptor[0] == "array":
                    container_stack.append(("array", descriptor[1], descriptor[2], 0))
                else:
                    return op_idx
            
            elif current[0] == "array":
                _, element_desc, capacity, array_count = current
                if name is not None:
                    return op_idx
                if array_count >= capacity:
                    return op_idx
                if element_desc != descriptor:
                    return op_idx
                
                container_stack[-1] = ("array", element_desc, capacity, array_count + 1)
                
                if descriptor[0] == "record":
                    new_field_count = get_field_count(descriptor[1])
                    container_stack.append(("record", descriptor[1], new_field_count, 0))
                elif descriptor[0] == "array":
                    container_stack.append(("array", descriptor[1], descriptor[2], 0))
                else:
                    return op_idx
        
        elif op_type == "default":
            _, k = operation
            current = container_stack[-1]
            
            if current[0] == "record":
                _, schema_idx, field_count, pos = current
                remaining = field_count - pos
                if k > remaining:
                    return op_idx
                if not check_all_primitive(schema_idx, pos, k):
                    return op_idx
                container_stack[-1] = ("record", schema_idx, field_count, pos + k)
            
            elif current[0] == "array":
                _, element_desc, capacity, array_count = current
                remaining = capacity - array_count
                if k > remaining:
                    return op_idx
                if element_desc not in ["int", "text"]:
                    return op_idx
                container_stack[-1] = ("array", element_desc, capacity, array_count + k)
        
        elif op_type == "close":
            current = container_stack[-1]
            
            if current[0] == "record":
                _, schema_idx, field_count, pos = current
                if pos != field_count:
                    return op_idx
                container_stack.pop()
            
            elif current[0] == "array":
                container_stack.pop()
    
    if len(container_stack) == 0:
        return 0
    else:
        return len(operations) + 1