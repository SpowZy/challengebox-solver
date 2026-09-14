def capture_binders(nodes, expr_root, target, replacement_root):
    def get_free_names(node_idx, bound_names):
        if not isinstance(node_idx, int) or node_idx >= len(nodes) or node_idx < 0:
            return set()
        
        term = nodes[node_idx]
        typ = term[0]
        
        if typ == "var":
            name = term[1]
            return {name} if name not in bound_names else set()
        
        elif typ == "call":
            free = set()
            for child_idx in term[1]:
                free |= get_free_names(child_idx, bound_names)
            return free
        
        elif typ == "bind":
            declarations, body_idx = term[1], term[2]
            new_bound = bound_names | {name for _, name in declarations}
            return get_free_names(body_idx, new_bound)
        
        elif typ == "let":
            declaration, value_idx, body_idx = term[1], term[2], term[3]
            _, decl_name = declaration
            free = get_free_names(value_idx, bound_names)
            new_bound = bound_names | {decl_name}
            free |= get_free_names(body_idx, new_bound)
            return free
        
        elif typ == "match":
            scrutinee_idx, shared, arms = term[1], term[2], term[3]
            free = get_free_names(scrutinee_idx, bound_names)
            
            shared_names = {name for _, name in shared} if shared else set()
            
            for arm in arms:
                arm_bound = bound_names | shared_names
                
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_bound |= {name for _, name in fields}
                    for aux_idx in auxiliaries:
                        free |= get_free_names(aux_idx, bound_names)
                    free |= get_free_names(body_idx, arm_bound)
                
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        free |= get_free_names(aux_idx, bound_names)
                    free |= get_free_names(body_idx, arm_bound)
                
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    _, pred_name = predecessor
                    arm_bound |= {pred_name}
                    for aux_idx in auxiliaries:
                        free |= get_free_names(aux_idx, bound_names)
                    free |= get_free_names(body_idx, arm_bound)
            
            return free
        
        return set()
    
    replacement_free = get_free_names(replacement_root, set())
    capturing = set()
    
    def dfs(node_idx, bound_names, scoped_decls):
        if not isinstance(node_idx, int) or node_idx >= len(nodes) or node_idx < 0:
            return
        
        term = nodes[node_idx]
        typ = term[0]
        
        if typ == "var":
            name = term[1]
            if name == target and name not in bound_names:
                for decl_id, decl_name in scoped_decls:
                    if decl_name in replacement_free:
                        capturing.add(decl_id)
        
        elif typ == "call":
            for child_idx in term[1]:
                dfs(child_idx, bound_names, scoped_decls)
        
        elif typ == "bind":
            declarations, body_idx = term[1], term[2]
            new_bound = bound_names | {name for _, name in declarations}
            new_decls = scoped_decls + declarations
            dfs(body_idx, new_bound, new_decls)
        
        elif typ == "let":
            declaration, value_idx, body_idx = term[1], term[2], term[3]
            decl_id, decl_name = declaration
            dfs(value_idx, bound_names, scoped_decls)
            new_bound = bound_names | {decl_name}
            new_decls = scoped_decls + [declaration]
            dfs(body_idx, new_bound, new_decls)
        
        elif typ == "match":
            scrutinee_idx, shared, arms = term[1], term[2], term[3]
            dfs(scrutinee_idx, bound_names, scoped_decls)
            
            shared_names = {name for _, name in shared} if shared else set()
            new_scoped_decls = scoped_decls + (shared if shared else [])
            
            for arm in arms:
                arm_bound = bound_names | shared_names
                arm_decls = new_scoped_decls
                
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_bound |= {name for _, name in fields}
                    arm_decls = arm_decls + fields
                    for aux_idx in auxiliaries:
                        dfs(aux_idx, bound_names, scoped_decls)
                    dfs(body_idx, arm_bound, arm_decls)
                
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        dfs(aux_idx, bound_names, scoped_decls)
                    dfs(body_idx, arm_bound, arm_decls)
                
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    _, pred_name = predecessor
                    arm_bound |= {pred_name}
                    arm_decls = arm_decls + [predecessor]
                    for aux_idx in auxiliaries:
                        dfs(aux_idx, bound_names, scoped_decls)
                    dfs(body_idx, arm_bound, arm_decls)
    
    dfs(expr_root, set(), [])
    return sorted(list(capturing))