def validate_build(schemas, root, operations):
    def descriptor_equal(d1, d2):
        if d1 == d2:
            return True
        if not isinstance(d1, tuple) or not isinstance(d2, tuple):
            return False
        if d1[0] != d2[0]:
            return False
        if d1[0] == "record":
            return d1[1] == d2[1]
        elif d1[0] == "array":
            return descriptor_equal(d1[1], d2[1]) and d1[2] == d2[2]
        return False
    
    _count_cache = {}
    _all_prim_cache = {}
    MAX_FIELDS = 10**18
    
    def count_fields(s):
        if s in _count_cache:
            return _count_cache[s]
        count = 0
        for term in schemas[s]:
            if term[0] == "field":
                count += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                fields_in_t = count_fields(t)
                if fields_in_t > 0:
                    if fields_in_t > MAX_FIELDS // r:
                        count = MAX_FIELDS
                    else:
                        count += fields_in_t * r
                    if count >= MAX_FIELDS:
                        count = MAX_FIELDS
        _count_cache[s] = count
        return count
    
    def all_fields_primitive(s):
        if s in _all_prim_cache:
            return _all_prim_cache[s]
        result = True
        for term in schemas[s]:
            if term[0] == "field":
                if term[2] not in ("int", "text"):
                    result = False
                    break
            elif term[0] == "repeat":
                if not all_fields_primitive(term[1]):
                    result = False
                    break
        _all_prim_cache[s] = result
        return result
    
    def get_field_at_pos(s, pos):
        current_pos = 0
        for term in schemas[s]:
            if term[0] == "field":
                if current_pos == pos:
                    return term[1], term[2]
                current_pos += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                fields_in_t = count_fields(t)
                if fields_in_t > 0:
                    space = fields_in_t * r if fields_in_t <= MAX_FIELDS // r else MAX_FIELDS
                    if current_pos <= pos < current_pos + space:
                        return get_field_at_pos(t, (pos - current_pos) % fields_in_t)
                    current_pos += space
        return None, None
    
    def can_default_from(s, pos, count):
        current_pos = 0
        remaining = count
        for term in schemas[s]:
            if remaining == 0:
                return True
            if term[0] == "field":
                if current_pos >= pos:
                    if term[2] not in ("int", "text"):
                        return False
                    remaining -= 1
                current_pos += 1
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                fields_in_t = count_fields(t)
                if fields_in_t > 0:
                    space = fields_in_t * r if fields_in_t <= MAX_FIELDS // r else MAX_FIELDS
                    if current_pos + space <= pos:
                        current_pos += space
                    elif current_pos < pos:
                        offset = pos - current_pos
                        field_in_rep = offset % fields_in_t
                        if not can_default_from(t, field_in_rep, remaining):
                            return False
                        remaining -= (fields_in_t - field_in_rep)
                        current_pos += space
                    else:
                        if not all_fields_primitive(t):
                            return False
                        consumed = min(space, remaining)
                        remaining -= consumed
                        current_pos += space
        return remaining == 0
    
    stack = [{'type': 'record', 'schema': root, 'pos': 0, 'total': count_fields(root)}]
    
    for op_idx, op in enumerate(operations, 1):
        if not stack:
            return op_idx
        current = stack[-1]
        
        if op[0] == "put":
            name, p = op[1], op[2]
            if current['type'] == 'record':
                if current['pos'] >= current['total']:
                    return op_idx
                fname, fdesc = get_field_at_pos(current['schema'], current['pos'])
                if fname is None or fname != name or fdesc != p:
                    return op_idx
                current['pos'] += 1
            else:
                if name is not None or not descriptor_equal(current['elem_desc'], p):
                    return op_idx
                if current['count'] >= current['capacity']:
                    return op_idx
                current['count'] += 1
        
        elif op[0] == "open":
            name, d = op[1], op[2]
            if current['type'] == 'record':
                if current['pos'] >= current['total']:
                    return op_idx
                fname, fdesc = get_field_at_pos(current['schema'], current['pos'])
                if fname is None or fname != name or not descriptor_equal(fdesc, d):
                    return op_idx
                current['pos'] += 1
            else:
                if name is not None or not descriptor_equal(current['elem_desc'], d):
                    return op_idx
                if current['count'] >= current['capacity']:
                    return op_idx
                current['count'] += 1
            
            if d[0] == 'record':
                stack.append({'type': 'record', 'schema': d[1], 'pos': 0, 'total': count_fields(d[1])})
            else:
                stack.append({'type': 'array', 'elem_desc': d[1], 'capacity': d[2], 'count': 0})
        
        elif op[0] == "default":
            k = op[1]
            if current['type'] == 'record':
                if current['pos'] + k > current['total'] or not can_default_from(current['schema'], current['pos'], k):
                    return op_idx
                current['pos'] += k
            else:
                if current['elem_desc'] not in ("int", "text") or current['count'] + k > current['capacity']:
                    return op_idx
                current['count'] += k
        
        elif op[0] == "close":
            if current['type'] == 'record' and current['pos'] != current['total']:
                return op_idx
            stack.pop()
            if not stack and op_idx < len(operations):
                return op_idx + 1
    
    return len(operations) + 1 if stack else 0