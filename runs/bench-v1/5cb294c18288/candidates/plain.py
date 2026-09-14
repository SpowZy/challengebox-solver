def validate_build(schemas, root, operations):
    size_memo = {}
    field_memo = {}
    
    def flatten_size(schema_idx):
        if schema_idx in size_memo:
            return size_memo[schema_idx]
        
        total = 0
        for term in schemas[schema_idx]:
            if term[0] == "field":
                total += 1
            elif term[0] == "repeat":
                _, t, r = term
                total += flatten_size(t) * r
        
        size_memo[schema_idx] = total
        return total
    
    def get_field(schema_idx, pos):
        if (schema_idx, pos) in field_memo:
            return field_memo[(schema_idx, pos)]
        
        current_pos = 0
        for term in schemas[schema_idx]:
            if term[0] == "field":
                if current_pos == pos:
                    field_memo[(schema_idx, pos)] = term
                    return term
                current_pos += 1
            elif term[0] == "repeat":
                _, t, r = term
                sub_size = flatten_size(t)
                total_size = sub_size * r
                
                if current_pos + total_size > pos:
                    offset = pos - current_pos
                    sub_pos = offset % sub_size
                    result = get_field(t, sub_pos)
                    field_memo[(schema_idx, pos)] = result
                    return result
                
                current_pos += total_size
        
        field_memo[(schema_idx, pos)] = None
        return None
    
    def all_fields_primitive(schema_idx, start_pos, count):
        if count == 0:
            return True
        
        current_pos = 0
        fields_checked = 0
        
        for term in schemas[schema_idx]:
            if fields_checked >= count:
                return True
            
            if term[0] == "field":
                if current_pos >= start_pos:
                    if term[2] not in ("int", "text"):
                        return False
                    fields_checked += 1
                current_pos += 1
            elif term[0] == "repeat":
                _, t, r = term
                sub_size = flatten_size(t)
                total_size = sub_size * r
                
                if current_pos + total_size <= start_pos:
                    current_pos += total_size
                    continue
                
                if current_pos >= start_pos + count:
                    return True
                
                if not all_fields_primitive(t, 0, sub_size):
                    return False
                
                first_pos_in_block = max(current_pos, start_pos)
                last_pos_in_block = min(current_pos + total_size, start_pos + count)
                fields_in_range = last_pos_in_block - first_pos_in_block
                fields_checked += fields_in_range
                
                current_pos += total_size
        
        return fields_checked >= count
    
    stack = [(("record", root), 0, flatten_size(root))]
    
    for op_idx, op in enumerate(operations):
        if not stack:
            return op_idx + 1
        
        current_container_type, current_pos, current_max = stack[-1]
        
        if op[0] == "put":
            _, name, p = op
            
            if current_container_type[0] == "record":
                if current_pos >= current_max:
                    return op_idx + 1
                
                expected = get_field(current_container_type[1], current_pos)
                if expected is None or expected[1] != name or expected[2] != p:
                    return op_idx + 1
                
                stack[-1] = (current_container_type, current_pos + 1, current_max)
            else:
                if current_pos >= current_max:
                    return op_idx + 1
                
                if name is not None or current_container_type[2] != p:
                    return op_idx + 1
                
                stack[-1] = (current_container_type, current_pos + 1, current_max)
        
        elif op[0] == "open":
            _, name, d = op
            
            if current_container_type[0] == "record":
                if current_pos >= current_max:
                    return op_idx + 1
                
                expected = get_field(current_container_type[1], current_pos)
                if expected is None or expected[1] != name or expected[2] != d:
                    return op_idx + 1
                
                stack[-1] = (current_container_type, current_pos + 1, current_max)
            else:
                if current_pos >= current_max:
                    return op_idx + 1
                
                if name is not None or current_container_type[2] != d:
                    return op_idx + 1
                
                stack[-1] = (current_container_type, current_pos + 1, current_max)
            
            if d[0] == "record":
                stack.append((d, 0, flatten_size(d[1])))
            else:
                stack.append((d, 0, d[2]))
        
        elif op[0] == "default":
            _, k = op
            
            if current_container_type[0] == "record":
                if current_max - current_pos < k:
                    return op_idx + 1
                
                if not all_fields_primitive(current_container_type[1], current_pos, k):
                    return op_idx + 1
                
                stack[-1] = (current_container_type, current_pos + k, current_max)
            else:
                if current_container_type[2] not in ("int", "text"):
                    return op_idx + 1
                
                if current_max - current_pos < k:
                    return op_idx + 1
                
                stack[-1] = (current_container_type, current_pos + k, current_max)
        
        elif op[0] == "close":
            if current_container_type[0] == "record":
                if current_pos != current_max:
                    return op_idx + 1
            
            stack.pop()
    
    return 0 if not stack else len(operations) + 1