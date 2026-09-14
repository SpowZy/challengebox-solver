import random

def gen(rng, scale):
    if scale == "edge":
        choice = rng.randint(0, 4)
        
        if choice == 0:
            # Single int field
            schemas = ((("field", "x", "int"),),)
            root = 0
            operations = (
                ("put", "x", "int"),
                ("close",),
            )
        elif choice == 1:
            # Default fill multiple ints
            schemas = ((("field", "a", "int"), ("field", "b", "int")),)
            root = 0
            operations = (
                ("default", 2),
                ("close",),
            )
        elif choice == 2:
            # Single element array with default
            schemas = ((("field", "arr", ("array", "int", 1)),),)
            root = 0
            operations = (
                ("open", "arr", ("array", "int", 1)),
                ("default", 1),
                ("close",),
                ("close",),
            )
        elif choice == 3:
            # Text field
            schemas = ((("field", "msg", "text"),),)
            root = 0
            operations = (
                ("put", "msg", "text"),
                ("close",),
            )
        else:
            # Partial array fill (close before full capacity)
            schemas = ((("field", "arr", ("array", "int", 3)),),)
            root = 0
            operations = (
                ("open", "arr", ("array", "int", 3)),
                ("default", 1),
                ("close",),
                ("close",),
            )
        
        return [schemas, root, operations]
    
    elif scale == "small":
        choice = rng.randint(0, 3)
        
        if choice == 0:
            # Three mixed primitive fields
            schemas = ((("field", "a", "int"), ("field", "b", "text"), ("field", "c", "int")),)
            root = 0
            operations = (
                ("put", "a", "int"),
                ("put", "b", "text"),
                ("put", "c", "int"),
                ("close",),
            )
        elif choice == 1:
            # Array with default fill
            schemas = ((("field", "x", "int"), ("field", "arr", ("array", "text", 2))),)
            root = 0
            operations = (
                ("put", "x", "int"),
                ("open", "arr", ("array", "text", 2)),
                ("default", 2),
                ("close",),
                ("close",),
            )
        elif choice == 2:
            # Nested record
            schemas = (
                (("field", "a", "int"), ("field", "b", "int"), ("field", "nested", ("record", 1))),
                (("field", "x", "int"), ("field", "y", "int")),
            )
            root = 0
            operations = (
                ("put", "a", "int"),
                ("put", "b", "int"),
                ("open", "nested", ("record", 1)),
                ("put", "x", "int"),
                ("put", "y", "int"),
                ("close",),
                ("close",),
            )
        else:
            # Array with partial fill then more fields
            schemas = ((("field", "arr", ("array", "int", 4)), ("field", "end", "text")),)
            root = 0
            operations = (
                ("open", "arr", ("array", "int", 4)),
                ("default", 2),
                ("close",),
                ("put", "end", "text"),
                ("close",),
            )
        
        return [schemas, root, operations]
    
    else:  # medium
        choice = rng.randint(0, 2)
        
        if choice == 0:
            # Schema with repeat (flattens to 4 fields)
            schemas = ((("field", "a", "int"), ("field", "b", "text"), ("repeat", 0, 2)),)
            root = 0
            operations = (
                ("default", 4),
                ("close",),
            )
        elif choice == 1:
            # Array of records
            schemas = (
                (("field", "outer_arr", ("array", ("record", 1), 2)),),
                (("field", "x", "int"), ("field", "y", "text")),
            )
            root = 0
            operations = (
                ("open", "outer_arr", ("array", ("record", 1), 2)),
                ("open", None, ("record", 1)),
                ("put", "x", "int"),
                ("put", "y", "text"),
                ("close",),
                ("close",),
                ("close",),
            )
        else:
            # Multiple arrays with fields
            schemas = ((("field", "a1", ("array", "int", 2)), ("field", "b", "text"), ("field", "a2", ("array", "int", 3))),)
            root = 0
            operations = (
                ("open", "a1", ("array", "int", 2)),
                ("default", 2),
                ("close",),
                ("put", "b", "text"),
                ("open", "a2", ("array", "int", 3)),
                ("default", 3),
                ("close",),
                ("close",),
            )
        
        return [schemas, root, operations]