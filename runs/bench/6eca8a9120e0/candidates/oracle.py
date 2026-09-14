def capture_binders(nodes, expr_root, target, replacement_root):
    def get_free_vars(node_idx, bound_names):
        if node_idx is None:
            return set()
        node = nodes[node_idx]
        
        if node[0] == "var":
            return {node[1]} if node[1] not in bound_names else set()
        elif node[0] == "call":
            free = set()
            for child in node[1]:
                free |= get_free_vars(child, bound_names)
            return free
        elif node[0] == "bind":
            decls, body = node[1], node[2]
            new_bound = bound_names | {d[1] for d in decls}
            return get_free_vars(body, new_bound)
        elif node[0] == "let":
            decl, val, body = node[1], node[2], node[3]
            free = get_free_vars(val, bound_names)
            new_bound = bound_names | {decl[1]}
            free |= get_free_vars(body, new_bound)
            return free
        elif node[0] == "match":
            scrutinee, shared_decls, arms = node[1], node[2], node[3]
            free = get_free_vars(scrutinee, bound_names)
            shared_names = {d[1] for d in shared_decls}
            new_bound = bound_names | shared_names
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, aux, body = arm[1], arm[2], arm[3]
                    for aux_idx in aux:
                        free |= get_free_vars(aux_idx, bound_names)
                    arm_bound = new_bound | {f[1] for f in fields}
                    free |= get_free_vars(body, arm_bound)
                elif arm[0] == "zero":
                    aux, body = arm[1], arm[2]
                    for aux_idx in aux:
                        free |= get_free_vars(aux_idx, bound_names)
                    free |= get_free_vars(body, new_bound)
                elif arm[0] == "succ":
                    pred, aux, body = arm[1], arm[2], arm[3]
                    for aux_idx in aux:
                        free |= get_free_vars(aux_idx, bound_names)
                    arm_bound = new_bound | {pred[1]}
                    free |= get_free_vars(body, arm_bound)
            return free
        return set()
    
    repl_free = get_free_vars(replacement_root, set())
    capturing = set()
    visited = set()
    
    def traverse(node_idx, in_scope, shadowed):
        key = (node_idx, in_scope, shadowed)
        if key in visited:
            return
        visited.add(key)
        
        if node_idx is None:
            return
        
        node = nodes[node_idx]
        
        if node[0] == "var":
            if node[1] == target and not shadowed:
                for name, decl_id in dict(in_scope).items():
                    if name in repl_free:
                        capturing.add(decl_id)
        elif node[0] == "call":
            for child in node[1]:
                traverse(child, in_scope, shadowed)
        elif node[0] == "bind":
            decls, body = node[1], node[2]
            new_scope = dict(in_scope)
            new_shadowed = shadowed
            for decl_id, name in decls:
                new_scope[name] = decl_id
                if name == target:
                    new_shadowed = True
            traverse(body, tuple(sorted(new_scope.items())), new_shadowed)
        elif node[0] == "let":
            decl, val, body = node[1], node[2], node[3]
            traverse(val, in_scope, shadowed)
            new_scope = dict(in_scope)
            new_scope[decl[1]] = decl[0]
            new_shadowed = shadowed or (decl[1] == target)
            traverse(body, tuple(sorted(new_scope.items())), new_shadowed)
        elif node[0] == "match":
            scrutinee, shared_decls, arms = node[1], node[2], node[3]
            traverse(scrutinee, in_scope, shadowed)
            
            new_scope = dict(in_scope)
            new_shadowed = shadowed
            for decl_id, name in shared_decls:
                new_scope[name] = decl_id
                if name == target:
                    new_shadowed = True
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, aux, body = arm[1], arm[2], arm[3]
                    for aux_idx in aux:
                        traverse(aux_idx, in_scope, shadowed)
                    arm_scope = dict(new_scope)
                    arm_shadowed = new_shadowed
                    for decl_id, name in fields:
                        arm_scope[name] = decl_id
                        if name == target:
                            arm_shadowed = True
                    traverse(body, tuple(sorted(arm_scope.items())), arm_shadowed)
                elif arm[0] == "zero":
                    aux, body = arm[1], arm[2]
                    for aux_idx in aux:
                        traverse(aux_idx, in_scope, shadowed)
                    traverse(body, tuple(sorted(new_scope.items())), new_shadowed)
                elif arm[0] == "succ":
                    pred, aux, body = arm[1], arm[2], arm[3]
                    for aux_idx in aux:
                        traverse(aux_idx, in_scope, shadowed)
                    arm_scope = dict(new_scope)
                    arm_shadowed = new_shadowed
                    arm_scope[pred[1]] = pred[0]
                    if pred[1] == target:
                        arm_shadowed = True
                    traverse(body, tuple(sorted(arm_scope.items())), arm_shadowed)
    
    traverse(expr_root, tuple(), False)
    return sorted(list(capturing))