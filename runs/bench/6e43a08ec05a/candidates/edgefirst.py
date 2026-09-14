def normalize_protection(ranges, edits, max_row, max_col):
    rects = list(ranges)
    
    # Apply all edits to rectangles
    for axis, index, delta in edits:
        new_rects = []
        for r1, c1, r2, c2 in rects:
            if axis == "row":
                if delta > 0:  # Insert delta unprotected rows before index
                    if r2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif r1 >= index:
                        new_rects.append((r1 + delta, c1, r2 + delta, c2))
                    else:
                        new_rects.append((r1, c1, index - 1, c2))
                        new_rects.append((index + delta, c1, r2 + delta, c2))
                else:  # Delete -delta rows starting at index
                    d = -delta
                    end = index + d
                    if r1 < index:
                        new_rects.append((r1, c1, min(r2, index - 1), c2))
                    if r2 >= end:
                        new_rects.append((max(r1, end) - d, c1, r2 - d, c2))
            else:  # axis == "column"
                if delta > 0:  # Insert delta unprotected columns before index
                    if c2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif c1 >= index:
                        new_rects.append((r1, c1 + delta, r2, c2 + delta))
                    else:
                        new_rects.append((r1, c1, r2, index - 1))
                        new_rects.append((r1, index + delta, r2, c2 + delta))
                else:  # Delete -delta columns starting at index
                    d = -delta
                    end = index + d
                    if c1 < index:
                        new_rects.append((r1, c1, r2, min(c2, index - 1)))
                    if c2 >= end:
                        new_rects.append((r1, max(c1, end) - d, r2, c2 - d))
        rects = new_rects
    
    if not rects:
        return []
    
    # Collect all row boundary events
    row_boundaries = set()
    for r1, c1, r2, c2 in rects:
        row_boundaries.add(r1)
        row_boundaries.add(r2 + 1)
    
    row_boundaries = sorted(row_boundaries)
    result = []
    
    # For each segment between consecutive row boundaries
    for i in range(len(row_boundaries) - 1):
        segment_start = row_boundaries[i]
        segment_end = row_boundaries[i + 1] - 1
        
        # Find all rectangles covering this entire row segment
        col_intervals = []
        for r1, c1, r2, c2 in rects:
            if r1 <= segment_start and segment_end <= r2:
                col_intervals.append((c1, c2))
        
        if col_intervals:
            # Merge overlapping and touching column intervals
            col_intervals.sort()
            merged = []
            for c1, c2 in col_intervals:
                if merged and merged[-1][1] >= c1 - 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
                else:
                    merged.append((c1, c2))
            
            # Create canonical rectangles
            for c1, c2 in merged:
                result.append((segment_start, c1, segment_end, c2))
    
    result.sort()
    return result