def track_indicator(initial_ids, selected_index, operations):
    result = []
    
    tabs = list(initial_ids)
    selected_id = tabs[selected_index] if selected_index >= 0 else None
    
    for op in operations:
        op_type = op[0]
        
        if op_type == "insert":
            _, p, ids = op
            ids_list = list(ids)
            tabs = tabs[:p] + ids_list + tabs[p:]
            if selected_id is None:
                selected_id = ids_list[0]
        
        elif op_type == "remove":
            _, ids_to_remove = op
            ids_set = set(ids_to_remove)
            
            if selected_id is not None and selected_id in ids_set:
                selected_pos = tabs.index(selected_id)
                
                selected_id = None
                for i in range(selected_pos + 1, len(tabs)):
                    if tabs[i] not in ids_set:
                        selected_id = tabs[i]
                        break
                
                if selected_id is None:
                    for i in range(selected_pos - 1, -1, -1):
                        if tabs[i] not in ids_set:
                            selected_id = tabs[i]
                            break
            
            tabs = [t for t in tabs if t not in ids_set]
        
        elif op_type == "reverse":
            _, left, right = op
            tabs = tabs[:left] + tabs[left:right][::-1] + tabs[right:]
        
        if selected_id is not None:
            result.append(tabs.index(selected_id))
        else:
            result.append(-1)
    
    return result