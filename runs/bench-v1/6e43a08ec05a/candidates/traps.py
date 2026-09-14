def normalize_protection(ranges, edits, max_row, max_col):
    def apply_row_edit(rect, index, delta):
        r1, c1, r2, c2 = rect
        if delta > 0:
            if r2 < index:
                return [rect]
            elif r1 >= index:
                return [(r1 + delta, c1, r2 + delta, c2)]
            else:
                return [(r1, c1, index - 1, c2), (index + delta, c1, r2 + delta, c2)]
        else:
            d = -delta
            if r2 < index:
                return [rect]
            elif r1 >= index + d:
                return [(r1 - d, c1, r2 - d, c2)]
            else:
                result = []
                if r1 < index:
                    result.append((r1, c1, index - 1, c2))
                if r2 >= index + d:
                    result.append((index, c1, r2 - d, c2))
                return result
    
    def apply_col_edit(rect, index, delta):
        r1, c1, r2, c2 = rect
        if delta > 0:
            if c2 < index:
                return [rect]
            elif c1 >= index:
                return [(r1, c1 + delta, r2, c2 + delta)]
            else:
                return [(r1, c1, r2, index - 1), (r1, index + delta, r2, c2 + delta)]
        else:
            d = -delta
            if c2 < index:
                return [rect]
            elif c1 >= index + d:
                return [(r1, c1 - d, r2, c2 - d)]
            else:
                result = []
                if c1 < index:
                    result.append((r1, c1, r2, index - 1))
                if c2 >= index + d:
                    result.append((r1, index, r2, c2 - d))
                return result
    
    def merge_intervals(intervals):
        if not intervals:
            return []
        sorted_intervals = sorted(set(intervals))
        merged = []
        for c1, c2 in sorted_intervals:
            if merged and merged[-1][1] >= c1 - 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], c2))
            else:
                merged.append((c1, c2))
        return merged
    
    rectangles = list(ranges)
    
    for axis, index, delta in edits:
        new_rectangles = []
        for rect in rectangles:
            if axis == "row":
                new_rectangles.extend(apply_row_edit(rect, index, delta))
            else:
                new_rectangles.extend(apply_col_edit(rect, index, delta))
        rectangles = new_rectangles
    
    if not rectangles:
        return []
    
    events = {}
    for r1, c1, r2, c2 in rectangles:
        if r1 not in events:
            events[r1] = ([], [])
        if r2 + 1 not in events:
            events[r2 + 1] = ([], [])
        events[r1][0].append((c1, c2))
        events[r2 + 1][1].append((c1, c2))
    
    result = []
    active = []
    prev_row = None
    prev_merged = None
    
    for row in sorted(events.keys()):
        for interval in events[row][0]:
            active.append(interval)
        for interval in events[row][1]:
            active.remove(interval)
        
        current_merged = tuple(merge_intervals(active))
        
        if prev_merged is not None and prev_merged != current_merged:
            for c1, c2 in prev_merged:
                result.append((prev_row, c1, row - 1, c2))
        
        if current_merged:
            prev_row = row
            prev_merged = current_merged
        else:
            prev_row = None
            prev_merged = None
    
    result.sort()
    return result