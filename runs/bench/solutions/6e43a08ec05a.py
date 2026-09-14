def normalize_protection(ranges, edits, max_row, max_col):
    rectangles = [list(r) for r in ranges]
    
    for axis, index, delta in edits:
        new_rectangles = []
        for r1, c1, r2, c2 in rectangles:
            if axis == "row":
                if delta > 0:
                    if r2 < index:
                        new_rectangles.append([r1, c1, r2, c2])
                    elif r1 >= index:
                        new_r1, new_r2 = r1 + delta, r2 + delta
                        if new_r1 <= max_row:
                            new_rectangles.append([new_r1, c1, min(new_r2, max_row), c2])
                    else:
                        new_rectangles.append([r1, c1, index - 1, c2])
                        new_r1, new_r2 = index + delta, r2 + delta
                        if new_r1 <= max_row:
                            new_rectangles.append([new_r1, c1, min(new_r2, max_row), c2])
                else:
                    d = -delta
                    if r2 < index:
                        new_rectangles.append([r1, c1, r2, c2])
                    elif r1 >= index + d:
                        new_rectangles.append([r1 - d, c1, r2 - d, c2])
                    elif r2 < index + d:
                        if r1 < index:
                            new_rectangles.append([r1, c1, index - 1, c2])
                    else:
                        if r1 < index:
                            new_rectangles.append([r1, c1, index - 1, c2])
                        new_rectangles.append([index, c1, r2 - d, c2])
            else:
                if delta > 0:
                    if c2 < index:
                        new_rectangles.append([r1, c1, r2, c2])
                    elif c1 >= index:
                        new_c1, new_c2 = c1 + delta, c2 + delta
                        if new_c1 <= max_col:
                            new_rectangles.append([r1, new_c1, r2, min(new_c2, max_col)])
                    else:
                        new_rectangles.append([r1, c1, r2, index - 1])
                        new_c1, new_c2 = index + delta, c2 + delta
                        if new_c1 <= max_col:
                            new_rectangles.append([r1, new_c1, r2, min(new_c2, max_col)])
                else:
                    d = -delta
                    if c2 < index:
                        new_rectangles.append([r1, c1, r2, c2])
                    elif c1 >= index + d:
                        new_rectangles.append([r1, c1 - d, r2, c2 - d])
                    elif c2 < index + d:
                        if c1 < index:
                            new_rectangles.append([r1, c1, r2, index - 1])
                    else:
                        if c1 < index:
                            new_rectangles.append([r1, c1, r2, index - 1])
                        new_rectangles.append([r1, index, r2, c2 - d])
        rectangles = new_rectangles
    
    if not rectangles:
        return []
    
    critical_rows = set()
    for r1, c1, r2, c2 in rectangles:
        critical_rows.add(r1)
        critical_rows.add(r2 + 1)
    
    critical_rows = sorted(critical_rows)
    row_ranges = []
    
    for i in range(len(critical_rows) - 1):
        row_start, row_end = critical_rows[i], critical_rows[i + 1] - 1
        intervals = []
        for r1, c1, r2, c2 in rectangles:
            if r1 <= row_start and row_end <= r2:
                intervals.append((c1, c2))
        
        if intervals:
            intervals.sort()
            merged = []
            for c1, c2 in intervals:
                if merged and merged[-1][1] >= c1 - 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
                else:
                    merged.append((c1, c2))
            row_ranges.append((row_start, row_end, tuple(merged)))
    
    if not row_ranges:
        return []
    
    result = []
    current_start, current_end, current_intervals = row_ranges[0][0], row_ranges[0][1], row_ranges[0][2]
    
    for row_start, row_end, intervals in row_ranges[1:]:
        if intervals == current_intervals and row_start == current_end + 1:
            current_end = row_end
        else:
            for c1, c2 in current_intervals:
                result.append((current_start, c1, current_end, c2))
            current_start, current_end, current_intervals = row_start, row_end, intervals
    
    for c1, c2 in current_intervals:
        result.append((current_start, c1, current_end, c2))
    
    result.sort()
    return result