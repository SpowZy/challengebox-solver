def track_indicator(initial_ids, selected_index, operations):
    result = []
    tabs = list(initial_ids)
    selected_id = initial_ids[selected_index] if selected_index >= 0 else None
    
    for op in operations:
        op_type = op[0]
        
        if op_type == "insert":
            _, p, ids = op
            for i, new_id in enumerate(ids):
                tabs.insert(p + i, new_id)
            if selected_id is None:
                selected_id = ids[0]
        
        elif op_type == "remove":
            _, ids_to_remove = op
            ids_set = set(ids_to_remove)
            
            if selected_id is not None and selected_id in ids_set:
                old_positions = {tab_id: i for i, tab_id in enumerate(tabs)}
                old_selected_pos = old_positions[selected_id]
                tabs = [t for t in tabs if t not in ids_set]
                
                new_selected = None
                for tab_id in tabs:
                    if old_positions[tab_id] > old_selected_pos:
                        new_selected = tab_id
                        break
                
                if new_selected is None:
                    for i in range(len(tabs) - 1, -1, -1):
                        if old_positions[tabs[i]] < old_selected_pos:
                            new_selected = tabs[i]
                            break
                
                selected_id = new_selected
            else:
                tabs = [t for t in tabs if t not in ids_set]
        
        elif op_type == "reverse":
            _, left, right = op
            tabs[left:right] = tabs[left:right][::-1]
        
        result.append(tabs.index(selected_id) if selected_id is not None else -1)
    
    return result