def track_indicator(initial_ids, selected_index, operations):
    result = []
    
    tabs = list(initial_ids)
    selected_id = tabs[selected_index] if selected_index >= 0 else None
    
    for op in operations:
        if op[0] == "insert":
            p, ids = op[1], op[2]
            tabs = tabs[:p] + list(ids) + tabs[p:]
            if selected_id is None:
                selected_id = ids[0]
        
        elif op[0] == "remove":
            ids_to_remove = set(op[1])
            if selected_id in ids_to_remove:
                selected_pos = tabs.index(selected_id)
                next_selected = None
                for i in range(selected_pos + 1, len(tabs)):
                    if tabs[i] not in ids_to_remove:
                        next_selected = tabs[i]
                        break
                
                if next_selected is not None:
                    selected_id = next_selected
                else:
                    for i in range(selected_pos - 1, -1, -1):
                        if tabs[i] not in ids_to_remove:
                            selected_id = tabs[i]
                            break
                    else:
                        selected_id = None
            
            tabs = [t for t in tabs if t not in ids_to_remove]
        
        elif op[0] == "reverse":
            left, right = op[1], op[2]
            tabs = tabs[:left] + tabs[left:right][::-1] + tabs[right:]
        
        if selected_id is not None:
            result.append(tabs.index(selected_id))
        else:
            result.append(-1)
    
    return result