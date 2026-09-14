def validate_build(schemas, root, operations):
    size_cache = {}
    all_prim_cache = {}
    
    def is_primitive(descriptor):
        return isinstance(descriptor, str) and descriptor in ["int", "text"]
    
    def get_flattened_size(schema_idx):
        if schema_idx in size_cache:
            return size_cache[schema_idx]
        
        schema = schemas[schema_idx]
        size = 0
        
        for term in schema:
            if term[0] == "field":
                size += 1
            elif term[0] == "repeat":
                _, ref_schema, count = term
                ref_size = get_flattened_size(ref_schema)
                size += ref_size * count
        
        size_cache[schema_idx] = size
        return size
    
    def all_primitives_in_schema(schema_idx):
        if schema_idx in all_prim_cache:
            return all_prim_cache[schema_idx]
        
        schema = schemas[schema_idx]
        for term in schema:
            if term[0] == "field":
                _, _, descriptor = term
                if not is_primitive(descriptor):
                    all_prim_cache[schema_idx] = False
                    return False
            elif term[0] == "repeat":
                _, ref_schema, _ = term
                if not all_primitives_in_schema(ref_schema):
                    all_prim_cache[schema_idx] = False
                    return False
        
        all_prim_cache[schema_idx] = True
        return True
    
    def get_field_at_index(schema_idx, index):
        schema = schemas[schema_idx]
        current = 0
        
        for term in schema:
            if term[0] == "field":
                if current == index:
                    _, name, descriptor = term
                    return (name, descriptor)
                current += 1
            elif term[0] == "repeat":
                _, ref_schema, count = term
                ref_size = get_flattened_size(ref_schema)
                total = ref_size * count
                
                if current + total > index:
                    offset = index - current
                    ref_index = offset % ref_size
                    return get_field_at_index(ref_schema, ref_index)
                
                current += total
        return None
    
    def all_primitives_in_range(schema_idx, start, end):
        if end <= start:
            return True
        
        schema = schemas[schema_idx]
        current = 0
        
        for term in schema:
            if term[0] == "field":
                if current >= end:
                    return True
                if current >= start:
                    _, _, descriptor = term
                    if not is_primitive(descriptor):
                        return False
                current += 1
            elif term[0] == "repeat":
                _, ref_schema, count = term
                ref_size = get_flattened_size(ref_schema)
                term_end = current + ref_size * count
                
                if term_end <= start:
                    current = term_end
                    continue
                if current >= end:
                    return True
                
                if all_primitives_in_schema(ref_schema):
                    current = term_end
                    continue
                
                relative_start = max(0, start - current)
                relative_end = min(ref_size * count, end - current)
                
                start_idx = relative_start % ref_size if ref_size > 0 else 0
                end_idx = start_idx + min(ref_size - start_idx, relative_end - relative_start)
                
                if not all_primitives_in_range(ref_schema, start_idx, min(end_idx, ref_size)):
                    return False
                
                if relative_end > ref_size - start_idx:
                    remaining = relative_end - (ref_size - start_idx)
                    last_idx = remaining % ref_size
                    if last_idx > 0 and not all_primitives_in_range(ref_schema, 0, last_idx):
                        return False
                
                current = term_end
        
        return True
    
    stack = [("record", root, 0)]
    
    for op_idx, operation in enumerate(operations, 1):
        if not stack:
            return op_idx
        
        container_type, info, pos = stack[-1]
        
        if operation[0] == "put":
            _, name, prim_type = operation
            
            if container_type == "record":
                schema_idx = info
                total_fields = get_flattened_size(schema_idx)
                
                if pos >= total_fields:
                    return op_idx
                
                field_name, field_desc = get_field_at_index(schema_idx, pos)
                if field_name != name or field_desc != prim_type:
                    return op_idx
                
                stack[-1] = ("record", schema_idx, pos + 1)
            else:
                elem_desc, capacity = info
                
                if pos >= capacity or elem_desc != prim_type or name is not None:
                    return op_idx
                
                stack[-1] = ("array", info, pos + 1)
        
        elif operation[0] == "open":
            _, name, descriptor = operation
            
            if container_type == "record":
                schema_idx = info
                total_fields = get_flattened_size(schema_idx)
                
                if pos >= total_fields:
                    return op_idx
                
                field_name, field_desc = get_field_at_index(schema_idx, pos)
                if field_name != name or field_desc != descriptor:
                    return op_idx
                
                stack[-1] = ("record", schema_idx, pos + 1)
                
                if isinstance(descriptor, tuple):
                    if descriptor[0] == "record":
                        stack.append(("record", descriptor[1], 0))
                    elif descriptor[0] == "array":
                        stack.append(("array", (descriptor[1], descriptor[2]), 0))
            else:
                elem_desc, capacity = info
                
                if pos >= capacity or elem_desc != descriptor or name is not None:
                    return op_idx
                
                stack[-1] = ("array", info, pos + 1)
                
                if isinstance(descriptor, tuple):
                    if descriptor[0] == "record":
                        stack.append(("record", descriptor[1], 0))
                    elif descriptor[0] == "array":
                        stack.append(("array", (descriptor[1], descriptor[2]), 0))
        
        elif operation[0] == "default":
            _, k = operation
            
            if container_type == "record":
                schema_idx = info
                total_fields = get_flattened_size(schema_idx)
                
                if pos + k > total_fields or not all_primitives_in_range(schema_idx, pos, pos + k):
                    return op_idx
                
                stack[-1] = ("record", schema_idx, pos + k)
            else:
                elem_desc, capacity = info
                
                if not is_primitive(elem_desc) or pos + k > capacity:
                    return op_idx
                
                stack[-1] = ("array", info, pos + k)
        
        elif operation[0] == "close":
            if container_type == "record":
                schema_idx = info
                total_fields = get_flattened_size(schema_idx)
                
                if pos != total_fields:
                    return op_idx
                
                stack.pop()
            else:
                stack.pop()
    
    if len(stack) > 1:
        return len(operations) + 1
    
    if stack and stack[0][0] == "record":
        schema_idx = stack[0][1]
        pos = stack[0][2]
        total_fields = get_flattened_size(schema_idx)
        if pos != total_fields:
            return len(operations) + 1
    
    return 0