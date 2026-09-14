def normalize_protection(ranges, edits, max_row, max_col):
    rects = [list(r) for r in ranges]
    
    for axis, index, delta in edits:
        new_rects = []
        for r1, c1, r2, c2 in rects:
            if axis == "row":
                if delta > 0:
                    if r2 < index:
                        new_rects.append([r1, c1, r2, c2])
                    elif r1 >= index:
                        nr2 = min(r2 + delta, max_row)
                        if r1 + delta <= max_row:
                            new_rects.append([r1 + delta, c1, nr2, c2])
                    else:
                        new_rects.append([r1, c1, index - 1, c2])
                        nr2 = min(r2 + delta, max_row)
                        if index + delta <= max_row:
                            new_rects.append([index + delta, c1, nr2, c2])
                else:
                    d = -delta
                    end = index + d - 1
                    if r2 < index:
                        new_rects.append([r1, c1, r2, c2])
                    elif r1 > end:
                        new_rects.append([r1 - d, c1, r2 - d, c2])
                    else:
                        if r1 < index:
                            new_rects.append([r1, c1, index - 1, c2])
                        if r2 > end:
                            new_rects.append([index, c1, r2 - d, c2])
            else:
                if delta > 0:
                    if c2 < index:
                        new_rects.append([r1, c1, r2, c2])
                    elif c1 >= index:
                        nc2 = min(c2 + delta, max_col)
                        if c1 + delta <= max_col:
                            new_rects.append([r1, c1 + delta, r2, nc2])
                    else:
                        new_rects.append([r1, c1, r2, index - 1])
                        nc2 = min(c2 + delta, max_col)
                        if index + delta <= max_col:
                            new_rects.append([r1, index + delta, r2, nc2])
                else:
                    d = -delta
                    end = index + d - 1
                    if c2 < index:
                        new_rects.append([r1, c1, r2, c2])
                    elif c1 > end:
                        new_rects.append([r1, c1 - d, r2, c2 - d])
                    else:
                        if c1 < index:
                            new_rects.append([r1, c1, r2, index - 1])
                        if c2 > end:
                            new_rects.append([r1, index, r2, c2 - d])
        rects = new_rects
    
    if not rects:
        return []
    
    events = []
    for r1, c1, r2, c2 in rects:
        events.append((r1, 0, c1, c2))
        events.append((r2 + 1, 1, c1, c2))
    
    events.sort()
    
    result = []
    active = set()
    prev_row = None
    prev_intervals = None
    
    i = 0
    while i < len(events):
        curr_row = events[i][0]
        
        if prev_intervals and curr_row > prev_row:
            for c1, c2 in prev_intervals:
                last_row = min(curr_row - 1, max_row)
                if last_row >= prev_row:
                    result.append((prev_row, c1, last_row, c2))
        
        if curr_row > max_row:
            break
        
        while i < len(events) and events[i][0] == curr_row:
            _, typ, c1, c2 = events[i]
            if typ == 0:
                active.add((c1, c2))
            else:
                active.discard((c1, c2))
            i += 1
        
        if active:
            sorted_active = sorted(active)
            merged = []
            for c1, c2 in sorted_active:
                if merged and merged[-1][1] >= c1 - 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
                else:
                    merged.append((c1, c2))
            curr_intervals = merged
        else:
            curr_intervals = None
        
        prev_row = curr_row
        prev_intervals = curr_intervals
    
    result.sort()
    return result