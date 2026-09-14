def normalize_protection(ranges, edits, max_row, max_col):
    if not ranges:
        return []
    
    rects = [list(r) for r in ranges]
    
    # Apply each edit in order
    for axis, index, delta in edits:
        new_rects = []
        for r1, c1, r2, c2 in rects:
            if axis == "row":
                if delta > 0:  # Insert delta rows before index
                    if r2 < index:
                        new_rects.append([r1, c1, r2, c2])
                    elif r1 >= index:
                        nr1, nr2 = r1 + delta, r2 + delta
                        if nr1 <= max_row:
                            nr2 = min(nr2, max_row)
                            new_rects.append([nr1, c1, nr2, c2])
                    else:
                        new_rects.append([r1, c1, index - 1, c2])
                        nr1, nr2 = index + delta, r2 + delta
                        if nr1 <= max_row:
                            nr2 = min(nr2, max_row)
                            new_rects.append([nr1, c1, nr2, c2])
                else:  # Delete -delta rows starting at index
                    d = -delta
                    if r2 < index:
                        new_rects.append([r1, c1, r2, c2])
                    elif r1 >= index + d:
                        new_rects.append([r1 - d, c1, r2 - d, c2])
                    else:
                        if r1 < index:
                            new_rects.append([r1, c1, index - 1, c2])
                        if r2 >= index + d:
                            new_rects.append([index, c1, r2 - d, c2])
            else:  # axis == "column"
                if delta > 0:  # Insert delta columns before index
                    if c2 < index:
                        new_rects.append([r1, c1, r2, c2])
                    elif c1 >= index:
                        nc1, nc2 = c1 + delta, c2 + delta
                        if nc1 <= max_col:
                            nc2 = min(nc2, max_col)
                            new_rects.append([r1, nc1, r2, nc2])
                    else:
                        new_rects.append([r1, c1, r2, index - 1])
                        nc1, nc2 = index + delta, c2 + delta
                        if nc1 <= max_col:
                            nc2 = min(nc2, max_col)
                            new_rects.append([r1, nc1, r2, nc2])
                else:  # Delete -delta columns starting at index
                    d = -delta
                    if c2 < index:
                        new_rects.append([r1, c1, r2, c2])
                    elif c1 >= index + d:
                        new_rects.append([r1, c1 - d, r2, c2 - d])
                    else:
                        if c1 < index:
                            new_rects.append([r1, c1, r2, index - 1])
                        if c2 >= index + d:
                            new_rects.append([r1, index, r2, c2 - d])
        rects = new_rects
    
    # Filter invalid rectangles
    rects = [tuple(r) for r in rects if r[0] <= r[2] and r[1] <= r[3]]
    
    if not rects:
        return []
    
    # Convert to canonical row-run form using sweep line
    row_breaks = set()
    for r1, c1, r2, c2 in rects:
        row_breaks.add(r1)
        row_breaks.add(r2 + 1)
    row_breaks = sorted(row_breaks)
    
    result = []
    
    # Process each row interval between breakpoints
    for i in range(len(row_breaks) - 1):
        r_start = row_breaks[i]
        r_end = row_breaks[i + 1] - 1
        
        # Find rectangles that completely cover [r_start, r_end]
        active = [r for r in rects if r[0] <= r_start and r_end <= r[2]]
        
        if not active:
            continue
        
        # Extract column intervals and merge overlapping ones
        col_intervals = [(r[1], r[3]) for r in active]
        col_intervals.sort()
        
        merged = []
        for c1, c2 in col_intervals:
            if merged and c1 <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
            else:
                merged.append((c1, c2))
        
        # Add canonical rectangles
        for c1, c2 in merged:
            result.append((r_start, c1, r_end, c2))
    
    result.sort()
    return result