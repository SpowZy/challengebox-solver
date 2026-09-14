def capture_binders(nodes, expr_root, target, replacement_root):
    def get_free_vars(node_idx):
        term = nodes[node_idx]
        
        if term[0] == "var":
            return {term[1]}
        
        elif term[0] == "call":
            free = set()
            for child_idx in term[1]:
                free.update(get_free_vars(child_idx))
            return free
        
        elif term[0] == "bind":
            declarations, body = term[1], term[2]
            bound = {name for _, name in declarations}
            return get_free_vars(body) - bound
        
        elif term[0] == "let":
            declaration, value, body = term[1], term[2], term[3]
            _, name = declaration
            return get_free_vars(value) | (get_free_vars(body) - {name})
        
        elif term[0] == "match":
            scrutinee, shared, arms = term[1], term[2], term[3]
            free = get_free_vars(scrutinee)
            shared_names = {name for _, name in shared}
            
            for arm in arms:
                if arm[0] == "ctor":
                    _, fields, auxiliaries, body = arm
                    bindings = shared_names | {name for _, name in fields}
                elif arm[0] == "zero":
                    _, auxiliaries, body = arm
                    bindings = shared_names
                else:  # succ
                    _, predecessor, auxiliaries, body = arm
                    _, pred_name = predecessor
                    bindings = shared_names | {pred_name}
                
                for aux in auxiliaries:
                    free.update(get_free_vars(aux))
                
                free.update(get_free_vars(body) - bindings)
            
            return free
    
    free_vars_repl = get_free_vars(replacement_root)
    capturing_decls = set()
    
    def dfs(node_idx, scoped_bindings):
        term = nodes[node_idx]
        
        if term[0] == "var":
            if term[1] == target:
                shadowed = any(name == target for _, name in scoped_bindings)
                if not shadowed:
                    for decl_id, decl_name in scoped_bindings:
                        if decl_name in free_vars_repl:
                            capturing_decls.add(decl_id)
        
        elif term[0] == "call":
            for child_idx in term[1]:
                dfs(child_idx, scoped_bindings)
        
        elif term[0] == "bind":
            declarations, body = term[1], term[2]
            dfs(body, scoped_bindings + list(declarations))
        
        elif term[0] == "let":
            declaration, value, body = term[1], term[2], term[3]
            dfs(value, scoped_bindings)
            dfs(body, scoped_bindings + [declaration])
        
        elif term[0] == "match":
            scrutinee, shared, arms = term[1], term[2], term[3]
            dfs(scrutinee, scoped_bindings)
            
            shared_bindings = scoped_bindings + list(shared)
            
            for arm in arms:
                if arm[0] == "ctor":
                    _, fields, auxiliaries, body = arm
                    for aux_idx in auxiliaries:
                        dfs(aux_idx, scoped_bindings)
                    dfs(body, shared_bindings + list(fields))
                
                elif arm[0] == "zero":
                    _, auxiliaries, body = arm
                    for aux_idx in auxiliaries:
                        dfs(aux_idx, scoped_bindings)
                    dfs(body, shared_bindings)
                
                elif arm[0] == "succ":
                    _, predecessor, auxiliaries, body = arm
                    for aux_idx in auxiliaries:
                        dfs(aux_idx, scoped_bindings)
                    dfs(body, shared_bindings + [predecessor])
    
    dfs(expr_root, [])
    return sorted(list(capturing_decls))