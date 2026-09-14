def validate_build(schemas, root, operations):
    field_counts_memo = {}
    
    def field_count(schema_idx):
        if schema_idx in field_counts_memo:
            return field_counts_memo[schema_idx]
        
        schema = schemas[schema_idx]
        count = 0
        
        for term in schema:
            if term[0] == "field":
                count += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                count += field_count(t) * r
        
        field_counts_memo[schema_idx] = count
        return count
    
    def get_field_at_position(schema_idx, position):
        pos = 0
        for term in schemas[schema_idx]:
            if term[0] == "field":
                if pos == position:
                    return (term[1], term[2])
                pos += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                base_count = field_count(t)
                repeat_total = base_count * r
                
                if position < pos + repeat_total:
                    rel_pos = position - pos
                    pos_in_rep = rel_pos % base_count
                    return get_field_at_position(t, pos_in_rep)
                
                pos += repeat_total
        
        return None
    
    is_all_primitive_memo = {}
    
    def is_all_primitive_full(schema_idx):
        if schema_idx in is_all_primitive_memo:
            return is_all_primitive_memo[schema_idx]
        
        schema = schemas[schema_idx]
        
        for term in schema:
            if term[0] == "field":
                if term[2] not in ["int", "text"]:
                    is_all_primitive_memo[schema_idx] = False
                    return False
            elif term[0] == "repeat":
                t = term[1]
                if not is_all_primitive_full(t):
                    is_all_primitive_memo[schema_idx] = False
                    return False
        
        is_all_primitive_memo[schema_idx] = True
        return True
    
    def is_range_all_primitive(schema_idx, start_pos, length):
        pos = 0
        
        for term in schemas[schema_idx]:
            if term[0] == "field":
                if start_pos <= pos < start_pos + length:
                    if term[2] not in ["int", "text"]:
                        return False
                pos += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                base_count = field_count(t)
                repeat_total = base_count * r
                
                term_end = pos + repeat_total
                
                if start_pos >= term_end or start_pos + length <= pos:
                    pos += repeat_total
                    continue
                
                if is_all_primitive_full(t):
                    pos += repeat_total
                    continue
                
                rel_start = max(0, start_pos - pos)
                rel_end = min(repeat_total, start_pos + length - pos)
                rel_length = rel_end - rel_start
                
                start_pat_pos = rel_start % base_count
                end_pat_pos = (rel_end - 1) % base_count if rel_end > 0 else (base_count - 1)
                
                if rel_start % base_count == 0 and rel_length >= base_count:
                    return False
                elif start_pat_pos <= end_pat_pos:
                    if not is_range_all_primitive(t, start_pat_pos, end_pat_pos - start_pat_pos + 1):
                        return False
                else:
                    if not is_range_all_primitive(t, start_pat_pos, base_count - start_pat_pos):
                        return False
                    if not is_range_all_primitive(t, 0, end_pat_pos + 1):
                        return False
                
                pos += repeat_total
        
        return True
    
    stack = [('record', root, field_count(root), 0)]
    
    for op_idx, op in enumerate(operations):
        if not stack:
            return op_idx + 1
        
        current_type, current_schema, current_field_count, current_pos = stack[-1]
        
        if op[0] == "put":
            name, p = op[1], op[2]
            
            if current_type == 'record':
                if current_pos >= current_field_count:
                    return op_idx + 1
                
                field_info = get_field_at_position(current_schema, current_pos)
                if field_info is None or name != field_info[0] or field_info[1] != p:
                    return op_idx + 1
                
                stack[-1] = (current_type, current_schema, current_field_count, current_pos + 1)
            else:
                if name is not None or current_pos >= current_field_count or current_schema != p:
                    return op_idx + 1
                
                stack[-1] = (current_type, current_schema, current_field_count, current_pos + 1)
        
        elif op[0] == "open":
            name, d = op[1], op[2]
            
            if current_type == 'record':
                if current_pos >= current_field_count:
                    return op_idx + 1
                
                field_info = get_field_at_position(current_schema, current_pos)
                if field_info is None or name != field_info[0] or field_info[1] != d:
                    return op_idx + 1
                
                stack[-1] = (current_type, current_schema, current_field_count, current_pos + 1)
            else:
                if name is not None or current_pos >= current_field_count or current_schema != d:
                    return op_idx + 1
                
                stack[-1] = (current_type, current_schema, current_field_count, current_pos + 1)
            
            if d[0] == "record":
                stack.append(('record', d[1], field_count(d[1]), 0))
            else:
                stack.append(('array', d[1], d[2], 0))
        
        elif op[0] == "default":
            k = op[1]
            
            if current_type == 'record':
                if k > current_field_count - current_pos:
                    return op_idx + 1
                
                if not is_range_all_primitive(current_schema, current_pos, k):
                    return op_idx + 1
                
                stack[-1] = (current_type, current_schema, current_field_count, current_pos + k)
            else:
                if current_schema not in ["int", "text"]:
                    return op_idx + 1
                
                if k > current_field_count - current_pos:
                    return op_idx + 1
                
                stack[-1] = (current_type, current_schema, current_field_count, current_pos + k)
        
        elif op[0] == "close":
            if current_type == 'record' and current_pos != current_field_count:
                return op_idx + 1
            
            stack.pop()
    
    return 0 if len(stack) == 0 else len(operations) + 1