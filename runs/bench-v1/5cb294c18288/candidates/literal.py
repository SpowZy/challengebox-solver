def validate_build(schemas, root, operations):
    flattened_cache = {}
    
    def get_flattened(schema_idx):
        if schema_idx in flattened_cache:
            return flattened_cache[schema_idx]
        
        schema = schemas[schema_idx]
        result = []
        
        for term in schema:
            if term[0] == "field":
                _, name, desc = term
                result.append(("field", name, desc))
            elif term[0] == "repeat":
                _, ref_idx, reps = term
                base = get_flattened(ref_idx)
                for _ in range(reps):
                    result.extend(base)
        
        flattened_cache[schema_idx] = result
        return result
    
    stack = [('record', (root, 0))]
    
    for op_idx, op in enumerate(operations):
        if not stack:
            return op_idx + 1
        
        cur_type, info = stack[-1]
        
        if op[0] == "put":
            _, name, prim = op
            
            if cur_type != 'record':
                return op_idx + 1
            
            schema_idx, field_idx = info
            layout = get_flattened(schema_idx)
            
            if field_idx >= len(layout):
                return op_idx + 1
            
            field_term = layout[field_idx]
            _, fname, fdesc = field_term
            
            if fname != name or fdesc != prim:
                return op_idx + 1
            
            stack[-1] = ('record', (schema_idx, field_idx + 1))
        
        elif op[0] == "open":
            _, name, desc = op
            
            if cur_type == 'record':
                schema_idx, field_idx = info
                layout = get_flattened(schema_idx)
                
                if field_idx >= len(layout):
                    return op_idx + 1
                
                field_term = layout[field_idx]
                _, fname, fdesc = field_term
                
                if fname != name or fdesc != desc:
                    return op_idx + 1
                
                stack[-1] = ('record', (schema_idx, field_idx + 1))
                
                if desc[0] == "record":
                    stack.append(('record', (desc[1], 0)))
                elif desc[0] == "array":
                    _, elem_desc, cap = desc
                    stack.append(('array', (elem_desc, 0, cap)))
            
            elif cur_type == 'array':
                elem_desc, count, capacity = info
                
                if name is not None or count >= capacity or elem_desc != desc:
                    return op_idx + 1
                
                stack[-1] = ('array', (elem_desc, count + 1, capacity))
                
                if desc[0] == "record":
                    stack.append(('record', (desc[1], 0)))
                elif desc[0] == "array":
                    _, elem_desc2, cap = desc
                    stack.append(('array', (elem_desc2, 0, cap)))
            
            else:
                return op_idx + 1
        
        elif op[0] == "default":
            _, k = op
            
            if cur_type == 'record':
                schema_idx, field_idx = info
                layout = get_flattened(schema_idx)
                
                if field_idx + k > len(layout):
                    return op_idx + 1
                
                for i in range(field_idx, field_idx + k):
                    field_term = layout[i]
                    _, _, fdesc = field_term
                    if fdesc not in ["int", "text"]:
                        return op_idx + 1
                
                stack[-1] = ('record', (schema_idx, field_idx + k))
            
            elif cur_type == 'array':
                elem_desc, count, capacity = info
                
                if elem_desc not in ["int", "text"] or count + k > capacity:
                    return op_idx + 1
                
                stack[-1] = ('array', (elem_desc, count + k, capacity))
            
            else:
                return op_idx + 1
        
        elif op[0] == "close":
            if cur_type == 'record':
                schema_idx, field_idx = info
                layout = get_flattened(schema_idx)
                
                if field_idx != len(layout):
                    return op_idx + 1
            
            stack.pop()
        
        else:
            return op_idx + 1
    
    if len(stack) == 0:
        return 0
    else:
        return len(operations) + 1