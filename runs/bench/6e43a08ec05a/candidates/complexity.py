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
                        new_rects.append((r1 + delta, c1, r2 + delta, c2))
                    else:
                        new_rects.append((r1, c1, index - 1, c2))
                        new_rects.append((index + delta, c1, r2 + delta, c2))
            else:
                d = -delta
                end = index + d
                for r1, c1, r2, c2 in rects:
                    if r2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif r1 >= end:
                        new_rects.append((r1 - d, c1, r2 - d, c2))
                    elif r2 >= end:
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
                        new_rects.append((r1, c1 + delta, r2, c2 + delta))
                    else:
                        new_rects.append((r1, c1, r2, index - 1))
                        new_rects.append((r1, index + delta, r2, c2 + delta))
            else:
                d = -delta
                end = index + d
                for r1, c1, r2, c2 in rects:
                    if c2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif c1 >= end:
                        new_rects.append((r1, c1 - d, r2, c2 - d))
                    elif c2 >= end:
                        if c1 < index:
                            new_rects.append((r1, c1, r2, index - 1))
                        new_rects.append((r1, index, r2, c2 - d))
                    elif c1 < index:
                        new_rects.append((r1, c1, r2, index - 1))
        rects = new_rects
    
    valid = []
    for r1, c1, r2, c2 in rects:
        r1, c1 = max(r1, 1), max(c1, 1)
        r2, c2 = min(r2, max_row), min(c2, max_col)
        if r1 <= r2 and c1 <= c2:
            valid.append((r1, c1, r2, c2))
    
    if not valid:
        return []
    
    boundaries = set()
    for r1, c1, r2, c2 in valid:
        boundaries.add(r1)
        boundaries.add(r2 + 1)
    boundaries = sorted(boundaries)
    
    interval_map = {}
    for i in range(len(boundaries) - 1):
        r_start = boundaries[i]
        r_end = boundaries[i + 1] - 1
        
        intervals = []
        for r1, c1, r2, c2 in valid:
            if r1 <= r_start and r_end <= r2:
                intervals.append((c1, c2))
        
        if intervals:
            intervals.sort()
            merged = []
            for c1, c2 in intervals:
                if merged and merged[-1][1] >= c1 - 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
                else:
                    merged.append((c1, c2))
            interval_map[(r_start, r_end)] = tuple(merged)
    
    result = []
    sorted_pairs = sorted(interval_map.keys())
    
    i = 0
    while i < len(sorted_pairs):
        r_start, r_end = sorted_pairs[i]
        intervals = interval_map[(r_start, r_end)]
        
        j = i + 1
        while j < len(sorted_pairs):
            r_start_j, r_end_j = sorted_pairs[j]
            if r_start_j == r_end + 1 and interval_map[(r_start_j, r_end_j)] == intervals:
                r_end = r_end_j
                j += 1
            else:
                break
        
        for c1, c2 in intervals:
            result.append((r_start, c1, r_end, c2))
        
        i = j
    
    result.sort()
    return result