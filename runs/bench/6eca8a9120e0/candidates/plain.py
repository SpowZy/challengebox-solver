def capture_binders(nodes, expr_root, target, replacement_root):
    def find_free_in_replacement():
        free = set()
        def visit(idx, bound):
            n = nodes[idx]
            if n[0] == "var":
                if n[1] not in bound:
                    free.add(n[1])
            elif n[0] == "call":
                for c in n[1]:
                    visit(c, bound)
            elif n[0] == "bind":
                new_bound = bound | {name for _, name in n[1]}
                visit(n[2], new_bound)
            elif n[0] == "let":
                _, name = n[1]
                visit(n[2], bound)
                visit(n[3], bound | {name})
            elif n[0] == "match":
                visit(n[1], bound)
                shared = {name for _, name in n[2]}
                for arm in n[3]:
                    if arm[0] == "ctor":
                        fields = {name for _, name in arm[1]}
                        for a in arm[2]:
                            visit(a, bound)
                        visit(arm[3], bound | shared | fields)
                    elif arm[0] == "zero":
                        for a in arm[1]:
                            visit(a, bound)
                        visit(arm[2], bound | shared)
                    elif arm[0] == "succ":
                        pred = arm[1][1]
                        for a in arm[2]:
                            visit(a, bound)
                        visit(arm[3], bound | shared | {pred})
        visit(replacement_root, set())
        return target in free
    
    if not find_free_in_replacement():
        return []
    
    capturing = set()
    
    def dfs(idx, path_bindings, bound_in_path):
        n = nodes[idx]
        
        if n[0] == "var":
            if n[1] == target and target not in bound_in_path:
                for decl_id, name in path_bindings:
                    if name == target:
                        capturing.add(decl_id)
        
        elif n[0] == "call":
            for c in n[1]:
                dfs(c, path_bindings, bound_in_path)
        
        elif n[0] == "bind":
            new_path = path_bindings + list(n[1])
            new_bound = bound_in_path | {name for _, name in n[1]}
            dfs(n[2], new_path, new_bound)
        
        elif n[0] == "let":
            id_, name = n[1]
            dfs(n[2], path_bindings, bound_in_path)
            dfs(n[3], path_bindings + [(id_, name)], bound_in_path | {name})
        
        elif n[0] == "match":
            dfs(n[1], path_bindings, bound_in_path)
            shared = n[2]
            shared_names = {name for _, name in shared}
            for arm in n[3]:
                if arm[0] == "ctor":
                    fields = arm[1]
                    field_names = {name for _, name in fields}
                    new_path = path_bindings + shared + fields
                    new_bound = bound_in_path | shared_names | field_names
                    for a in arm[2]:
                        dfs(a, path_bindings, bound_in_path)
                    dfs(arm[3], new_path, new_bound)
                elif arm[0] == "zero":
                    new_path = path_bindings + shared
                    new_bound = bound_in_path | shared_names
                    for a in arm[1]:
                        dfs(a, path_bindings, bound_in_path)
                    dfs(arm[2], new_path, new_bound)
                elif arm[0] == "succ":
                    pred = arm[1]
                    new_path = path_bindings + shared + [pred]
                    new_bound = bound_in_path | shared_names | {pred[1]}
                    for a in arm[2]:
                        dfs(a, path_bindings, bound_in_path)
                    dfs(arm[3], new_path, new_bound)
    
    dfs(expr_root, [], set())
    return sorted(capturing)