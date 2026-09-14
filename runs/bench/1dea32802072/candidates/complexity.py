def track_indicator(initial_ids, selected_index, operations):
    result = []
    tabs = list(initial_ids)
    selected_id = initial_ids[selected_index] if initial_ids else None
    
    for op in operations:
        if op[0] == "insert":
            _, p, ids = op
            for i, tab_id in enumerate(ids):
                tabs.insert(p + i, tab_id)
            
            if selected_id is None:
                selected_id = ids[0]
        
        elif op[0] == "remove":
            _, ids_to_remove = op
            ids_set = set(ids_to_remove)
            
            if selected_id in ids_set:
                old_selected_pos = tabs.index(selected_id)
                new_selected_id = None
                
                for i in range(old_selected_pos + 1, len(tabs)):
                    if tabs[i] not in ids_set:
                        new_selected_id = tabs[i]
                        break
                
                if new_selected_id is None:
                    for i in range(old_selected_pos - 1, -1, -1):
                        if tabs[i] not in ids_set:
                            new_selected_id = tabs[i]
                            break
                
                selected_id = new_selected_id
            
            tabs = [tab_id for tab_id in tabs if tab_id not in ids_set]
        
        elif op[0] == "reverse":
            _, left, right = op
            tabs[left:right] = reversed(tabs[left:right])
        
        if selected_id is not None and selected_id in tabs:
            indicator_index = tabs.index(selected_id)
        else:
            indicator_index = -1
        
        result.append(indicator_index)
    
    return result