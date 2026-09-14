def track_indicator(initial_ids, selected_index, operations):
    # Current state of tabs
    tabs = list(initial_ids)
    # Track which tab is currently selected by its identifier
    selected_id = initial_ids[selected_index] if selected_index >= 0 else None
    
    # Result includes initial state
    result = [selected_index]
    
    for op in operations:
        op_type = op[0]
        
        if op_type == "insert":
            _, p, ids = op
            
            # Insert identifiers at position p
            for i, tab_id in enumerate(ids):
                tabs.insert(p + i, tab_id)
            
            # If strip was empty, first inserted becomes selected
            if selected_id is None:
                selected_id = ids[0]
            
            # Find index of selected tab
            selected_index = tabs.index(selected_id)
            
        elif op_type == "remove":
            _, ids_to_remove = op
            ids_to_remove_set = set(ids_to_remove)
            
            # Check if selected tab will survive
            selected_survives = selected_id is not None and selected_id not in ids_to_remove_set
            
            if not selected_survives and selected_id is not None:
                # Find replacement for selection
                # Use original order to find next tab
                original_pos = tabs.index(selected_id)
                
                # Try to find first surviving tab to the right
                new_selected_id = None
                for i in range(original_pos + 1, len(tabs)):
                    if tabs[i] not in ids_to_remove_set:
                        new_selected_id = tabs[i]
                        break
                
                # If none to right, find last surviving to the left
                if new_selected_id is None:
                    for i in range(original_pos - 1, -1, -1):
                        if tabs[i] not in ids_to_remove_set:
                            new_selected_id = tabs[i]
                            break
                
                selected_id = new_selected_id
            
            # Remove the identifiers
            tabs = [tab for tab in tabs if tab not in ids_to_remove_set]
            
            # Find new index of selected tab
            if selected_id is not None:
                selected_index = tabs.index(selected_id)
            else:
                selected_index = -1
        
        elif op_type == "reverse":
            _, left, right = op
            # Reverse tabs from position left to right-1
            tabs[left:right] = list(reversed(tabs[left:right]))
            
            # Find new index of selected tab
            if selected_id is not None:
                selected_index = tabs.index(selected_id)
            else:
                selected_index = -1
        
        result.append(selected_index)
    
    return result