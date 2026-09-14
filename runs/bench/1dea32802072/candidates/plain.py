def track_indicator(initial_ids, selected_index, operations):
    tabs = list(initial_ids)
    selected_id = initial_ids[selected_index] if selected_index >= 0 else -1
    selected_pos = selected_index
    
    result = []
    
    for op in operations:
        if op[0] == "insert":
            _, p, ids = op
            # Update selected_pos if inserting before or at it
            if selected_pos >= 0 and p <= selected_pos:
                selected_pos += len(ids)
            
            tabs[p:p] = ids
            
            if selected_id == -1:
                selected_id = ids[0]
                selected_pos = p
        
        elif op[0] == "remove":
            _, ids_to_remove = op
            ids_to_remove_set = set(ids_to_remove)
            
            # If selected_id is being removed, find replacement
            if selected_id in ids_to_remove_set:
                old_pos = selected_pos
                
                # Look to the right first
                selected_id = -1
                for i in range(old_pos + 1, len(tabs)):
                    if tabs[i] not in ids_to_remove_set:
                        selected_id = tabs[i]
                        break
                
                # If not found to the right, look to the left
                if selected_id == -1:
                    for i in range(old_pos - 1, -1, -1):
                        if tabs[i] not in ids_to_remove_set:
                            selected_id = tabs[i]
                            break
            
            # Remove the tabs and update selected_pos
            new_tabs = []
            new_selected_pos = -1
            for t in tabs:
                if t not in ids_to_remove_set:
                    if t == selected_id:
                        new_selected_pos = len(new_tabs)
                    new_tabs.append(t)
            
            tabs = new_tabs
            selected_pos = new_selected_pos if selected_id != -1 else -1
        
        elif op[0] == "reverse":
            _, left, right = op
            tabs[left:right] = tabs[left:right][::-1]
            
            # Update selected_pos if it's in the reversed range
            if selected_pos >= 0 and left <= selected_pos < right:
                selected_pos = left + (right - 1 - selected_pos)
        
        # Append current indicator
        result.append(selected_pos)
    
    return result