def normalize_protection(ranges, edits, max_row, max_col):
    from collections import defaultdict
    
    rectangles = list(ranges)
    
    # Apply edits to rectangles
    for axis, index, delta in edits:
        new_rects = []
        for r1, c1, r2, c2 in rectangles:
            if axis == "row":
                if delta > 0:
                    # Insert delta rows before index
                    if r2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif r1 >= index:
                        new_rects.append((r1 + delta, c1, r2 + delta, c2))
                    else:
                        new_rects.append((r1, c1, index - 1, c2))
                        new_rects.append((index + delta, c1, r2 + delta, c2))
                else:
                    # Delete -delta rows starting at index
                    d = -delta
                    del_end = index + d
                    if r2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif r1 >= del_end:
                        new_rects.append((r1 - d, c1, r2 - d, c2))
                    elif r2 < del_end:
                        if r1 < index:
                            new_rects.append((r1, c1, index - 1, c2))
                    else:
                        if r1 < index:
                            new_rects.append((r1, c1, index - 1, c2))
                        new_rects.append((index, c1, r2 - d, c2))
            else:
                if delta > 0:
                    # Insert delta columns before index
                    if c2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif c1 >= index:
                        new_rects.append((r1, c1 + delta, r2, c2 + delta))
                    else:
                        new_rects.append((r1, c1, r2, index - 1))
                        new_rects.append((r1, index + delta, r2, c2 + delta))
                else:
                    # Delete -delta columns starting at index
                    d = -delta
                    del_end = index + d
                    if c2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif c1 >= del_end:
                        new_rects.append((r1, c1 - d, r2, c2 - d))
                    elif c2 < del_end:
                        if c1 < index:
                            new_rects.append((r1, c1, r2, index - 1))
                    else:
                        if c1 < index:
                            new_rects.append((r1, c1, r2, index - 1))
                        new_rects.append((r1, index, r2, c2 - d))
        rectangles = new_rects
    
    # Clip to worksheet bounds
    clipped = []
    for r1, c1, r2, c2 in rectangles:
        if r1 > max_row or r2 < 1 or c1 > max_col or c2 < 1:
            continue
        r1 = max(1, r1)
        r2 = min(max_row, r2)
        c1 = max(1, c1)
        c2 = min(max_col, c2)
        if r1 <= r2 and c1 <= c2:
            clipped.append((r1, c1, r2, c2))
    
    if not clipped:
        return []
    
    # Build row interval events
    row_events = set()
    for r1, c1, r2, c2 in clipped:
        row_events.add(r1)
        row_events.add(r2 + 1)
    row_events = sorted(row_events)
    
    # For each row interval, find protected column intervals
    intermediate = []
    for i in range(len(row_events) - 1):
        row_start = row_events[i]
        row_end = row_events[i + 1] - 1
        
        col_intervals = []
        for r1, c1, r2, c2 in clipped:
            if r1 <= row_start and row_end <= r2:
                col_intervals.append((c1, c2))
        
        if col_intervals:
            col_intervals.sort()
            merged = []
            for c1, c2 in col_intervals:
                if merged and c1 <= merged[-1][1] + 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
                else:
                    merged.append((c1, c2))
            for c1, c2 in merged:
                intermediate.append((row_start, row_end, c1, c2))
    
    # Group by column interval and merge consecutive rows
    by_col = defaultdict(list)
    for row_start, row_end, c1, c2 in intermediate:
        by_col[(c1, c2)].append((row_start, row_end))
    
    result = []
    for (c1, c2) in sorted(by_col.keys()):
        row_ranges = sorted(by_col[(c1, c2)])
        merged_rows = []
        for row_start, row_end in row_ranges:
            if merged_rows and row_start == merged_rows[-1][1] + 1:
                merged_rows[-1] = (merged_rows[-1][0], row_end)
            else:
                merged_rows.append((row_start, row_end))
        for row_start, row_end in merged_rows:
            result.append((row_start, c1, row_end, c2))
    
    result.sort()
    return result