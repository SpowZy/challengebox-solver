def normalize_protection(ranges, edits, max_row, max_col):
    def transform_rect(rect, axis, index, delta, max_row, max_col):
        r1, c1, r2, c2 = rect
        
        if axis == "row":
            if delta > 0:  # Insert delta rows before index
                if r2 < index:
                    return [rect]
                elif r1 >= index:
                    new_r1 = r1 + delta
                    new_r2 = r2 + delta
                    if new_r1 > max_row:
                        return []
                    new_r2 = min(new_r2, max_row)
                    return [(new_r1, c1, new_r2, c2)]
                else:
                    result = [(r1, c1, index - 1, c2)]
                    new_r1 = index + delta
                    new_r2 = r2 + delta
                    if new_r1 <= max_row:
                        new_r2 = min(new_r2, max_row)
                        result.append((new_r1, c1, new_r2, c2))
                    return result
            else:  # Delete rows [index, index-delta)
                d = -delta
                end = index + d
                if r2 < index:
                    return [rect]
                elif r1 >= end:
                    return [(r1 - d, c1, r2 - d, c2)]
                elif r1 < index and r2 >= end:
                    return [(r1, c1, index - 1, c2), (index, c1, r2 - d, c2)]
                elif r1 < index and r2 < end:
                    return [(r1, c1, index - 1, c2)]
                elif r1 >= index and r1 < end and r2 >= end:
                    return [(index, c1, r2 - d, c2)]
                else:
                    return []
        else:  # axis == "column"
            if delta > 0:  # Insert delta columns before index
                if c2 < index:
                    return [rect]
                elif c1 >= index:
                    new_c1 = c1 + delta
                    new_c2 = c2 + delta
                    if new_c1 > max_col:
                        return []
                    new_c2 = min(new_c2, max_col)
                    return [(r1, new_c1, r2, new_c2)]
                else:
                    result = [(r1, c1, r2, index - 1)]
                    new_c1 = index + delta
                    new_c2 = c2 + delta
                    if new_c1 <= max_col:
                        new_c2 = min(new_c2, max_col)
                        result.append((r1, new_c1, r2, new_c2))
                    return result
            else:  # Delete columns [index, index-delta)
                d = -delta
                end = index + d
                if c2 < index:
                    return [rect]
                elif c1 >= end:
                    return [(r1, c1 - d, r2, c2 - d)]
                elif c1 < index and c2 >= end:
                    return [(r1, c1, r2, index - 1), (r1, index, r2, c2 - d)]
                elif c1 < index and c2 < end:
                    return [(r1, c1, r2, index - 1)]
                elif c1 >= index and c1 < end and c2 >= end:
                    return [(r1, index, r2, c2 - d)]
                else:
                    return []
    
    rectangles = list(ranges)
    for axis, index, delta in edits:
        new_rectangles = []
        for rect in rectangles:
            new_rectangles.extend(transform_rect(rect, axis, index, delta, max_row, max_col))
        rectangles = new_rectangles
    
    if not rectangles:
        return []
    
    critical_rows = set()
    for r1, c1, r2, c2 in rectangles:
        critical_rows.add(r1)
        critical_rows.add(r2 + 1)
    
    critical_rows = sorted([r for r in critical_rows if r <= max_row])
    
    if not critical_rows:
        return []
    
    row_intervals = {}
    for row in critical_rows:
        col_ranges = []
        for r1, c1, r2, c2 in rectangles:
            if r1 <= row <= r2:
                col_ranges.append((c1, c2))
        
        if col_ranges:
            col_ranges.sort()
            merged = []
            for c1, c2 in col_ranges:
                if merged and merged[-1][1] >= c1 - 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
                else:
                    merged.append((c1, c2))
            row_intervals[row] = tuple(merged)
        else:
            row_intervals[row] = ()
    
    result = []
    i = 0
    while i < len(critical_rows):
        current_row = critical_rows[i]
        current_intervals = row_intervals[current_row]
        
        if not current_intervals:
            i += 1
            continue
        
        j = i + 1
        while j < len(critical_rows) and row_intervals[critical_rows[j]] == current_intervals:
            j += 1
        
        last_row = critical_rows[j] - 1 if j < len(critical_rows) else max_row
        
        for c1, c2 in current_intervals:
            result.append((current_row, c1, last_row, c2))
        
        i = j
    
    result.sort()
    return result