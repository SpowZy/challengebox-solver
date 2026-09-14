def capture_binders(nodes, expr_root, target, replacement_root):
    # Find all free variables in the replacement term
    def find_free_vars(idx, bound_names=None):
        if bound_names is None:
            bound_names = set()
        
        result = set()
        node = nodes[idx]
        
        if node[0] == "var":
            if node[1] not in bound_names:
                result.add(node[1])
        elif node[0] == "call":
            for child_idx in node[1]:
                result.update(find_free_vars(child_idx, bound_names))
        elif node[0] == "bind":
            declarations, body_idx = node[1], node[2]
            new_bound = bound_names | {name for _, name in declarations}
            result.update(find_free_vars(body_idx, new_bound))
        elif node[0] == "let":
            declaration, value_idx, body_idx = node[1], node[2], node[3]
            _, name = declaration
            result.update(find_free_vars(value_idx, bound_names))
            new_bound = bound_names | {name}
            result.update(find_free_vars(body_idx, new_bound))
        elif node[0] == "match":
            scrutinee_idx, shared, arms = node[1], node[2], node[3]
            result.update(find_free_vars(scrutinee_idx, bound_names))
            
            shared_names = {name for _, name in shared} if shared else set()
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    field_names = {name for _, name in fields} if fields else set()
                    for aux_idx in auxiliaries:
                        result.update(find_free_vars(aux_idx, bound_names))
                    arm_bound = bound_names | shared_names | field_names
                    result.update(find_free_vars(body_idx, arm_bound))
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        result.update(find_free_vars(aux_idx, bound_names))
                    arm_bound = bound_names | shared_names
                    result.update(find_free_vars(body_idx, arm_bound))
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    pred_name = {predecessor[1]} if isinstance(predecessor, tuple) else set()
                    for aux_idx in auxiliaries:
                        result.update(find_free_vars(aux_idx, bound_names))
                    arm_bound = bound_names | shared_names | pred_name
                    result.update(find_free_vars(body_idx, arm_bound))
        
        return result
    
    free_vars = find_free_vars(replacement_root)
    
    # Find all target occurrences and their scoping declarations
    capturing = set()
    
    def find_targets(idx, scope):
        """scope is a dict mapping declaration name to (decl_id, decl_name)"""
        node = nodes[idx]
        
        if node[0] == "var":
            if node[1] == target:
                for name, (decl_id, _) in scope.items():
                    if name in free_vars:
                        capturing.add(decl_id)
        elif node[0] == "call":
            for child_idx in node[1]:
                find_targets(child_idx, scope)
        elif node[0] == "bind":
            declarations, body_idx = node[1], node[2]
            new_scope = dict(scope)
            for decl_id, decl_name in declarations:
                new_scope[decl_name] = (decl_id, decl_name)
            find_targets(body_idx, new_scope)
        elif node[0] == "let":
            declaration, value_idx, body_idx = node[1], node[2], node[3]
            find_targets(value_idx, scope)
            decl_id, decl_name = declaration
            new_scope = dict(scope)
            new_scope[decl_name] = (decl_id, decl_name)
            find_targets(body_idx, new_scope)
        elif node[0] == "match":
            scrutinee_idx, shared, arms = node[1], node[2], node[3]
            find_targets(scrutinee_idx, scope)
            
            shared_scope = dict(scope)
            if shared:
                for decl_id, decl_name in shared:
                    shared_scope[decl_name] = (decl_id, decl_name)
            
            for arm in arms:
                if arm[0] == "ctor":
                    fields, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    for aux_idx in auxiliaries:
                        find_targets(aux_idx, scope)
                    arm_scope = dict(shared_scope)
                    for decl_id, decl_name in fields:
                        arm_scope[decl_name] = (decl_id, decl_name)
                    find_targets(body_idx, arm_scope)
                elif arm[0] == "zero":
                    auxiliaries, body_idx = arm[1], arm[2]
                    for aux_idx in auxiliaries:
                        find_targets(aux_idx, scope)
                    find_targets(body_idx, shared_scope)
                elif arm[0] == "succ":
                    predecessor, auxiliaries, body_idx = arm[1], arm[2], arm[3]
                    for aux_idx in auxiliaries:
                        find_targets(aux_idx, scope)
                    arm_scope = dict(shared_scope)
                    if isinstance(predecessor, tuple):
                        decl_id, decl_name = predecessor
                        arm_scope[decl_name] = (decl_id, decl_name)
                    find_targets(body_idx, arm_scope)
    
    find_targets(expr_root, {})
    
    return sorted(list(capturing))