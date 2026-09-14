def track_indicator(initial_ids, selected_index, operations):
    tabs = list(initial_ids)
    if initial_ids:
        selected_id = initial_ids[selected_index]
    else:
        selected_id = None
    
    result = []
    
    for op in operations:
        if op[0] == "insert":
            p, ids = op[1], op[2]
            tabs[p:p] = ids
            
            if selected_id is None:
                selected_id = ids[0]
                selected_index = p
            else:
                selected_index = tabs.index(selected_id)
            
            result.append(selected_index)
        
        elif op[0] == "remove":
            ids_to_remove = set(op[1])
            
            if selected_id is not None and selected_id in ids_to_remove:
                old_pos = tabs.index(selected_id)
                
                new_selected_id = None
                for i in range(old_pos + 1, len(tabs)):
                    if tabs[i] not in ids_to_remove:
                        new_selected_id = tabs[i]
                        break
                
                if new_selected_id is None:
                    for i in range(old_pos - 1, -1, -1):
                        if tabs[i] not in ids_to_remove:
                            new_selected_id = tabs[i]
                            break
                
                tabs = [t for t in tabs if t not in ids_to_remove]
                
                if new_selected_id is not None:
                    selected_id = new_selected_id
                    selected_index = tabs.index(selected_id)
                else:
                    selected_id = None
                    selected_index = -1
            else:
                tabs = [t for t in tabs if t not in ids_to_remove]
                if selected_id is not None:
                    selected_index = tabs.index(selected_id)
                else:
                    selected_index = -1
            
            result.append(selected_index)
        
        elif op[0] == "reverse":
            left, right = op[1], op[2]
            tabs[left:right] = tabs[left:right][::-1]
            if selected_id is not None:
                selected_index = tabs.index(selected_id)
            else:
                selected_index = -1
            result.append(selected_index)
    
    return result