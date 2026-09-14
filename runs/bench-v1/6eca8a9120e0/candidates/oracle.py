def capture_binders(nodes, expr_root, target, replacement_root):
    occurrences = []
    
    def traverse_expr(node_idx, path_bindings):
        term = nodes[node_idx]
        typ = term[0]
        
        if typ == "var":
            if term[1] == target:
                occurrences.append((node_idx, path_bindings.copy()))
        elif typ == "call":
            for child_idx in term[1]:
                traverse_expr(child_idx, path_bindings)
        elif typ == "bind":
            decls, body_idx = term[1], term[2]
            new_path = path_bindings.copy()
            for decl in decls:
                new_path.append(decl)
            traverse_expr(body_idx, new_path)
        elif typ == "let":
            decl, value_idx, body_idx = term[1], term[2], term[3]
            traverse_expr(value_idx, path_bindings)
            new_path = path_bindings.copy()
            new_path.append(decl)
            traverse_expr(body_idx, new_path)
        elif typ == "match":
            scrutinee_idx, shared_decls, arms = term[1], term[2], term[3]
            traverse_expr(scrutinee_idx, path_bindings)
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_path = path_bindings.copy()
                    for f in fields:
                        arm_path.append(f)
                    for s in shared_decls:
                        arm_path.append(s)
                    traverse_expr(body_idx, arm_path)
                    for aux_idx in auxiliaries:
                        traverse_expr(aux_idx, path_bindings)
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    arm_path = path_bindings.copy()
                    for s in shared_decls:
                        arm_path.append(s)
                    traverse_expr(body_idx, arm_path)
                    for aux_idx in auxiliaries:
                        traverse_expr(aux_idx, path_bindings)
                elif arm[0] == "succ":
                    pred_decl, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_path = path_bindings.copy()
                    arm_path.append(pred_decl)
                    for s in shared_decls:
                        arm_path.append(s)
                    traverse_expr(body_idx, arm_path)
                    for aux_idx in auxiliaries:
                        traverse_expr(aux_idx, path_bindings)
    
    traverse_expr(expr_root, [])
    
    replaced = []
    for occ_idx, path_bindings in occurrences:
        shadowed = any(decl_name == target for decl_id, decl_name in path_bindings)
        if not shadowed:
            replaced.append((occ_idx, path_bindings))
    
    free_vars = set()
    
    def traverse_replacement(node_idx, bound_vars):
        term = nodes[node_idx]
        typ = term[0]
        
        if typ == "var":
            if term[1] not in bound_vars:
                free_vars.add(term[1])
        elif typ == "call":
            for child_idx in term[1]:
                traverse_replacement(child_idx, bound_vars)
        elif typ == "bind":
            decls, body_idx = term[1], term[2]
            new_bound = bound_vars.copy()
            for decl_id, decl_name in decls:
                new_bound.add(decl_name)
            traverse_replacement(body_idx, new_bound)
        elif typ == "let":
            decl, value_idx, body_idx = term[1], term[2], term[3]
            traverse_replacement(value_idx, bound_vars)
            new_bound = bound_vars.copy()
            new_bound.add(decl[1])
            traverse_replacement(body_idx, new_bound)
        elif typ == "match":
            scrutinee_idx, shared_decls, arms = term[1], term[2], term[3]
            traverse_replacement(scrutinee_idx, bound_vars)
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_bound = bound_vars.copy()
                    for decl_id, decl_name in fields:
                        arm_bound.add(decl_name)
                    for decl_id, decl_name in shared_decls:
                        arm_bound.add(decl_name)
                    traverse_replacement(body_idx, arm_bound)
                    for aux_idx in auxiliaries:
                        traverse_replacement(aux_idx, bound_vars)
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    arm_bound = bound_vars.copy()
                    for decl_id, decl_name in shared_decls:
                        arm_bound.add(decl_name)
                    traverse_replacement(body_idx, arm_bound)
                    for aux_idx in auxiliaries:
                        traverse_replacement(aux_idx, bound_vars)
                elif arm[0] == "succ":
                    pred_decl, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    arm_bound = bound_vars.copy()
                    arm_bound.add(pred_decl[1])
                    for decl_id, decl_name in shared_decls:
                        arm_bound.add(decl_name)
                    traverse_replacement(body_idx, arm_bound)
                    for aux_idx in auxiliaries:
                        traverse_replacement(aux_idx, bound_vars)
    
    traverse_replacement(replacement_root, set())
    
    capturing = set()
    for occ_idx, path_bindings in replaced:
        for decl_id, decl_name in path_bindings:
            if decl_name in free_vars:
                capturing.add(decl_id)
    
    return sorted(list(capturing))