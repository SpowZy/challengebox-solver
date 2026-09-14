def validate_build(schemas, root, operations):
    field_count_cache = {}
    
    def count_fields(idx):
        if idx in field_count_cache:
            return field_count_cache[idx]
        count = 0
        for term in schemas[idx]:
            if term[0] == "field":
                count += 1
            elif term[0] == "repeat":
                schema_idx, repeat_count = term[1], term[2]
                base_count = count_fields(schema_idx)
                count += base_count * repeat_count
        field_count_cache[idx] = count
        return count
    
    field_all_primitive_cache = {}
    
    def all_fields_primitive(schema_idx):
        if schema_idx in field_all_primitive_cache:
            return field_all_primitive_cache[schema_idx]
        result = True
        for term in schemas[schema_idx]:
            if term[0] == "field":
                _, desc = term[1], term[2]
                if desc not in ["int", "text"]:
                    result = False
                    break
            elif term[0] == "repeat":
                repeat_schema_idx, _ = term[1], term[2]
                if not all_fields_primitive(repeat_schema_idx):
                    result = False
                    break
        field_all_primitive_cache[schema_idx] = result
        return result
    
    def get_field(schema_idx, position):
        current_pos = 0
        for term in schemas[schema_idx]:
            if term[0] == "field":
                if current_pos == position:
                    return term[1], term[2]
                current_pos += 1
            elif term[0] == "repeat":
                repeat_schema_idx, repeat_count = term[1], term[2]
                base_count = count_fields(repeat_schema_idx)
                total_repeat_count = base_count * repeat_count
                if position < current_pos + total_repeat_count:
                    offset = position - current_pos
                    field_in_base = offset % base_count
                    return get_field(repeat_schema_idx, field_in_base)
                current_pos += total_repeat_count
        return None
    
    def fields_in_range_all_primitive(schema_idx, start_idx, end_idx):
        current_pos = 0
        for term in schemas[schema_idx]:
            if term[0] == "field":
                if current_pos >= start_idx and current_pos < end_idx:
                    _, desc = term[1], term[2]
                    if desc not in ["int", "text"]:
                        return False
                current_pos += 1
            elif term[0] == "repeat":
                repeat_schema_idx, repeat_count = term[1], term[2]
                base_count = count_fields(repeat_schema_idx)
                total_repeat_count = base_count * repeat_count
                if current_pos + total_repeat_count > start_idx and current_pos < end_idx:
                    if not all_fields_primitive(repeat_schema_idx):
                        return False
                current_pos += total_repeat_count
        return True
    
    stack = [{'type': 'record', 'schema_idx': root, 'current_field_idx': 0, 'total_fields': count_fields(root)}]
    
    for op_idx, op in enumerate(operations, 1):
        if not stack:
            return op_idx
        current = stack[-1]
        
        if op[0] == "put":
            name, value_type = op[1], op[2]
            if current['type'] == 'record':
                if current['current_field_idx'] >= current['total_fields']:
                    return op_idx
                field_info = get_field(current['schema_idx'], current['current_field_idx'])
                if field_info is None or field_info[0] != name or field_info[1] != value_type:
                    return op_idx
                current['current_field_idx'] += 1
            elif current['type'] == 'array':
                if name is not None or current['element_desc'] != value_type or current['current_count'] >= current['capacity']:
                    return op_idx
                current['current_count'] += 1
        
        elif op[0] == "open":
            name, descriptor = op[1], op[2]
            if current['type'] == 'record':
                if current['current_field_idx'] >= current['total_fields']:
                    return op_idx
                field_info = get_field(current['schema_idx'], current['current_field_idx'])
                if field_info is None or field_info[0] != name or field_info[1] != descriptor:
                    return op_idx
                current['current_field_idx'] += 1
                if descriptor[0] == "record":
                    stack.append({'type': 'record', 'schema_idx': descriptor[1], 'current_field_idx': 0, 'total_fields': count_fields(descriptor[1])})
                elif descriptor[0] == "array":
                    stack.append({'type': 'array', 'element_desc': descriptor[1], 'capacity': descriptor[2], 'current_count': 0})
                else:
                    return op_idx
            elif current['type'] == 'array':
                if name is not None or current['element_desc'] != descriptor or current['current_count'] >= current['capacity']:
                    return op_idx
                current['current_count'] += 1
                if descriptor[0] == "record":
                    stack.append({'type': 'record', 'schema_idx': descriptor[1], 'current_field_idx': 0, 'total_fields': count_fields(descriptor[1])})
                elif descriptor[0] == "array":
                    stack.append({'type': 'array', 'element_desc': descriptor[1], 'capacity': descriptor[2], 'current_count': 0})
                else:
                    return op_idx
        
        elif op[0] == "default":
            k = op[1]
            if current['type'] == 'record':
                remaining = current['total_fields'] - current['current_field_idx']
                if remaining < k or not fields_in_range_all_primitive(current['schema_idx'], current['current_field_idx'], current['current_field_idx'] + k):
                    return op_idx
                current['current_field_idx'] += k
            elif current['type'] == 'array':
                if current['element_desc'] not in ["int", "text"] or current['current_count'] + k > current['capacity']:
                    return op_idx
                current['current_count'] += k
        
        elif op[0] == "close":
            if current['type'] == 'record' and current['current_field_idx'] != current['total_fields']:
                return op_idx
            stack.pop()
        
        else:
            return op_idx
    
    return 0 if len(stack) == 0 else len(operations) + 1