def capture_binders(nodes, expr_root, target, replacement_root):
    # Find free variables in replacement tree
    free_vars = set()
    
    def find_free_vars(idx, bound_names):
        node = nodes[idx]
        
        if node[0] == "var":
            if node[1] not in bound_names:
                free_vars.add(node[1])
        elif node[0] == "call":
            for child_idx in node[1]:
                find_free_vars(child_idx, bound_names)
        elif node[0] == "bind":
            declarations, body = node[1], node[2]
            new_bound = bound_names | {name for _, name in declarations}
            find_free_vars(body, new_bound)
        elif node[0] == "let":
            declaration, value, body = node[1], node[2], node[3]
            find_free_vars(value, bound_names)
            new_bound = bound_names | {declaration[1]}
            find_free_vars(body, new_bound)
        elif node[0] == "match":
            scrutinee, shared, arms = node[1], node[2], node[3]
            find_free_vars(scrutinee, bound_names)
            
            shared_names = {name for _, name in shared} if shared else set()
            new_bound_with_shared = bound_names | shared_names
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body = arm[1], arm[2], arm[3]
                    for aux_idx in auxiliaries:
                        find_free_vars(aux_idx, bound_names)
                    new_bound = new_bound_with_shared | {name for _, name in fields}
                    find_free_vars(body, new_bound)
                elif arm[0] == "zero":
                    auxiliaries, body = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        find_free_vars(aux_idx, bound_names)
                    find_free_vars(body, new_bound_with_shared)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body = arm[1], arm[2], arm[3]
                    for aux_idx in auxiliaries:
                        find_free_vars(aux_idx, bound_names)
                    new_bound = new_bound_with_shared | {predecessor[1]}
                    find_free_vars(body, new_bound)
    
    find_free_vars(replacement_root, set())
    
    # Find replaceable occurrences of target and check for capture
    capturing_decls = set()
    
    def find_and_check(idx, scope_stack):
        node = nodes[idx]
        
        if node[0] == "var" and node[1] == target:
            # Check if target is shadowed by a binding in scope
            shadowed = any(decl_name == target for _, decl_name in scope_stack)
            
            if not shadowed:
                # Mark declarations whose names are free in replacement
                for decl_id, decl_name in scope_stack:
                    if decl_name in free_vars:
                        capturing_decls.add(decl_id)
        
        elif node[0] == "call":
            for child_idx in node[1]:
                find_and_check(child_idx, scope_stack)
        
        elif node[0] == "bind":
            declarations, body = node[1], node[2]
            new_scope = scope_stack + list(declarations)
            find_and_check(body, new_scope)
        
        elif node[0] == "let":
            declaration, value, body = node[1], node[2], node[3]
            find_and_check(value, scope_stack)
            new_scope = scope_stack + [declaration]
            find_and_check(body, new_scope)
        
        elif node[0] == "match":
            scrutinee, shared, arms = node[1], node[2], node[3]
            find_and_check(scrutinee, scope_stack)
            
            shared_decls = shared if shared else []
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body = arm[1], arm[2], arm[3]
                    for aux_idx in auxiliaries:
                        find_and_check(aux_idx, scope_stack)
                    new_scope = scope_stack + shared_decls + list(fields)
                    find_and_check(body, new_scope)
                elif arm[0] == "zero":
                    auxiliaries, body = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        find_and_check(aux_idx, scope_stack)
                    new_scope = scope_stack + shared_decls
                    find_and_check(body, new_scope)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body = arm[1], arm[2], arm[3]
                    for aux_idx in auxiliaries:
                        find_and_check(aux_idx, scope_stack)
                    new_scope = scope_stack + shared_decls + [predecessor]
                    find_and_check(body, new_scope)
    
    find_and_check(expr_root, [])
    
    return sorted(list(capturing_decls))