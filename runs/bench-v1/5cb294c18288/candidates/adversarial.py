def validate_build(schemas, root, operations):
    flattened_cache = {}
    
    class FlattenedSchema:
        def __init__(self, schema_index):
            self.schema_index = schema_index
            self.terms = schemas[schema_index]
            self._count_cache = None
            self._field_cache = {}
        
        def count_fields(self):
            if self._count_cache is not None:
                return self._count_cache
            
            count = 0
            for term in self.terms:
                if term[0] == "field":
                    count += 1
                elif term[0] == "repeat":
                    _, schema_idx, repeat_count = term
                    sub_flat = get_flattened(schema_idx)
                    count += sub_flat.count_fields() * repeat_count
            
            self._count_cache = count
            return count
        
        def field_at(self, position):
            if position in self._field_cache:
                return self._field_cache[position]
            
            pos = 0
            for term in self.terms:
                if term[0] == "field":
                    if position == pos:
                        _, name, desc = term
                        result = (name, desc)
                        self._field_cache[position] = result
                        return result
                    pos += 1
                elif term[0] == "repeat":
                    _, schema_idx, repeat_count = term
                    sub_flat = get_flattened(schema_idx)
                    sub_count = sub_flat.count_fields()
                    total_count = sub_count * repeat_count
                    if position < pos + total_count:
                        offset = position - pos
                        sub_position = offset % sub_count
                        result = sub_flat.field_at(sub_position)
                        self._field_cache[position] = result
                        return result
                    pos += total_count
            
            raise IndexError()
    
    def get_flattened(schema_index):
        if schema_index not in flattened_cache:
            flattened_cache[schema_index] = FlattenedSchema(schema_index)
        return flattened_cache[schema_index]
    
    def is_primitive(d):
        return d == "int" or d == "text"
    
    root_flat = get_flattened(root)
    stack = [("record", (root_flat, 0))]
    
    for op_idx, op in enumerate(operations):
        op_idx_1based = op_idx + 1
        
        if not stack:
            return op_idx_1based
        
        container_type, state = stack[-1]
        
        if op[0] == "put":
            _, name, p = op
            
            if container_type != "record":
                return op_idx_1based
            
            flat, filled = state
            if filled >= flat.count_fields():
                return op_idx_1based
            
            next_name, next_desc = flat.field_at(filled)
            
            if name != next_name or next_desc != p or not is_primitive(next_desc):
                return op_idx_1based
            
            stack[-1] = ("record", (flat, filled + 1))
        
        elif op[0] == "open":
            _, name, d = op
            
            if container_type == "record":
                flat, filled = state
                if filled >= flat.count_fields():
                    return op_idx_1based
                
                next_name, next_desc = flat.field_at(filled)
                
                if name != next_name or next_desc != d or is_primitive(next_desc):
                    return op_idx_1based
                
                stack[-1] = ("record", (flat, filled + 1))
                
                if next_desc[0] == "record":
                    stack.append(("record", (get_flattened(next_desc[1]), 0)))
                else:
                    stack.append(("array", (next_desc[1], next_desc[2], 0)))
            
            elif container_type == "array":
                elem_desc, capacity, filled = state
                
                if filled >= capacity or name is not None or elem_desc != d or is_primitive(elem_desc):
                    return op_idx_1based
                
                stack[-1] = ("array", (elem_desc, capacity, filled + 1))
                
                if elem_desc[0] == "record":
                    stack.append(("record", (get_flattened(elem_desc[1]), 0)))
                else:
                    stack.append(("array", (elem_desc[1], elem_desc[2], 0)))
        
        elif op[0] == "default":
            _, k = op
            
            if container_type == "record":
                flat, filled = state
                total = flat.count_fields()
                
                if filled + k > total:
                    return op_idx_1based
                
                for i in range(k):
                    _, desc = flat.field_at(filled + i)
                    if not is_primitive(desc):
                        return op_idx_1based
                
                stack[-1] = ("record", (flat, filled + k))
            
            elif container_type == "array":
                elem_desc, capacity, filled = state
                
                if filled + k > capacity or not is_primitive(elem_desc):
                    return op_idx_1based
                
                stack[-1] = ("array", (elem_desc, capacity, filled + k))
        
        elif op[0] == "close":
            if container_type == "record":
                flat, filled = state
                if filled != flat.count_fields():
                    return op_idx_1based
            
            stack.pop()
    
    return 0 if len(stack) == 0 else len(operations) + 1