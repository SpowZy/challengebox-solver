def validate_build(schemas, root, operations):
    flattened_cache = {}
    
    def flatten_schema(schema_idx):
        if schema_idx in flattened_cache:
            return flattened_cache[schema_idx]
        
        schema = schemas[schema_idx]
        fields = []
        
        for term in schema:
            if term[0] == "field":
                name, d = term[1], term[2]
                fields.append((name, d))
            elif term[0] == "repeat":
                t, r = term[1], term[2]
                sub_fields = flatten_schema(t)
                for _ in range(r):
                    fields.extend(sub_fields)
        
        flattened_cache[schema_idx] = fields
        return fields
    
    def desc_equal(d1, d2):
        if type(d1) != type(d2):
            return False
        if isinstance(d1, str):
            return d1 == d2
        if isinstance(d1, tuple):
            if d1[0] != d2[0]:
                return False
            if d1[0] == "record":
                return d1[1] == d2[1]
            elif d1[0] == "array":
                return desc_equal(d1[1], d2[1]) and d1[2] == d2[2]
        return False
    
    def is_primitive(d):
        return isinstance(d, str) and d in ("int", "text")
    
    class RecordContainer:
        def __init__(self, fields):
            self.fields = fields
            self.position = 0
        
        def get_next_field(self):
            if self.position < len(self.fields):
                return self.fields[self.position]
            return None
        
        def can_close(self):
            return self.position == len(self.fields)
    
    class ArrayContainer:
        def __init__(self, element_descriptor, capacity):
            self.element_descriptor = element_descriptor
            self.capacity = capacity
            self.position = 0
    
    root_fields = flatten_schema(root)
    container_stack = [RecordContainer(root_fields)]
    
    for op_idx, op in enumerate(operations, 1):
        if not container_stack:
            return op_idx
        
        current = container_stack[-1]
        
        if op[0] == "put":
            name, p = op[1], op[2]
            
            if isinstance(current, RecordContainer):
                field_info = current.get_next_field()
                if field_info is None:
                    return op_idx
                
                field_name, field_desc = field_info
                if field_name != name or not desc_equal(field_desc, p):
                    return op_idx
                
                current.position += 1
            
            elif isinstance(current, ArrayContainer):
                if name is not None:
                    return op_idx
                if current.position >= current.capacity:
                    return op_idx
                if not desc_equal(current.element_descriptor, p):
                    return op_idx
                
                current.position += 1
        
        elif op[0] == "open":
            name, d = op[1], op[2]
            
            if isinstance(current, RecordContainer):
                field_info = current.get_next_field()
                if field_info is None:
                    return op_idx
                
                field_name, field_desc = field_info
                if field_name != name or not desc_equal(field_desc, d):
                    return op_idx
                
                current.position += 1
                
                if isinstance(d, tuple) and d[0] == "record":
                    schema_idx = d[1]
                    new_fields = flatten_schema(schema_idx)
                    container_stack.append(RecordContainer(new_fields))
                elif isinstance(d, tuple) and d[0] == "array":
                    element_desc, capacity = d[1], d[2]
                    container_stack.append(ArrayContainer(element_desc, capacity))
            
            elif isinstance(current, ArrayContainer):
                if name is not None:
                    return op_idx
                if current.position >= current.capacity:
                    return op_idx
                if not desc_equal(current.element_descriptor, d):
                    return op_idx
                
                current.position += 1
                
                if isinstance(d, tuple) and d[0] == "record":
                    schema_idx = d[1]
                    new_fields = flatten_schema(schema_idx)
                    container_stack.append(RecordContainer(new_fields))
                elif isinstance(d, tuple) and d[0] == "array":
                    element_desc, capacity = d[1], d[2]
                    container_stack.append(ArrayContainer(element_desc, capacity))
        
        elif op[0] == "close":
            if isinstance(current, RecordContainer):
                if not current.can_close():
                    return op_idx
            
            container_stack.pop()
        
        elif op[0] == "default":
            k = op[1]
            
            if isinstance(current, RecordContainer):
                remaining = current.fields[current.position:]
                if len(remaining) < k:
                    return op_idx
                for i in range(k):
                    if not is_primitive(remaining[i][1]):
                        return op_idx
                current.position += k
            
            elif isinstance(current, ArrayContainer):
                if not is_primitive(current.element_descriptor):
                    return op_idx
                remaining_capacity = current.capacity - current.position
                if remaining_capacity < k:
                    return op_idx
                current.position += k
    
    if container_stack:
        return len(operations) + 1
    else:
        return 0