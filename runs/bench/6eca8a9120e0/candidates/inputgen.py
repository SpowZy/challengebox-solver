import random

def gen(rng, scale):
    if scale == "edge":
        return gen_edge(rng)
    elif scale == "small":
        return gen_small(rng)
    else:  # medium
        return gen_medium(rng)


def gen_edge(rng):
    """Edge cases: minimal, degenerate, and extreme valid inputs."""
    case = rng.randint(0, 4)
    
    if case == 0:
        # Single variable node, no binding
        nodes = [("var", "x")]
        return [nodes, 0, "y", 0]
    
    elif case == 1:
        # Two disjoint variables, no structure
        nodes = [
            ("var", "a"),  # 0: replacement
            ("var", "b"),  # 1: expression
        ]
        return [nodes, 1, "c", 0]
    
    elif case == 2:
        # Variable with binding that shadows target
        nodes = [
            ("var", "x"),        # 0: replacement - free var x
            ("var", "x"),        # 1: var in body of bind
            ("bind", [(1, "x")], 1),  # 2: bind x (could capture)
        ]
        return [nodes, 2, "x", 0]
    
    elif case == 3:
        # Call node with single child
        nodes = [
            ("var", "v"),     # 0: replacement
            ("var", "w"),     # 1: child of call
            ("call", [1]),    # 2: call (expression)
        ]
        return [nodes, 2, "target", 0]
    
    else:
        # Let binding
        nodes = [
            ("var", "r"),           # 0: replacement
            ("var", "a"),           # 1: value expr
            ("var", "b"),           # 2: body expr
            ("let", (1, "a"), 1, 2),  # 3: let a = value in body
        ]
        return [nodes, 3, "a", 0]


def gen_small(rng):
    """Small inputs: 3-8 nodes, simple nesting."""
    nodes = [
        ("var", "x"),        # 0: replacement - has free variable x
        ("var", "x"),        # 1: variable to replace
        ("bind", [(0, "x")], 1),  # 2: binding x (could capture)
    ]
    
    # Optionally nest another binding
    if rng.random() < 0.5:
        nodes.append(("bind", [(1, "y")], 2))
        expr_root = 3
    else:
        expr_root = 2
    
    # Optionally add a call wrapping
    if rng.random() < 0.3:
        nodes.append(("call", [1]))
        expr_root = len(nodes) - 1
    
    return [nodes, expr_root, "x", 0]


def gen_medium(rng):
    """Medium inputs: 10-30 nodes, deeper nesting and structure."""
    nodes = []
    idx = 0
    
    # Build replacement tree (2-3 nodes)
    repl_root = idx
    repl_var = "z"
    nodes.append(("var", repl_var))
    idx += 1
    
    # Build expression: start with inner variable
    inner_var_idx = idx
    nodes.append(("var", "inner"))
    idx += 1
    
    # Wrap in nested bindings (3-5 layers)
    current_body = inner_var_idx
    num_bindings = rng.randint(3, 5)
    
    for i in range(num_bindings):
        bind_idx = idx
        decl_name = chr(ord("a") + (i % 26))
        nodes.append(("bind", [(i, decl_name)], current_body))
        idx += 1
        current_body = bind_idx
    
    # Optionally wrap in a call
    expr_root = current_body
    if rng.random() < 0.5:
        call_idx = idx
        nodes.append(("call", [current_body]))
        expr_root = call_idx
    
    return [nodes, expr_root, repl_var, repl_root]