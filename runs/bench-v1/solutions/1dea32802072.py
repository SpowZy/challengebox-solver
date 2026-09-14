def track_indicator(initial_ids, selected_index, operations):
    tabs = list(initial_ids)
    selected_id = tabs[selected_index] if selected_index >= 0 else None
    
    result = []
    
    for op in operations:
        if op[0] == "insert":
            p, ids = op[1], op[2]
            new_ids = list(ids)
            tabs = tabs[:p] + new_ids + tabs[p:]
            
            if selected_id is None and len(tabs) > 0:
                selected_id = tabs[p]
        
        elif op[0] == "remove":
            ids_to_remove = set(op[1])
            
            if selected_id in ids_to_remove:
                old_selected_pos = tabs.index(selected_id)
                
                new_selected_id = None
                for i in range(old_selected_pos + 1, len(tabs)):
                    if tabs[i] not in ids_to_remove:
                        new_selected_id = tabs[i]
                        break
                
                if new_selected_id is None:
                    for i in range(old_selected_pos - 1, -1, -1):
                        if tabs[i] not in ids_to_remove:
                            new_selected_id = tabs[i]
                            break
                
                selected_id = new_selected_id
            
            tabs = [t for t in tabs if t not in ids_to_remove]
        
        elif op[0] == "reverse":
            left, right = op[1], op[2]
            tabs = tabs[:left] + tabs[left:right][::-1] + tabs[right:]
        
        if selected_id is None:
            result.append(-1)
        else:
            result.append(tabs.index(selected_id))
    
    return result