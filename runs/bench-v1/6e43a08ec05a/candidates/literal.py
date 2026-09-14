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
                        new_r1, new_r2 = r1 + delta, min(r2 + delta, max_row)
                        if new_r1 <= max_row:
                            new_rects.append((new_r1, c1, new_r2, c2))
                    else:
                        new_rects.append((r1, c1, index - 1, c2))
                        new_r1, new_r2 = index + delta, min(r2 + delta, max_row)
                        if new_r1 <= max_row:
                            new_rects.append((new_r1, c1, new_r2, c2))
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
                        new_c1, new_c2 = c1 + delta, min(c2 + delta, max_col)
                        if new_c1 <= max_col:
                            new_rects.append((r1, new_c1, r2, new_c2))
                    else:
                        new_rects.append((r1, c1, r2, index - 1))
                        new_c1, new_c2 = index + delta, min(c2 + delta, max_col)
                        if new_c1 <= max_col:
                            new_rects.append((r1, new_c1, r2, new_c2))
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
    
    row_boundaries = sorted([b for b in row_boundaries if b <= max_row])
    
    result_rects_by_interval = {}
    
    for i in range(len(row_boundaries) - 1):
        start_row = row_boundaries[i]
        end_row = row_boundaries[i + 1] - 1
        
        intervals = []
        for r1, c1, r2, c2 in rects:
            if r1 <= start_row and end_row <= r2:
                intervals.append((c1, c2))
        
        if not intervals:
            continue
        
        intervals.sort()
        merged = []
        s, e = intervals[0]
        for start, end in intervals[1:]:
            if start <= e + 1:
                e = max(e, end)
            else:
                merged.append((s, e))
                s, e = start, end
        merged.append((s, e))
        
        for c1, c2 in merged:
            if (c1, c2) not in result_rects_by_interval:
                result_rects_by_interval[(c1, c2)] = []
            result_rects_by_interval[(c1, c2)].append((start_row, end_row))
    
    result = []
    for (c1, c2), row_spans in result_rects_by_interval.items():
        row_spans.sort()
        
        i = 0
        while i < len(row_spans):
            start_row, end_row = row_spans[i]
            j = i + 1
            while j < len(row_spans) and row_spans[j][0] == end_row + 1:
                end_row = row_spans[j][1]
                j += 1
            
            result.append((start_row, c1, end_row, c2))
            i = j
    
    result.sort()
    return result