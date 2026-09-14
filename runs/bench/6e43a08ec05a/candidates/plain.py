def normalize_protection(ranges, edits, max_row, max_col):
    current_ranges = [list(r) for r in ranges]
    
    for axis, index, delta in edits:
        new_ranges = []
        
        for r1, c1, r2, c2 in current_ranges:
            if axis == "row":
                if delta > 0:
                    if r2 < index:
                        new_ranges.append([r1, c1, r2, c2])
                    elif r1 >= index:
                        new_ranges.append([r1 + delta, c1, r2 + delta, c2])
                    else:
                        new_ranges.append([r1, c1, index - 1, c2])
                        new_ranges.append([index + delta, c1, r2 + delta, c2])
                else:
                    d = -delta
                    del_end = index + d - 1
                    
                    if r2 < index:
                        new_ranges.append([r1, c1, r2, c2])
                    elif r1 > del_end:
                        new_ranges.append([r1 - d, c1, r2 - d, c2])
                    else:
                        if r1 < index:
                            new_ranges.append([r1, c1, index - 1, c2])
                        if r2 > del_end:
                            new_ranges.append([index, c1, r2 - d, c2])
            
            elif axis == "column":
                if delta > 0:
                    if c2 < index:
                        new_ranges.append([r1, c1, r2, c2])
                    elif c1 >= index:
                        new_ranges.append([r1, c1 + delta, r2, c2 + delta])
                    else:
                        new_ranges.append([r1, c1, r2, index - 1])
                        new_ranges.append([r1, index + delta, r2, c2 + delta])
                else:
                    d = -delta
                    del_end = index + d - 1
                    
                    if c2 < index:
                        new_ranges.append([r1, c1, r2, c2])
                    elif c1 > del_end:
                        new_ranges.append([r1, c1 - d, r2, c2 - d])
                    else:
                        if c1 < index:
                            new_ranges.append([r1, c1, r2, index - 1])
                        if c2 > del_end:
                            new_ranges.append([r1, index, r2, c2 - d])
        
        current_ranges = new_ranges
    
    if not current_ranges:
        return []
    
    row_boundaries = set()
    for r1, c1, r2, c2 in current_ranges:
        row_boundaries.add(r1)
        row_boundaries.add(r2 + 1)
    
    row_boundaries = sorted(row_boundaries)
    
    row_segments = []
    for i in range(len(row_boundaries) - 1):
        r_start = row_boundaries[i]
        r_end = row_boundaries[i + 1] - 1
        
        col_intervals = []
        for r1, c1, r2, c2 in current_ranges:
            if r1 <= r_start and r_end <= r2:
                col_intervals.append((c1, c2))
        
        if col_intervals:
            col_intervals.sort()
            merged_cols = []
            for c1, c2 in col_intervals:
                if merged_cols and merged_cols[-1][1] >= c1 - 1:
                    merged_cols[-1] = (merged_cols[-1][0], max(merged_cols[-1][1], c2))
                else:
                    merged_cols.append((c1, c2))
            
            row_segments.append((r_start, r_end, tuple(merged_cols)))
    
    result = []
    i = 0
    while i < len(row_segments):
        r_start, r_end, cols = row_segments[i]
        
        j = i + 1
        while j < len(row_segments) and row_segments[j][2] == cols:
            next_start, next_end, _ = row_segments[j]
            if next_start == r_end + 1:
                r_end = next_end
                j += 1
            else:
                break
        
        for c1, c2 in cols:
            result.append((r_start, c1, r_end, c2))
        
        i = j
    
    result.sort()
    return result