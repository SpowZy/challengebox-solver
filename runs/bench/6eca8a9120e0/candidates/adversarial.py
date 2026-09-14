def capture_binders(nodes, expr_root, target, replacement_root):
    def get_replacement_free_vars(node_idx, bound_names=None):
        if bound_names is None:
            bound_names = set()
        if node_idx is None:
            return set()
        
        node = nodes[node_idx]
        
        if node[0] == "var":
            return set() if node[1] in bound_names else {node[1]}
        elif node[0] == "call":
            free = set()
            for child_idx in node[1]:
                free.update(get_replacement_free_vars(child_idx, bound_names))
            return free
        elif node[0] == "bind":
            declarations, body_idx = node[1], node[2]
            new_bound = bound_names | {decl[1] for decl in declarations}
            return get_replacement_free_vars(body_idx, new_bound)
        elif node[0] == "let":
            decl, value_idx, body_idx = node[1], node[2], node[3]
            free = get_replacement_free_vars(value_idx, bound_names)
            free.update(get_replacement_free_vars(body_idx, bound_names | {decl[1]}))
            return free
        elif node[0] == "match":
            scrutinee_idx, shared_idx, arms = node[1], node[2], node[3]
            free = get_replacement_free_vars(scrutinee_idx, bound_names)
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_bound = bound_names | {f[1] for f in fields}
                    free.update(get_replacement_free_vars(shared_idx, arm_bound))
                    free.update(get_replacement_free_vars(body_idx, arm_bound))
                    for aux_idx in auxiliaries:
                        free.update(get_replacement_free_vars(aux_idx, bound_names))
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    free.update(get_replacement_free_vars(shared_idx, bound_names))
                    free.update(get_replacement_free_vars(body_idx, bound_names))
                    for aux_idx in auxiliaries:
                        free.update(get_replacement_free_vars(aux_idx, bound_names))
                elif arm[0] == "succ":
                    pred, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_bound = bound_names | {pred[1]}
                    free.update(get_replacement_free_vars(shared_idx, arm_bound))
                    free.update(get_replacement_free_vars(body_idx, arm_bound))
                    for aux_idx in auxiliaries:
                        free.update(get_replacement_free_vars(aux_idx, bound_names))
            return free
        return set()
    
    replacement_free_vars = get_replacement_free_vars(replacement_root)
    capturing_decls = set()
    
    def traverse(node_idx, bound_decls, target_shadowed):
        if node_idx is None:
            return
        node = nodes[node_idx]
        
        if node[0] == "var":
            if node[1] == target and not target_shadowed:
                for decl_id, decl_name in bound_decls:
                    if decl_name in replacement_free_vars:
                        capturing_decls.add(decl_id)
        elif node[0] == "call":
            for child_idx in node[1]:
                traverse(child_idx, bound_decls, target_shadowed)
        elif node[0] == "bind":
            declarations, body_idx = node[1], node[2]
            new_shadowed = target_shadowed or any(d[1] == target for d in declarations)
            traverse(body_idx, bound_decls + declarations, new_shadowed)
        elif node[0] == "let":
            decl, value_idx, body_idx = node[1], node[2], node[3]
            traverse(value_idx, bound_decls, target_shadowed)
            new_shadowed = target_shadowed or decl[1] == target
            traverse(body_idx, bound_decls + [decl], new_shadowed)
        elif node[0] == "match":
            scrutinee_idx, shared_idx, arms = node[1], node[2], node[3]
            traverse(scrutinee_idx, bound_decls, target_shadowed)
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    new_shadowed = target_shadowed or any(f[1] == target for f in fields)
                    arm_bound = bound_decls + fields
                    traverse(shared_idx, arm_bound, new_shadowed)
                    traverse(body_idx, arm_bound, new_shadowed)
                    for aux_idx in auxiliaries:
                        traverse(aux_idx, bound_decls, target_shadowed)
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    traverse(shared_idx, bound_decls, target_shadowed)
                    traverse(body_idx, bound_decls, target_shadowed)
                    for aux_idx in auxiliaries:
                        traverse(aux_idx, bound_decls, target_shadowed)
                elif arm[0] == "succ":
                    pred, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    new_shadowed = target_shadowed or pred[1] == target
                    arm_bound = bound_decls + [pred]
                    traverse(shared_idx, arm_bound, new_shadowed)
                    traverse(body_idx, arm_bound, new_shadowed)
                    for aux_idx in auxiliaries:
                        traverse(aux_idx, bound_decls, target_shadowed)
    
    traverse(expr_root, [], False)
    return sorted(list(capturing_decls))