def normalize_protection(ranges, edits, max_row, max_col):
    # Apply edits to ranges
    active_ranges = list(ranges)
    
    for axis, index, delta in edits:
        new_ranges = []
        
        if axis == "row":
            for r1, c1, r2, c2 in active_ranges:
                if delta > 0:
                    # Insert delta unprotected rows before index
                    if r2 < index:
                        new_ranges.append((r1, c1, r2, c2))
                    elif r1 >= index:
                        new_ranges.append((r1 + delta, c1, r2 + delta, c2))
                    else:
                        # Split range at insertion point
                        new_ranges.append((r1, c1, index - 1, c2))
                        new_ranges.append((index + delta, c1, r2 + delta, c2))
                else:
                    # Delete abs(delta) rows starting at index
                    d = -delta
                    delete_end = index + d - 1
                    if r2 < index:
                        new_ranges.append((r1, c1, r2, c2))
                    elif r1 > delete_end:
                        new_ranges.append((r1 - d, c1, r2 - d, c2))
                    else:
                        if r1 < index:
                            new_ranges.append((r1, c1, index - 1, c2))
                        if r2 > delete_end:
                            new_ranges.append((delete_end + 1 - d, c1, r2 - d, c2))
        
        elif axis == "column":
            for r1, c1, r2, c2 in active_ranges:
                if delta > 0:
                    # Insert delta unprotected columns before index
                    if c2 < index:
                        new_ranges.append((r1, c1, r2, c2))
                    elif c1 >= index:
                        new_ranges.append((r1, c1 + delta, r2, c2 + delta))
                    else:
                        # Split range at insertion point
                        new_ranges.append((r1, c1, r2, index - 1))
                        new_ranges.append((r1, index + delta, r2, c2 + delta))
                else:
                    # Delete abs(delta) columns starting at index
                    d = -delta
                    delete_end = index + d - 1
                    if c2 < index:
                        new_ranges.append((r1, c1, r2, c2))
                    elif c1 > delete_end:
                        new_ranges.append((r1, c1 - d, r2, c2 - d))
                    else:
                        if c1 < index:
                            new_ranges.append((r1, c1, r2, index - 1))
                        if c2 > delete_end:
                            new_ranges.append((r1, delete_end + 1 - d, r2, c2 - d))
        
        active_ranges = new_ranges
    
    if not active_ranges:
        return []
    
    # Find row event boundaries
    row_events = set()
    for r1, c1, r2, c2 in active_ranges:
        row_events.add(r1)
        row_events.add(r2 + 1)
    
    row_events = sorted(row_events)
    
    # For each row segment, compute merged column intervals
    segment_intervals = {}
    
    for i in range(len(row_events) - 1):
        row_start = row_events[i]
        row_end = row_events[i + 1] - 1
        
        # Find column intervals that apply to this entire row segment
        col_intervals = []
        for r1, c1, r2, c2 in active_ranges:
            if r1 <= row_start and row_end <= r2:
                col_intervals.append((c1, c2))
        
        if not col_intervals:
            continue
        
        # Merge overlapping and touching intervals
        col_intervals.sort()
        merged = [col_intervals[0]]
        for c1, c2 in col_intervals[1:]:
            if c1 <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
            else:
                merged.append((c1, c2))
        
        segment_intervals[(row_start, row_end)] = tuple(merged)
    
    # Group consecutive row segments with identical column interval sets
    segments = sorted(segment_intervals.keys())
    result = []
    
    i = 0
    while i < len(segments):
        row_start, row_end = segments[i]
        intervals = segment_intervals[(row_start, row_end)]
        first_row = row_start
        last_row = row_end
        
        # Find consecutive segments with same intervals
        j = i + 1
        while j < len(segments):
            next_row_start, next_row_end = segments[j]
            if next_row_start == last_row + 1 and segment_intervals[segments[j]] == intervals:
                last_row = next_row_end
                j += 1
            else:
                break
        
        # Create output rectangles for this group
        for c1, c2 in intervals:
            result.append((first_row, c1, last_row, c2))
        
        i = j
    
    result.sort()
    return result