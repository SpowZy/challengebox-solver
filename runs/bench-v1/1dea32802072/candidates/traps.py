def track_indicator(initial_ids, selected_index, operations):
    result = []
    
    tabs = list(initial_ids)
    selected_id = initial_ids[selected_index] if selected_index >= 0 else None
    selected_pos = selected_index if selected_index >= 0 else -1
    
    for op in operations:
        if op[0] == "insert":
            p, ids = op[1], op[2]
            for i, tab_id in enumerate(ids):
                tabs.insert(p + i, tab_id)
                if selected_id is not None and p + i <= selected_pos:
                    selected_pos += 1
            
            if selected_id is None:
                selected_id = ids[0]
                selected_pos = p
        
        elif op[0] == "remove":
            ids_to_remove = set(op[1])
            old_tabs = tabs[:]
            old_selected_pos = selected_pos
            
            if selected_id in ids_to_remove:
                found = False
                for i in range(old_selected_pos + 1, len(old_tabs)):
                    if old_tabs[i] not in ids_to_remove:
                        selected_id = old_tabs[i]
                        found = True
                        break
                
                if not found:
                    for i in range(old_selected_pos - 1, -1, -1):
                        if old_tabs[i] not in ids_to_remove:
                            selected_id = old_tabs[i]
                            found = True
                            break
                
                if not found:
                    selected_id = None
            
            new_tabs = []
            new_selected_pos = -1
            for tab_id in old_tabs:
                if tab_id not in ids_to_remove:
                    if tab_id == selected_id:
                        new_selected_pos = len(new_tabs)
                    new_tabs.append(tab_id)
            
            tabs = new_tabs
            selected_pos = new_selected_pos
        
        elif op[0] == "reverse":
            left, right = op[1], op[2]
            tabs[left:right] = tabs[left:right][::-1]
            
            if selected_id is not None and left <= selected_pos < right:
                selected_pos = left + (right - 1 - selected_pos)
        
        result.append(selected_pos)
    
    return result