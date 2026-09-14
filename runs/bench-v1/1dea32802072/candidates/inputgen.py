def gen(rng, scale):
    if scale == "edge":
        cases = [
            ([], -1, []),
            ([1], 0, []),
            ([], -1, [("insert", 0, [100])]),
            ([], -1, [("insert", 0, [100, 101, 102])]),
            ([1], 0, [("remove", [1])]),
            ([1, 2], 0, [("remove", [1])]),
            ([1, 2], 1, [("remove", [2])]),
            ([1, 2], 0, [("remove", [2])]),
            ([10, 20, 30], 0, [("remove", [20, 30])]),
            ([10, 20, 30], 1, [("remove", [10, 30])]),
            ([10, 20, 30], 2, [("remove", [10, 20])]),
            ([10, 20, 30], 0, [("reverse", 0, 2)]),
            ([10, 20, 30], 1, [("reverse", 1, 3)]),
            ([10, 20, 30], 2, [("reverse", 0, 3)]),
            ([1, 2], 0, [("reverse", 0, 2)]),
            ([1, 2, 3, 4], 0, [("insert", 0, [100])]),
            ([1, 2, 3, 4], 2, [("insert", 4, [100, 101])]),
        ]
        return rng.choice(cases)
    
    if scale == "small":
        max_ops = 12
        max_initial = 6
        max_insert = 2
        max_remove = 2
    else:
        max_ops = 35
        max_initial = 22
        max_insert = 4
        max_remove = 4
    
    num_initial = rng.randint(0 if scale == "small" else 1, max_initial)
    next_id = 100000
    initial_ids = list(range(next_id, next_id + num_initial))
    next_id += num_initial
    
    initial_selected = rng.randint(0, len(initial_ids) - 1) if initial_ids else -1
    
    current_ids = list(initial_ids)
    selected_id = initial_ids[initial_selected] if initial_selected != -1 else None
    operations = []
    
    for _ in range(rng.randint(0, max_ops)):
        if not current_ids:
            num_new = rng.randint(1, max_insert)
            new_ids = list(range(next_id, next_id + num_new))
            next_id += num_new
            operations.append(("insert", 0, new_ids))
            current_ids = new_ids
            selected_id = new_ids[0]
        else:
            op_choice = rng.choices(
                ["insert", "remove", "reverse"],
                weights=[30, 40, 30],
                k=1
            )[0]
            
            if op_choice == "insert":
                num_new = rng.randint(1, max_insert)
                new_ids = list(range(next_id, next_id + num_new))
                next_id += num_new
                pos = rng.randint(0, len(current_ids))
                operations.append(("insert", pos, new_ids))
                current_ids[pos:pos] = new_ids
            
            elif op_choice == "remove":
                num_rem = rng.randint(1, min(max_remove, len(current_ids)))
                to_rem = rng.sample(current_ids, num_rem)
                operations.append(("remove", to_rem))
                
                if selected_id in to_rem:
                    pos = current_ids.index(selected_id)
                    current_ids = [x for x in current_ids if x not in to_rem]
                    if current_ids:
                        selected_id = current_ids[min(pos, len(current_ids) - 1)]
                    else:
                        selected_id = None
                else:
                    current_ids = [x for x in current_ids if x not in to_rem]
            
            elif len(current_ids) >= 2:
                left = rng.randint(0, len(current_ids) - 2)
                right = rng.randint(left + 1, len(current_ids))
                operations.append(("reverse", left, right))
                current_ids[left:right] = reversed(current_ids[left:right])
    
    return [initial_ids, initial_selected, operations]