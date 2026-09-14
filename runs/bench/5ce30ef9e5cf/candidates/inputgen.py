def gen(rng, scale):
    if scale == "edge":
        # Minimal valid input: one object, one cell, one GET
        N, K, Q = 1, 1, 1
        lines = [f"{N} {K} {Q}"]
        lines.append("1 1 I 0")
        lines.append("GET 1 1 1")
        return "\n".join(lines)
    
    elif scale == "small":
        # Small: 3 objects, 6 cells, 12 commands
        N, K, Q = 3, 6, 12
        lines = [f"{N} {K} {Q}"]
        
        # Create a cycle via attr 1: obj 1 -> 2 -> 3 -> 1
        lines.append("1 1 O 2")  # obj 1, attr 1 points to obj 2
        lines.append("1 2 I 10")  # obj 1, attr 2 is integer
        lines.append("2 1 O 3")  # obj 2, attr 1 points to obj 3
        lines.append("2 2 I 20")  # obj 2, attr 2 is integer
        lines.append("3 1 O 1")  # obj 3, attr 1 points to obj 1
        lines.append("3 2 I 30")  # obj 3, attr 2 is integer
        
        # Valid commands using the paths we set up
        lines.append("GET 1 1 1")  # Read obj 1, attr 1
        lines.append("GET 2 1 1")  # Read obj 2, attr 1
        lines.append("START 1 1 1 2 1 2 I 99")  # Activation 1: follow 1->2, write to attr 2
        lines.append("STACK")  # Check active activations
        lines.append("GET 1 2 1")  # Read obj 1, attr 2
        lines.append("STOP 1")  # Restore activation 1
        lines.append("GET 1 2 1")  # Read restored value
        lines.append("START 2 1 2 2 1 2 O 3")  # Activation 2: follow 2->3, write reference
        lines.append("STOPALL")  # Stop all active
        lines.append("STACK")
        lines.append("GET 2 2 1")  # Read obj 2, attr 2
        lines.append("GET 3 1 1")  # Read obj 3, attr 1
        
        return "\n".join(lines)
    
    else:  # medium
        # Medium: 6 objects, 15 cells, 30 commands
        N, K, Q = 6, 15, 30
        lines = [f"{N} {K} {Q}"]
        
        # Create reference chain via attr 1
        for i in range(1, min(N + 1, K + 1)):
            next_obj = (i % N) + 1
            lines.append(f"{i} 1 O {next_obj}")
        
        # Fill remaining cells with integers at different attributes
        for i in range(N, K):
            obj = ((i - N) % N) + 1
            attr = 2 + ((i - N) // N)
            val = rng.randint(-50000, 50000)
            lines.append(f"{obj} {attr} I {val}")
        
        # Generate commands with varied operations
        act_id = 1
        for idx in range(Q - K):
            operation = idx % 5
            
            if operation == 0 and act_id <= Q:
                root = (idx % N) + 1
                value = rng.randint(-10000, 10000)
                lines.append(f"START {act_id} 1 {root} 2 1 2 I {value}")
                act_id += 1
            elif operation == 1:
                root = (idx % N) + 1
                lines.append(f"GET {root} 1 1")
            elif operation == 2 and act_id > 1:
                stop_id = ((idx % (act_id - 1)) + 1)
                lines.append(f"STOP {stop_id}")
            elif operation == 3 and act_id > 1:
                lines.append("STOPALL")
                act_id = 1
            else:
                lines.append("STACK")
        
        return "\n".join(lines)