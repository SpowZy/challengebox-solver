def validate_build(schemas, root, operations):
    # Precompute flattened field counts and whether all fields are primitive
    flattened_count = {}
    all_primitive = {}
    
    def compute_flattened_info(schema_idx):
        if schema_idx in flattened_count:
            return
        
        schema = schemas[schema_idx]
        count = 0
        primitive = True
        
        for term in schema:
            if term[0] == "field":
                count += 1
                descriptor = term[2]
                if descriptor not in ("int", "text"):
                    primitive = False
            elif term[0] == "repeat":
                source_schema, repetitions = term[1], term[2]
                compute_flattened_info(source_schema)
                source_count = flattened_count[source_schema]
                source_all_primitive = all_primitive[source_schema]
                
                count += source_count * repetitions
                if not source_all_primitive:
                    primitive = False
        
        flattened_count[schema_idx] = count
        all_primitive[schema_idx] = primitive
    
    for i in range(len(schemas)):
        compute_flattened_info(i)
    
    def get_flattened_field(schema_idx, position):
        schema = schemas[schema_idx]
        current_pos = 0
        
        for term in schema:
            if term[0] == "field":
                if current_pos == position:
                    return term
                current_pos += 1
            elif term[0] == "repeat":
                source_schema, repetitions = term[1], term[2]
                source_count = flattened_count[source_schema]
                term_size = source_count * repetitions
                
                if current_pos + term_size > position:
                    offset = position - current_pos
                    source_position = offset % source_count
                    return get_flattened_field(source_schema, source_position)
                
                current_pos += term_size
        
        return None
    
    def are_fields_primitive(schema_idx, start_pos, end_pos):
        schema = schemas[schema_idx]
        current_pos = 0
        
        for term in schema:
            if term[0] == "field":
                if start_pos <= current_pos < end_pos:
                    descriptor = term[2]
                    if descriptor not in ("int", "text"):
                        return False
                current_pos += 1
            elif term[0] == "repeat":
                source_schema, repetitions = term[1], term[2]
                source_count = flattened_count[source_schema]
                term_size = source_count * repetitions
                
                if start_pos < current_pos + term_size and end_pos > current_pos:
                    if not all_primitive[source_schema]:
                        return False
                
                current_pos += term_size
        
        return True
    
    class Container:
        def __init__(self, descriptor, is_root=False):
            self.descriptor = descriptor
            self.is_root = is_root
            if descriptor[0] == "record":
                schema_idx = descriptor[1]
                self.layout_size = flattened_count[schema_idx]
                self.position = 0
                self.schema_idx = schema_idx
            elif descriptor[0] == "array":
                self.element_descriptor = descriptor[1]
                self.capacity = descriptor[2]
                self.position = 0
    
    stack = [Container(("record", root), is_root=True)]
    
    for op_idx, operation in enumerate(operations):
        if not stack:
            return op_idx + 1
        
        current = stack[-1]
        
        if operation[0] == "put":
            name, primitive = operation[1], operation[2]
            
            if current.descriptor[0] == "record":
                if current.position >= current.layout_size:
                    return op_idx + 1
                
                field = get_flattened_field(current.schema_idx, current.position)
                if field is None or field[0] != "field":
                    return op_idx + 1
                
                field_name, field_descriptor = field[1], field[2]
                
                if name != field_name or field_descriptor != primitive:
                    return op_idx + 1
                
                current.position += 1
                
            elif current.descriptor[0] == "array":
                if name is not None:
                    return op_idx + 1
                
                if current.position >= current.capacity:
                    return op_idx + 1
                
                if current.element_descriptor != primitive:
                    return op_idx + 1
                
                current.position += 1
        
        elif operation[0] == "open":
            name, descriptor = operation[1], operation[2]
            
            if current.descriptor[0] == "record":
                if current.position >= current.layout_size:
                    return op_idx + 1
                
                field = get_flattened_field(current.schema_idx, current.position)
                if field is None or field[0] != "field":
                    return op_idx + 1
                
                field_name, field_descriptor = field[1], field[2]
                
                if name != field_name or field_descriptor != descriptor:
                    return op_idx + 1
                
                current.position += 1
                stack.append(Container(descriptor))
                
            elif current.descriptor[0] == "array":
                if name is not None:
                    return op_idx + 1
                
                if current.position >= current.capacity:
                    return op_idx + 1
                
                if current.element_descriptor != descriptor:
                    return op_idx + 1
                
                current.position += 1
                stack.append(Container(descriptor))
        
        elif operation[0] == "default":
            k = operation[1]
            
            if current.descriptor[0] == "record":
                remaining = current.layout_size - current.position
                if k > remaining:
                    return op_idx + 1
                
                if not are_fields_primitive(current.schema_idx, current.position, current.position + k):
                    return op_idx + 1
                
                current.position += k
                
            elif current.descriptor[0] == "array":
                if current.element_descriptor not in ("int", "text"):
                    return op_idx + 1
                
                remaining = current.capacity - current.position
                if k > remaining:
                    return op_idx + 1
                
                current.position += k
        
        elif operation[0] == "close":
            if current.descriptor[0] == "record":
                if current.position != current.layout_size:
                    return op_idx + 1
            
            stack.pop()
    
    if len(stack) == 0:
        return 0
    else:
        return len(operations) + 1