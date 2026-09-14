def capture_binders(nodes, expr_root, target, replacement_root):
    def find_free_vars(node_idx, bound_names=None):
        if bound_names is None:
            bound_names = set()
        if node_idx is None:
            return set()
        
        node = nodes[node_idx]
        free = set()
        
        if node[0] == "var":
            if node[1] not in bound_names:
                free.add(node[1])
        elif node[0] == "call":
            for child_idx in node[1]:
                free.update(find_free_vars(child_idx, bound_names))
        elif node[0] == "bind":
            declarations, body_idx = node[1], node[2]
            new_bound = bound_names | {name for _, name in declarations}
            free.update(find_free_vars(body_idx, new_bound))
        elif node[0] == "let":
            decl, value_idx, body_idx = node[1], node[2], node[3]
            free.update(find_free_vars(value_idx, bound_names))
            new_bound = bound_names | {decl[1]}
            free.update(find_free_vars(body_idx, new_bound))
        elif node[0] == "match":
            scrutinee_idx, shared_decls, arms = node[1], node[2], node[3]
            free.update(find_free_vars(scrutinee_idx, bound_names))
            
            shared_names = set()
            if shared_decls is not None:
                shared_names = {name for _, name in shared_decls}
            
            for arm in arms:
                arm_bound = bound_names | shared_names
                
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    for _, name in fields:
                        arm_bound = arm_bound | {name}
                    for aux_idx in auxiliaries:
                        free.update(find_free_vars(aux_idx, bound_names))
                    free.update(find_free_vars(body_idx, arm_bound))
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        free.update(find_free_vars(aux_idx, bound_names))
                    free.update(find_free_vars(body_idx, arm_bound))
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_bound = arm_bound | {predecessor[1]}
                    for aux_idx in auxiliaries:
                        free.update(find_free_vars(aux_idx, bound_names))
                    free.update(find_free_vars(body_idx, arm_bound))
        
        return free
    
    replacement_free = find_free_vars(replacement_root)
    capturing_ids = set()
    
    def traverse_expr(node_idx, bound_decls):
        if node_idx is None:
            return
        
        node = nodes[node_idx]
        
        if node[0] == "var":
            if node[1] == target:
                for decl_id, decl_name in bound_decls:
                    if decl_name in replacement_free:
                        capturing_ids.add(decl_id)
        elif node[0] == "call":
            for child_idx in node[1]:
                traverse_expr(child_idx, bound_decls)
        elif node[0] == "bind":
            declarations, body_idx = node[1], node[2]
            traverse_expr(body_idx, bound_decls + declarations)
        elif node[0] == "let":
            decl, value_idx, body_idx = node[1], node[2], node[3]
            traverse_expr(value_idx, bound_decls)
            traverse_expr(body_idx, bound_decls + [decl])
        elif node[0] == "match":
            scrutinee_idx, shared_decls, arms = node[1], node[2], node[3]
            traverse_expr(scrutinee_idx, bound_decls)
            
            for arm in arms:
                arm_bound = list(bound_decls)
                if shared_decls is not None:
                    arm_bound.extend(shared_decls)
                
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_bound.extend(fields)
                    for aux_idx in auxiliaries:
                        traverse_expr(aux_idx, bound_decls)
                    traverse_expr(body_idx, arm_bound)
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        traverse_expr(aux_idx, bound_decls)
                    traverse_expr(body_idx, arm_bound)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_bound.append(predecessor)
                    for aux_idx in auxiliaries:
                        traverse_expr(aux_idx, bound_decls)
                    traverse_expr(body_idx, arm_bound)
    
    traverse_expr(expr_root, [])
    return sorted(list(capturing_ids))