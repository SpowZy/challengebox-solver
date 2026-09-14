def normalize_protection(ranges, edits, max_row, max_col):
    current_ranges = [list(r) for r in ranges]
    
    # Apply all edits in order
    for axis, index, delta in edits:
        new_ranges = []
        
        for r1, c1, r2, c2 in current_ranges:
            if axis == "row":
                if delta > 0:  # Insert delta rows before index
                    if r2 < index:
                        new_ranges.append([r1, c1, r2, c2])
                    elif r1 >= index:
                        if r1 + delta <= max_row:
                            new_ranges.append([r1 + delta, c1, min(r2 + delta, max_row), c2])
                    else:
                        # Rectangle spans insertion point
                        new_ranges.append([r1, c1, index - 1, c2])
                        if index + delta <= max_row:
                            new_ranges.append([index + delta, c1, min(r2 + delta, max_row), c2])
                else:
                    # Delete rows [index, index - delta)
                    d = -delta
                    if r2 < index:
                        new_ranges.append([r1, c1, r2, c2])
                    elif r1 >= index + d:
                        new_ranges.append([r1 - d, c1, r2 - d, c2])
                    else:
                        if r1 < index:
                            new_ranges.append([r1, c1, index - 1, c2])
                        if r2 >= index + d:
                            new_ranges.append([index, c1, r2 - d, c2])
            else:  # axis == "column"
                if delta > 0:  # Insert delta columns before index
                    if c2 < index:
                        new_ranges.append([r1, c1, r2, c2])
                    elif c1 >= index:
                        if c1 + delta <= max_col:
                            new_ranges.append([r1, c1 + delta, r2, min(c2 + delta, max_col)])
                    else:
                        new_ranges.append([r1, c1, r2, index - 1])
                        if index + delta <= max_col:
                            new_ranges.append([r1, index + delta, r2, min(c2 + delta, max_col)])
                else:
                    # Delete columns [index, index - delta)
                    d = -delta
                    if c2 < index:
                        new_ranges.append([r1, c1, r2, c2])
                    elif c1 >= index + d:
                        new_ranges.append([r1, c1 - d, r2, c2 - d])
                    else:
                        if c1 < index:
                            new_ranges.append([r1, c1, r2, index - 1])
                        if c2 >= index + d:
                            new_ranges.append([r1, index, r2, c2 - d])
        
        current_ranges = new_ranges
    
    if not current_ranges:
        return []
    
    # Collect row boundaries where covering rectangles change
    boundaries = set()
    for r1, c1, r2, c2 in current_ranges:
        boundaries.add(r1)
        boundaries.add(r2 + 1)
    
    boundaries = sorted(boundaries)
    
    # For each row segment, compute maximal column intervals
    row_to_intervals = {}
    
    for i in range(len(boundaries) - 1):
        seg_start = boundaries[i]
        seg_end = boundaries[i + 1] - 1
        
        covering = []
        for r1, c1, r2, c2 in current_ranges:
            if r1 <= seg_start and seg_end <= r2:
                covering.append((c1, c2))
        
        if not covering:
            continue
        
        # Merge overlapping/touching column intervals
        covering.sort()
        merged = []
        for c1, c2 in covering:
            if merged and merged[-1][1] >= c1 - 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
            else:
                merged.append((c1, c2))
        
        row_to_intervals[(seg_start, seg_end)] = tuple(merged)
    
    # Group consecutive row ranges with the same intervals
    interval_to_ranges = {}
    for (seg_start, seg_end), intervals in row_to_intervals.items():
        if intervals not in interval_to_ranges:
            interval_to_ranges[intervals] = []
        interval_to_ranges[intervals].append((seg_start, seg_end))
    
    result = []
    for intervals in sorted(interval_to_ranges.keys()):
        ranges_list = sorted(interval_to_ranges[intervals])
        
        # Merge consecutive row ranges
        merged_rows = []
        for seg_start, seg_end in ranges_list:
            if merged_rows and merged_rows[-1][1] == seg_start - 1:
                merged_rows[-1] = (merged_rows[-1][0], seg_end)
            else:
                merged_rows.append((seg_start, seg_end))
        
        for r1, r2 in merged_rows:
            for c1, c2 in intervals:
                result.append((r1, c1, r2, c2))
    
    result.sort()
    return result