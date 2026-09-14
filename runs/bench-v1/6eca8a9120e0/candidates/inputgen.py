import random

def gen(rng, scale):
    """Generate valid inputs for capture_binders differential testing."""
    
    if scale == "edge":
        return gen_edge(rng)
    elif scale == "small":
        return gen_small(rng)
    elif scale == "medium":
        return gen_medium(rng)
    else:
        raise ValueError(f"Unknown scale: {scale}")

def gen_edge(rng):
    """Edge cases: degenerate, minimal, and boundary conditions."""
    choice = rng.randint(0, 4)
    
    if choice == 0:
        # No target match in expression
        expr_nodes = [("var", "x")]
        repl_nodes = [("var", "y")]
        return [expr_nodes, 0, "notfound", repl_nodes, 0]
    
    elif choice == 1:
        # Single var, target found, no binding, no capture
        expr_nodes = [("var", "x")]
        repl_nodes = [("var", "y")]
        return [expr_nodes, 0, "x", repl_nodes, 0]
    
    elif choice == 2:
        # Simple let binding with capture
        expr_nodes = [
            ("let", (0, "x"), 1, 2),
            ("var", "v"),
            ("var", "x")
        ]
        repl_nodes = [("var", "x")]
        return [expr_nodes, 0, "x", repl_nodes, 0]
    
    elif choice == 3:
        # Simple bind, no capture (replacement doesn't use binding name)
        expr_nodes = [
            ("bind", [(0, "x")], 1),
            ("var", "x")
        ]
        repl_nodes = [("var", "y")]
        return [expr_nodes, 0, "x", repl_nodes, 0]
    
    else:  # choice == 4
        # Call node with variable reuse
        expr_nodes = [
            ("call", [1]),
            ("var", "x")
        ]
        repl_nodes = [("var", "x")]
        return [expr_nodes, 0, "x", repl_nodes, 0]

def gen_small(rng):
    """Small cases: few elements, quadratic algorithms feasible."""
    choice = rng.randint(0, 3)
    
    if choice == 0:
        # Nested let bindings
        expr_nodes = [
            ("let", (0, "x"), 1, 2),
            ("var", "v1"),
            ("let", (1, "y"), 3, 4),
            ("var", "v2"),
            ("var", "y")
        ]
        repl_nodes = [("var", "free")]
        return [expr_nodes, 0, "y", repl_nodes, 0]
    
    elif choice == 1:
        # Match with constructor arm
        expr_nodes = [
            ("match", 0, [], [1]),
            ("ctor", [2], [], 3),
            ("var", "field"),
            ("var", "target")
        ]
        repl_nodes = [("var", "z")]
        return [expr_nodes, 0, "target", repl_nodes, 0]
    
    elif choice == 2:
        # DAG with variable reuse
        expr_nodes = [
            ("call", [1, 1, 2]),
            ("var", "x"),
            ("var", "y")
        ]
        repl_nodes = [("var", "z")]
        return [expr_nodes, 0, "x", repl_nodes, 0]
    
    else:  # choice == 3
        # Bind with multiple declarations
        expr_nodes = [
            ("bind", [(0, "a"), (1, "b"), (2, "c")], 1),
            ("call", [2, 3, 4]),
            ("var", "a"),
            ("var", "b"),
            ("var", "c")
        ]
        repl_nodes = [("var", "x")]
        return [expr_nodes, 0, "a", repl_nodes, 0]

def gen_medium(rng):
    """Medium cases: tens of elements, slower algorithms acceptable."""
    choice = rng.randint(0, 4)
    
    if choice == 0:
        # Deeper nesting of let bindings
        expr_nodes = [
            ("let", (0, "x"), 1, 2),
            ("var", "v0"),
            ("let", (1, "y"), 3, 4),
            ("var", "v1"),
            ("let", (2, "z"), 5, 6),
            ("var", "v2"),
            ("var", "z")
        ]
        repl_nodes = [("var", "free")]
        return [expr_nodes, 0, "z", repl_nodes, 0]
    
    elif choice == 1:
        # Match with all three arm types (ctor, zero, succ)
        expr_nodes = [
            ("match", 1, [], [2, 3, 4]),
            ("var", "scrutinee"),
            ("ctor", [5], [], 6),
            ("zero", [], 7),
            ("succ", 8, [], 9),
            ("var", "field"),
            ("var", "target"),
            ("var", "target"),
            ("var", "pred"),
            ("var", "target")
        ]
        repl_nodes = [("var", "x")]
        return [expr_nodes, 0, "target", repl_nodes, 0]
    
    elif choice == 2:
        # DAG with diamond pattern
        expr_nodes = [
            ("call", [1, 2]),
            ("call", [3, 4]),
            ("call", [3, 5]),
            ("var", "target"),
            ("var", "y"),
            ("var", "z")
        ]
        repl_nodes = [("var", "w")]
        return [expr_nodes, 0, "target", repl_nodes, 0]
    
    elif choice == 3:
        # Bind and let nested together
        expr_nodes = [
            ("bind", [(0, "x")], 1),
            ("let", (1, "y"), 2, 3),
            ("var", "target"),
            ("call", [2, 4]),
            ("var", "y")
        ]
        repl_nodes = [("var", "free")]
        return [expr_nodes, 0, "target", repl_nodes, 0]
    
    else:  # choice == 4
        # Complex: let with match, replacement tree with call
        expr_nodes = [
            ("let", (0, "outer"), 1, 2),
            ("var", "init_value"),
            ("match", 3, [], [4]),
            ("var", "scrutinee"),
            ("ctor", [5], [], 6),
            ("var", "field"),
            ("var", "target")
        ]
        repl_nodes = [
            ("var", "a"),
            ("call", [0])
        ]
        return [expr_nodes, 0, "target", repl_nodes, 0]