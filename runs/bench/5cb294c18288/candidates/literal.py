def validate_build(schemas, root, operations):
    memo_size = {}
    
    def get_schema_size(schema_idx):
        if schema_idx in memo_size:
            return memo_size[schema_idx]
        
        size = 0
        schema = schemas[schema_idx]
        
        for term in schema:
            if term[0] == "field":
                size += 1
            elif term[0] == "repeat":
                template_idx, repetitions = term[1], term[2]
                template_size = get_schema_size(template_idx)
                size += template_size * repetitions
        
        memo_size[schema_idx] = size
        return size
    
    def get_field_at_position(schema_idx, position):
        current_pos = 0
        schema = schemas[schema_idx]
        
        for term in schema:
            if term[0] == "field":
                if current_pos == position:
                    return (term[1], term[2])
                current_pos += 1
            elif term[0] == "repeat":
                template_idx, repetitions = term[1], term[2]
                template_size = get_schema_size(template_idx)
                repeat_size = template_size * repetitions
                
                if position < current_pos + repeat_size:
                    offset = position - current_pos
                    template_position = offset % template_size
                    return get_field_at_position(template_idx, template_position)
                
                current_pos += repeat_size
        
        raise IndexError()
    
    def all_fields_primitive(schema_idx, start_pos, count):
        check_limit = min(count, 100000)
        for i in range(check_limit):
            try:
                _, desc = get_field_at_position(schema_idx, start_pos + i)
                if desc not in ("int", "text"):
                    return False
            except IndexError:
                return False
        return True
    
    stack = [("record", root, 0, None)]
    
    for op_idx, op in enumerate(operations):
        if not stack:
            return op_idx + 1
        
        container_type, ref, pos, cap = stack[-1]
        
        try:
            if op[0] == "put":
                name, prim_type = op[1], op[2]
                
                if container_type == "record":
                    field_name, field_desc = get_field_at_position(ref, pos)
                    if name != field_name or field_desc != prim_type:
                        return op_idx + 1
                    stack[-1] = ("record", ref, pos + 1, None)
                else:
                    if name is not None or cap is None or pos >= cap or ref != prim_type:
                        return op_idx + 1
                    stack[-1] = ("array", ref, pos + 1, cap)
            
            elif op[0] == "open":
                name, descriptor = op[1], op[2]
                
                if container_type == "record":
                    field_name, field_desc = get_field_at_position(ref, pos)
                    if name != field_name or field_desc != descriptor:
                        return op_idx + 1
                    stack[-1] = ("record", ref, pos + 1, None)
                else:
                    if name is not None or cap is None or pos >= cap or ref != descriptor:
                        return op_idx + 1
                    stack[-1] = ("array", ref, pos + 1, cap)
                
                if isinstance(descriptor, tuple):
                    if descriptor[0] == "record":
                        stack.append(("record", descriptor[1], 0, None))
                    elif descriptor[0] == "array":
                        stack.append(("array", descriptor[1], 0, descriptor[2]))
                    else:
                        return op_idx + 1
                else:
                    return op_idx + 1
            
            elif op[0] == "default":
                k = op[1]
                
                if container_type == "record":
                    schema_size = get_schema_size(ref)
                    if pos + k > schema_size:
                        return op_idx + 1
                    if not all_fields_primitive(ref, pos, k):
                        return op_idx + 1
                    stack[-1] = ("record", ref, pos + k, None)
                else:
                    if ref not in ("int", "text") or cap is None or pos + k > cap:
                        return op_idx + 1
                    stack[-1] = ("array", ref, pos + k, cap)
            
            elif op[0] == "close":
                if container_type == "record":
                    schema_size = get_schema_size(ref)
                    if pos != schema_size:
                        return op_idx + 1
                stack.pop()
        
        except (IndexError, KeyError, TypeError):
            return op_idx + 1
    
    return 0 if len(stack) == 0 else len(operations) + 1