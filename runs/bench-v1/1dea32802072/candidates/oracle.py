def track_indicator(initial_ids, selected_index, operations):
    tabs = list(initial_ids)
    
    if tabs:
        selected_id = tabs[selected_index]
    else:
        selected_id = None
    
    result = []
    
    for op in operations:
        if op[0] == "insert":
            _, p, ids = op
            new_ids = list(ids)
            
            was_empty = len(tabs) == 0
            tabs = tabs[:p] + new_ids + tabs[p:]
            
            if was_empty:
                selected_id = new_ids[0]
        
        elif op[0] == "remove":
            _, ids_to_remove = op
            ids_to_remove_set = set(ids_to_remove)
            
            if selected_id is not None and selected_id in ids_to_remove_set:
                old_tabs = tabs
                selected_pos = tabs.index(selected_id)
                
                tabs = [t for t in tabs if t not in ids_to_remove_set]
                
                if not tabs:
                    selected_id = None
                else:
                    found = False
                    # First surviving to the right
                    for i in range(selected_pos + 1, len(old_tabs)):
                        if old_tabs[i] not in ids_to_remove_set:
                            selected_id = old_tabs[i]
                            found = True
                            break
                    
                    if not found:
                        # Last surviving to the left
                        for i in range(selected_pos - 1, -1, -1):
                            if old_tabs[i] not in ids_to_remove_set:
                                selected_id = old_tabs[i]
                                found = True
                                break
            else:
                tabs = [t for t in tabs if t not in ids_to_remove_set]
        
        elif op[0] == "reverse":
            _, left, right = op
            tabs = tabs[:left] + tabs[left:right][::-1] + tabs[right:]
        
        # Record current indicator index
        if selected_id is not None and selected_id in tabs:
            current_index = tabs.index(selected_id)
        else:
            current_index = -1
        
        result.append(current_index)
    
    return result