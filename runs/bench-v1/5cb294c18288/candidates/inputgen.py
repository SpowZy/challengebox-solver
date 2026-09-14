import random

def gen(rng, scale):
    if scale == "edge":
        # Degenerate cases: single field, minimal operations
        choice = rng.randint(0, 2)
        if choice == 0:
            schemas = [(("field", "a", "int"),)]
            operations = [("put", "a", "int"), ("close",)]
        elif choice == 1:
            schemas = [(("field", "x", "text"),)]
            operations = [("put", "x", "text"), ("close",)]
        else:
            # Two identical fields
            schemas = [(("field", "a", "int"), ("field", "b", "int"))]
            operations = [("put", "a", "int"), ("put", "b", "int"), ("close",)]
        
        root = 0
        return [schemas, root, operations]
    
    elif scale == "small":
        # Small: multiple primitive fields, with or without default
        choice = rng.randint(0, 1)
        if choice == 0:
            # Multiple fields with individual puts
            schemas = [(("field", "a", "int"), ("field", "b", "text"), ("field", "c", "int"))]
            root = 0
            operations = [
                ("put", "a", "int"),
                ("put", "b", "text"),
                ("put", "c", "int"),
                ("close",)
            ]
        else:
            # Default operation on all int fields
            schemas = [(("field", "x", "int"), ("field", "y", "int"), ("field", "z", "int"))]
            root = 0
            operations = [("default", 3), ("close",)]
        
        return [schemas, root, operations]
    
    elif scale == "medium":
        # Medium: arrays, nested records, or schema repeats
        choice = rng.randint(0, 2)
        
        if choice == 0:
            # Array of primitives with partial fill
            schemas = [(("field", "items", ("array", "int", 3)), ("field", "name", "text"))]
            root = 0
            operations = [
                ("open", "items", ("array", "int", 3)),
                ("put", None, "int"),
                ("put", None, "int"),
                ("close",),
                ("put", "name", "text"),
                ("close",)
            ]
        elif choice == 1:
            # Nested record
            schemas = [
                (("field", "val", "int"),),
                (("field", "nested", ("record", 0)), ("field", "tag", "text"))
            ]
            root = 1
            operations = [
                ("open", "nested", ("record", 0)),
                ("put", "val", "int"),
                ("close",),
                ("put", "tag", "text"),
                ("close",)
            ]
        else:
            # Schema with repeat: repeats schema 0 twice then adds field b
            schemas = [
                (("field", "a", "int"),),
                (("repeat", 0, 2), ("field", "b", "text"))
            ]
            root = 1
            operations = [
                ("put", "a", "int"),
                ("put", "a", "int"),
                ("put", "b", "text"),
                ("close",)
            ]
        
        return [schemas, root, operations]