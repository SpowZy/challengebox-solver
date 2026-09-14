def capture_binders(nodes, expr_root, target, replacement_root):
    free_names = set()
    
    def traverse_repl(idx, bound):
        if idx is None:
            return
        node = nodes[idx]
        if node[0] == "var":
            if node[1] not in bound:
                free_names.add(node[1])
        elif node[0] == "call":
            for child in node[1]:
                traverse_repl(child, bound)
        elif node[0] == "bind":
            decls, body = node[1], node[2]
            traverse_repl(body, bound | {d[1] for d in decls})
        elif node[0] == "let":
            decl, value, body = node[1], node[2], node[3]
            traverse_repl(value, bound)
            traverse_repl(body, bound | {decl[1]})
        elif node[0] == "match":
            scrutinee, shared, arms = node[1], node[2], node[3]
            traverse_repl(scrutinee, bound)
            shared_bound = bound | {d[1] for d in shared}
            for arm in arms:
                if arm[0] == "ctor":
                    fields, aux, body = arm[1], arm[2], arm[3]
                    traverse_repl(body, shared_bound | {d[1] for d in fields})
                elif arm[0] == "zero":
                    aux, body = arm[1], arm[2]
                    traverse_repl(body, shared_bound)
                elif arm[0] == "succ":
                    pred, aux, body = arm[1], arm[2], arm[3]
                    traverse_repl(body, shared_bound | {pred[1]})
    
    traverse_repl(replacement_root, set())
    
    capturing = set()
    
    def dfs(idx, decls):
        if idx is None:
            return
        node = nodes[idx]
        
        if node[0] == "var":
            if node[1] == target:
                if not any(d[1] == target for d in decls):
                    for did, dname in decls:
                        if dname in free_names:
                            capturing.add(did)
        elif node[0] == "call":
            for child in node[1]:
                dfs(child, decls)
        elif node[0] == "bind":
            decls_list, body = node[1], node[2]
            dfs(body, decls + decls_list)
        elif node[0] == "let":
            decl, value, body = node[1], node[2], node[3]
            dfs(value, decls)
            dfs(body, decls + [decl])
        elif node[0] == "match":
            scrutinee, shared, arms = node[1], node[2], node[3]
            dfs(scrutinee, decls)
            new_decls = decls + shared
            for arm in arms:
                if arm[0] == "ctor":
                    fields, aux, body = arm[1], arm[2], arm[3]
                    for a in aux:
                        dfs(a, decls)
                    dfs(body, new_decls + fields)
                elif arm[0] == "zero":
                    aux, body = arm[1], arm[2]
                    for a in aux:
                        dfs(a, decls)
                    dfs(body, new_decls)
                elif arm[0] == "succ":
                    pred, aux, body = arm[1], arm[2], arm[3]
                    for a in aux:
                        dfs(a, decls)
                    dfs(body, new_decls + [pred])
    
    dfs(expr_root, [])
    
    return sorted(list(capturing))