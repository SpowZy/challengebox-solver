def track_indicator(initial_ids, selected_index, operations):
    tabs = list(initial_ids)
    selected_id = tabs[selected_index] if selected_index >= 0 else None
    
    result = []
    
    for op in operations:
        if op[0] == "insert":
            p, ids = op[1], op[2]
            ids_list = list(ids)
            
            if not tabs:
                selected_id = ids_list[0]
            
            tabs = tabs[:p] + ids_list + tabs[p:]
        
        elif op[0] == "remove":
            remove_ids = set(op[1])
            
            if selected_id in remove_ids:
                selected_pos = tabs.index(selected_id)
                
                new_selected = None
                for i in range(selected_pos + 1, len(tabs)):
                    if tabs[i] not in remove_ids:
                        new_selected = tabs[i]
                        break
                
                if new_selected is None:
                    for i in range(selected_pos - 1, -1, -1):
                        if tabs[i] not in remove_ids:
                            new_selected = tabs[i]
                            break
                
                selected_id = new_selected
            
            tabs = [t for t in tabs if t not in remove_ids]
        
        elif op[0] == "reverse":
            left, right = op[1], op[2]
            tabs = tabs[:left] + tabs[left:right][::-1] + tabs[right:]
        
        if selected_id is None:
            result.append(-1)
        else:
            result.append(tabs.index(selected_id))
    
    return result