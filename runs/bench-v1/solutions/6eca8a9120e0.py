def capture_binders(nodes, expr_root, target, replacement_root):
    def find_free_vars(node_idx, bound_names=None):
        if bound_names is None:
            bound_names = set()
        
        term = nodes[node_idx]
        term_type = term[0]
        free = set()
        
        if term_type == "var":
            name = term[1]
            if name not in bound_names:
                free.add(name)
        elif term_type == "call":
            for child_idx in term[1]:
                free.update(find_free_vars(child_idx, bound_names))
        elif term_type == "bind":
            declarations, body = term[1], term[2]
            new_bound = bound_names | {decl[1] for decl in declarations}
            free.update(find_free_vars(body, new_bound))
        elif term_type == "let":
            declaration, value, body = term[1], term[2], term[3]
            free.update(find_free_vars(value, bound_names))
            new_bound = bound_names | {declaration[1]}
            free.update(find_free_vars(body, new_bound))
        elif term_type == "match":
            scrutinee, shared, arms = term[1], term[2], term[3]
            free.update(find_free_vars(scrutinee, bound_names))
            shared_names = {decl[1] for decl in shared}
            new_bound_shared = bound_names | shared_names
            
            for arm in arms:
                if arm[0] == "ctor":
                    field_names = {decl[1] for decl in arm[1]}
                    arm_bound = new_bound_shared | field_names
                    free.update(find_free_vars(arm[3], arm_bound))
                elif arm[0] == "zero":
                    free.update(find_free_vars(arm[2], new_bound_shared))
                elif arm[0] == "succ":
                    pred_name = arm[1][1]
                    arm_bound = new_bound_shared | {pred_name}
                    free.update(find_free_vars(arm[3], arm_bound))
                
                for aux_idx in arm[2]:
                    free.update(find_free_vars(aux_idx, bound_names))
        
        return free
    
    replacement_free = find_free_vars(replacement_root)
    capturing_decls = set()
    visited = set()
    
    def dfs(node_idx, path_decls_tuple):
        state = (node_idx, path_decls_tuple)
        if state in visited:
            return
        visited.add(state)
        
        term = nodes[node_idx]
        term_type = term[0]
        
        if term_type == "var":
            if term[1] == target:
                shadowed = any(name == target for _, name in path_decls_tuple)
                if not shadowed:
                    for decl_id, decl_name in path_decls_tuple:
                        if decl_name in replacement_free:
                            capturing_decls.add(decl_id)
        
        elif term_type == "call":
            for child_idx in term[1]:
                dfs(child_idx, path_decls_tuple)
        
        elif term_type == "bind":
            declarations, body = term[1], term[2]
            new_path = path_decls_tuple + tuple(declarations)
            dfs(body, new_path)
        
        elif term_type == "let":
            declaration, value, body = term[1], term[2], term[3]
            dfs(value, path_decls_tuple)
            new_path = path_decls_tuple + (declaration,)
            dfs(body, new_path)
        
        elif term_type == "match":
            scrutinee, shared, arms = term[1], term[2], term[3]
            dfs(scrutinee, path_decls_tuple)
            
            shared_path = path_decls_tuple + tuple(shared)
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body = arm[1], arm[2], arm[3]
                    arm_path = shared_path + tuple(fields)
                    dfs(body, arm_path)
                elif arm[0] == "zero":
                    auxiliaries, body = arm[1], arm[2]
                    dfs(body, shared_path)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body = arm[1], arm[2], arm[3]
                    arm_path = shared_path + (predecessor,)
                    dfs(body, arm_path)
                
                for aux_idx in auxiliaries:
                    dfs(aux_idx, path_decls_tuple)
    
    dfs(expr_root, ())
    
    return sorted(list(capturing_decls))