def capture_binders(nodes, expr_root, target, replacement_root):
    # Get free variables in replacement tree
    def free_vars():
        def dfs(node_idx, bound_names):
            node = nodes[node_idx]
            free = set()
            
            if node[0] == "var":
                if node[1] not in bound_names:
                    free.add(node[1])
            elif node[0] == "call":
                for child_idx in node[1]:
                    free.update(dfs(child_idx, bound_names))
            elif node[0] == "bind":
                decls, body_idx = node[1], node[2]
                new_bound = bound_names | {name for _, name in decls}
                free.update(dfs(body_idx, new_bound))
            elif node[0] == "let":
                decl, value_idx, body_idx = node[1], node[2], node[3]
                _, name = decl
                free.update(dfs(value_idx, bound_names))
                new_bound = bound_names | {name}
                free.update(dfs(body_idx, new_bound))
            elif node[0] == "match":
                scrutinee_idx, shared_idx, arms = node[1], node[2], node[3]
                free.update(dfs(scrutinee_idx, bound_names))
                free.update(dfs(shared_idx, bound_names))
                
                shared_bound = bound_names
                shared_node = nodes[shared_idx]
                if shared_node[0] == "bind":
                    shared_bound = bound_names | {name for _, name in shared_node[1]}
                
                for arm in arms:
                    if arm[0] == "ctor":
                        fields, auxi_idxs, body_idx = arm[1], arm[2], arm[3]
                        field_names = {name for _, name in fields}
                        for aux_idx in auxi_idxs:
                            free.update(dfs(aux_idx, bound_names))
                        arm_bound = shared_bound | field_names
                        free.update(dfs(body_idx, arm_bound))
                    elif arm[0] == "zero":
                        auxi_idxs, body_idx = arm[1], arm[2]
                        for aux_idx in auxi_idxs:
                            free.update(dfs(aux_idx, bound_names))
                        free.update(dfs(body_idx, shared_bound))
                    elif arm[0] == "succ":
                        pred, auxi_idxs, body_idx = arm[1], arm[2], arm[3]
                        _, pred_name = pred
                        for aux_idx in auxi_idxs:
                            free.update(dfs(aux_idx, bound_names))
                        arm_bound = shared_bound | {pred_name}
                        free.update(dfs(body_idx, arm_bound))
            
            return free
        
        return dfs(replacement_root, frozenset())
    
    repl_free = free_vars()
    
    # Find capturing declarations
    capturing = set()
    
    def find_captures(node_idx, scope_stack):
        node = nodes[node_idx]
        
        if node[0] == "var":
            if node[1] == target:
                for free_name in repl_free:
                    if free_name in scope_stack and scope_stack[free_name]:
                        capturing.add(scope_stack[free_name][-1])
        elif node[0] == "call":
            for child_idx in node[1]:
                find_captures(child_idx, scope_stack)
        elif node[0] == "bind":
            decls, body_idx = node[1], node[2]
            new_scope = dict(scope_stack)
            for decl_id, name in decls:
                if name not in new_scope:
                    new_scope[name] = []
                else:
                    new_scope[name] = list(new_scope[name])
                new_scope[name].append(decl_id)
            find_captures(body_idx, new_scope)
        elif node[0] == "let":
            decl, value_idx, body_idx = node[1], node[2], node[3]
            decl_id, name = decl
            find_captures(value_idx, scope_stack)
            new_scope = dict(scope_stack)
            if name not in new_scope:
                new_scope[name] = []
            else:
                new_scope[name] = list(new_scope[name])
            new_scope[name].append(decl_id)
            find_captures(body_idx, new_scope)
        elif node[0] == "match":
            scrutinee_idx, shared_idx, arms = node[1], node[2], node[3]
            find_captures(scrutinee_idx, scope_stack)
            
            shared_scope = dict(scope_stack)
            shared_node = nodes[shared_idx]
            if shared_node[0] == "bind":
                for decl_id, name in shared_node[1]:
                    if name not in shared_scope:
                        shared_scope[name] = []
                    else:
                        shared_scope[name] = list(shared_scope[name])
                    shared_scope[name].append(decl_id)
            
            find_captures(shared_idx, scope_stack)
            
            for arm in arms:
                arm_scope = dict(shared_scope)
                
                if arm[0] == "ctor":
                    fields, auxi_idxs, body_idx = arm[1], arm[2], arm[3]
                    for decl_id, name in fields:
                        if name not in arm_scope:
                            arm_scope[name] = []
                        else:
                            arm_scope[name] = list(arm_scope[name])
                        arm_scope[name].append(decl_id)
                    for aux_idx in auxi_idxs:
                        find_captures(aux_idx, scope_stack)
                    find_captures(body_idx, arm_scope)
                elif arm[0] == "zero":
                    auxi_idxs, body_idx = arm[1], arm[2]
                    for aux_idx in auxi_idxs:
                        find_captures(aux_idx, scope_stack)
                    find_captures(body_idx, arm_scope)
                elif arm[0] == "succ":
                    pred, auxi_idxs, body_idx = arm[1], arm[2], arm[3]
                    pred_id, pred_name = pred
                    if pred_name not in arm_scope:
                        arm_scope[pred_name] = []
                    else:
                        arm_scope[pred_name] = list(arm_scope[pred_name])
                    arm_scope[pred_name].append(pred_id)
                    for aux_idx in auxi_idxs:
                        find_captures(aux_idx, scope_stack)
                    find_captures(body_idx, arm_scope)
    
    find_captures(expr_root, {})
    
    return sorted(list(capturing))