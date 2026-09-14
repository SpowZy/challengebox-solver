import random

def gen(rng, scale):
    if scale == "edge":
        choice = rng.randint(0, 4)
        if choice == 0:
            return [[], -1, []]
        elif choice == 1:
            return [[1], 0, []]
        elif choice == 2:
            return [[1], 0, [("insert", 1, [2])]]
        elif choice == 3:
            return [[], -1, [("insert", 0, [1])]]
        else:
            return [[1], 0, [("insert", 0, [2, 3]), ("remove", [2])]]
    
    elif scale == "small":
        num_initial = rng.randint(0, 5)
        initial_ids = list(range(1, num_initial + 1))
        selected_index = -1 if num_initial == 0 else rng.randint(0, num_initial - 1)
        
        operations = []
        next_id = num_initial + 1
        current_order = list(initial_ids)
        current_selected_id = initial_ids[selected_index] if selected_index >= 0 else None
        
        num_ops = rng.randint(2, 8)
        
        for _ in range(num_ops):
            if len(current_order) == 0:
                ops_possible = ["insert"]
            else:
                ops_possible = ["insert", "remove", "reverse"]
            
            op_type = rng.choice(ops_possible)
            
            if op_type == "insert":
                num_insert = rng.randint(1, 3)
                insert_ids = list(range(next_id, next_id + num_insert))
                next_id += num_insert
                
                pos = rng.randint(0, len(current_order))
                operations.append(("insert", pos, insert_ids))
                
                current_order = current_order[:pos] + insert_ids + current_order[pos:]
                if current_selected_id is None:
                    current_selected_id = insert_ids[0]
            
            elif op_type == "remove":
                num_remove = min(rng.randint(1, 2), len(current_order))
                remove_ids = rng.sample(current_order, num_remove)
                operations.append(("remove", remove_ids))
                
                if current_selected_id in remove_ids:
                    old_pos = current_order.index(current_selected_id)
                    
                    new_selected_id = None
                    for i in range(old_pos + 1, len(current_order)):
                        if current_order[i] not in remove_ids:
                            new_selected_id = current_order[i]
                            break
                    
                    if new_selected_id is None:
                        for i in range(old_pos - 1, -1, -1):
                            if current_order[i] not in remove_ids:
                                new_selected_id = current_order[i]
                                break
                    
                    current_selected_id = new_selected_id
                
                current_order = [x for x in current_order if x not in remove_ids]
            
            elif op_type == "reverse":
                if len(current_order) > 1:
                    left = rng.randint(0, len(current_order) - 1)
                    right = rng.randint(left + 1, len(current_order))
                    operations.append(("reverse", left, right))
                    
                    current_order = current_order[:left] + current_order[left:right][::-1] + current_order[right:]
        
        return [initial_ids, selected_index, operations]
    
    else:
        num_initial = rng.randint(5, 20)
        initial_ids = list(range(1, num_initial + 1))
        selected_index = -1 if num_initial == 0 else rng.randint(0, num_initial - 1)
        
        operations = []
        next_id = num_initial + 1
        current_order = list(initial_ids)
        current_selected_id = initial_ids[selected_index] if selected_index >= 0 else None
        
        num_ops = rng.randint(10, 30)
        total_inserts = 0
        total_removes = 0
        max_inserts = 50
        max_removes = 50
        
        for _ in range(num_ops):
            can_insert = total_inserts < max_inserts
            can_remove = len(current_order) > 0 and total_removes < max_removes
            can_reverse = len(current_order) > 1
            
            valid_ops = []
            if can_insert:
                valid_ops.append("insert")
            if can_remove:
                valid_ops.append("remove")
            if can_reverse:
                valid_ops.append("reverse")
            
            if not valid_ops:
                break
            
            op_type = rng.choice(valid_ops)
            
            if op_type == "insert":
                num_insert = rng.randint(1, 5)
                if total_inserts + num_insert > max_inserts:
                    num_insert = max_inserts - total_inserts
                
                insert_ids = list(range(next_id, next_id + num_insert))
                next_id += num_insert
                total_inserts += num_insert
                
                pos = rng.randint(0, len(current_order))
                operations.append(("insert", pos, insert_ids))
                
                current_order = current_order[:pos] + insert_ids + current_order[pos:]
                if current_selected_id is None:
                    current_selected_id = insert_ids[0]
            
            elif op_type == "remove":
                num_remove = min(rng.randint(1, 3), len(current_order))
                if total_removes + num_remove > max_removes:
                    num_remove = max_removes - total_removes
                
                remove_ids = rng.sample(current_order, num_remove)
                operations.append(("remove", remove_ids))
                total_removes += num_remove
                
                if current_selected_id in remove_ids:
                    old_pos = current_order.index(current_selected_id)
                    
                    new_selected_id = None
                    for i in range(old_pos + 1, len(current_order)):
                        if current_order[i] not in remove_ids:
                            new_selected_id = current_order[i]
                            break
                    
                    if new_selected_id is None:
                        for i in range(old_pos - 1, -1, -1):
                            if current_order[i] not in remove_ids:
                                new_selected_id = current_order[i]
                                break
                    
                    current_selected_id = new_selected_id
                
                current_order = [x for x in current_order if x not in remove_ids]
            
            elif op_type == "reverse":
                left = rng.randint(0, len(current_order) - 1)
                right = rng.randint(left + 1, len(current_order))
                operations.append(("reverse", left, right))
                
                current_order = current_order[:left] + current_order[left:right][::-1] + current_order[right:]
        
        return [initial_ids, selected_index, operations]