def capture_binders(nodes, expr_root, target, replacement_root):
    # Find free variables in replacement tree
    def find_free_in_tree(root_idx):
        free = set()
        bound = set()
        
        def dfs(idx):
            term = nodes[idx]
            if term[0] == "var":
                if term[1] not in bound:
                    free.add(term[1])
            elif term[0] == "call":
                for child in term[1]:
                    dfs(child)
            elif term[0] == "bind":
                decls, body = term[1], term[2]
                old_bound = bound.copy()
                for _, name in decls:
                    bound.add(name)
                dfs(body)
                bound.clear()
                bound.update(old_bound)
            elif term[0] == "let":
                decl, value, body = term[1], term[2], term[3]
                _, name = decl
                dfs(value)
                old_bound = bound.copy()
                bound.add(name)
                dfs(body)
                bound.clear()
                bound.update(old_bound)
            elif term[0] == "match":
                scrutinee, shared_decls, arms = term[1], term[2], term[3]
                dfs(scrutinee)
                for arm in arms:
                    old_bound = bound.copy()
                    for _, name in shared_decls:
                        bound.add(name)
                    
                    if arm[0] == "ctor":
                        fields, auxiliaries, body = arm[1], arm[2], arm[3]
                        for _, name in fields:
                            bound.add(name)
                        for aux_idx in auxiliaries:
                            saved_bound = bound.copy()
                            bound.clear()
                            bound.update(old_bound)
                            dfs(aux_idx)
                            bound = saved_bound
                        dfs(body)
                    elif arm[0] == "zero":
                        auxiliaries, body = arm[1], arm[2]
                        for aux_idx in auxiliaries:
                            saved_bound = bound.copy()
                            bound.clear()
                            bound.update(old_bound)
                            dfs(aux_idx)
                            bound = saved_bound
                        dfs(body)
                    elif arm[0] == "succ":
                        predecessor, auxiliaries, body = arm[1], arm[2], arm[3]
                        _, pred_name = predecessor
                        bound.add(pred_name)
                        for aux_idx in auxiliaries:
                            saved_bound = bound.copy()
                            bound.clear()
                            bound.update(old_bound)
                            dfs(aux_idx)
                            bound = saved_bound
                        dfs(body)
                    
                    bound.clear()
                    bound.update(old_bound)
        
        dfs(root_idx)
        return free
    
    repl_free = find_free_in_tree(replacement_root)
    capturing = set()
    memo = {}
    
    def find_captures(idx, bound_scope_tuple):
        if (idx, bound_scope_tuple) in memo:
            return
        memo[(idx, bound_scope_tuple)] = True
        
        bound_scope = dict(bound_scope_tuple)
        term = nodes[idx]
        if term[0] == "var":
            if term[1] == target:
                for name, decl_id in bound_scope.items():
                    if name in repl_free:
                        capturing.add(decl_id)
        elif term[0] == "call":
            for child in term[1]:
                find_captures(child, bound_scope_tuple)
        elif term[0] == "bind":
            decls, body = term[1], term[2]
            new_scope = dict(bound_scope)
            for decl_id, name in decls:
                new_scope[name] = decl_id
            new_tuple = tuple(sorted(new_scope.items()))
            find_captures(body, new_tuple)
        elif term[0] == "let":
            decl, value, body = term[1], term[2], term[3]
            decl_id, name = decl
            find_captures(value, bound_scope_tuple)
            new_scope = dict(bound_scope)
            new_scope[name] = decl_id
            new_tuple = tuple(sorted(new_scope.items()))
            find_captures(body, new_tuple)
        elif term[0] == "match":
            scrutinee, shared_decls, arms = term[1], term[2], term[3]
            find_captures(scrutinee, bound_scope_tuple)
            
            shared_scope = dict(bound_scope)
            for decl_id, name in shared_decls:
                shared_scope[name] = decl_id
            shared_tuple = tuple(sorted(shared_scope.items()))
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body = arm[1], arm[2], arm[3]
                    for aux_idx in auxiliaries:
                        find_captures(aux_idx, bound_scope_tuple)
                    arm_scope = dict(shared_scope)
                    for decl_id, name in fields:
                        arm_scope[name] = decl_id
                    arm_tuple = tuple(sorted(arm_scope.items()))
                    find_captures(body, arm_tuple)
                elif arm[0] == "zero":
                    auxiliaries, body = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        find_captures(aux_idx, bound_scope_tuple)
                    find_captures(body, shared_tuple)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body = arm[1], arm[2], arm[3]
                    pred_id, pred_name = predecessor
                    for aux_idx in auxiliaries:
                        find_captures(aux_idx, bound_scope_tuple)
                    arm_scope = dict(shared_scope)
                    arm_scope[pred_name] = pred_id
                    arm_tuple = tuple(sorted(arm_scope.items()))
                    find_captures(body, arm_tuple)
    
    find_captures(expr_root, ())
    return sorted(list(capturing))