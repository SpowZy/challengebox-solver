def track_indicator(initial_ids, selected_index, operations):
    tabs = list(initial_ids)
    selected_id = initial_ids[selected_index] if selected_index != -1 else None
    result = []
    
    for op in operations:
        if op[0] == "insert":
            _, p, ids_to_insert = op
            tabs = tabs[:p] + list(ids_to_insert) + tabs[p:]
            if selected_id is None:
                selected_id = ids_to_insert[0]
        
        elif op[0] == "remove":
            _, ids_to_remove = op
            ids_to_remove_set = set(ids_to_remove)
            
            if selected_id in ids_to_remove_set:
                selected_pos = tabs.index(selected_id)
                new_selected_id = None
                for i in range(selected_pos + 1, len(tabs)):
                    if tabs[i] not in ids_to_remove_set:
                        new_selected_id = tabs[i]
                        break
                if new_selected_id is None:
                    for i in range(selected_pos - 1, -1, -1):
                        if tabs[i] not in ids_to_remove_set:
                            new_selected_id = tabs[i]
                            break
                selected_id = new_selected_id
            
            tabs = [t for t in tabs if t not in ids_to_remove_set]
        
        elif op[0] == "reverse":
            _, left, right = op
            tabs = tabs[:left] + tabs[left:right][::-1] + tabs[right:]
        
        if selected_id is None:
            result.append(-1)
        else:
            result.append(tabs.index(selected_id))
    
    return result