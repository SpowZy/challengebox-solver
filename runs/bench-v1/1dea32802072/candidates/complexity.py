def track_indicator(initial_ids, selected_index, operations):
    tabs = list(initial_ids)
    selected_pos = selected_index
    
    result = [selected_index]
    
    for op in operations:
        if op[0] == "insert":
            _, p, ids = op
            tabs[p:p] = ids
            if selected_pos >= 0 and p <= selected_pos:
                selected_pos += len(ids)
            elif selected_pos < 0:
                selected_pos = 0
        
        elif op[0] == "remove":
            _, ids_to_remove = op
            ids_set = set(ids_to_remove)
            
            if selected_pos >= 0 and tabs[selected_pos] in ids_set:
                old_pos = selected_pos
                new_tabs = []
                first_after = -1
                last_before = -1
                
                for i, id_ in enumerate(tabs):
                    if id_ not in ids_set:
                        new_tabs.append(id_)
                        if i > old_pos and first_after < 0:
                            first_after = len(new_tabs) - 1
                        if i < old_pos:
                            last_before = len(new_tabs) - 1
                
                tabs = new_tabs
                
                if first_after >= 0:
                    selected_pos = first_after
                elif last_before >= 0:
                    selected_pos = last_before
                else:
                    selected_pos = -1
            else:
                count_before = 0
                new_tabs = []
                for i, id_ in enumerate(tabs):
                    if id_ not in ids_set:
                        new_tabs.append(id_)
                    elif selected_pos >= 0 and i < selected_pos:
                        count_before += 1
                
                tabs = new_tabs
                if selected_pos >= 0:
                    selected_pos -= count_before
        
        elif op[0] == "reverse":
            _, left, right = op
            tabs[left:right] = tabs[left:right][::-1]
            if selected_pos >= 0 and left <= selected_pos < right:
                selected_pos = left + right - 1 - selected_pos
        
        result.append(selected_pos)
    
    return result