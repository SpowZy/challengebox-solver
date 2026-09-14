def normalize_protection(ranges, edits, max_row, max_col):
    rects = list(ranges)
    
    for axis, index, delta in edits:
        new_rects = []
        
        if axis == "row":
            if delta > 0:
                for r1, c1, r2, c2 in rects:
                    if r2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif r1 >= index:
                        if r1 + delta <= max_row:
                            new_rects.append((r1 + delta, c1, min(r2 + delta, max_row), c2))
                    else:
                        new_rects.append((r1, c1, index - 1, c2))
                        if index + delta <= max_row:
                            new_rects.append((index + delta, c1, min(r2 + delta, max_row), c2))
            else:
                d = -delta
                for r1, c1, r2, c2 in rects:
                    if r2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif r1 >= index + d:
                        new_rects.append((r1 - d, c1, r2 - d, c2))
                    elif r2 >= index + d:
                        if r1 < index:
                            new_rects.append((r1, c1, index - 1, c2))
                        new_rects.append((index, c1, r2 - d, c2))
                    elif r1 < index:
                        new_rects.append((r1, c1, index - 1, c2))
        else:
            if delta > 0:
                for r1, c1, r2, c2 in rects:
                    if c2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif c1 >= index:
                        if c1 + delta <= max_col:
                            new_rects.append((r1, c1 + delta, r2, min(c2 + delta, max_col)))
                    else:
                        new_rects.append((r1, c1, r2, index - 1))
                        if index + delta <= max_col:
                            new_rects.append((r1, index + delta, r2, min(c2 + delta, max_col)))
            else:
                d = -delta
                for r1, c1, r2, c2 in rects:
                    if c2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif c1 >= index + d:
                        new_rects.append((r1, c1 - d, r2, c2 - d))
                    elif c2 >= index + d:
                        if c1 < index:
                            new_rects.append((r1, c1, r2, index - 1))
                        new_rects.append((r1, index, r2, c2 - d))
                    elif c1 < index:
                        new_rects.append((r1, c1, r2, index - 1))
        
        rects = new_rects
    
    if not rects:
        return []
    
    row_boundaries = set()
    for r1, c1, r2, c2 in rects:
        row_boundaries.add(r1)
        row_boundaries.add(r2 + 1)
    
    row_boundaries = sorted(row_boundaries)
    
    row_segments = []
    for i in range(len(row_boundaries) - 1):
        r_start = row_boundaries[i]
        r_end = row_boundaries[i + 1] - 1
        
        if r_end < 1 or r_start > max_row:
            continue
        
        r_start = max(r_start, 1)
        r_end = min(r_end, max_row)
        
        if r_start > r_end:
            continue
        
        col_intervals = []
        for r1, c1, r2, c2 in rects:
            if r1 <= r_start and r_start <= r2:
                col_intervals.append((c1, c2))
        
        if col_intervals:
            col_intervals.sort()
            merged = []
            for c1, c2 in col_intervals:
                if merged and merged[-1][1] >= c1 - 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
                else:
                    merged.append((c1, c2))
            
            row_segments.append((r_start, r_end, tuple(merged)))
    
    result = []
    if row_segments:
        current_r_start, current_r_end, current_intervals = row_segments[0]
        
        for i in range(1, len(row_segments)):
            r_start, r_end, intervals = row_segments[i]
            
            if intervals == current_intervals and r_start == current_r_end + 1:
                current_r_end = r_end
            else:
                for c1, c2 in current_intervals:
                    result.append((current_r_start, c1, current_r_end, c2))
                current_r_start = r_start
                current_r_end = r_end
                current_intervals = intervals
        
        for c1, c2 in current_intervals:
            result.append((current_r_start, c1, current_r_end, c2))
    
    result.sort()
    return result