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
                for r1, c1, r2, c2 in rects:
                    if r2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif r1 >= index + d:
                        new_rects.append((r1 - d, c1, r2 - d, c2))
                    else:
                        if r1 < index:
                            new_rects.append((r1, c1, index - 1, c2))
                        if r2 >= index + d:
                            new_rects.append((index, c1, r2 - d, c2))
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
                for r1, c1, r2, c2 in rects:
                    if c2 < index:
                        new_rects.append((r1, c1, r2, c2))
                    elif c1 >= index + d:
                        new_rects.append((r1, c1 - d, r2, c2 - d))
                    else:
                        if c1 < index:
                            new_rects.append((r1, c1, r2, index - 1))
                        if c2 >= index + d:
                            new_rects.append((r1, index, r2, c2 - d))
        
        rects = new_rects
    
    if not rects:
        return []
    
    row_events = {}
    for r1, c1, r2, c2 in rects:
        if r1 not in row_events:
            row_events[r1] = {'start': [], 'end': []}
        row_events[r1]['start'].append((c1, c2))
        if r2 + 1 not in row_events:
            row_events[r2 + 1] = {'start': [], 'end': []}
        row_events[r2 + 1]['end'].append((c1, c2))
    
    sorted_rows = sorted(row_events.keys())
    result = []
    
    current_intervals = {}
    current_row_start = None
    last_row = None
    
    for row in sorted_rows:
        for c1, c2 in row_events[row]['end']:
            current_intervals[(c1, c2)] = current_intervals.get((c1, c2), 0) - 1
            if current_intervals[(c1, c2)] == 0:
                del current_intervals[(c1, c2)]
        
        for c1, c2 in row_events[row]['start']:
            current_intervals[(c1, c2)] = current_intervals.get((c1, c2), 0) + 1
        
        if current_intervals:
            merged = []
            for c1, c2 in sorted(current_intervals.keys()):
                if merged and merged[-1][1] >= c1 - 1:
                    merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
                else:
                    merged.append((c1, c2))
            
            if current_row_start is None:
                current_row_start = row
                current_merged = merged
                last_row = row
            elif merged == current_merged:
                last_row = row
            else:
                for c1, c2 in current_merged:
                    result.append((current_row_start, c1, last_row, c2))
                current_row_start = row
                current_merged = merged
                last_row = row
        else:
            if current_row_start is not None:
                for c1, c2 in current_merged:
                    result.append((current_row_start, c1, last_row, c2))
                current_row_start = None
                last_row = None
    
    result.sort()
    return result