def track_indicator(initial_ids, selected_index, operations):
    tabs = list(initial_ids)
    selected_id = tabs[selected_index] if selected_index >= 0 else None
    result = []
    
    for op in operations:
        if op[0] == "insert":
            _, pos, ids = op
            tabs[pos:pos] = ids
            if selected_id is None and tabs:
                selected_id = ids[0]
        
        elif op[0] == "remove":
            _, ids_to_remove = op
            ids_set = set(ids_to_remove)
            
            if selected_id in ids_set:
                selected_pos = tabs.index(selected_id)
                surviving_indices = [i for i, tab_id in enumerate(tabs) if tab_id not in ids_set]
                
                new_selected_id = None
                for idx in surviving_indices:
                    if idx > selected_pos:
                        new_selected_id = tabs[idx]
                        break
                
                if new_selected_id is None:
                    for idx in reversed(surviving_indices):
                        if idx < selected_pos:
                            new_selected_id = tabs[idx]
                            break
                
                selected_id = new_selected_id
            
            tabs = [tab_id for tab_id in tabs if tab_id not in ids_set]
        
        elif op[0] == "reverse":
            _, left, right = op
            tabs[left:right] = tabs[left:right][::-1]
        
        indicator = tabs.index(selected_id) if selected_id is not None else -1
        result.append(indicator)
    
    return result