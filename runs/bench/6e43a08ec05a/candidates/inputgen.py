def gen(rng, scale):
    """
    Generate valid inputs for normalize_protection.
    
    Returns [ranges, edits, max_row, max_col] where:
    - ranges: list of (r1, c1, r2, c2) tuples
    - edits: list of (axis, index, delta) tuples
    - max_row, max_col: worksheet dimensions (fixed throughout)
    """
    
    if scale == "edge":
        # Degenerate cases
        case = rng.randint(0, 8)
        
        if case == 0:
            return [], [], 10, 10
        elif case == 1:
            return [(5, 5, 5, 5)], [], 10, 10
        elif case == 2:
            return [(1, 1, 1, 10)], [], 10, 10
        elif case == 3:
            return [(1, 1, 10, 1)], [], 10, 10
        elif case == 4:
            return [(1, 1, 10, 10)], [], 10, 10
        elif case == 5:
            return [(1, 1, 5, 5), (3, 3, 8, 8)], [], 10, 10
        elif case == 6:
            return [(5, 5, 5, 5)], [("row", 1, 2)], 10, 10
        elif case == 7:
            return [(1, 5, 10, 10)], [("row", 5, -2)], 10, 10
        else:
            return [(1, 1, 10, 10)], [("column", 5, 1), ("row", 3, -1)], 10, 10
    
    elif scale == "small":
        max_row = rng.randint(5, 30)
        max_col = rng.randint(5, 30)
        
        num_ranges = rng.randint(0, 5)
        ranges = []
        for _ in range(num_ranges):
            r1 = rng.randint(1, max_row)
            r2 = rng.randint(r1, max_row)
            c1 = rng.randint(1, max_col)
            c2 = rng.randint(c1, max_col)
            ranges.append((r1, c1, r2, c2))
        
        num_edits = rng.randint(0, 4)
        edits = []
        
        curr_rows = max_row
        curr_cols = max_col
        
        for _ in range(num_edits):
            axis = rng.choice(["row", "column"])
            if axis == "row":
                dim = curr_rows
                if rng.random() < 0.5 and dim > 1:
                    delete_count = rng.randint(1, min(2, dim))
                    index = rng.randint(1, dim - delete_count + 1)
                    delta = -delete_count
                    edits.append((axis, index, delta))
                    curr_rows -= delete_count
                else:
                    index = rng.randint(1, dim)
                    delta = rng.randint(1, 2)
                    edits.append((axis, index, delta))
                    curr_rows += delta
            else:
                dim = curr_cols
                if rng.random() < 0.5 and dim > 1:
                    delete_count = rng.randint(1, min(2, dim))
                    index = rng.randint(1, dim - delete_count + 1)
                    delta = -delete_count
                    edits.append((axis, index, delta))
                    curr_cols -= delete_count
                else:
                    index = rng.randint(1, dim)
                    delta = rng.randint(1, 2)
                    edits.append((axis, index, delta))
                    curr_cols += delta
        
        return ranges, edits, max_row, max_col
    
    else:  # medium
        max_row = rng.randint(50, 150)
        max_col = rng.randint(50, 150)
        
        num_ranges = rng.randint(5, 20)
        ranges = []
        for _ in range(num_ranges):
            r1 = rng.randint(1, max_row)
            r2 = rng.randint(r1, max_row)
            c1 = rng.randint(1, max_col)
            c2 = rng.randint(c1, max_col)
            ranges.append((r1, c1, r2, c2))
        
        num_edits = rng.randint(5, 20)
        edits = []
        
        curr_rows = max_row
        curr_cols = max_col
        
        for _ in range(num_edits):
            axis = rng.choice(["row", "column"])
            if axis == "row":
                dim = curr_rows
                if rng.random() < 0.5 and dim > 1:
                    delete_count = rng.randint(1, min(3, dim))
                    index = rng.randint(1, dim - delete_count + 1)
                    delta = -delete_count
                    edits.append((axis, index, delta))
                    curr_rows -= delete_count
                else:
                    index = rng.randint(1, dim)
                    delta = rng.randint(1, 3)
                    edits.append((axis, index, delta))
                    curr_rows += delta
            else:
                dim = curr_cols
                if rng.random() < 0.5 and dim > 1:
                    delete_count = rng.randint(1, min(3, dim))
                    index = rng.randint(1, dim - delete_count + 1)
                    delta = -delete_count
                    edits.append((axis, index, delta))
                    curr_cols -= delete_count
                else:
                    index = rng.randint(1, dim)
                    delta = rng.randint(1, 3)
                    edits.append((axis, index, delta))
                    curr_cols += delta
        
        return ranges, edits, max_row, max_col