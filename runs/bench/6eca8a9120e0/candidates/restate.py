def capture_binders(nodes, expr_root, target, replacement_root):
    def get_free_names():
        free = set()
        
        def visit(node_idx, bound_names):
            node = nodes[node_idx]
            
            if node[0] == "var":
                if node[1] not in bound_names:
                    free.add(node[1])
            elif node[0] == "call":
                for child in node[1]:
                    visit(child, bound_names)
            elif node[0] == "bind":
                new_bound = bound_names | {name for _, name in node[1]}
                visit(node[2], new_bound)
            elif node[0] == "let":
                visit(node[2], bound_names)
                new_bound = bound_names | {node[1][1]}
                visit(node[3], new_bound)
            elif node[0] == "match":
                visit(node[1], bound_names)
                shared_bound = bound_names | {name for _, name in node[2]}
                for arm in node[3]:
                    if arm[0] == "ctor":
                        arm_bound = shared_bound | {name for _, name in arm[1]}
                        for aux in arm[2]:
                            visit(aux, bound_names)
                        visit(arm[3], arm_bound)
                    elif arm[0] == "zero":
                        for aux in arm[1]:
                            visit(aux, bound_names)
                        visit(arm[2], shared_bound)
                    elif arm[0] == "succ":
                        arm_bound = shared_bound | {arm[1][1]}
                        for aux in arm[2]:
                            visit(aux, bound_names)
                        visit(arm[3], arm_bound)
        
        visit(replacement_root, set())
        return free
    
    repl_free = get_free_names()
    reached_var_scopes = {}
    visited = set()
    
    def dfs(node_idx, scope):
        scope_key = frozenset(scope.items())
        if (node_idx, scope_key) in visited:
            return
        visited.add((node_idx, scope_key))
        
        node = nodes[node_idx]
        
        if node[0] == "var":
            if node[1] == target and target not in scope:
                if node_idx not in reached_var_scopes:
                    reached_var_scopes[node_idx] = []
                reached_var_scopes[node_idx].append(scope)
        elif node[0] == "call":
            for child in node[1]:
                dfs(child, scope)
        elif node[0] == "bind":
            new_scope = scope.copy()
            for decl_id, name in node[1]:
                new_scope[name] = decl_id
            dfs(node[2], new_scope)
        elif node[0] == "let":
            dfs(node[2], scope)
            new_scope = scope.copy()
            new_scope[node[1][1]] = node[1][0]
            dfs(node[3], new_scope)
        elif node[0] == "match":
            dfs(node[1], scope)
            shared_scope = scope.copy()
            for decl_id, name in node[2]:
                shared_scope[name] = decl_id
            for arm in node[3]:
                if arm[0] == "ctor":
                    arm_scope = shared_scope.copy()
                    for decl_id, name in arm[1]:
                        arm_scope[name] = decl_id
                    for aux in arm[2]:
                        dfs(aux, scope)
                    dfs(arm[3], arm_scope)
                elif arm[0] == "zero":
                    for aux in arm[1]:
                        dfs(aux, scope)
                    dfs(arm[2], shared_scope)
                elif arm[0] == "succ":
                    arm_scope = shared_scope.copy()
                    arm_scope[arm[1][1]] = arm[1][0]
                    for aux in arm[2]:
                        dfs(aux, scope)
                    dfs(arm[3], arm_scope)
    
    dfs(expr_root, {})
    
    capturing_ids = set()
    for var_idx, scopes in reached_var_scopes.items():
        for scope in scopes:
            for name, decl_id in scope.items():
                if name in repl_free:
                    capturing_ids.add(decl_id)
    
    return sorted(list(capturing_ids))