def capture_binders(nodes, expr_root, target, replacement_root):
    def find_free_vars(node_idx):
        if node_idx is None or node_idx < 0 or node_idx >= len(nodes):
            return set()
        
        node = nodes[node_idx]
        
        if node[0] == "var":
            return {node[1]}
        elif node[0] == "call":
            free = set()
            for child_idx in node[1]:
                free.update(find_free_vars(child_idx))
            return free
        elif node[0] == "bind":
            declarations, body_idx = node[1], node[2]
            bound_names = {name for _, name in declarations}
            body_free = find_free_vars(body_idx)
            return body_free - bound_names
        elif node[0] == "let":
            declaration, value_idx, body_idx = node[1], node[2], node[3]
            decl_name = declaration[1]
            value_free = find_free_vars(value_idx)
            body_free = find_free_vars(body_idx)
            return (value_free | body_free) - {decl_name}
        elif node[0] == "match":
            scrutinee_idx, shared_idx, arms = node[1], node[2], node[3]
            free = find_free_vars(scrutinee_idx)
            
            shared_names = set()
            if shared_idx is not None and isinstance(shared_idx, int) and 0 <= shared_idx < len(nodes):
                shared_node = nodes[shared_idx]
                if shared_node[0] == "bind":
                    shared_names = {name for _, name in shared_node[1]}
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    field_names = {name for _, name in fields}
                    arm_free = set()
                    for aux_idx in auxiliaries:
                        arm_free.update(find_free_vars(aux_idx))
                    body_free = find_free_vars(body_idx)
                    free.update(arm_free | (body_free - field_names - shared_names))
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    arm_free = set()
                    for aux_idx in auxiliaries:
                        arm_free.update(find_free_vars(aux_idx))
                    body_free = find_free_vars(body_idx)
                    free.update(arm_free | (body_free - shared_names))
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    pred_name = predecessor[1]
                    arm_free = set()
                    for aux_idx in auxiliaries:
                        arm_free.update(find_free_vars(aux_idx))
                    body_free = find_free_vars(body_idx)
                    free.update(arm_free | (body_free - {pred_name} - shared_names))
            
            return free
        else:
            return set()
    
    replacement_free = find_free_vars(replacement_root)
    capturing_decls = set()
    
    def dfs_find_targets(node_idx, scope_stack):
        if node_idx is None or node_idx < 0 or node_idx >= len(nodes):
            return
        
        node = nodes[node_idx]
        
        if node[0] == "var":
            if node[1] == target:
                for decl_id, name in scope_stack:
                    if name in replacement_free:
                        capturing_decls.add(decl_id)
        elif node[0] == "call":
            for child_idx in node[1]:
                dfs_find_targets(child_idx, scope_stack)
        elif node[0] == "bind":
            declarations, body_idx = node[1], node[2]
            new_scope = scope_stack + list(declarations)
            dfs_find_targets(body_idx, new_scope)
        elif node[0] == "let":
            declaration, value_idx, body_idx = node[1], node[2], node[3]
            dfs_find_targets(value_idx, scope_stack)
            new_scope = scope_stack + [declaration]
            dfs_find_targets(body_idx, new_scope)
        elif node[0] == "match":
            scrutinee_idx, shared_idx, arms = node[1], node[2], node[3]
            dfs_find_targets(scrutinee_idx, scope_stack)
            
            shared_decls = []
            if shared_idx is not None and isinstance(shared_idx, int) and 0 <= shared_idx < len(nodes):
                shared_node = nodes[shared_idx]
                if shared_node[0] == "bind":
                    shared_decls = list(shared_node[1])
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    for aux_idx in auxiliaries:
                        dfs_find_targets(aux_idx, scope_stack)
                    arm_scope = scope_stack + shared_decls + list(fields)
                    dfs_find_targets(body_idx, arm_scope)
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        dfs_find_targets(aux_idx, scope_stack)
                    arm_scope = scope_stack + shared_decls
                    dfs_find_targets(body_idx, arm_scope)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    for aux_idx in auxiliaries:
                        dfs_find_targets(aux_idx, scope_stack)
                    arm_scope = scope_stack + shared_decls + [predecessor]
                    dfs_find_targets(body_idx, arm_scope)
    
    dfs_find_targets(expr_root, [])
    return sorted(list(capturing_decls))