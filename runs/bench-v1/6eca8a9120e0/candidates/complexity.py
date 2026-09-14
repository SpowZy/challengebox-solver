def capture_binders(nodes, expr_root, target, replacement_root):
    def get_free_vars(node_idx, bound_set=None):
        if bound_set is None:
            bound_set = set()
        
        term = nodes[node_idx]
        typ = term[0]
        free = set()
        
        if typ == "var":
            name = term[1]
            if name not in bound_set:
                free.add(name)
        elif typ == "call":
            for child_idx in term[1]:
                free |= get_free_vars(child_idx, bound_set)
        elif typ == "bind":
            declarations, body = term[1], term[2]
            new_bound = bound_set | {name for _, name in declarations}
            free = get_free_vars(body, new_bound)
        elif typ == "let":
            declaration, value, body = term[1], term[2], term[3]
            _, decl_name = declaration
            free |= get_free_vars(value, bound_set)
            new_bound = bound_set | {decl_name}
            free |= get_free_vars(body, new_bound)
        elif typ == "match":
            scrutinee, shared, arms = term[1], term[2], term[3]
            free |= get_free_vars(scrutinee, bound_set)
            
            shared_decls_names = get_all_decl_names(shared)
            shared_free = get_free_vars(shared, bound_set)
            free |= shared_free
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body = arm[1], arm[2], arm[3]
                    fields_names = {name for _, name in fields}
                    body_bound = bound_set | shared_decls_names | fields_names
                    free |= get_free_vars(body, body_bound)
                    for aux_idx in auxiliaries:
                        free |= get_free_vars(aux_idx, bound_set)
                elif arm[0] == "zero":
                    auxiliaries, body = arm[1], arm[2]
                    body_bound = bound_set | shared_decls_names
                    free |= get_free_vars(body, body_bound)
                    for aux_idx in auxiliaries:
                        free |= get_free_vars(aux_idx, bound_set)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body = arm[1], arm[2], arm[3]
                    _, pred_name = predecessor
                    body_bound = bound_set | shared_decls_names | {pred_name}
                    free |= get_free_vars(body, body_bound)
                    for aux_idx in auxiliaries:
                        free |= get_free_vars(aux_idx, bound_set)
        
        return free
    
    def get_all_decl_names(node_idx):
        term = nodes[node_idx]
        typ = term[0]
        names = set()
        
        if typ == "var":
            pass
        elif typ == "call":
            for child_idx in term[1]:
                names |= get_all_decl_names(child_idx)
        elif typ == "bind":
            declarations, body = term[1], term[2]
            names = {name for _, name in declarations}
            names |= get_all_decl_names(body)
        elif typ == "let":
            declaration, value, body = term[1], term[2], term[3]
            _, decl_name = declaration
            names = {decl_name}
            names |= get_all_decl_names(value)
            names |= get_all_decl_names(body)
        elif typ == "match":
            scrutinee, shared, arms = term[1], term[2], term[3]
            names |= get_all_decl_names(scrutinee)
            names |= get_all_decl_names(shared)
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body = arm[1], arm[2], arm[3]
                    names |= {name for _, name in fields}
                    for aux_idx in auxiliaries:
                        names |= get_all_decl_names(aux_idx)
                    names |= get_all_decl_names(body)
                elif arm[0] == "zero":
                    auxiliaries, body = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        names |= get_all_decl_names(aux_idx)
                    names |= get_all_decl_names(body)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body = arm[1], arm[2], arm[3]
                    _, pred_name = predecessor
                    names.add(pred_name)
                    for aux_idx in auxiliaries:
                        names |= get_all_decl_names(aux_idx)
                    names |= get_all_decl_names(body)
        
        return names
    
    def get_all_decls(node_idx):
        term = nodes[node_idx]
        typ = term[0]
        decls = []
        
        if typ == "var":
            pass
        elif typ == "call":
            for child_idx in term[1]:
                decls.extend(get_all_decls(child_idx))
        elif typ == "bind":
            declarations, body = term[1], term[2]
            decls = list(declarations) + get_all_decls(body)
        elif typ == "let":
            declaration, value, body = term[1], term[2], term[3]
            decls = [declaration] + get_all_decls(value) + get_all_decls(body)
        elif typ == "match":
            scrutinee, shared, arms = term[1], term[2], term[3]
            decls.extend(get_all_decls(scrutinee))
            decls.extend(get_all_decls(shared))
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body = arm[1], arm[2], arm[3]
                    decls.extend(list(fields))
                    for aux_idx in auxiliaries:
                        decls.extend(get_all_decls(aux_idx))
                    decls.extend(get_all_decls(body))
                elif arm[0] == "zero":
                    auxiliaries, body = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        decls.extend(get_all_decls(aux_idx))
                    decls.extend(get_all_decls(body))
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body = arm[1], arm[2], arm[3]
                    decls.append(predecessor)
                    for aux_idx in auxiliaries:
                        decls.extend(get_all_decls(aux_idx))
                    decls.extend(get_all_decls(body))
        
        return decls
    
    repl_free = get_free_vars(replacement_root)
    capturing = set()
    
    def traverse(node_idx, active_decls, shadowing_target):
        term = nodes[node_idx]
        typ = term[0]
        
        if typ == "var":
            if term[1] == target and not shadowing_target:
                for decl_id, decl_name in active_decls:
                    if decl_name in repl_free:
                        capturing.add(decl_id)
        elif typ == "call":
            for child_idx in term[1]:
                traverse(child_idx, active_decls, shadowing_target)
        elif typ == "bind":
            declarations, body = term[1], term[2]
            new_active = active_decls + list(declarations)
            new_shadowing = shadowing_target or any(name == target for _, name in declarations)
            traverse(body, new_active, new_shadowing)
        elif typ == "let":
            declaration, value, body = term[1], term[2], term[3]
            traverse(value, active_decls, shadowing_target)
            decl_id, decl_name = declaration
            new_shadowing = decl_name == target
            new_active = active_decls + [declaration]
            traverse(body, new_active, new_shadowing or shadowing_target)
        elif typ == "match":
            scrutinee, shared, arms = term[1], term[2], term[3]
            traverse(scrutinee, active_decls, shadowing_target)
            
            shared_decls = get_all_decls(shared)
            shared_has_target = any(name == target for _, name in shared_decls)
            traverse(shared, active_decls, shadowing_target)
            
            arm_body_active = active_decls + shared_decls
            arm_body_shadowing = shadowing_target or shared_has_target
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body = arm[1], arm[2], arm[3]
                    fields_decls = list(fields)
                    fields_has_target = any(name == target for _, name in fields_decls)
                    for aux_idx in auxiliaries:
                        traverse(aux_idx, active_decls, shadowing_target)
                    body_active = arm_body_active + fields_decls
                    body_shadowing = arm_body_shadowing or fields_has_target
                    traverse(body, body_active, body_shadowing)
                elif arm[0] == "zero":
                    auxiliaries, body = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        traverse(aux_idx, active_decls, shadowing_target)
                    traverse(body, arm_body_active, arm_body_shadowing)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body = arm[1], arm[2], arm[3]
                    pred_name = predecessor[1]
                    pred_has_target = pred_name == target
                    for aux_idx in auxiliaries:
                        traverse(aux_idx, active_decls, shadowing_target)
                    body_active = arm_body_active + [predecessor]
                    body_shadowing = arm_body_shadowing or pred_has_target
                    traverse(body, body_active, body_shadowing)
    
    traverse(expr_root, [], False)
    return sorted(list(capturing))